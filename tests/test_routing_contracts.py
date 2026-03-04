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
