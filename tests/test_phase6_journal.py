from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.contracts import ApprovalMode, ExecutionApprovalContract, ExecutionDecisionCode, ExecutionRequest
from intent_pipeline.phase6.engine import run_phase6
from intent_pipeline.phase6.journal import ExecutionJournal


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


def _build_registry(request: ExecutionRequest) -> dict[str, object]:
    return {
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


def _build_approval(request: ExecutionRequest, *, key: str) -> ExecutionApprovalContract:
    return ExecutionApprovalContract(
        schema_version="6.0.0",
        approval_mode=ApprovalMode.EXECUTE_APPROVED,
        approval_id="approval-01",
        approved_by="qa@example.com",
        approved_at="2026-03-09T10:00:00Z",
        expires_at="2026-03-10T10:00:00Z",
        idempotency_key=key,
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
    )


def test_journal_records_blocked_attempts_with_canonical_evidence(
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

    journal = ExecutionJournal(tmp_path)
    lookup = journal.lookup("missing-approval")
    payload = json.loads((tmp_path / lookup.relative_path).read_text(encoding="utf-8").splitlines()[0])

    assert "PHASE6-JOURNAL-01"
    assert result.decision_code is ExecutionDecisionCode.APPROVAL_MISSING
    assert payload["decision"] == "NEEDS_REVIEW"
    assert payload["evidence_paths"] == sorted(payload["evidence_paths"])


def test_journal_prevents_duplicate_approved_attempts(
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
    approval = _build_approval(request, key="idem-shared")
    registry = _build_registry(request)

    first = run_phase6(
        request,
        approval,
        registry,
        journal_root=tmp_path,
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )
    second = run_phase6(
        request,
        approval,
        registry,
        journal_root=tmp_path,
        now=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
    )

    journal = ExecutionJournal(tmp_path)
    lookup = journal.lookup("idem-shared")

    assert "PHASE6-JOURNAL-02"
    assert first.decision_code is ExecutionDecisionCode.EXECUTION_COMPLETED
    assert second.decision_code is ExecutionDecisionCode.IDEMPOTENT_REPLAY
    assert second.replayed_from_journal is True
    assert len(lookup.records) == 1
