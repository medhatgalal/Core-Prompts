from __future__ import annotations

import json
import subprocess
import sys
import shutil
from pathlib import Path

from intent_pipeline.uac_baselines import (
    BaselineContext,
    baseline_artifact_findings,
    evaluate_candidate_against_baseline,
    historical_richness_score,
    persist_source_baseline,
    resolve_historical_baseline,
    validate_registry_entry,
)


ROOT = Path(__file__).resolve().parents[1]


def test_resolve_historical_baseline_returns_expected_gold_commits() -> None:
    assert resolve_historical_baseline(ROOT, "supercharge").baseline_path == "sources/ssot-baselines/supercharge/baseline.md"
    assert resolve_historical_baseline(ROOT, "supercharge").selected_commit == "3bc88b43"
    assert resolve_historical_baseline(ROOT, "converge").baseline_path == "sources/ssot-baselines/converge/baseline.md"
    assert resolve_historical_baseline(ROOT, "converge").selected_commit == "3bc88b43"
    assert resolve_historical_baseline(ROOT, "analyze-context").baseline_path == "sources/ssot-baselines/analyze-context/baseline.md"
    assert resolve_historical_baseline(ROOT, "analyze-context").selected_commit == "4bb1f7e5"
    assert resolve_historical_baseline(ROOT, "threader").baseline_path == "sources/ssot-baselines/threader/baseline.md"
    assert resolve_historical_baseline(ROOT, "threader").selected_commit == "db5c3789"
    assert resolve_historical_baseline(ROOT, "code-review").baseline_path == "sources/ssot-baselines/code-review/baseline.md"
    assert resolve_historical_baseline(ROOT, "code-review").selected_commit == "a78c1c21"
    assert resolve_historical_baseline(ROOT, "resolve-conflict").baseline_path == "sources/ssot-baselines/resolve-conflict/baseline.md"
    assert resolve_historical_baseline(ROOT, "resolve-conflict").selected_commit == "db5c3789"
    assert resolve_historical_baseline(ROOT, "gitops-review").baseline_path == "sources/ssot-baselines/gitops-review/baseline.md"
    assert resolve_historical_baseline(ROOT, "gitops-review").selected_commit == "4e16d6a4"


def test_registry_entries_match_git_history_for_known_regressions() -> None:
    supercharge = validate_registry_entry(ROOT, "supercharge")
    converge = validate_registry_entry(ROOT, "converge")

    assert supercharge["registry_commit"] == "3bc88b43"
    assert converge["registry_commit"] == "3bc88b43"
    assert supercharge["baseline_source"] == "source_library"
    assert converge["baseline_source"] == "source_library"
    assert supercharge["verified_by_git_history"] is False
    assert converge["verified_by_git_history"] is False
    assert supercharge["derived_commit"] != supercharge["registry_commit"]
    assert converge["derived_commit"] != converge["registry_commit"]


def test_recovered_supercharge_is_additive_against_historical_baseline() -> None:
    baseline = resolve_historical_baseline(ROOT, "supercharge")
    candidate = (ROOT / "ssot" / "supercharge.md").read_text(encoding="utf-8")

    result = evaluate_candidate_against_baseline(candidate, baseline)

    assert result["classification"] == "additive"
    assert result["hard_failures"] == []


def test_additive_threader_preserves_hard_export_contract() -> None:
    baseline = resolve_historical_baseline(ROOT, "threader")
    candidate = (ROOT / "ssot" / "threader.md").read_text(encoding="utf-8")

    result = evaluate_candidate_against_baseline(candidate, baseline)

    assert result["classification"] in {"preserved", "additive"}
    assert result["hard_failures"] == []


