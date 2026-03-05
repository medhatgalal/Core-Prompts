"""Phase-5 deterministic machine and human output generation."""

from __future__ import annotations

from typing import Iterable

from intent_pipeline.phase4.contracts import (
    FallbackDecision,
    MockStepStatus,
    Phase4Result,
)
from intent_pipeline.phase5.contracts import (
    OutputSurfaceCode,
    OutputTerminalStatus,
    Phase5OutputPayload,
    Phase5OutputSurfaces,
)


_STATUS_TO_SURFACE_CODE: dict[OutputTerminalStatus, OutputSurfaceCode] = {
    OutputTerminalStatus.USE_PRIMARY: OutputSurfaceCode.PRIMARY_PATH,
    OutputTerminalStatus.DEGRADED: OutputSurfaceCode.DEGRADED_PATH,
    OutputTerminalStatus.NEEDS_REVIEW: OutputSurfaceCode.NEEDS_REVIEW_PATH,
}


def generate_output_surfaces(phase4_result: Phase4Result) -> Phase5OutputSurfaces:
    """Generate deterministic machine payload + human-readable output from a Phase4Result."""
    if not isinstance(phase4_result, Phase4Result):
        raise TypeError("generate_output_surfaces expects Phase4Result input")

    terminal_status = _terminal_status_from_phase4(phase4_result)
    issue_codes = _collect_issue_codes(phase4_result)
    evidence_paths = _collect_evidence_paths(phase4_result, issue_codes)

    machine_payload = Phase5OutputPayload(
        schema_version="5.0.0",
        phase4_schema_version=phase4_result.schema_version,
        route_spec_schema_version=phase4_result.route_spec_schema_version,
        terminal_status=terminal_status,
        terminal_code=phase4_result.fallback.terminal_code.value if phase4_result.fallback.terminal_code is not None else None,
        dominant_rule_id=phase4_result.fallback.dominant_rule_id,
        output_code=_STATUS_TO_SURFACE_CODE[terminal_status],
        issues=issue_codes,
        evidence_paths=evidence_paths,
        pipeline_order=("generate_output_surfaces",),
    )

    human_text = _render_human_output(phase4_result, machine_payload)
    return Phase5OutputSurfaces(machine_payload=machine_payload, human_text=human_text)


def _terminal_status_from_phase4(phase4_result: Phase4Result) -> OutputTerminalStatus:
    decision = phase4_result.fallback.decision
    if decision is FallbackDecision.USE_PRIMARY:
        return OutputTerminalStatus.USE_PRIMARY
    if decision is FallbackDecision.DEGRADED:
        return OutputTerminalStatus.DEGRADED
    if decision is FallbackDecision.NEEDS_REVIEW:
        return OutputTerminalStatus.NEEDS_REVIEW
    raise ValueError(f"Unsupported fallback decision '{decision}'")


def _collect_issue_codes(phase4_result: Phase4Result) -> tuple[str, ...]:
    codes = {issue.code.value for issue in phase4_result.validation.issues}
    if phase4_result.fallback.terminal_code is not None:
        codes.add(phase4_result.fallback.terminal_code.value)
    return tuple(sorted(codes))


def _collect_evidence_paths(phase4_result: Phase4Result, issue_codes: Iterable[str]) -> tuple[str, ...]:
    paths: set[str] = set()
    for issue in phase4_result.validation.issues:
        paths.update(issue.evidence_paths)
    for step in phase4_result.mock.steps:
        paths.update(step.evidence_paths)
    paths.update(phase4_result.fallback.evidence_paths)
    paths.add("phase5.output.issues")
    for code in issue_codes:
        paths.add(f"phase5.output.issue_codes::{code}")
    return tuple(sorted(path for path in paths if path.strip()))


def _render_human_output(phase4_result: Phase4Result, machine_payload: Phase5OutputPayload) -> str:
    validation_issues = ", ".join(machine_payload.issues) if machine_payload.issues else "none"
    failed_stages = sorted(
        {
            step.stage.value
            for step in phase4_result.mock.steps
            if step.status is MockStepStatus.FAIL
        }
    )
    failed_stage_text = ", ".join(failed_stages) if failed_stages else "none"
    attempted_tier_lines = [
        f"{attempt.tier.value}: accepted={str(attempt.accepted).lower()}, reason={attempt.reason_code.value if attempt.reason_code else 'none'}"
        for attempt in phase4_result.fallback.attempted_tiers
    ]
    attempted_tiers = "; ".join(attempted_tier_lines) if attempted_tier_lines else "none"

    sections = {
        "Summary": [
            f"- terminal_status: {machine_payload.terminal_status.value}",
            f"- output_code: {machine_payload.output_code.value}",
            f"- dominant_rule_id: {machine_payload.dominant_rule_id}",
        ],
        "Validation": [
            f"- decision: {phase4_result.validation.decision.value}",
            f"- can_proceed: {str(phase4_result.validation.can_proceed).lower()}",
            f"- issues: {validation_issues}",
        ],
        "Mock Execution": [
            f"- decision: {phase4_result.mock.decision.value}",
            f"- failed_stages: {failed_stage_text}",
        ],
        "Fallback": [
            f"- decision: {phase4_result.fallback.decision.value}",
            f"- chosen_tier: {phase4_result.fallback.chosen_tier.value}",
            f"- terminal_code: {machine_payload.terminal_code or 'none'}",
            f"- attempted_tiers: {attempted_tiers}",
        ],
    }

    ordered_sections = []
    for title in ("Summary", "Validation", "Mock Execution", "Fallback"):
        body = "\n".join(sections[title])
        ordered_sections.append(f"{title}\n{body}")
    return "\n\n".join(ordered_sections)


__all__ = ["generate_output_surfaces"]
