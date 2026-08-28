from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from core_prompts_eval.contracts import ContractError, artifact_hash, validate_goal_contract, validate_topology
from core_prompts_eval.topology import compile_topology


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals/history/batman/e602e19"


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _historical(path: str) -> Path:
    return HISTORY / path


def _historical_json(path: str) -> dict:
    return json.loads(_historical(path).read_text(encoding="utf-8"))


def _historical_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in _historical(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _historical_score_case(case: dict, trace: dict) -> dict:
    scorer_path = _historical("src/core_prompts_eval/scorers/batman.py")
    namespace = {
        "__builtins__": __builtins__,
        "__file__": str(scorer_path),
        "__name__": "historical_batman_scorer",
    }
    code = compile(scorer_path.read_text(encoding="utf-8"), str(scorer_path), "exec")
    exec(code, namespace)
    return namespace["score_case"](case, trace)


def test_batman_evaluation_assets_satisfy_public_schemas() -> None:
    case_schema = _json("evals/schemas/batman-public-case.schema.json")
    for case in _historical_jsonl("evals/cases/public/batman/core.jsonl"):
        jsonschema.validate(case, case_schema)
    for artifact, schema in (
        ("evals/reviews/batman.json", "evals/schemas/capability-topology-review.schema.json"),
        ("evals/mutations/batman.json", "evals/schemas/capability-mutation-inventory.schema.json"),
        ("evals/preregistrations/batman-promotion.json", "evals/schemas/capability-preregistration.schema.json"),
    ):
        jsonschema.validate(_historical_json(artifact), _json(schema))


def test_batman_goal_contract_is_reviewed_and_bound_to_frozen_revisions() -> None:
    contract = _historical_json("evals/contracts/batman.json")

    validate_goal_contract(contract)
    assert contract["review_status"] == "human_reviewed"
    assert contract["baseline"] == {
        "commit": "22eeab3cb5018fea46bdcc6cf67514dfdd19eb68",
        "ssot_sha256": "ac7e2684d99dc6a0267d785d1a6751a742e39e74ce3853a9877f98051690b3f2",
    }
    assert contract["candidate"] == {
        "commit": "e602e19c757b7e0c9ac81fc9f89730ecdf3ba237",
        "ssot_sha256": "3f649676d77fad3ef73e068bd0b8544c7511b696dd2511b73b2835f136da8ca1",
    }
    assert contract["change_class"] == "authority-impact"
    assert contract["evaluation_profile"] == "promotion"
    assert contract["cost_latency_limits"]["hard_raw_token_cap"] == 5_000_000
    assert contract["runtime_envelope"]["required_cells"]
    assert contract["runtime_envelope"]["status"] == "preregistered"
    assert contract["primary_outcome"]["threshold"] != "human_review_required"


def test_batman_review_overlay_closes_all_normative_coverage_deterministically() -> None:
    frozen_ssot = _historical("ssot/batman.md")
    first = compile_topology(frozen_ssot)
    second = compile_topology(frozen_ssot)

    assert first == second
    validate_topology(first)
    assert first["review_status"] == "human_reviewed"
    assert first["known_ambiguities"] == []
    assert first["normative_clause_coverage"] == {"total": 53, "mapped": 45, "waived": 8}
    assert len(first["risk_tiers"]["critical"]) >= 10
    assert all(clause["mapped_to"] or clause.get("waiver") for clause in first["protected_invariants"])
    assert artifact_hash(frozen_ssot) == first["ssot_sha256"]


def test_batman_review_overlay_fails_closed_when_ssot_hash_is_stale(tmp_path: Path) -> None:
    ssot_dir = tmp_path / "ssot"
    review_dir = tmp_path / "evals" / "reviews"
    ssot_dir.mkdir(parents=True)
    review_dir.mkdir(parents=True)
    (ssot_dir / "batman.md").write_text(_historical("ssot/batman.md").read_text(encoding="utf-8") + "\n", encoding="utf-8")
    (review_dir / "batman.json").write_text(_historical("evals/reviews/batman.json").read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(ContractError, match="review overlay SSOT hash is stale"):
        compile_topology(ssot_dir / "batman.md")


def test_batman_public_dataset_has_unique_cases_and_complete_clause_mapping() -> None:
    cases = _historical_jsonl("evals/cases/public/batman/core.jsonl")
    topology = compile_topology(_historical("ssot/batman.md"))
    mapped_ids = {clause_id for case in cases for clause_id in case["clause_ids"]}
    expected_mapped = {clause["id"] for clause in topology["protected_invariants"] if clause["mapped_to"]}
    case_ids = {case["id"] for case in cases}

    assert len(cases) == 25
    assert len({case["id"] for case in cases}) == 25
    assert all(case["id"].startswith("BAT-PUB-") for case in cases)
    assert all(case["risk"] in {"critical", "high", "standard"} for case in cases)
    assert mapped_ids == expected_mapped
    assert all(_historical(case["fixture"]).is_file() for case in cases)
    assert all(set(clause["mapped_to"]) <= case_ids for clause in topology["protected_invariants"])


def test_every_batman_public_gold_microflow_passes_its_deterministic_oracle() -> None:
    for case in _historical_jsonl("evals/cases/public/batman/core.jsonl"):
        fixture = _historical_json(case["fixture"])
        score = _historical_score_case(case, fixture["gold_trace"])
        assert score["passed"] is True, (case["id"], score)
        assert score["model_calls"] == 0


def test_batman_mutation_inventory_enforces_critical_and_overall_kill_bars() -> None:
    inventory = _historical_json("evals/mutations/batman.json")
    mutation_ids = {mutation["id"] for mutation in inventory["mutations"]}
    case_ids = {case["id"] for case in _historical_jsonl("evals/cases/public/batman/core.jsonl")}

    assert len(inventory["mutations"]) >= 20
    assert len(mutation_ids) == len(inventory["mutations"])
    assert set(inventory["critical_mutation_ids"]) <= mutation_ids
    assert len(inventory["critical_mutation_ids"]) >= 10
    assert inventory["promotion_thresholds"] == {
        "critical_mutant_kill_rate": 1.0,
        "overall_mutant_kill_rate_minimum": 0.95,
    }
    assert all(mutation["killed_by"] for mutation in inventory["mutations"])
    assert all(set(mutation["killed_by"]) <= case_ids for mutation in inventory["mutations"])


def test_batman_deterministic_scorer_accepts_gold_and_rejects_mutated_trace() -> None:
    case = _historical_jsonl("evals/cases/public/batman/core.jsonl")[0]
    fixture = _historical_json(case["fixture"])

    passing = _historical_score_case(case, fixture["gold_trace"])
    failing = _historical_score_case(case, fixture["mutated_traces"][0])

    assert passing["passed"] is True
    assert passing["score"] == 1.0
    assert failing["passed"] is False
    assert failing["score"] < 1.0
    assert failing["failed_checks"]


def test_batman_preregistration_is_blind_paired_and_has_no_favorable_early_stop() -> None:
    prereg = _historical_json("evals/preregistrations/batman-promotion.json")

    assert prereg["status"] == "preregistered_not_run"
    assert prereg["baseline_commit"] == "22eeab3cb5018fea46bdcc6cf67514dfdd19eb68"
    assert prereg["candidate_commit"] == "e602e19c757b7e0c9ac81fc9f89730ecdf3ba237"
    assert prereg["trial_design"]["paired"] is True
    assert prereg["trial_design"]["blind"] is True
    assert prereg["trial_design"]["repetitions_per_case_per_cell"] >= 3
    assert prereg["statistics"]["multiple_comparison_correction"] == "holm"
    assert prereg["statistics"]["interval_method"] == "paired_bootstrap"
    assert prereg["stopping_rule"]["favorable_early_stop_allowed"] is False
    assert sum(prereg["token_allocation"].values()) <= 5_000_000
    assert prereg["promotion_allowed_without_run"] is False


def test_batman_baseline_candidate_mapping_names_material_behavior_changes() -> None:
    mapping = _historical_json("evals/mappings/batman-baseline-to-candidate.json")

    assert mapping["baseline_commit"] == "22eeab3cb5018fea46bdcc6cf67514dfdd19eb68"
    assert mapping["candidate_commit"] == "e602e19c757b7e0c9ac81fc9f89730ecdf3ba237"
    classes = {change["class"] for change in mapping["material_changes"]}
    assert {"subagent_implementation", "milestone_backpressure", "progress_reporting", "portability", "mentor_retirement"} <= classes
    assert mapping["behavioral_claim"] == "pending_execution"


def test_current_batman_contract_and_topology_are_structural_drafts() -> None:
    contract = _json("evals/contracts/batman.json")
    topology = compile_topology(ROOT / "ssot" / "batman.md")

    validate_goal_contract(contract)
    validate_topology(topology)
    assert contract["review_status"] == "draft"
    assert contract["primary_outcome"]["threshold"] == "human_review_required"
    assert contract["runtime_envelope"]["status"] == "unresolved"
    assert topology["review_status"] == "draft"
    assert topology["known_ambiguities"] == []
    assert topology["normative_clause_coverage"] == {"total": 55, "mapped": 0, "waived": 0}
    assert topology["ssot_sha256"] == artifact_hash(ROOT / "ssot" / "batman.md")
