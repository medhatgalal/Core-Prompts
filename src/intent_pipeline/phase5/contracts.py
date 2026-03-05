"""Phase-5 typed output contracts and deterministic serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any


PHASE5_OUTPUT_SCHEMA_VERSION = "5.0.0"
SUPPORTED_PHASE5_SCHEMA_MAJOR = "5"

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


__all__ = [
    "OUTPUT_SECTION_ORDER",
    "PHASE5_OUTPUT_SCHEMA_VERSION",
    "SUPPORTED_PHASE5_SCHEMA_MAJOR",
    "OutputSurfaceCode",
    "OutputTerminalStatus",
    "Phase5OutputPayload",
    "Phase5OutputSurfaces",
]
