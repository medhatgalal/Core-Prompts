"""Progress regression evidence only; all host/reviewer observations are fixtures."""
import json
import subprocess
import sys

import pytest

from test_shaping_runtime import (
    RESOURCE, SCRIPT, accept_fixture, advance, fake_receipt, prepare, prepared_delivery,
    runtime, version, workshop, write_json,
)

AS_OF = "2026-09-18T12:00:00Z"


@pytest.fixture(autouse=True)
def observation_clock(runtime, monkeypatch):
    monkeypatch.setattr(runtime, "utc_now", lambda: AS_OF)


def context(rt, stop="G4", name="Fixture <script>alert(1)</script>"):
    spec = {"name": name, "evidence_mode": "simulated", "requested_stop": stop,
            "observed_at": "2026-09-18T10:00:00Z", "evidence": "sources/original.txt",
            "investment_appetite": "unknown"}
    rt.progress_context(spec, version(rt))
    return spec


def observe(rt, order, kind="started", **extra):
    record = {"event_id": f"event-{version(rt)}", "run_id": order["run_id"],
              "version": version(rt), "generation": rt.status()["generation"],
              "work_order_id": order["work_order_id"], "kind": kind,
              "observed_at": "2026-09-18T11:59:00Z", "actor": order["author"],
              "evidence": "sources/context.txt", **extra}
    rt.observe(record, version(rt))
    return record


def progress(rt):
    return rt.progress(AS_OF)


def test_legacy_consistency_is_not_acceptance(workshop):
    rt = workshop
    assert rt.status()["status"] == "consistent"
    p = progress(rt)
    assert p["requested_stop"] is None
    assert p["evidence"]["mode"] == "unknown"
    assert p["activity"]["state"] == "unknown"
    assert p["requested_complete"] is None
    assert all(g["state"] == "not_reached" for g in p["gates"])


def test_scoped_frame_finish_and_repeatable_read_only_projection(workshop):
    rt = workshop
    context(rt, "G1")
    advance(rt, 1)
    pointer = (rt.root / "state/run.json").read_bytes()
    p = progress(rt)
    assert p == progress(rt)
    assert p["requested_complete"] is True
    assert p["verified_count"] == 2 and p["applicable_count"] == 2
    assert [g["state"] for g in p["gates"]] == ["verified", "verified"] + ["outside_scope"] * 3
    assert p["evidence"]["mode"] == "simulated"
    assert p["evidence"]["provenance"]["path"] == "sources/original.txt"
    assert (rt.root / "state/run.json").read_bytes() == pointer


def test_prepare_is_queued_not_active_and_seal_is_review_pending(workshop):
    rt = workshop
    context(rt)
    order, _ = prepare(rt, "G0")
    p = progress(rt)
    assert p["gates"][0]["state"] == "queued"
    assert p["activity"]["state"] == "unknown"
    assert p["current"]["assignment"]["work_order_id"] == order["work_order_id"]
    observe(rt, order)
    assert progress(rt)["gates"][0]["state"] == "last_observed_active"
    rt.seal(order["work_order_id"], version(rt))
    assert progress(rt)["gates"][0]["state"] == "review_pending"


def test_stopped_observation_does_not_erase_acceptance(workshop):
    rt = workshop
    context(rt)
    order, candidate = prepare(rt, "G0")
    accept_fixture(rt, order, candidate)
    observe(rt, order, "stopped")
    p = progress(rt)
    assert p["gates"][0]["state"] == "verified"
    assert p["activity"]["state"] == "stopped"


def test_activity_age_is_not_failure_or_continuous_liveness(workshop):
    rt = workshop
    context(rt)
    order, _ = prepare(rt, "G0")
    observe(rt, order, observed_at="2026-09-18T10:30:00Z")
    p = progress(rt)
    assert p["activity"]["state"] == "stale"
    assert p["gates"][0]["state"] == "queued"
    assert "hung" not in json.dumps(p)


