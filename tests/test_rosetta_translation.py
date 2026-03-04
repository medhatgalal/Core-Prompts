from __future__ import annotations

from dataclasses import replace

import pytest

from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.routing.rosetta import (
    RosettaTranslationError,
    RosettaTranslationErrorCode,
    translate_to_route_spec,
)
from intent_pipeline.routing.semantic_router import select_route
from intent_pipeline.routing.signal_bundle import SignalBundle, build_signal_bundle


def _signal_bundle_with(base: SignalBundle, **overrides: object) -> SignalBundle:
    return replace(base, **overrides)


def test_rosetta_01_route_spec_schema_and_payload_shape_is_canonical(
    routing_uplift_payload: dict[str, object],
) -> None:
    bundle = build_signal_bundle(routing_uplift_payload)
    selection = select_route(bundle)

    route_spec = translate_to_route_spec(selection, bundle, routing_uplift_payload)
    payload = route_spec.as_payload()

    assert "ROSETTA-01"
    assert payload["schema_version"] == "3.0.0"
    assert payload["decision"] == selection.decision.value
    assert payload["route_profile"] == selection.route_profile.value
    assert payload["dominant_signal"] == selection.dominant_layer
    assert payload["dominant_rule_id"] == selection.dominant_rule_id
    assert payload["applied_rule_ids"]
    assert payload["evidence_links"]

    assert list(payload.keys()) == [
        "schema_version",
        "decision",
        "route_profile",
        "dominant_signal",
        "dominant_rule_id",
        "applied_rule_ids",
        "task_focus_ids",
        "evidence_links",
        "acceptance_gate",
        "missing_evidence",
        "ambiguity_reasons",
    ]


def test_rosetta_02_task_focus_ids_follow_constrained_task_subset(
    routing_uplift_payload: dict[str, object],
) -> None:
    base_bundle = build_signal_bundle(routing_uplift_payload)
    focused_bundle = _signal_bundle_with(
        base_bundle,
        constrained_task_ids=(
            "constraint-resolution",
            "scope-01-routing-contracts",
            "constraint-resolution",
        ),
    )
    selection = select_route(focused_bundle)

    route_spec = translate_to_route_spec(selection, focused_bundle, routing_uplift_payload)

    assert "ROSETTA-02"
    assert route_spec.task_focus_ids == (
        "constraint-resolution",
        "scope-01-routing-contracts",
    )


def test_rosetta_02_task_focus_ids_reject_unknown_graph_node(
    routing_uplift_payload: dict[str, object],
) -> None:
    base_bundle = build_signal_bundle(routing_uplift_payload)
    invalid_bundle = _signal_bundle_with(
        base_bundle,
        constrained_task_ids=("constraint-resolution", "ghost-node"),
    )
    selection = select_route(invalid_bundle)

    with pytest.raises(RosettaTranslationError) as error_info:
        translate_to_route_spec(selection, invalid_bundle, routing_uplift_payload)

    assert "ROSETTA-02"
    assert error_info.value.code is RosettaTranslationErrorCode.TASK_FOCUS_OUTSIDE_TASK_GRAPH
    assert error_info.value.detail["invalid_ids"] == ["ghost-node"]


def test_rosetta_02_linkage_evidence_and_provenance_remain_consistent(
    routing_uplift_payload: dict[str, object],
) -> None:
    bundle = build_signal_bundle(routing_uplift_payload)
    selection = select_route(bundle)

    route_spec = translate_to_route_spec(selection, bundle, routing_uplift_payload)
    payload = route_spec.as_payload()

    assert "ROSETTA-02"
    assert payload["dominant_rule_id"] in payload["applied_rule_ids"]
    assert payload["task_focus_ids"]
    evidence_task_ids = {link["task_id"] for link in payload["evidence_links"]}
    assert evidence_task_ids.issubset(set(payload["task_focus_ids"]))


def test_rosetta_01_schema_serialization_is_byte_stable(
    routing_uplift_payload: dict[str, object],
) -> None:
    bundle = build_signal_bundle(routing_uplift_payload)
    selection = select_route(bundle)

    outputs = [translate_to_route_spec(selection, bundle, routing_uplift_payload).to_json() for _ in range(20)]

    assert "ROSETTA-01"
    assert outputs == [outputs[0]] * len(outputs)


def test_rosetta_01_engine_orchestration_emits_route_spec_contract(
    routing_uplift_payload: dict[str, object],
) -> None:
    result = run_semantic_routing(routing_uplift_payload)
    payload = result.as_payload()

    assert "ROSETTA-01"
    assert payload["schema_version"] == "3.0.0"
    assert payload["uplift_schema_version"] == "2.0.0"
    assert payload["route_spec"]["schema_version"] == "3.0.0"
    assert payload["route_spec"]["dominant_rule_id"] == payload["route_selection"]["dominant_rule_id"]
    assert payload["route_spec"]["task_focus_ids"]


def test_rosetta_01_engine_orchestration_is_byte_stable(
    routing_uplift_payload: dict[str, object],
) -> None:
    outputs = [run_semantic_routing(routing_uplift_payload).to_json() for _ in range(20)]

    assert "ROSETTA-01"
    assert outputs == [outputs[0]] * len(outputs)
