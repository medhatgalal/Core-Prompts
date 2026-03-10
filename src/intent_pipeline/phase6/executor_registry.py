"""Phase-6 closed executor registry parsing and resolution."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Iterable

from intent_pipeline.phase6.contracts import (
    ExecutionDecisionCode,
    Phase6ContractError,
    SUPPORTED_PHASE6_SCHEMA_MAJOR,
)


PHASE6_REGISTRY_SCHEMA_VERSION = "6.0.0"


@dataclass(frozen=True, slots=True)
class ExecutorRegistryEntry:
    adapter_id: str
    route_profile: str
    target_tool_id: str
    capabilities: tuple[str, ...]
    supports_simulation: bool
    supports_execution: bool
    rule_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "adapter_id", _require_text(self.adapter_id, "adapter_id"))
        object.__setattr__(self, "route_profile", _require_text(self.route_profile, "route_profile"))
        object.__setattr__(self, "target_tool_id", _require_text(self.target_tool_id, "target_tool_id"))
        object.__setattr__(self, "capabilities", _normalize_sorted_text(self.capabilities))
        object.__setattr__(self, "supports_simulation", bool(self.supports_simulation))
        object.__setattr__(self, "supports_execution", bool(self.supports_execution))
        object.__setattr__(self, "rule_id", _require_text(self.rule_id, "rule_id"))
        if not self.capabilities:
            raise ValueError("ExecutorRegistryEntry capabilities must be non-empty")

    def as_payload(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "capabilities": list(self.capabilities),
            "supports_simulation": self.supports_simulation,
            "supports_execution": self.supports_execution,
            "rule_id": self.rule_id,
        }


@dataclass(frozen=True, slots=True)
class ExecutorRegistry:
    schema_version: str
    entries: tuple[ExecutorRegistryEntry, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE6_SCHEMA_MAJOR))
        ordered_entries = tuple(sorted(self.entries, key=lambda entry: (entry.route_profile, entry.target_tool_id, entry.adapter_id)))
        object.__setattr__(self, "entries", ordered_entries)
        seen_keys: set[tuple[str, str]] = set()
        for entry in ordered_entries:
            binding = (entry.route_profile, entry.target_tool_id)
            if binding in seen_keys:
                raise ValueError(f"Duplicate registry binding for {entry.route_profile}/{entry.target_tool_id}")
            seen_keys.add(binding)

    def resolve(self, route_profile: str, target_tool_id: str) -> ExecutorRegistryEntry:
        normalized_profile = _require_text(route_profile, "route_profile")
        normalized_tool_id = _require_text(target_tool_id, "target_tool_id")
        matches = [entry for entry in self.entries if entry.route_profile == normalized_profile and entry.target_tool_id == normalized_tool_id]
        if not matches:
            raise Phase6ContractError(
                ExecutionDecisionCode.REGISTRY_UNMAPPED,
                "No executor registry binding exists for route_profile/target_tool_id",
                evidence_path="phase6.registry.entries",
                detail={"route_profile": normalized_profile, "target_tool_id": normalized_tool_id},
            )
        if len(matches) > 1:
            raise Phase6ContractError(
                ExecutionDecisionCode.REGISTRY_DUPLICATE,
                "Ambiguous executor registry binding exists for route_profile/target_tool_id",
                evidence_path="phase6.registry.entries",
                detail={"route_profile": normalized_profile, "target_tool_id": normalized_tool_id},
            )
        return matches[0]

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "entries": [entry.as_payload() for entry in self.entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def parse_executor_registry(registry: ExecutorRegistry | Mapping[str, Any]) -> ExecutorRegistry:
    if isinstance(registry, ExecutorRegistry):
        return registry
    if not isinstance(registry, Mapping):
        raise Phase6ContractError(
            ExecutionDecisionCode.REGISTRY_UNMAPPED,
            "registry must be an ExecutorRegistry or mapping payload",
            evidence_path="phase6.registry",
            detail={"payload_type": type(registry).__name__},
        )
    payload = _canonicalize_mapping(registry)
    schema_version = _require_mapping_text(payload, "schema_version", "phase6.registry.schema_version")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        raise Phase6ContractError(
            ExecutionDecisionCode.REGISTRY_UNMAPPED,
            "phase6.registry.entries must be a list",
            evidence_path="phase6.registry.entries",
        )
    entries: list[ExecutorRegistryEntry] = []
    seen_keys: set[tuple[str, str]] = set()
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, Mapping):
            raise Phase6ContractError(
                ExecutionDecisionCode.REGISTRY_UNMAPPED,
                "Registry entries must be mapping payloads",
                evidence_path=f"phase6.registry.entries[{index}]",
            )
        entry = ExecutorRegistryEntry(
            adapter_id=_require_mapping_text(raw_entry, "adapter_id", f"phase6.registry.entries[{index}].adapter_id"),
            route_profile=_require_mapping_text(raw_entry, "route_profile", f"phase6.registry.entries[{index}].route_profile"),
            target_tool_id=_require_mapping_text(raw_entry, "target_tool_id", f"phase6.registry.entries[{index}].target_tool_id"),
            capabilities=tuple(_require_mapping_text_list(raw_entry, "capabilities", f"phase6.registry.entries[{index}].capabilities")),
            supports_simulation=bool(raw_entry.get("supports_simulation")),
            supports_execution=bool(raw_entry.get("supports_execution")),
            rule_id=_require_mapping_text(raw_entry, "rule_id", f"phase6.registry.entries[{index}].rule_id"),
        )
        binding = (entry.route_profile, entry.target_tool_id)
        if binding in seen_keys:
            raise Phase6ContractError(
                ExecutionDecisionCode.REGISTRY_DUPLICATE,
                "Duplicate executor registry binding exists for route_profile/target_tool_id",
                evidence_path=f"phase6.registry.entries[{index}]",
                detail={"route_profile": entry.route_profile, "target_tool_id": entry.target_tool_id},
            )
        seen_keys.add(binding)
        entries.append(entry)
    return ExecutorRegistry(schema_version=schema_version, entries=tuple(entries))


def _validate_schema_major(schema_version: str, expected_major: str) -> str:
    normalized = _require_text(schema_version, "schema_version")
    major = normalized.split(".", 1)[0]
    if major != expected_major:
        raise ValueError(f"Unsupported schema major '{major}', expected {expected_major}.x")
    return normalized


def _require_mapping_text(payload: Mapping[str, Any], key: str, evidence_path: str) -> str:
    value = _require_text(payload.get(key), key)
    if not value:
        raise Phase6ContractError(ExecutionDecisionCode.REGISTRY_UNMAPPED, f"{key} is required", evidence_path=evidence_path)
    return value


def _require_mapping_text_list(payload: Mapping[str, Any], key: str, evidence_path: str) -> list[str]:
    raw_values = payload.get(key)
    if not isinstance(raw_values, list):
        raise Phase6ContractError(
            ExecutionDecisionCode.REGISTRY_UNMAPPED,
            f"{key} must be a list of strings",
            evidence_path=evidence_path,
        )
    values = [_require_text(item, key) for item in raw_values if _require_text(item, key)]
    if not values:
        raise Phase6ContractError(
            ExecutionDecisionCode.REGISTRY_UNMAPPED,
            f"{key} must be non-empty",
            evidence_path=evidence_path,
        )
    return values


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        return ""
    normalized = " ".join(value.split()).strip()
    if not normalized:
        return ""
    return normalized


def _normalize_sorted_text(values: Iterable[str]) -> tuple[str, ...]:
    normalized = {text for text in (_require_text(item, "value") for item in values) if text}
    return tuple(sorted(normalized))


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
    "ExecutorRegistry",
    "ExecutorRegistryEntry",
    "PHASE6_REGISTRY_SCHEMA_VERSION",
    "parse_executor_registry",
]
