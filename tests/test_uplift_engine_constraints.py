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


def test_uplift_constraints_04_soft_tie_break_is_deterministic() -> None:
    constraints = [
        {"id": "soft-a", "key": "ordering", "value": "alpha", "strength": "soft", "priority": 5, "source": "phase"},
        {"id": "soft-b", "key": "ordering", "value": "beta", "strength": "soft", "priority": 5, "source": "phase"},
    ]

    resolution = resolve_constraints(constraints)
    payload = resolution.as_payload()

    assert [entry["id"] for entry in payload["applied_soft"]] == ["soft-a"]
    assert [entry["id"] for entry in payload["dropped_soft"]] == ["soft-b"]
    assert payload["conflicts"] == [
        {
            "code": ConstraintConflictCode.SOFT_TIE_BREAK.value,
            "key": "ordering",
            "winner_id": "soft-a",
            "loser_ids": ["soft-b"],
            "detail": "Soft constraint winner selected deterministically: 'alpha'.",
        }
    ]


def test_uplift_constraints_05_conflict_matrix_hard_vs_soft_contradictions() -> None:
    constraints = [
        {"id": "hard-format", "key": "format", "value": "json", "strength": "hard", "priority": 9},
        {"id": "soft-format-a", "key": "format", "value": "xml", "strength": "soft", "priority": 4},
        {"id": "soft-format-b", "key": "format", "value": "json", "strength": "soft", "priority": 3},
        {"id": "soft-order-a", "key": "order", "value": "desc", "strength": "soft", "priority": 2},
        {"id": "soft-order-b", "key": "order", "value": "asc", "strength": "soft", "priority": 2},
    ]

    resolution = resolve_constraints(constraints)
    payload = resolution.as_payload()

    assert [entry["id"] for entry in payload["applied_hard"]] == ["hard-format"]
    assert [entry["id"] for entry in payload["applied_soft"]] == ["soft-format-b", "soft-order-b"]
    assert [entry["id"] for entry in payload["dropped_soft"]] == ["soft-format-a", "soft-order-a"]
    assert [entry["code"] for entry in payload["conflicts"]] == [
        ConstraintConflictCode.SOFT_CONFLICTS_WITH_HARD.value,
        ConstraintConflictCode.SOFT_TIE_BREAK.value,
    ]


def test_uplift_constraints_06_repeated_runs_and_permutations_are_byte_stable() -> None:
    canonical_constraints = [
        {"id": "hard-schema", "key": "schema", "value": "v2", "strength": "hard", "priority": 5},
        {"id": "soft-schema", "key": "schema", "value": "v2", "strength": "soft", "priority": 3},
        {"id": "soft-mode-a", "key": "mode", "value": "safe", "strength": "soft", "priority": 1},
        {"id": "soft-mode-b", "key": "mode", "value": "fast", "strength": "soft", "priority": 1},
    ]
    permuted_constraints = [
        canonical_constraints[3],
        canonical_constraints[0],
        canonical_constraints[2],
        canonical_constraints[1],
    ]

    baseline = resolve_constraints(canonical_constraints).to_json()
    payloads = [resolve_constraints(permuted_constraints).to_json() for _ in range(8)]
    assert payloads == [baseline] * len(payloads)
