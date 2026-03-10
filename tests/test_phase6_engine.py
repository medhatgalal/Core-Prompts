from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.contracts import ApprovalMode, ExecutionApprovalContract, ExecutionDecision, ExecutionDecisionCode, ExecutionRequest
from intent_pipeline.phase6.engine import run_phase6


def _build_request(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> ExecutionRequest:
    phase4_result = run_phase4(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        deepcopy(phase4_policy_contract_payload),
    )
    phase5_result = run_phase5(phase4_result)
    return ExecutionRequest.from_phase_results(
        phase4_result,
        phase5_result,
        policy_schema_version="4.0.0",
        policy_rule_ids=("POLICY-RULE-001",),
    )


def _build_registry(request: ExecutionRequest, *, supports_execution: bool = True) -> dict[str, object]:
    return {
        "schema_version": "6.0.0",
        "entries": [
            {
                "adapter_id": "hermetic-adapter",
                "route_profile": request.route_profile,
                "target_tool_id": request.target_tool_id,
                "capabilities": list(request.required_capabilities),
                "supports_simulation": True,
                "supports_execution": supports_execution,
                "rule_id": "REGISTRY-RULE-001",
            }
        ],
    }


def _build_approval(request: ExecutionRequest, *, mode: ApprovalMode) -> ExecutionApprovalContract:
    return ExecutionApprovalContract(
        schema_version="6.0.0",
        approval_mode=mode,
        approval_id="approval-01",
        approved_by="qa@example.com",
        approved_at="2026-03-09T10:00:00Z",
        expires_at="2026-03-10T10:00:00Z",
        idempotency_key=f"idem-{mode.value.lower()}",
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
    )


def test_missing_approval_returns_needs_review_without_execution(
    tmp_path,
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request = _build_request(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )

    result = run_phase6(
        request,
        None,
        _build_registry(request),
        journal_root=tmp_path,
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )

    assert "PHASE6-ENGINE-01"
    assert result.decision is ExecutionDecision.NEEDS_REVIEW
    assert result.decision_code is ExecutionDecisionCode.APPROVAL_MISSING
    assert result.adapter_id is None
    assert result.produced_artifacts == ()


def test_simulate_only_approval_uses_hermetic_adapter_and_no_side_effects(
    tmp_path,
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request = _build_request(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )
    approval = _build_approval(request, mode=ApprovalMode.SIMULATE_ONLY)

    result = run_phase6(
        request,
        approval,
        _build_registry(request, supports_execution=False),
        journal_root=tmp_path,
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )

    assert "PHASE6-ENGINE-02"
    assert result.decision is ExecutionDecision.SIMULATED
    assert result.decision_code is ExecutionDecisionCode.SIMULATION_COMPLETED
    assert result.adapter_id == "hermetic-adapter"
    assert all(artifact.startswith("phase6:simulate:") for artifact in result.produced_artifacts)
    assert len(list(tmp_path.iterdir())) == 1


def test_unmapped_or_ambiguous_registry_path_blocks_deterministically(
    tmp_path,
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request = _build_request(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )
    approval = _build_approval(request, mode=ApprovalMode.EXECUTE_APPROVED)

    unmapped = run_phase6(
        request,
        approval,
        {"schema_version": "6.0.0", "entries": []},
        journal_root=tmp_path / "unmapped",
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )
    duplicate = run_phase6(
        request,
        approval,
        {
            "schema_version": "6.0.0",
            "entries": [
                {
                    "adapter_id": "adapter-a",
                    "route_profile": request.route_profile,
                    "target_tool_id": request.target_tool_id,
                    "capabilities": list(request.required_capabilities),
                    "supports_simulation": True,
                    "supports_execution": True,
                    "rule_id": "REGISTRY-RULE-001",
                },
                {
                    "adapter_id": "adapter-b",
                    "route_profile": request.route_profile,
                    "target_tool_id": request.target_tool_id,
                    "capabilities": list(request.required_capabilities),
                    "supports_simulation": True,
                    "supports_execution": True,
                    "rule_id": "REGISTRY-RULE-002",
                },
            ],
        },
        journal_root=tmp_path / "duplicate",
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )

    assert "PHASE6-ENGINE-03"
    assert unmapped.decision is ExecutionDecision.NEEDS_REVIEW
    assert unmapped.decision_code is ExecutionDecisionCode.REGISTRY_UNMAPPED
    assert duplicate.decision is ExecutionDecision.NEEDS_REVIEW
    assert duplicate.decision_code is ExecutionDecisionCode.REGISTRY_DUPLICATE


def test_invalid_approval_payload_returns_needs_review_without_exception(
    tmp_path,
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    request = _build_request(
        phase4_route_spec_payload,
        phase4_capability_matrix_payload,
        phase4_policy_contract_payload,
    )

    result = run_phase6(
        request,
        {"schema_version": "6.0.0", "approval_mode": "SIMULATE_ONLY"},
        _build_registry(request),
        journal_root=tmp_path,
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )

    assert "PHASE6-ENGINE-04"
    assert result.decision is ExecutionDecision.NEEDS_REVIEW
    assert result.decision_code is ExecutionDecisionCode.APPROVAL_INVALID
