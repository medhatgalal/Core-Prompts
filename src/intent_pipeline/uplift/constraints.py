"""Typed deterministic constraint classification and resolution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Mapping, Sequence


class ConstraintStrength(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class ConstraintConflictCode(str, Enum):
    HARD_CONFLICT = "HARD_CONFLICT"
    SOFT_CONFLICTS_WITH_HARD = "SOFT_CONFLICTS_WITH_HARD"
    SOFT_CONFLICT = "SOFT_CONFLICT"
    SOFT_TIE_BREAK = "SOFT_TIE_BREAK"


@dataclass(frozen=True, slots=True)
class Constraint:
    key: str
    value: str
    strength: ConstraintStrength
    priority: int = 0
    source: str = "unspecified"
    constraint_id: str | None = None

    def stable_id(self) -> str:
        if self.constraint_id is not None:
            return self.constraint_id
        return f"{self.key}:{self.value}:{self.source}:{self.priority}:{self.strength.value}"

    def as_payload(self) -> dict[str, object]:
        return {
            "id": self.stable_id(),
            "key": self.key,
            "value": self.value,
            "strength": self.strength.value,
            "priority": self.priority,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class ConstraintConflict:
    code: ConstraintConflictCode
    key: str
    winner_id: str | None
    loser_ids: tuple[str, ...]
    detail: str

    def as_payload(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "key": self.key,
            "winner_id": self.winner_id,
            "loser_ids": list(self.loser_ids),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class ConstraintResolution:
    applied_hard: tuple[Constraint, ...]
    applied_soft: tuple[Constraint, ...]
    dropped_soft: tuple[Constraint, ...]
    conflicts: tuple[ConstraintConflict, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "applied_hard": [constraint.as_payload() for constraint in self.applied_hard],
            "applied_soft": [constraint.as_payload() for constraint in self.applied_soft],
            "dropped_soft": [constraint.as_payload() for constraint in self.dropped_soft],
            "conflicts": [conflict.as_payload() for conflict in self.conflicts],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class HardConstraintConflict:
    key: str
    constraints: tuple[Constraint, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "code": ConstraintConflictCode.HARD_CONFLICT.value,
            "key": self.key,
            "constraints": [constraint.as_payload() for constraint in self.constraints],
            "values": sorted({constraint.value for constraint in self.constraints}),
        }


class HardConstraintConflictError(ValueError):
    """Raised when contradictory hard constraints are present."""

    def __init__(self, conflict: HardConstraintConflict) -> None:
        super().__init__(f"HARD_CONFLICT: {conflict.key}")
        self.conflict = conflict


ConstraintInput = Constraint | Mapping[str, object]


def resolve_constraints(constraints: Sequence[ConstraintInput]) -> ConstraintResolution:
    typed_constraints = tuple(sorted((_coerce_constraint(constraint) for constraint in constraints), key=_ordering_key))
    by_key: dict[str, list[Constraint]] = {}
    for constraint in typed_constraints:
        by_key.setdefault(constraint.key, []).append(constraint)

    applied_hard: list[Constraint] = []
    applied_soft: list[Constraint] = []
    dropped_soft: list[Constraint] = []
    conflicts: list[ConstraintConflict] = []

    for key in sorted(by_key):
        candidates = by_key[key]
        hard_constraints = [constraint for constraint in candidates if constraint.strength is ConstraintStrength.HARD]
        soft_constraints = [constraint for constraint in candidates if constraint.strength is ConstraintStrength.SOFT]

        hard_winner: Constraint | None = None
        if hard_constraints:
            hard_winner = _resolve_hard_constraints(key, hard_constraints)
            applied_hard.append(hard_winner)

        if soft_constraints:
            soft_result = _resolve_soft_constraints(
                key=key,
                soft_constraints=soft_constraints,
                hard_winner=hard_winner,
            )
            if soft_result["winner"] is not None:
                applied_soft.append(soft_result["winner"])
            dropped_soft.extend(soft_result["dropped"])
            conflicts.extend(soft_result["conflicts"])

    return ConstraintResolution(
        applied_hard=tuple(sorted(applied_hard, key=_ordering_key)),
        applied_soft=tuple(sorted(applied_soft, key=_ordering_key)),
        dropped_soft=tuple(sorted(dropped_soft, key=_ordering_key)),
        conflicts=tuple(sorted(conflicts, key=lambda conflict: (conflict.key, conflict.code.value, conflict.winner_id or ""))),
    )


def _coerce_constraint(raw: ConstraintInput) -> Constraint:
    if isinstance(raw, Constraint):
        return raw
    key = str(raw.get("key", "")).strip()
    value = str(raw.get("value", "")).strip()
    if key == "" or value == "":
        raise TypeError("Constraint key and value must be non-empty strings.")

    strength_raw = str(raw.get("strength", "")).strip().lower()
    if strength_raw not in {ConstraintStrength.HARD.value, ConstraintStrength.SOFT.value}:
        raise TypeError("Constraint strength must be 'hard' or 'soft'.")

    priority_raw = raw.get("priority", 0)
    if not isinstance(priority_raw, int):
        raise TypeError("Constraint priority must be an int.")

    source = str(raw.get("source", "unspecified")).strip() or "unspecified"
    constraint_id_raw = raw.get("id")
    constraint_id = str(constraint_id_raw).strip() if constraint_id_raw is not None else None
    return Constraint(
        key=key,
        value=value,
        strength=ConstraintStrength(strength_raw),
        priority=priority_raw,
        source=source,
        constraint_id=constraint_id or None,
    )


def _resolve_hard_constraints(key: str, constraints: Sequence[Constraint]) -> Constraint:
    unique_values = {constraint.value for constraint in constraints}
    if len(unique_values) > 1:
        raise HardConstraintConflictError(
            HardConstraintConflict(
                key=key,
                constraints=tuple(sorted(constraints, key=_ordering_key)),
            )
        )
    ordered = sorted(constraints, key=_priority_ordering_key)
    return ordered[0]


def _resolve_soft_constraints(
    *,
    key: str,
    soft_constraints: Sequence[Constraint],
    hard_winner: Constraint | None,
) -> dict[str, object]:
    ordered_soft = sorted(soft_constraints, key=_priority_ordering_key)
    conflicts: list[ConstraintConflict] = []
    dropped: list[Constraint] = []

    if hard_winner is not None:
        matching = [constraint for constraint in ordered_soft if constraint.value == hard_winner.value]
        conflicting = [constraint for constraint in ordered_soft if constraint.value != hard_winner.value]
        if conflicting:
            dropped.extend(conflicting)
            conflicts.append(
                ConstraintConflict(
                    code=ConstraintConflictCode.SOFT_CONFLICTS_WITH_HARD,
                    key=key,
                    winner_id=hard_winner.stable_id(),
                    loser_ids=tuple(constraint.stable_id() for constraint in conflicting),
                    detail=f"Hard constraint value '{hard_winner.value}' overrides conflicting soft constraints.",
                )
            )
        if matching:
            winner = matching[0]
            return {"winner": winner, "dropped": dropped, "conflicts": conflicts}
        return {"winner": None, "dropped": dropped, "conflicts": conflicts}

    winner = ordered_soft[0]
    conflicting = [constraint for constraint in ordered_soft[1:] if constraint.value != winner.value]
    duplicates = [constraint for constraint in ordered_soft[1:] if constraint.value == winner.value]

    if conflicting:
        dropped.extend(conflicting)
        tie_detected = any(constraint.priority == winner.priority for constraint in conflicting)
        conflict_code = ConstraintConflictCode.SOFT_TIE_BREAK if tie_detected else ConstraintConflictCode.SOFT_CONFLICT
        conflicts.append(
            ConstraintConflict(
                code=conflict_code,
                key=key,
                winner_id=winner.stable_id(),
                loser_ids=tuple(constraint.stable_id() for constraint in conflicting),
                detail=f"Soft constraint winner selected deterministically: '{winner.value}'.",
            )
        )
    dropped.extend(duplicates)
    return {"winner": winner, "dropped": dropped, "conflicts": conflicts}


def _ordering_key(constraint: Constraint) -> tuple[str, int, str, str]:
    return (constraint.key, -constraint.priority, constraint.value, constraint.stable_id())


def _priority_ordering_key(constraint: Constraint) -> tuple[int, str, str, str]:
    return (-constraint.priority, constraint.value, constraint.source, constraint.stable_id())


__all__ = [
    "Constraint",
    "ConstraintConflict",
    "ConstraintConflictCode",
    "ConstraintResolution",
    "ConstraintStrength",
    "HardConstraintConflict",
    "HardConstraintConflictError",
    "resolve_constraints",
]

