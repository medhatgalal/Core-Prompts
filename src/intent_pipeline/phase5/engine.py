"""Phase-5 help orchestration with non-mutating terminal semantic guards."""

from __future__ import annotations

from intent_pipeline.phase4.contracts import Phase4Result
from intent_pipeline.phase5.contracts import HelpCode, HelpTopic, Phase5HelpResponse
from intent_pipeline.phase5.help import resolve_help_response
from intent_pipeline.phase5.output_generator import generate_output_surfaces


def generate_help_response(
    phase4_result: Phase4Result,
    *,
    topic: HelpTopic | str | None = None,
    code: HelpCode | str | None = None,
) -> Phase5HelpResponse:
    """Generate advisory-only help from Phase4Result without mutating terminal semantics."""
    if not isinstance(phase4_result, Phase4Result):
        raise TypeError("generate_help_response expects Phase4Result input")

    phase4_snapshot = phase4_result.to_json()
    output_surfaces = generate_output_surfaces(phase4_result)
    _guard_terminal_semantics(phase4_result, output_surfaces.machine_payload.terminal_status.value)

    help_response = resolve_help_response(output_surfaces, topic=topic, code=code)

    if phase4_result.to_json() != phase4_snapshot:
        raise ValueError("Phase5 help generation must not mutate upstream Phase4 terminal semantics")
    return help_response


def _guard_terminal_semantics(phase4_result: Phase4Result, resolved_status: str) -> None:
    upstream_status = phase4_result.fallback.decision.value
    if resolved_status != upstream_status:
        raise ValueError("Phase5 help engine must preserve upstream terminal decision semantics")


__all__ = ["generate_help_response"]
