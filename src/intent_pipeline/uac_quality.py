from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


QUALITY_PROFILE_DIR = ".meta/quality-profiles"
QUALITY_REVIEW_DIR = "reports/quality-reviews"

JUDGE_ORDER = (
    "operational_richness",
    "source_fidelity",
    "metadata_integrity",
)

JUDGE_TITLES = {
    "operational_richness": "Operational Richness",
    "source_fidelity": "Source Fidelity and Uplift",
    "metadata_integrity": "Metadata and Handoff Integrity",
}


@dataclass(frozen=True, slots=True)
class QualityProfile:
    name: str
    payload: dict[str, Any]

    @property
    def max_passes(self) -> int:
        return int(self.payload.get("max_passes") or 4)

    @property
    def targets(self) -> dict[str, int]:
        return {key: int(value) for key, value in dict(self.payload.get("judge_targets") or {}).items()}

    @property
    def required_markers(self) -> dict[str, tuple[str, ...]]:
        return {
            key: tuple(str(item) for item in values)
            for key, values in dict(self.payload.get("required_markers") or {}).items()
        }

    @property
    def local_benchmarks(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.payload.get("local_benchmarks") or ())

    @property
    def external_sources(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.payload.get("external_sources") or ())


def quality_profile_dir(repo_root: Path) -> Path:
    return repo_root / QUALITY_PROFILE_DIR


def quality_review_dir(repo_root: Path, slug: str) -> Path:
    return repo_root / QUALITY_REVIEW_DIR / slug


def quality_review_path(repo_root: Path, slug: str, pass_number: int, stamp: str) -> Path:
    return quality_review_dir(repo_root, slug) / f"{stamp}-pass-{pass_number}.json"


def latest_quality_review_path(repo_root: Path, slug: str) -> Path:
    return quality_review_dir(repo_root, slug) / "LATEST.md"


def load_quality_profile(repo_root: Path, slug: str, requested: str) -> QualityProfile:
    if requested != "auto":
        name = requested
    elif slug == "architecture":
        name = "architecture"
    else:
        name = "default"
    path = quality_profile_dir(repo_root) / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"quality profile not found: {path}")
    return QualityProfile(name=name, payload=json.loads(path.read_text(encoding="utf-8")))


def build_quality_plan(
    *,
    slug: str,
    profile: QualityProfile,
    descriptor_path: str,
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, Any]],
    max_passes_override: int | None = None,
) -> dict[str, Any]:
    max_passes = max_passes_override or profile.max_passes
    packets = []
    for judge_name in JUDGE_ORDER:
        packets.append(
            {
                "judge": judge_name,
                "title": JUDGE_TITLES[judge_name],
                "prompt_fields": {
                    "slug": slug,
                    "display_name_target": profile.payload.get("display_name") or slug,
                    "target_description": profile.payload.get("description") or "",
                    "candidate_ssot_body_or_path": f"ssot/{slug}.md",
                    "descriptor_path": descriptor_path,
                    "quality_profile": profile.name,
                    "local_benchmark_files": list(profile.local_benchmarks),
                    "external_source_set": list(profile.external_sources or source_refs),
                    "must_exceed": list(profile.payload.get("must_exceed") or ()),
                    "prohibited_regressions": list(profile.payload.get("prohibited_regressions") or ()),
                    "scoring_rubric": profile.targets,
                    "pass_number": 1,
                    "prior_pass_blockers": [],
                    "stop_target": profile.targets.get(judge_name),
                    "read_only_instruction": "Read-only judge. Do not propose orchestration ownership or runtime routing.",
                },
            }
        )
    return {
        "quality_profile": profile.name,
        "judge_targets": profile.targets,
        "max_passes": max_passes,
        "local_benchmarks": list(profile.local_benchmarks),
        "external_sources": list(profile.external_sources or source_refs),
        "benchmark_sources": list(benchmark_sources),
        "artifact_plan": {
            "profile_file": f".meta/quality-profiles/{profile.name}.json",
            "review_directory": f"reports/quality-reviews/{slug}/",
            "latest_review_file": f"reports/quality-reviews/{slug}/LATEST.md",
        },
        "judge_packets": packets,
        "stop_conditions": {
            "ship": "all judge thresholds met, no blocker, validation green when required",
            "revise": "thresholds not met and passes remain",
            "manual_review": "max passes reached or blocker remains unresolved",
        },
    }


