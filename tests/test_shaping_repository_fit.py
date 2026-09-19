"""Repository-fit policy enforcement through the real Runtime.

All source material and semantic receipts are explicitly FAKE fixtures. These
tests prove mechanical gate enforcement, not the truth of a repository-fit
assessment, reviewer independence, or rubric calibration.
"""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from test_shaping_runtime import (
    RESOURCE, accept_fixture, advance, fake_receipt, prepare,
    runtime, version, workshop, write_json,
)


CURRENT = "shaping-gates.v2+rubric.v3"
LEGACY = "shaping-gates.v1+rubric.v2"
FIT = [("G2", "existing_capability_evidence"), ("G3", "architecture_fit")]
ROOT = Path(__file__).resolve().parents[1]
SHAPING_SKILLS = (
    "engos-design-shaping",
    "engos-design-frame-from-vague",
    "engos-quality-shaping-gate",
    "engos-delivery-diagram-contract-artifacts",
    "engos-delivery-artifact-embed",
    "engos-audit-pitch-review",
)
APPIAN_READER_EXAMPLE_MARKERS = (
    "lcp-mcp-server", "AE site", "AIP wiring", "createInterface",
    "broken SAIL", "Composer and Agents",
)


def test_direct_specialist_route_delivers_question_budget_and_decision_guidance():
    from intent_pipeline.capability_resources import load_resource_bundle
    root = RESOURCE.parent / 'engos-design-shaping'
    files = {item['path'] for item in load_resource_bundle(root, 'architecture-fit')['resources']}
    assert {'architecture-fit.md', 'questions.md', 'decisions.md'} <= files
    frame_files = {item['path'] for item in load_resource_bundle(root, 'frame')['resources']}
    assert 'architecture-fit.md' not in frame_files
    assert 'code-scan.md' not in frame_files
    assert 'repository-discovery.md' not in frame_files


def test_code_scan_route_loads_runtime_repository_discovery():
    from intent_pipeline.capability_resources import load_resource_bundle
    root = RESOURCE.parent / "engos-design-shaping"
    files = {item["path"] for item in load_resource_bundle(root, "code-scan")["resources"]}
    assert {"code-scan.md", "repository-discovery.md", "sources.md"} <= files


def test_appian_worked_example_is_reader_docs_only():
    skill = (ROOT / "ssot/engos-audit-pitch-review.md").read_text()
    docs = (ROOT / "docs/EXAMPLES.md").read_text()
    for marker in APPIAN_READER_EXAMPLE_MARKERS:
        assert marker not in skill, f"reader example leaked into skill: {marker!r}"
        assert marker in docs, f"reader example not retained in docs: {marker!r}"


def test_shipped_shaping_skills_have_no_task_local_machine_paths():
    for slug in SHAPING_SKILLS:
        paths = [ROOT / "ssot" / f"{slug}.md"]
        resource_root = ROOT / "sources" / "capability-resources" / slug
        if resource_root.is_dir():
            paths.extend(path for path in resource_root.rglob("*") if path.is_file())
        text = "\n".join(path.read_text(errors="replace") for path in paths)
        assert "/Users/medhat.galal/" not in text
        assert "/private/tmp/engos-shaping-research-" not in text


def stage_policy(rt, legacy=False):
    policy = json.loads((RESOURCE / "schemas/policy.example.json").read_text())
    if legacy:
        policy["policy_id"] = LEGACY
        for gate, predicate in FIT:
            policy["gates"][gate]["predicates"] = [
                p for p in policy["gates"][gate]["predicates"] if p != predicate
            ]
    for role, name in (("gates", "gates.md"), ("rubric", "rubrics.md")):
        content = (f"FAKE pinned legacy {role}; no repository-fit assessment\n"
                   if legacy else (RESOURCE / "references" / name).read_text())
        (rt.root / policy["references"][role]).write_text(content)
    return write_json(rt.root / "sources/policy.json", policy)


@pytest.fixture
def current(workshop):
    rt = workshop
    path = stage_policy(rt)
    rt.reopen("G0", "FAKE fixture adopts shipped current policy", version(rt), path)
    return rt


def review_at(rt, gate, suffix="a", extra_inputs=()):
    advance(rt, int(gate[1]) - 1)
    order, candidate = prepare(rt, gate, suffix, extra_inputs=extra_inputs)
    seal = rt.seal(order["work_order_id"], version(rt))
    return order, candidate, fake_receipt(rt, order, seal)


