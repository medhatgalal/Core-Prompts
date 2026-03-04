from __future__ import annotations

import json

from intent_pipeline.uplift.context_layer import build_context_layer


def _sample_context_input() -> str:
    return "\n".join(
        [
            "Primary Objective: Build deterministic context and intent layers.",
            "In Scope: Context Layer, Intent Layer",
            "Out of Scope: Rosetta translation",
            "Must preserve explicit and inferred boundaries.",
            "Acceptance Criteria: outputs remain byte-stable for identical inputs.",
            "Objective should be deterministic and testable.",
        ]
    )


def test_uplift_ctx_01_layer_shape_is_deterministic_and_schema_versioned() -> None:
    context = build_context_layer(_sample_context_input(), schema_version="2.1.0")

    assert "UPLIFT-CTX"
    assert list(context.keys()) == [
        "schema_version",
        "source",
        "normalized_facts",
        "inferred_facts",
        "candidate_constraints",
        "acceptance_inputs",
    ]
    assert context["schema_version"] == "2.1.0"
    assert set(context["source"].keys()) == {"content_sha256", "line_count", "content_type"}
    assert context["source"]["line_count"] == 6


def test_uplift_ctx_02_inferred_entries_are_marked_and_do_not_override_explicit() -> None:
    context = build_context_layer(_sample_context_input())

    explicit_keys = [fact["key"] for fact in context["normalized_facts"]]
    inferred_keys = [fact["key"] for fact in context["inferred_facts"]]

    assert "primary_objective" in explicit_keys
    assert "primary_objective" not in inferred_keys
    assert all(fact["inferred"] is True for fact in context["inferred_facts"])
    assert all(fact["source"] == "inferred" for fact in context["inferred_facts"])


def test_uplift_ctx_03_repeated_runs_produce_byte_stable_serialized_output() -> None:
    input_text = _sample_context_input()
    outputs = [
        json.dumps(build_context_layer(input_text), separators=(",", ":"), ensure_ascii=True)
        for _ in range(20)
    ]
    assert len(set(outputs)) == 1
