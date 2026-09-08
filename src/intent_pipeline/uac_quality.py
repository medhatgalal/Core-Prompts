from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from intent_pipeline.uac_baselines import (
    BaselineContext,
    evaluate_candidate_against_baseline,
    matching_requirement_review,
    resolve_historical_baseline,
    text_sha256,
    validate_requirement_reviews,
)
from intent_pipeline.uac_templates import load_capability_template


QUALITY_PROFILE_DIR = ".meta/quality-profiles"
QUALITY_REVIEW_DIR = "reports/quality-reviews"
REPO_ROOT = Path(__file__).resolve().parents[2]

JUDGE_ORDER = (
    "source_fidelity",
    "operational_richness",
    "metadata_integrity",
    "benchmark_readiness",
)

JUDGE_TITLES = {
    "operational_richness": "Operational Richness",
    "source_fidelity": "Source Fidelity and Uplift",
    "metadata_integrity": "Metadata and Handoff Integrity",
    "benchmark_readiness": "Benchmark Readiness and Template Fit",
}

MARKER_ALIASES = {
    "## workflow": ("## Invocation", "## Commands", "## Workflow Contract", "## Standard Workflow"),
    "## rules": (
        "## Rules",
        "### Gate Condition",
        "### Shaped Status Rules",
        "### Verdict Rules",
        "### Review Output Rules",
        "### Scoring Thresholds",
        "Non-Negotiable",
        "## Core Principles",
    ),
    "## tool boundaries": ("Tool Boundaries:",),
    "## constraints": ("## Constraints", "## Tool Boundaries", "No-Gos & Boundaries", "Forbidden:"),
    "## output directory": (
        "## Output Directory",
        "## Output Format",
        "### `pitch export",
        "write to a specified location",
        "Outputs as clean markdown",
    ),
    "constraints": ("Constraints", "## Tool Boundaries", "No-Gos & Boundaries", "Forbidden:"),
    "do not": ("do not", "does NOT", "Forbidden:", "must not"),
    "descriptor": ("descriptor", "sidecar descriptor", ".meta/capabilities"),
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
    elif slug in {"architecture", "engos-design-architecture"}:
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
    capability_type: str,
    descriptor_path: str,
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, Any]],
    max_passes_override: int | None = None,
) -> dict[str, Any]:
    max_passes = max_passes_override or profile.max_passes
    template = load_capability_template(REPO_ROOT, capability_type)
    baseline = resolve_historical_baseline(REPO_ROOT, slug)
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
                    "capability_template": template.name,
                    "local_benchmark_files": list(profile.local_benchmarks),
                    "external_source_set": list(profile.external_sources or source_refs),
                    "must_exceed": list(profile.payload.get("must_exceed") or ()),
                    "prohibited_regressions": list(profile.payload.get("prohibited_regressions") or ()),
                    "scoring_rubric": profile.targets,
                    "benchmark_dimensions": list(template.benchmark_dimensions),
                    "pass_number": 1,
                    "prior_pass_blockers": [],
                    "stop_target": profile.targets.get(judge_name),
                    "read_only_instruction": "Read-only judge. Do not propose orchestration ownership or runtime routing.",
                },
            }
        )
    return {
        "quality_profile": profile.name,
        "assessment_scope": "mechanical_structure_only_not_semantic_or_behavioral_proof",
        "judge_targets": profile.targets,
        "max_passes": max_passes,
        "gate_order": [
            "historical baseline selection",
            "prompt-body fidelity",
            "operational richness",
            "metadata integrity",
            "benchmark readiness",
        ],
        "historical_baseline": baseline.as_payload(),
        "hard_fail_rules": [
            "fail if a rich prompt body is replaced by a capability summary",
            "fail if module-specific sections are reduced to shallow one-liners",
            "fail if a generic UAC template shape replaces an operational command, mode, help, or workflow contract",
            "fail if direct operating instructions move into metadata and disappear from the body",
            "fail if orchestration or portability language weakens user-facing execution semantics",
        ],
        "validation_matrix": [scenario.as_payload() for scenario in baseline.scenario_matrix],
        "local_benchmarks": list(profile.local_benchmarks),
        "external_sources": list(profile.external_sources or source_refs),
        "benchmark_sources": list(benchmark_sources),
        "artifact_plan": {
            "profile_file": f".meta/quality-profiles/{profile.name}.json",
            "template_file": f".meta/capability-templates/{template.name}.json",
            "review_directory": f"reports/quality-reviews/{slug}/",
            "latest_review_file": f"reports/quality-reviews/{slug}/LATEST.md",
        },
        "judge_packets": packets,
        "stop_conditions": {
            "structural_ready": "all structural judge thresholds met, no blocker, validation green when required",
            "revise": "thresholds not met and passes remain",
            "manual_review": "candidate unchanged or repeated, max passes reached, or blocker remains unresolved",
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
    source_text: str | Sequence[str] | None = None,
    semantic_reviews: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    current_text = candidate_text
    reports: list[dict[str, Any]] = []
    stop_reason = "max_passes_reached"
    final_status = "manual_review"
    final_pass = 0
    capability_type = str(((descriptor.get("layers") or {}).get("minimal") or {}).get("capability_type") or descriptor.get("capability_type") or "skill")
    template = load_capability_template(REPO_ROOT, capability_type)
    baseline = resolve_historical_baseline(REPO_ROOT, slug, candidate_text=candidate_text)
    seen_candidates = {text_sha256(current_text)}

    for pass_number in range(1, max_passes + 1):
        pass_report = evaluate_quality_pass(
            slug=slug,
            profile=profile,
            candidate_text=current_text,
            baseline=baseline,
            source_text=source_text,
            descriptor=descriptor,
            source_refs=source_refs,
            benchmark_sources=benchmark_sources,
            pass_number=pass_number,
            max_passes=max_passes,
            template_name=template.name,
            template=template.payload,
            semantic_reviews=semantic_reviews,
        )
        reports.append(pass_report)
        final_pass = pass_number
        if pass_report["status"] == "structural_ready":
            stop_reason = "thresholds_met"
            final_status = "structural_ready"
            break
        if pass_number < max_passes:
            refined = refine_candidate_text(current_text, pass_report, profile)
            if refined == current_text:
                stop_reason = "candidate_unchanged"
                final_status = "manual_review"
                break
            if text_sha256(refined) in seen_candidates:
                stop_reason = "candidate_cycle_detected"
                final_status = "manual_review"
                break
            seen_candidates.add(text_sha256(refined))
            current_text = refined
            final_status = "revise"

    if final_status != "structural_ready":
        final_status = "manual_review"
    return {
        "quality_profile": profile.name,
        "status": final_status,
        "pass_count": final_pass,
        "stop_reason": stop_reason,
        "historical_baseline": baseline.as_payload(),
        "judge_reports": reports,
        "final_candidate_text": current_text,
        "scorecard": dict(reports[-1].get("scorecard") or {}) if reports else {},
        "consumption_hints": dict(profile.payload.get("consumption_hints") or {}),
        "repair_requests": reports[-1].get("repair_requests", []) if reports else [],
        "assessment_scope": "mechanical_structure_and_bound_external_review_attestations",
        "behavioral_status": "behavioral_pending",
    }


def evaluate_quality_pass(
    *,
    slug: str,
    profile: QualityProfile,
    candidate_text: str,
    baseline: BaselineContext,
    descriptor: Mapping[str, Any],
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, Any]],
    pass_number: int,
    max_passes: int,
    template_name: str,
    template: Mapping[str, Any],
    source_text: str | Sequence[str] | None = None,
    semantic_reviews: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    # Package assembly establishes available content, never actual model consumption.
    from intent_pipeline.capability_resources import ResourceContractError, effective_capability_text
    resource_failures: list[str] = []
    try:
        effective_text = effective_capability_text(REPO_ROOT, slug, candidate_text)
        resource_texts = _load_declared_capability_resource_texts(slug, candidate_text)
    except ResourceContractError as error:
        effective_text = candidate_text
        resource_texts = ()
        resource_failures.append(f"resource contract invalid: {error}")
    review_original_texts = [source_text] if isinstance(source_text, str) else list(source_text or ())
    if baseline.baseline_text is not None:
        review_original_texts.append(baseline.baseline_text)
    current_source = REPO_ROOT / "ssot" / f"{slug}.md"
    if current_source.is_file():
        review_original_texts.append(current_source.read_text(encoding="utf-8"))
    source_fidelity = _judge_source_fidelity(profile, slug, candidate_text, baseline, source_refs, benchmark_sources,
        effective_text=effective_text, preserved_resource_texts=resource_texts, semantic_reviews=semantic_reviews,
        review_original_texts=review_original_texts)
    source_failures = evaluate_imported_source_fidelity(
        candidate_text, source_text,
        preserved_resource_texts=resource_texts, slug=slug,
        effective_text=effective_text, semantic_reviews=semantic_reviews,
        review_original_texts=review_original_texts,
    )
    source_failures.extend(resource_failures)
    if source_failures:
        source_fidelity['blockers'].extend(source_failures)
        source_fidelity['score'] = min(source_fidelity['score'], 1)
        source_fidelity['classification'] = 'flattened'
    operational_richness = _judge_operational_richness(profile, effective_text)
    metadata_integrity = _judge_metadata_integrity(profile, slug, effective_text, descriptor)
    benchmark_readiness = _judge_benchmark_readiness(profile, effective_text, descriptor, template_name=template_name, template=template)
    metadata_integrity = _cap_dependent_judge_from_source_fidelity(profile, source_fidelity, metadata_integrity)
    benchmark_readiness = _cap_dependent_judge_from_source_fidelity(profile, source_fidelity, benchmark_readiness)
    judge_reports = [
        source_fidelity,
        operational_richness,
        metadata_integrity,
        benchmark_readiness,
    ]
    thresholds = profile.targets
    blockers = [
        issue
        for judge in judge_reports
        for issue in judge["blockers"]
    ]
    semantic_findings = semantic_review_findings(effective_text)
    blockers.extend(f"semantic review required: {finding['message']}" for finding in semantic_findings)
    meets_targets = all(judge["score"] >= int(thresholds.get(judge["judge"]) or 0) for judge in judge_reports)
    if meets_targets and not blockers:
        status = "structural_ready"
    elif pass_number < max_passes:
        status = "revise"
    else:
        status = "manual_review"
    return {
        "pass_number": pass_number,
        "status": status,
        "historical_baseline": baseline.as_payload(),
        "judge_reports": judge_reports,
        "blockers": blockers,
        "scorecard": _pass_scorecard(judge_reports),
        "template_name": template_name,
        "effective_sha256": text_sha256(effective_text),
        "semantic_findings": semantic_findings,
        "repair_requests": _repair_requests(blockers, semantic_findings),
        "dimension_inventory": [
            {"dimension": judge["judge"], "status": "unresolved" if judge["blockers"] else "mechanical_checks_passed"}
            for judge in judge_reports
        ] + [{"dimension": "semantic_consistency", "status": "semantic_review_required" if semantic_findings else "no_detected_conflict_not_semantic_proof"}],
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
        f"- Scorecard: `{json.dumps(quality_result.get('scorecard') or {}, sort_keys=True)}`",
        "",
    ]
    baseline = quality_result.get("historical_baseline") or {}
    if baseline:
        lines.extend(
            [
                "## Historical Baseline",
                f"- Source path: `{baseline.get('baseline_path')}`",
                f"- Lineage commit: `{baseline.get('selected_commit')}`",
                f"- Strategy: `{baseline.get('strategy')}`",
                f"- Group: `{baseline.get('group')}`",
                f"- Source: `{baseline.get('source')}`",
                f"- Verified by git history: `{baseline.get('verified_by_git_history')}`",
                f"- Reason: {baseline.get('reason')}",
                "",
            ]
        )
    for report in quality_result.get("judge_reports") or []:
        lines.append(f"## Pass {report['pass_number']}")
        lines.append(f"- Status: `{report['status']}`")
        if report.get("scorecard"):
            lines.append(f"- Scorecard: `{json.dumps(report['scorecard'], sort_keys=True)}`")
        for judge in report.get("judge_reports") or []:
            lines.append(f"- {judge['title']}: `{judge['score']}/10`")
            if judge.get("classification"):
                lines.append(f"  - classification: `{judge['classification']}`")
            for scenario in judge.get("scenario_results") or ():
                lines.append(
                    f"  - scenario `{scenario['id']}`: `{'pass' if scenario['passed'] else 'fail'}`"
                    + (
                        f" missing {', '.join(scenario['missing_markers'])}"
                        if scenario.get("missing_markers")
                        else ""
                    )
                )
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
        "quality_scorecard": dict(quality_result.get("scorecard") or {}),
        "historical_baseline": dict(quality_result.get("historical_baseline") or {}),
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
    slug: str,
    candidate_text: str,
    baseline: BaselineContext,
    source_refs: Sequence[str],
    benchmark_sources: Sequence[Mapping[str, Any]],
    *, effective_text: str | None = None,
    preserved_resource_texts: Sequence[str] = (),
    semantic_reviews: Sequence[Mapping[str, Any]] = (),
    review_original_texts: Sequence[str] = (),
) -> dict[str, Any]:
    markers = profile.required_markers.get("source_fidelity", ())
    ratio, missing = _marker_ratio(effective_text or candidate_text, markers)
    blockers = [f"missing source-fidelity marker: {item}" for item in missing]
    if not source_refs and not benchmark_sources:
        blockers.append("no source set or benchmark set attached to quality run")
    fidelity = evaluate_candidate_against_baseline(
        candidate_text,
        baseline,
        preserved_resource_texts=preserved_resource_texts,
        effective_text=effective_text, semantic_reviews=semantic_reviews,
        review_original_texts=review_original_texts,
    )
    blockers.extend(str(item) for item in fidelity["hard_failures"])
    score = min(_score_from_ratio(ratio, penalty=len(blockers)), int(fidelity["score"]))
    return {
        "judge": "source_fidelity",
        "title": JUDGE_TITLES["source_fidelity"],
        "score": score,
        "blockers": blockers,
        "classification": fidelity["classification"],
        "scenario_results": fidelity["scenario_results"],
        "reviewed_deltas": fidelity["reviewed_deltas"],
        "requirement_review": fidelity["requirement_review"],
        "scorecard": {
            "baseline_richness": int(fidelity["baseline_richness"]),
            "candidate_richness": int(fidelity["candidate_richness"]),
            "baseline_operational_score": int(fidelity["baseline_operational_score"]),
            "candidate_operational_score": int(fidelity["candidate_operational_score"]),
            "baseline_preserved_in_resource": bool(fidelity.get("baseline_preserved_in_resource")),
        },
        "baseline_commit": baseline.selected_commit,
        "baseline_slug": slug,
    }


