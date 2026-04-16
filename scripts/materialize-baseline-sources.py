#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.uac_baselines import (
    baseline_artifact_findings,
    historical_richness_score,
    persist_source_baseline,
    text_sha256,
)

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
    if not (ROOT / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H", "--", f"ssot/{slug}.md"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    first = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
    return first[:8] or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize baseline sources into sources/ssot-baselines.")
    parser.add_argument("--slug", action="append", help="Only materialize the named slug(s).")
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="Also create registry entries for SSOT files that do not yet have baseline entries.",
    )
    return parser.parse_args()


def read_existing_baseline(slug: str, entry: dict[str, object]) -> str | None:
    baseline_path = str(entry.get("baseline_path") or "").strip()
    if not baseline_path:
        return None
    path = ROOT / baseline_path
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def should_materialize_from_current_ssot(slug: str, entry: dict[str, object], current_text: str) -> bool:
    strategy = str(entry.get("strategy") or "").strip()
    if strategy in {"head_snapshot", "head_plus_invariants"}:
        return True
    existing_text = read_existing_baseline(slug, entry)
    if not existing_text:
        return True
    if baseline_artifact_findings(existing_text):
        return True
    current_richness = historical_richness_score(current_text)
    existing_richness = historical_richness_score(existing_text)
    return current_richness >= existing_richness + 3


def materialize_entry(slug: str, entry: dict[str, object]) -> dict[str, object]:
    current_text = read_current_ssot(slug)
    if should_materialize_from_current_ssot(slug, entry, current_text):
        entry["group"] = "current_oracle"
        entry["strategy"] = "head_snapshot"
        entry["reason"] = (
            "Current SSOT baseline source snapshot materialized into the source library because the stored baseline "
            "was missing, stale, or structurally degraded."
        )
        current_commit = latest_commit_for_slug(slug)
        entry["selected_commit"] = current_commit
        result = persist_source_baseline(
            ROOT,
            slug=slug,
            baseline_text=current_text,
            overwrite=False,
            source_kind="current_ssot",
            source_path=f"ssot/{slug}.md",
            source_sha256=text_sha256(current_text.rstrip() + "\n"),
            source_commit=current_commit,
        )
    else:
        commit = str(entry.get("selected_commit") or "").strip()
        text = git_show(commit, slug)
        result = persist_source_baseline(
            ROOT,
            slug=slug,
            baseline_text=text,
            overwrite=False,
            source_kind="historical_gold",
            source_path=f"ssot/{slug}.md",
            source_sha256=text_sha256(text.rstrip() + "\n"),
            source_commit=commit,
        )
    refreshed = json.loads(TARGET_INDEX.read_text(encoding="utf-8"))
    merged = dict((refreshed.get("skills") or {}).get(slug) or {})
    merged.update(entry)
    historical_proof = dict(merged.get("historical_proof") or {})
    historical_proof.update(dict(((refreshed.get("skills") or {}).get(slug) or {}).get("historical_proof") or {}))
    merged["historical_proof"] = historical_proof
    if result.get("blocked_reasons"):
        merged["historical_proof"]["last_blocked_reasons"] = list(result["blocked_reasons"])
    return merged


def main() -> None:
    args = parse_args()
    if LEGACY_REGISTRY.exists():
        legacy = json.loads(LEGACY_REGISTRY.read_text(encoding="utf-8"))
    elif TARGET_INDEX.exists():
        legacy = json.loads(TARGET_INDEX.read_text(encoding="utf-8"))
    else:
        legacy = {"skills": {}}
    requested_slugs = set(args.slug or [])
    legacy_skills = dict(legacy.get("skills") or {})
    if requested_slugs:
        missing_requested = sorted(slug for slug in requested_slugs if not (ROOT / "ssot" / f"{slug}.md").exists())
        if missing_requested:
            raise SystemExit(f"unknown slug(s): {', '.join(missing_requested)}")
    target_slugs = set(legacy_skills)
    if requested_slugs:
        target_slugs &= requested_slugs
    if args.include_missing:
        ssot_slugs = {path.stem for path in (ROOT / "ssot").glob("*.md")}
        target_slugs |= requested_slugs or ssot_slugs

    skills = dict(legacy_skills)
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    for slug in sorted(target_slugs):
        entry = dict(skills.get(slug) or {})
        if not entry:
            text = read_current_ssot(slug)
            current_commit = latest_commit_for_slug(slug)
            baseline_path = Path("sources") / "ssot-baselines" / slug / "baseline.md"
            skills[slug] = {
                "group": "current_oracle",
                "strategy": "head_snapshot",
                "selected_commit": current_commit,
                "richness_score": richness_score(text),
                "line_count": len(text.splitlines()),
                "equivalent_commits": [],
                "reason": "Current SSOT baseline source snapshot materialized into the source library because no stronger curated pre-SSOT baseline has been recorded yet.",
                "historical_proof": {
                    "current_head_commit": current_commit,
                    "current_head_richness_score": richness_score(text),
                    "current_head_line_count": len(text.splitlines()),
                    "materialized_from_commit": current_commit,
                    "materialized_from_source_kind": "current_ssot",
                    "materialized_from_path": f"ssot/{slug}.md",
                    "materialized_from_sha256": text_sha256(text.rstrip() + "\n"),
                },
                "expected_companions": [],
                "scenario_matrix": [],
                "baseline_path": str(baseline_path).replace("\\", "/"),
            }
        skills[slug] = materialize_entry(slug, dict(skills[slug]))
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
