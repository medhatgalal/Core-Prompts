from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_prompts_eval.contracts import (
    ContractError,
    REQUIRED_PROMOTION_GATES,
    artifact_hash,
    validate_promotion_verdict,
)


ROOT = Path(__file__).resolve().parents[1]


def _binding(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": artifact_hash(path)}


def _promotion_verdict(tmp_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    files = {}
    for name in (
        "run-manifest.json",
        "sealed-attestation.json",
        "score-report.json",
        "token-ledger.json",
        "approved-trust-policy.json",
        "receipt.json",
        "conformance-usage.json",
        "adjudication-usage.json",
        "adapter.json",
        "judge.json",
        "reproduction.json",
        "reproduction-receipt.json",
        "policy.json",
        "impact-plan.json",
        "evaluator.json",
        "trust-root.json",
    ):
        path = artifacts / name
        path.write_text(json.dumps({"name": name}) + "\n", encoding="utf-8")
        files[name] = path
    contract_dir = tmp_path / "evals/contracts"
    topology_dir = tmp_path / "evals/topologies"
    contract_dir.mkdir(parents=True)
    topology_dir.mkdir(parents=True)
    goal = {
        "schema_version": "GoalContract.v1",
        "slug": "batman",
        "target": "deliver",
        "intended_outcome": "verified delivery",
        "change_class": "authority",
        "non_goals": [],
        "protected_behaviors": [],
        "editable_behavior": [],
        "primary_outcome": {},
        "secondary_outcomes": [],
        "regression_limits": {},
        "cost_latency_limits": {},
        "runtime_envelope": {},
        "promotion_rule": "all gates",
        "rollback_trigger": "regression",
        "source_clause_hashes": [],
        "review_status": "human_reviewed",
    }
    topology = {
        "schema_version": "CapabilityTopology.v1",
        "slug": "batman",
        "ssot_sha256": "2" * 64,
        "nodes": {},
        "composition": {},
        "state_machine": {},
        "outputs": [],
        "authority_boundaries": [],
        "resources": [],
        "handoffs": [],
        "protected_invariants": [],
        "risk_tiers": {},
        "source_references": [],
        "known_ambiguities": [],
        "coverage_policy": {},
        "normative_clause_coverage": {"total": 1, "mapped": 1, "waived": 0},
        "review_status": "human_reviewed",
    }
    goal_path = contract_dir / "batman.json"
    topology_path = topology_dir / "batman.json"
    goal_path.write_text(json.dumps(goal) + "\n", encoding="utf-8")
    topology_path.write_text(json.dumps(topology) + "\n", encoding="utf-8")
    cells = [
        {
            "host": "codex",
            "result": "pass",
            "evidence_grade": "A",
            "resolved_model_identifier": "gpt-5.5-2026-08-01",
            "critical": True,
            "receipt_ids": ["primary"],
        }
    ]
    usage = {"raw": 100, "cached": 0, "billed": 100}
    gates = {name: True for name in REQUIRED_PROMOTION_GATES}
    verdict: dict[str, object] = {
        "schema_version": "PromotionVerdict.v2",
        "run_id": "run-primary",
        "slug": "batman",
        "status": "promote",
        "baseline_revision": "a" * 40,
        "candidate_revision": "b" * 40,
        "baseline_sha256": "1" * 64,
        "candidate_sha256": "2" * 64,
        "goal_contract_sha256": artifact_hash(goal_path),
        "topology_sha256": artifact_hash(topology_path),
        "dataset_sha256": "5" * 64,
        "scorer_sha256": "6" * 64,
        "run_manifest_path": _binding(files["run-manifest.json"], tmp_path)["path"],
        "run_manifest_sha256": artifact_hash(files["run-manifest.json"]),
        "sealed_bundle_attestation_binding": _binding(files["sealed-attestation.json"], tmp_path),
        "score_report_binding": _binding(files["score-report.json"], tmp_path),
        "token_ledger_binding": _binding(files["token-ledger.json"], tmp_path),
        "approved_trust_policy_binding": {
            **_binding(files["approved-trust-policy.json"], tmp_path),
            "revision": "9" * 40,
        },
        "primary_runner_identity_sha256": "e" * 64,
        "receipt_bindings": [
            {"receipt_id": "primary", **_binding(files["receipt.json"], tmp_path)}
        ],
        "auxiliary_receipt_bindings": [
            {
                "binding_id": "conformance",
                "phase": "adapter_conformance",
                "run_id": "adapter-probes",
                **_binding(files["conformance-usage.json"], tmp_path),
            },
            {
                "binding_id": "judge",
                "phase": "adjudication",
                "run_id": "judge-run-primary",
                **_binding(files["adjudication-usage.json"], tmp_path),
            },
        ],
        "adapter_bindings": [
            {
                "adapter_id": "codex",
                "version": "1",
                "phase": "primary",
                "runner_identity_sha256": "e" * 64,
                **_binding(files["adapter.json"], tmp_path),
            }
        ],
        "judge_qualification_bindings": [
            {
                "judge_id": "judge-1",
                **_binding(files["judge.json"], tmp_path),
                "judge_model_sha256": "8" * 64,
                "judge_prompt_sha256": "9" * 64,
                "judge_rubric_sha256": "a" * 64,
                "judge_tool_policy_sha256": "b" * 64,
                "judge_preregistration_sha256": "c" * 64,
                "gold_set_commitment_sha256": "d" * 64,
            }
        ],
        "reproduction_manifest_bindings": [
            {
                "run_id": "run-reproduction",
                **_binding(files["reproduction.json"], tmp_path),
                "seed": 2,
                "runner_identity_sha256": "f" * 64,
                "receipt_bindings": [
                    {
                        "receipt_id": "reproduction-primary",
                        **_binding(files["reproduction-receipt.json"], tmp_path),
                    }
                ],
            }
        ],
        "evaluation_policy_path": _binding(files["policy.json"], tmp_path)["path"],
        "evaluation_policy_sha256": artifact_hash(files["policy.json"]),
        "impact_plan_path": _binding(files["impact-plan.json"], tmp_path)["path"],
        "impact_plan_sha256": artifact_hash(files["impact-plan.json"]),
        "evaluator_path": _binding(files["evaluator.json"], tmp_path)["path"],
        "evaluator_sha256": artifact_hash(files["evaluator.json"]),
        "trust_root_sha256": artifact_hash(files["trust-root.json"]),
        "evaluator_version": "1",
        "profile": "promotion",
        "token_cap": 5_000_000,
        "required_cells": cells,
        "hard_gates": gates,
        "token_usage": usage,
        "issued_at": "2026-08-27T12:00:00Z",
        "expires_at": "2026-08-28T12:00:00Z",
        "issuer": "independent-evaluator",
        "signature": {
            "algorithm": "Ed25519",
            "key_id": "release-key-1",
            "purpose": "promotion_verdict",
            "signed_at": "2026-08-27T12:00:00Z",
            "payload_sha256": "7" * 64,
            "value_base64": "ZmFrZS10ZXN0LXNpZ25hdHVyZQ==",
        },
    }
    derived = {"hard_gates": gates, "required_cells": cells, "token_usage": usage}
    return verdict, derived


def test_promotion_verdict_schema_is_closed_and_requires_immutable_bindings() -> None:
    schema = json.loads((ROOT / "evals/schemas/promotion-verdict.schema.json").read_text(encoding="utf-8"))

    assert schema["$id"] == "PromotionVerdict.v2"
    assert schema["properties"]["schema_version"]["const"] == "PromotionVerdict.v2"
    assert schema["additionalProperties"] is False
    for field in (
        "baseline_revision",
        "candidate_revision",
        "run_manifest_path",
        "run_manifest_sha256",
        "sealed_bundle_attestation_binding",
        "score_report_binding",
        "token_ledger_binding",
        "approved_trust_policy_binding",
        "primary_runner_identity_sha256",
        "receipt_bindings",
        "auxiliary_receipt_bindings",
        "adapter_bindings",
        "judge_qualification_bindings",
        "reproduction_manifest_bindings",
        "evaluation_policy_path",
        "evaluation_policy_sha256",
        "impact_plan_path",
        "impact_plan_sha256",
        "evaluator_path",
        "evaluator_sha256",
        "trust_root_sha256",
        "issued_at",
        "expires_at",
        "issuer",
        "signature",
    ):
        assert field in schema["required"]

    legacy = json.loads(
        (ROOT / "evals/schemas/promotion-verdict-v1.schema.json").read_text(encoding="utf-8")
    )
    assert legacy["$id"] == "PromotionVerdict.v1"


def test_approved_trust_policy_schema_is_closed_and_binds_store_and_keys() -> None:
    schema = json.loads(
        (ROOT / "evals/schemas/approved-trust-policy.schema.json").read_text(encoding="utf-8")
    )

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "schema_version",
        "policy_id",
        "status",
        "trust_store_sha256",
        "authorized_keys",
        "approved_at",
        "expires_at",
    }


def test_signed_sealed_bundle_may_bind_distinct_bundle_and_dataset_hashes(tmp_path: Path) -> None:
    verdict, derived = _promotion_verdict(tmp_path)
    sealed_path = tmp_path / str(verdict["sealed_bundle_attestation_binding"]["path"])
    sealed_path.write_text(
        json.dumps({"bundle_sha256": "8" * 64, "dataset_sha256": verdict["dataset_sha256"]}) + "\n",
        encoding="utf-8",
    )
    verdict["sealed_bundle_attestation_binding"]["sha256"] = artifact_hash(sealed_path)

    validate_promotion_verdict(
        verdict,
        repo_root=tmp_path,
        trust_root=tmp_path / "artifacts/trust-root.json",
        now="2026-08-27T13:00:00Z",
        evidence_verifier=lambda *args, **kwargs: derived,
        approved_trust_policy_sha256=verdict["approved_trust_policy_binding"]["sha256"],
        approved_trust_policy_revision=verdict["approved_trust_policy_binding"]["revision"],
    )


def test_promote_derives_gates_from_signed_artifacts_instead_of_trusting_booleans(tmp_path: Path) -> None:
    verdict, derived = _promotion_verdict(tmp_path)
    verdict["hard_gates"] = {**derived["hard_gates"], "critical_mutant_kill_100_percent": False}
    calls = []

    def fake_verifier(payload, *, trust_root, repo_root, approved_trust_policy_sha256, approved_trust_policy_revision, now=None):
        calls.append((payload, trust_root, repo_root, now))
        return derived

    with pytest.raises(ContractError, match="hard gates do not match signed evidence"):
        validate_promotion_verdict(
            verdict,
            repo_root=tmp_path,
            trust_root=tmp_path / "artifacts/trust-root.json",
            now="2026-08-27T13:00:00Z",
            evidence_verifier=fake_verifier,
            approved_trust_policy_sha256=verdict["approved_trust_policy_binding"]["sha256"],
            approved_trust_policy_revision=verdict["approved_trust_policy_binding"]["revision"],
        )

    assert len(calls) == 1


def test_promote_accepts_only_matching_derived_receipts_and_cells(tmp_path: Path) -> None:
    verdict, derived = _promotion_verdict(tmp_path)

    validate_promotion_verdict(
        verdict,
        repo_root=tmp_path,
        trust_root=tmp_path / "artifacts/trust-root.json",
        now="2026-08-27T13:00:00Z",
        evidence_verifier=lambda *args, **kwargs: derived,
        approved_trust_policy_sha256=verdict["approved_trust_policy_binding"]["sha256"],
        approved_trust_policy_revision=verdict["approved_trust_policy_binding"]["revision"],
    )


def test_promote_requires_external_operator_approval_for_trust_policy(tmp_path: Path) -> None:
    verdict, derived = _promotion_verdict(tmp_path)

    with pytest.raises(ContractError, match="operator-approved trust policy hash"):
        validate_promotion_verdict(
            verdict,
            repo_root=tmp_path,
            trust_root=tmp_path / "artifacts/trust-root.json",
            evidence_verifier=lambda *args, **kwargs: derived,
        )


def test_promote_refuses_a_stale_bound_artifact_before_signature_verification(tmp_path: Path) -> None:
    verdict, derived = _promotion_verdict(tmp_path)
    (tmp_path / str(verdict["evaluation_policy_path"])).write_text('{"tampered":true}\n', encoding="utf-8")
    called = False

    def fake_verifier(*args, **kwargs):
        nonlocal called
        called = True
        return derived

    with pytest.raises(ContractError, match="evaluation policy artifact is missing or stale"):
        validate_promotion_verdict(
            verdict,
            repo_root=tmp_path,
            trust_root=tmp_path / "artifacts/trust-root.json",
            evidence_verifier=fake_verifier,
            approved_trust_policy_sha256=verdict["approved_trust_policy_binding"]["sha256"],
            approved_trust_policy_revision=verdict["approved_trust_policy_binding"]["revision"],
        )

    assert called is False
