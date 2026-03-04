from __future__ import annotations

import pytest

from intent_pipeline.routing.contracts import (
    ROUTING_CONTRACT_SCHEMA_VERSION,
    RouteProfile,
    RoutingBoundaryError,
    RoutingBoundaryErrorCode,
    RoutingContract,
    validate_uplift_artifact,
)
from intent_pipeline.routing.signal_bundle import build_signal_bundle
from intent_pipeline.uplift.engine import run_uplift_engine


def _sample_uplift_input() -> str:
    return "\n".join(
        [
            "Primary Objective: compose deterministic routing boundary contracts.",
            "Secondary Objectives: preserve traceability and schema-major guards.",
            "In Scope: schema-major validation, enum closure, signal extraction.",
            "Out of Scope: target validation, execution, output generation.",
            "Must keep schema major deterministic.",
            "Acceptance Criteria: produce deterministic canonical payloads.",
        ]
    )


def _valid_uplift_payload() -> dict[str, object]:
    return run_uplift_engine(_sample_uplift_input()).as_payload()


def test_route_ctx_01_schema_major_rejects_unsupported_input_schema_major() -> None:
    payload = _valid_uplift_payload()
    payload["schema_version"] = "1.9.9"

    with pytest.raises(RoutingBoundaryError) as error_info:
        validate_uplift_artifact(payload)

    assert "ROUTE-CTX-01"
    assert error_info.value.code is RoutingBoundaryErrorCode.UNSUPPORTED_INPUT_SCHEMA
    assert "Expected 2.x" in str(error_info.value)


def test_route_ctx_01_schema_major_rejects_unsupported_routing_schema_major() -> None:
    payload = _valid_uplift_payload()

    with pytest.raises(RoutingBoundaryError) as error_info:
        RoutingContract(
            schema_version="4.0.0",
            uplift_schema_version=str(payload["schema_version"]),
            route_profile=RouteProfile.NEEDS_REVIEW,
        )

    assert "ROUTE-CTX-01"
    assert error_info.value.code is RoutingBoundaryErrorCode.UNSUPPORTED_ROUTING_SCHEMA


def test_route_enum_01_enum_is_closed_and_deterministic() -> None:
    expected = [
        "IMPLEMENTATION",
        "RESEARCH",
        "VALIDATION",
        "NEEDS_REVIEW",
    ]

    assert "ROUTE-ENUM-01"
    assert [profile.value for profile in RouteProfile] == expected


def test_route_ctx_01_required_fields_missing_sections_are_typed_and_sorted() -> None:
    payload = _valid_uplift_payload()
    payload.pop("intent", None)
    payload.pop("constraints", None)

    with pytest.raises(RoutingBoundaryError) as error_info:
        validate_uplift_artifact(payload)

    assert "ROUTE-CTX-01"
    assert error_info.value.code is RoutingBoundaryErrorCode.MISSING_REQUIRED_SECTION
    assert error_info.value.detail == {
        "missing_sections": ["constraints", "intent"],
    }


def test_route_enum_01_routing_contract_serialization_is_canonical() -> None:
    payload = _valid_uplift_payload()
    contract = RoutingContract(
        schema_version=ROUTING_CONTRACT_SCHEMA_VERSION,
        uplift_schema_version=str(payload["schema_version"]),
        route_profile=RouteProfile.RESEARCH,
        rationale="Semantic evidence is exploratory and incomplete.",
        missing_evidence=("intent.primary_objective", "intent.primary_objective"),
    )

    assert contract.as_payload() == {
        "schema_version": "3.0.0",
        "uplift_schema_version": "2.0.0",
        "route_profile": "RESEARCH",
        "rationale": "Semantic evidence is exploratory and incomplete.",
        "missing_evidence": ["intent.primary_objective"],
    }


def test_route_ctx_01_signal_bundle_extracts_routing_signals(
    routing_uplift_contract,
) -> None:
    bundle = build_signal_bundle(routing_uplift_contract)
    payload = bundle.as_payload()

    assert "ROUTE-CTX-01"
    assert payload["schema_version"] == "3.0.0"
    assert payload["uplift_schema_version"] == "2.0.0"
    assert payload["context_schema_version"] == "2.0.0"
    assert payload["primary_objective"] is not None
    assert payload["task_node_ids"]
    assert payload["acceptance_decision"] == "PASS"


def test_route_ctx_01_signal_bundle_normalization_orders_constraints_deterministically(
    routing_uplift_payload: dict[str, object],
) -> None:
    routing_uplift_payload["constraints"] = {
        "applied_hard": [
            {
                "id": "hard-z",
                "key": "zeta",
                "value": "later",
                "strength": "hard",
                "priority": 1,
                "source": "intent.quality_constraints",
            },
            {
                "id": "hard-a",
                "key": "alpha",
                "value": "first",
                "strength": "hard",
                "priority": 100,
                "source": "context.schema_version",
            },
        ],
        "applied_soft": [
            {
                "id": "soft-b",
                "key": "beta",
                "value": "preserve",
                "strength": "soft",
                "priority": 2,
                "source": "intent.quality_constraints",
            },
            {
                "id": "soft-a",
                "key": "alpha",
                "value": "enforce",
                "strength": "soft",
                "priority": 2,
                "source": "intent.quality_constraints",
            },
        ],
        "dropped_soft": [],
        "conflicts": [{"code": "SOFT_CONFLICT"}, {"code": "SOFT_TIE_BREAK"}],
    }
    routing_uplift_payload["intent"] = {
        **routing_uplift_payload["intent"],  # type: ignore[arg-type]
        "quality_constraints": [
            "  Keep deterministic outputs  ",
            "Keep deterministic outputs",
            "No hidden defaults",
        ],
    }

    bundle = build_signal_bundle(routing_uplift_payload)

    assert "normalization"
    assert [item.constraint_id for item in bundle.hard_constraints] == ["hard-a", "hard-z"]
    assert [item.constraint_id for item in bundle.soft_constraints] == ["soft-a", "soft-b"]
    assert bundle.conflict_codes == ("SOFT_CONFLICT", "SOFT_TIE_BREAK")
    assert bundle.quality_constraints == (
        "Keep deterministic outputs",
        "No hidden defaults",
    )


def test_route_ctx_01_signal_bundle_missing_evidence_is_explicit_without_defaults(
    routing_uplift_payload: dict[str, object],
) -> None:
    intent = dict(routing_uplift_payload["intent"])  # type: ignore[arg-type]
    intent.pop("primary_objective", None)
    intent["quality_constraints"] = []
    routing_uplift_payload["intent"] = intent

    task_graph = dict(routing_uplift_payload["task_graph"])  # type: ignore[arg-type]
    task_graph["nodes"] = []
    routing_uplift_payload["task_graph"] = task_graph

    acceptance = dict(routing_uplift_payload["acceptance"])  # type: ignore[arg-type]
    acceptance["decision"] = ""
    acceptance["missing_evidence"] = ["acceptance.criteria"]
    routing_uplift_payload["acceptance"] = acceptance

    bundle = build_signal_bundle(routing_uplift_payload)

    assert "missing_evidence"
    assert bundle.primary_objective is None
    assert bundle.acceptance_decision is None
    assert bundle.task_node_ids == ()
    assert "intent.primary_objective" in bundle.missing_evidence
    assert "intent.quality_constraints" in bundle.missing_evidence
    assert "task_graph.nodes" in bundle.missing_evidence
    assert "acceptance.decision" in bundle.missing_evidence
    assert "acceptance.criteria" in bundle.missing_evidence
