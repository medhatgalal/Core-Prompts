from __future__ import annotations

import json
from copy import deepcopy

from intent_pipeline.uplift.context_layer import build_context_layer
from intent_pipeline.uplift.intent_layer import derive_intent_layer


def _sample_intent_input() -> str:
    return "\n".join(
        [
            "Primary Objective: Build deterministic context and intent layers",
            "Secondary Objectives: Add stable handoff checks; Preserve field ordering",
            "In Scope: Context Layer, Intent Layer",
            "Out of Scope: Rosetta translation, output generation",
            "Must keep outputs deterministic.",
            "Constraint: deterministic ordering only",
            "Constraint: deterministic ordering only",
        ]
    )


def test_uplift_intent_01_maps_context_to_stable_intent_fields() -> None:
    context = build_context_layer(_sample_intent_input())
    intent = derive_intent_layer(context)

    assert "UPLIFT-INTENT"
    assert list(intent.keys()) == [
        "schema_version",
        "primary_objective",
        "secondary_objectives",
        "in_scope",
        "out_of_scope",
        "quality_constraints",
        "unknowns",
    ]
    assert intent["primary_objective"] == "Build deterministic context and intent layers"
    assert intent["secondary_objectives"] == [
        "Add stable handoff checks",
        "Preserve field ordering",
    ]
    assert intent["in_scope"] == ["Context Layer", "Intent Layer"]
    assert intent["out_of_scope"] == ["Rosetta translation", "output generation"]
    assert "Must keep outputs deterministic." in intent["quality_constraints"]
    assert "deterministic ordering only" in intent["quality_constraints"]


def test_uplift_intent_02_routes_incomplete_evidence_to_unknowns() -> None:
    context = build_context_layer(
        "\n".join(
            [
                "In Scope: Context Layer",
                "Must stay deterministic.",
            ]
        )
    )
    intent = derive_intent_layer(context)

    assert intent["primary_objective"] is None
    assert "primary_objective: missing explicit evidence" in intent["unknowns"]
    assert "secondary_objectives: no explicit secondary objectives found" in intent["unknowns"]
    assert "out_of_scope: missing explicit out-of-scope definition" in intent["unknowns"]


def test_uplift_intent_03_repeated_runs_produce_byte_stable_serialized_output() -> None:
    context = build_context_layer(_sample_intent_input())
    outputs = [
        json.dumps(derive_intent_layer(context), separators=(",", ":"), ensure_ascii=True)
        for _ in range(20)
    ]
    assert len(set(outputs)) == 1


def test_uplift_intent_04_context_to_intent_handoff_is_byte_stable_and_ordered() -> None:
    input_text = _sample_intent_input()
    outputs: list[str] = []
    key_orders: list[list[str]] = []
    for _ in range(20):
        context = build_context_layer(input_text)
        intent = derive_intent_layer(context)
        outputs.append(json.dumps(intent, separators=(",", ":"), ensure_ascii=True))
        key_orders.append(list(intent.keys()))

    assert len(set(outputs)) == 1
    assert len({tuple(order) for order in key_orders}) == 1


def test_uplift_intent_05_intent_derivation_uses_context_artifacts_without_mutation() -> None:
    context = build_context_layer(_sample_intent_input())
    original_context = deepcopy(context)

    intent = derive_intent_layer(context)

    assert context == original_context
    assert intent["schema_version"] == context["schema_version"]
    assert intent["primary_objective"] == "Build deterministic context and intent layers"
    assert "Must keep outputs deterministic." in intent["quality_constraints"]
