"""Phase-5 orchestration engine with deterministic runtime/output/help ordering."""

from __future__ import annotations

from intent_pipeline.phase4.contracts import Phase4Result
from typing import Iterable, Mapping

from intent_pipeline.phase5.contracts import (
    HelpCode,
    HelpTopic,
    PHASE5_ENGINE_SCHEMA_VERSION,
    Phase5HelpResponse,
    Phase5Result,
    RuntimeDependencySpec,
)
from intent_pipeline.phase5.help import resolve_help_response
from intent_pipeline.phase5.output_generator import generate_output_surfaces
from intent_pipeline.phase5.runtime_checks import run_runtime_dependency_checks


def run_phase5(
    phase4_result: Phase4Result,
    *,
    dependency_specs: Iterable[RuntimeDependencySpec | Mapping[str, object]] | None = None,
    topic: HelpTopic | str | None = None,
    code: HelpCode | str | None = None,
) -> Phase5Result:
    """Run Phase 5 in fixed deterministic order: runtime checks -> output -> help."""
    if not isinstance(phase4_result, Phase4Result):
        raise TypeError("run_phase5 expects Phase4Result input")

    phase4_snapshot = phase4_result.to_json()
    runtime_report = run_runtime_dependency_checks(dependency_specs)
    output_surfaces = generate_output_surfaces(phase4_result)
    _guard_terminal_semantics(phase4_result, output_surfaces.machine_payload.terminal_status.value)
    help_response = resolve_help_response(output_surfaces, topic=topic, code=code)

    if phase4_result.to_json() != phase4_snapshot:
        raise ValueError("Phase5 engine must not mutate upstream Phase4 terminal semantics")

    return Phase5Result(
        schema_version=PHASE5_ENGINE_SCHEMA_VERSION,
        route_spec_schema_version=phase4_result.route_spec_schema_version,
        pipeline_order=("run_runtime_dependency_checks", "generate_output_surfaces", "resolve_help_response"),
        runtime=runtime_report,
        output=output_surfaces,
        help=help_response,
    )


def generate_help_response(
    phase4_result: Phase4Result,
    *,
    topic: HelpTopic | str | None = None,
    code: HelpCode | str | None = None,
) -> Phase5HelpResponse:
    """Backward-compatible helper for direct deterministic help generation."""
    return run_phase5(phase4_result, topic=topic, code=code).help


def _guard_terminal_semantics(phase4_result: Phase4Result, resolved_status: str) -> None:
    upstream_status = phase4_result.fallback.decision.value
    if resolved_status != upstream_status:
        raise ValueError("Phase5 help engine must preserve upstream terminal decision semantics")


__all__ = ["generate_help_response", "run_phase5"]
