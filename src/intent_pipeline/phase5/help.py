"""Phase-5 deterministic help resolver with closed taxonomy and typed help codes."""

from __future__ import annotations

from intent_pipeline.phase5.contracts import (
    HelpCode,
    HelpTopic,
    OutputTerminalStatus,
    Phase5HelpResponse,
    Phase5OutputSurfaces,
)


_DEFAULT_CODE_BY_STATUS: dict[OutputTerminalStatus, HelpCode] = {
    OutputTerminalStatus.USE_PRIMARY: HelpCode.USAGE_STATUS_OVERVIEW,
    OutputTerminalStatus.DEGRADED: HelpCode.REMEDIATION_DEGRADED_STATUS,
    OutputTerminalStatus.NEEDS_REVIEW: HelpCode.FAILURE_BLOCKING_STATUS,
}

_DEFAULT_CODE_BY_TOPIC: dict[HelpTopic, HelpCode] = {
    HelpTopic.USAGE_GUIDANCE: HelpCode.USAGE_STATUS_OVERVIEW,
    HelpTopic.FAILURE_EXPLANATION: HelpCode.FAILURE_BLOCKING_STATUS,
    HelpTopic.REMEDIATION_HINTS: HelpCode.REMEDIATION_DEGRADED_STATUS,
    HelpTopic.BOUNDARY_CLARIFICATION: HelpCode.BOUNDARY_NON_EXECUTING_GUIDANCE,
}

_TEMPLATE_BY_CODE: dict[HelpCode, str] = {
    HelpCode.USAGE_STATUS_OVERVIEW: (
        "Status remains {terminal_status}. Review output code {output_code} and keep execution decisions unchanged."
    ),
    HelpCode.FAILURE_BLOCKING_STATUS: (
        "Failure state is {terminal_status}. Review terminal code {terminal_code} and keep escalation in manual review."
    ),
    HelpCode.REMEDIATION_DEGRADED_STATUS: (
        "Result is {terminal_status}. Capture remediation hints from evidence paths before any follow-up planning."
    ),
    HelpCode.BOUNDARY_NON_EXECUTING_GUIDANCE: (
        "Help guidance is advisory-only. Preserve output code {output_code} and avoid execution or auto-remediation."
    ),
}

_ACTIONS_BY_CODE: dict[HelpCode, tuple[str, ...]] = {
    HelpCode.USAGE_STATUS_OVERVIEW: (
        "Review the ordered evidence paths tied to the output code.",
        "Confirm terminal status alignment in manual review notes.",
    ),
    HelpCode.FAILURE_BLOCKING_STATUS: (
        "Review blocking evidence before requesting policy updates.",
        "Document unresolved blockers for human triage.",
    ),
    HelpCode.REMEDIATION_DEGRADED_STATUS: (
        "Inspect degraded evidence paths and record manual follow-up tasks.",
        "Capture non-blocking gaps in deterministic issue tracking.",
    ),
    HelpCode.BOUNDARY_NON_EXECUTING_GUIDANCE: (
        "Confirm no execution or installation steps are introduced.",
        "Escalate only through manual approval channels.",
    ),
}


def resolve_help_response(
    output_surfaces: Phase5OutputSurfaces,
    *,
    topic: HelpTopic | str | None = None,
    code: HelpCode | str | None = None,
) -> Phase5HelpResponse:
    """Resolve deterministic help content from the closed topic/code taxonomy."""
    if not isinstance(output_surfaces, Phase5OutputSurfaces):
        raise TypeError("resolve_help_response expects Phase5OutputSurfaces input")

    resolved_topic, resolved_code = _resolve_topic_and_code(
        output_surfaces=output_surfaces,
        topic=topic,
        code=code,
    )

    machine_payload = output_surfaces.machine_payload
    terminal_code = machine_payload.terminal_code or "none"
    message = _TEMPLATE_BY_CODE[resolved_code].format(
        terminal_status=machine_payload.terminal_status.value,
        output_code=machine_payload.output_code.value,
        terminal_code=terminal_code,
    )
    evidence_paths = tuple(
        sorted(
            {
                *machine_payload.evidence_paths,
                f"phase5.help.topic::{resolved_topic.value}",
                f"phase5.help.code::{resolved_code.value}",
            }
        )
    )
    actions = _ACTIONS_BY_CODE[resolved_code]

    return Phase5HelpResponse(
        topic=resolved_topic,
        code=resolved_code,
        message=message,
        evidence_paths=evidence_paths,
        actions=actions,
        terminal_status=machine_payload.terminal_status,
        output_code=machine_payload.output_code,
    )


def _resolve_topic_and_code(
    *,
    output_surfaces: Phase5OutputSurfaces,
    topic: HelpTopic | str | None,
    code: HelpCode | str | None,
) -> tuple[HelpTopic, HelpCode]:
    machine_payload = output_surfaces.machine_payload
    if topic is None and code is None:
        resolved_code = _DEFAULT_CODE_BY_STATUS[machine_payload.terminal_status]
        return _topic_for_code(resolved_code), resolved_code

    resolved_topic = _coerce_topic(topic) if topic is not None else None
    resolved_code = _coerce_code(code) if code is not None else None

    if resolved_topic is not None and resolved_code is not None:
        expected_topic = _topic_for_code(resolved_code)
        if expected_topic is not resolved_topic:
            raise ValueError("Help topic and code must match closed deterministic mapping")
        return resolved_topic, resolved_code

    if resolved_topic is not None:
        return resolved_topic, _DEFAULT_CODE_BY_TOPIC[resolved_topic]

    assert resolved_code is not None
    return _topic_for_code(resolved_code), resolved_code


def _topic_for_code(code: HelpCode) -> HelpTopic:
    for known_topic, known_code in _DEFAULT_CODE_BY_TOPIC.items():
        if known_code is code:
            return known_topic
    raise ValueError(f"Unsupported help code '{code.value}'")


def _coerce_topic(topic: HelpTopic | str | None) -> HelpTopic:
    if isinstance(topic, HelpTopic):
        return topic
    if isinstance(topic, str):
        try:
            return HelpTopic(topic)
        except ValueError as exc:
            raise ValueError(f"Unsupported help topic '{topic}'") from exc
    raise ValueError("Unsupported help topic type")


def _coerce_code(code: HelpCode | str | None) -> HelpCode:
    if isinstance(code, HelpCode):
        return code
    if isinstance(code, str):
        try:
            return HelpCode(code)
        except ValueError as exc:
            raise ValueError(f"Unsupported help code '{code}'") from exc
    raise ValueError("Unsupported help code type")


__all__ = ["resolve_help_response"]