@pytest.mark.parametrize("field,value", [
    ("run_id", "other"), ("generation", 99), ("version", 99),
    ("actor", "unassigned"), ("evidence", "../escape"),
    ("evidence", "https://example.org"), ("observed_at", "tomorrow"),
    ("observed_at", "2099-01-01T00:00:00Z"),
])
def test_invalid_observations_rejected_without_mutation(workshop, field, value):
    rt = workshop
    order, _ = prepare(rt, "G0")
    before = version(rt)
    with pytest.raises(rt.Hold): observe(rt, order, **{field: value})
    assert version(rt) == before


def test_observation_replay_conflict_ordering_and_late_generation(workshop):
    rt = workshop
    order, _ = prepare(rt, "G0")
    event = observe(rt, order)
    before = version(rt)
    assert rt.observe(event, event["version"])["replayed"] is True
    assert version(rt) == before
    with pytest.raises(rt.Hold, match="conflict"):
        rt.observe({**event, "kind": "stopped"}, before)
    with pytest.raises(rt.Hold, match="out-of-order"):
        observe(rt, order, observed_at="2026-09-18T11:00:00Z")
    rt.reopen("G0", "new attempt", version(rt))
    with pytest.raises(rt.Hold): rt.observe(event, event["version"])
    with pytest.raises(rt.Hold): observe(rt, order)
    assert progress(rt)["activity"]["state"] == "unknown"


@pytest.mark.parametrize("hold_type,state", [("prerequisite", "blocked"), ("decision", "awaiting_input")])
def test_hold_exposes_needed_answer_owner_and_action(workshop, hold_type, state):
    rt = workshop
    context(rt)
    order, _ = prepare(rt, "G0")
    observe(rt, order, "held", hold_type=hold_type, reason="Appetite missing",
            needed="Investment limit", respondent=None, next_action="Identify decision maker")
    p = progress(rt)
    assert p["gates"][0]["state"] == state
    assert p["current"]["blockers"][0]["respondent"] is None
    assert p["current"]["next_action"] == "Identify decision maker"


def test_failed_review_candidate_keeps_predecessor_accepted(workshop):
    rt = workshop
    context(rt)
    advance(rt, 0)
    accepted = rt.status()["accepted"]["G0"]
    order, _ = prepare(rt, "G1")
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    receipt["verdict"] = "fail"
    receipt["assessments"]["problem_frame"]["outcome"] = "fail"
    write_json(rt.root / "sources/failed-review.json", receipt)
    observe(rt, order, "review_returned", actor=order["reviewer"]["identity"],
            evidence="sources/failed-review.json")
    p = progress(rt)
    assert p["gates"][0]["state"] == "verified"
    assert p["gates"][1]["state"] == "changes_requested"
    assert p["latest_accepted"]["snapshot"] == accepted
    assert p["latest_draft"]["work_order_id"] == order["work_order_id"]


def test_conflicting_reviews_do_not_use_last_writer_wins(workshop):
    rt = workshop
    context(rt)
    order, _ = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    for i, verdict in enumerate(("fail", "pass")):
        receipt = fake_receipt(rt, order, seal)
        receipt["verdict"] = verdict
        path = f"sources/review-{i}.json"
        write_json(rt.root / path, receipt)
        observe(rt, order, "review_returned", actor=order["reviewer"]["identity"], evidence=path)
    p = progress(rt)
    assert p["gates"][0]["state"] == "blocked"
    assert "conflicting" in p["current"]["next_action"].lower()
    assert p["latest_accepted"] is None


def test_source_drift_and_reopen_keep_historical_acceptance(workshop):
    rt = workshop
    context(rt, "G1")
    advance(rt, 1)
    (rt.root / "sources/original.txt").write_text("changed original")
    p = progress(rt)
    assert not p["requested_complete"]
    assert p["gates"][0]["state"] == "stale"
    assert p["latest_accepted"]["state"] == "stale"
    rt.reopen("G1", "changed appetite", version(rt))
    assert progress(rt)["gates"][1]["accepted"]["state"] == "stale"


