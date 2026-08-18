from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .clarity import audit_text, load_policy
from .contracts import (
    PROFILE_TOKEN_CAPS,
    artifact_hash,
    load_json,
    validate_goal_contract,
    validate_promotion_verdict,
    validate_topology,
)
from .impact import build_impact_plan
from .topology import compile_topology


PILOT_SKILLS = ("supercharge", "pulse", "code-review", "weekly-intel", "uac-import", "architecture")

SKILL_OUTCOMES = {
    "supercharge": "Correct routing, canonical stack order, module preservation, explicit-only behavior, state transitions, output-contract adherence, and improved downstream artifacts.",
    "code-review": "Seeded-defect recall, precision, severity calibration, evidence quality, actionable findings, low noise, and no unauthorized edits.",
    "weekly-intel": "Source coverage, time-window correctness, citation integrity, deduplication, fact/inference separation, uncertainty, synthesis quality, and forwardability.",
    "pulse": "Priority accuracy, conservative uncertainty handling, correct approval boundaries, tool discipline, and no destructive false positives.",
    "uac-import": "Source fidelity, correct capability classification, overlap detection, safe landing decisions, and no invented behavioral confidence.",
    "architecture": "Boundary quality, implementation usability, rejected alternatives, failure awareness, migration safety, and correct routing away from unrelated asks.",
    "instruction-editor": "Clearer instruction artifacts with exact preservation of commands, modality, authority, ordering, outputs, exceptions, fallbacks, and routing boundaries.",
}


