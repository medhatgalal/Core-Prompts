"""Canonical deterministic Rosetta route-spec translation for phase 3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping

from intent_pipeline.routing.contracts import validate_routing_schema_version, validate_uplift_artifact
from intent_pipeline.routing.semantic_router import RouteSelection
from intent_pipeline.routing.signal_bundle import SignalBundle
from intent_pipeline.uplift.contracts import UpliftContract


ROSETTA_ROUTE_SPEC_SCHEMA_VERSION = "3.0.0"


class RosettaTranslationErrorCode(str, Enum):
    TASK_FOCUS_OUTSIDE_TASK_GRAPH = "TASK_FOCUS_OUTSIDE_TASK_GRAPH"
    EVIDENCE_TASK_OUTSIDE_TASK_GRAPH = "EVIDENCE_TASK_OUTSIDE_TASK_GRAPH"


class RosettaTranslationError(ValueError):
    """Typed Rosetta translation error with deterministic code + detail payload."""

    def __init__(
        self,
        code: RosettaTranslationErrorCode,
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
class RosettaEvidenceLink:
    criterion_id: str
    evidence_id: str
    task_id: str
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "criterion_id", _normalize_text(self.criterion_id))
        object.__setattr__(self, "evidence_id", _normalize_text(self.evidence_id))
        object.__setattr__(self, "task_id", _normalize_text(self.task_id))
        object.__setattr__(self, "source", _normalize_text(self.source))

    def as_payload(self) -> dict[str, str]:
        return {
            "criterion_id": self.criterion_id,
            "evidence_id": self.evidence_id,
            "task_id": self.task_id,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class RosettaRouteSpec:
    schema_version: str
    decision: str
    route_profile: str
    dominant_signal: str
    dominant_rule_id: str
    applied_rule_ids: tuple[str, ...]
    task_focus_ids: tuple[str, ...]
    evidence_links: tuple[RosettaEvidenceLink, ...]
    acceptance_gate: str | None
    missing_evidence: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", validate_routing_schema_version(self.schema_version))
        object.__setattr__(self, "decision", _normalize_text(self.decision))
        object.__setattr__(self, "route_profile", _normalize_text(self.route_profile))
        object.__setattr__(self, "dominant_signal", _normalize_text(self.dominant_signal))
        object.__setattr__(self, "dominant_rule_id", _normalize_text(self.dominant_rule_id))
        object.__setattr__(self, "applied_rule_ids", _unique_in_order(self.applied_rule_ids))
        object.__setattr__(self, "task_focus_ids", _unique_in_order(self.task_focus_ids))
        object.__setattr__(
            self,
            "evidence_links",
            tuple(sorted(self.evidence_links, key=lambda entry: (entry.criterion_id, entry.evidence_id, entry.task_id, entry.source))),
        )
        object.__setattr__(self, "acceptance_gate", _normalize_optional_text(self.acceptance_gate))
        object.__setattr__(self, "missing_evidence", _normalize_sorted_text(self.missing_evidence))
        object.__setattr__(self, "ambiguity_reasons", _normalize_sorted_text(self.ambiguity_reasons))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision,
            "route_profile": self.route_profile,
            "dominant_signal": self.dominant_signal,
            "dominant_rule_id": self.dominant_rule_id,
            "applied_rule_ids": list(self.applied_rule_ids),
            "task_focus_ids": list(self.task_focus_ids),
            "evidence_links": [link.as_payload() for link in self.evidence_links],
            "acceptance_gate": self.acceptance_gate,
            "missing_evidence": list(self.missing_evidence),
            "ambiguity_reasons": list(self.ambiguity_reasons),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def translate_to_route_spec(
    selection: RouteSelection,
    signals: SignalBundle,
    uplift: UpliftContract | Mapping[str, Any],
) -> RosettaRouteSpec:
    """Translate deterministic routing outputs into canonical Rosetta route-spec."""
    if not isinstance(selection, RouteSelection):
        raise TypeError("translate_to_route_spec expects RouteSelection")
    if not isinstance(signals, SignalBundle):
        raise TypeError("translate_to_route_spec expects SignalBundle")

    uplift_payload = validate_uplift_artifact(uplift)
    task_graph = _as_mapping(uplift_payload.get("task_graph"))
    allowed_task_ids = _extract_task_ids(task_graph.get("nodes"))

    task_focus_ids = _resolve_task_focus_ids(signals, allowed_task_ids)
    evidence_links = _extract_evidence_links(
        uplift_payload,
        allowed_task_ids=allowed_task_ids,
        task_focus_ids=task_focus_ids,
    )

    missing_evidence = set(signals.missing_evidence)
    missing_evidence.update(selection.missing_evidence)
    linked_task_ids = {link.task_id for link in evidence_links}
    missing_focus_evidence = sorted(task_id for task_id in task_focus_ids if task_id not in linked_task_ids)
    for task_id in missing_focus_evidence:
        missing_evidence.add(f"acceptance.criteria.evidence::{task_id}")

    applied_rule_ids = _unique_in_order((*selection.applied_rule_ids, selection.dominant_rule_id))

    return RosettaRouteSpec(
        schema_version=ROSETTA_ROUTE_SPEC_SCHEMA_VERSION,
        decision=selection.decision.value,
        route_profile=selection.route_profile.value,
        dominant_signal=selection.dominant_layer,
        dominant_rule_id=selection.dominant_rule_id,
        applied_rule_ids=applied_rule_ids,
        task_focus_ids=task_focus_ids,
        evidence_links=evidence_links,
        acceptance_gate=signals.acceptance_decision,
        missing_evidence=tuple(sorted(missing_evidence)),
        ambiguity_reasons=selection.ambiguity_reasons,
    )


def _resolve_task_focus_ids(signals: SignalBundle, allowed_task_ids: tuple[str, ...]) -> tuple[str, ...]:
    focus_candidates = signals.constrained_task_ids or signals.task_node_ids
    task_focus_ids = _unique_in_order(focus_candidates)
    invalid_ids = sorted(task_id for task_id in task_focus_ids if task_id not in allowed_task_ids)
    if invalid_ids:
        raise RosettaTranslationError(
            RosettaTranslationErrorCode.TASK_FOCUS_OUTSIDE_TASK_GRAPH,
            "task_focus_ids must be a subset of uplift task graph node IDs",
            detail={
                "task_focus_ids": list(task_focus_ids),
                "invalid_ids": invalid_ids,
            },
        )
    return task_focus_ids


def _extract_evidence_links(
    uplift_payload: Mapping[str, Any],
    *,
    allowed_task_ids: tuple[str, ...],
    task_focus_ids: tuple[str, ...],
) -> tuple[RosettaEvidenceLink, ...]:
    acceptance = _as_mapping(uplift_payload.get("acceptance"))
    criteria = acceptance.get("criteria")
    if not isinstance(criteria, list):
        return ()

    focus_set = set(task_focus_ids)
    links: list[RosettaEvidenceLink] = []

    for criterion in sorted((entry for entry in criteria if isinstance(entry, Mapping)), key=lambda entry: _normalize_text(str(entry.get("criterion_id", "")))):
        criterion_id = _normalize_text(str(criterion.get("criterion_id", "")))
        evidence_entries = criterion.get("evidence")
        if not isinstance(evidence_entries, list):
            continue
        for evidence in sorted(
            (entry for entry in evidence_entries if isinstance(entry, Mapping)),
            key=lambda entry: _normalize_text(str(entry.get("evidence_id", ""))),
        ):
            task_id = _normalize_text(str(evidence.get("task_id", "")))
            if task_id not in allowed_task_ids:
                raise RosettaTranslationError(
                    RosettaTranslationErrorCode.EVIDENCE_TASK_OUTSIDE_TASK_GRAPH,
                    "acceptance evidence task_id must exist in uplift task graph",
                    detail={
                        "task_id": task_id,
                        "allowed_task_ids": list(allowed_task_ids),
                    },
                )
            if focus_set and task_id not in focus_set:
                continue
            links.append(
                RosettaEvidenceLink(
                    criterion_id=criterion_id,
                    evidence_id=_normalize_text(str(evidence.get("evidence_id", ""))),
                    task_id=task_id,
                    source=_normalize_text(str(evidence.get("source", ""))),
                )
            )

    return tuple(links)


def _extract_task_ids(raw_nodes: object) -> tuple[str, ...]:
    if not isinstance(raw_nodes, list):
        return ()
    task_ids: list[str] = []
    for node in raw_nodes:
        if not isinstance(node, Mapping):
            continue
        task_id = _normalize_optional_text(node.get("node_id"))
        if task_id:
            task_ids.append(task_id)
    return _unique_in_order(task_ids)


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_optional_text(value: object) -> str | None:
    normalized = _normalize_text(value)
    return normalized or None


def _normalize_sorted_text(values: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    return tuple(sorted({normalized for normalized in (_normalize_text(value) for value in values) if normalized}))


def _unique_in_order(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = _normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


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
    "ROSETTA_ROUTE_SPEC_SCHEMA_VERSION",
    "RosettaEvidenceLink",
    "RosettaRouteSpec",
    "RosettaTranslationError",
    "RosettaTranslationErrorCode",
    "translate_to_route_spec",
]
