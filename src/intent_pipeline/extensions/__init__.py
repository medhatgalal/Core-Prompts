"""Shared extension policy contracts and fail-closed gate primitives."""

from intent_pipeline.extensions.contracts import (
    EXTENSION_GATE_SCHEMA_VERSION,
    EXTENSION_POLICY_SCHEMA_VERSION,
    SUPPORTED_EXTENSION_SCHEMA_MAJOR,
    ExtensionContractErrorCode,
    ExtensionGateDecision,
    ExtensionGateReasonCode,
    ExtensionGateResult,
    ExtensionMode,
    ExtensionPolicyContract,
    ExtensionPolicyContractError,
    ExtensionPolicyRule,
    ExtensionSourceKind,
    parse_extension_policy_contract,
    parse_extension_policy_contract_fail_closed,
    validate_extension_schema_version,
)


__all__ = [
    "EXTENSION_GATE_SCHEMA_VERSION",
    "EXTENSION_POLICY_SCHEMA_VERSION",
    "SUPPORTED_EXTENSION_SCHEMA_MAJOR",
    "ExtensionContractErrorCode",
    "ExtensionGateDecision",
    "ExtensionGateReasonCode",
    "ExtensionGateResult",
    "ExtensionMode",
    "ExtensionPolicyContract",
    "ExtensionPolicyContractError",
    "ExtensionPolicyRule",
    "ExtensionSourceKind",
    "parse_extension_policy_contract",
    "parse_extension_policy_contract_fail_closed",
    "validate_extension_schema_version",
]
