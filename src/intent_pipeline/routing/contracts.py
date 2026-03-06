"""Phase-3 routing boundary contracts and schema validation primitives."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping

from intent_pipeline.uplift.contracts import UpliftContract


ROUTING_CONTRACT_SCHEMA_VERSION = "3.0.0"
SUPPORTED_ROUTING_SCHEMA_MAJOR = "3"
SUPPORTED_UPLIFT_SCHEMA_MAJOR = "2"
REQUIRED_UPLIFT_SECTIONS: tuple[str, ...] = (
    "context",
    "intent",
    "task_graph",
    "constraints",
    "acceptance",
)


class RouteProfile(str, Enum):
    """Closed deterministic profile taxonomy for routing outcomes."""

    IMPLEMENTATION = "IMPLEMENTATION"
    RESEARCH = "RESEARCH"
    VALIDATION = "VALIDATION"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RouteDecision(str, Enum):
    """Typed deterministic routing decision semantics."""

    PASS_ROUTE = "PASS_ROUTE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RoutingBoundaryErrorCode(str, Enum):
    INVALID_UPLIFT_PAYLOAD = "INVALID_UPLIFT_PAYLOAD"
    UNSUPPORTED_INPUT_SCHEMA = "UNSUPPORTED_INPUT_SCHEMA"
    UNSUPPORTED_ROUTING_SCHEMA = "UNSUPPORTED_ROUTING_SCHEMA"
    MISSING_REQUIRED_SECTION = "MISSING_REQUIRED_SECTION"


class RoutingBoundaryError(ValueError):
    """Typed routing boundary error with deterministic machine-readable code."""

    def __init__(
        self,
        code: RoutingBoundaryErrorCode,
        message: str,
        *,
        detail: Mapping[str, Any] | None = None,
    ) -> None:
        normalized_message = _normalize_text(message)
        if not normalized_message:
            normalized_message = code.value
        super().__init__(f"{code.value}: {normalized_message}")
        self.code = code
        self.detail = _canonicalize_mapping(detail or {})


@dataclass(frozen=True, slots=True)
class RoutingContract:
    schema_version: str
    uplift_schema_version: str
    route_profile: RouteProfile
    rationale: str = ""
    missing_evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", validate_routing_schema_version(self.schema_version))
        object.__setattr__(self, "uplift_schema_version", validate_uplift_schema_version(self.uplift_schema_version))
        if not isinstance(self.route_profile, RouteProfile):
            object.__setattr__(self, "route_profile", RouteProfile(str(self.route_profile)))
        object.__setattr__(self, "rationale", _normalize_text(self.rationale))
        object.__setattr__(
            self,
            "missing_evidence",
            tuple(sorted({item.strip() for item in self.missing_evidence if isinstance(item, str) and item.strip()})),
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "uplift_schema_version": self.uplift_schema_version,
            "route_profile": self.route_profile.value,
            "rationale": self.rationale,
            "missing_evidence": list(self.missing_evidence),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def validate_uplift_artifact(uplift: UpliftContract | Mapping[str, Any]) -> dict[str, Any]:
    payload = _coerce_uplift_payload(uplift)
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str):
        raise RoutingBoundaryError(
            RoutingBoundaryErrorCode.INVALID_UPLIFT_PAYLOAD,
            "Uplift payload requires string schema_version",
            detail={"field": "schema_version"},
        )

    normalized_schema = validate_uplift_schema_version(schema_version)
    missing_sections = tuple(sorted(section for section in REQUIRED_UPLIFT_SECTIONS if section not in payload))
    if missing_sections:
        raise RoutingBoundaryError(
            RoutingBoundaryErrorCode.MISSING_REQUIRED_SECTION,
            "Uplift payload is missing required routing sections",
            detail={"missing_sections": list(missing_sections)},
        )

    for section in REQUIRED_UPLIFT_SECTIONS:
        if not isinstance(payload[section], Mapping):
            raise RoutingBoundaryError(
                RoutingBoundaryErrorCode.INVALID_UPLIFT_PAYLOAD,
                f"Uplift section '{section}' must be a mapping",
                detail={"section": section},
            )

    canonical = _canonicalize_mapping(payload)
    canonical["schema_version"] = normalized_schema
    return canonical


def validate_routing_schema_version(schema_version: str) -> str:
    return _validate_schema_version(
        schema_version,
        expected_major=SUPPORTED_ROUTING_SCHEMA_MAJOR,
        code=RoutingBoundaryErrorCode.UNSUPPORTED_ROUTING_SCHEMA,
    )


def validate_uplift_schema_version(schema_version: str) -> str:
    return _validate_schema_version(
        schema_version,
        expected_major=SUPPORTED_UPLIFT_SCHEMA_MAJOR,
        code=RoutingBoundaryErrorCode.UNSUPPORTED_INPUT_SCHEMA,
    )


def _coerce_uplift_payload(uplift: UpliftContract | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(uplift, UpliftContract):
        return uplift.as_payload()
    if isinstance(uplift, Mapping):
        return _canonicalize_mapping(uplift)
    raise RoutingBoundaryError(
        RoutingBoundaryErrorCode.INVALID_UPLIFT_PAYLOAD,
        "Routing boundary requires UpliftContract or mapping payload",
        detail={"payload_type": type(uplift).__name__},
    )


def _validate_schema_version(
    schema_version: str,
    *,
    expected_major: str,
    code: RoutingBoundaryErrorCode,
) -> str:
    if not isinstance(schema_version, str):
        raise RoutingBoundaryError(
            code,
            "schema_version must be str",
            detail={"value_type": type(schema_version).__name__},
        )
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise RoutingBoundaryError(code, "schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != expected_major:
        raise RoutingBoundaryError(
            code,
            f"Unsupported schema major version '{major}'. Expected {expected_major}.x",
            detail={"schema_version": normalized, "expected_major": expected_major},
        )
    return normalized


def _normalize_text(value: str) -> str:
    return value.strip()


def _canonicalize_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _canonicalize_value(data[key]) for key in sorted(data)}


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _canonicalize_mapping(value)
    if isinstance(value, tuple):
        return [_canonicalize_value(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize_value(item) for item in value]
    return value


__all__ = [
    "REQUIRED_UPLIFT_SECTIONS",
    "ROUTING_CONTRACT_SCHEMA_VERSION",
    "RouteDecision",
    "RouteProfile",
    "RoutingBoundaryError",
    "RoutingBoundaryErrorCode",
    "RoutingContract",
    "SUPPORTED_ROUTING_SCHEMA_MAJOR",
    "SUPPORTED_UPLIFT_SCHEMA_MAJOR",
    "validate_routing_schema_version",
    "validate_uplift_artifact",
    "validate_uplift_schema_version",
]
