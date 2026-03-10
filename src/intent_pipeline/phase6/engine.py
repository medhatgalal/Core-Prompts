"""Phase-6 simulate-first controlled execution engine."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from intent_pipeline.phase6.authorizer import authorize_execution
from intent_pipeline.phase6.contracts import (
    ApprovalMode,
    ExecutionApprovalContract,
    ExecutionDecision,
    ExecutionDecisionCode,
    ExecutionJournalRecord,
    ExecutionRequest,
    ExecutionResult,
    PHASE6_RESULT_SCHEMA_VERSION,
    Phase6ContractError,
    build_request_envelope_sha256,
    parse_execution_approval_contract,
    parse_execution_request,
)
from intent_pipeline.phase6.executor_registry import ExecutorRegistry, ExecutorRegistryEntry
from intent_pipeline.phase6.journal import ExecutionJournal


def run_phase6(
    execution_request: ExecutionRequest | Mapping[str, Any],
    approval_contract: ExecutionApprovalContract | Mapping[str, Any] | None,
    registry: ExecutorRegistry | Mapping[str, Any],
    *,
    journal_root: Path | str = ".phase6-journal",
    now: datetime | None = None,
) -> ExecutionResult:
    request = parse_execution_request(execution_request)
    envelope_sha256 = build_request_envelope_sha256(request)
    journal = ExecutionJournal(journal_root)

    if approval_contract is not None:
        try:
            approval = parse_execution_approval_contract(approval_contract)
        except Phase6ContractError as error:
            journal_record = ExecutionJournalRecord(
                schema_version="6.0.0",
                decision=ExecutionDecision.NEEDS_REVIEW,
                decision_code=error.code,
                approval_mode=None,
                approval_id=None,
                idempotency_key="invalid-approval",
                policy_schema_version=request.policy_schema_version,
                policy_rule_ids=request.policy_rule_ids,
                route_profile=request.route_profile,
                target_tool_id=request.target_tool_id,
                dominant_rule_id=request.dominant_rule_id,
                evidence_paths=(error.evidence_path or "approval_contract",),
                envelope_sha256=envelope_sha256,
            )
            journal_path = journal.append(journal_record)
            return ExecutionResult(
                schema_version=PHASE6_RESULT_SCHEMA_VERSION,
                request_schema_version=request.schema_version,
                decision=ExecutionDecision.NEEDS_REVIEW,
                decision_code=error.code,
                approval_mode=None,
                approval_id=None,
                idempotency_key="invalid-approval",
                route_profile=request.route_profile,
                target_tool_id=request.target_tool_id,
                dominant_rule_id=request.dominant_rule_id,
                adapter_id=None,
                evidence_paths=(error.evidence_path or "approval_contract",),
                applied_rule_ids=("PHASE6-RULE-000-APPROVAL-PARSE", request.dominant_rule_id),
                envelope_sha256=envelope_sha256,
                journal_path=journal_path,
                produced_artifacts=(),
            )
        replay_record = journal.already_recorded(approval.idempotency_key, envelope_sha256)
        if replay_record is not None:
            return ExecutionResult(
                schema_version=PHASE6_RESULT_SCHEMA_VERSION,
                request_schema_version=request.schema_version,
                decision=replay_record.decision,
                decision_code=ExecutionDecisionCode.IDEMPOTENT_REPLAY,
                approval_mode=replay_record.approval_mode,
                approval_id=replay_record.approval_id,
                idempotency_key=replay_record.idempotency_key,
                route_profile=replay_record.route_profile,
                target_tool_id=replay_record.target_tool_id,
                dominant_rule_id=replay_record.dominant_rule_id,
                adapter_id=replay_record.adapter_id,
                evidence_paths=(*replay_record.evidence_paths, "phase6.journal.replay"),
                applied_rule_ids=("PHASE6-RULE-004-IDEMPOTENCY", request.dominant_rule_id),
                envelope_sha256=replay_record.envelope_sha256,
                journal_path=journal.relative_path_for(replay_record.idempotency_key),
                produced_artifacts=replay_record.produced_artifacts,
                replayed_from_journal=True,
            )
    else:
        approval = None

    authorization, registry_entry = authorize_execution(request, approval_contract, registry, now=now)
    if authorization.decision.value == "NEEDS_REVIEW":
        idempotency_key = approval.idempotency_key if approval is not None else "missing-approval"
        approval_id = approval.approval_id if approval is not None else None
        approval_mode = approval.approval_mode if approval is not None else None
        journal_record = ExecutionJournalRecord(
            schema_version="6.0.0",
            decision=ExecutionDecision.NEEDS_REVIEW,
            decision_code=authorization.decision_code,
            approval_mode=approval_mode,
            approval_id=approval_id,
            idempotency_key=idempotency_key,
            policy_schema_version=request.policy_schema_version,
            policy_rule_ids=request.policy_rule_ids,
            route_profile=request.route_profile,
            target_tool_id=request.target_tool_id,
            dominant_rule_id=request.dominant_rule_id,
            evidence_paths=authorization.evidence_paths,
            envelope_sha256=envelope_sha256,
        )
        journal_path = journal.append(journal_record)
        return ExecutionResult(
            schema_version=PHASE6_RESULT_SCHEMA_VERSION,
            request_schema_version=request.schema_version,
            decision=ExecutionDecision.NEEDS_REVIEW,
            decision_code=authorization.decision_code,
            approval_mode=approval_mode,
            approval_id=approval_id,
            idempotency_key=idempotency_key,
            route_profile=request.route_profile,
            target_tool_id=request.target_tool_id,
            dominant_rule_id=request.dominant_rule_id,
            adapter_id=None,
            evidence_paths=authorization.evidence_paths,
            applied_rule_ids=authorization.applied_rule_ids,
            envelope_sha256=envelope_sha256,
            journal_path=journal_path,
            produced_artifacts=(),
        )

    if approval is None or registry_entry is None:
        raise ValueError("Eligible phase6 execution requires approval and registry entry")

    produced_artifacts = _run_hermetic_adapter(request, approval, registry_entry)
    if approval.approval_mode is ApprovalMode.SIMULATE_ONLY:
        decision = ExecutionDecision.SIMULATED
        decision_code = ExecutionDecisionCode.SIMULATION_COMPLETED
    else:
        decision = ExecutionDecision.EXECUTED
        decision_code = ExecutionDecisionCode.EXECUTION_COMPLETED

    journal_record = ExecutionJournalRecord(
        schema_version="6.0.0",
        decision=decision,
        decision_code=decision_code,
        approval_mode=approval.approval_mode,
        approval_id=approval.approval_id,
        idempotency_key=approval.idempotency_key,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        evidence_paths=authorization.evidence_paths,
        envelope_sha256=envelope_sha256,
        adapter_id=registry_entry.adapter_id,
        produced_artifacts=produced_artifacts,
    )
    journal_path = journal.append(journal_record)
    return ExecutionResult(
        schema_version=PHASE6_RESULT_SCHEMA_VERSION,
        request_schema_version=request.schema_version,
        decision=decision,
        decision_code=decision_code,
        approval_mode=approval.approval_mode,
        approval_id=approval.approval_id,
        idempotency_key=approval.idempotency_key,
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        adapter_id=registry_entry.adapter_id,
        evidence_paths=authorization.evidence_paths,
        applied_rule_ids=authorization.applied_rule_ids,
        envelope_sha256=envelope_sha256,
        journal_path=journal_path,
        produced_artifacts=produced_artifacts,
    )


def _run_hermetic_adapter(
    request: ExecutionRequest,
    approval: ExecutionApprovalContract,
    registry_entry: ExecutorRegistryEntry,
) -> tuple[str, ...]:
    mode_fragment = "simulate" if approval.approval_mode is ApprovalMode.SIMULATE_ONLY else "execute"
    return tuple(
        sorted(
            (
                f"phase6:{mode_fragment}:adapter:{registry_entry.adapter_id}",
                f"phase6:{mode_fragment}:tool:{request.target_tool_id}",
                f"phase6:{mode_fragment}:route:{request.route_profile}",
            )
        )
    )


__all__ = ["run_phase6"]
