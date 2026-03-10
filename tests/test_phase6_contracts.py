from __future__ import annotations

import hashlib
import json

import pytest

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.contracts import (
    ApprovalMode,
    ExecutionApprovalContract,
    ExecutionDecisionCode,
    ExecutionRequest,
    Phase6ContractError,
    parse_execution_approval_contract,
    parse_execution_request,
)


def _build_phase_results(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
):
    phase4_result = run_phase4(phase4_route_spec_payload, phase4_capability_matrix_payload, phase4_policy_contract_payload)
    phase5_result = run_phase5(phase4_result)
    return phase4_result, phase5_result


def _build_request(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> ExecutionRequest:
    phase4_result, phase5_result = _build_phase_results(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )
    return ExecutionRequest.from_phase_results(
        phase4_result,
        phase5_result,
        policy_schema_version="4.0.0",
        policy_rule_ids=("POLICY-RULE-001", "POLICY-RULE-002"),
    )


def test_approval_contract_requires_exact_execute_binding_fields(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request = _build_request(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )
    invalid_payload = {
        "schema_version": "6.0.0",
        "approval_mode": "EXECUTE_APPROVED",
        "approval_id": "approval-01",
        "approved_by": "qa@example.com",
        "approved_at": "2026-03-09T10:00:00Z",
        "expires_at": "2026-03-10T10:00:00Z",
        "idempotency_key": "idem-01",
        "route_profile": request.route_profile,
        "target_tool_id": request.target_tool_id,
        "dominant_rule_id": request.dominant_rule_id,
        "required_capabilities": list(request.required_capabilities),
        "policy_schema_version": request.policy_schema_version,
        "policy_rule_ids": [],
    }

    assert "PHASE6-CONTRACT-01"
    with pytest.raises(Phase6ContractError) as exc_info:
        parse_execution_approval_contract(invalid_payload)
    assert exc_info.value.code is ExecutionDecisionCode.APPROVAL_INVALID


def test_phase6_request_from_phase_results_is_canonical_and_byte_stable(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    outputs = [
        _build_request(
            phase4_route_spec_payload,
            phase4_capability_matrix_payload,
            phase4_policy_contract_payload,
        ).to_json().encode("utf-8")
        for _ in range(20)
    ]

    assert "PHASE6-CONTRACT-02"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(item).hexdigest() for item in outputs]
    assert len(set(digests)) == 1
    payload = json.loads(outputs[0].decode("utf-8"))
    assert tuple(payload) == tuple(sorted(payload))
    assert payload["required_capabilities"] == sorted(payload["required_capabilities"])


def test_phase6_contract_round_trip_preserves_mode_and_policy_ids(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request = _build_request(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )
    contract = ExecutionApprovalContract(
        schema_version="6.0.0",
        approval_mode=ApprovalMode.SIMULATE_ONLY,
        approval_id="approval-02",
        approved_by="qa@example.com",
        approved_at="2026-03-09T10:00:00Z",
        expires_at="2026-03-10T10:00:00Z",
        idempotency_key="idem-02",
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
    )

    assert "PHASE6-CONTRACT-03"
    reparsed = parse_execution_approval_contract(contract.as_payload())
    assert reparsed.approval_mode is ApprovalMode.SIMULATE_ONLY
    assert reparsed.policy_rule_ids == request.policy_rule_ids


def test_phase6_request_rejects_non_boolean_validation_can_proceed_payload() -> None:
    payload = {
        "schema_version": "6.0.0",
        "phase4_schema_version": "4.0.0",
        "phase5_schema_version": "5.0.0",
        "route_spec_schema_version": "4.0.0",
        "validation_decision": "PASS",
        "validation_can_proceed": "false",
        "fallback_decision": "USE_PRIMARY",
        "phase5_terminal_status": "USE_PRIMARY",
        "route_profile": "IMPLEMENTATION",
        "target_tool_id": "tool-implementation",
        "dominant_rule_id": "RULE-1",
        "required_capabilities": ["cap.read"],
        "policy_schema_version": "4.0.0",
        "policy_rule_ids": ["POLICY-RULE-001"],
    }

    assert "PHASE6-CONTRACT-04"
    with pytest.raises(Phase6ContractError) as exc_info:
        parse_execution_request(payload)
    assert exc_info.value.code is ExecutionDecisionCode.APPROVAL_INVALID
    assert exc_info.value.evidence_path == "execution_request.validation_can_proceed"
