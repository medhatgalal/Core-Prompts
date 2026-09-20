"""Mechanical runtime tests. All semantic receipts below are FAKE FIXTURES.

These tests never establish actual independent review, source truth, or pixel QA.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest


RESOURCE = Path(__file__).resolve().parents[1] / "sources/capability-resources/engos-quality-shaping-gate"
SCRIPT = RESOURCE / "scripts/shaping_run.py"


@pytest.fixture
def runtime():
    spec = importlib.util.spec_from_file_location("shaping_runtime", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture
def workshop(tmp_path, runtime):
    root = tmp_path / "workshop"
    root.mkdir()
    policy = {
        "schema_version": 1, "policy_id": "FAKE-TEST-POLICY",
        "gates": {f"G{i}": {"predicates": runtime.PREDICATES[f"G{i}"],
                              "required_outputs": names}
                  for i, names in enumerate(runtime.MIN_OUTPUTS)},
        "scoring": {"dimensions": runtime.TEAM + runtime.PITCH,
                    "minimum_dimension": 3, "minimum_overall": 4},
        "references": {"gates": "sources/gates.md", "rubric": "sources/rubric.txt"},
        "delivery_targets": [{"surface": "html", "destination": "local-preview"},
                             {"surface": "google-doc", "destination": "private-folder"}],
    }
    policy_path = write_json(root / "sources/policy.json", policy)
    for name in ("original", "assignment", "context", "rubric"):
        (root / f"sources/{name}.txt").write_text(f"FAKE fixture {name}\n")
    (root / "sources/gates.md").write_text("FAKE test gate policy, not independent review\n")
    rt = runtime.Runtime(root)
    rt.init("fixture-run", "fixture-controller", policy_path)
    return rt


def version(rt):
    return rt.status()["version"]


def prepare(rt, gate, suffix="a", extra_inputs=()):
    spec = {
        "schema_version": 1, "work_order_id": f"{gate}-{suffix}", "gate": gate,
        "author": "fixture-author", "reviewer": {
            "identity": "fixture-reviewer", "independent": True,
            "assignment_evidence": "sources/assignment.txt",
            "context_evidence": "sources/context.txt"},
        "inputs": [f"sources/{n}.txt" for n in ("original", "assignment", "context", "rubric")],
        "source_revision": "fixture-source-1", "resource_revision": "fixture-resource-1",
        "skill_allowlist": ["fixture-only"], "original_constraints": ["Fixture, never real review"],
        "assigned_questions": [], "source_access_scope": "fixture sources only",
        "effort_bound": "one fake assessment", "stop_conditions": ["missing evidence"],
    }
    spec['inputs'].extend(extra_inputs)
    order = rt.prepare(spec, version(rt))
    candidate = rt.root / order["candidate_root"]
    candidate.mkdir(parents=True)
    for name in rt.policy()["gates"][gate]["required_outputs"]:
        (candidate / name).write_text(f"FAKE fixture content for {name}\n")
    (candidate / "evidence.txt").write_text("FAKE semantic evidence; no truth claim\n")
    write_json(candidate / "questions.json", [])
    write_json(candidate / "decisions.json", [])
    return order, candidate


def fake_receipt(rt, order, seal):
    """Deliberately fabricated reviewer fixture, not independent review evidence."""
    return {
        "schema_version": 1, "run_id": order["run_id"], "gate": order["gate"],
        "work_order_id": order["work_order_id"], "generation": order["generation"],
        "policy_hash": order["policy_hash"], "resource_revision": order["resource_revision"],
        "predecessor": order["predecessor"], "return_hash": seal["return_hash"],
        "subject": seal["subject"], "reviewer": order["reviewer"]["identity"],
        "authored_candidate": False, "independence_confirmed": True,
        "evidence": {"E1": "evidence.txt"},
        "assessments": {p: {"outcome": "pass", "evidence_ids": ["E1"],
                            "explanation": "FAKE test assessment, not a real review"}
                        for p in rt.policy()["gates"][order["gate"]]["predicates"]},
        "findings": [], "unresolved_blockers": [], "verdict": "pass",
        "next_state": order["gate"],
        "scores": ({"dimensions": {d: {"score": 4, "rationale": "FAKE fixture",
                                      "evidence_ids": ["E1"]}
                                   for d in rt.policy()["scoring"]["dimensions"]},
                    "team_mean": 4, "pitch_mean": 4, "overall": 4}
                   if order["gate"] == "G3" else None),
        "render_evidence": {name: ["E1"] for name in ("component.mmd", "sequence.mmd", "data-flow.mmd")}
                           if order["gate"] == "G3" else {},
        "targets": [],
    }


def accept_fixture(rt, order, candidate, receipt=None):
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = receipt or fake_receipt(rt, order, seal)
    path = write_json(rt.root / f"receipt-{order['work_order_id']}.json", receipt)
    return rt.accept(path, version(rt)), path


def advance(rt, through=3):
    for number in range(through + 1):
        order, candidate = prepare(rt, f"G{number}")
        accept_fixture(rt, order, candidate)


def prepared_delivery(rt, include_delivery_inputs=False):
    """Create a full mechanical delivery fixture; never real external QA."""
    advance(rt)
    assert rt.status()["content_ready"] is True
    assert rt.status()["delivery_state"] == "delivery_pending"
    operations = []
    for target in rt.policy()["delivery_targets"]:
        op = rt.delivery_intent(target["surface"], target["destination"], version(rt))
        evidence = {}
        roles = ("readback", "structured", "inventory") if target["surface"] == "json" else ("readback", "pixels", "inventory")
        for role in roles:
            path = f"sources/{target['surface']}-{role}.txt"
            if role == "readback" and target["surface"] == "json":
                write_json(rt.root / path, {"fixture": "FAKE structured export; not real parity proof"})
            else:
                (rt.root / path).write_text(f"FAKE {role} evidence {target}\n")
            evidence[role] = path
        rt.delivery_record(op["operation_id"], {
            "status": "verified", "target_id": target["destination"], "revision": "saved-1",
            "evidence": evidence, "note": "FAKE delivery fixture"}, version(rt))
        operations.append((op, evidence))
    delivery_inputs = [p for _, evidence in operations for p in evidence.values()] if include_delivery_inputs else []
    order, candidate = prepare(rt, "G4", extra_inputs=delivery_inputs)
    refs = []
    for number, (op, evidence) in enumerate(operations):
        item = {"operation_id": op["operation_id"]}
        for role, path in evidence.items():
            name = f"target-{number}-{role}.txt"
            (candidate / name).write_bytes((rt.root / path).read_bytes())
            item[role] = [f"E{number}_{role}"]
        refs.append(item)
    sealed = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, sealed)
    for number, item in enumerate(refs):
        for role in set(item) - {"operation_id"}:
            receipt["evidence"][item[role][0]] = f"target-{number}-{role}.txt"
    receipt["targets"] = refs
    return order, candidate, receipt


def test_complete_advancement_snapshot_and_delivery(workshop):
    rt = workshop
    order, candidate, receipt = prepared_delivery(rt)
    result, path = accept_fixture(rt, order, candidate, receipt)
    assert rt.status()["stage"] == "G4"
    assert rt.status()["delivery_state"] == "verified"
    snapshot = rt.snapshot(result["snapshot"])
    assert all(name in snapshot["files"] for group in rt.MIN_OUTPUTS for name in group)
    assert snapshot["questions"] == snapshot["decisions"] == []
    assert snapshot["receipt"] == receipt
    before = version(rt)
    assert rt.accept(path, 0)["replayed"] is True
    assert version(rt) == before


@pytest.mark.parametrize('changed', ['sources/policy.json', 'sources/rubric.txt'])
def test_policy_bindings_cannot_be_shadowed_by_ordinary_inputs(workshop, runtime, changed):
    rt = workshop
    if changed.endswith('.json'):
        modified = deepcopy(rt.policy())
        modified['scoring']['minimum_overall'] = 5
        write_json(rt.root/changed, modified)
    else:
        (rt.root/changed).write_text('Changed required rubric, not accepted policy')
    before = (rt.root/'state/run.json').read_bytes()
    extras = [changed] if changed.endswith('.json') else []
    with pytest.raises(runtime.Hold, match='changed dependency'):
        prepare(rt, 'G0', extra_inputs=extras)
    assert (rt.root/'state/run.json').read_bytes() == before


def test_status_preserves_policy_pin_even_in_legacy_shadowed_snapshot(workshop, monkeypatch):
    rt = workshop
    modified = deepcopy(rt.policy()); modified['scoring']['minimum_overall'] = 5
    write_json(rt.root/'sources/policy.json', modified)
    # Model a store accepted by the earlier masking bug; not a semantic receipt.
    with monkeypatch.context() as m:
        m.setattr(rt, '_check_bindings', lambda *args: None)
        order, candidate = prepare(rt, 'G0', extra_inputs=['sources/policy.json'])
        accept_fixture(rt, order, candidate)
    assert 'sources/policy.json' in rt.status()['dependency_drift']


def test_g4_input_drift_does_not_revoke_unchanged_content(workshop):
    rt = workshop
    order, candidate, receipt = prepared_delivery(rt, include_delivery_inputs=True)
    accept_fixture(rt, order, candidate, receipt)
    (rt.root/'sources/html-readback.txt').write_text('Changed delivery observation only')
    observed = rt.status()
    assert observed['content_ready'] is True
    assert observed['delivery_state'] == 'delivery_pending'
    assert 'sources/html-readback.txt' in observed['dependency_drift']


@pytest.mark.parametrize('through', [1, 3])
def test_no_delivery_target_needed_for_frame_or_shaped_draft(workshop, runtime, tmp_path, through):
    policy = deepcopy(workshop.policy()); policy['delivery_targets'] = []
    root = tmp_path/'draft-only'; (root/'sources').mkdir(parents=True)
    for file in (workshop.root/'sources').iterdir():
        (root/'sources'/file.name).write_bytes(file.read_bytes())
    path = write_json(root/'sources/policy.json', policy)
    rt = runtime.Runtime(root); rt.init('draft-only','fixture-controller',path)
    advance(rt, through)
    assert rt.status()['stage'] == f'G{through}'
    if through == 3:
        assert rt.status()['content_ready'] is True
        with pytest.raises(runtime.Hold, match='target not requested'):
            rt.delivery_intent('html','unrequested',version(rt))
        order, candidate = prepare(rt,'G4')
        seal = rt.seal(order['work_order_id'],version(rt))
        after_seal = (root/'state/run.json').read_bytes()
        receipt = fake_receipt(rt,order,seal)
        with pytest.raises(runtime.Hold, match='missing required delivery targets'):
            rt.accept(write_json(root/'empty-G4.json',receipt),version(rt))
        assert (root/'state/run.json').read_bytes() == after_seal
        assert rt.status()['stage'] == 'G3'


@pytest.mark.parametrize("mutation", ["missing_assessment", "fail", "unverifiable", "no_evidence",
                                       "invented_ref", "author", "reviewer", "predecessor",
                                       "generation", "hash", "blocker", "next_state"])
def test_bad_receipts_hold_without_mutation(workshop, mutation):
    rt = workshop
    order, _ = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    assessment = next(iter(receipt["assessments"].values()))
    if mutation == "missing_assessment": receipt["assessments"] = {}
    elif mutation in ("fail", "unverifiable"): assessment["outcome"] = mutation
    elif mutation == "no_evidence": assessment["evidence_ids"] = []
    elif mutation == "invented_ref": assessment["evidence_ids"] = ["does-not-exist"]
    elif mutation == "author": receipt["authored_candidate"] = True
    elif mutation == "reviewer": receipt["reviewer"] = "fixture-author"
    elif mutation == "predecessor": receipt["predecessor"] = "0" * 64
    elif mutation == "generation": receipt["generation"] += 1
    elif mutation == "hash": receipt["subject"]["brief.md"] = "0" * 64
    elif mutation == "blocker": receipt["unresolved_blockers"] = ["no proof"]
    elif mutation == "next_state": receipt["next_state"] = "G4"
    path = write_json(rt.root / "bad.json", receipt)
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Hold): rt.accept(path, version(rt))
    assert (rt.root / "state/run.json").read_bytes() == before


@pytest.mark.parametrize("changed", ["candidate", "input", "policy"])
def test_changed_bytes_refused(workshop, changed):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    path = write_json(rt.root / "review.json", fake_receipt(rt, order, seal))
    target = {"candidate": candidate / "brief.md", "input": rt.root / "sources/original.txt",
              "policy": rt.root / "sources/policy.json"}[changed]
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(rt.Hold): rt.accept(path, version(rt))
    assert rt.status()["stage"] is None


def test_paths_symlinks_and_missing_outputs(workshop, tmp_path):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    (candidate / "brief.md").unlink()
    with pytest.raises(rt.Hold): rt.seal(order["work_order_id"], version(rt))
    external = tmp_path / "secret.txt"
    external.write_text("not evidence")
    (candidate / "brief.md").symlink_to(external)
    with pytest.raises(rt.Hold): rt.seal(order["work_order_id"], version(rt))
    for path in ("../secret.txt", "/tmp/secret.txt", "a/../../secret.txt", "a\\b", "./brief.md"):
        with pytest.raises(rt.Hold): rt.safe_relative(path)


def test_reopen_invalidates_late_work_and_keeps_history(workshop):
    rt = workshop
    advance(rt, 1)
    order, candidate = prepare(rt, "G2")
    seal = rt.seal(order["work_order_id"], version(rt))
    path = write_json(rt.root / "late.json", fake_receipt(rt, order, seal))
    rt.reopen("G1", "appetite changed", version(rt))
    assert rt.status()["stage"] == "G0"
    with pytest.raises(rt.Hold): rt.accept(path, version(rt))
    replacement, folder = prepare(rt, "G1", "new")
    accept_fixture(rt, replacement, folder)
    assert rt.status()["stage"] == "G1"
    assert len(list((rt.root / "accepted").glob("*.json"))) == 3


@pytest.mark.parametrize("status", ["proposed", "deferred", "disputed", "excluded"])
def test_blocking_uncertainty_cannot_be_hidden(workshop, status):
    rt = workshop
    advance(rt, 1)
    order, candidate = prepare(rt, "G2")
    write_json(candidate / "questions.json", [{
        "id": "U1", "blocking": True, "in_scope": True, "status": status,
        "evidence": [], "decision_id": None, "dependency_evidence": [], "evidence_standard": "observed fixture result"}])
    with pytest.raises(rt.Hold): accept_fixture(rt, order, candidate)
    assert rt.status()["stage"] == "G1"


def test_uncertainty_cannot_disappear_from_next_snapshot(workshop):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    write_json(candidate / "questions.json", [{
        "id": "U1", "blocking": True, "in_scope": True, "status": "deferred",
        "evidence": [], "decision_id": None, "dependency_evidence": [], "evidence_standard": "observed fixture result"}])
    accept_fixture(rt, order, candidate)
    order, candidate = prepare(rt, "G1")
    with pytest.raises(rt.Hold): accept_fixture(rt, order, candidate)


@pytest.mark.parametrize("mutation", ["low_dimension", "low_overall", "missing_dimension", "no_render"])
def test_g3_score_and_render_requirements(workshop, mutation):
    rt = workshop
    advance(rt, 2)
    order, candidate = prepare(rt, "G3")
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    if mutation == "low_dimension": receipt["scores"]["dimensions"]["simplicity"]["score"] = 2
    if mutation == "low_overall": receipt["scores"]["overall"] = 3.9
    if mutation == "missing_dimension": del receipt["scores"]["dimensions"]["simplicity"]
    if mutation == "no_render": receipt["render_evidence"] = {}
    path = write_json(rt.root / "review.json", receipt)
    with pytest.raises(rt.Hold): rt.accept(path, version(rt))


def test_g4_empty_targets_and_uncertain_delivery(workshop):
    rt = workshop
    advance(rt)
    target = rt.policy()["delivery_targets"][0]
    op = rt.delivery_intent(target["surface"], target["destination"], version(rt))
    with pytest.raises(rt.Hold, match="reconciliation_required"):
        rt.delivery_intent(target["surface"], target["destination"], version(rt))
    rt.delivery_record(op["operation_id"], {"status": "uncertain", "note": "write timed out"}, version(rt))
    with pytest.raises(rt.Hold, match="reconciliation_required"):
        rt.delivery_intent(target["surface"], target["destination"], version(rt))
    order, candidate = prepare(rt, "G4")
    with pytest.raises(rt.Hold): accept_fixture(rt, order, candidate)
    assert rt.status()["content_ready"] is True
    assert rt.status()["delivery_state"] == "delivery_pending"


def test_expected_version_conflict_and_receipt_conflict(workshop):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    path = write_json(rt.root / "review.json", fake_receipt(rt, order, seal))
    with pytest.raises(rt.Hold): rt.accept(path, version(rt) - 1)
    rt.accept(path, version(rt))
    receipt = json.loads(path.read_text())
    receipt["findings"] = ["different return"]
    write_json(path, receipt)
    with pytest.raises(rt.Hold, match="conflict"): rt.accept(path, version(rt))


@pytest.mark.parametrize("after", [False, True])
def test_pointer_crash_replay(workshop, monkeypatch, after):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    path = write_json(rt.root / "review.json", fake_receipt(rt, order, seal))
    expected = version(rt)
    # Patch the runtime's commit boundary, not a simulated external service.
    original = rt._replace_pointer
    def crash(pointer):
        if after: original(pointer)
        raise OSError("injected crash at pointer commit")
    monkeypatch.setattr(rt, "_replace_pointer", crash)
    with pytest.raises(OSError): rt.accept(path, expected)
    monkeypatch.setattr(rt, "_replace_pointer", original)
    assert rt.status()["stage"] == ("G0" if after else None)
    result = rt.accept(path, expected)
    assert result["replayed"] is after
    assert rt.status()["stage"] == "G0"


def test_corrupt_snapshot_is_recovery_pending(workshop):
    rt = workshop
    advance(rt, 0)
    snapshot = next((rt.root / "accepted").glob("*.json"))
    snapshot.write_text("{}")
    with pytest.raises(rt.Recovery, match="recovery_pending"): rt.status()


def test_cli_help_and_malformed_input(tmp_path):
    for command in ("init", "status", "prepare", "seal", "accept", "reopen", "delivery-intent", "delivery-record"):
        proc = subprocess.run([sys.executable, str(SCRIPT), command, "--help"], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        assert "--run" in proc.stdout
    proc = subprocess.run([sys.executable, str(SCRIPT), "status", "--run", str(tmp_path / "absent")], capture_output=True, text=True)
    assert proc.returncode == 3
    assert json.loads(proc.stdout)["status"] == "recovery_pending"


@pytest.mark.parametrize("role", ["readback", "pixels", "inventory"])
@pytest.mark.parametrize("fault", ["missing", "empty", "wrong_bytes", "drift"])
def test_g4_requires_each_saved_target_evidence(workshop, role, fault):
    rt = workshop
    order, candidate, receipt = prepared_delivery(rt)
    if fault == "missing": del receipt["targets"][0][role]
    if fault == "empty": receipt["targets"][0][role] = []
    if fault == "wrong_bytes": receipt["targets"][0][role] = ["E1"]
    if fault == "drift": (rt.root / f"sources/html-{role}.txt").write_text("different saved observation")
    path = write_json(rt.root / "bad-g4.json", receipt)
    before = version(rt)
    with pytest.raises(rt.Hold): rt.accept(path, before)
    assert version(rt) == before
    assert rt.status()["content_ready"] is True


@pytest.mark.parametrize("stage,name", [(0, "brief.md"), (0, "intake.md"), (1, "framed.md"),
    (2, "research-notes.md"), *[(3, n) for n in ("pitch.md", "pitch-summary.md", "workstreams.md", "traceability.md",
    "contracts.md", "security-owners.md", "component.mmd", "sequence.mmd", "data-flow.mmd")], (4, "betting-table-prep.md")])
def test_every_minimum_artifact_is_required(workshop, stage, name):
    rt = workshop
    advance(rt, stage - 1)
    order, candidate = prepare(rt, f"G{stage}")
    (candidate / name).unlink()
    with pytest.raises(rt.Hold, match="missing outputs"): rt.seal(order["work_order_id"], version(rt))


@pytest.mark.parametrize("closure", ["answered", "excluded"])
def test_valid_blocking_uncertainty_closure_advances(workshop, closure):
    rt = workshop
    advance(rt, 1)
    order, candidate = prepare(rt, "G2")
    questions = [{"id": "U1", "blocking": True, "in_scope": closure == "answered", "status": closure,
                  "evidence_standard": "Actual observed fixture behavior", "evidence": ["evidence.txt"],
                  "decision_id": "D1" if closure == "excluded" else None,
                  "dependency_evidence": ["evidence.txt"] if closure == "excluded" else []}]
    write_json(candidate / "questions.json", questions)
    decisions = [{"id": "D1", "status": "confirmed", "authority": "FAKE human", "reason": "FAKE scope reduction",
                  "evidence": ["evidence.txt"]}] if closure == "excluded" else []
    write_json(candidate / "decisions.json", decisions)
    result, _ = accept_fixture(rt, order, candidate)
    snapshot = rt.snapshot(result["snapshot"])
    assert snapshot["questions"] == questions
    assert snapshot["decisions"] == decisions
    assert rt.status()["stage"] == "G2"


def test_cannot_revise_accepted_decision_or_upstream_prose(workshop):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    decisions = [{"id": "D1", "status": "confirmed", "authority": "FAKE human", "reason": "FAKE constraint",
                  "evidence": ["evidence.txt"]}]
    write_json(candidate / "decisions.json", decisions)
    accept_fixture(rt, order, candidate)
    order, candidate = prepare(rt, "G1")
    decisions[0]["reason"] = "changed constraint"
    write_json(candidate / "decisions.json", decisions)
    with pytest.raises(rt.Hold, match="decision changed"): rt.seal(order["work_order_id"], version(rt))
    decisions[0]["reason"] = "FAKE constraint"
    write_json(candidate / "decisions.json", decisions)
    (candidate / "brief.md").write_text("new problem")
    with pytest.raises(rt.Hold, match="upstream artifact changed"): rt.seal(order["work_order_id"], version(rt))


def test_policy_rebind_requires_g0_and_old_work_stays_stale(workshop):
    rt = workshop
    advance(rt, 1)
    policy_path = rt.root / "sources/policy.json"
    policy = rt.policy()
    policy["policy_id"] = "new-fixture-policy"
    write_json(policy_path, policy)
    with pytest.raises(rt.Hold): rt.reopen("G1", "policy changed", version(rt), policy_path)
    rt.reopen("G0", "policy changed", version(rt), policy_path)
    order, candidate = prepare(rt, "G0", "new-policy")
    accept_fixture(rt, order, candidate)
    assert rt.status()["stage"] == "G0"


def test_prepare_assignment_precedes_candidate_and_self_review_refused(workshop):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    spec = {key: order[key] for key in ("schema_version", "work_order_id", "gate", "author", "reviewer", "inputs",
        "source_revision", "resource_revision", "skill_allowlist", "original_constraints", "assigned_questions",
        "source_access_scope", "effort_bound", "stop_conditions")}
    spec = deepcopy(spec)
    spec["work_order_id"] = "G0-new"
    spec["reviewer"]["identity"] = spec["author"]
    with pytest.raises(rt.Hold, match="independent reviewer"): rt.prepare(spec, version(rt))
    spec["reviewer"]["identity"] = "other-reviewer"
    (rt.root / "candidates/G0-new").mkdir()
    with pytest.raises(rt.Hold, match="before reviewer assignment"): rt.prepare(spec, version(rt))


def test_state_symlink_nested_candidate_symlink_and_fifo_refused(workshop, tmp_path):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    (candidate / "linked").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(rt.Hold): rt.seal(order["work_order_id"], version(rt))
    (candidate / "linked").unlink()
    if sys.platform != "win32":
        import os
        os.mkfifo(candidate / "fifo")
        with pytest.raises(rt.Hold): rt.seal(order["work_order_id"], version(rt))


def test_runtime_rejects_malformed_json_and_nonfinite_scores(workshop, runtime):
    for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b'not json', b'\xff'):
        with pytest.raises(runtime.Hold): runtime.decode(data)
    for value in (True, float("nan"), float("inf"), "4", None):
        with pytest.raises(runtime.Hold): runtime.number(value)


def test_missing_pointer_and_orphan_revision_never_guess_success(workshop):
    rt = workshop
    path = rt.root / "state/run.json"
    original = path.read_bytes()
    path.unlink()
    with pytest.raises(rt.Recovery): rt.status()
    with pytest.raises(rt.Hold): rt.init("other", "controller", rt.root / "sources/policy.json")
    path.write_bytes(original)
    assert rt.status()["stage"] is None


def test_controller_lock_blocks_second_process(workshop):
    rt = workshop
    with rt.lock():
        proc = subprocess.run([sys.executable, str(SCRIPT), "reopen", "--run", str(rt.root),
            "--gate", "G0", "--reason", "competing controller", "--expected-version", str(version(rt))],
            capture_output=True, text=True, timeout=10)
    assert proc.returncode == 2
    assert "lock busy" in json.loads(proc.stdout)["reason"]


def test_concurrent_identical_accepts_commit_once(workshop):
    rt = workshop
    order, _ = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    path = write_json(rt.root / "review.json", fake_receipt(rt, order, seal))
    expected = version(rt)
    cmd = [sys.executable, str(SCRIPT), "accept", "--run", str(rt.root), "--receipt", str(path),
           "--expected-version", str(expected)]
    processes = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = [(p, p.communicate(timeout=10)) for p in processes]
    assert all(p.returncode in (0, 2) for p, _ in results)
    assert any(p.returncode == 0 for p, _ in results)
    assert version(rt) == expected + 1
    assert rt.accept(path, expected)["replayed"] is True


def test_delivery_replay_and_reconciliation_after_reopen(workshop):
    rt = workshop
    order, candidate, receipt = prepared_delivery(rt)
    accept_fixture(rt, order, candidate, receipt)
    operation = next(iter(rt.status()["deliveries"].values()))
    same = rt.delivery_intent(operation["surface"], operation["destination"], version(rt))
    assert same["may_create"] is False
    assert same["replayed"] is True
    record = deepcopy(operation["record"])
    record["evidence"] = {role: value["path"] for role, value in record["evidence"].items()}
    assert rt.delivery_record(operation["operation_id"], record, 0)["replayed"] is True
    record["revision"] = "saved-2"
    with pytest.raises(rt.Hold): rt.delivery_record(operation["operation_id"], record, version(rt))
    rt.reopen("G4", "external edit requires new readback", version(rt))
    rt.delivery_record(operation["operation_id"], record, version(rt))
    assert rt.status()["content_ready"] is True
    assert rt.status()["delivery_state"] == "delivery_pending"
    assert rt.status()["deliveries"][operation["operation_id"]]["history"]


def test_uncertain_create_cannot_hide_behind_reopened_bundle(workshop):
    rt = workshop
    advance(rt)
    target = rt.policy()["delivery_targets"][0]
    rt.delivery_intent(target["surface"], target["destination"], version(rt))
    rt.reopen("G3", "revised solution", version(rt))
    order, candidate = prepare(rt, "G3", "revised")
    accept_fixture(rt, order, candidate)
    with pytest.raises(rt.Hold, match="reconciliation_required"):
        rt.delivery_intent(target["surface"], target["destination"], version(rt))


def test_status_discloses_drift_without_changing_pointer(workshop):
    rt = workshop
    advance(rt)
    before = (rt.root / "state/run.json").read_bytes()
    (rt.root / "sources/original.txt").write_text("new problem")
    status = rt.status()
    assert status["dependency_drift"] == ["sources/original.txt"]
    assert status["content_ready"] is False
    assert (rt.root / "state/run.json").read_bytes() == before


def json_only_policy(rt):
    policy = rt.policy()
    policy["delivery_targets"] = [{"surface": "json", "destination": "authorized-json-export"}]
    path = write_json(rt.root / "sources/policy.json", policy)
    rt.reopen("G0", "Explicit fixture scope: JSON-only export", version(rt), path)


def test_json_only_advances_with_structured_evidence_and_no_target_pixels(workshop):
    rt = workshop
    json_only_policy(rt)
    order, candidate, receipt = prepared_delivery(rt)
    assert "pixels" not in receipt["targets"][0]
    assert receipt["targets"][0]["structured"]
    result, _ = accept_fixture(rt, order, candidate, receipt)
    snapshot = rt.snapshot(result["snapshot"])
    assert snapshot["deliveries"]
    assert rt.status()["stage"] == "G4"
    assert rt.status()["delivery_state"] == "verified"


@pytest.mark.parametrize("fault", ["no_structured", "invalid_json", "pixels_instead"])
def test_json_target_needs_parsing_and_structured_assessment(workshop, fault):
    rt = workshop
    json_only_policy(rt)
    advance(rt)
    op = rt.delivery_intent("json", "authorized-json-export", version(rt))
    for name in ("readback", "structured", "inventory"):
        write_json(rt.root / f"sources/json-{name}.json", {"fixture": name})
    record = {"status": "verified", "target_id": "json-1", "revision": "1", "note": "FAKE fixture",
              "evidence": {k: f"sources/json-{k}.json" for k in ("readback", "structured", "inventory")}}
    if fault == "no_structured": del record["evidence"]["structured"]
    if fault == "invalid_json": (rt.root / "sources/json-readback.json").write_text("not a JSON document")
    if fault == "pixels_instead": record["evidence"]["pixels"] = record["evidence"].pop("structured")
    with pytest.raises(rt.Hold): rt.delivery_record(op["operation_id"], record, version(rt))


@pytest.mark.parametrize("surface", ["html", "google-doc"])
def test_visual_target_cannot_substitute_structured_evidence_for_pixels(workshop, surface):
    rt = workshop
    advance(rt)
    target = next(t for t in rt.policy()["delivery_targets"] if t["surface"] == surface)
    op = rt.delivery_intent(surface, target["destination"], version(rt))
    record = {"status": "verified", "target_id": "saved-id", "revision": "1", "note": "FAKE fixture",
              "evidence": {k: "sources/original.txt" for k in ("readback", "structured", "inventory")}}
    with pytest.raises(rt.Hold): rt.delivery_record(op["operation_id"], record, version(rt))


def test_json_only_still_requires_g3_local_diagram_inspection(workshop):
    rt = workshop
    json_only_policy(rt)
    advance(rt, 2)
    order, _ = prepare(rt, "G3")
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    del receipt["render_evidence"]["sequence.mmd"]
    path = write_json(rt.root / "bad-g3.json", receipt)
    with pytest.raises(rt.Hold): rt.accept(path, version(rt))


@pytest.mark.parametrize("team_values,pitch_values,expected_pass", [
    ([3, 4, 4, 4, 4, 4, 4], [5, 4, 4, 4, 4], True),  # 27+21=48; category-mean mean >4
    ([5, 4, 4, 4, 4, 4, 4], [3, 4, 4, 4, 4], True),  # 29+19=48; category-mean mean <4
    ([3, 3, 3, 4, 4, 4, 4], [5, 5, 4, 4, 4], False), # 25+22=47; category-mean mean >4
])
def test_overall_is_equal_weight_across_twelve_dimensions(workshop, team_values, pitch_values, expected_pass):
    rt = workshop
    advance(rt, 2)
    order, _ = prepare(rt, "G3")
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    for key, value in zip(rt.policy()["scoring"]["dimensions"], team_values + pitch_values):
        receipt["scores"]["dimensions"][key]["score"] = value
    receipt["scores"].update(team_mean=sum(team_values)/7, pitch_mean=sum(pitch_values)/5,
                             overall=(sum(team_values)+sum(pitch_values))/12)
    path = write_json(rt.root / "weighted.json", receipt)
    if expected_pass:
        rt.accept(path, version(rt))
        assert rt.status()["stage"] == "G3"
    else:
        with pytest.raises(rt.Hold): rt.accept(path, version(rt))


def test_delivery_evidence_drift_keeps_content_ready(workshop):
    rt = workshop
    order, candidate, receipt = prepared_delivery(rt)
    accept_fixture(rt, order, candidate, receipt)
    (rt.root / "sources/html-pixels.txt").write_text("changed saved-target observation")
    status = rt.status()
    assert status["content_ready"] is True
    assert status["delivery_state"] == "delivery_pending"
    assert status["delivery_drift"] == ["sources/html-pixels.txt"]


def test_new_blocking_uncertainty_in_shaping_requires_research_reopen(workshop):
    rt = workshop
    advance(rt, 2)
    order, candidate = prepare(rt, "G3")
    write_json(candidate / "questions.json", [{"id": "new-seam", "blocking": True, "in_scope": True,
        "status": "answered", "evidence_standard": "actual compatibility result", "evidence": ["evidence.txt"],
        "decision_id": None, "dependency_evidence": []}])
    with pytest.raises(rt.Hold, match="reopen G2"): rt.seal(order["work_order_id"], version(rt))


@pytest.mark.parametrize("representation", ["visual", "json"])
def test_published_schema_matches_complete_fixture_receipts(workshop, representation):
    # Optional development-only validator; the shipped runtime stays stdlib-only.
    jsonschema = pytest.importorskip("jsonschema")
    rt = workshop
    schema = json.loads((RESOURCE / "schemas/runtime.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    example = json.loads((RESOURCE / "schemas/policy.example.json").read_text())
    validator.validate(example)
    if representation == "json": json_only_policy(rt)
    order, candidate, receipt = prepared_delivery(rt)
    validator.validate(rt.policy())
    validator.validate(receipt)
    result, _ = accept_fixture(rt, order, candidate, receipt)
    for key in rt.status()["accepted"].values():
        validator.validate(rt.snapshot(key)["receipt"])
