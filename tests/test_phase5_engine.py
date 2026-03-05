from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.contracts import (
    OutputTerminalStatus,
    RuntimeDependencyAggregateStatus,
    RuntimeDependencyClassification,
    RuntimeDependencyReasonCode,
)
from intent_pipeline.phase5.engine import generate_help_response
from intent_pipeline.phase5.help import resolve_help_response
from intent_pipeline.phase5 import help as phase5_help_module
from intent_pipeline.phase5.output_generator import generate_output_surfaces
from intent_pipeline.phase5 import output_generator as phase5_output_generator
from intent_pipeline.phase5.runtime_checks import run_runtime_dependency_checks
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


def _runtime_specs(*, required_missing: bool, optional_missing: bool) -> tuple[dict[str, str], ...]:
    return (
        {
            "dependency_id": "dep.required.json",
            "classification": "required",
            "probe_type": "python_module",
            "target": "json",
        },
        {
            "dependency_id": "dep.required.missing" if required_missing else "dep.required.pathlib",
            "classification": "required",
            "probe_type": "python_module",
            "target": "__phase5_required_missing__" if required_missing else "pathlib",
        },
        {
            "dependency_id": "dep.optional.missing" if optional_missing else "dep.optional.tomllib",
            "classification": "optional",
            "probe_type": "python_module",
            "target": "__phase5_optional_missing__" if optional_missing else "tomllib",
        },
    )


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


def test_phase5_help_template_evidence_paths_are_deterministic_for_identical_input() -> None:
    phase4_result = _build_phase4_result(enforce_blocking=True)
    surfaces = generate_output_surfaces(phase4_result)
    rendered = [resolve_help_response(surfaces).to_json() for _ in range(20)]

    assert "HELP-02"
    assert rendered == [rendered[0]] * len(rendered)
    digests = [hashlib.sha256(item.encode("utf-8")).hexdigest() for item in rendered]
    assert len(set(digests)) == 1


def test_phase5_help_template_evidence_paths_use_fixed_message_pattern() -> None:
    phase4_result = _build_phase4_result(enforce_blocking=True)
    surfaces = generate_output_surfaces(phase4_result)
    response = resolve_help_response(surfaces)

    assert "HELP-02"
    assert response.message.startswith("Failure state is NEEDS_REVIEW.")
    assert "Evidence paths:" in response.message
    assert response.evidence_paths == tuple(sorted(response.evidence_paths))
    assert "phase5.help.topic::failure_explanation" in response.evidence_paths
    assert "phase5.help.code::HELP-201-FAILURE-BLOCKING-STATUS" in response.evidence_paths


def test_phase5_help_non_executing_remediation_actions_remain_advisory_only() -> None:
    phase4_result = _build_phase4_result(enforce_blocking=False)
    response = generate_help_response(phase4_result)

    assert "HELP-03"
    forbidden_markers = ("run ", "install ", "pip ", "npm ", "curl ", "wget ", "execute ")
    for action in response.actions:
        normalized = action.casefold()
        assert not any(marker in normalized for marker in forbidden_markers)

    phase4_snapshot = phase4_result.to_json()
    assert response.terminal_status.value == phase4_result.fallback.decision.value
    assert phase4_result.to_json() == phase4_snapshot


def test_phase5_help_non_executing_remediation_guard_rejects_execution_steps(monkeypatch) -> None:
    phase4_result = _build_phase4_result(enforce_blocking=False)
    surfaces = generate_output_surfaces(phase4_result)

    monkeypatch.setitem(
        phase5_help_module._ACTIONS_BY_CODE,
        phase5_help_module.HelpCode.USAGE_STATUS_OVERVIEW,
        ("Run pip install forbidden-package",),
    )

    assert "HELP-03"
    with pytest.raises(ValueError, match="non-executing"):
        resolve_help_response(surfaces)


def test_phase5_runtime_required_optional_missing_required_is_blocking() -> None:
    report = run_runtime_dependency_checks(
        _runtime_specs(required_missing=True, optional_missing=True)
    )

    assert "RUNTIME-02"
    assert report.aggregate_status is RuntimeDependencyAggregateStatus.BLOCKING
    assert tuple(check.dependency_id for check in report.checks) == tuple(
        sorted(check.dependency_id for check in report.checks)
    )
    required_missing = [
        check
        for check in report.checks
        if check.classification is RuntimeDependencyClassification.REQUIRED and check.status.value == "MISSING"
    ]
    optional_missing = [
        check
        for check in report.checks
        if check.classification is RuntimeDependencyClassification.OPTIONAL and check.status.value == "MISSING"
    ]
    assert required_missing
    assert optional_missing
    assert all(check.reason_code is RuntimeDependencyReasonCode.REQUIRED_MISSING for check in required_missing)
    assert all(check.reason_code is RuntimeDependencyReasonCode.OPTIONAL_MISSING for check in optional_missing)


def test_phase5_runtime_required_optional_missing_optional_is_degraded() -> None:
    report = run_runtime_dependency_checks(
        _runtime_specs(required_missing=False, optional_missing=True)
    )

    assert "RUNTIME-03"
    assert report.aggregate_status is RuntimeDependencyAggregateStatus.DEGRADED
    required_missing = [
        check
        for check in report.checks
        if check.classification is RuntimeDependencyClassification.REQUIRED and check.status.value == "MISSING"
    ]
    optional_missing = [
        check
        for check in report.checks
        if check.classification is RuntimeDependencyClassification.OPTIONAL and check.status.value == "MISSING"
    ]
    assert required_missing == []
    assert optional_missing
    assert all(check.reason_code is RuntimeDependencyReasonCode.OPTIONAL_MISSING for check in optional_missing)