def artifact_metrics(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    frontmatter: dict[str, str] = {}
    if text.startswith("---\n"):
        header = text.split("---\n", 2)[1]
        for line in header.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip().strip('"')
    return {
        "name": frontmatter.get("name"),
        "description": frontmatter.get("description"),
        "lines": len(text.splitlines()),
        "words": len(text.split()),
        "bytes": len(text.encode("utf-8")),
        "model_tokens_estimate": max(1, round(len(text.encode("utf-8")) / 4)),
        "sha256": artifact_hash(text),
    }


def compile_skill(repo_root: Path, slug: str, *, write: bool = False) -> dict[str, Any]:
    ssot_path = repo_root / "ssot" / f"{slug}.md"
    if not ssot_path.exists():
        raise FileNotFoundError(ssot_path)
    topology = compile_topology(ssot_path)
    goal_path = repo_root / "evals" / "contracts" / f"{slug}.json"
    if goal_path.exists():
        goal = load_json(goal_path)
        validate_goal_contract(goal)
        if write and goal.get("review_status") == "draft":
            goal = draft_goal_contract(repo_root, slug)
    else:
        goal = draft_goal_contract(repo_root, slug)
    clarity = audit_text(ssot_path.read_text(encoding="utf-8"), load_policy(repo_root))
    if write:
        topology_path = repo_root / "evals" / "topologies" / f"{slug}.json"
        topology_path.parent.mkdir(parents=True, exist_ok=True)
        topology_path.write_text(json.dumps(topology, indent=2) + "\n", encoding="utf-8")
        if not goal_path.exists() or goal.get("review_status") == "draft":
            goal_path.parent.mkdir(parents=True, exist_ok=True)
            goal_path.write_text(json.dumps(goal, indent=2) + "\n", encoding="utf-8")
    return {
        "slug": slug,
        "goal_contract": goal,
        "topology": topology,
        "clarity": clarity,
        "status": "blocked_contract" if topology["known_ambiguities"] else "structural_ready",
    }


def draft_goal_contract(repo_root: Path, slug: str) -> dict[str, Any]:
    path = repo_root / "ssot" / f"{slug}.md"
    text = path.read_text(encoding="utf-8")
    clauses = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and any(word in stripped.lower() for word in ("must", "never", "required", "only", "forbidden", "do not")):
            clauses.append({"sha256": artifact_hash(stripped), "source": f"ssot/{slug}.md", "text": stripped})
    return {
        "schema_version": "GoalContract.v1",
        "slug": slug,
        "target": f"Fulfill the canonical intent of {slug}.",
        "intended_outcome": SKILL_OUTCOMES.get(slug, "Preserve the canonical SSOT objective and required output."),
        "change_class": "unknown",
        "non_goals": [],
        "protected_behaviors": [item["sha256"] for item in clauses],
        "editable_behavior": [],
        "primary_outcome": {
            "metric": "skill_specific_task_success",
            "definition": SKILL_OUTCOMES.get(slug, "Canonical task success with protected behavior preserved."),
            "threshold": "human_review_required",
        },
        "secondary_outcomes": [],
        "regression_limits": {"protected_binary_margin": 0.02, "critical_deterministic": "exact_pass"},
        "cost_latency_limits": {"profile_caps": PROFILE_TOKEN_CAPS},
        "runtime_envelope": {
            "required_cells": ["anchor"] if slug in PILOT_SKILLS else [],
            "cross_host_required_for_pilot": slug in PILOT_SKILLS,
            "status": "unresolved",
        },
        "promotion_rule": "Change-class-specific proof plus all hard gates; no aggregate compensation.",
        "rollback_trigger": "Any protected regression or stale bound evidence.",
        "source_clause_hashes": clauses,
        "review_status": "draft",
    }


def compile_all(repo_root: Path, *, write: bool = False) -> dict[str, Any]:
    results = [compile_skill(repo_root, path.stem, write=write) for path in sorted((repo_root / "ssot").glob("*.md"))]
    return {
        "schema_version": "CorpusTopologyAudit.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "skill_count": len(results),
        "blocked_contract": [result["slug"] for result in results if result["status"] == "blocked_contract"],
        "draft_contracts": [result["slug"] for result in results if result["goal_contract"]["review_status"] != "human_reviewed"],
        "results": results,
        "behavioral_claim": "none",
    }


def calibrate_static(repo_root: Path) -> dict[str, Any]:
    controls_path = repo_root / "evals" / "controls" / "evaluator-controls.jsonl"
    controls = []
    if controls_path.exists():
        controls = [json.loads(line) for line in controls_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    required = {
        "polished_sabotage",
        "invented_evidence",
        "hidden_uncertainty",
        "deleted_obscure_module",
        "reversed_canonical_order",
        "weakened_modality",
        "broken_stop_state",
        "broadened_tool_authority",
        "output_schema_drift",
        "cross_surface_drift",
        "verbosity_inflation",
        "terse_correct",
        "style_only",
        "correct_semantic_fix",
    }
    present = {control.get("control_type") for control in controls}
    missing = sorted(required - present)
    corpus = compile_all(repo_root, write=False)
    return {
        "schema_version": "EvaluatorCalibration.v1",
        "status": "structural_ready" if not missing else "hold",
        "controls_present": len(present),
        "missing_controls": missing,
        "corpus_contract_blockers": corpus["blocked_contract"],
        "judge_qualified": False,
        "judge_note": "Semantic judges remain unqualified until gold-label agreement and bias checks are run.",
        "model_calls": 0,
    }


def compare(
    repo_root: Path,
    slug: str,
    candidate: Path,
    profile: str,
    *,
    allow_model_calls: bool,
    max_tokens: int | None,
) -> dict[str, Any]:
    if profile not in PROFILE_TOKEN_CAPS:
        raise ValueError(f"unknown profile: {profile}")
    cap = PROFILE_TOKEN_CAPS[profile]
    if max_tokens is not None and max_tokens > cap:
        raise ValueError(f"requested token budget exceeds {profile} hard cap of {cap}")
    compiled = compile_skill(repo_root, slug, write=False)
    baseline = repo_root / "ssot" / f"{slug}.md"
    if compiled["status"] == "blocked_contract":
        return {"status": "blocked_contract", "slug": slug, "profile": profile, "model_calls": 0, "blockers": compiled["topology"]["known_ambiguities"]}
    if profile in {"static", "native"}:
        before = artifact_metrics(baseline)
        after = artifact_metrics(candidate)
        return {
            "status": "structural_ready",
            "slug": slug,
            "profile": profile,
            "baseline_sha256": artifact_hash(baseline),
            "candidate_sha256": artifact_hash(candidate),
            "before": before,
            "after": after,
            "size_delta": {key: after[key] - before[key] for key in ("lines", "words", "bytes", "model_tokens_estimate")},
            "model_calls": 0,
            "behavioral_claim": "none",
        }
    if not allow_model_calls:
        return {
            "status": "inconclusive",
            "slug": slug,
            "profile": profile,
            "reason": "model-mediated profile requires explicit --allow-model-calls",
            "hard_token_cap": cap,
            "model_calls": 0,
        }
    return {
        "status": "inconclusive",
        "slug": slug,
        "profile": profile,
        "reason": "live provider execution is intentionally disabled until adapter conformance and judge calibration pass",
        "hard_token_cap": cap,
        "model_calls": 0,
    }


def report_run(repo_root: Path, run_id: str) -> dict[str, Any]:
    path = repo_root / "reports" / "evals" / run_id / "summary.json"
    payload = load_json(path)
    verdict = payload.get("promotion_verdict")
    if isinstance(verdict, dict):
        validate_promotion_verdict(verdict, repo_root=repo_root)
    return payload
