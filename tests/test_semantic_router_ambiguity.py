from __future__ import annotations

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


def test_route_unk_01_missing_evidence_yields_sorted_explicit_review_payload() -> None:
    signals = _bundle(
        missing_evidence=(
            "task_graph.nodes",
            "acceptance.criteria",
            "intent.primary_objective",
            "task_graph.nodes",
        )
    )

    result = select_route(signals)

    assert "ROUTE-UNK-01"
    assert result.decision is RouteDecision.NEEDS_REVIEW
    assert result.route_profile is RouteProfile.NEEDS_REVIEW
    assert result.dominant_rule_id == "ROUTE-UNK-001"
    assert result.missing_evidence == (
        "acceptance.criteria",
        "intent.primary_objective",
        "task_graph.nodes",
    )
    assert result.ambiguity_reasons == ()


def test_route_unk_01_conflicting_hard_evidence_yields_deterministic_needs_review() -> None:
    signals = _bundle(
        hard_constraints=(
            _hard_route("hard-impl", "IMPLEMENTATION"),
            _hard_route("hard-research", "RESEARCH"),
        ),
        conflict_codes=("SOFT_CONFLICT", "HARD_CONFLICT"),
    )

    result = select_route(signals)

    assert "ROUTE-UNK-01"
    assert result.decision is RouteDecision.NEEDS_REVIEW
    assert result.route_profile is RouteProfile.NEEDS_REVIEW
    assert result.dominant_rule_id == "ROUTE-UNK-002"
    assert result.missing_evidence == ()
    assert result.ambiguity_reasons == (
        "hard_constraint_conflict_code:HARD_CONFLICT;hard_constraints_conflicting_profiles:IMPLEMENTATION,RESEARCH",
    )


def test_route_unk_01_non_decisive_signals_return_explicit_needs_review() -> None:
    result = select_route(_bundle())

    assert "ROUTE-UNK-01"
    assert result.decision is RouteDecision.NEEDS_REVIEW
    assert result.route_profile is RouteProfile.NEEDS_REVIEW
    assert result.dominant_rule_id == "ROUTE-UNK-003"
    assert result.missing_evidence == ()
    assert result.ambiguity_reasons == ("no_decisive_route_after_precedence",)


def test_route_unk_01_payload_shape_is_canonical_and_roleplay_free() -> None:
    result = select_route(_bundle(missing_evidence=("intent.primary_objective",)))
    payload = result.as_payload()

    assert list(payload.keys()) == [
        "decision",
        "route_profile",
        "dominant_layer",
        "dominant_rule_id",
        "applied_rule_ids",
        "missing_evidence",
        "ambiguity_reasons",
    ]
    forbidden_fields = {
        "assistant_message",
        "chat_response",
        "conversation",
        "dialogue",
        "roleplay",
        "response_text",
    }
    assert forbidden_fields.isdisjoint(payload)


def test_route_unk_01_repeated_runs_keep_review_arrays_and_rules_stable() -> None:
    signals = _bundle(
        hard_constraints=(
            _hard_route("hard-impl", "IMPLEMENTATION"),
            _hard_route("hard-research", "RESEARCH"),
        ),
        conflict_codes=("HARD_CONFLICT",),
    )

    outputs = [select_route(signals).to_json() for _ in range(25)]
    assert outputs == [outputs[0]] * len(outputs)

    decisions = [select_route(signals) for _ in range(25)]
    assert {decision.dominant_rule_id for decision in decisions} == {"ROUTE-UNK-002"}
    assert {decision.ambiguity_reasons for decision in decisions} == {
        (
            "hard_constraint_conflict_code:HARD_CONFLICT;hard_constraints_conflicting_profiles:IMPLEMENTATION,RESEARCH",
        )
    }