def test_pulse_release_regression_fails_historical_operational_baseline() -> None:
    baseline_text = subprocess.run(
        ["git", "show", "22aa8d5:ssot/pulse.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    candidate_text = subprocess.run(
        ["git", "show", "14045e7:ssot/pulse.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    baseline = BaselineContext(
        slug="pulse",
        strategy="derived_history",
        group="derived",
        baseline_path=None,
        selected_commit="22aa8d5d",
        richness_score=historical_richness_score(baseline_text),
        line_count=len(baseline_text.splitlines()),
        reason="historical regression repro",
        equivalent_commits=(),
        expected_companions=(),
        operator_invariants=(),
        scenario_matrix=(),
        historical_proof={},
        source="git_history",
        verified_by_git_history=True,
        baseline_text=baseline_text,
    )

    result = evaluate_candidate_against_baseline(candidate_text, baseline)

    assert result["classification"] == "flattened"
    assert any("operational" in failure or "scenario failed" in failure for failure in result["hard_failures"])


def test_generic_template_with_required_headings_still_fails_operational_baseline() -> None:
    baseline_text = subprocess.run(
        ["git", "show", "22aa8d5:ssot/pulse.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    candidate_text = """# Pulse

## Purpose
Summarize the capability.

## Primary Objective
Emit a deterministic summary.

## Workflow
1. Read the source.
2. Emit metadata.

## Rules
- Stay deterministic.

## Required Inputs
- source text

## Required Output
- summary

## Constraints
- No live actions.

## Examples
### Example Request
> Review this capability.

### Example Output Shape
- summary

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Output contract | The summary is present |
"""

    baseline = BaselineContext(
        slug="pulse",
        strategy="derived_history",
        group="derived",
        baseline_path=None,
        selected_commit="22aa8d5d",
        richness_score=historical_richness_score(baseline_text),
        line_count=len(baseline_text.splitlines()),
        reason="generic template negative control",
        equivalent_commits=(),
        expected_companions=(),
        operator_invariants=(),
        scenario_matrix=(),
        historical_proof={},
        source="git_history",
        verified_by_git_history=True,
        baseline_text=baseline_text,
    )

    result = evaluate_candidate_against_baseline(candidate_text, baseline)

    assert result["classification"] == "flattened"
    assert result["hard_failures"]


def test_registry_fallback_works_without_git_history(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store", ".venv", "node_modules"),
    )

    baseline = resolve_historical_baseline(workspace, "supercharge")
    candidate = (workspace / "ssot" / "supercharge.md").read_text(encoding="utf-8")
    result = evaluate_candidate_against_baseline(candidate, baseline)

    assert baseline.selected_commit == "3bc88b43"
    assert baseline.baseline_path == "sources/ssot-baselines/supercharge/baseline.md"
    assert baseline.source == "source_library"
    assert baseline.verified_by_git_history is False
    assert result["classification"] == "additive"


def test_baseline_artifact_findings_detects_flattened_autosearch_shape() -> None:
    findings = baseline_artifact_findings(
        "## Invocation Hints\nIntent\n- bad\nRequested Outcome\n- bad\nRejected/Out-of-Scope Signals\n- bad\n"
    )

    assert "flattened_uac_prompt_sections" in findings
    assert "corrupted_invocation_hints_section" in findings


def test_persist_source_baseline_refuses_structurally_noisy_overwrite(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store", ".venv", "node_modules"),
    )

    baseline_path = workspace / "sources" / "ssot-baselines" / "autosearch" / "baseline.md"
    baseline_before = baseline_path.read_text(encoding="utf-8")
    noisy_candidate = """## Invocation Hints
Intent
- malformed flattening marker
Requested Outcome
- malformed flattening marker
Rejected/Out-of-Scope Signals
- malformed flattening marker
"""

    result = persist_source_baseline(
        workspace,
        slug="autosearch",
        baseline_text=noisy_candidate,
        overwrite=False,
        source_kind="canonical_source",
        source_path=None,
        source_sha256="test",
        source_commit=None,
    )
    registry = json.loads((workspace / "sources" / "ssot-baselines" / "index.json").read_text(encoding="utf-8"))

    assert result["updated"] is False
    assert "artifact:flattened_uac_prompt_sections" in result["blocked_reasons"]
    assert baseline_path.read_text(encoding="utf-8") == baseline_before
    assert "artifact:flattened_uac_prompt_sections" in (
        registry["skills"]["autosearch"]["historical_proof"]["last_blocked_reasons"]
    )


def test_materialize_baseline_sources_refreshes_autosearch_from_current_ssot(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store", ".venv", "node_modules"),
    )

    result = subprocess.run(
        [sys.executable, str(workspace / "scripts" / "materialize-baseline-sources.py"), "--slug", "autosearch"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    baseline_path = workspace / "sources" / "ssot-baselines" / "autosearch" / "baseline.md"
    ssot_path = workspace / "ssot" / "autosearch.md"
    registry = json.loads((workspace / "sources" / "ssot-baselines" / "index.json").read_text(encoding="utf-8"))

    assert baseline_path.read_text(encoding="utf-8") == ssot_path.read_text(encoding="utf-8")
    assert registry["skills"]["autosearch"]["strategy"] == "head_snapshot"
    assert registry["skills"]["autosearch"]["group"] == "current_oracle"
    assert registry["skills"]["autosearch"]["historical_proof"]["materialized_from_source_kind"] == "current_ssot"
    assert not (workspace / "sources" / "ssot-baselines" / "weekly-intel" / "baseline.md").exists()
