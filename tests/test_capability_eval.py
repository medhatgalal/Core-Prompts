from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_prompts_eval.clarity import audit_text, load_policy, safe_fixes
from core_prompts_eval.contracts import ContractError, PROFILE_TOKEN_CAPS, REQUIRED_PROMOTION_GATES, validate_promotion_verdict
from core_prompts_eval.evaluator import calibrate_static, compare, compile_skill
from core_prompts_eval.impact import build_impact_plan
from core_prompts_eval.topology import compile_topology


ROOT = Path(__file__).resolve().parents[1]


def test_clarity_lint_is_advisory_and_safe_fix_is_whitespace_only() -> None:
    policy = load_policy(ROOT)
    result = audit_text("It should be done simply.  \n", policy)
    fixed, ledger = safe_fixes("Keep must.  \n")

    assert result["advisory_only"] is True
    assert result["behavioral_claim"] == "none"
    assert result["finding_count"] >= 1
    assert fixed == "Keep must.\n"
    assert ledger[0]["rule_id"] == "IC-SAFE-001"


def test_impact_plan_escalates_unknown_and_caps_tokens() -> None:
    plan = build_impact_plan("example", ["formatting", "unknown"])

    assert plan["minimum_profile"] == "canary"
    assert plan["hard_token_cap"] == PROFILE_TOKEN_CAPS["canary"]


def test_promotion_verdict_cannot_average_over_failed_gate() -> None:
    verdict = {
        "schema_version": "PromotionVerdict.v1",
        "run_id": "run-1",
        "slug": "example",
        "status": "promote",
        "baseline_sha256": "a" * 64,
        "candidate_sha256": "b" * 64,
        "goal_contract_sha256": "c" * 64,
        "topology_sha256": "d" * 64,
        "dataset_sha256": "e" * 64,
        "scorer_sha256": "f" * 64,
        "evaluator_version": "1",
        "profile": "promotion",
        "token_cap": 5_000_000,
        "required_cells": [{"host": "codex", "result": "pass"}],
        "hard_gates": {**{name: True for name in REQUIRED_PROMOTION_GATES}, "critical_mutant_kill_100_percent": False},
        "token_usage": {"raw": 0, "cached": 0, "billed": 0},
        "created_at": "2026-08-18T00:00:00Z",
    }

    with pytest.raises(ContractError, match="failed hard gates"):
        validate_promotion_verdict(verdict)


def test_compile_supercharge_has_no_known_contract_blocker() -> None:
    topology = compile_topology(ROOT / "ssot" / "supercharge.md")

    assert topology["schema_version"] == "CapabilityTopology.v1"
    assert topology["normative_clause_coverage"]["total"] > 0
    assert topology["review_status"] == "draft"
    assert topology["known_ambiguities"] == []


def test_static_compare_uses_zero_model_calls(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.md"
    candidate.write_text((ROOT / "ssot" / "code-review.md").read_text(encoding="utf-8"), encoding="utf-8")
    result = compare(ROOT, "code-review", candidate, "static", allow_model_calls=False, max_tokens=0)

    assert result["status"] == "structural_ready"
    assert result["model_calls"] == 0
    assert result["behavioral_claim"] == "none"
    assert result["before"]["name"] == "code-review"
    assert result["size_delta"] == {"lines": 0, "words": 0, "bytes": 0, "model_tokens_estimate": 0}


def test_model_profile_is_inconclusive_without_explicit_permission(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.md"
    candidate.write_text((ROOT / "ssot" / "code-review.md").read_text(encoding="utf-8"), encoding="utf-8")
    result = compare(ROOT, "code-review", candidate, "promotion", allow_model_calls=False, max_tokens=None)

    assert result["status"] == "inconclusive"
    assert result["model_calls"] == 0


def test_calibration_control_inventory_is_complete() -> None:
    result = calibrate_static(ROOT)

    assert result["missing_controls"] == []
    assert result["controls_present"] == 14
    assert result["judge_qualified"] is False


def test_instruction_editor_compiles_as_a_skill() -> None:
    result = compile_skill(ROOT, "instruction-editor")

    assert result["goal_contract"]["slug"] == "instruction-editor"
    assert result["clarity"]["behavioral_claim"] == "none"
