from __future__ import annotations

import shutil
from pathlib import Path

from intent_pipeline.uac_baselines import (
    evaluate_candidate_against_baseline,
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
