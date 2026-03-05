from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.contracts import OutputTerminalStatus
from intent_pipeline.phase5.output_generator import generate_output_surfaces
from intent_pipeline.phase5 import output_generator as phase5_output_generator
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine


def _phase5_input_text() -> str:
    return "\n".join(
        [
            "Primary Objective: render deterministic output surfaces from phase4 artifacts.",
            "Secondary Objectives: preserve typed statuses and canonical serialization.",
            "In Scope: machine payload + human output section ordering.",
            "Out of Scope: help responder and runtime dependency checks.",
            "Must keep deterministic fixed template output.",
            "Acceptance Criteria: identical inputs produce byte-stable output surfaces.",
        ]
    )


def _phase5_phase4_payloads(*, enforce_blocking: bool) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    uplift = run_uplift_engine(_phase5_input_text())
    route_spec = run_semantic_routing(uplift).route_spec.as_payload()
    route_profile = str(route_spec["route_profile"])
    tool_id = f"tool-{route_profile.lower()}"

    capability_matrix = {
        "schema_version": "4.0.0",
        "tools": [
            {
                "tool_id": tool_id,
                "supported_route_profiles": [route_profile],
                "capabilities": ["cap.read", "cap.write"],
            }
        ],
    }
    policy_contract: dict[str, object] = {
        "schema_version": "4.0.0",
        "route_to_tool": [{"route_profile": route_profile, "tool_id": tool_id}],
        "required_capabilities": [{"route_profile": route_profile, "capabilities": ["cap.read", "cap.write"]}],
        "blocked_dominant_rule_ids": [],
        "allowed_route_decisions": ["PASS_ROUTE"],
    }
    if enforce_blocking:
        policy_contract["required_capabilities"] = [
            {
                "route_profile": route_profile,
                "capabilities": ["cap.read", "cap.write", "cap.execute"],
            }
        ]
        policy_contract["allowed_route_decisions"] = ["NEEDS_REVIEW"]
        policy_contract["blocked_dominant_rule_ids"] = [str(route_spec["dominant_rule_id"])]

    return route_spec, capability_matrix, policy_contract


def _build_phase4_result(*, enforce_blocking: bool):
    route_spec, capability_matrix, policy_contract = _phase5_phase4_payloads(enforce_blocking=enforce_blocking)
    return run_phase4(deepcopy(route_spec), deepcopy(capability_matrix), deepcopy(policy_contract))


def test_phase5_output_fixed_section_order_human_template_is_deterministic() -> None:
    phase4_result = _build_phase4_result(enforce_blocking=False)
    rendered = [generate_output_surfaces(phase4_result).human_text for _ in range(15)]

    assert "OUT-02"
    assert rendered == [rendered[0]] * len(rendered)
    headers = [line for line in rendered[0].splitlines() if line and not line.startswith("-")]
    assert headers == ["Summary", "Validation", "Mock Execution", "Fallback"]


def test_phase5_output_fixed_section_order_machine_payload_is_canonical() -> None:
    phase4_result = _build_phase4_result(enforce_blocking=True)
    payload_bytes = [generate_output_surfaces(phase4_result).machine_payload.to_json().encode("utf-8") for _ in range(20)]

    assert "OUT-02"
    assert len(set(payload_bytes)) == 1
    digests = [hashlib.sha256(item).hexdigest() for item in payload_bytes]
    assert len(set(digests)) == 1

    payload = json.loads(payload_bytes[0].decode("utf-8"))
    assert tuple(payload) == tuple(sorted(payload))
    assert payload["pipeline_order"] == ["generate_output_surfaces"]
    assert payload["issues"] == sorted(payload["issues"])


def test_phase5_preserve_needs_review_terminal_semantics_unchanged() -> None:
    phase4_result = _build_phase4_result(enforce_blocking=True)
    phase4_snapshot = phase4_result.to_json()

    surfaces = generate_output_surfaces(phase4_result)

    assert "OUT-03"
    assert phase4_result.fallback.decision.value == "NEEDS_REVIEW"
    assert surfaces.machine_payload.terminal_status.value == "NEEDS_REVIEW"
    assert surfaces.machine_payload.terminal_code == "FB-005-TERMINAL-NEEDS-REVIEW"
    assert phase4_result.to_json() == phase4_snapshot


def test_phase5_preserve_needs_review_guard_rejects_status_rewrite(monkeypatch) -> None:
    phase4_result = _build_phase4_result(enforce_blocking=True)

    monkeypatch.setattr(
        phase5_output_generator,
        "_terminal_status_from_phase4",
        lambda _phase4_result: OutputTerminalStatus.USE_PRIMARY,
    )

    assert "OUT-03"
    with pytest.raises(ValueError, match="preserve Phase4 terminal status"):
        generate_output_surfaces(phase4_result)
