from __future__ import annotations

import json
from pathlib import Path

from intent_pipeline.uac_quality import load_quality_profile, run_quality_loop

ROOT = Path(__file__).resolve().parents[1]


def test_load_quality_profile_auto_resolves_architecture() -> None:
    profile = load_quality_profile(ROOT, "architecture", "auto")
    assert profile.name == "architecture"
    assert profile.targets["operational_richness"] == 10


def test_run_quality_loop_ships_rich_architecture_candidate() -> None:
    profile = load_quality_profile(ROOT, "architecture", "auto")
    candidate = (ROOT / "ssot" / "architecture.md").read_text(encoding="utf-8")
    descriptor = json.loads((ROOT / ".meta" / "capabilities" / "architecture.json").read_text(encoding="utf-8"))

    result = run_quality_loop(
        slug="architecture",
        profile=profile,
        candidate_text=candidate,
        descriptor=descriptor,
        source_refs=list(profile.external_sources),
        benchmark_sources=[],
        max_passes=2,
    )

    assert result["status"] == "ship"
    assert result["pass_count"] >= 1
    assert result["scorecard"]["benchmark_readiness"] >= 9


def test_run_quality_loop_marks_thin_candidate_for_manual_review() -> None:
    profile = load_quality_profile(ROOT, "sample-skill", "default")
    result = run_quality_loop(
        slug="sample-skill",
        profile=profile,
        candidate_text="# Sample\n\nThin summary only.\n",
        descriptor={"slug": "sample-skill"},
        source_refs=["https://example.com/sample.md"],
        benchmark_sources=[],
        max_passes=1,
    )

    assert result["status"] == "manual_review"
    assert result["judge_reports"][0]["judge_reports"][0]["judge"] == "source_fidelity"
    assert result["judge_reports"][0]["judge_reports"][0]["score"] < 9
    assert result["scorecard"]["benchmark_readiness"] < 9


def test_run_quality_loop_caps_later_judges_when_source_fidelity_fails() -> None:
    profile = load_quality_profile(ROOT, "sample-skill", "default")
    candidate = """# Sample

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

    result = run_quality_loop(
        slug="pulse",
        profile=profile,
        candidate_text=candidate,
        descriptor={"slug": "pulse"},
        source_refs=["ssot/pulse.md"],
        benchmark_sources=[],
        max_passes=1,
    )

    judge_reports = result["judge_reports"][0]["judge_reports"]
    metadata = next(judge for judge in judge_reports if judge["judge"] == "metadata_integrity")
    benchmark = next(judge for judge in judge_reports if judge["judge"] == "benchmark_readiness")

    assert result["status"] == "manual_review"
    assert any("source fidelity failed" in blocker for blocker in metadata["blockers"])
    assert any("source fidelity failed" in blocker for blocker in benchmark["blockers"])
