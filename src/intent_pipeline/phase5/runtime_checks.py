"""Phase-5 preflight-only runtime dependency checks."""

from __future__ import annotations

import importlib.util
from shutil import which
from typing import Iterable, Mapping

from intent_pipeline.phase5.contracts import (
    PHASE5_RUNTIME_SCHEMA_VERSION,
    RuntimeDependencyAggregateStatus,
    RuntimeDependencyCheck,
    RuntimeDependencyClassification,
    RuntimeDependencyProbeType,
    RuntimeDependencyReasonCode,
    RuntimeDependencyReport,
    RuntimeDependencySpec,
    RuntimeDependencyStatus,
)


DEFAULT_RUNTIME_DEPENDENCY_SPECS: tuple[RuntimeDependencySpec, ...] = (
    RuntimeDependencySpec(
        dependency_id="python.json",
        classification=RuntimeDependencyClassification.REQUIRED,
        probe_type=RuntimeDependencyProbeType.PYTHON_MODULE,
        target="json",
    ),
    RuntimeDependencySpec(
        dependency_id="python.tomllib",
        classification=RuntimeDependencyClassification.OPTIONAL,
        probe_type=RuntimeDependencyProbeType.PYTHON_MODULE,
        target="tomllib",
    ),
)


def run_runtime_dependency_checks(
    dependency_specs: Iterable[RuntimeDependencySpec | Mapping[str, object]] | None = None,
) -> RuntimeDependencyReport:
    """Run deterministic static dependency presence checks without side effects."""
    normalized_specs = _coerce_specs(
        dependency_specs if dependency_specs is not None else DEFAULT_RUNTIME_DEPENDENCY_SPECS
    )
    checks = tuple(_run_single_check(spec) for spec in normalized_specs)
    aggregate_status = _aggregate_status(checks)
    return RuntimeDependencyReport(
        schema_version=PHASE5_RUNTIME_SCHEMA_VERSION,
        aggregate_status=aggregate_status,
        checks=checks,
        pipeline_order=("run_runtime_dependency_checks",),
    )


def _coerce_specs(
    specs: Iterable[RuntimeDependencySpec | Mapping[str, object]],
) -> tuple[RuntimeDependencySpec, ...]:
    normalized: list[RuntimeDependencySpec] = []
    for raw_spec in specs:
        if isinstance(raw_spec, RuntimeDependencySpec):
            normalized.append(raw_spec)
            continue
        if isinstance(raw_spec, Mapping):
            normalized.append(
                RuntimeDependencySpec(
                    dependency_id=str(raw_spec.get("dependency_id", "")),
                    classification=RuntimeDependencyClassification(str(raw_spec.get("classification", ""))),
                    probe_type=RuntimeDependencyProbeType(str(raw_spec.get("probe_type", ""))),
                    target=str(raw_spec.get("target", "")),
                )
            )
            continue
        raise TypeError("Runtime dependency specs must be RuntimeDependencySpec or mapping payloads")

    return tuple(
        sorted(
            normalized,
            key=lambda entry: (
                entry.dependency_id,
                entry.classification.value,
                entry.probe_type.value,
                entry.target,
            ),
        )
    )


def _run_single_check(spec: RuntimeDependencySpec) -> RuntimeDependencyCheck:
    status = _resolve_status(spec)
    reason_code = _reason_code(spec.classification, status)
    detail = _detail_for(spec, status)
    return RuntimeDependencyCheck(
        dependency_id=spec.dependency_id,
        classification=spec.classification,
        probe_type=spec.probe_type,
        target=spec.target,
        status=status,
        reason_code=reason_code,
        evidence_paths=(
            f"phase5.runtime.dependency_id:{spec.dependency_id}",
            f"phase5.runtime.probe:{spec.probe_type.value}:{spec.target}",
        ),
        detail=detail,
    )


def _resolve_status(spec: RuntimeDependencySpec) -> RuntimeDependencyStatus:
    if spec.probe_type is RuntimeDependencyProbeType.PYTHON_MODULE:
        return RuntimeDependencyStatus.PRESENT if importlib.util.find_spec(spec.target) is not None else RuntimeDependencyStatus.MISSING
    if spec.probe_type is RuntimeDependencyProbeType.SHELL_COMMAND:
        return RuntimeDependencyStatus.PRESENT if which(spec.target) is not None else RuntimeDependencyStatus.MISSING
    raise ValueError(f"Unsupported runtime probe type '{spec.probe_type.value}'")


def _reason_code(
    classification: RuntimeDependencyClassification,
    status: RuntimeDependencyStatus,
) -> RuntimeDependencyReasonCode:
    if status is RuntimeDependencyStatus.PRESENT:
        return RuntimeDependencyReasonCode.PRESENT
    if classification is RuntimeDependencyClassification.REQUIRED:
        return RuntimeDependencyReasonCode.REQUIRED_MISSING
    return RuntimeDependencyReasonCode.OPTIONAL_MISSING


def _detail_for(spec: RuntimeDependencySpec, status: RuntimeDependencyStatus) -> str:
    if status is RuntimeDependencyStatus.PRESENT:
        return f"Dependency '{spec.target}' is available via {spec.probe_type.value} preflight probe"
    return f"Dependency '{spec.target}' is missing via {spec.probe_type.value} preflight probe"


def _aggregate_status(
    checks: tuple[RuntimeDependencyCheck, ...],
) -> RuntimeDependencyAggregateStatus:
    has_required_missing = any(
        check.status is RuntimeDependencyStatus.MISSING
        and check.classification is RuntimeDependencyClassification.REQUIRED
        for check in checks
    )
    if has_required_missing:
        return RuntimeDependencyAggregateStatus.BLOCKING
    has_optional_missing = any(
        check.status is RuntimeDependencyStatus.MISSING
        and check.classification is RuntimeDependencyClassification.OPTIONAL
        for check in checks
    )
    if has_optional_missing:
        return RuntimeDependencyAggregateStatus.DEGRADED
    return RuntimeDependencyAggregateStatus.PASS


__all__ = [
    "DEFAULT_RUNTIME_DEPENDENCY_SPECS",
    "run_runtime_dependency_checks",
]
