"""Deterministic fail-closed extension boundary gate evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping, Sequence

from intent_pipeline.extensions.contracts import (
    EXTENSION_GATE_SCHEMA_VERSION,
    ExtensionGateDecision as PolicyGateDecision,
    ExtensionPolicyContract,
    ExtensionPolicyContractError,
    ExtensionSourceKind,
    parse_extension_policy_contract,
)
from intent_pipeline.routing.contracts import RouteProfile


_KNOWN_EXTENSION_MODES = frozenset({"DISABLED", "CONTROLLED"})
_KNOWN_ROUTE_PROFILES = frozenset(profile.value for profile in RouteProfile)
_KNOWN_CAPABILITIES = frozenset({"cap.read", "cap.fetch", "cap.write", "cap.execute"})


class ExtensionGateOutcome(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ExtensionGateReasonCode(str, Enum):
    EXTENSIONS_DISABLED = "EXT-GATE-001-EXTENSIONS-DISABLED"
    UNKNOWN_MODE = "EXT-GATE-002-UNKNOWN-MODE"
    MISSING_POLICY = "EXT-GATE-003-MISSING-POLICY"
    INVALID_POLICY = "EXT-GATE-004-INVALID-POLICY"
    UNKNOWN_ROUTE_PROFILE = "EXT-GATE-005-UNKNOWN-ROUTE-PROFILE"
    NO_MATCHING_RULE = "EXT-GATE-006-NO-MATCHING-RULE"
    UNKNOWN_CAPABILITY = "EXT-GATE-007-UNKNOWN-CAPABILITY"
    RULE_BLOCK = "EXT-GATE-008-RULE-BLOCK"
    RULE_NEEDS_REVIEW = "EXT-GATE-009-RULE-NEEDS-REVIEW"
    RULE_ALLOW = "EXT-GATE-010-RULE-ALLOW"


@dataclass(frozen=True, slots=True)
class ExtensionGateDecision:
    schema_version: str
    outcome: ExtensionGateOutcome
    reason_code: ExtensionGateReasonCode
    extension_mode: str
    route_profile: str
    policy_schema_version: str
    matched_rule_ids: tuple[str, ...]
    requested_capabilities: tuple[str, ...]
    evidence_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _normalize_text(self.schema_version) or EXTENSION_GATE_SCHEMA_VERSION)
        if not isinstance(self.outcome, ExtensionGateOutcome):
            object.__setattr__(self, "outcome", ExtensionGateOutcome(str(self.outcome)))
        if not isinstance(self.reason_code, ExtensionGateReasonCode):
            object.__setattr__(self, "reason_code", ExtensionGateReasonCode(str(self.reason_code)))
        object.__setattr__(self, "extension_mode", _normalize_upper(self.extension_mode) or "UNKNOWN")
        object.__setattr__(self, "route_profile", _normalize_upper(self.route_profile) or "UNKNOWN")
        object.__setattr__(self, "policy_schema_version", _normalize_text(self.policy_schema_version) or "unknown")
        object.__setattr__(self, "matched_rule_ids", _normalize_sorted_text(self.matched_rule_ids, uppercase=False))
        object.__setattr__(self, "requested_capabilities", _normalize_sorted_text(self.requested_capabilities, uppercase=False))
        object.__setattr__(self, "evidence_paths", _normalize_paths(self.evidence_paths))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "outcome": self.outcome.value,
            "reason_code": self.reason_code.value,
            "extension_mode": self.extension_mode,
            "route_profile": self.route_profile,
            "policy_schema_version": self.policy_schema_version,
            "matched_rule_ids": list(self.matched_rule_ids),
            "requested_capabilities": list(self.requested_capabilities),
            "evidence_paths": list(self.evidence_paths),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def evaluate_extension_gate(
    *,
    extension_mode: str,
    route_profile: str,
    requested_capabilities: Sequence[str] = (),
    policy_contract: ExtensionPolicyContract | Mapping[str, Any] | None = None,
) -> ExtensionGateDecision:
    """Evaluate extension policy gate with deterministic fail-closed precedence."""
    normalized_mode = _normalize_upper(extension_mode)
    normalized_profile = _normalize_upper(route_profile)
    normalized_capabilities = _normalize_sorted_text(tuple(requested_capabilities), uppercase=False)

    if normalized_mode not in _KNOWN_EXTENSION_MODES:
        return _decision(
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.UNKNOWN_MODE,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="unknown",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("pipeline.extension_mode",),
        )

    if normalized_profile not in _KNOWN_ROUTE_PROFILES:
        return _decision(
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.UNKNOWN_ROUTE_PROFILE,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="unknown",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("pipeline.route_profile",),
        )

    if normalized_mode == "DISABLED":
        return _decision(
            outcome=ExtensionGateOutcome.ALLOW,
            reason_code=ExtensionGateReasonCode.EXTENSIONS_DISABLED,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="disabled",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("pipeline.extension_mode",),
        )

    unknown_capabilities = tuple(
        capability
        for capability in normalized_capabilities
        if capability not in _KNOWN_CAPABILITIES
    )
    if unknown_capabilities:
        return _decision(
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.UNKNOWN_CAPABILITY,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="unknown",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=(
                "pipeline.requested_capabilities",
                f"pipeline.requested_capabilities::{unknown_capabilities[0]}",
            ),
        )

    if policy_contract is None:
        return _decision(
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.MISSING_POLICY,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="missing",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("pipeline.extension_policy",),
        )

    try:
        policy = parse_extension_policy_contract(policy_contract)
    except ExtensionPolicyContractError as error:
        return _decision(
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.INVALID_POLICY,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version="invalid",
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("pipeline.extension_policy", error.evidence_path),
        )

    if policy.extension_mode.value != normalized_mode:
        return _decision(
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.NO_MATCHING_RULE,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version=policy.schema_version,
            matched_rule_ids=(),
            requested_capabilities=normalized_capabilities,
            evidence_paths=("policy_contract.extension_mode",),
        )

    policy_result = policy.evaluate_source_kind(ExtensionSourceKind.URL)
    matched_rule_ids = tuple(
        rule.rule_id
        for rule in policy.rules
        if rule.source_kind is ExtensionSourceKind.URL
    )
    if policy_result.decision is PolicyGateDecision.BLOCK:
        return _decision(
            outcome=ExtensionGateOutcome.BLOCK,
            reason_code=ExtensionGateReasonCode.RULE_BLOCK,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version=policy.schema_version,
            matched_rule_ids=matched_rule_ids,
            requested_capabilities=normalized_capabilities,
            evidence_paths=tuple(policy_result.evidence_paths),
        )
    if policy_result.decision is PolicyGateDecision.NEEDS_REVIEW:
        return _decision(
            outcome=ExtensionGateOutcome.NEEDS_REVIEW,
            reason_code=ExtensionGateReasonCode.RULE_NEEDS_REVIEW,
            extension_mode=normalized_mode,
            route_profile=normalized_profile,
            policy_schema_version=policy.schema_version,
            matched_rule_ids=matched_rule_ids,
            requested_capabilities=normalized_capabilities,
            evidence_paths=tuple(policy_result.evidence_paths),
        )
    return _decision(
        outcome=ExtensionGateOutcome.ALLOW,
        reason_code=ExtensionGateReasonCode.RULE_ALLOW,
        extension_mode=normalized_mode,
        route_profile=normalized_profile,
        policy_schema_version=policy.schema_version,
        matched_rule_ids=matched_rule_ids,
        requested_capabilities=normalized_capabilities,
        evidence_paths=tuple(policy_result.evidence_paths),
    )


def _decision(
    *,
    outcome: ExtensionGateOutcome,
    reason_code: ExtensionGateReasonCode,
    extension_mode: str,
    route_profile: str,
    policy_schema_version: str,
    matched_rule_ids: tuple[str, ...],
    requested_capabilities: tuple[str, ...],
    evidence_paths: tuple[str, ...],
) -> ExtensionGateDecision:
    return ExtensionGateDecision(
        schema_version=EXTENSION_GATE_SCHEMA_VERSION,
        outcome=outcome,
        reason_code=reason_code,
        extension_mode=extension_mode,
        route_profile=route_profile,
        policy_schema_version=policy_schema_version,
        matched_rule_ids=matched_rule_ids,
        requested_capabilities=requested_capabilities,
        evidence_paths=evidence_paths,
    )


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_upper(value: object) -> str:
    return _normalize_text(value).upper()


def _normalize_sorted_text(
    values: tuple[str, ...] | list[str] | set[str],
    *,
    uppercase: bool,
) -> tuple[str, ...]:
    normalized_values = set()
    for value in values:
        normalized = _normalize_text(value)
        if not normalized:
            continue
        normalized_values.add(normalized.upper() if uppercase else normalized)
    return tuple(sorted(normalized_values))


def _normalize_paths(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for value in (_normalize_text(entry) for entry in values)
                if value
            }
        )
    )


__all__ = [
    "EXTENSION_GATE_SCHEMA_VERSION",
    "ExtensionGateDecision",
    "ExtensionGateOutcome",
    "ExtensionGateReasonCode",
    "evaluate_extension_gate",
]