def run_quality_loop(
    *,
    slug: str,
    profile: QualityProfile,
    candidate_text: str,
    descriptor: Mapping[str, Any],
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, Any]],
    max_passes: int,
) -> dict[str, Any]:
    current_text = candidate_text
    reports: list[dict[str, Any]] = []
    stop_reason = "max_passes_reached"
    final_status = "manual_review"
    final_pass = 0

    for pass_number in range(1, max_passes + 1):
        pass_report = evaluate_quality_pass(
            slug=slug,
            profile=profile,
            candidate_text=current_text,
            descriptor=descriptor,
            source_refs=source_refs,
            benchmark_sources=benchmark_sources,
            pass_number=pass_number,
            max_passes=max_passes,
        )
        reports.append(pass_report)
        final_pass = pass_number
        if pass_report["status"] == "ship":
            stop_reason = "thresholds_met"
            final_status = "ship"
            break
        if pass_number < max_passes:
            current_text = refine_candidate_text(current_text, pass_report, profile)
            final_status = "revise"

    if final_status != "ship" and reports:
        final_status = reports[-1]["status"]
    return {
        "quality_profile": profile.name,
        "status": final_status,
        "pass_count": final_pass,
        "stop_reason": stop_reason,
        "judge_reports": reports,
        "final_candidate_text": current_text,
        "consumption_hints": dict(profile.payload.get("consumption_hints") or {}),
    }


def evaluate_quality_pass(
    *,
    slug: str,
    profile: QualityProfile,
    candidate_text: str,
    descriptor: Mapping[str, Any],
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, Any]],
    pass_number: int,
    max_passes: int,
) -> dict[str, Any]:
    judge_reports = [
        _judge_operational_richness(profile, candidate_text),
        _judge_source_fidelity(profile, candidate_text, source_refs, benchmark_sources),
        _judge_metadata_integrity(profile, slug, candidate_text, descriptor),
    ]
    thresholds = profile.targets
    blockers = [
        issue
        for judge in judge_reports
        for issue in judge["blockers"]
    ]
    meets_targets = all(judge["score"] >= int(thresholds.get(judge["judge"]) or 0) for judge in judge_reports)
    if meets_targets and not blockers:
        status = "ship"
    elif pass_number < max_passes:
        status = "revise"
    else:
        status = "manual_review"
    return {
        "pass_number": pass_number,
        "status": status,
        "judge_reports": judge_reports,
        "blockers": blockers,
    }


def render_latest_review_markdown(
    *,
    slug: str,
    quality_result: Mapping[str, Any],
) -> str:
    lines = [
        f"# {slug} quality review",
        "",
        f"- Profile: `{quality_result.get('quality_profile')}`",
        f"- Status: `{quality_result.get('status')}`",
        f"- Passes: `{quality_result.get('pass_count')}`",
        f"- Stop reason: `{quality_result.get('stop_reason')}`",
        "",
    ]
    for report in quality_result.get("judge_reports") or []:
        lines.append(f"## Pass {report['pass_number']}")
        lines.append(f"- Status: `{report['status']}`")
        for judge in report.get("judge_reports") or []:
            lines.append(f"- {judge['title']}: `{judge['score']}/10`")
            for blocker in judge.get("blockers") or ():
                lines.append(f"  - blocker: {blocker}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def quality_descriptor_fields(
    *,
    profile: QualityProfile,
    quality_result: Mapping[str, Any],
    benchmark_sources: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "quality_profile": profile.name,
        "quality_status": quality_result.get("status"),
        "benchmark_sources": list(benchmark_sources),
        "judge_reports": list(quality_result.get("judge_reports") or []),
        "consumption_hints": dict(quality_result.get("consumption_hints") or profile.payload.get("consumption_hints") or {}),
        "quality_pass_count": int(quality_result.get("pass_count") or 0),
        "quality_stop_reason": quality_result.get("stop_reason"),
    }


def _judge_operational_richness(profile: QualityProfile, candidate_text: str) -> dict[str, Any]:
    markers = profile.required_markers.get("operational_richness", ())
    ratio, missing = _marker_ratio(candidate_text, markers)
    blockers = [f"missing operational marker: {item}" for item in missing]
    min_words = int(profile.payload.get("minimum_word_count") or 0)
    min_code_blocks = int(profile.payload.get("minimum_code_blocks") or 0)
    word_count = len(candidate_text.split())
    code_block_count = candidate_text.count("```") // 2
    if min_words and word_count < min_words:
        blockers.append(f"candidate is too thin: {word_count} words < {min_words}")
    if min_code_blocks and code_block_count < min_code_blocks:
        blockers.append(f"candidate has too few worked examples/code blocks: {code_block_count} < {min_code_blocks}")
    return {
        "judge": "operational_richness",
        "title": JUDGE_TITLES["operational_richness"],
        "score": _score_from_ratio(ratio, penalty=len(blockers)),
        "blockers": blockers,
    }


