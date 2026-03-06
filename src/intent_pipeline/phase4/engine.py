"""Phase-4 deterministic orchestration engine."""

from __future__ import annotations

from typing import Any, Mapping

from intent_pipeline.phase4.contracts import (
    CapabilityMatrix,
    PHASE4_ENGINE_SCHEMA_VERSION,
    Phase4Result,
    PolicyContract,
)
from intent_pipeline.phase4.fallback import resolve_fallback
from intent_pipeline.phase4.mock_executor import run_mock_execution
from intent_pipeline.phase4.validator import validate_target


def run_phase4(
    route_spec: Mapping[str, Any] | Any,
    capability_matrix: CapabilityMatrix | Mapping[str, Any],
    policy_contract: PolicyContract | Mapping[str, Any],
) -> Phase4Result:
    """Compose validation, dry-run mock execution, and fixed fallback resolution."""
    validation_report = validate_target(route_spec, capability_matrix, policy_contract)
    mock_trace = run_mock_execution(validation_report)
    fallback_outcome = resolve_fallback(validation_report, mock_trace)

    return Phase4Result(
        schema_version=PHASE4_ENGINE_SCHEMA_VERSION,
        route_spec_schema_version=validation_report.route_spec_schema_version,
        pipeline_order=("validate_target", "run_mock_execution", "resolve_fallback"),
        validation=validation_report,
        mock=mock_trace,
        fallback=fallback_outcome,
    )


__all__ = ["run_phase4"]
