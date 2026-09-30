"""Mechanical shaping-loop checks. Receipts and source material are FAKE fixtures."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

import pytest

from test_shaping_runtime import (
    accept_fixture, advance, fake_receipt, prepare, runtime, version, workshop, write_json,
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def loop_policy(rt):
    policy = deepcopy(rt.policy())
    policy["shaping_loop"] = True
    for gate, name in (("G2", "research-coverage.json"), ("G3", "shape-set.json")):
        if name not in policy["gates"][gate]["required_outputs"]:
            policy["gates"][gate]["required_outputs"].append(name)
    path = write_json(rt.root / "sources/policy.json", policy)
    rt.reopen("G0", "FAKE fixture enables mechanical shaping loop", version(rt), path)
    return rt


def failed_g3_review(rt, order, candidate, *, score2=False, semantic_failure=False):
    seal = rt.seal(order["work_order_id"], version(rt))
    receipt = fake_receipt(rt, order, seal)
    receipt["verdict"] = "fail"
    receipt["assessments"]["rubric_assessment"]["outcome"] = "fail"
    if semantic_failure:
        receipt["assessments"]["workstreams_proof"]["outcome"] = "fail"
    for item in receipt["scores"]["dimensions"].values():
        item["score"] = 4
    receipt["scores"]["dimensions"]["cost"]["score"] = 3
    receipt["scores"]["dimensions"]["confidence"]["score"] = 3
    dimensions = receipt["scores"]["dimensions"]
    team = ("simplicity", "testability", "security", "architecture", "cost", "feasibility", "confidence")
    pitch = ("problem_clarity", "appetite_fit", "solution_sharpness", "contract_quality", "boundary_discipline")
    receipt["scores"]["team_mean"] = sum(dimensions[name]["score"] for name in team) / 7
    receipt["scores"]["pitch_mean"] = sum(dimensions[name]["score"] for name in pitch) / 5
    receipt["scores"]["overall"] = sum(item["score"] for item in dimensions.values()) / 12
    if score2:
        receipt["scores"]["dimensions"]["simplicity"]["score"] = 2
        receipt["scores"]["team_mean"] = sum(dimensions[name]["score"] for name in team) / 7
        receipt["scores"]["pitch_mean"] = sum(dimensions[name]["score"] for name in pitch) / 5
        receipt["scores"]["overall"] = sum(item["score"] for item in dimensions.values()) / 12
    path = write_json(rt.root / "reviews/fake-G3-failure.json", receipt)
    with pytest.raises(rt.Hold):
        rt.accept(path, version(rt))
    record = {
        "event_id": f"fake-review-{order['work_order_id']}", "run_id": order["run_id"],
        "version": version(rt), "generation": order["generation"],
        "work_order_id": order["work_order_id"], "kind": "review_returned",
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "actor": order["reviewer"]["identity"],
        "evidence": "reviews/fake-G3-failure.json",
    }
    rt.observe(record, version(rt))
    return receipt


def test_floor_only_retry_is_blocked_before_prepare_pointer_mutation(workshop):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "failed")
    failed_g3_review(rt, order, candidate)
    (candidate / "pitch.md").write_text("FAKE revised prose cannot create an opened fact\n", encoding="utf-8")
    rt.reopen("G3", "FAKE fixture preserves failed review history", version(rt))

    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Hold, match="floor-only G3 retry blocked"):
        prepare(rt, "G3", "repeat")
    assert (rt.root / "state/run.json").read_bytes() == before

    # A path rename with identical source bytes and locators is not a new fact.
    rt.reopen("G2", "FAKE fixture tests renamed source identity", version(rt))
    original = rt.root / "sources/original.txt"
    alias = rt.root / "sources/renamed-original.txt"
    alias.write_bytes(original.read_bytes())
    assignment = rt.root / "sources/added-reviewer-assignment.txt"
    assignment.write_text("FAKE additional reviewer assignment metadata\n", encoding="utf-8")
    retry, candidate = prepare(
        rt, "G2", "renamed",
        extra_inputs=["sources/renamed-original.txt", "sources/added-reviewer-assignment.txt"],
        assignment_evidence="sources/added-reviewer-assignment.txt")
    coverage = json.loads((candidate / "research-coverage.json").read_text())
    coverage["opened"].append({"path": "sources/renamed-original.txt",
                               "sha256": sha(alias.read_bytes()),
                               "locators": ["1:1"]})
    coverage["opened"].append({"path": "sources/added-reviewer-assignment.txt",
                               "sha256": sha(assignment.read_bytes()),
                               "locators": ["1:1"]})
    write_json(candidate / "research-coverage.json", coverage)
    accept_fixture(rt, retry, candidate)
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Hold, match="floor-only G3 retry blocked"):
        prepare(rt, "G3", "renamed-repeat")
    assert (rt.root / "state/run.json").read_bytes() == before


def test_new_opened_source_fact_allows_fresh_prepare_after_preserved_failure(workshop):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "failed")
    failed_g3_review(rt, order, candidate)
    rt.reopen("G2", "FAKE fixture adds source evidence after review return", version(rt))

    new_source = rt.root / "sources/new-observation.txt"
    new_source.write_text("FAKE additional source observation\n", encoding="utf-8")
    order, candidate = prepare(rt, "G2", "new-fact", extra_inputs=["sources/new-observation.txt"])
    coverage = json.loads((candidate / "research-coverage.json").read_text())
    coverage["opened"].append({"path": "sources/new-observation.txt",
                               "sha256": sha(new_source.read_bytes()),
                               "locators": ["1:1"]})
    write_json(candidate / "research-coverage.json", coverage)
    accept_fixture(rt, order, candidate)

    fresh, candidate = prepare(rt, "G3", "after-new-fact")
    assert fresh["gate"] == "G3"
    # It must actually use the new source; adding an unused source is not clearance.
    shape_set = json.loads((candidate / "shape-set.json").read_text())
    shape_set["claims"][0]["evidence"] = [coverage["opened"][-1]]
    write_json(candidate / "shape-set.json", shape_set)
    rt.seal(fresh["work_order_id"], version(rt))


@pytest.mark.parametrize("failure", ["score2", "semantic"])
def test_other_review_failures_do_not_trigger_floor_only_rule(workshop, failure):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", failure)
    failed_g3_review(rt, order, candidate, score2=failure == "score2",
                     semantic_failure=failure == "semantic")
    rt.reopen("G3", "FAKE fixture retries after non-floor-only failure", version(rt))
    fresh, _ = prepare(rt, "G3", f"{failure}-retry")
    assert fresh["gate"] == "G3"


def test_empty_selection_holds_before_review_and_names_walkaway(workshop):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "no-selection")
    shape_set = json.loads((candidate / "shape-set.json").read_text())
    shape_set["selected_parts"] = []
    shape_set["walk_away_item"] = "FAKE explicit walk-away condition"
    write_json(candidate / "shape-set.json", shape_set)
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Hold, match="FAKE explicit walk-away condition"):
        rt.seal(order["work_order_id"], version(rt))
    assert (rt.root / "state/run.json").read_bytes() == before


def test_missing_opened_fact_routes_claim_back_to_research(workshop):
    rt = loop_policy(workshop)
    advance(rt, 1)
    order, candidate = prepare(rt, "G2", "empty-coverage")
    write_json(candidate / "research-coverage.json", {"schema_version": 1, "opened": []})
    accept_fixture(rt, order, candidate)

    order, candidate = prepare(rt, "G3", "unopened-claim")
    source = "sources/original.txt"
    evidence = {"path": source, "sha256": sha((rt.root / source).read_bytes()),
                "locators": ["1:1"]}
    write_json(candidate / "shape-set.json", {
        "schema_version": 1, "selected_parts": ["fixture-part"],
        "walk_away_item": "FAKE walk-away", "claims": [
            {"id": "existing", "status": "existing", "load_bearing": True,
             "evidence": [evidence], "basis_claims": []}],
    })
    with pytest.raises(rt.Hold, match="return to research.*not opened"):
        rt.seal(order["work_order_id"], version(rt))


def test_proposed_extension_uses_grounded_basis_without_execution_claim(workshop):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "proposed-extension")
    shape_set = json.loads((candidate / "shape-set.json").read_text())
    shape_set["claims"].append({"id": "proposed-write", "status": "proposed_extension",
                                "load_bearing": True, "evidence": [],
                                "basis_claims": ["fixture-existing"]})
    write_json(candidate / "shape-set.json", shape_set)
    seal = rt.seal(order["work_order_id"], version(rt))
    assert seal["subject"]["shape-set.json"] == sha((candidate / "shape-set.json").read_bytes())


def test_sequence_diagram_accepts_gray_actor_and_semantic_color_bands(workshop):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "sequence")
    (candidate / "sequence.mmd").write_text(
        "sequenceDiagram\n participant A as Gray actor\n rect rgb(220, 220, 220)\n"
        "  A->>Reviewer: FAKE semantic color band\n end\n", encoding="utf-8")
    rt.seal(order["work_order_id"], version(rt))


@pytest.mark.parametrize("diagram", [
    "flowchart TD\n A-->B\n",
    "sequenceDiagram\n participant A\n alt condition\n  A->>B: FAKE\n end\n",
    "sequenceDiagram\n participant A\n A->>B: FAKE\n else condition\n",
])
def test_unsupported_sequence_artifacts_are_rejected(workshop, diagram):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "unsupported")
    (candidate / "sequence.mmd").write_text(diagram, encoding="utf-8")
    match = "sequenceDiagram" if diagram.startswith("flowchart") else "alt/else"
    with pytest.raises(rt.Hold, match=match):
        rt.seal(order["work_order_id"], version(rt))


def research_with_new_fact_after_average_failure(rt):
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "failed")
    failed_g3_review(rt, order, candidate)
    rt.reopen("G2", "FAKE acquire a new fact", version(rt))
    source = rt.root / "sources/new-fact.txt"
    source.write_text("FAKE new behavior observation\n")
    evidence = {"path": "sources/new-fact.txt", "sha256": sha(source.read_bytes()), "locators": ["1:1"]}
    order, candidate = prepare(rt, "G2", "new", extra_inputs=[evidence["path"]])
    coverage = json.loads((candidate / "research-coverage.json").read_text())
    old_evidence = coverage["opened"][0]
    coverage["opened"].append(evidence)
    write_json(candidate / "research-coverage.json", coverage)
    accept_fixture(rt, order, candidate)
    return old_evidence, evidence


def test_unrelated_new_fact_cannot_dispatch_old_basis(workshop):
    rt = loop_policy(workshop)
    old, _ = research_with_new_fact_after_average_failure(rt)
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Hold, match="newly opened evidence must be included"):
        prepare(rt, "G3", "old-basis", shape_basis=[old])
    assert (rt.root / "state/run.json").read_bytes() == before


def test_declared_but_unused_new_fact_cannot_seal_repeat(workshop):
    rt = loop_policy(workshop)
    old, new = research_with_new_fact_after_average_failure(rt)
    order, candidate = prepare(rt, "G3", "unused", shape_basis=[old, new])
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Hold, match="selected claim basis does not use"):
        rt.seal(order["work_order_id"], version(rt))
    assert (rt.root / "state/run.json").read_bytes() == before


def test_placeholder_selected_part_without_claim_is_unscorable(workshop):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "placeholder")
    record = json.loads((candidate / "shape-set.json").read_text())
    record.update(selected_parts=["placeholder"], claims=[])
    write_json(candidate / "shape-set.json", record)
    with pytest.raises(rt.Hold, match="no corresponding shape claim"):
        rt.seal(order["work_order_id"], version(rt))


@pytest.mark.parametrize("locator", ["line 1", "01:1", "1:2", "2:1"])
def test_coverage_locator_is_verified_against_source(workshop, locator):
    rt = loop_policy(workshop)
    advance(rt, 1)
    order, candidate = prepare(rt, "G2", "invalid-locator")
    coverage = json.loads((candidate / "research-coverage.json").read_text())
    coverage["opened"][0]["locators"] = [locator]
    write_json(candidate / "research-coverage.json", coverage)
    with pytest.raises(rt.Hold, match="locator"):
        rt.seal(order["work_order_id"], version(rt))


def test_split_ranges_do_not_manufacture_new_fact(workshop):
    rt = loop_policy(workshop)
    (rt.root / "sources/original.txt").write_text("FAKE first fact\nFAKE second fact\n")
    advance(rt, 1)
    order, candidate = prepare(rt, "G2", "whole-range")
    coverage = json.loads((candidate / "research-coverage.json").read_text())
    coverage["opened"][0]["locators"] = ["1:2"]
    write_json(candidate / "research-coverage.json", coverage)
    accept_fixture(rt, order, candidate)
    order, candidate = prepare(rt, "G3", "failed")
    failed_g3_review(rt, order, candidate)
    rt.reopen("G2", "FAKE splitting identical inspected lines", version(rt))
    order, candidate = prepare(rt, "G2", "split-range")
    coverage["opened"][0]["locators"] = ["1:1", "2:2"]
    write_json(candidate / "research-coverage.json", coverage)
    accept_fixture(rt, order, candidate)
    with pytest.raises(rt.Hold, match="floor-only G3 retry blocked"):
        prepare(rt, "G3", "split-retry")


def test_bookkeeping_cannot_ground_product_claims(workshop):
    rt = loop_policy(workshop)
    advance(rt, 1)
    order, candidate = prepare(rt, "G2", "assignment")
    path = "sources/assignment.txt"
    evidence = {"path": path, "sha256": sha((rt.root / path).read_bytes()), "locators": ["1:1"]}
    coverage = json.loads((candidate / "research-coverage.json").read_text())
    coverage["opened"].append(evidence)
    write_json(candidate / "research-coverage.json", coverage)
    accept_fixture(rt, order, candidate)
    with pytest.raises(rt.Hold, match="cannot use policy"):
        prepare(rt, "G3", "assignment-basis", shape_basis=[evidence])


def test_real_resources_module_is_not_bookkeeping(workshop):
    rt = loop_policy(workshop)
    advance(rt, 1)
    source = rt.root / "sources/resources/template.txt"
    source.parent.mkdir()
    source.write_text("FAKE actual product template contract\n")
    evidence = {"path": "sources/resources/template.txt", "sha256": sha(source.read_bytes()), "locators": ["1:1"]}
    order, candidate = prepare(rt, "G2", "resources-module", extra_inputs=[evidence["path"]])
    coverage = json.loads((candidate / "research-coverage.json").read_text())
    coverage["opened"].append(evidence)
    write_json(candidate / "research-coverage.json", coverage)
    accept_fixture(rt, order, candidate)
    order, candidate = prepare(rt, "G3", "template", shape_basis=[evidence])
    record = json.loads((candidate / "shape-set.json").read_text())
    record["claims"][0]["evidence"] = [evidence]
    write_json(candidate / "shape-set.json", record)
    rt.seal(order["work_order_id"], version(rt))


def test_malformed_failure_history_enters_recovery_before_dispatch(workshop):
    rt = loop_policy(workshop)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "failed")
    failed_g3_review(rt, order, candidate)
    state = rt._load()
    state["observations"][-1]["review"]["scores"]["dimensions"].pop("cost")
    rt._commit(state, version(rt))  # Deliberate corrupted-journal control.
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(rt.Recovery, match="recorded G3 review_returned"):
        prepare(rt, "G3", "corrupt-history")
    assert (rt.root / "state/run.json").read_bytes() == before


def test_current_profile_cannot_disable_its_loop_checks(runtime, workshop):
    policy = deepcopy(workshop.policy())
    policy.update(policy_id="shaping-gates.v3+rubric.v4", shaping_loop=False)
    with pytest.raises(runtime.Hold, match="requires shaping_loop=true"):
        runtime.validate_policy(policy)
