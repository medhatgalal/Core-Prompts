"""Phase-6 simulate-first controlled execution contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from typing import Any, Mapping, Iterable

from intent_pipeline.phase4.contracts import Phase4Result
from intent_pipeline.phase5.contracts import Phase5Result


PHASE6_APPROVAL_SCHEMA_VERSION = "6.0.0"
PHASE6_REQUEST_SCHEMA_VERSION = "6.0.0"
PHASE6_AUTHORIZATION_SCHEMA_VERSION = "6.0.0"
PHASE6_RESULT_SCHEMA_VERSION = "6.0.0"
PHASE6_JOURNAL_SCHEMA_VERSION = "6.0.0"
SUPPORTED_PHASE6_SCHEMA_MAJOR = "6"
SUPPORTED_PHASE4_SCHEMA_MAJOR = "4"
SUPPORTED_PHASE5_SCHEMA_MAJOR = "5"


class ApprovalMode(str, Enum):
    SIMULATE_ONLY = "SIMULATE_ONLY"
    EXECUTE_APPROVED = "EXECUTE_APPROVED"


class AuthorizationDecision(str, Enum):
    EXECUTION_READY = "EXECUTION_READY"
    SIMULATION_READY = "SIMULATION_READY"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ExecutionDecision(str, Enum):
    EXECUTED = "EXECUTED"
    SIMULATED = "SIMULATED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ExecutionDecisionCode(str, Enum):
    APPROVAL_MISSING = "EXEC-001-APPROVAL-MISSING"
    APPROVAL_INVALID = "EXEC-002-APPROVAL-INVALID"
    UPSTREAM_VALIDATION_BLOCKED = "EXEC-003-UPSTREAM-VALIDATION-BLOCKED"
    UPSTREAM_FALLBACK_INELIGIBLE = "EXEC-004-UPSTREAM-FALLBACK-INELIGIBLE"
    UPSTREAM_PHASE5_INELIGIBLE = "EXEC-005-UPSTREAM-PHASE5-INELIGIBLE"
    APPROVAL_EXPIRED = "EXEC-006-APPROVAL-EXPIRED"
    APPROVAL_ROUTE_MISMATCH = "EXEC-007-APPROVAL-ROUTE-MISMATCH"
    APPROVAL_TOOL_MISMATCH = "EXEC-008-APPROVAL-TOOL-MISMATCH"
    APPROVAL_RULE_MISMATCH = "EXEC-009-APPROVAL-RULE-MISMATCH"
    APPROVAL_CAPABILITY_MISMATCH = "EXEC-010-APPROVAL-CAPABILITY-MISMATCH"
    POLICY_SCHEMA_MISMATCH = "EXEC-011-POLICY-SCHEMA-MISMATCH"
    POLICY_RULE_MISMATCH = "EXEC-012-POLICY-RULE-MISMATCH"
    REGISTRY_UNMAPPED = "EXEC-013-REGISTRY-UNMAPPED"
    REGISTRY_DUPLICATE = "EXEC-014-REGISTRY-DUPLICATE"
    REGISTRY_SIMULATION_UNSUPPORTED = "EXEC-015-REGISTRY-SIMULATION-UNSUPPORTED"
    REGISTRY_EXECUTION_UNSUPPORTED = "EXEC-016-REGISTRY-EXECUTION-UNSUPPORTED"
    SIMULATION_COMPLETED = "EXEC-017-SIMULATION-COMPLETED"
    EXECUTION_COMPLETED = "EXEC-018-EXECUTION-COMPLETED"
    IDEMPOTENT_REPLAY = "EXEC-019-IDEMPOTENT-REPLAY"


class Phase6BoundaryErrorCode(str, Enum):
    FORBIDDEN_NETWORK_IMPORT = "BOUND-06-001-FORBIDDEN-NETWORK-IMPORT"
    FORBIDDEN_PROCESS_IMPORT = "BOUND-06-002-FORBIDDEN-PROCESS-IMPORT"
    FORBIDDEN_MUTATION_CALL = "BOUND-06-003-FORBIDDEN-MUTATION-CALL"
    FORBIDDEN_PHASE_LEAK = "BOUND-06-004-FORBIDDEN-PHASE-LEAK"


class Phase6ContractError(ValueError):
    """Typed contract coercion error used to fail closed in phase6."""

    def __init__(self, code: ExecutionDecisionCode, message: str, *, evidence_path: str, detail: Mapping[str, Any] | None = None) -> None:
        normalized_message = _normalize_text(message) or code.value
        super().__init__(f"{code.value}: {normalized_message}")
        self.code = code
        self.evidence_path = _normalize_text(evidence_path)
        self.detail = _canonicalize_mapping(detail or {})


@dataclass(frozen=True, slots=True)
class ExecutionApprovalContract:
    schema_version: str
    approval_mode: ApprovalMode
    approval_id: str
    approved_by: str
    approved_at: str
    expires_at: str
    idempotency_key: str
    route_profile: str
    target_tool_id: str
    dominant_rule_id: str
    required_capabilities: tuple[str, ...]
    policy_schema_version: str
    policy_rule_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE6_SCHEMA_MAJOR))
        if not isinstance(self.approval_mode, ApprovalMode):
            object.__setattr__(self, "approval_mode", ApprovalMode(str(self.approval_mode)))
        object.__setattr__(self, "approval_id", _require_text(self.approval_id, "approval_id"))
        object.__setattr__(self, "approved_by", _require_text(self.approved_by, "approved_by"))
        object.__setattr__(self, "approved_at", _require_text(self.approved_at, "approved_at"))
        object.__setattr__(self, "expires_at", _require_text(self.expires_at, "expires_at"))
        object.__setattr__(self, "idempotency_key", _require_text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(self, "route_profile", _require_text(self.route_profile, "route_profile"))
        object.__setattr__(self, "target_tool_id", _require_text(self.target_tool_id, "target_tool_id"))
        object.__setattr__(self, "dominant_rule_id", _require_text(self.dominant_rule_id, "dominant_rule_id"))
        object.__setattr__(self, "required_capabilities", _normalize_sorted_text(self.required_capabilities))
        object.__setattr__(self, "policy_schema_version", _require_text(self.policy_schema_version, "policy_schema_version"))
        object.__setattr__(self, "policy_rule_ids", _normalize_sorted_text(self.policy_rule_ids))
        _parse_timestamp(self.approved_at)
        _parse_timestamp(self.expires_at)
        if not self.required_capabilities:
            raise ValueError("ExecutionApprovalContract required_capabilities must be non-empty")
        if not self.policy_rule_ids:
            raise ValueError("ExecutionApprovalContract policy_rule_ids must be non-empty")

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "approval_mode": self.approval_mode.value,
            "approval_id": self.approval_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "expires_at": self.expires_at,
            "idempotency_key": self.idempotency_key,
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "dominant_rule_id": self.dominant_rule_id,
            "required_capabilities": list(self.required_capabilities),
            "policy_schema_version": self.policy_schema_version,
            "policy_rule_ids": list(self.policy_rule_ids),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    schema_version: str
    phase4_schema_version: str
    phase5_schema_version: str
    route_spec_schema_version: str
    validation_decision: str
    validation_can_proceed: bool
    fallback_decision: str
    phase5_terminal_status: str
    route_profile: str
    target_tool_id: str
    dominant_rule_id: str
    required_capabilities: tuple[str, ...]
    policy_schema_version: str
    policy_rule_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE6_SCHEMA_MAJOR))
        object.__setattr__(self, "phase4_schema_version", _validate_schema_major(self.phase4_schema_version, SUPPORTED_PHASE4_SCHEMA_MAJOR))
        object.__setattr__(self, "phase5_schema_version", _validate_schema_major(self.phase5_schema_version, SUPPORTED_PHASE5_SCHEMA_MAJOR))
        object.__setattr__(self, "route_spec_schema_version", _require_text(self.route_spec_schema_version, "route_spec_schema_version"))
        object.__setattr__(self, "validation_decision", _require_text(self.validation_decision, "validation_decision"))
        object.__setattr__(self, "validation_can_proceed", bool(self.validation_can_proceed))
        object.__setattr__(self, "fallback_decision", _require_text(self.fallback_decision, "fallback_decision"))
        object.__setattr__(self, "phase5_terminal_status", _require_text(self.phase5_terminal_status, "phase5_terminal_status"))
        object.__setattr__(self, "route_profile", _require_text(self.route_profile, "route_profile"))
        object.__setattr__(self, "target_tool_id", _require_text(self.target_tool_id, "target_tool_id"))
        object.__setattr__(self, "dominant_rule_id", _require_text(self.dominant_rule_id, "dominant_rule_id"))
        object.__setattr__(self, "required_capabilities", _normalize_sorted_text(self.required_capabilities))
        object.__setattr__(self, "policy_schema_version", _require_text(self.policy_schema_version, "policy_schema_version"))
        object.__setattr__(self, "policy_rule_ids", _normalize_sorted_text(self.policy_rule_ids))
        if not self.required_capabilities:
            raise ValueError("ExecutionRequest required_capabilities must be non-empty")
        if not self.policy_rule_ids:
            raise ValueError("ExecutionRequest policy_rule_ids must be non-empty")

    @classmethod
    def from_phase_results(
        cls,
        phase4_result: Phase4Result,
        phase5_result: Phase5Result,
        *,
        policy_schema_version: str,
        policy_rule_ids: Iterable[str],
    ) -> "ExecutionRequest":
        if not isinstance(phase4_result, Phase4Result):
            raise TypeError("phase4_result must be Phase4Result")
        if not isinstance(phase5_result, Phase5Result):
            raise TypeError("phase5_result must be Phase5Result")
        return cls(
            schema_version=PHASE6_REQUEST_SCHEMA_VERSION,
            phase4_schema_version=phase4_result.schema_version,
            phase5_schema_version=phase5_result.schema_version,
            route_spec_schema_version=phase4_result.route_spec_schema_version,
            validation_decision=phase4_result.validation.decision.value,
            validation_can_proceed=phase4_result.validation.can_proceed,
            fallback_decision=phase4_result.fallback.decision.value,
            phase5_terminal_status=phase5_result.output.machine_payload.terminal_status.value,
            route_profile=phase4_result.validation.route_profile,
            target_tool_id=phase4_result.validation.target_tool_id or "unknown-tool",
            dominant_rule_id=phase4_result.validation.dominant_rule_id,
            required_capabilities=phase4_result.validation.checked_capabilities,
            policy_schema_version=policy_schema_version,
            policy_rule_ids=tuple(policy_rule_ids),
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase4_schema_version": self.phase4_schema_version,
            "phase5_schema_version": self.phase5_schema_version,
            "route_spec_schema_version": self.route_spec_schema_version,
            "validation_decision": self.validation_decision,
            "validation_can_proceed": self.validation_can_proceed,
            "fallback_decision": self.fallback_decision,
            "phase5_terminal_status": self.phase5_terminal_status,
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "dominant_rule_id": self.dominant_rule_id,
            "required_capabilities": list(self.required_capabilities),
            "policy_schema_version": self.policy_schema_version,
            "policy_rule_ids": list(self.policy_rule_ids),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ExecutionAuthorizationReport:
    schema_version: str
    decision: AuthorizationDecision
    decision_code: ExecutionDecisionCode
    execute_eligible: bool
    simulation_allowed: bool
    route_profile: str
    target_tool_id: str
    dominant_rule_id: str
    approval_mode: ApprovalMode | None
    required_capabilities: tuple[str, ...]
    policy_schema_version: str
    policy_rule_ids: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    applied_rule_ids: tuple[str, ...]
    issues: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE6_SCHEMA_MAJOR))
        if not isinstance(self.decision, AuthorizationDecision):
            object.__setattr__(self, "decision", AuthorizationDecision(str(self.decision)))
        if not isinstance(self.decision_code, ExecutionDecisionCode):
            object.__setattr__(self, "decision_code", ExecutionDecisionCode(str(self.decision_code)))
        object.__setattr__(self, "execute_eligible", bool(self.execute_eligible))
        object.__setattr__(self, "simulation_allowed", bool(self.simulation_allowed))
        object.__setattr__(self, "route_profile", _require_text(self.route_profile, "route_profile"))
        object.__setattr__(self, "target_tool_id", _require_text(self.target_tool_id, "target_tool_id"))
        object.__setattr__(self, "dominant_rule_id", _require_text(self.dominant_rule_id, "dominant_rule_id"))
        if self.approval_mode is not None and not isinstance(self.approval_mode, ApprovalMode):
            object.__setattr__(self, "approval_mode", ApprovalMode(str(self.approval_mode)))
        object.__setattr__(self, "required_capabilities", _normalize_sorted_text(self.required_capabilities))
        object.__setattr__(self, "policy_schema_version", _require_text(self.policy_schema_version, "policy_schema_version"))
        object.__setattr__(self, "policy_rule_ids", _normalize_sorted_text(self.policy_rule_ids))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "applied_rule_ids", _unique_in_order(self.applied_rule_ids))
        object.__setattr__(self, "issues", _normalize_sorted_text(self.issues))
        if self.decision is AuthorizationDecision.EXECUTION_READY:
            if not self.execute_eligible or not self.simulation_allowed:
                raise ValueError("EXECUTION_READY authorization must allow execution and simulation")
        elif self.decision is AuthorizationDecision.SIMULATION_READY:
            if self.execute_eligible or not self.simulation_allowed:
                raise ValueError("SIMULATION_READY authorization must allow simulation only")
        else:
            if self.execute_eligible or self.simulation_allowed:
                raise ValueError("NEEDS_REVIEW authorization must fail closed")
            if not self.issues:
                raise ValueError("NEEDS_REVIEW authorization must include issues")

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "decision_code": self.decision_code.value,
            "execute_eligible": self.execute_eligible,
            "simulation_allowed": self.simulation_allowed,
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "dominant_rule_id": self.dominant_rule_id,
            "approval_mode": self.approval_mode.value if self.approval_mode is not None else None,
            "required_capabilities": list(self.required_capabilities),
            "policy_schema_version": self.policy_schema_version,
            "policy_rule_ids": list(self.policy_rule_ids),
            "evidence_paths": list(self.evidence_paths),
            "applied_rule_ids": list(self.applied_rule_ids),
            "issues": list(self.issues),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ExecutionJournalRecord:
    schema_version: str
    decision: ExecutionDecision
    decision_code: ExecutionDecisionCode
    approval_mode: ApprovalMode | None
    approval_id: str | None
    idempotency_key: str
    policy_schema_version: str
    policy_rule_ids: tuple[str, ...]
    route_profile: str
    target_tool_id: str
    dominant_rule_id: str
    evidence_paths: tuple[str, ...]
    envelope_sha256: str
    adapter_id: str | None = None
    produced_artifacts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE6_SCHEMA_MAJOR))
        if not isinstance(self.decision, ExecutionDecision):
            object.__setattr__(self, "decision", ExecutionDecision(str(self.decision)))
        if not isinstance(self.decision_code, ExecutionDecisionCode):
            object.__setattr__(self, "decision_code", ExecutionDecisionCode(str(self.decision_code)))
        if self.approval_mode is not None and not isinstance(self.approval_mode, ApprovalMode):
            object.__setattr__(self, "approval_mode", ApprovalMode(str(self.approval_mode)))
        object.__setattr__(self, "approval_id", _normalize_optional_text(self.approval_id))
        object.__setattr__(self, "idempotency_key", _require_text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(self, "policy_schema_version", _require_text(self.policy_schema_version, "policy_schema_version"))
        object.__setattr__(self, "policy_rule_ids", _normalize_sorted_text(self.policy_rule_ids))
        object.__setattr__(self, "route_profile", _require_text(self.route_profile, "route_profile"))
        object.__setattr__(self, "target_tool_id", _require_text(self.target_tool_id, "target_tool_id"))
        object.__setattr__(self, "dominant_rule_id", _require_text(self.dominant_rule_id, "dominant_rule_id"))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "envelope_sha256", _require_text(self.envelope_sha256, "envelope_sha256"))
        object.__setattr__(self, "adapter_id", _normalize_optional_text(self.adapter_id))
        object.__setattr__(self, "produced_artifacts", _normalize_sorted_text(self.produced_artifacts))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "decision_code": self.decision_code.value,
            "approval_mode": self.approval_mode.value if self.approval_mode is not None else None,
            "approval_id": self.approval_id,
            "idempotency_key": self.idempotency_key,
            "policy_schema_version": self.policy_schema_version,
            "policy_rule_ids": list(self.policy_rule_ids),
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "dominant_rule_id": self.dominant_rule_id,
            "evidence_paths": list(self.evidence_paths),
            "envelope_sha256": self.envelope_sha256,
            "adapter_id": self.adapter_id,
            "produced_artifacts": list(self.produced_artifacts),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    schema_version: str
    request_schema_version: str
    decision: ExecutionDecision
    decision_code: ExecutionDecisionCode
    approval_mode: ApprovalMode | None
    approval_id: str | None
    idempotency_key: str
    route_profile: str
    target_tool_id: str
    dominant_rule_id: str
    adapter_id: str | None
    evidence_paths: tuple[str, ...]
    applied_rule_ids: tuple[str, ...]
    envelope_sha256: str
    journal_path: str | None
    produced_artifacts: tuple[str, ...] = ()
    replayed_from_journal: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE6_SCHEMA_MAJOR))
        object.__setattr__(self, "request_schema_version", _validate_schema_major(self.request_schema_version, SUPPORTED_PHASE6_SCHEMA_MAJOR))
        if not isinstance(self.decision, ExecutionDecision):
            object.__setattr__(self, "decision", ExecutionDecision(str(self.decision)))
        if not isinstance(self.decision_code, ExecutionDecisionCode):
            object.__setattr__(self, "decision_code", ExecutionDecisionCode(str(self.decision_code)))
        if self.approval_mode is not None and not isinstance(self.approval_mode, ApprovalMode):
            object.__setattr__(self, "approval_mode", ApprovalMode(str(self.approval_mode)))
        object.__setattr__(self, "approval_id", _normalize_optional_text(self.approval_id))
        object.__setattr__(self, "idempotency_key", _require_text(self.idempotency_key, "idempotency_key"))
        object.__setattr__(self, "route_profile", _require_text(self.route_profile, "route_profile"))
        object.__setattr__(self, "target_tool_id", _require_text(self.target_tool_id, "target_tool_id"))
        object.__setattr__(self, "dominant_rule_id", _require_text(self.dominant_rule_id, "dominant_rule_id"))
        object.__setattr__(self, "adapter_id", _normalize_optional_text(self.adapter_id))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "applied_rule_ids", _unique_in_order(self.applied_rule_ids))
        object.__setattr__(self, "envelope_sha256", _require_text(self.envelope_sha256, "envelope_sha256"))
        object.__setattr__(self, "journal_path", _normalize_optional_text(self.journal_path))
        object.__setattr__(self, "produced_artifacts", _normalize_sorted_text(self.produced_artifacts))
        object.__setattr__(self, "replayed_from_journal", bool(self.replayed_from_journal))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_schema_version": self.request_schema_version,
            "decision": self.decision.value,
            "decision_code": self.decision_code.value,
            "approval_mode": self.approval_mode.value if self.approval_mode is not None else None,
            "approval_id": self.approval_id,
            "idempotency_key": self.idempotency_key,
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "dominant_rule_id": self.dominant_rule_id,
            "adapter_id": self.adapter_id,
            "evidence_paths": list(self.evidence_paths),
            "applied_rule_ids": list(self.applied_rule_ids),
            "envelope_sha256": self.envelope_sha256,
            "journal_path": self.journal_path,
            "produced_artifacts": list(self.produced_artifacts),
            "replayed_from_journal": self.replayed_from_journal,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Phase6BoundaryViolation:
    code: Phase6BoundaryErrorCode
    evidence_paths: tuple[str, ...]
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, Phase6BoundaryErrorCode):
            object.__setattr__(self, "code", Phase6BoundaryErrorCode(str(self.code)))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "detail", _require_text(self.detail, "detail"))

    def as_payload(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "evidence_paths": list(self.evidence_paths),
            "detail": self.detail,
        }


def parse_execution_approval_contract(approval_contract: ExecutionApprovalContract | Mapping[str, Any]) -> ExecutionApprovalContract:
    if isinstance(approval_contract, ExecutionApprovalContract):
        return approval_contract
    if not isinstance(approval_contract, Mapping):
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            "approval_contract must be an ExecutionApprovalContract or mapping payload",
            evidence_path="approval_contract",
            detail={"payload_type": type(approval_contract).__name__},
        )
    payload = _canonicalize_mapping(approval_contract)
    try:
        return ExecutionApprovalContract(
            schema_version=_extract_required_text(payload, "schema_version", "approval_contract.schema_version"),
            approval_mode=_extract_required_text(payload, "approval_mode", "approval_contract.approval_mode"),
            approval_id=_extract_required_text(payload, "approval_id", "approval_contract.approval_id"),
            approved_by=_extract_required_text(payload, "approved_by", "approval_contract.approved_by"),
            approved_at=_extract_required_text(payload, "approved_at", "approval_contract.approved_at"),
            expires_at=_extract_required_text(payload, "expires_at", "approval_contract.expires_at"),
            idempotency_key=_extract_required_text(payload, "idempotency_key", "approval_contract.idempotency_key"),
            route_profile=_extract_required_text(payload, "route_profile", "approval_contract.route_profile"),
            target_tool_id=_extract_required_text(payload, "target_tool_id", "approval_contract.target_tool_id"),
            dominant_rule_id=_extract_required_text(payload, "dominant_rule_id", "approval_contract.dominant_rule_id"),
            required_capabilities=tuple(_extract_required_text_list(payload, "required_capabilities", "approval_contract.required_capabilities")),
            policy_schema_version=_extract_required_text(payload, "policy_schema_version", "approval_contract.policy_schema_version"),
            policy_rule_ids=tuple(_extract_required_text_list(payload, "policy_rule_ids", "approval_contract.policy_rule_ids")),
        )
    except (ValueError, TypeError) as exc:
        if isinstance(exc, Phase6ContractError):
            raise
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            str(exc),
            evidence_path="approval_contract",
        ) from exc


def parse_execution_request(execution_request: ExecutionRequest | Mapping[str, Any]) -> ExecutionRequest:
    if isinstance(execution_request, ExecutionRequest):
        return execution_request
    if not isinstance(execution_request, Mapping):
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            "execution_request must be an ExecutionRequest or mapping payload",
            evidence_path="execution_request",
            detail={"payload_type": type(execution_request).__name__},
        )
    payload = _canonicalize_mapping(execution_request)
    try:
        return ExecutionRequest(
            schema_version=_extract_required_text(payload, "schema_version", "execution_request.schema_version"),
            phase4_schema_version=_extract_required_text(payload, "phase4_schema_version", "execution_request.phase4_schema_version"),
            phase5_schema_version=_extract_required_text(payload, "phase5_schema_version", "execution_request.phase5_schema_version"),
            route_spec_schema_version=_extract_required_text(payload, "route_spec_schema_version", "execution_request.route_spec_schema_version"),
            validation_decision=_extract_required_text(payload, "validation_decision", "execution_request.validation_decision"),
            validation_can_proceed=_extract_required_bool(payload, "validation_can_proceed", "execution_request.validation_can_proceed"),
            fallback_decision=_extract_required_text(payload, "fallback_decision", "execution_request.fallback_decision"),
            phase5_terminal_status=_extract_required_text(payload, "phase5_terminal_status", "execution_request.phase5_terminal_status"),
            route_profile=_extract_required_text(payload, "route_profile", "execution_request.route_profile"),
            target_tool_id=_extract_required_text(payload, "target_tool_id", "execution_request.target_tool_id"),
            dominant_rule_id=_extract_required_text(payload, "dominant_rule_id", "execution_request.dominant_rule_id"),
            required_capabilities=tuple(_extract_required_text_list(payload, "required_capabilities", "execution_request.required_capabilities")),
            policy_schema_version=_extract_required_text(payload, "policy_schema_version", "execution_request.policy_schema_version"),
            policy_rule_ids=tuple(_extract_required_text_list(payload, "policy_rule_ids", "execution_request.policy_rule_ids")),
        )
    except (ValueError, TypeError) as exc:
        if isinstance(exc, Phase6ContractError):
            raise
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            str(exc),
            evidence_path="execution_request",
        ) from exc


def build_request_envelope_sha256(execution_request: ExecutionRequest) -> str:
    if not isinstance(execution_request, ExecutionRequest):
        raise TypeError("build_request_envelope_sha256 expects ExecutionRequest input")
    import hashlib
    return hashlib.sha256(execution_request.to_json().encode("utf-8")).hexdigest()


def _extract_required_text(payload: Mapping[str, Any], key: str, evidence_path: str) -> str:
    value = _normalize_text(payload.get(key))
    if not value:
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            f"{key} is required",
            evidence_path=evidence_path,
        )
    return value


def _extract_required_bool(payload: Mapping[str, Any], key: str, evidence_path: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            f"{key} must be a boolean",
            evidence_path=evidence_path,
        )
    return value


def _extract_required_text_list(payload: Mapping[str, Any], key: str, evidence_path: str) -> list[str]:
    raw_value = payload.get(key)
    if not isinstance(raw_value, list):
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            f"{key} must be a list of strings",
            evidence_path=evidence_path,
        )
    values = [_normalize_text(item) for item in raw_value if _normalize_text(item)]
    if not values:
        raise Phase6ContractError(
            ExecutionDecisionCode.APPROVAL_INVALID,
            f"{key} must be non-empty",
            evidence_path=evidence_path,
        )
    return values


def _validate_schema_major(schema_version: str, expected_major: str) -> str:
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise ValueError("schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != expected_major:
        raise ValueError(f"Unsupported schema major '{major}', expected {expected_major}.x")
    return normalized


def _parse_timestamp(value: str) -> datetime:
    normalized = _normalize_text(value)
    candidate = normalized[:-1] + "+00:00" if normalized.endswith("Z") else normalized
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _require_text(value: object, field_name: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_optional_text(value: object) -> str | None:
    normalized = _normalize_text(value)
    return normalized or None


def _normalize_sorted_text(values: Iterable[str]) -> tuple[str, ...]:
    normalized = {text for text in (_normalize_text(item) for item in values) if text}
    return tuple(sorted(normalized))


def _unique_in_order(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for entry in values:
        normalized = _normalize_text(entry)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _canonicalize_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _canonicalize_value(data[key]) for key in sorted(data)}


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _canonicalize_mapping(value)
    if isinstance(value, tuple):
        return [_canonicalize_value(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize_value(item) for item in value]
    return value


__all__ = [
    "ApprovalMode",
    "AuthorizationDecision",
    "ExecutionApprovalContract",
    "ExecutionAuthorizationReport",
    "ExecutionDecision",
    "ExecutionDecisionCode",
    "ExecutionJournalRecord",
    "ExecutionRequest",
    "ExecutionResult",
    "PHASE6_APPROVAL_SCHEMA_VERSION",
    "PHASE6_AUTHORIZATION_SCHEMA_VERSION",
    "PHASE6_JOURNAL_SCHEMA_VERSION",
    "PHASE6_REQUEST_SCHEMA_VERSION",
    "PHASE6_RESULT_SCHEMA_VERSION",
    "Phase6BoundaryErrorCode",
    "Phase6BoundaryViolation",
    "Phase6ContractError",
    "SUPPORTED_PHASE6_SCHEMA_MAJOR",
    "build_request_envelope_sha256",
    "parse_execution_approval_contract",
    "parse_execution_request",
]
