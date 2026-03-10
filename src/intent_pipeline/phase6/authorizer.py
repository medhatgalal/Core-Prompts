"""Phase-6 execute-eligibility authorizer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from intent_pipeline.phase6.contracts import (
    ApprovalMode,
    AuthorizationDecision,
    ExecutionApprovalContract,
    ExecutionAuthorizationReport,
    ExecutionDecisionCode,
    ExecutionRequest,
    PHASE6_AUTHORIZATION_SCHEMA_VERSION,
    Phase6ContractError,
    parse_execution_approval_contract,
    parse_execution_request,
)
from intent_pipeline.phase6.executor_registry import ExecutorRegistry, ExecutorRegistryEntry, parse_executor_registry


_AUTHORIZE_RULE_IDS: tuple[str, ...] = (
    "PHASE6-RULE-001-UPSTREAM",
    "PHASE6-RULE-002-APPROVAL",
    "PHASE6-RULE-003-REGISTRY",
)


def authorize_execution(
    execution_request: ExecutionRequest | Mapping[str, Any],
    approval_contract: ExecutionApprovalContract | Mapping[str, Any] | None,
    registry: ExecutorRegistry | Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> tuple[ExecutionAuthorizationReport, ExecutorRegistryEntry | None]:
    request = parse_execution_request(execution_request)

    if request.validation_decision != "PASS" or not request.validation_can_proceed:
        return _needs_review(
            request,
            ExecutionDecisionCode.UPSTREAM_VALIDATION_BLOCKED,
            issues=("validation decision must be PASS with can_proceed=true",),
            evidence_paths=("phase4.validation.decision", "phase4.validation.can_proceed"),
        ), None
    if request.fallback_decision != "USE_PRIMARY":
        return _needs_review(
            request,
            ExecutionDecisionCode.UPSTREAM_FALLBACK_INELIGIBLE,
            issues=("fallback decision must remain USE_PRIMARY",),
            evidence_paths=("phase4.fallback.decision",),
        ), None
    if request.phase5_terminal_status != "USE_PRIMARY":
        return _needs_review(
            request,
            ExecutionDecisionCode.UPSTREAM_PHASE5_INELIGIBLE,
            issues=("phase5 terminal status must remain USE_PRIMARY",),
            evidence_paths=("phase5.output.machine_payload.terminal_status",),
        ), None

    if approval_contract is None:
        return _needs_review(
            request,
            ExecutionDecisionCode.APPROVAL_MISSING,
            issues=("approval contract is required",),
            evidence_paths=("phase6.approval_contract",),
        ), None

    try:
        approval = parse_execution_approval_contract(approval_contract)
    except Phase6ContractError as error:
        return _needs_review(
            request,
            error.code,
            issues=(str(error),),
            evidence_paths=(error.evidence_path or "phase6.approval_contract",),
        ), None

    current_time = now.astimezone(timezone.utc) if now is not None else datetime.now(timezone.utc)
    if _parse_timestamp(approval.expires_at) <= current_time:
        return _needs_review(
            request,
            ExecutionDecisionCode.APPROVAL_EXPIRED,
            approval_mode=approval.approval_mode,
            issues=("approval contract is expired",),
            evidence_paths=("approval_contract.expires_at",),
        ), None
    if approval.route_profile != request.route_profile:
        return _needs_review(
            request,
            ExecutionDecisionCode.APPROVAL_ROUTE_MISMATCH,
            approval_mode=approval.approval_mode,
            issues=("approval route_profile must match execution request",),
            evidence_paths=("approval_contract.route_profile", "execution_request.route_profile"),
        ), None
    if approval.target_tool_id != request.target_tool_id:
        return _needs_review(
            request,
            ExecutionDecisionCode.APPROVAL_TOOL_MISMATCH,
            approval_mode=approval.approval_mode,
            issues=("approval target_tool_id must match execution request",),
            evidence_paths=("approval_contract.target_tool_id", "execution_request.target_tool_id"),
        ), None
    if approval.dominant_rule_id != request.dominant_rule_id:
        return _needs_review(
            request,
            ExecutionDecisionCode.APPROVAL_RULE_MISMATCH,
            approval_mode=approval.approval_mode,
            issues=("approval dominant_rule_id must match execution request",),
            evidence_paths=("approval_contract.dominant_rule_id", "execution_request.dominant_rule_id"),
        ), None
    if approval.required_capabilities != request.required_capabilities:
        return _needs_review(
            request,
            ExecutionDecisionCode.APPROVAL_CAPABILITY_MISMATCH,
            approval_mode=approval.approval_mode,
            issues=("approval required_capabilities must exactly match execution request",),
            evidence_paths=("approval_contract.required_capabilities", "execution_request.required_capabilities"),
        ), None
    if approval.policy_schema_version != request.policy_schema_version:
        return _needs_review(
            request,
            ExecutionDecisionCode.POLICY_SCHEMA_MISMATCH,
            approval_mode=approval.approval_mode,
            issues=("approval policy_schema_version must match execution request",),
            evidence_paths=("approval_contract.policy_schema_version", "execution_request.policy_schema_version"),
        ), None
    if approval.policy_rule_ids != request.policy_rule_ids:
        return _needs_review(
            request,
            ExecutionDecisionCode.POLICY_RULE_MISMATCH,
            approval_mode=approval.approval_mode,
            issues=("approval policy_rule_ids must exactly match execution request",),
            evidence_paths=("approval_contract.policy_rule_ids", "execution_request.policy_rule_ids"),
        ), None

    try:
        parsed_registry = parse_executor_registry(registry)
        registry_entry = parsed_registry.resolve(request.route_profile, request.target_tool_id)
    except Phase6ContractError as error:
        return _needs_review(
            request,
            error.code,
            approval_mode=approval.approval_mode,
            issues=(str(error),),
            evidence_paths=(error.evidence_path or "phase6.registry",),
        ), None

    if not set(request.required_capabilities).issubset(set(registry_entry.capabilities)):
        return _needs_review(
            request,
            ExecutionDecisionCode.APPROVAL_CAPABILITY_MISMATCH,
            approval_mode=approval.approval_mode,
            issues=("registry capabilities must cover execution request capabilities",),
            evidence_paths=("phase6.registry.capabilities", "execution_request.required_capabilities"),
        ), None

    if approval.approval_mode is ApprovalMode.SIMULATE_ONLY:
        if not registry_entry.supports_simulation:
            return _needs_review(
                request,
                ExecutionDecisionCode.REGISTRY_SIMULATION_UNSUPPORTED,
                approval_mode=approval.approval_mode,
                issues=("registry entry does not support simulation",),
                evidence_paths=("phase6.registry.supports_simulation",),
            ), None
        return ExecutionAuthorizationReport(
            schema_version=PHASE6_AUTHORIZATION_SCHEMA_VERSION,
            decision=AuthorizationDecision.SIMULATION_READY,
            decision_code=ExecutionDecisionCode.SIMULATION_COMPLETED,
            execute_eligible=False,
            simulation_allowed=True,
            route_profile=request.route_profile,
            target_tool_id=request.target_tool_id,
            dominant_rule_id=request.dominant_rule_id,
            approval_mode=approval.approval_mode,
            required_capabilities=request.required_capabilities,
            policy_schema_version=request.policy_schema_version,
            policy_rule_ids=request.policy_rule_ids,
            evidence_paths=(
                "phase4.validation.decision",
                "phase4.fallback.decision",
                "phase5.output.machine_payload.terminal_status",
                "approval_contract.approval_mode",
                "phase6.registry.supports_simulation",
            ),
            applied_rule_ids=(*_AUTHORIZE_RULE_IDS, request.dominant_rule_id),
        ), registry_entry

    if not registry_entry.supports_execution:
        return _needs_review(
            request,
            ExecutionDecisionCode.REGISTRY_EXECUTION_UNSUPPORTED,
            approval_mode=approval.approval_mode,
            issues=("registry entry does not support execute-approved flow",),
            evidence_paths=("phase6.registry.supports_execution",),
        ), None

    return ExecutionAuthorizationReport(
        schema_version=PHASE6_AUTHORIZATION_SCHEMA_VERSION,
        decision=AuthorizationDecision.EXECUTION_READY,
        decision_code=ExecutionDecisionCode.EXECUTION_COMPLETED,
        execute_eligible=True,
        simulation_allowed=True,
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        approval_mode=approval.approval_mode,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
        evidence_paths=(
            "phase4.validation.decision",
            "phase4.fallback.decision",
            "phase5.output.machine_payload.terminal_status",
            "approval_contract.approval_mode",
            "phase6.registry.supports_execution",
        ),
        applied_rule_ids=(*_AUTHORIZE_RULE_IDS, request.dominant_rule_id),
    ), registry_entry


def _needs_review(
    request: ExecutionRequest,
    decision_code: ExecutionDecisionCode,
    *,
    approval_mode: ApprovalMode | None = None,
    issues: tuple[str, ...],
    evidence_paths: tuple[str, ...],
) -> ExecutionAuthorizationReport:
    return ExecutionAuthorizationReport(
        schema_version=PHASE6_AUTHORIZATION_SCHEMA_VERSION,
        decision=AuthorizationDecision.NEEDS_REVIEW,
        decision_code=decision_code,
        execute_eligible=False,
        simulation_allowed=False,
        route_profile=request.route_profile,
        target_tool_id=request.target_tool_id,
        dominant_rule_id=request.dominant_rule_id,
        approval_mode=approval_mode,
        required_capabilities=request.required_capabilities,
        policy_schema_version=request.policy_schema_version,
        policy_rule_ids=request.policy_rule_ids,
        evidence_paths=evidence_paths,
        applied_rule_ids=(*_AUTHORIZE_RULE_IDS, request.dominant_rule_id),
        issues=issues,
    )


def _parse_timestamp(value: str) -> datetime:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


__all__ = ["authorize_execution"]
