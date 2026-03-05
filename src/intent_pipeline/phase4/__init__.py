"""Phase-4 target validation surfaces."""

from intent_pipeline.phase4.contracts import (
    CapabilityMatrix,
    PHASE4_VALIDATION_SCHEMA_VERSION,
    PolicyContract,
    RequiredCapabilityBinding,
    RouteSpecTarget,
    RouteToolBinding,
    ToolCapability,
    ValidationContractError,
    ValidationDecision,
    ValidationErrorCode,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    parse_capability_matrix,
    parse_policy_contract,
    parse_route_spec_target,
)
from intent_pipeline.phase4.validator import validate_target


__all__ = [
    "CapabilityMatrix",
    "PHASE4_VALIDATION_SCHEMA_VERSION",
    "PolicyContract",
    "RequiredCapabilityBinding",
    "RouteSpecTarget",
    "RouteToolBinding",
    "ToolCapability",
    "ValidationContractError",
    "ValidationDecision",
    "ValidationErrorCode",
    "ValidationIssue",
    "ValidationReport",
    "ValidationSeverity",
    "parse_capability_matrix",
    "parse_policy_contract",
    "parse_route_spec_target",
    "validate_target",
]