def _judge_source_fidelity(
    profile: QualityProfile,
    candidate_text: str,
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    markers = profile.required_markers.get("source_fidelity", ())
    ratio, missing = _marker_ratio(candidate_text, markers)
    blockers = [f"missing source-fidelity marker: {item}" for item in missing]
    if not source_refs and not benchmark_sources:
        blockers.append("no source set or benchmark set attached to quality run")
    return {
        "judge": "source_fidelity",
        "title": JUDGE_TITLES["source_fidelity"],
        "score": _score_from_ratio(ratio, penalty=len(blockers)),
        "blockers": blockers,
    }


def _judge_metadata_integrity(
    profile: QualityProfile,
    slug: str,
    candidate_text: str,
    descriptor: Mapping[str, Any],
) -> dict[str, Any]:
    markers = profile.required_markers.get("metadata_integrity", ())
    lowered = candidate_text.casefold()
    satisfied = 0
    missing: list[str] = []
    for marker in markers:
        marker_lower = marker.casefold()
        if marker_lower in lowered:
            satisfied += 1
            continue
        if marker_lower == "advisory" and descriptor.get("consumption_hints"):
            satisfied += 1
            continue
        if marker_lower == "descriptor" and descriptor:
            satisfied += 1
            continue
        missing.append(marker)
    ratio = 1.0 if not markers else satisfied / len(markers)
    blockers = [f"missing metadata-integrity marker: {item}" for item in missing]
    if str(descriptor.get("slug") or "") != slug:
        blockers.append("descriptor slug does not match candidate slug")
    minimal = (
        descriptor.get("layers", {}).get("minimal")
        if isinstance(descriptor.get("layers"), Mapping)
        else {}
    )
    if isinstance(minimal, Mapping):
        capability_type = str(minimal.get("capability_type") or "")
        review_status = str(minimal.get("review_status") or "")
        if capability_type == "manual_review" or review_status == "manual_review":
            blockers.append("candidate still resolves to manual_review and cannot auto-land")
    consumption_hints = descriptor.get("consumption_hints") or profile.payload.get("consumption_hints") or {}
    if not consumption_hints:
        blockers.append("descriptor lacks advisory consumption hints")
    leakage_patterns = (
        r"\byou are .*orchestrator\b",
        r"\bassign sub-agents\b",
        r"\bruntime delegation\b",
    )
    for pattern in leakage_patterns:
        if re.search(pattern, lowered) and "do not" not in lowered:
            blockers.append("candidate leaks orchestration or runtime-delegation ownership")
            break
    return {
        "judge": "metadata_integrity",
        "title": JUDGE_TITLES["metadata_integrity"],
        "score": _score_from_ratio(ratio, penalty=len(blockers)),
        "blockers": blockers,
    }


def refine_candidate_text(candidate_text: str, pass_report: Mapping[str, Any], profile: QualityProfile) -> str:
    refined = candidate_text
    templates = dict(profile.payload.get("refinement_templates") or {})
    missing_markers = []
    for judge in pass_report.get("judge_reports") or []:
        for blocker in judge.get("blockers") or []:
            if ": " in blocker:
                missing_markers.append(blocker.split(": ", 1)[1])
    for marker in missing_markers:
        if marker and marker not in refined and marker in templates:
            refined = refined.rstrip() + "\n\n" + str(templates[marker]).rstrip() + "\n"
    return refined


def _marker_ratio(candidate_text: str, markers: Sequence[str]) -> tuple[float, list[str]]:
    if not markers:
        return 1.0, []
    lowered = candidate_text.casefold()
    present = 0
    missing: list[str] = []
    for marker in markers:
        if marker.casefold() in lowered:
            present += 1
        else:
            missing.append(marker)
    return present / len(markers), missing


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
    "QUALITY_PROFILE_DIR",
    "QUALITY_REVIEW_DIR",
    "QualityProfile",
    "build_quality_plan",
    "latest_quality_review_path",
    "load_quality_profile",
    "quality_descriptor_fields",
    "quality_profile_dir",
    "quality_review_dir",
    "quality_review_path",
    "render_latest_review_markdown",
    "run_quality_loop",
]
