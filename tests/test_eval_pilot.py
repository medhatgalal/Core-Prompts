from __future__ import annotations

import json
import shutil
from pathlib import Path

from core_prompts_eval.evaluator import PILOT_SKILLS, calibrate_static, draft_goal_contract
from core_prompts_eval.pilot import validate_pilot_foundations


ROOT = Path(__file__).resolve().parents[1]


def test_pilot_is_four_questions_not_a_repo_wide_behavioral_sweep() -> None:
    plan = json.loads((ROOT / "evals" / "pilot-plan.json").read_text(encoding="utf-8"))

    assert len(plan["experiments"]) == 4
    assert set(PILOT_SKILLS) == {
        "supercharge",
        "code-review",
        "feature-status",
        "eng-report",
        "codebase-health-audit",
        "uac-import",
    }
    assert set(plan["deferred"]["skills"]) == {"architecture", "instruction-editor", "pulse", "weekly-intel"}


def test_static_pilot_foundations_are_executable_at_zero_tokens() -> None:
    result = validate_pilot_foundations(ROOT)

    assert result["status"] == "structural_ready"
    assert result["experiment_count"] == 4
    assert result["case_count"] >= 30
    assert result["model_calls"] == 0
    assert result["behavioral_claim"] == "none"


def test_code_review_public_cases_cover_each_lifecycle_dimension_and_control() -> None:
    fixture = json.loads(
        (ROOT / "evals" / "fixtures" / "code-review" / "seeded-defects.json").read_text(encoding="utf-8")
    )
    lifecycle_cases = fixture["lifecycle_cases"]
    by_category: dict[str, set[bool]] = {}
    for case in lifecycle_cases:
        by_category.setdefault(case["category"], set()).add(case["should_flag"])
        assert (ROOT / case["artifact"]).is_file()

    assert by_category == {
        "resource": {False, True},
        "concurrency_init": {False, True},
        "operational_readiness": {False, True},
        "api_contract": {False, True},
    }

    public_cases = [
        json.loads(line)
        for line in (ROOT / fixture["public_cases"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(public_cases) == 10
    assert len({case["id"] for case in public_cases}) == len(public_cases)
    for case in public_cases:
        assert (ROOT / "evals" / "fixtures" / "code-review" / case["fixture"]).is_file()


def test_pilot_does_not_pretend_anchor_evidence_is_cross_host_proof() -> None:
    pilot = draft_goal_contract(ROOT, "supercharge")["runtime_envelope"]
    deferred = draft_goal_contract(ROOT, "pulse")["runtime_envelope"]

    assert pilot["required_cells"] == ["anchor"]
    assert pilot["cross_host_required_for_pilot"] is False
    assert deferred["required_cells"] == []


def test_calibration_includes_pilot_fixture_result_without_model_calls() -> None:
    result = calibrate_static(ROOT)

    assert result["pilot_foundations"]["status"] == "structural_ready"
    assert result["pilot_foundations"]["model_calls"] == 0


def test_static_pilot_validator_fails_when_a_protected_marker_disappears(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "evals", tmp_path / "evals")
    shutil.copytree(ROOT / ".meta", tmp_path / ".meta")
    (tmp_path / "ssot").mkdir()
    (tmp_path / "scripts").mkdir()
    supercharge = (ROOT / "ssot" / "supercharge.md").read_text(encoding="utf-8")
    (tmp_path / "ssot" / "supercharge.md").write_text(
        supercharge.replace("## MODULE: /basis", "## REMOVED MODULE: /basis"),
        encoding="utf-8",
    )
    shutil.copy2(ROOT / "scripts" / "uac-import.py", tmp_path / "scripts" / "uac-import.py")

    result = validate_pilot_foundations(tmp_path)

    assert result["status"] == "hold"
    assert any("missing marker" in error for error in result["errors"])


def test_static_pilot_validator_fails_when_a_lifecycle_fixture_is_missing(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "evals", tmp_path / "evals")
    shutil.copytree(ROOT / ".meta", tmp_path / ".meta")
    shutil.copytree(ROOT / "ssot", tmp_path / "ssot")
    (tmp_path / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts" / "uac-import.py", tmp_path / "scripts" / "uac-import.py")
    (tmp_path / "evals" / "fixtures" / "code-review" / "unbounded-temp-storage.diff").unlink()

    result = validate_pilot_foundations(tmp_path)

    assert result["status"] == "hold"
    assert any("unbounded-temp-storage.diff" in error for error in result["errors"])