def test_delivery_drift_is_separate_from_content_and_remote_freshness(workshop):
    rt = workshop
    context(rt)
    order, candidate, receipt = prepared_delivery(rt)
    accept_fixture(rt, order, candidate, receipt)
    p = progress(rt)
    assert p["gates"][3]["state"] == "verified"
    assert p["targets"][0]["remote_freshness"] == "unknown"
    assert p["targets"][0]["target_revision"] == "saved-1"
    assert p["targets"][0]["last_read_at"] is None
    (rt.root / "sources/html-pixels.txt").write_text("changed target observation")
    p = progress(rt)
    assert p["gates"][3]["state"] == "verified"
    assert p["gates"][4]["state"] == "stale"
    assert next(t for t in p["targets"] if t["surface"] == "html")["local_integrity"] == "stale"


def test_missing_corrupt_and_changed_sealed_candidate_fail_closed(workshop):
    rt = workshop
    context(rt)
    order, candidate = prepare(rt, "G0")
    rt.seal(order["work_order_id"], version(rt))
    (candidate / "brief.md").write_text("changed sealed bytes")
    assert progress(rt)["gates"][0]["state"] == "stale"
    (rt.root / "state/run.json").write_text("{corrupt")
    p = progress(rt)
    assert p["status"] == "unverifiable"
    assert p["verified_count"] == 0
    assert all(g["state"] == "unverifiable" for g in p["gates"])


