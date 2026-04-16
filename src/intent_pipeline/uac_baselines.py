from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


BASELINE_REGISTRY = "sources/ssot-baselines/index.json"


@dataclass(frozen=True, slots=True)
class BaselineScenario:
    scenario_id: str
    kind: str
    label: str
    must_contain: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "id": self.scenario_id,
            "kind": self.kind,
            "label": self.label,
            "must_contain": list(self.must_contain),
        }


@dataclass(frozen=True, slots=True)
class BaselineContext:
    slug: str
    strategy: str
    group: str
    baseline_path: str | None
    selected_commit: str | None
    richness_score: int
    line_count: int
    reason: str
    equivalent_commits: tuple[str, ...]
    expected_companions: tuple[str, ...]
    operator_invariants: tuple[str, ...]
    scenario_matrix: tuple[BaselineScenario, ...]
    historical_proof: dict[str, object]
    source: str
    verified_by_git_history: bool
    baseline_text: str | None

    def as_payload(self) -> dict[str, object]:
        return {
            "slug": self.slug,
            "strategy": self.strategy,
            "group": self.group,
            "baseline_path": self.baseline_path,
            "selected_commit": self.selected_commit,
            "richness_score": self.richness_score,
            "line_count": self.line_count,
            "reason": self.reason,
            "equivalent_commits": list(self.equivalent_commits),
            "expected_companions": list(self.expected_companions),
            "operator_invariants": list(self.operator_invariants),
            "scenario_matrix": [scenario.as_payload() for scenario in self.scenario_matrix],
            "historical_proof": dict(self.historical_proof),
            "source": self.source,
            "verified_by_git_history": self.verified_by_git_history,
            "has_baseline_text": self.baseline_text is not None,
        }


def historical_baseline_registry_path(repo_root: Path) -> Path:
    return repo_root / BASELINE_REGISTRY


