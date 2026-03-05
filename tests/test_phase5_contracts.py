from __future__ import annotations

import hashlib
import json

import pytest

from intent_pipeline.phase5.contracts import (
    OUTPUT_SECTION_ORDER,
    OutputSurfaceCode,
    OutputTerminalStatus,
    Phase5OutputPayload,
    Phase5OutputSurfaces,
)


def _make_phase5_output_payload() -> Phase5OutputPayload:
    return Phase5OutputPayload(
        schema_version="5.0.0",
        phase4_schema_version="4.0.0",
        route_spec_schema_version="3.0.0",
        terminal_status=OutputTerminalStatus.NEEDS_REVIEW,
        terminal_code="FB-005-TERMINAL-NEEDS-REVIEW",
        dominant_rule_id="RULE-OUTPUT-001",
        output_code=OutputSurfaceCode.NEEDS_REVIEW_PATH,
        issues=("issue.beta", "issue.alpha", "issue.alpha"),
        evidence_paths=(
            "fallback.evidence",
            "route_spec.route_profile",
            "fallback.evidence",
        ),
        pipeline_order=("generate_output_surfaces",),
    )


def test_phase5_output_schema_rejects_non_5x_schema_version() -> None:
    assert "OUT-01"
    with pytest.raises(ValueError, match="expected 5.x"):
        Phase5OutputPayload(
            schema_version="4.9.0",
            phase4_schema_version="4.0.0",
            route_spec_schema_version="3.0.0",
            terminal_status=OutputTerminalStatus.USE_PRIMARY,
            terminal_code=None,
            dominant_rule_id="RULE-OUTPUT-001",
            output_code=OutputSurfaceCode.PRIMARY_PATH,
            issues=(),
            evidence_paths=("route_spec.route_profile",),
            pipeline_order=("generate_output_surfaces",),
        )


def test_phase5_output_schema_normalizes_ordered_collections_and_evidence_paths() -> None:
    payload = _make_phase5_output_payload()

    assert "OUT-01"
    assert payload.issues == ("issue.alpha", "issue.beta")
    assert payload.evidence_paths == ("fallback.evidence", "route_spec.route_profile")
    assert payload.pipeline_order == ("generate_output_surfaces",)


def test_phase5_output_schema_canonical_json_is_byte_stable_for_identical_inputs() -> None:
    outputs = [_make_phase5_output_payload().to_json().encode("utf-8") for _ in range(25)]

    assert "OUT-01"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(item).hexdigest() for item in outputs]
    assert len(set(digests)) == 1

    payload = json.loads(outputs[0].decode("utf-8"))
    assert tuple(payload) == tuple(sorted(payload))
    assert payload["issues"] == ["issue.alpha", "issue.beta"]
    assert payload["evidence_paths"] == ["fallback.evidence", "route_spec.route_profile"]


def test_phase5_output_schema_surface_contract_enforces_fixed_section_order() -> None:
    machine_payload = _make_phase5_output_payload()
    surfaces = Phase5OutputSurfaces(
        machine_payload=machine_payload,
        human_text="Summary\n- Terminal status: NEEDS_REVIEW",
    )

    assert "OUT-02"
    assert surfaces.section_order == OUTPUT_SECTION_ORDER
    assert surfaces.human_text.endswith("\n")
    assert surfaces.as_payload()["section_order"] == list(OUTPUT_SECTION_ORDER)

    with pytest.raises(ValueError, match="section_order"):
        Phase5OutputSurfaces(
            machine_payload=machine_payload,
            human_text="Summary\n- Terminal status: NEEDS_REVIEW",
            section_order=("Validation", "Summary", "Mock Execution", "Fallback"),
        )
