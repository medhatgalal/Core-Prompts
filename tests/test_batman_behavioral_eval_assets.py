from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import jsonschema

from core_prompts_eval.contracts import (
    ContractError,
    artifact_hash,
    validate_goal_contract,
    validate_topology,
)
from core_prompts_eval.topology import compile_topology

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "evals/history/batman/e602e19"
RETIRED_PUBLIC_IDENTITIES = {"super" + "man"}


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
    exec(code, namespace)  # noqa: S102 - execute the immutable historical scorer under test
    return namespace["score_case"](case, trace)


class BatmanBehavioralEvalAssetsTest(unittest.TestCase):
    def test_evaluation_assets_satisfy_public_schemas(self) -> None:
        case_schema = _json("evals/schemas/batman-public-case.schema.json")
        for case in _historical_jsonl("evals/cases/public/batman/core.jsonl"):
            with self.subTest(case=case["id"]):
                jsonschema.validate(case, case_schema)
        for artifact, schema in (
            ("evals/reviews/batman.json", "evals/schemas/capability-topology-review.schema.json"),
            ("evals/mutations/batman.json", "evals/schemas/capability-mutation-inventory.schema.json"),
            ("evals/preregistrations/batman-promotion.json", "evals/schemas/capability-preregistration.schema.json"),
        ):
            with self.subTest(artifact=artifact):
                jsonschema.validate(_historical_json(artifact), _json(schema))

    def test_goal_contract_is_reviewed_and_bound_to_frozen_revisions(self) -> None:
        contract = _historical_json("evals/contracts/batman.json")

        validate_goal_contract(contract)
        self.assertEqual(contract["review_status"], "human_reviewed")
        self.assertEqual(
            contract["baseline"],
            {
                "commit": "22eeab3cb5018fea46bdcc6cf67514dfdd19eb68",
                "ssot_sha256": "ac7e2684d99dc6a0267d785d1a6751a742e39e74ce3853a9877f98051690b3f2",
            },
        )
        self.assertEqual(
            contract["candidate"],
            {
                "commit": "e602e19c757b7e0c9ac81fc9f89730ecdf3ba237",
                "ssot_sha256": "3f649676d77fad3ef73e068bd0b8544c7511b696dd2511b73b2835f136da8ca1",
            },
        )
        self.assertEqual(contract["change_class"], "authority-impact")
        self.assertEqual(contract["evaluation_profile"], "promotion")
        self.assertEqual(contract["cost_latency_limits"]["hard_raw_token_cap"], 5_000_000)
        self.assertTrue(contract["runtime_envelope"]["required_cells"])
        self.assertEqual(contract["runtime_envelope"]["status"], "preregistered")
        self.assertNotEqual(contract["primary_outcome"]["threshold"], "human_review_required")

    def test_review_overlay_closes_all_normative_coverage_deterministically(self) -> None:
        frozen_ssot = _historical("ssot/batman.md")
        first = compile_topology(frozen_ssot)
        second = compile_topology(frozen_ssot)

        self.assertEqual(first, second)
        validate_topology(first)
        self.assertEqual(first["review_status"], "human_reviewed")
        self.assertEqual(first["known_ambiguities"], [])
        self.assertEqual(first["normative_clause_coverage"], {"total": 53, "mapped": 45, "waived": 8})
        self.assertGreaterEqual(len(first["risk_tiers"]["critical"]), 10)
        self.assertTrue(all(clause["mapped_to"] or clause.get("waiver") for clause in first["protected_invariants"]))
        self.assertEqual(artifact_hash(frozen_ssot), first["ssot_sha256"])

    def test_review_overlay_fails_closed_when_ssot_hash_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ssot_dir = root / "ssot"
            review_dir = root / "evals" / "reviews"
            ssot_dir.mkdir(parents=True)
            review_dir.mkdir(parents=True)
            (ssot_dir / "batman.md").write_text(
                _historical("ssot/batman.md").read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            (review_dir / "batman.json").write_text(
                _historical("evals/reviews/batman.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "review overlay SSOT hash is stale"):
                compile_topology(ssot_dir / "batman.md")

    def test_public_dataset_has_unique_cases_and_complete_clause_mapping(self) -> None:
        cases = _historical_jsonl("evals/cases/public/batman/core.jsonl")
        topology = compile_topology(_historical("ssot/batman.md"))
        mapped_ids = {clause_id for case in cases for clause_id in case["clause_ids"]}
        expected_mapped = {clause["id"] for clause in topology["protected_invariants"] if clause["mapped_to"]}
        case_ids = {case["id"] for case in cases}

        self.assertEqual(len(cases), 25)
        self.assertEqual(len({case["id"] for case in cases}), 25)
        self.assertTrue(all(case["id"].startswith("BAT-PUB-") for case in cases))
        self.assertTrue(all(case["risk"] in {"critical", "high", "standard"} for case in cases))
        self.assertEqual(mapped_ids, expected_mapped)
        self.assertTrue(all(_historical(case["fixture"]).is_file() for case in cases))
        self.assertTrue(all(set(clause["mapped_to"]) <= case_ids for clause in topology["protected_invariants"]))

    def test_every_public_gold_microflow_passes_its_deterministic_oracle(self) -> None:
        for case in _historical_jsonl("evals/cases/public/batman/core.jsonl"):
            with self.subTest(case=case["id"]):
                fixture = _historical_json(case["fixture"])
                score = _historical_score_case(case, fixture["gold_trace"])
                self.assertIs(score["passed"], True, (case["id"], score))
                self.assertEqual(score["model_calls"], 0)

    def test_mutation_inventory_enforces_critical_and_overall_kill_bars(self) -> None:
        inventory = _historical_json("evals/mutations/batman.json")
        mutation_ids = {mutation["id"] for mutation in inventory["mutations"]}
        case_ids = {case["id"] for case in _historical_jsonl("evals/cases/public/batman/core.jsonl")}

        self.assertGreaterEqual(len(inventory["mutations"]), 20)
        self.assertEqual(len(mutation_ids), len(inventory["mutations"]))
        self.assertLessEqual(set(inventory["critical_mutation_ids"]), mutation_ids)
        self.assertGreaterEqual(len(inventory["critical_mutation_ids"]), 10)
        self.assertEqual(
            inventory["promotion_thresholds"],
            {"critical_mutant_kill_rate": 1.0, "overall_mutant_kill_rate_minimum": 0.95},
        )
        self.assertTrue(all(mutation["killed_by"] for mutation in inventory["mutations"]))
        self.assertTrue(all(set(mutation["killed_by"]) <= case_ids for mutation in inventory["mutations"]))

    def test_deterministic_scorer_accepts_gold_and_rejects_mutated_trace(self) -> None:
        case = _historical_jsonl("evals/cases/public/batman/core.jsonl")[0]
        fixture = _historical_json(case["fixture"])

        passing = _historical_score_case(case, fixture["gold_trace"])
        failing = _historical_score_case(case, fixture["mutated_traces"][0])

        self.assertIs(passing["passed"], True)
        self.assertEqual(passing["score"], 1.0)
        self.assertIs(failing["passed"], False)
        self.assertLess(failing["score"], 1.0)
        self.assertTrue(failing["failed_checks"])

    def test_preregistration_is_blind_paired_and_has_no_favorable_early_stop(self) -> None:
        prereg = _historical_json("evals/preregistrations/batman-promotion.json")

        self.assertEqual(prereg["status"], "preregistered_not_run")
        self.assertEqual(prereg["baseline_commit"], "22eeab3cb5018fea46bdcc6cf67514dfdd19eb68")
        self.assertEqual(prereg["candidate_commit"], "e602e19c757b7e0c9ac81fc9f89730ecdf3ba237")
        self.assertIs(prereg["trial_design"]["paired"], True)
        self.assertIs(prereg["trial_design"]["blind"], True)
        self.assertGreaterEqual(prereg["trial_design"]["repetitions_per_case_per_cell"], 3)
        self.assertEqual(prereg["statistics"]["multiple_comparison_correction"], "holm")
        self.assertEqual(prereg["statistics"]["interval_method"], "paired_bootstrap")
        self.assertIs(prereg["stopping_rule"]["favorable_early_stop_allowed"], False)
        self.assertLessEqual(sum(prereg["token_allocation"].values()), 5_000_000)
        self.assertIs(prereg["promotion_allowed_without_run"], False)

    def test_baseline_candidate_mapping_names_material_behavior_changes(self) -> None:
        mapping = _historical_json("evals/mappings/batman-baseline-to-candidate.json")

        self.assertEqual(mapping["baseline_commit"], "22eeab3cb5018fea46bdcc6cf67514dfdd19eb68")
        self.assertEqual(mapping["candidate_commit"], "e602e19c757b7e0c9ac81fc9f89730ecdf3ba237")
        classes = {change["class"] for change in mapping["material_changes"]}
        expected = {
            "subagent_implementation",
            "milestone_backpressure",
            "progress_reporting",
            "portability",
            "mentor_retirement",
        }
        self.assertLessEqual(expected, classes)
        self.assertEqual(mapping["behavioral_claim"], "pending_execution")

    def test_current_contract_and_topology_are_structural_drafts(self) -> None:
        contract = _json("evals/contracts/batman.json")
        stored_topology = _json("evals/topologies/batman.json")
        ssot = ROOT / "ssot" / "batman.md"
        topology = compile_topology(ssot)

        validate_goal_contract(contract)
        validate_topology(topology)
        self.assertEqual(topology, stored_topology)
        self.assertEqual(contract["review_status"], "draft")
        self.assertEqual(contract["primary_outcome"]["threshold"], "human_review_required")
        self.assertEqual(contract["runtime_envelope"]["status"], "unresolved")
        self.assertEqual(topology["review_status"], "draft")
        self.assertEqual(topology["known_ambiguities"], [])
        coverage = topology["normative_clause_coverage"]
        self.assertEqual(coverage["mapped"], 0)
        self.assertEqual(coverage["waived"], 0)
        self.assertEqual(coverage["total"], len(topology["protected_invariants"]))
        self.assertEqual(topology["ssot_sha256"], artifact_hash(ssot))
        self.assertEqual(
            contract["protected_behaviors"],
            [clause["sha256"] for clause in topology["protected_invariants"]],
        )

        self.assertTrue(
            RETIRED_PUBLIC_IDENTITIES.isdisjoint(alias.casefold() for alias in topology["aliases_shortcuts"])
        )
        for clause in topology["protected_invariants"]:
            with self.subTest(clause=clause["id"]):
                words = {word.strip("`.,:;()[]{}").casefold() for word in clause["text"].split()}
                self.assertTrue(RETIRED_PUBLIC_IDENTITIES.isdisjoint(words))


if __name__ == "__main__":
    unittest.main()
