from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.authorizer import authorize_execution
from intent_pipeline.phase6.contracts import ApprovalMode, AuthorizationDecision, ExecutionApprovalContract, ExecutionRequest


def _build_phase_results(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
):
    phase4_result = run_phase4(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        deepcopy(phase4_policy_contract_payload),
    )
    phase5_result = run_phase5(phase4_result)
    return phase4_result, phase5_result


def _build_request_and_contract(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
):
    phase4_result, phase5_result = _build_phase_results(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )
    request = ExecutionRequest.from_phase_results(
        phase4_result,
        phase5_result,
        policy_schema_version="4.0.0",
        policy_rule_ids=("POLICY-RULE-001",),
    )
    approval = ExecutionApprovalContract(
        schema_version="6.0.0",
        approval_mode=ApprovalMode.EXECUTE_APPROVED,
        approval_id="approval-01",
        approved_by="qa@example.com",
        approved_at="2026-03-09T10:00:00Z",
        expires_at="2026-03-10T10:00:00Z",
        idempotency_key="idem-01",
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
    )
    registry = {
        "schema_version": "6.0.0",
        "entries": [
            {
                "adapter_id": "hermetic-adapter",
                "route_profile": request.route_profile,
                "target_tool_id": request.target_tool_id,
                "capabilities": list(request.required_capabilities),
                "supports_simulation": True,
                "supports_execution": True,
                "rule_id": "REGISTRY-RULE-001",
            }
        ],
    }
    return request, approval, registry


def test_execute_eligible_requires_phase4_phase5_and_approval_alignment(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request, approval, registry = _build_request_and_contract(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )

    report, entry = authorize_execution(
        request,
        approval,
        registry,
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )

    assert "PHASE6-AUTH-01"
    assert report.decision is AuthorizationDecision.EXECUTION_READY
    assert report.execute_eligible is True
    assert entry is not None
    assert entry.adapter_id == "hermetic-adapter"


def test_authorizer_blocks_mismatched_capabilities_deterministically(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request, approval, registry = _build_request_and_contract(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )
    mismatched = approval.as_payload()
    mismatched["required_capabilities"] = ["cap.read", "cap.execute"]

    report, entry = authorize_execution(
        request,
        mismatched,
        registry,
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )

    assert "PHASE6-AUTH-02"
    assert report.decision is AuthorizationDecision.NEEDS_REVIEW
    assert entry is None
    assert any("required_capabilities" in path for path in report.evidence_paths)