@pytest.mark.parametrize("gate,predicate", FIT)
def test_current_policy_emits_and_accepts_repository_fit_predicates(current, gate, predicate):
    rt = current
    assert rt.policy()["policy_id"] == CURRENT
    assert rt.policy()["references"] == {
        "gates": "sources/gates.md", "rubric": "sources/rubrics.md",
    }
    order, candidate, receipt = review_at(rt, gate)
    assert predicate in order["required_predicates"]
    assert order["required_outputs"] == [*rt.MIN_OUTPUTS[int(gate[1])],
                                          "questions.json", "decisions.json"]
    result, _ = accept_fixture(rt, order, candidate, receipt)
    snapshot = rt.snapshot(result["snapshot"])
    assert snapshot["receipt"]["assessments"][predicate]["outcome"] == "pass"
    assert snapshot["policy_bindings"] == order["policy_bindings"]
    assert rt.status()["stage"] == gate


@pytest.mark.parametrize("gate,predicate", FIT)
@pytest.mark.parametrize("fault", ["missing", "fail", "unverifiable", "no_evidence", "unknown_evidence"])
def test_repository_fit_assessment_fault_holds_without_mutation(current, gate, predicate, fault):
    rt = current
    _, _, receipt = review_at(rt, gate)
    if fault == "missing":
        receipt["assessments"].pop(predicate, None)
    else:
        assessment = receipt["assessments"].setdefault(predicate, {
            "outcome": "pass", "evidence_ids": ["E1"], "explanation": "FAKE fit review",
        })
        if fault in ("fail", "unverifiable"):
            assessment["outcome"] = fault
        else:
            assessment["evidence_ids"] = [] if fault == "no_evidence" else ["not-observed"]
    path = write_json(rt.root / "fault.json", receipt)
    pointer = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Hold):
        rt.accept(path, version(rt))
    assert (rt.root / "state/run.json").read_bytes() == pointer
    assert rt.status()["stage"] == f"G{int(gate[1]) - 1}"


@pytest.mark.parametrize("disposition", [
    "configuration", "reuse", "extend", "evolve", "replace", "new",
    "intentionally separate", "nontechnical: no material technical scope",
])
def test_passing_review_needs_no_optional_skill_or_positive_reuse_find(current, disposition):
    # Runtime accepts the review's evidence binding; it does NOT judge this prose.
    rt = current
    advance(rt, 1)
    order, candidate = prepare(rt, "G2")
    (candidate / "research-notes.md").write_text(
        "FAKE scoped inspection: fixture sources only; no applicable candidate found.\n"
        "FAKE citation: evidence.txt; coverage: supplied fixture; unknowns: none in scope.\n"
        f"FAKE applicability context: {disposition}.\n"
    )
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    receipt["evidence"]["FIT"] = "research-notes.md"
    receipt["assessments"]["existing_capability_evidence"] = {
        "outcome": "pass", "evidence_ids": ["FIT"],
        "explanation": "FAKE reviewer accepts scoped negative result/applicability reason",
    }
    accept_fixture(rt, order, candidate, receipt)
    order, candidate = prepare(rt, "G3")
    assert order["skill_allowlist"] == ["fixture-only"]
    (candidate / "pitch.md").write_text(
        f"FAKE disposition: {disposition}; rationale and fit: fixture constraints satisfied.\n"
        "FAKE credible alternatives: none applicable; trust/contract effects: none.\n"
        "FAKE migration/owner/rollback/retirement: not applicable to this fixture.\n"
    )
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    receipt["evidence"]["FIT"] = "pitch.md"
    receipt["assessments"]["architecture_fit"] = {
        "outcome": "pass", "evidence_ids": ["FIT"],
        "explanation": "FAKE reviewer accepts disposition/applicability rationale",
    }
    accept_fixture(rt, order, candidate, receipt)
    assert rt.status()["content_ready"] is True


