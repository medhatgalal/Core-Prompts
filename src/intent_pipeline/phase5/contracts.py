"""Phase-5 typed output contracts and deterministic serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any


PHASE5_OUTPUT_SCHEMA_VERSION = "5.0.0"
SUPPORTED_PHASE5_SCHEMA_MAJOR = "5"
PHASE5_RUNTIME_SCHEMA_VERSION = "5.0.0"
PHASE5_ENGINE_SCHEMA_VERSION = "5.0.0"

OUTPUT_SECTION_ORDER: tuple[str, ...] = (
    "Summary",
    "Validation",
    "Mock Execution",
    "Fallback",
)


class OutputTerminalStatus(str, Enum):
    USE_PRIMARY = "USE_PRIMARY"
    DEGRADED = "DEGRADED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class OutputSurfaceCode(str, Enum):
    PRIMARY_PATH = "OUT-001-PRIMARY-PATH"
    DEGRADED_PATH = "OUT-002-DEGRADED-PATH"
    NEEDS_REVIEW_PATH = "OUT-003-NEEDS-REVIEW-PATH"


class HelpTopic(str, Enum):
    USAGE_GUIDANCE = "usage_guidance"
    FAILURE_EXPLANATION = "failure_explanation"
    REMEDIATION_HINTS = "remediation_hints"
    BOUNDARY_CLARIFICATION = "boundary_clarification"


class HelpCode(str, Enum):
    USAGE_STATUS_OVERVIEW = "HELP-101-USAGE-STATUS-OVERVIEW"
    FAILURE_BLOCKING_STATUS = "HELP-201-FAILURE-BLOCKING-STATUS"
    REMEDIATION_DEGRADED_STATUS = "HELP-301-REMEDIATION-DEGRADED-STATUS"
    BOUNDARY_NON_EXECUTING_GUIDANCE = "HELP-401-BOUNDARY-NON-EXECUTING-GUIDANCE"


class RuntimeDependencyClassification(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class RuntimeDependencyProbeType(str, Enum):
    PYTHON_MODULE = "python_module"
    SHELL_COMMAND = "shell_command"


class RuntimeDependencyStatus(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"


class RuntimeDependencyReasonCode(str, Enum):
    PRESENT = "RUNTIME-000-PRESENT"
    REQUIRED_MISSING = "RUNTIME-001-REQUIRED-MISSING"
    OPTIONAL_MISSING = "RUNTIME-002-OPTIONAL-MISSING"


class RuntimeDependencyAggregateStatus(str, Enum):
    PASS = "PASS"
    DEGRADED = "DEGRADED"
    BLOCKING = "BLOCKING"


class Phase5BoundaryErrorCode(str, Enum):
    FORBIDDEN_EXECUTION_IMPORT = "BOUND-05-001-FORBIDDEN-EXECUTION-IMPORT"
    FORBIDDEN_AUTOREMEDIATION_IMPORT = "BOUND-05-002-FORBIDDEN-AUTOREMEDIATION-IMPORT"
    FORBIDDEN_INSTALL_IMPORT = "BOUND-05-003-FORBIDDEN-INSTALL-IMPORT"
    FORBIDDEN_NETWORK_IMPORT = "BOUND-05-004-FORBIDDEN-NETWORK-IMPORT"


HELP_CODE_TOPIC_MAP: dict[HelpCode, HelpTopic] = {
    HelpCode.USAGE_STATUS_OVERVIEW: HelpTopic.USAGE_GUIDANCE,
    HelpCode.FAILURE_BLOCKING_STATUS: HelpTopic.FAILURE_EXPLANATION,
    HelpCode.REMEDIATION_DEGRADED_STATUS: HelpTopic.REMEDIATION_HINTS,
    HelpCode.BOUNDARY_NON_EXECUTING_GUIDANCE: HelpTopic.BOUNDARY_CLARIFICATION,
}


@dataclass(frozen=True, slots=True)
class Phase5OutputPayload:
    schema_version: str
    phase4_schema_version: str
    route_spec_schema_version: str
    terminal_status: OutputTerminalStatus
    terminal_code: str | None
    dominant_rule_id: str
    output_code: OutputSurfaceCode
    issues: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    pipeline_order: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _validate_schema_major(self.schema_version, SUPPORTED_PHASE5_SCHEMA_MAJOR),
        )
        object.__setattr__(self, "phase4_schema_version", _normalize_text(self.phase4_schema_version))
        object.__setattr__(self, "route_spec_schema_version", _normalize_text(self.route_spec_schema_version))
        if not isinstance(self.terminal_status, OutputTerminalStatus):
            object.__setattr__(self, "terminal_status", OutputTerminalStatus(str(self.terminal_status)))
        object.__setattr__(self, "terminal_code", _normalize_optional_text(self.terminal_code))
        object.__setattr__(self, "dominant_rule_id", _normalize_text(self.dominant_rule_id))
        if not isinstance(self.output_code, OutputSurfaceCode):
            object.__setattr__(self, "output_code", OutputSurfaceCode(str(self.output_code)))
        object.__setattr__(self, "issues", _normalize_sorted_text(self.issues))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))

        if tuple(self.pipeline_order) != ("generate_output_surfaces",):
            raise ValueError("Phase5OutputPayload pipeline_order must be ('generate_output_surfaces',)")
        object.__setattr__(self, "pipeline_order", ("generate_output_surfaces",))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase4_schema_version": self.phase4_schema_version,
            "route_spec_schema_version": self.route_spec_schema_version,
            "terminal_status": self.terminal_status.value,
            "terminal_code": self.terminal_code,
            "dominant_rule_id": self.dominant_rule_id,
            "output_code": self.output_code.value,
            "issues": list(self.issues),
            "evidence_paths": list(self.evidence_paths),
            "pipeline_order": list(self.pipeline_order),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Phase5OutputSurfaces:
    machine_payload: Phase5OutputPayload
    human_text: str
    section_order: tuple[str, ...] = OUTPUT_SECTION_ORDER

    def __post_init__(self) -> None:
        if not isinstance(self.machine_payload, Phase5OutputPayload):
            raise TypeError("machine_payload must be a Phase5OutputPayload")
        normalized_human = self.human_text.rstrip()
        if not normalized_human:
            raise ValueError("human_text must be non-empty")
        object.__setattr__(self, "human_text", normalized_human + "\n")

        if tuple(self.section_order) != OUTPUT_SECTION_ORDER:
            raise ValueError(
                "Phase5OutputSurfaces section_order must follow Summary -> Validation -> Mock Execution -> Fallback"
            )
        object.__setattr__(self, "section_order", OUTPUT_SECTION_ORDER)

    def as_payload(self) -> dict[str, Any]:
        return {
            "machine_payload": self.machine_payload.as_payload(),
            "human_text": self.human_text,
            "section_order": list(self.section_order),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Phase5HelpResponse:
    topic: HelpTopic
    code: HelpCode
    message: str
    evidence_paths: tuple[str, ...]
    actions: tuple[str, ...]
    terminal_status: OutputTerminalStatus
    output_code: OutputSurfaceCode

    def __post_init__(self) -> None:
        if not isinstance(self.topic, HelpTopic):
            object.__setattr__(self, "topic", HelpTopic(str(self.topic)))
        if not isinstance(self.code, HelpCode):
            object.__setattr__(self, "code", HelpCode(str(self.code)))
        expected_topic = HELP_CODE_TOPIC_MAP.get(self.code)
        if expected_topic is None or expected_topic is not self.topic:
            raise ValueError("Help code/topic mapping must match the closed deterministic taxonomy")

        normalized_message = _normalize_text(self.message)
        if not normalized_message:
            raise ValueError("Help message must be non-empty")
        object.__setattr__(self, "message", normalized_message)
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "actions", _normalize_action_steps(self.actions))

        if not isinstance(self.terminal_status, OutputTerminalStatus):
            object.__setattr__(self, "terminal_status", OutputTerminalStatus(str(self.terminal_status)))
        if not isinstance(self.output_code, OutputSurfaceCode):
            object.__setattr__(self, "output_code", OutputSurfaceCode(str(self.output_code)))

    def as_payload(self) -> dict[str, Any]:
        return {
            "topic": self.topic.value,
            "code": self.code.value,
            "message": self.message,
            "evidence_paths": list(self.evidence_paths),
            "actions": list(self.actions),
            "terminal_status": self.terminal_status.value,
            "output_code": self.output_code.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class RuntimeDependencySpec:
    dependency_id: str
    classification: RuntimeDependencyClassification
    probe_type: RuntimeDependencyProbeType
    target: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependency_id", _normalize_text(self.dependency_id))
        if not isinstance(self.classification, RuntimeDependencyClassification):
            object.__setattr__(self, "classification", RuntimeDependencyClassification(str(self.classification)))
        if not isinstance(self.probe_type, RuntimeDependencyProbeType):
            object.__setattr__(self, "probe_type", RuntimeDependencyProbeType(str(self.probe_type)))
        object.__setattr__(self, "target", _normalize_text(self.target))
        if not self.dependency_id:
            raise ValueError("Runtime dependency_id is required")
        if not self.target:
            raise ValueError("Runtime dependency target is required")

    def as_payload(self) -> dict[str, str]:
        return {
            "dependency_id": self.dependency_id,
            "classification": self.classification.value,
            "probe_type": self.probe_type.value,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class RuntimeDependencyCheck:
    dependency_id: str
    classification: RuntimeDependencyClassification
    probe_type: RuntimeDependencyProbeType
    target: str
    status: RuntimeDependencyStatus
    reason_code: RuntimeDependencyReasonCode
    evidence_paths: tuple[str, ...]
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependency_id", _normalize_text(self.dependency_id))
        if not isinstance(self.classification, RuntimeDependencyClassification):
            object.__setattr__(self, "classification", RuntimeDependencyClassification(str(self.classification)))
        if not isinstance(self.probe_type, RuntimeDependencyProbeType):
            object.__setattr__(self, "probe_type", RuntimeDependencyProbeType(str(self.probe_type)))
        object.__setattr__(self, "target", _normalize_text(self.target))
        if not isinstance(self.status, RuntimeDependencyStatus):
            object.__setattr__(self, "status", RuntimeDependencyStatus(str(self.status)))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "detail", _normalize_text(self.detail))
        if not self.dependency_id:
            raise ValueError("Runtime dependency_id is required")
        if not self.target:
            raise ValueError("Runtime dependency target is required")

        normalized_reason = _runtime_reason_for(
            classification=self.classification,
            status=self.status,
        )
        object.__setattr__(self, "reason_code", normalized_reason)

    def as_payload(self) -> dict[str, Any]:
        return {
            "dependency_id": self.dependency_id,
            "classification": self.classification.value,
            "probe_type": self.probe_type.value,
            "target": self.target,
            "status": self.status.value,
            "reason_code": self.reason_code.value,
            "evidence_paths": list(self.evidence_paths),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class RuntimeDependencyReport:
    schema_version: str
    aggregate_status: RuntimeDependencyAggregateStatus
    checks: tuple[RuntimeDependencyCheck, ...]
    pipeline_order: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _validate_schema_major(self.schema_version, SUPPORTED_PHASE5_SCHEMA_MAJOR),
        )
        if not isinstance(self.aggregate_status, RuntimeDependencyAggregateStatus):
            object.__setattr__(self, "aggregate_status", RuntimeDependencyAggregateStatus(str(self.aggregate_status)))
        ordered_checks = tuple(
            sorted(
                self.checks,
                key=lambda entry: (
                    entry.dependency_id,
                    entry.classification.value,
                    entry.probe_type.value,
                    entry.target,
                ),
            )
        )
        object.__setattr__(self, "checks", ordered_checks)

        derived_status = _runtime_aggregate_from_checks(ordered_checks)
        if self.aggregate_status is not derived_status:
            raise ValueError("Runtime aggregate_status must match deterministic required/optional aggregation rules")

        expected_pipeline = ("run_runtime_dependency_checks",)
        if tuple(self.pipeline_order) != expected_pipeline:
            raise ValueError("RuntimeDependencyReport pipeline_order must be ('run_runtime_dependency_checks',)")
        object.__setattr__(self, "pipeline_order", expected_pipeline)

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "aggregate_status": self.aggregate_status.value,
            "checks": [entry.as_payload() for entry in self.checks],
            "pipeline_order": list(self.pipeline_order),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Phase5Result:
    schema_version: str
    route_spec_schema_version: str
    pipeline_order: tuple[str, ...]
    runtime: RuntimeDependencyReport
    output: Phase5OutputSurfaces
    help: Phase5HelpResponse

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _validate_schema_major(self.schema_version, SUPPORTED_PHASE5_SCHEMA_MAJOR),
        )
        object.__setattr__(self, "route_spec_schema_version", _normalize_text(self.route_spec_schema_version))
        expected_pipeline = ("run_runtime_dependency_checks", "generate_output_surfaces", "resolve_help_response")
        if tuple(self.pipeline_order) != expected_pipeline:
            raise ValueError(
                "Phase5Result pipeline_order must be run_runtime_dependency_checks -> generate_output_surfaces -> resolve_help_response"
            )
        object.__setattr__(self, "pipeline_order", expected_pipeline)
        if not isinstance(self.runtime, RuntimeDependencyReport):
            raise TypeError("runtime must be a RuntimeDependencyReport")
        if not isinstance(self.output, Phase5OutputSurfaces):
            raise TypeError("output must be a Phase5OutputSurfaces")
        if not isinstance(self.help, Phase5HelpResponse):
            raise TypeError("help must be a Phase5HelpResponse")
        if self.output.machine_payload.route_spec_schema_version != self.route_spec_schema_version:
            raise ValueError("Phase5Result route_spec_schema_version must align with output machine payload")
        if self.help.terminal_status is not self.output.machine_payload.terminal_status:
            raise ValueError("Phase5Result help terminal status must align with output terminal status")
        if self.help.output_code is not self.output.machine_payload.output_code:
            raise ValueError("Phase5Result help output code must align with output machine payload")

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "route_spec_schema_version": self.route_spec_schema_version,
            "pipeline_order": list(self.pipeline_order),
            "runtime": self.runtime.as_payload(),
            "output": self.output.as_payload(),
            "help": self.help.as_payload(),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Phase5BoundaryViolation:
    code: Phase5BoundaryErrorCode
    evidence_paths: tuple[str, ...]
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, Phase5BoundaryErrorCode):
            object.__setattr__(self, "code", Phase5BoundaryErrorCode(str(self.code)))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "detail", _normalize_text(self.detail))

    def as_payload(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "evidence_paths": list(self.evidence_paths),
            "detail": self.detail,
        }


def _validate_schema_major(schema_version: str, expected_major: str) -> str:
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise ValueError("schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != expected_major:
        raise ValueError(f"Unsupported schema major '{major}', expected {expected_major}.x")
    return normalized


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_optional_text(value: object) -> str | None:
    normalized = _normalize_text(value)
    return normalized or None


def _normalize_sorted_text(values: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    normalized = {
        text
        for text in (_normalize_text(item) for item in values)
        if text
    }
    return tuple(sorted(normalized))


def _normalize_action_steps(actions: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized = []
    seen: set[str] = set()
    for action in actions:
        text = _normalize_text(action)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    if not normalized:
        raise ValueError("Help actions must include at least one deterministic advisory step")
    return tuple(normalized)


def _runtime_reason_for(
    *,
    classification: RuntimeDependencyClassification,
    status: RuntimeDependencyStatus,
) -> RuntimeDependencyReasonCode:
    if status is RuntimeDependencyStatus.PRESENT:
        return RuntimeDependencyReasonCode.PRESENT
    if classification is RuntimeDependencyClassification.REQUIRED:
        return RuntimeDependencyReasonCode.REQUIRED_MISSING
    return RuntimeDependencyReasonCode.OPTIONAL_MISSING


def _runtime_aggregate_from_checks(
    checks: tuple[RuntimeDependencyCheck, ...],
) -> RuntimeDependencyAggregateStatus:
    has_required_missing = any(
        entry.status is RuntimeDependencyStatus.MISSING
        and entry.classification is RuntimeDependencyClassification.REQUIRED
        for entry in checks
    )
    if has_required_missing:
        return RuntimeDependencyAggregateStatus.BLOCKING

    has_optional_missing = any(
        entry.status is RuntimeDependencyStatus.MISSING
        and entry.classification is RuntimeDependencyClassification.OPTIONAL
        for entry in checks
    )
    if has_optional_missing:
        return RuntimeDependencyAggregateStatus.DEGRADED
    return RuntimeDependencyAggregateStatus.PASS


__all__ = [
    "HELP_CODE_TOPIC_MAP",
    "OUTPUT_SECTION_ORDER",
    "PHASE5_ENGINE_SCHEMA_VERSION",
    "PHASE5_OUTPUT_SCHEMA_VERSION",
    "PHASE5_RUNTIME_SCHEMA_VERSION",
    "SUPPORTED_PHASE5_SCHEMA_MAJOR",
    "HelpCode",
    "HelpTopic",
    "OutputSurfaceCode",
    "OutputTerminalStatus",
    "Phase5BoundaryErrorCode",
    "Phase5BoundaryViolation",
    "Phase5HelpResponse",
    "Phase5OutputPayload",
    "Phase5OutputSurfaces",
    "Phase5Result",
    "RuntimeDependencyAggregateStatus",
    "RuntimeDependencyCheck",
    "RuntimeDependencyClassification",
    "RuntimeDependencyProbeType",
    "RuntimeDependencyReasonCode",
    "RuntimeDependencyReport",
    "RuntimeDependencySpec",
    "RuntimeDependencyStatus",
]