def load_historical_baseline_registry(repo_root: Path) -> dict[str, Any]:
    path = historical_baseline_registry_path(repo_root)
    if not path.exists():
        return {"version": "uac-historical-baselines.missing", "skills": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def historical_richness_score(text: str) -> int:
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


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def baseline_artifact_findings(text: str) -> tuple[str, ...]:
    findings: list[str] = []
    lowered = text.casefold()
    if (
        "intent\n-" in lowered
        and "requested outcome\n-" in lowered
        and "rejected/out-of-scope signals\n-" in lowered
    ):
        findings.append("flattened_uac_prompt_sections")
    if "## invocation hints\nintent\n-" in lowered:
        findings.append("corrupted_invocation_hints_section")
    if "\n- - " in text:
        findings.append("nested_bullet_flattening")
    return tuple(dict.fromkeys(findings))


def resolve_historical_baseline(
    repo_root: Path,
    slug: str,
    *,
    candidate_text: str | None = None,
) -> BaselineContext:
    registry = load_historical_baseline_registry(repo_root)
    skill_entry = dict((registry.get("skills") or {}).get(slug) or {})
    if skill_entry:
        baseline_text = _baseline_text_from_registry(repo_root, slug, skill_entry)
        verified = _verify_registry_entry(repo_root, slug, skill_entry)
        return BaselineContext(
            slug=slug,
            strategy=str(skill_entry.get("strategy") or "registry_only"),
            group=str(skill_entry.get("group") or "unclassified"),
            baseline_path=_clean_relpath(skill_entry.get("baseline_path")),
            selected_commit=_clean_commit(
                skill_entry.get("selected_commit")
                or (skill_entry.get("historical_proof") or {}).get("materialized_from_commit")
            ),
            richness_score=int(skill_entry.get("richness_score") or 0),
            line_count=int(skill_entry.get("line_count") or 0),
            reason=str(skill_entry.get("reason") or ""),
            equivalent_commits=tuple(str(item) for item in skill_entry.get("equivalent_commits") or ()),
            expected_companions=tuple(str(item) for item in skill_entry.get("expected_companions") or ()),
            operator_invariants=tuple(str(item) for item in skill_entry.get("operator_invariants") or ()),
            scenario_matrix=_load_scenarios(skill_entry),
            historical_proof=dict(skill_entry.get("historical_proof") or {}),
            source="source_library",
            verified_by_git_history=verified,
            baseline_text=baseline_text,
        )

    derived = derive_historical_baseline(repo_root, slug, candidate_text=candidate_text)
    if derived is not None:
        return derived

    fallback_text = candidate_text
    return BaselineContext(
        slug=slug,
        strategy="candidate_seed",
        group="new_or_untracked",
        baseline_path=None,
        selected_commit=None,
        richness_score=historical_richness_score(fallback_text or ""),
        line_count=len((fallback_text or "").splitlines()),
        reason="No registry entry or git history available; use the candidate as the provisional seed baseline.",
        equivalent_commits=(),
        expected_companions=(),
        operator_invariants=(),
        scenario_matrix=(),
        historical_proof={},
        source="candidate_seed",
        verified_by_git_history=False,
        baseline_text=fallback_text,
    )


def derive_historical_baseline(
    repo_root: Path,
    slug: str,
    *,
    candidate_text: str | None = None,
) -> BaselineContext | None:
    history = _git_history(repo_root, slug)
    if not history:
        current_path = repo_root / "ssot" / f"{slug}.md"
        if current_path.exists():
            current_text = current_path.read_text(encoding="utf-8")
            return BaselineContext(
                slug=slug,
                strategy="head_snapshot",
                group="derived_current",
                baseline_path=str(current_path.relative_to(repo_root)),
                selected_commit=None,
                richness_score=historical_richness_score(current_text),
                line_count=len(current_text.splitlines()),
                reason="No git history was available, so the current SSOT body is the strongest available baseline.",
                equivalent_commits=(),
                expected_companions=(),
                operator_invariants=(),
                scenario_matrix=(),
                historical_proof={},
                source="current_ssot",
                verified_by_git_history=False,
                baseline_text=current_text,
            )
        return None

    ordered = []
    for index, commit in enumerate(history):
        text = _git_show(repo_root, commit, slug)
        if text is None:
            continue
        ordered.append(
            {
                "commit": commit,
                "order": index,
                "text": text,
                "richness_score": historical_richness_score(text),
                "line_count": len(text.splitlines()),
            }
        )
    if not ordered:
        return None
    strongest_score = max(item["richness_score"] for item in ordered)
    strongest = [item for item in ordered if item["richness_score"] == strongest_score]
    selected = strongest[0]
    return BaselineContext(
        slug=slug,
        strategy="derived_history",
        group="derived",
        baseline_path=None,
        selected_commit=_clean_commit(selected["commit"]),
        richness_score=int(selected["richness_score"]),
        line_count=int(selected["line_count"]),
        reason="Selected from git history using the strongest richness score, then the latest commit within the highest-scoring equivalence class.",
        equivalent_commits=tuple(_clean_commit(item["commit"]) for item in strongest[1:]),
        expected_companions=(),
        operator_invariants=(),
        scenario_matrix=(),
        historical_proof={},
        source="git_history",
        verified_by_git_history=True,
        baseline_text=str(selected["text"]),
    )


def evaluate_candidate_against_baseline(
    candidate_text: str,
    baseline: BaselineContext,
) -> dict[str, object]:
    candidate_richness = historical_richness_score(candidate_text)
    candidate_lines = len(candidate_text.splitlines())
    scenarios = evaluate_scenarios(candidate_text, baseline.scenario_matrix, baseline.operator_invariants)
    hard_failures: list[str] = []

    scenario_failures = [scenario for scenario in scenarios if not scenario["passed"]]
    if scenario_failures:
        hard_failures.extend(
            f"baseline scenario failed: {scenario['id']} missing {', '.join(scenario['missing_markers'])}"
            for scenario in scenario_failures
        )

    richness_gap = max(0, baseline.richness_score - candidate_richness)
    if baseline.richness_score >= 5 and richness_gap >= 3:
        hard_failures.append(
            f"candidate richness regressed from baseline {baseline.richness_score} to {candidate_richness}"
        )
    if baseline.line_count and candidate_lines < max(80, int(baseline.line_count * 0.5)):
        hard_failures.append(
            f"candidate body is materially thinner than the baseline ({candidate_lines} lines vs {baseline.line_count})"
        )
    if baseline.baseline_text and baseline.baseline_text != candidate_text and candidate_richness > baseline.richness_score and not scenario_failures:
        classification = "additive"
    elif baseline.baseline_text and baseline.baseline_text == candidate_text:
        classification = "preserved"
    elif hard_failures:
        classification = "flattened"
    elif baseline.richness_score == candidate_richness and not scenario_failures:
        classification = "preserved"
    elif candidate_richness >= baseline.richness_score and not scenario_failures:
        classification = "additive"
    else:
        classification = "normalized"

    pass_rate = 1.0 if not scenarios else sum(1 for item in scenarios if item["passed"]) / len(scenarios)
    score = _score_from_ratio(pass_rate, penalty=min(5, len(hard_failures)))
    return {
        "classification": classification,
        "candidate_richness": candidate_richness,
        "candidate_line_count": candidate_lines,
        "baseline_richness": baseline.richness_score,
        "baseline_line_count": baseline.line_count,
        "scenario_results": scenarios,
        "hard_failures": hard_failures,
        "score": score,
    }


def evaluate_scenarios(
    candidate_text: str,
    scenarios: Sequence[BaselineScenario],
    operator_invariants: Sequence[str] = (),
) -> list[dict[str, object]]:
    lowered = candidate_text.casefold()
    results: list[dict[str, object]] = []
    for scenario in scenarios:
        missing = [marker for marker in scenario.must_contain if marker.casefold() not in lowered]
        results.append(
            {
                "id": scenario.scenario_id,
                "kind": scenario.kind,
                "label": scenario.label,
                "passed": not missing,
                "missing_markers": missing,
            }
        )
    if operator_invariants:
        missing = [marker for marker in operator_invariants if marker.casefold() not in lowered]
        results.append(
            {
                "id": "operator_invariants",
                "kind": "hybrid_invariants",
                "label": "historical operator invariants",
                "passed": not missing,
                "missing_markers": missing,
            }
        )
    return results


def validate_registry_entry(repo_root: Path, slug: str) -> dict[str, object]:
    baseline = resolve_historical_baseline(repo_root, slug)
    derived = derive_historical_baseline(repo_root, slug)
    matches = bool(derived and baseline.selected_commit and baseline.selected_commit == derived.selected_commit)
    return {
        "slug": slug,
        "baseline_path": baseline.baseline_path,
        "registry_commit": baseline.selected_commit,
        "derived_commit": derived.selected_commit if derived else None,
        "registry_matches_history": matches if baseline.selected_commit else False,
        "baseline_source": baseline.source,
        "verified_by_git_history": baseline.verified_by_git_history,
    }


def persist_source_baseline(
    repo_root: Path,
    *,
    slug: str,
    baseline_text: str,
    overwrite: bool = False,
    source_kind: str | None = None,
    source_path: str | None = None,
    source_sha256: str | None = None,
    source_commit: str | None = None,
) -> dict[str, object]:
    registry = load_historical_baseline_registry(repo_root)
    skills = dict(registry.get("skills") or {})
    entry = dict(skills.get(slug) or {})
    baseline_path = _clean_relpath(entry.get("baseline_path")) or f"sources/ssot-baselines/{slug}/baseline.md"
    path = repo_root / baseline_path
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate_text = baseline_text.rstrip() + "\n"
    existing_text = path.read_text(encoding="utf-8") if path.exists() else None
    blocked_reasons = tuple(_baseline_regression_reasons(candidate_text, existing_text))
    created = not path.exists()
    updated = False
    if overwrite or not path.exists():
        path.write_text(candidate_text, encoding="utf-8")
        updated = True
        blocked_reasons = ()
    elif existing_text != candidate_text and not blocked_reasons:
        path.write_text(candidate_text, encoding="utf-8")
        updated = True
    current_text = path.read_text(encoding="utf-8")
    entry["strategy"] = str(entry.get("strategy") or "source_library")
    entry["group"] = str(entry.get("group") or "applied_baseline")
    entry["baseline_path"] = baseline_path
    entry["richness_score"] = historical_richness_score(current_text)
    entry["line_count"] = len(current_text.splitlines())
    entry["reason"] = str(
        entry.get("reason")
        or "Repo-resident baseline source snapshot used as the fidelity oracle for future UAC judging."
    )
    historical_proof = dict(entry.get("historical_proof") or {})
    historical_proof.setdefault("materialized_from_commit", None)
    if source_kind is not None:
        historical_proof["materialized_from_source_kind"] = source_kind
    if source_path is not None:
        historical_proof["materialized_from_path"] = source_path
    if source_sha256 is not None:
        historical_proof["materialized_from_sha256"] = source_sha256
    if source_commit is not None:
        historical_proof["materialized_from_commit"] = _clean_commit(source_commit)
    historical_proof["last_materialized_at"] = datetime.now(timezone.utc).isoformat()
    if blocked_reasons:
        historical_proof["last_blocked_reasons"] = list(blocked_reasons)
    elif "last_blocked_reasons" in historical_proof:
        historical_proof.pop("last_blocked_reasons", None)
    entry["historical_proof"] = historical_proof
    if source_commit is not None:
        entry["selected_commit"] = _clean_commit(source_commit)
    skills[slug] = entry
    registry["version"] = str(registry.get("version") or "uac-baseline-sources.v1")
    registry["skills"] = skills
    historical_baseline_registry_path(repo_root).parent.mkdir(parents=True, exist_ok=True)
    historical_baseline_registry_path(repo_root).write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return {
        "slug": slug,
        "baseline_path": baseline_path,
        "created": created,
        "updated": updated,
        "blocked_reasons": list(blocked_reasons),
    }


def _baseline_text_from_registry(repo_root: Path, slug: str, entry: Mapping[str, object]) -> str | None:
    baseline_path = _clean_relpath(entry.get("baseline_path"))
    if baseline_path:
        path = repo_root / baseline_path
        if path.exists():
            return path.read_text(encoding="utf-8")
    strategy = str(entry.get("strategy") or "")
    selected_commit = _clean_commit(entry.get("selected_commit"))
    if strategy in {"head_snapshot", "head_plus_invariants"}:
        current_path = repo_root / "ssot" / f"{slug}.md"
        if current_path.exists():
            return current_path.read_text(encoding="utf-8")
    if selected_commit:
        return _git_show(repo_root, selected_commit, slug)
    return None


def _verify_registry_entry(repo_root: Path, slug: str, entry: Mapping[str, object]) -> bool:
    baseline_path = _clean_relpath(entry.get("baseline_path"))
    if baseline_path:
        path = repo_root / baseline_path
        if not path.exists():
            return False
    selected_commit = _clean_commit(entry.get("selected_commit"))
    if not selected_commit:
        return False
    derived = derive_historical_baseline(repo_root, slug)
    return bool(derived and derived.selected_commit == selected_commit)


def _load_scenarios(entry: Mapping[str, object]) -> tuple[BaselineScenario, ...]:
    scenarios = []
    for raw in entry.get("scenario_matrix") or ():
        if not isinstance(raw, Mapping):
            continue
        scenarios.append(
            BaselineScenario(
                scenario_id=str(raw.get("id") or ""),
                kind=str(raw.get("kind") or "validation"),
                label=str(raw.get("label") or raw.get("id") or "scenario"),
                must_contain=tuple(str(item) for item in raw.get("must_contain") or ()),
            )
        )
    return tuple(scenarios)


def _git_history(repo_root: Path, slug: str) -> list[str]:
    path = repo_root / "ssot" / f"{slug}.md"
    if not (repo_root / ".git").exists() or not path.exists():
        return []
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H", "--", str(path.relative_to(repo_root))],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _git_show(repo_root: Path, commit: str, slug: str) -> str | None:
    rel_path = f"ssot/{slug}.md"
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{rel_path}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout


def _clean_commit(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:8]


def _clean_relpath(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().strip("/")
    return normalized or None


def _baseline_regression_reasons(candidate_text: str, existing_text: str | None) -> list[str]:
    reasons = [f"artifact:{finding}" for finding in baseline_artifact_findings(candidate_text)]
    if not existing_text:
        return reasons

    existing_richness = historical_richness_score(existing_text)
    candidate_richness = historical_richness_score(candidate_text)
    if existing_richness >= 5 and candidate_richness <= existing_richness - 3:
        reasons.append(
            f"richness:{candidate_richness} is materially weaker than existing {existing_richness}"
        )

    existing_lines = len(existing_text.splitlines())
    candidate_lines = len(candidate_text.splitlines())
    if existing_lines and candidate_lines < max(80, int(existing_lines * 0.5)):
        reasons.append(f"line_count:{candidate_lines} is materially thinner than existing {existing_lines}")
    return reasons


def _score_from_ratio(ratio: float, *, penalty: int) -> int:
    if ratio >= 0.99:
        score = 10
    elif ratio >= 0.9:
        score = 9
    elif ratio >= 0.8:
        score = 8
    elif ratio >= 0.7:
        score = 7
    elif ratio >= 0.6:
        score = 6
    elif ratio >= 0.5:
        score = 5
    elif ratio >= 0.4:
        score = 4
    elif ratio >= 0.3:
        score = 3
    elif ratio >= 0.2:
        score = 2
    else:
        score = 1
    return max(1, score - penalty)


__all__ = [
    "BaselineContext",
    "BaselineScenario",
    "baseline_artifact_findings",
    "evaluate_candidate_against_baseline",
    "evaluate_scenarios",
    "historical_baseline_registry_path",
    "historical_richness_score",
    "load_historical_baseline_registry",
    "persist_source_baseline",
    "resolve_historical_baseline",
    "text_sha256",
    "validate_registry_entry",
]
