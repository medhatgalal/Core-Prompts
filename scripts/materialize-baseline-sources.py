#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LEGACY_REGISTRY = ROOT / ".meta" / "historical-baselines.json"
TARGET_ROOT = ROOT / "sources" / "ssot-baselines"
TARGET_INDEX = TARGET_ROOT / "index.json"


def richness_score(text: str) -> int:
    score = 0
    score += 5 if "## MODULE:" in text or "## MODULE " in text else 0
    score += 4 if "## HELP OUTPUT" in text else 0
    score += 4 if "## MODULE REFERENCE" in text else 0
    score += 3 if "## The Prompt" in text else 0
    score += 2 if "```text" in text or "~~~~text" in text else 0
    score += 2 if "HARD CONSTRAINTS" in text else 0
    score += 2 if "Output Structure (MANDATORY)" in text else 0
    score += 1 if "Invocation Hints" in text else 0
    score += 1 if "Evaluation Rubric" in text else 0
    return score


def git_show(commit: str, slug: str) -> str:
    return subprocess.run(
        ["git", "show", f"{commit}:ssot/{slug}.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def read_current_ssot(slug: str) -> str:
    return (ROOT / "ssot" / f"{slug}.md").read_text(encoding="utf-8")


def latest_commit_for_slug(slug: str) -> str | None:
    result = subprocess.run(
        ["git", "log", "--format=%H", "--", f"ssot/{slug}.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    first = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
    return first[:8] or None


def main() -> None:
    if LEGACY_REGISTRY.exists():
        legacy = json.loads(LEGACY_REGISTRY.read_text(encoding="utf-8"))
    elif TARGET_INDEX.exists():
        legacy = json.loads(TARGET_INDEX.read_text(encoding="utf-8"))
    else:
        legacy = {"skills": {}}
    skills = {}
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    for slug, entry in sorted((legacy.get("skills") or {}).items()):
        commit = str(entry.get("selected_commit") or "").strip()
        if commit:
            text = git_show(commit, slug)
        else:
            text = read_current_ssot(slug)
        baseline_path = Path("sources") / "ssot-baselines" / slug / "baseline.md"
        full_path = ROOT / baseline_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(text.rstrip() + "\n", encoding="utf-8")
        migrated = dict(entry)
        migrated["baseline_path"] = str(baseline_path).replace("\\", "/")
        historical_proof = dict(migrated.get("historical_proof") or {})
        historical_proof.setdefault("materialized_from_commit", commit or None)
        migrated["historical_proof"] = historical_proof
        migrated["richness_score"] = richness_score(text)
        migrated["line_count"] = len(text.splitlines())
        skills[slug] = migrated
    for path in sorted((ROOT / "ssot").glob("*.md")):
        slug = path.stem
        if slug in skills:
            continue
        text = path.read_text(encoding="utf-8")
        baseline_path = Path("sources") / "ssot-baselines" / slug / "baseline.md"
        full_path = ROOT / baseline_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(text.rstrip() + "\n", encoding="utf-8")
        skills[slug] = {
            "group": "current_oracle",
            "strategy": "head_snapshot",
            "selected_commit": latest_commit_for_slug(slug),
            "richness_score": richness_score(text),
            "line_count": len(text.splitlines()),
            "equivalent_commits": [],
            "reason": "Current SSOT baseline source snapshot materialized into the source library because no stronger curated pre-SSOT baseline has been recorded yet.",
            "historical_proof": {
                "current_head_commit": latest_commit_for_slug(slug),
                "current_head_richness_score": richness_score(text),
                "current_head_line_count": len(text.splitlines()),
                "materialized_from_commit": latest_commit_for_slug(slug),
            },
            "expected_companions": [],
            "scenario_matrix": [],
            "baseline_path": str(baseline_path).replace("\\", "/"),
        }
    TARGET_INDEX.write_text(
        json.dumps(
            {
                "version": "uac-baseline-sources.v1",
                "canonical_root": "sources/ssot-baselines",
                "skills": skills,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