def evaluate_imported_source_fidelity(
    candidate_text: str, source_text: str | Sequence[str] | None, *,
    preserved_resource_texts: Sequence[str] = (),
    slug: str = "",
    effective_text: str | None = None,
    semantic_reviews: Sequence[Mapping[str, Any]] = (),
    review_original_texts: Sequence[str] = (),
) -> list[str]:
    """Conservative content retention, separate from historical and behavioral proof.

    Require the operating body and nested metadata schemas to remain intact in
    the candidate or one declared resource. Scalar root metadata may normalize.
    Exact retention is the default. A separately supplied independent review can
    disposition a rewrite; Python checks bindings, not identity or semantics.
    """
    originals = [source_text] if isinstance(source_text, str) else list(source_text or ())
    originals.extend(review_original_texts)
    review_failures = validate_requirement_reviews(
        semantic_reviews, slug=slug, original_texts=originals,
        candidate_text=candidate_text, effective_text=effective_text if effective_text is not None else candidate_text,
    )
    if review_failures:
        return review_failures
    if source_text is None:
        return []  # Backward-compatible API for historical-only quality runs.
    if not isinstance(source_text, str):
        return [failure for text in source_text for failure in evaluate_imported_source_fidelity(
            candidate_text, text, preserved_resource_texts=preserved_resource_texts,
            slug=slug, effective_text=effective_text, semantic_reviews=semantic_reviews,
            review_original_texts=originals,
        )]
    if not source_text.strip():
        return ['imported source content is unavailable; re-ingest before judging or applying']
    if matching_requirement_review(semantic_reviews, slug=slug, original_text=source_text,
                                   candidate_text=candidate_text, effective_text=effective_text or candidate_text):
        return []
    source = source_text.replace('\r\n', '\n').strip()
    source = re.sub(r'\nCapability resource: `[^`]+`\s*$', '', source).strip()
    contracts = []
    while source.startswith('---\n'):
        end = re.search(r'^---[ \t]*$', source[4:], re.MULTILINE)
        if not end:
            break
        header = source[4:4 + end.start()]
        # A root entry extends to the next root key, including comments,
        # blank lines, unindented sequences, and multiline flow collections.
        entries = list(re.finditer(r'^(?P<key>[^ \t#\n][^:\n]*):[ \t]*(?P<value>[^\n]*)', header, re.MULTILINE))
        normalizable_metadata = {
            'name', 'display_name', 'description', 'kind', 'capability_type',
            'install_target', 'agent_tools', 'version', 'author', 'compatibility',
            'supported_agents', 'agents',
        }
        if not entries and header.strip():
            contracts.append(header.strip())
        for index, entry in enumerate(entries):
            key = entry.group('key').strip().strip('"').strip("'")
            value = entry.group('value').strip()
            # Only recognized scalar metadata may normalize. Everything else
            # is retained verbatim, including YAML forms we do not interpret.
            scalar_metadata = key in normalizable_metadata and value and not value.startswith(('#', '{', '[', '&', '*', '!'))
            if not scalar_metadata:
                stop = entries[index + 1].start() if index + 1 < len(entries) else len(header)
                contracts.append(header[entry.start():stop].strip())
        source = source[4 + end.end():].strip('\n')
    if source.strip():
        contracts.append(source.strip())
    candidates = [text.replace('\r\n', '\n') for text in (candidate_text, *preserved_resource_texts)]
    if effective_text is not None:
        candidates.append(effective_text.replace('\r\n', '\n'))
    missing = sum(not any(contract in text for text in candidates) for contract in contracts)
    return [f'imported source content was not preserved ({missing} operating body/schema blocks missing)'] if missing else []


