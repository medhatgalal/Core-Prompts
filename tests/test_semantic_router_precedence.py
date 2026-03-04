from __future__ import annotations

import pytest

from intent_pipeline.routing.contracts import RouteDecision, RouteProfile
from intent_pipeline.routing.semantic_router import select_route
from intent_pipeline.routing.signal_bundle import ConstraintSignal, SignalBundle


def _bundle(**overrides: object) -> SignalBundle:
    payload: dict[str, object] = {
        "schema_version": "3.0.0",
        "uplift_schema_version": "2.0.0",
        "context_schema_version": "2.0.0",
        "primary_objective": None,
        "in_scope": (),
        "out_of_scope": (),
        "quality_constraints": (),
        "intent_unknowns": (),
        "hard_constraints": (),
        "soft_constraints": (),
        "dropped_soft_constraints": (),
        "conflict_codes": (),
        "task_node_ids": (),
        "constrained_task_ids": (),
        "acceptance_decision": "PASS",
        "acceptance_failed_hard_criteria": (),
        "acceptance_missing_evidence": (),
        "acceptance_criterion_ids": (),
        "missing_evidence": (),
    }
    payload.update(overrides)
    return SignalBundle(**payload)


def _hard_route(route_id: str, profile: str) -> ConstraintSignal:
    return ConstraintSignal(
        constraint_id=route_id,
        key="route_profile",
        value=profile,
        strength="hard",
        priority=100,
        source="constraints.applied_hard",
    )


@pytest.mark.parametrize(
    ("signals", "expected_profile", "expected_layer", "expected_rule_id"),
    [
        (
            _bundle(
                hard_constraints=(_hard_route("hard-impl", "IMPLEMENTATION"),),
                primary_objective="research platform risks",
                task_node_ids=("validate-suite-01",),
                acceptance_criterion_ids=("validation-checklist",),
            ),
            RouteProfile.IMPLEMENTATION,
            "hard",
            "ROUTE-HARD-001",
        ),
        (
            _bundle(
                primary_objective="research fallback behavior and investigate ambiguity",
                task_node_ids=("implement-core-module-01",),
                acceptance_criterion_ids=("validation-checklist",),
            ),
            RouteProfile.RESEARCH,
            "intent",
            "ROUTE-INTENT-001",
        ),
        (
            _bundle(
                task_node_ids=("validate-suite-01",),
                constrained_task_ids=("test-acceptance-02",),
                acceptance_criterion_ids=("build-release-readiness",),
            ),
            RouteProfile.VALIDATION,
            "task_graph",
            "ROUTE-TASK-001",
        ),
        (
            _bundle(
                acceptance_criterion_ids=("implement-core-feature",),
            ),
            RouteProfile.IMPLEMENTATION,
            "acceptance",
            "ROUTE-ACCEPT-001",
        ),
    ],
)
def test_route_prec_01_precedence_matrix_is_fixed(
    signals: SignalBundle,
    expected_profile: RouteProfile,
    expected_layer: str,
    expected_rule_id: str,
) -> None:
    result = select_route(signals)

    assert "ROUTE-PREC-01"
    assert result.decision is RouteDecision.PASS_ROUTE
    assert result.route_profile is expected_profile
    assert result.dominant_layer == expected_layer
    assert result.dominant_rule_id == expected_rule_id
    assert result.missing_evidence == ()
    assert result.ambiguity_reasons == ()


def test_route_prec_01_acceptance_can_block_but_not_override_higher_layer() -> None:
    signals = _bundle(
        hard_constraints=(_hard_route("hard-impl", "IMPLEMENTATION"),),
        acceptance_decision="FAIL",
        acceptance_failed_hard_criteria=("hard-context-schema",),
    )

    result = select_route(signals)

    assert "ROUTE-PREC-01"
    assert result.decision is RouteDecision.NEEDS_REVIEW
    assert result.route_profile is RouteProfile.NEEDS_REVIEW
    assert result.dominant_rule_id == "ROUTE-ACCEPT-900"
    assert result.ambiguity_reasons == ("acceptance_failed_hard_criteria:hard-context-schema",)
