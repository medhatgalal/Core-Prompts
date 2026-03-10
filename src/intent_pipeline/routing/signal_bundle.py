"""Deterministic uplift-to-routing signal bundle extraction."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Sequence

from intent_pipeline.routing.contracts import (
    ROUTING_CONTRACT_SCHEMA_VERSION,
    RoutingBoundaryError,
    validate_routing_schema_version,
    validate_uplift_artifact,
    validate_uplift_schema_version,
)
from intent_pipeline.uplift.contracts import UpliftContract


@dataclass(frozen=True, slots=True)
class ConstraintSignal:
    constraint_id: str
    key: str
    value: str
    strength: str
    priority: int
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraint_id", _normalize_text(self.constraint_id))
        object.__setattr__(self, "key", _normalize_text(self.key))
        object.__setattr__(self, "value", _normalize_text(self.value))
        object.__setattr__(self, "strength", _normalize_text(self.strength))
        object.__setattr__(self, "source", _normalize_text(self.source))

    def as_payload(self) -> dict[str, Any]:
        return {
            "id": self.constraint_id,
            "key": self.key,
            "value": self.value,
            "strength": self.strength,
            "priority": self.priority,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class SignalBundle:
    schema_version: str
    uplift_schema_version: str
    context_schema_version: str | None
    primary_objective: str | None
    in_scope: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    quality_constraints: tuple[str, ...]
    intent_unknowns: tuple[str, ...]
    hard_constraints: tuple[ConstraintSignal, ...]
    soft_constraints: tuple[ConstraintSignal, ...]
    dropped_soft_constraints: tuple[ConstraintSignal, ...]
    conflict_codes: tuple[str, ...]
    task_node_ids: tuple[str, ...]
    constrained_task_ids: tuple[str, ...]
    acceptance_decision: str | None
    acceptance_failed_hard_criteria: tuple[str, ...]
    acceptance_missing_evidence: tuple[str, ...]
    acceptance_criterion_ids: tuple[str, ...]
    missing_evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", validate_routing_schema_version(self.schema_version))
        object.__setattr__(self, "uplift_schema_version", validate_uplift_schema_version(self.uplift_schema_version))
        object.__setattr__(
            self,
            "context_schema_version",
            _normalize_optional_text(self.context_schema_version),
        )
        object.__setattr__(self, "primary_objective", _normalize_optional_text(self.primary_objective))
        object.__setattr__(self, "in_scope", _unique_in_order(self.in_scope))
        object.__setattr__(self, "out_of_scope", _unique_in_order(self.out_of_scope))
        object.__setattr__(self, "quality_constraints", _unique_in_order(self.quality_constraints))
        object.__setattr__(self, "intent_unknowns", _unique_in_order(self.intent_unknowns))
        object.__setattr__(
            self,
            "hard_constraints",
            tuple(sorted(self.hard_constraints, key=_constraint_sort_key)),
        )
        object.__setattr__(
            self,
            "soft_constraints",
            tuple(sorted(self.soft_constraints, key=_constraint_sort_key)),
        )
        object.__setattr__(
            self,
            "dropped_soft_constraints",
            tuple(sorted(self.dropped_soft_constraints, key=_constraint_sort_key)),
        )
        object.__setattr__(
            self,
            "conflict_codes",
            tuple(sorted({item for item in self.conflict_codes if item})),
        )
        object.__setattr__(self, "task_node_ids", _unique_in_order(self.task_node_ids))
        object.__setattr__(self, "constrained_task_ids", _unique_in_order(self.constrained_task_ids))
        object.__setattr__(
            self,
            "acceptance_decision",
            _normalize_optional_text(self.acceptance_decision),
        )
        object.__setattr__(
            self,
            "acceptance_failed_hard_criteria",
            tuple(sorted({item for item in self.acceptance_failed_hard_criteria if item})),
        )
        object.__setattr__(
            self,
            "acceptance_missing_evidence",
            tuple(sorted({item for item in self.acceptance_missing_evidence if item})),
        )
        object.__setattr__(
            self,
            "acceptance_criterion_ids",
            _unique_in_order(self.acceptance_criterion_ids),
        )
        object.__setattr__(
            self,
            "missing_evidence",
            tuple(sorted({item for item in self.missing_evidence if item})),
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "uplift_schema_version": self.uplift_schema_version,
            "context_schema_version": self.context_schema_version,
            "primary_objective": self.primary_objective,
            "in_scope": list(self.in_scope),
            "out_of_scope": list(self.out_of_scope),
            "quality_constraints": list(self.quality_constraints),
            "intent_unknowns": list(self.intent_unknowns),
            "hard_constraints": [constraint.as_payload() for constraint in self.hard_constraints],
            "soft_constraints": [constraint.as_payload() for constraint in self.soft_constraints],
            "dropped_soft_constraints": [constraint.as_payload() for constraint in self.dropped_soft_constraints],
            "conflict_codes": list(self.conflict_codes),
            "task_node_ids": list(self.task_node_ids),
            "constrained_task_ids": list(self.constrained_task_ids),
            "acceptance_decision": self.acceptance_decision,
            "acceptance_failed_hard_criteria": list(self.acceptance_failed_hard_criteria),
            "acceptance_missing_evidence": list(self.acceptance_missing_evidence),
            "acceptance_criterion_ids": list(self.acceptance_criterion_ids),
            "missing_evidence": list(self.missing_evidence),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def build_signal_bundle(uplift: UpliftContract | Mapping[str, Any]) -> SignalBundle:
    payload = validate_uplift_artifact(uplift)
    missing_evidence: list[str] = []

    context = _as_mapping(payload["context"])
    intent = _as_mapping(payload["intent"])
    constraints = _as_mapping(payload["constraints"])
    task_graph = _as_mapping(payload["task_graph"])
    acceptance = _as_mapping(payload["acceptance"])

    context_schema_version = _extract_schema_version(
        context.get("schema_version"),
        field="context.schema_version",
        missing_evidence=missing_evidence,
    )
    primary_objective = _normalize_optional_text(intent.get("primary_objective"))
    if primary_objective is None:
        missing_evidence.append("intent.primary_objective")

    in_scope = _normalize_text_sequence(intent.get("in_scope"))
    out_of_scope = _normalize_text_sequence(intent.get("out_of_scope"))
    quality_constraints = _normalize_text_sequence(intent.get("quality_constraints"))
    intent_unknowns = _normalize_text_sequence(intent.get("unknowns"))

    if not in_scope:
        missing_evidence.append("intent.in_scope")
    if not quality_constraints:
        missing_evidence.append("intent.quality_constraints")

    hard_constraints = _extract_constraint_signals(
        constraints.get("applied_hard"),
        field="constraints.applied_hard",
        missing_evidence=missing_evidence,
    )
    soft_constraints = _extract_constraint_signals(
        constraints.get("applied_soft"),
        field="constraints.applied_soft",
        missing_evidence=missing_evidence,
    )
    dropped_soft_constraints = _extract_constraint_signals(
        constraints.get("dropped_soft"),
        field="constraints.dropped_soft",
        missing_evidence=missing_evidence,
    )
    conflict_codes = _extract_conflict_codes(
        constraints.get("conflicts"),
        field="constraints.conflicts",
        missing_evidence=missing_evidence,
    )

    task_node_ids, constrained_task_ids = _extract_task_graph_signals(
        task_graph.get("nodes"),
        missing_evidence=missing_evidence,
    )
    if not task_node_ids:
        missing_evidence.append("task_graph.nodes")

    acceptance_decision = _normalize_optional_text(acceptance.get("decision"))
    if acceptance_decision is None:
        missing_evidence.append("acceptance.decision")
    acceptance_failed_hard_criteria = _normalize_text_sequence(acceptance.get("failed_hard_criteria"))
    acceptance_missing_evidence = _normalize_text_sequence(acceptance.get("missing_evidence"))
    acceptance_criterion_ids = _extract_criterion_ids(
        acceptance.get("criteria"),
        field="acceptance.criteria",
        missing_evidence=missing_evidence,
    )

    combined_missing = sorted(
        set(missing_evidence).union(acceptance_missing_evidence)
    )

    return SignalBundle(
        schema_version=ROUTING_CONTRACT_SCHEMA_VERSION,
        uplift_schema_version=str(payload["schema_version"]),
        context_schema_version=context_schema_version,
        primary_objective=primary_objective,
        in_scope=in_scope,
        out_of_scope=out_of_scope,
        quality_constraints=quality_constraints,
        intent_unknowns=intent_unknowns,
        hard_constraints=hard_constraints,
        soft_constraints=soft_constraints,
        dropped_soft_constraints=dropped_soft_constraints,
        conflict_codes=conflict_codes,
        task_node_ids=task_node_ids,
        constrained_task_ids=constrained_task_ids,
        acceptance_decision=acceptance_decision,
        acceptance_failed_hard_criteria=acceptance_failed_hard_criteria,
        acceptance_missing_evidence=acceptance_missing_evidence,
        acceptance_criterion_ids=acceptance_criterion_ids,
        missing_evidence=tuple(combined_missing),
    )


def _extract_schema_version(value: object, *, field: str, missing_evidence: list[str]) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        missing_evidence.append(field)
        return None
    try:
        return validate_uplift_schema_version(normalized)
    except RoutingBoundaryError:
        missing_evidence.append(field)
        return normalized


def _extract_constraint_signals(
    raw_constraints: object,
    *,
    field: str,
    missing_evidence: list[str],
) -> tuple[ConstraintSignal, ...]:
    if not _is_list_like(raw_constraints):
        missing_evidence.append(field)
        return ()

    signals: list[ConstraintSignal] = []
    for index, candidate in enumerate(raw_constraints):
        if not isinstance(candidate, Mapping):
            missing_evidence.append(f"{field}[{index}]")
            continue
        constraint_id = _normalize_optional_text(candidate.get("id"))
        key = _normalize_optional_text(candidate.get("key"))
        value = _normalize_optional_text(candidate.get("value"))
        strength = _normalize_optional_text(candidate.get("strength"))
        source = _normalize_optional_text(candidate.get("source"))
        priority = candidate.get("priority")

        if constraint_id is None:
            missing_evidence.append(f"{field}[{index}].id")
        if key is None:
            missing_evidence.append(f"{field}[{index}].key")
        if value is None:
            missing_evidence.append(f"{field}[{index}].value")
        if strength is None:
            missing_evidence.append(f"{field}[{index}].strength")
        if source is None:
            missing_evidence.append(f"{field}[{index}].source")
        if not isinstance(priority, int):
            missing_evidence.append(f"{field}[{index}].priority")

        if (
            constraint_id is None
            or key is None
            or value is None
            or strength is None
            or source is None
            or not isinstance(priority, int)
        ):
            continue

        signals.append(
            ConstraintSignal(
                constraint_id=constraint_id,
                key=key,
                value=value,
                strength=strength,
                priority=priority,
                source=source,
            )
        )

    return tuple(sorted(signals, key=_constraint_sort_key))


def _extract_conflict_codes(
    raw_conflicts: object,
    *,
    field: str,
    missing_evidence: list[str],
) -> tuple[str, ...]:
    if not _is_list_like(raw_conflicts):
        missing_evidence.append(field)
        return ()

    codes: list[str] = []
    for index, conflict in enumerate(raw_conflicts):
        if not isinstance(conflict, Mapping):
            missing_evidence.append(f"{field}[{index}]")
            continue
        code = _normalize_optional_text(conflict.get("code"))
        if code is None:
            missing_evidence.append(f"{field}[{index}].code")
            continue
        codes.append(code)
    return tuple(sorted(set(codes)))


def _extract_task_graph_signals(
    raw_nodes: object,
    *,
    missing_evidence: list[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not _is_list_like(raw_nodes):
        missing_evidence.append("task_graph.nodes")
        return (), ()

    node_ids: list[str] = []
    constrained_ids: list[str] = []
    for index, candidate in enumerate(raw_nodes):
        if not isinstance(candidate, Mapping):
            missing_evidence.append(f"task_graph.nodes[{index}]")
            continue
        node_id = _normalize_optional_text(candidate.get("node_id"))
        if node_id is None:
            missing_evidence.append(f"task_graph.nodes[{index}].node_id")
            continue
        node_ids.append(node_id)
        constraint_keys = candidate.get("constraint_keys")
        if _is_list_like(constraint_keys) and any(_normalize_optional_text(item) for item in constraint_keys):
            constrained_ids.append(node_id)

    return _unique_in_order(node_ids), _unique_in_order(constrained_ids)


def _extract_criterion_ids(
    raw_criteria: object,
    *,
    field: str,
    missing_evidence: list[str],
) -> tuple[str, ...]:
    if not _is_list_like(raw_criteria):
        missing_evidence.append(field)
        return ()

    criterion_ids: list[str] = []
    for index, criterion in enumerate(raw_criteria):
        if not isinstance(criterion, Mapping):
            missing_evidence.append(f"{field}[{index}]")
            continue
        criterion_id = _normalize_optional_text(criterion.get("criterion_id"))
        if criterion_id is None:
            missing_evidence.append(f"{field}[{index}].criterion_id")
            continue
        criterion_ids.append(criterion_id)
    return _unique_in_order(criterion_ids)


def _as_mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("routing section must be mapping")
    return value


def _normalize_optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = _normalize_text(value)
    return normalized or None


def _normalize_text(value: str) -> str:
    return value.strip()


def _normalize_text_sequence(value: object) -> tuple[str, ...]:
    if not _is_list_like(value):
        return ()
    normalized: list[str] = []
    for candidate in value:
        normalized_value = _normalize_optional_text(candidate)
        if normalized_value is not None:
            normalized.append(normalized_value)
    return _unique_in_order(normalized)


def _is_list_like(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _unique_in_order(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


def _constraint_sort_key(constraint: ConstraintSignal) -> tuple[str, int, str, str, str]:
    return (
        constraint.key,
        -constraint.priority,
        constraint.value,
        constraint.constraint_id,
        constraint.source,
    )


__all__ = [
    "ConstraintSignal",
    "SignalBundle",
    "build_signal_bundle",
]