def _load_declared_capability_resource_texts(
    slug: str, candidate_text: str, *, repo_root: Path | None = None,
) -> tuple[str, ...]:
    from intent_pipeline.capability_resources import load_resource_bundle
    resource_root = ((repo_root or REPO_ROOT) / "sources" / "capability-resources" / slug).resolve()
    if (resource_root / "resource-map.json").exists():
        return tuple(item["content"] for item in load_resource_bundle(resource_root)["resources"])
    resource_refs = set()
    for match in re.finditer(r"`?(resources/[A-Za-z0-9_.:/@+~=-][A-Za-z0-9_./:@+~=-]*)`?", candidate_text):
        resource_refs.add(match.group(1))
    texts: list[str] = []
    for resource_ref in sorted(resource_refs):
        relative = resource_ref.removeprefix("resources/")
        source_path = (resource_root / relative).resolve()
        if source_path.is_relative_to(resource_root) and source_path.is_file():
            texts.append(source_path.read_text(encoding="utf-8"))
    return tuple(texts)


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
    minimal = (
        descriptor.get("layers", {}).get("minimal")
        if isinstance(descriptor.get("layers"), Mapping)
        else {}
    )
    for marker in markers:
        marker_lower = marker.casefold()
        aliases = (marker, *MARKER_ALIASES.get(marker_lower, ()))
        if any(alias.casefold() in lowered for alias in aliases):
            satisfied += 1
            continue
        if marker_lower == "advisory" and (
            descriptor.get("consumption_hints")
            or (isinstance(minimal, Mapping) and minimal.get("review_status"))
            or (isinstance(minimal, Mapping) and minimal.get("tool_policy"))
        ):
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
    if isinstance(minimal, Mapping):
        capability_type = str(minimal.get("capability_type") or "")
        review_status = str(minimal.get("review_status") or "")
        if capability_type == "manual_review" or review_status == "manual_review":
            blockers.append("candidate still resolves to manual_review and cannot auto-land")
    consumption_hints = descriptor.get("consumption_hints") or profile.payload.get("consumption_hints") or {}
    if not consumption_hints:
        blockers.append("descriptor lacks advisory consumption hints")
    handoff_contract = descriptor.get("handoff_contract") or {}
    has_structured_handoff_fallback = (
        isinstance(minimal, Mapping)
        and bool(minimal.get("required_inputs"))
        and bool(minimal.get("expected_outputs"))
        and bool(minimal.get("emitted_surfaces"))
        and bool(minimal.get("install_target"))
    )
    if not isinstance(handoff_contract, Mapping) or not handoff_contract:
        if not has_structured_handoff_fallback:
            blockers.append("descriptor lacks orchestrator handoff payload")
    recommendation = descriptor.get("recommendation") or {}
    has_next_action_fallback = (
        isinstance(minimal, Mapping)
        and bool(minimal.get("resources"))
        and bool(minimal.get("tool_policy"))
        and bool(minimal.get("review_status"))
    )
    if not isinstance(recommendation, Mapping) or not tuple(recommendation.get("next_actions") or ()):
        if not has_next_action_fallback:
            blockers.append("descriptor lacks orchestrator next actions")
    # Authorized subagent use is not host/runtime ownership. Match concrete
    # ownership claims in active prose; a distant 'do not' cannot cancel one.
    for line in _active_instruction_lines(candidate_text):
        if re.search(r"\b(?:own|override|control) (?:the )?(?:host runtime|runtime policy|host delegation policy)\b", line, re.I) and not re.search(r"\b(?:not|never|forbidden)\b", line, re.I):
            blockers.append("semantic review required: candidate claims host runtime-policy ownership")
            break
    return {
        "judge": "metadata_integrity",
        "title": JUDGE_TITLES["metadata_integrity"],
        "score": _score_from_ratio(ratio, penalty=len(blockers)),
        "blockers": blockers,
    }