def test_safe_formats_share_projection_and_legacy_cli_is_unchanged(workshop, runtime):
    rt = workshop
    context(rt)
    p = progress(rt)
    html = runtime.render_progress(p, "html")
    markdown = runtime.render_progress(p, "markdown")
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "<script>" not in markdown
    assert p == json.loads(runtime.render_progress(p, "json"))
    for fmt in ("json", "markdown", "html"):
        proc = subprocess.run([sys.executable, str(SCRIPT), "progress", "--run", str(rt.root),
                               "--format", fmt, "--as-of", AS_OF], capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.strip() == runtime.render_progress(p, fmt).strip()
    proc = subprocess.run([sys.executable, str(SCRIPT), "status", "--run", str(rt.root)],
                          capture_output=True, text=True)
    assert json.loads(proc.stdout) == rt.status()


def test_no_unsafe_artifact_links(workshop, runtime):
    rt = workshop
    context(rt)
    order, candidate = prepare(rt, "G0")
    (candidate / '<img onerror="bad">.md').write_text("unsafe filename")
    accept_fixture(rt, order, candidate)
    html = runtime.render_progress(progress(rt), "html")
    assert "<img" not in html
    for path in ("../escape", "javascript:alert(1)", "//evil.test/x", "a%2f..%2fx", "a#frag"):
        with pytest.raises(rt.Hold): runtime.progress_link(path)


@pytest.mark.parametrize("after", [False, True])
def test_observation_crash_replay(workshop, monkeypatch, after):
    rt = workshop
    order, _ = prepare(rt, "G0")
    expected = version(rt)
    record = {"event_id": "crash", "run_id": order["run_id"], "version": expected,
              "generation": 0, "work_order_id": order["work_order_id"], "kind": "started",
              "observed_at": "2026-09-18T11:59:00Z", "actor": order["author"],
              "evidence": "sources/context.txt"}
    original = rt._replace_pointer
    def crash(pointer):
        if after: original(pointer)
        raise OSError("injected progress commit crash")
    monkeypatch.setattr(rt, "_replace_pointer", crash)
    with pytest.raises(OSError): rt.observe(record, expected)
    monkeypatch.setattr(rt, "_replace_pointer", original)
    assert rt.observe(record, expected)["replayed"] is after
    assert len(progress(rt)["observations"]) == 1


def test_completed_attempt_is_not_reported_active(workshop):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    observe(rt, order)
    accept_fixture(rt, order, candidate)
    assert progress(rt)["activity"]["state"] == "unknown"


def test_conflicting_accepted_subject_stays_explicit(workshop):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    receipt["verdict"] = "fail"
    write_json(rt.root / "sources/fail.json", receipt)
    observe(rt, order, "review_returned", actor=order["reviewer"]["identity"], evidence="sources/fail.json")
    accept_fixture(rt, order, candidate)
    p = progress(rt)
    assert p["gates"][0]["accepted"]["state"] == "verified"
    assert p["gates"][0]["state"] == "blocked"
    assert "conflicting" in p["current"]["next_action"].lower()


def test_accepted_questions_are_carried_into_next_gate(workshop):
    rt = workshop
    context(rt)
    order, candidate = prepare(rt, "G0")
    write_json(candidate / "questions.json", [{"id": "U1", "blocking": True, "in_scope": True,
        "status": "deferred", "evidence_standard": "confirmed appetite", "evidence": [],
        "decision_id": None, "dependency_evidence": [], "details": {"question": "What is the appetite?",
        "respondent": "owner_unassigned"}}])
    accept_fixture(rt, order, candidate)
    p = progress(rt)
    assert p["gates"][0]["state"] == "verified"
    assert p["gates"][1]["state"] == "awaiting_input"
    assert p["current"]["blockers"][0]["respondent"] is None
    assert "appetite" in p["current"]["blockers"][0]["needed"]


def test_projection_loads_one_revision(workshop, monkeypatch):
    rt = workshop
    advance(rt, 1)
    original = rt._load
    calls = []
    def load_once():
        calls.append(1)
        assert len(calls) == 1
        return original()
    monkeypatch.setattr(rt, "_load", load_once)
    assert progress(rt)["status"] == "projected"


def test_invalidated_observation_is_exposed(workshop):
    rt = workshop
    order, _ = prepare(rt, "G0")
    event = observe(rt, order)
    (rt.root / "sources/context.txt").write_text("replaced host observation")
    p = progress(rt)
    assert p["invalid_observations"][0]["event_id"] == event["event_id"]
    assert p["gates"][0]["state"] == "stale"
    assert p["activity"]["state"] == "unknown"


def test_hold_resolution_needs_controller_and_evidence(workshop):
    rt = workshop
    order, _ = prepare(rt, "G0")
    hold = observe(rt, order, "held", hold_type="prerequisite", reason="Access denied",
                   needed="Source access", respondent=None, next_action="Obtain access")
    observe(rt, order, "started")
    assert progress(rt)["gates"][0]["state"] == "blocked"
    with pytest.raises(rt.Hold): observe(rt, order, "released", resolves=[hold["event_id"]])
    observe(rt, order, "released", actor="fixture-controller", resolves=[hold["event_id"]])
    assert progress(rt)["gates"][0]["state"] == "queued"


@pytest.mark.parametrize("fmt", ["json", "markdown", "html"])
def test_missing_state_fails_closed_in_each_cli_format(tmp_path, fmt):
    proc = subprocess.run([sys.executable, str(SCRIPT), "progress", "--run", str(tmp_path / "missing"),
                           "--format", fmt, "--as-of", AS_OF], capture_output=True, text=True)
    assert proc.returncode == 3
    assert "unverifiable" in proc.stdout


@pytest.mark.parametrize("result,state", [("changed", "stale"), ("failed", "blocked"), ("unchanged", "review_pending")])
def test_target_observation_preserves_content_and_reports_remote_state(workshop, result, state):
    rt = workshop
    context(rt)
    order, _, _ = prepared_delivery(rt)
    operation = next(k for k, op in rt.status()["deliveries"].items() if op["surface"] == "html")
    observe(rt, order, "delivery_result", actor="fixture-controller", operation_id=operation,
            result=result, target_revision="saved-1" if result == "unchanged" else "saved-2")
    p = progress(rt)
    assert p["gates"][3]["state"] == "verified"
    assert p["gates"][4]["state"] == state
    target = next(t for t in p["targets"] if t["surface"] == "html")
    assert target["remote_freshness"] == ("observed_unchanged" if result == "unchanged" else result)
    assert target["last_read_at"] == "2026-09-18T11:59:00Z"


def test_readback_time_is_optional_and_validated(workshop):
    rt = workshop
    advance(rt)
    op = rt.delivery_intent("html", "local-preview", version(rt))
    record = {"status": "verified", "note": "FAKE timestamped readback", "target_id": "t1", "revision": "r1",
              "observed_at": "2026-09-18T11:00:00Z",
              "evidence": {key: "sources/original.txt" for key in ("readback", "pixels", "inventory")}}
    rt.delivery_record(op["operation_id"], record, version(rt))
    assert progress(rt)["targets"][0]["last_read_at"] == record["observed_at"]


def test_symlinked_candidate_is_not_a_status_link(workshop, tmp_path):
    rt = workshop
    order, candidate = prepare(rt, "G0")
    # Select the assigned path through controller state, then replace its empty test directory.
    for path in candidate.iterdir(): path.unlink()
    candidate.rmdir()
    candidate.symlink_to(tmp_path, target_is_directory=True)
    assert progress(rt)["status"] == "unverifiable"


def test_progress_schema_matches_context_observations_and_projection(workshop):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((RESOURCE / "schemas/progress.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    rt = workshop
    validator.validate(context(rt))
    order, _ = prepare(rt, "G0")
    validator.validate(observe(rt, order))
    validator.validate(progress(rt))
    hold = observe(rt, order, "held", hold_type="decision", reason="Missing appetite", needed="Decision",
                   respondent=None, next_action="Ask decision maker")
    validator.validate(hold)
    validator.validate(observe(rt, order, "released", actor="fixture-controller", resolves=[hold["event_id"]]))
    (rt.root / "state/run.json").write_text("corrupt")
    validator.validate(progress(rt))


def test_renderer_refuses_injected_projection_links(workshop, runtime):
    rt = workshop
    advance(rt, 0)
    p = progress(rt)
    p["latest_accepted"]["href"] = "javascript:alert(1)"
    for fmt in ("html", "markdown"):
        with pytest.raises(rt.Hold): runtime.render_progress(p, fmt)


def test_observation_can_never_accept_and_context_cannot_relabel(workshop):
    rt = workshop
    spec = context(rt)
    order, _ = prepare(rt, "G0")
    with pytest.raises(rt.Hold): observe(rt, order, "accepted")
    with pytest.raises(rt.Hold): rt.progress_context({**spec, "evidence_mode": "real"}, version(rt))
    assert not rt.status()["accepted"]


def test_hold_cannot_smuggle_a_resolution(workshop):
    rt = workshop
    order, _ = prepare(rt, "G0")
    with pytest.raises(rt.Hold):
        observe(rt, order, "held", hold_type="decision", reason="missing", needed="decision",
                respondent=None, next_action="ask", resolves=["old-hold"])


def test_pending_g4_exposes_drift_in_saved_target_evidence(workshop):
    rt = workshop
    context(rt)
    prepared_delivery(rt)
    (rt.root / "sources/html-pixels.txt").write_text("replaced saved pixels")
    p = progress(rt)
    assert p["gates"][3]["state"] == "verified"
    assert p["gates"][4]["state"] == "stale"


def test_different_review_wording_is_not_a_conflicting_assessment(workshop):
    rt = workshop
    order, _ = prepare(rt, "G0")
    seal = rt.seal(order["work_order_id"], version(rt))
    for i in range(2):
        review = fake_receipt(rt, order, seal)
        review["assessments"]["original_preserved"]["explanation"] += str(i)
        path = f"sources/reworded-{i}.json"
        write_json(rt.root / path, review)
        observe(rt, order, "review_returned", actor=order["reviewer"]["identity"], evidence=path)
    assert progress(rt)["gates"][0]["state"] == "review_pending"


def review_observation(rt, order, fault="verdict"):
    seal = rt.seal(order["work_order_id"], version(rt))
    review = fake_receipt(rt, order, seal)
    if fault == "verdict": review["verdict"] = "fail"
    elif fault == "scores":
        for item in review["scores"]["dimensions"].values(): item["score"] = 1
        review["scores"].update(team_mean=1, pitch_mean=1, overall=1)
    elif fault == "blockers": review["unresolved_blockers"] = ["Missing safety decision"]
    path = f"sources/negative-{order['work_order_id']}.json"
    write_json(rt.root / path, review)
    return observe(rt, order, "review_returned", actor=order["reviewer"]["identity"], evidence=path)


@pytest.mark.parametrize("change", ["evidence_drift", "unrelated_reopen"])
def test_review_fix_negative_review_survives_drift_and_generation(workshop, change):
    rt = workshop
    context(rt, "G0")
    order, candidate = prepare(rt, "G0")
    event = review_observation(rt, order)
    accept_fixture(rt, order, candidate)
    if change == "evidence_drift": (rt.root / event["evidence"]).write_text("replacement bytes")
    else: rt.reopen("G1", "unrelated next stage retry", version(rt))
    p = progress(rt)
    assert p["gates"][0]["accepted"]["state"] == "verified"
    assert p["gates"][0]["state"] == "blocked"
    assert p["requested_complete"] is False
    assert p["observations"][0]["review"]["verdict"] == "fail"


@pytest.mark.parametrize("fault", ["scores", "blockers"])
@pytest.mark.parametrize("accepted", [False, True])
def test_review_fix_all_acceptance_requirements_affect_progress(workshop, fault, accepted):
    rt = workshop
    context(rt, "G3")
    advance(rt, 2)
    order, candidate = prepare(rt, "G3")
    review_observation(rt, order, fault)
    if accepted: accept_fixture(rt, order, candidate)
    p = progress(rt)
    assert p["gates"][3]["state"] == ("blocked" if accepted else "changes_requested")
    assert p["requested_complete"] is False
    if accepted: assert p["content_review"] == "blocked"


@pytest.mark.parametrize("change", ["evidence_drift", "unrelated_generation"])
def test_review_fix_known_remote_change_survives_invalid_observation(workshop, change):
    rt = workshop
    context(rt)
    order, candidate, receipt = prepared_delivery(rt)
    accept_fixture(rt, order, candidate, receipt)
    operation = next(k for k, op in rt.status()["deliveries"].items() if op["surface"] == "html")
    (rt.root / "sources/changed-target.txt").write_text("Observed changed target")
    event = observe(rt, order, "delivery_result", actor="fixture-controller", operation_id=operation,
                    result="changed", target_revision="saved-2", evidence="sources/changed-target.txt")
    if change == "evidence_drift": (rt.root / event["evidence"]).write_text("replaced observation")
    else: rt.reopen("G4", "new delivery assessment", version(rt))
    p = progress(rt)
    target = next(t for t in p["targets"] if t["surface"] == "html")
    assert target["remote_freshness"] == "changed"
    assert p["gates"][4]["state"] == "stale"
    assert p["requested_complete"] is False
    assert p["gates"][3]["state"] == "verified"


def test_review_fix_markdown_escapes_policy_labels(workshop, runtime):
    rt = workshop
    policy = rt.policy()
    payload = '<img src=x onerror=alert(1)> [target](javascript:alert%281%29)'
    policy["delivery_targets"][0]["surface"] = payload
    path = write_json(rt.root / "sources/policy.json", policy)
    rt.reopen("G0", "fixture policy", version(rt), path)
    rendered = runtime.render_progress(progress(rt), "markdown")
    assert payload not in rendered
    assert "Target &lt;img" in rendered
    assert "Target &lt;img src=x onerror=alert&#40;1&#41;&gt; &#91;target&#93;" in rendered


def test_review_fix_sealed_answer_replaces_inherited_question(workshop):
    rt = workshop
    context(rt, "G1")
    order, candidate = prepare(rt, "G0")
    question = {"id": "U1", "blocking": True, "in_scope": True, "status": "deferred",
                "evidence_standard": "confirmed appetite", "evidence": [], "decision_id": None,
                "dependency_evidence": [], "details": {"question": "What appetite?", "respondent": "owner"}}
    write_json(candidate / "questions.json", [question])
    accept_fixture(rt, order, candidate)
    order, candidate = prepare(rt, "G1")
    question.update(status="answered", evidence=["evidence.txt"])
    write_json(candidate / "questions.json", [question])
    rt.seal(order["work_order_id"], version(rt))
    p = progress(rt)
    assert p["gates"][1]["state"] == "review_pending"
    assert p["current"]["blockers"] == []
    assert p["requested_complete"] is False
    assert p["registers"]["questions"][0]["status"] == "deferred"  # accepted history remains intact


def test_review_fix_late_stop_does_not_override_current_attempt(workshop):
    rt = workshop
    context(rt)
    old, candidate = prepare(rt, "G0")
    observe(rt, old, observed_at="2026-09-18T11:55:00Z")
    accept_fixture(rt, old, candidate)
    current, _ = prepare(rt, "G1")
    observe(rt, current, observed_at="2026-09-18T11:58:00Z")
    observe(rt, old, "stopped", observed_at="2026-09-18T11:59:00Z")
    p = progress(rt)
    assert p["activity"]["state"] == "last_observed_active"
    assert p["activity"]["work_order_id"] == current["work_order_id"]
    assert p["observations"][-1]["record"]["kind"] == "stopped"


def test_review_fix_review_return_ends_started_activity(workshop):
    rt = workshop
    order, _ = prepare(rt, "G0")
    observe(rt, order)
    review_observation(rt, order)
    assert progress(rt)["activity"]["state"] == "review_returned"


def test_review_fix_new_assessment_resolves_only_its_subject(workshop):
    rt = workshop
    context(rt, "G0")
    order, candidate = prepare(rt, "G0")
    event = review_observation(rt, order)
    old, _ = accept_fixture(rt, order, candidate)
    (rt.root / event["evidence"]).write_text("lost external evidence")
    rt.reopen("G0", "resolve conflicting assessment with new attempt", version(rt))
    order, candidate = prepare(rt, "G0", "reassessed")
    accept_fixture(rt, order, candidate)
    p = progress(rt)
    assert p["requested_complete"] is True
    assert p["observations"][0]["review"]["verdict"] == "fail"
    assert rt.snapshot(old["snapshot"])["receipt"]["verdict"] == "pass"
    assert p["invalid_observations"][0]["event_id"] == event["event_id"]


@pytest.mark.parametrize("resolution", ["unrelated_update", "verified_readback", "unchanged_observation", "invalid_unchanged"])
def test_review_fix_target_negative_requires_applicable_reconciliation(workshop, resolution):
    rt = workshop
    context(rt)
    order, candidate, receipt = prepared_delivery(rt)
    accept_fixture(rt, order, candidate, receipt)
    operation_id, operation = next((k, op) for k, op in rt.status()["deliveries"].items() if op["surface"] == "html")
    (rt.root / "sources/negative-target.txt").write_text("changed target observation")
    negative = observe(rt, order, "delivery_result", actor="fixture-controller", operation_id=operation_id,
                       result="changed", target_revision="saved-2", evidence="sources/negative-target.txt",
                       observed_at="2026-09-18T11:58:00Z")
    (rt.root / negative["evidence"]).write_text("changed evidence must not clear negative")
    if resolution in ("verified_readback", "unrelated_update"):
        rt.reopen("G4", "reconcile saved target", version(rt))
        record = {**operation["record"], "revision": "saved-2",
                  "evidence": {role: item["path"] for role, item in operation["record"]["evidence"].items()}}
        if resolution == "verified_readback": record["observed_at"] = "2026-09-18T11:59:00Z"
        rt.delivery_record(operation_id, record, version(rt))
    else:
        (rt.root / "sources/new-read.txt").write_text("observed restoration to saved-1")
        event = observe(rt, order, "delivery_result", actor="fixture-controller", operation_id=operation_id,
                        result="unchanged", target_revision="saved-1", evidence="sources/new-read.txt")
        if resolution == "invalid_unchanged": (rt.root / event["evidence"]).write_text("corrupt new observation")
    p = progress(rt)
    target = next(t for t in p["targets"] if t["surface"] == "html")
    unresolved = resolution in ("unrelated_update", "invalid_unchanged")
    assert bool(target["unresolved_observations"]) is unresolved
    assert (target["remote_freshness"] == "changed") is unresolved
    if unresolved:
        assert target["observation_integrity"] == "stale"
        assert p["requested_complete"] is False
    assert p["gates"][3]["state"] == "verified"
    assert any(e["record"]["event_id"] == negative["event_id"] for e in p["observations"])


@pytest.mark.parametrize("evidence_drift", [False, True])
def test_summary_fix_diagram_conflict_cannot_claim_visual_readiness(workshop, runtime, evidence_drift):
    rt = workshop
    context(rt, "G3")
    advance(rt, 2)
    order, candidate = prepare(rt, "G3")
    seal = rt.seal(order["work_order_id"], version(rt))
    review = fake_receipt(rt, order, seal)
    review["assessments"]["diagrams_visual"]["outcome"] = "fail"
    path = "sources/diagram-failure.json"
    write_json(rt.root / path, review)
    observe(rt, order, "review_returned", actor=order["reviewer"]["identity"], evidence=path)
    accept_fixture(rt, order, candidate)
    if evidence_drift: (rt.root / path).write_text("replaced failed-review evidence")
    p = progress(rt)
    assert p["gates"][3]["state"] == p["content_review"] == p["visual_review"]["local_diagrams"] == "blocked"
    assert p["gates"][3]["accepted"]["state"] == "verified"  # historical receipt retained
    for fmt in ("html", "markdown"):
        assert "local diagrams: verified" not in runtime.render_progress(p, fmt)
        assert "local diagrams: blocked" in runtime.render_progress(p, fmt)


@pytest.mark.parametrize("terminal", ["stopped", "review_returned", "held"])
@pytest.mark.parametrize("fault", ["changed", "missing"])
def test_summary_fix_invalid_later_event_never_resurrects_started(workshop, terminal, fault):
    rt = workshop
    order, _ = prepare(rt, "G0")
    observe(rt, order, observed_at="2026-09-18T11:55:00Z")
    evidence = "sources/terminal.json"
    fields = {}
    if terminal == "review_returned":
        seal = rt.seal(order["work_order_id"], version(rt))
        review = fake_receipt(rt, order, seal)
        review["verdict"] = "fail"
        write_json(rt.root / evidence, review)
        fields["actor"] = order["reviewer"]["identity"]
    else:
        (rt.root / evidence).write_text("host-observed terminal/hold")
        if terminal == "held":
            fields.update(hold_type="prerequisite", reason="Access revoked", needed="Access",
                          respondent=None, next_action="Restore access")
    event = observe(rt, order, terminal, evidence=evidence, **fields)
    assert progress(rt)["activity"]["state"] == terminal
    if fault == "missing": (rt.root / evidence).unlink()
    else: (rt.root / evidence).write_text("replaced observation bytes")
    p = progress(rt)
    assert p["gates"][0]["state"] == "stale"
    assert p["activity"]["state"] in ("unknown", "stale")
    assert p["activity"]["observed_at"] == event["observed_at"]
    assert p["observations"][-1]["record"] == event


@pytest.mark.parametrize("scope", ["G0", "G3"])
def test_summary_fix_context_drift_requires_revalidation_not_finish(workshop, runtime, scope):
    rt = workshop
    evidence = "sources/scope-only.txt"
    (rt.root / evidence).write_text("scope and provenance independent of gate inputs")
    rt.progress_context({"name": "Scope drift fixture", "evidence_mode": "simulated", "requested_stop": scope,
                         "observed_at": "2026-09-18T10:00:00Z", "investment_appetite": "unknown",
                         "evidence": evidence}, version(rt))
    advance(rt, int(scope[1]))
    assert progress(rt)["requested_complete"] is True
    (rt.root / evidence).write_text("changed context")
    p = progress(rt)
    assert p["requested_complete"] is False
    assert p["evidence"]["mode"] == "unknown"
    assert "revalidat" in p["current"]["next_action"].lower()
    assert p["content_review"] != "verified"
    assert p["visual_review"]["local_diagrams"] != "verified"
    for fmt in ("html", "markdown"):
        rendered = runtime.render_progress(p, fmt)
        assert "requested finish" not in rendered
        assert "Requested stopping point reached" not in rendered


@pytest.mark.parametrize("stop", ["G0", "G1", "G2", "G3"])
def test_summary_fix_readiness_invariants_at_each_requested_stop(workshop, stop):
    rt = workshop
    context(rt, stop)
    advance(rt, int(stop[1]))
    p = progress(rt)
    for summary in (p["content_review"], p["visual_review"]["local_diagrams"]):
        assert summary == p["gates"][3]["state"]
    assert p["requested_complete"] is True
    assert all(g["state"] == "verified" for g in p["gates"] if g["applicable"])