@pytest.mark.parametrize("gate,predicate", FIT)
def test_fit_review_stale_input_holds_then_fresh_attempt_passes(current, gate, predicate):
    rt = current
    source = rt.root / "sources/repository-evidence.txt"
    source.write_text("FAKE repository observation revision 1\n")
    order, candidate, receipt = review_at(rt, gate, extra_inputs=["sources/repository-evidence.txt"])
    assert predicate in order["required_predicates"]
    path = write_json(rt.root / "stale.json", receipt)
    source.write_text("FAKE changed repository observation revision 2\n")
    before = version(rt)
    with pytest.raises(rt.Hold, match="changed dependency"):
        rt.accept(path, before)
    assert version(rt) == before
    rt.reopen(gate, "FAKE repository evidence changed", version(rt))
    with pytest.raises(rt.Hold, match="stale generation"):
        rt.accept(path, version(rt))
    fresh, candidate = prepare(rt, gate, "fresh", extra_inputs=["sources/repository-evidence.txt"])
    assert fresh["input_hashes"] != order["input_hashes"]
    accept_fixture(rt, fresh, candidate)
    assert rt.status()["stage"] == gate


@pytest.mark.parametrize("fault", ["missing_review", "low_architecture", "low_overall"])
def test_repository_fit_does_not_relax_review_or_team_thresholds(current, runtime, fault):
    rt = current
    _, _, receipt = review_at(rt, "G3")
    assert rt.policy()["scoring"]["minimum_dimension"] == 3
    assert rt.policy()["scoring"]["minimum_overall"] == 4
    if fault == "missing_review":
        receipt["independence_confirmed"] = False
    else:
        dimensions = receipt["scores"]["dimensions"]
        if fault == "low_architecture":
            for item in dimensions.values():
                item["score"] = 5
            dimensions["architecture"]["score"] = 2
        else:
            for item in dimensions.values():
                item["score"] = 3
        receipt["scores"].update(
            team_mean=sum(dimensions[d]["score"] for d in runtime.TEAM) / 7,
            pitch_mean=sum(dimensions[d]["score"] for d in runtime.PITCH) / 5,
            overall=sum(d["score"] for d in dimensions.values()) / 12,
        )
    path = write_json(rt.root / "mandatory-hold.json", receipt)
    before = version(rt)
    with pytest.raises(rt.Hold):
        rt.accept(path, before)
    assert version(rt) == before


def test_legacy_runs_retain_pins_without_claiming_new_predicates(workshop):
    rt = workshop
    policy_path = stage_policy(rt, legacy=True)
    rt.reopen("G0", "FAKE legacy policy fixture", version(rt), policy_path)
    advance(rt)
    pins = deepcopy(rt.snapshot(rt.status()["accepted"]["G3"])["policy_bindings"])
    # A later resource package does not mutate an existing run's staged policy.
    assert rt.policy()["policy_id"] == LEGACY
    for gate, predicate in FIT:
        snapshot = rt.snapshot(rt.status()["accepted"][gate])
        assert predicate not in snapshot["receipt"]["assessments"]
        assert predicate not in snapshot["work_order"]["required_predicates"]
        assert snapshot["policy_bindings"] == pins
    assert rt.status()["content_ready"] is True  # Under the pinned legacy policy only.


def test_adopting_current_policy_requires_g0_rebind_and_preserves_history(workshop):
    rt = workshop
    legacy_path = stage_policy(rt, legacy=True)
    rt.reopen("G0", "FAKE legacy run", version(rt), legacy_path)
    advance(rt)
    accepted = dict(rt.status()["accepted"])
    history = {key: (rt.root / f"accepted/{key}.json").read_bytes() for key in accepted.values()}
    old_receipt = rt.root / "receipt-G3-a.json"
    current_path = stage_policy(rt)
    assert rt.status()["content_ready"] is False
    before = version(rt)
    with pytest.raises(rt.Hold, match="policy changes require G0"):
        rt.reopen("G2", "FAKE adoption", before, current_path)
    assert version(rt) == before
    result = rt.reopen("G0", "FAKE explicitly adopt current policy", before, current_path)
    assert result["invalidated"] == accepted
    assert rt.status()["accepted"] == {}
    with pytest.raises(rt.Hold, match="stale accepted result"):
        rt.accept(old_receipt, version(rt))
    for number in range(4):
        order, candidate = prepare(rt, f"G{number}", "current")
        accept_fixture(rt, order, candidate)
    for gate, predicate in FIT:
        snapshot = rt.snapshot(rt.status()["accepted"][gate])
        assert snapshot["receipt"]["assessments"][predicate]["outcome"] == "pass"
        assert snapshot["policy_bindings"] != rt.snapshot(accepted[gate])["policy_bindings"]
    assert rt.policy()["policy_id"] == CURRENT
    assert rt.status()["content_ready"] is True
    for key, original in history.items():
        assert (rt.root / f"accepted/{key}.json").read_bytes() == original