def _judge_benchmark_readiness(
    profile: QualityProfile,
    candidate_text: str,
    descriptor: Mapping[str, Any],
    *,
    template_name: str,
    template: Mapping[str, Any],
) -> dict[str, Any]:
    required_headings = tuple(str(item) for item in template.get("required_headings") or ())
    heading_ratio, missing_headings = _marker_ratio(candidate_text, required_headings)
    h1 = next((line[2:].strip() for line in candidate_text.splitlines() if line.startswith("# ")), "")
    minimal = ((descriptor.get("layers") or {}).get("minimal") or {}) if isinstance(descriptor.get("layers"), Mapping) else {}
    summary = str(minimal.get("summary") or descriptor.get("shared_summary") or "")
    emitted = minimal.get("emitted_surfaces") or {}
    scorecard = {
        "title_clarity": 10 if h1 and 12 <= len(h1) <= 96 else (7 if h1 else 3),
        "description_richness": 10 if len(summary) >= 90 else (7 if len(summary) >= 50 else 4),
        "intent_coverage": _score_from_ratio(heading_ratio, penalty=0),
        "boundary_clarity": _boundary_clarity_score(candidate_text),
        "output_specificity": _output_specificity_score(candidate_text, minimal),
        "metadata_completeness": _metadata_completeness_score(descriptor),
        "surface_usability": _surface_usability_score(candidate_text, minimal, template_name, emitted),
    }
    score = max(1, round(sum(scorecard.values()) / len(scorecard)))
    blockers = [f"missing template heading: {heading}" for heading in missing_headings]
    blockers.extend(
        f"benchmark category below target: {label} ({value}/10)"
        for label, value in scorecard.items()
        if value < 8
    )
    if score < int(profile.targets.get("benchmark_readiness") or 0):
        blockers.append("candidate is below the benchmark-readiness threshold")
    return {
        "judge": "benchmark_readiness",
        "title": JUDGE_TITLES["benchmark_readiness"],
        "score": score,
        "blockers": blockers,
        "scorecard": scorecard,
    }


