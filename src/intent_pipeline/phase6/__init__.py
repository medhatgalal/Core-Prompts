"""Phase-6 simulate-first controlled execution surfaces."""

from intent_pipeline.phase6.authorizer import authorize_execution
from intent_pipeline.phase6.contracts import (
    ApprovalMode,
    AuthorizationDecision,
    ExecutionApprovalContract,
    ExecutionAuthorizationReport,
    ExecutionDecision,
    ExecutionDecisionCode,
    ExecutionJournalRecord,
    ExecutionRequest,
    ExecutionResult,
    PHASE6_APPROVAL_SCHEMA_VERSION,
    PHASE6_AUTHORIZATION_SCHEMA_VERSION,
    PHASE6_JOURNAL_SCHEMA_VERSION,
    PHASE6_REQUEST_SCHEMA_VERSION,
    PHASE6_RESULT_SCHEMA_VERSION,
    Phase6BoundaryErrorCode,
    Phase6BoundaryViolation,
    Phase6ContractError,
    build_request_envelope_sha256,
    parse_execution_approval_contract,
    parse_execution_request,
)
from intent_pipeline.phase6.engine import run_phase6
from intent_pipeline.phase6.executor_registry import ExecutorRegistry, ExecutorRegistryEntry, PHASE6_REGISTRY_SCHEMA_VERSION, parse_executor_registry
from intent_pipeline.phase6.journal import ExecutionJournal, JournalLookup


__all__ = [
    "ApprovalMode",
    "AuthorizationDecision",
    "ExecutionApprovalContract",
    "ExecutionAuthorizationReport",
    "ExecutionDecision",
    "ExecutionDecisionCode",
    "ExecutionJournal",
    "ExecutionJournalRecord",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutorRegistry",
    "ExecutorRegistryEntry",
    "JournalLookup",
    "PHASE6_APPROVAL_SCHEMA_VERSION",
    "PHASE6_AUTHORIZATION_SCHEMA_VERSION",
    "PHASE6_JOURNAL_SCHEMA_VERSION",
    "PHASE6_REGISTRY_SCHEMA_VERSION",
    "PHASE6_REQUEST_SCHEMA_VERSION",
    "PHASE6_RESULT_SCHEMA_VERSION",
    "Phase6BoundaryErrorCode",
    "Phase6BoundaryViolation",
    "Phase6ContractError",
    "authorize_execution",
    "build_request_envelope_sha256",
    "parse_execution_approval_contract",
    "parse_execution_request",
    "parse_executor_registry",
    "run_phase6",
]
