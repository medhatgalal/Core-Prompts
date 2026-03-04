"""UPLIFT-CONSTRAINTS deterministic conflict-resolution coverage."""

from __future__ import annotations

import pytest

from intent_pipeline.uplift.constraints import (
    ConstraintConflictCode,
    ConstraintStrength,
    HardConstraintConflictError,
    resolve_constraints,
)


REQUIREMENT_ID = "UPLIFT-CONSTRAINTS"


def test_uplift_constraints_01_hard_conflict_raises_structured_payload() -> None:
    constraints = [
        {"id": "hard-tool-a", "key": "tool", "value": "pytest", "strength": "hard", "priority": 10},
        {"id": "hard-tool-b", "key": "tool", "value": "ruff", "strength": "hard", "priority": 10},
    ]

    with pytest.raises(HardConstraintConflictError) as exc_info:
        resolve_constraints(constraints)

    payload = exc_info.value.conflict.as_payload()
    assert payload["code"] == ConstraintConflictCode.HARD_CONFLICT.value
    assert payload["key"] == "tool"
    assert payload["values"] == ["pytest", "ruff"]
    assert [entry["id"] for entry in payload["constraints"]] == ["hard-tool-a", "hard-tool-b"]


def test_uplift_constraints_02_hard_precedence_over_soft_conflicts() -> None:
    constraints = [
        {"id": "hard-time", "key": "timebox", "value": "strict", "strength": "hard", "priority": 5},
        {"id": "soft-time-1", "key": "timebox", "value": "flex", "strength": "soft", "priority": 7},
        {"id": "soft-time-2", "key": "timebox", "value": "strict", "strength": "soft", "priority": 6},
    ]

    resolution = resolve_constraints(constraints)
    payload = resolution.as_payload()

    assert [entry["id"] for entry in payload["applied_hard"]] == ["hard-time"]
    assert [entry["id"] for entry in payload["applied_soft"]] == ["soft-time-2"]
    assert [entry["id"] for entry in payload["dropped_soft"]] == ["soft-time-1"]
    assert payload["conflicts"] == [
        {
            "code": ConstraintConflictCode.SOFT_CONFLICTS_WITH_HARD.value,
            "key": "timebox",
            "winner_id": "hard-time",
            "loser_ids": ["soft-time-1"],
            "detail": "Hard constraint value 'strict' overrides conflicting soft constraints.",
        }
    ]


def test_uplift_constraints_03_resolution_payload_is_deterministic() -> None:
    constraints = [
        {"id": "soft-priority-1", "key": "order", "value": "alpha", "strength": ConstraintStrength.SOFT.value, "priority": 2},
        {"id": "soft-priority-2", "key": "order", "value": "beta", "strength": ConstraintStrength.SOFT.value, "priority": 1},
        {"id": "hard-schema", "key": "schema_version", "value": "2", "strength": ConstraintStrength.HARD.value, "priority": 1},
    ]

    first = resolve_constraints(constraints)
    second = resolve_constraints(constraints)
    third = resolve_constraints(constraints)

    assert first.to_json() == second.to_json() == third.to_json()