def _cap_dependent_judge_from_source_fidelity(
    profile: QualityProfile,
    source_fidelity: Mapping[str, Any],
    judge_report: Mapping[str, Any],
) -> dict[str, Any]:
    if not source_fidelity.get("blockers"):
        return dict(judge_report)
    blocked = dict(judge_report)
    blockers = list(blocked.get("blockers") or [])
    blockers.append(f"source fidelity failed, so {blocked['judge']} cannot clear ship independently")
    blocked["blockers"] = blockers
    target = int(profile.targets.get(str(blocked["judge"])) or 10)
    blocked["score"] = min(int(blocked["score"]), max(1, target - 1))
    return blocked


def refine_candidate_text(candidate_text: str, pass_report: Mapping[str, Any], profile: QualityProfile) -> str:
    """Perform only source-preserving heading normalization.

    Missing meaning requires a source-grounded author/reviewer repair. Template
    stubs are authoring references, never completed capability obligations.
    """
    refined = candidate_text
    aliases = dict(profile.payload.get("heading_aliases") or {})
    missing_markers: set[str] = set()
    for judge in pass_report.get("judge_reports") or []:
        for blocker in judge.get("blockers") or []:
            if ": " in blocker:
                missing_markers.add(blocker.split(": ", 1)[1])
    for marker in sorted(missing_markers):
        if not marker.startswith("## ") or re.search(rf"^{re.escape(marker)}\s*$", refined, re.MULTILINE):
            continue
        for alias in aliases.get(marker, []):
            # Heading-only edits never touch code fences or quoted examples.
            lines = refined.splitlines(keepends=True)
            for index, line, prose in _markdown_lines(refined):
                if prose and line.rstrip("\r\n") == alias:
                    lines[index] = marker + ("\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else "")
                    refined = "".join(lines)
                    break
            if refined != candidate_text and re.search(rf"^{re.escape(marker)}\s*$", refined, re.MULTILINE):
                break
    return refined


def _markdown_lines(text: str) -> list[tuple[int, str, bool]]:
    """Track CommonMark fence character, length and valid closing syntax.

    The bool says whether a line can be active prose/headings. Literal content
    is retained verbatim for callers extracting output schemas.
    """
    result: list[tuple[int, str, bool]] = []
    fence: tuple[str, int] | None = None
    for index, line in enumerate(text.splitlines(keepends=True)):
        if fence is not None:
            char, length = fence
            if re.fullmatch(rf" {{0,3}}{re.escape(char)}{{{length},}}[ \t]*(?:\r?\n)?", line):
                fence = None
            result.append((index, line, False))
            continue
        opener = re.match(r"^ {0,3}(`{3,}|~{3,})(.*?)(?:\r?\n)?$", line)
        if opener and not (opener[1][0] == "`" and "`" in opener[2]):
            fence = (opener[1][0], len(opener[1]))
            result.append((index, line, False))
            continue
        prose = not line.startswith(("    ", "\t")) and not line.lstrip().startswith(">")
        result.append((index, line, prose))
    return result


def _active_instruction_records(text: str) -> list[tuple[tuple[str, ...], str]]:
    records: list[tuple[tuple[str, ...], str]] = []
    example_level: int | None = None
    scopes: list[tuple[int, str]] = []
    for _, line, prose in _markdown_lines(text):
        stripped = line.strip()
        if not prose:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if heading:
            level, title = len(heading[1]), heading[2]
            scopes = [scope for scope in scopes if scope[0] < level]
            if re.search(r"\bmode\b|\bmodule(?:\s|:)|(?:^|[ `])/\w+", title, re.I):
                scopes.append((level, title.casefold().strip()))
            if example_level is not None and level <= example_level:
                example_level = None
            if re.search(r"\b(?:examples?|sample|illustration)\b", title, re.I):
                example_level = level
            continue
        if example_level is None and stripped:
            records.append((tuple(scope[1] for scope in scopes), stripped))
    return records


def _active_instruction_lines(text: str) -> list[str]:
    return [line for _, line in _active_instruction_records(text)]


def semantic_review_findings(candidate_text: str) -> list[dict[str, Any]]:
    """Find narrow unconditional opposites; absence is not semantic clearance."""
    clauses: dict[tuple[tuple[str, ...], str], dict[str, str]] = {}
    findings: list[dict[str, Any]] = []
    for scope, line in _active_instruction_records(candidate_text):
        clean = re.sub(r"^(?:[-*]|\d+\.)\s*", "", line).strip()
        # Scoped exceptions need interpretation; do not flatten their conditions.
        if re.search(r"\b(?:if|when|unless|except|until|during|in .+ mode)\b", clean, re.I):
            continue
        match = re.match(r"^(?:you\s+)?(always|never|must not|must|do not)\s+(.+?)[.!]?$", clean, re.I)
        if not match:
            continue
        polarity = "negative" if match[1].casefold() in {"never", "must not", "do not"} else "positive"
        predicate = re.sub(r"[.!]+$", "", match[2]).casefold().strip()
        values = clauses.setdefault((scope, predicate), {})
        values[polarity] = clean
        if len(values) == 2:
            findings.append({"code": "potential_boundary_conflict", "disposition": "semantic_review_required",
                             "message": f"unconditional opposing instructions for '{predicate}'",
                             "scope": list(scope),
                             "evidence": [values["positive"], values["negative"]]})
    return findings


def _repair_requests(blockers: Sequence[str], semantic_findings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for blocker in dict.fromkeys(blockers):
        requests.append({"finding": blocker, "disposition": "semantic_review_required" if "semantic review" in blocker or "missing" in blocker else "repair_required",
                         "instruction": "Locate and repair the authoritative source or supply a reviewed requirement mapping; preserve existing commands, schemas, boundaries, and user intent. Do not insert generic instructions or infer missing domain facts."})
    return requests


def _section_bodies(text: str, names: Sequence[str]) -> list[str]:
    """Extract heading-delimited contract bodies, accepting prose and schemas."""
    names_lower = {name.casefold() for name in names}
    result: list[str] = []
    active: list[str] | None = None
    level = 0
    for _, raw_line, prose in _markdown_lines(text):
        line = raw_line.rstrip("\r\n")
        heading = re.match(r"^ {0,3}(#{1,6})\s+(.*?)\s*$", line) if prose else None
        if heading:
            if active is not None and len(heading[1]) <= level:
                result.append("\n".join(active)); active = None
            if heading[2].casefold() in names_lower:
                active, level = [], len(heading[1])
                continue
        if active is not None:
            active.append(line)
    if active is not None:
        result.append("\n".join(active))
    return result


def _boundary_clarity_score(candidate_text: str) -> int:
    if semantic_review_findings(candidate_text):
        return 3
    bodies = _section_bodies(candidate_text, ("Constraints", "Tool Boundaries", "Rules", "Boundaries", "No-Gos & Boundaries", "Agent Operating Contract"))
    lines = _active_instruction_lines("\n".join(bodies))
    clauses = [line for line in lines if len(line.split()) >= 5 and re.search(r"\b(?:do not|must not|never|only|out of scope|unless|forbidden)\b", line, re.I)]
    return 8 if clauses else 4  # Structural presence, never a 10/10 semantic verdict.


def _output_specificity_score(candidate_text: str, minimal: Mapping[str, Any]) -> int:
    bodies = _section_bodies(candidate_text, ("Required Output", "Output Contract", "Expected Output", "Expected Outputs"))
    if not bodies:
        return 3
    body = "\n".join(bodies).strip()
    if not body or _has_unfilled_output_placeholder(body):
        return 4
    # Count content only inside the contract, not unrelated global bullets or
    # claims in descriptor metadata. Schemas, prose, and tables are all valid.
    return 10 if len(body.split()) >= 30 else 8 if len(body.split()) >= 3 else 6


def _has_unfilled_output_placeholder(body: str) -> bool:
    """Identify authoring stubs, not legitimate uncertainty-marker conventions.

    A marker mentioned within an output instruction or schema is content. An
    entire unresolved slot (optionally with a label) is a repair finding.
    """
    slot = re.compile(
        r"(?:[A-Za-z][A-Za-z _/-]*:[ \t]*)?"
        r"(?:\[(?:TODO|TBD)(?::[^\]]*)?\]|(?:TODO|TBD)(?::.*)?)[.!]?",
        re.I,
    )
    # Even quoted or fenced placeholder-only content is still an empty contract.
    literal_body = "\n".join(
        line for line in body.splitlines() if not re.match(r"^\s*(`{3,}|~{3,})", line)
    ).strip(" \t\r\n>`\"'")
    if slot.fullmatch(literal_body):
        return True
    for _, line, prose in _markdown_lines(body):
        if not prose:
            continue
        content = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line).strip()
        if slot.fullmatch(content):
            return True
        if re.fullmatch(r"(?:describe the output here|fill in (?:the )?(?:output|contract)(?: here)?)[.!]?", content, re.I):
            return True
    return False


def _metadata_completeness_score(descriptor: Mapping[str, Any]) -> int:
    minimal = ((descriptor.get("layers") or {}).get("minimal") or {}) if isinstance(descriptor.get("layers"), Mapping) else {}
    checks = [
        bool(descriptor.get("slug")),
        bool(minimal.get("capability_type")),
        bool(minimal.get("install_target")),
        bool(minimal.get("emitted_surfaces")),
        bool(minimal.get("source_provenance")),
        bool(descriptor.get("consumption_hints") or minimal.get("display_name")),
    ]
    ratio = sum(1 for passed in checks if passed) / len(checks)
    return _score_from_ratio(ratio, penalty=0)


def _surface_usability_score(
    candidate_text: str,
    minimal: Mapping[str, Any],
    template_name: str,
    emitted: Mapping[str, Any],
) -> int:
    capability_type = str(minimal.get("capability_type") or template_name)
    has_examples = "## Examples" in candidate_text
    if capability_type == "both":
        agentish = "## Agent Operating Contract" in candidate_text and _marker_ratio(candidate_text, ("## Tool Boundaries",))[0] == 1.0
        both_surfaces = any("agent" in item for values in emitted.values() for item in values) and any("skill" in item for values in emitted.values() for item in values)
        return 10 if agentish and both_surfaces and has_examples else 6
    if capability_type == "agent":
        return 10 if "## Agent Operating Contract" in candidate_text and has_examples else 6
    return 10 if has_examples and "## Workflow" in candidate_text else 6


def _pass_scorecard(judge_reports: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    scorecard: dict[str, int] = {}
    for judge in judge_reports:
        scorecard[str(judge["judge"])] = int(judge["score"])
        nested = judge.get("scorecard")
        if isinstance(nested, Mapping):
            for key, value in nested.items():
                if isinstance(value, int):
                    scorecard[str(key)] = value
    return scorecard


def _marker_ratio(candidate_text: str, markers: Sequence[str]) -> tuple[float, list[str]]:
    if not markers:
        return 1.0, []
    lowered = candidate_text.casefold()
    present = 0
    missing: list[str] = []
    for marker in markers:
        marker_lower = marker.casefold()
        aliases = (marker, *MARKER_ALIASES.get(marker_lower, ()))
        if any(alias.casefold() in lowered for alias in aliases):
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
