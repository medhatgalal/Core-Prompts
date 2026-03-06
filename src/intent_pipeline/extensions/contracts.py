"""Shared extension policy contracts and fail-closed gate primitives."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import re
from typing import Any, Mapping


EXTENSION_GATE_SCHEMA_VERSION = "1.0.0"
EXTENSION_POLICY_SCHEMA_VERSION = "1.0.0"
SUPPORTED_EXTENSION_SCHEMA_MAJOR = "1"
_VERSIONED_RULE_ID = re.compile(r"^v(?P<major>[0-9]+)\.[A-Za-z0-9._-]+$")


class ExtensionMode(str, Enum):
    DISABLED = "DISABLED"
    CONTROLLED = "CONTROLLED"


class ExtensionSourceKind(str, Enum):
    LOCAL_FILE = "LOCAL_FILE"
    URL = "URL"


class ExtensionGateDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ExtensionGateReasonCode(str, Enum):
    POLICY_VALIDATED = "EXT-GATE-000-POLICY-VALIDATED"
    POLICY_RULE_ALLOW = "EXT-GATE-001-POLICY-RULE-ALLOW"
    POLICY_RULE_BLOCK = "EXT-GATE-002-POLICY-RULE-BLOCK"
    FAIL_CLOSED_MISSING_POLICY = "EXT-GATE-003-FAIL-CLOSED-MISSING-POLICY"
    FAIL_CLOSED_INVALID_POLICY = "EXT-GATE-004-FAIL-CLOSED-INVALID-POLICY"
    EXTENSIONS_DISABLED = "EXT-GATE-005-EXTENSIONS-DISABLED"
    NO_MATCHING_RULE = "EXT-GATE-006-NO-MATCHING-RULE"


class ExtensionContractErrorCode(str, Enum):
    INVALID_POLICY_CONTRACT = "EXT-CONTRACT-001-INVALID-POLICY-CONTRACT"
    UNSUPPORTED_SCHEMA_MAJOR = "EXT-CONTRACT-002-UNSUPPORTED-SCHEMA-MAJOR"
    INVALID_RULE_ID = "EXT-CONTRACT-003-INVALID-RULE-ID"
    DUPLICATE_RULE_ID = "EXT-CONTRACT-004-DUPLICATE-RULE-ID"
    INVALID_RULE_FIELD = "EXT-CONTRACT-005-INVALID-RULE-FIELD"


class ExtensionPolicyContractError(ValueError):
    """Typed extension-policy coercion error for deterministic fail-closed behavior."""

    def __init__(
        self,
        code: ExtensionContractErrorCode,
        message: str,
        *,
        evidence_path: str,
        detail: Mapping[str, Any] | None = None,
    ) -> None:
        normalized_message = _normalize_text(message)
        if not normalized_message:
            normalized_message = code.value
        super().__init__(f"{code.value}: {normalized_message}")
        self.code = code
        self.evidence_path = _normalize_text(evidence_path)
        self.detail = _canonicalize_mapping(detail or {})


@dataclass(frozen=True, slots=True)
class ExtensionPolicyRule:
    rule_id: str
    source_kind: ExtensionSourceKind
    decision: ExtensionGateDecision
    priority: int = 100
    evidence_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", _normalize_text(self.rule_id))
        if not self.rule_id:
            raise ValueError("rule_id must be non-empty")
        if not isinstance(self.source_kind, ExtensionSourceKind):
            object.__setattr__(self, "source_kind", ExtensionSourceKind(str(self.source_kind)))
        if not isinstance(self.decision, ExtensionGateDecision):
            object.__setattr__(self, "decision", ExtensionGateDecision(str(self.decision)))
        object.__setattr__(self, "priority", int(self.priority))
        if self.priority < 0:
            raise ValueError("priority must be non-negative")
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))

    def as_payload(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "source_kind": self.source_kind.value,
            "decision": self.decision.value,
            "priority": self.priority,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass(frozen=True, slots=True)
class ExtensionGateResult:
    schema_version: str
    policy_schema_version: str
    source_kind: ExtensionSourceKind
    decision: ExtensionGateDecision
    reason_code: ExtensionGateReasonCode
    matched_rule_id: str | None = None
    evidence_paths: tuple[str, ...] = ()
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", validate_extension_schema_version(self.schema_version))
        object.__setattr__(self, "policy_schema_version", validate_extension_schema_version(self.policy_schema_version))
        if not isinstance(self.source_kind, ExtensionSourceKind):
            object.__setattr__(self, "source_kind", ExtensionSourceKind(str(self.source_kind)))
        if not isinstance(self.decision, ExtensionGateDecision):
            object.__setattr__(self, "decision", ExtensionGateDecision(str(self.decision)))
        if not isinstance(self.reason_code, ExtensionGateReasonCode):
            object.__setattr__(self, "reason_code", ExtensionGateReasonCode(str(self.reason_code)))
        object.__setattr__(self, "matched_rule_id", _normalize_optional_text(self.matched_rule_id))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "detail", _normalize_text(self.detail))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_schema_version": self.policy_schema_version,
            "source_kind": self.source_kind.value,
            "decision": self.decision.value,
            "reason_code": self.reason_code.value,
            "matched_rule_id": self.matched_rule_id,
            "evidence_paths": list(self.evidence_paths),
            "detail": self.detail,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ExtensionPolicyContract:
    schema_version: str
    extension_mode: ExtensionMode = ExtensionMode.DISABLED
    rules: tuple[ExtensionPolicyRule, ...] = ()

    def __post_init__(self) -> None:
        normalized_schema = validate_extension_schema_version(self.schema_version)
        major = normalized_schema.split(".", 1)[0]
        ordered_rules = tuple(sorted(self.rules, key=lambda rule: (rule.priority, rule.rule_id)))

        seen_rule_ids: set[str] = set()
        for rule in ordered_rules:
            rule_major = _extract_rule_major(rule.rule_id)
            if rule_major != major:
                raise ValueError(
                    f"rule_id '{rule.rule_id}' must be versioned with schema major v{major}.<id>"
                )
            if rule.rule_id in seen_rule_ids:
                raise ValueError(f"Duplicate rule_id '{rule.rule_id}'")
            seen_rule_ids.add(rule.rule_id)

        object.__setattr__(self, "schema_version", normalized_schema)
        if not isinstance(self.extension_mode, ExtensionMode):
            object.__setattr__(self, "extension_mode", ExtensionMode(str(self.extension_mode)))
        object.__setattr__(self, "rules", ordered_rules)

    def evaluate_source_kind(self, source_kind: ExtensionSourceKind) -> ExtensionGateResult:
        if not isinstance(source_kind, ExtensionSourceKind):
            source_kind = ExtensionSourceKind(str(source_kind))

        if source_kind is ExtensionSourceKind.LOCAL_FILE:
            return ExtensionGateResult(
                schema_version=EXTENSION_GATE_SCHEMA_VERSION,
                policy_schema_version=self.schema_version,
                source_kind=source_kind,
                decision=ExtensionGateDecision.ALLOW,
                reason_code=ExtensionGateReasonCode.POLICY_RULE_ALLOW,
                matched_rule_id=f"v{self.schema_version.split('.', 1)[0]}.local.baseline.allow",
                evidence_paths=("ingestion.local_file", "policy_contract.extension_mode"),
                detail="Local-file ingestion remains enabled under the extension contract.",
            )

        if self.extension_mode is ExtensionMode.DISABLED:
            return ExtensionGateResult(
                schema_version=EXTENSION_GATE_SCHEMA_VERSION,
                policy_schema_version=self.schema_version,
                source_kind=source_kind,
                decision=ExtensionGateDecision.BLOCK,
                reason_code=ExtensionGateReasonCode.EXTENSIONS_DISABLED,
                matched_rule_id=f"v{self.schema_version.split('.', 1)[0]}.mode.disabled",
                evidence_paths=("policy_contract.extension_mode",),
                detail="fail.closed: extension mode is disabled",
            )

        for rule in self.rules:
            if rule.source_kind is not source_kind:
                continue
            reason_code = (
                ExtensionGateReasonCode.POLICY_RULE_ALLOW
                if rule.decision is ExtensionGateDecision.ALLOW
                else ExtensionGateReasonCode.POLICY_RULE_BLOCK
            )
            return ExtensionGateResult(
                schema_version=EXTENSION_GATE_SCHEMA_VERSION,
                policy_schema_version=self.schema_version,
                source_kind=source_kind,
                decision=rule.decision,
                reason_code=reason_code,
                matched_rule_id=rule.rule_id,
                evidence_paths=rule.evidence_paths,
                detail=f"Applied extension policy rule {rule.rule_id}",
            )

        return ExtensionGateResult(
            schema_version=EXTENSION_GATE_SCHEMA_VERSION,
            policy_schema_version=self.schema_version,
            source_kind=source_kind,
            decision=ExtensionGateDecision.BLOCK,
            reason_code=ExtensionGateReasonCode.NO_MATCHING_RULE,
            matched_rule_id=f"v{self.schema_version.split('.', 1)[0]}.default.no-matching-rule",
            evidence_paths=("policy_contract.rules",),
            detail="fail.closed: no matching extension policy rule",
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "extension_mode": self.extension_mode.value,
            "rules": [rule.as_payload() for rule in self.rules],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def validate_extension_schema_version(schema_version: str) -> str:
    if not isinstance(schema_version, str):
        raise ValueError(f"schema_version must be str, got {type(schema_version).__name__}")
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise ValueError("schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != SUPPORTED_EXTENSION_SCHEMA_MAJOR:
        raise ValueError(
            f"Unsupported schema major version '{major}'. "
            f"Expected {SUPPORTED_EXTENSION_SCHEMA_MAJOR}.x"
        )
    return normalized


def parse_extension_policy_contract(
    policy_contract: ExtensionPolicyContract | Mapping[str, Any],
) -> ExtensionPolicyContract:
    if isinstance(policy_contract, ExtensionPolicyContract):
        return policy_contract
    if not isinstance(policy_contract, Mapping):
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            "policy_contract must be ExtensionPolicyContract or mapping payload",
            evidence_path="policy_contract",
            detail={"payload_type": type(policy_contract).__name__},
        )

    payload = _canonicalize_mapping(policy_contract)
    allowed_keys = {"schema_version", "extension_mode", "rules"}
    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        bad_key = unknown_keys[0]
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            f"Unsupported policy_contract field '{bad_key}'",
            evidence_path=f"policy_contract.{bad_key}",
        )

    schema_version = _extract_required_text(
        payload,
        key="schema_version",
        evidence_path="policy_contract.schema_version",
    )
    try:
        normalized_schema = validate_extension_schema_version(schema_version)
    except ValueError as exc:
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.UNSUPPORTED_SCHEMA_MAJOR,
            str(exc),
            evidence_path="policy_contract.schema_version",
            detail={"schema_version": schema_version},
        ) from exc

    extension_mode = payload.get("extension_mode", ExtensionMode.DISABLED.value)
    if not isinstance(extension_mode, str):
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            "policy_contract.extension_mode must be a string",
            evidence_path="policy_contract.extension_mode",
            detail={"value_type": type(extension_mode).__name__},
        )
    try:
        parsed_mode = ExtensionMode(_normalize_text(extension_mode))
    except ValueError as exc:
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            "policy_contract.extension_mode must be one of DISABLED|CONTROLLED",
            evidence_path="policy_contract.extension_mode",
            detail={"value": extension_mode},
        ) from exc

    raw_rules = payload.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            "policy_contract.rules must be a list",
            evidence_path="policy_contract.rules",
            detail={"value_type": type(raw_rules).__name__},
        )

    parsed_rules: list[ExtensionPolicyRule] = []
    seen_rule_ids: set[str] = set()
    for index, raw_rule in enumerate(raw_rules):
        path_prefix = f"policy_contract.rules[{index}]"
        if not isinstance(raw_rule, Mapping):
            raise ExtensionPolicyContractError(
                ExtensionContractErrorCode.INVALID_RULE_FIELD,
                "Each policy_contract.rules entry must be a mapping",
                evidence_path=path_prefix,
            )
        allowed_rule_fields = {"rule_id", "source_kind", "decision", "priority", "evidence_paths"}
        unknown_rule_fields = sorted(set(raw_rule) - allowed_rule_fields)
        if unknown_rule_fields:
            bad_field = unknown_rule_fields[0]
            raise ExtensionPolicyContractError(
                ExtensionContractErrorCode.INVALID_RULE_FIELD,
                f"Unsupported rules field '{bad_field}'",
                evidence_path=f"{path_prefix}.{bad_field}",
            )

        rule_id = _extract_required_text(
            raw_rule,
            key="rule_id",
            evidence_path=f"{path_prefix}.rule_id",
        )
        rule_major = _extract_rule_major(rule_id)
        if rule_major != normalized_schema.split(".", 1)[0]:
            raise ExtensionPolicyContractError(
                ExtensionContractErrorCode.INVALID_RULE_ID,
                f"rule_id '{rule_id}' must match schema major v{normalized_schema.split('.', 1)[0]}",
                evidence_path=f"{path_prefix}.rule_id",
            )
        if rule_id in seen_rule_ids:
            raise ExtensionPolicyContractError(
                ExtensionContractErrorCode.DUPLICATE_RULE_ID,
                f"Duplicate rule_id '{rule_id}'",
                evidence_path=f"{path_prefix}.rule_id",
            )
        seen_rule_ids.add(rule_id)

        source_kind = _extract_required_text(
            raw_rule,
            key="source_kind",
            evidence_path=f"{path_prefix}.source_kind",
        )
        decision = _extract_required_text(
            raw_rule,
            key="decision",
            evidence_path=f"{path_prefix}.decision",
        )
        priority = raw_rule.get("priority", 100)
        if not isinstance(priority, int):
            raise ExtensionPolicyContractError(
                ExtensionContractErrorCode.INVALID_RULE_FIELD,
                "rule priority must be an integer",
                evidence_path=f"{path_prefix}.priority",
                detail={"value_type": type(priority).__name__},
            )

        evidence_paths = raw_rule.get("evidence_paths", ())
        if isinstance(evidence_paths, list):
            evidence_paths = tuple(evidence_paths)
        if not isinstance(evidence_paths, tuple):
            raise ExtensionPolicyContractError(
                ExtensionContractErrorCode.INVALID_RULE_FIELD,
                "rule evidence_paths must be a tuple or list",
                evidence_path=f"{path_prefix}.evidence_paths",
                detail={"value_type": type(evidence_paths).__name__},
            )

        try:
            parsed_rules.append(
                ExtensionPolicyRule(
                    rule_id=rule_id,
                    source_kind=ExtensionSourceKind(source_kind),
                    decision=ExtensionGateDecision(decision),
                    priority=priority,
                    evidence_paths=evidence_paths,
                )
            )
        except (ValueError, TypeError) as exc:
            raise ExtensionPolicyContractError(
                ExtensionContractErrorCode.INVALID_RULE_FIELD,
                str(exc),
                evidence_path=path_prefix,
            ) from exc

    try:
        return ExtensionPolicyContract(
            schema_version=normalized_schema,
            extension_mode=parsed_mode,
            rules=tuple(parsed_rules),
        )
    except ValueError as exc:
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            str(exc),
            evidence_path="policy_contract",
        ) from exc


def parse_extension_policy_contract_fail_closed(
    policy_contract: ExtensionPolicyContract | Mapping[str, Any] | None,
    *,
    evidence_path: str = "extension_policy",
) -> tuple[ExtensionPolicyContract | None, ExtensionGateResult]:
    schema_major = SUPPORTED_EXTENSION_SCHEMA_MAJOR
    if policy_contract is None:
        return (
            None,
            ExtensionGateResult(
                schema_version=EXTENSION_GATE_SCHEMA_VERSION,
                policy_schema_version=EXTENSION_POLICY_SCHEMA_VERSION,
                source_kind=ExtensionSourceKind.URL,
                decision=ExtensionGateDecision.BLOCK,
                reason_code=ExtensionGateReasonCode.FAIL_CLOSED_MISSING_POLICY,
                matched_rule_id=f"v{schema_major}.policy.missing",
                evidence_paths=(evidence_path,),
                detail="fail.closed: extension policy artifact is missing",
            ),
        )

    try:
        parsed = parse_extension_policy_contract(policy_contract)
    except ExtensionPolicyContractError as exc:
        return (
            None,
            ExtensionGateResult(
                schema_version=EXTENSION_GATE_SCHEMA_VERSION,
                policy_schema_version=EXTENSION_POLICY_SCHEMA_VERSION,
                source_kind=ExtensionSourceKind.URL,
                decision=ExtensionGateDecision.NEEDS_REVIEW,
                reason_code=ExtensionGateReasonCode.FAIL_CLOSED_INVALID_POLICY,
                matched_rule_id=f"v{schema_major}.policy.invalid",
                evidence_paths=(exc.evidence_path or evidence_path,),
                detail=f"fail.closed: {exc.code.value}",
            ),
        )

    return (
        parsed,
        ExtensionGateResult(
            schema_version=EXTENSION_GATE_SCHEMA_VERSION,
            policy_schema_version=parsed.schema_version,
            source_kind=ExtensionSourceKind.URL,
            decision=ExtensionGateDecision.ALLOW,
            reason_code=ExtensionGateReasonCode.POLICY_VALIDATED,
            matched_rule_id=f"v{parsed.schema_version.split('.', 1)[0]}.policy.validated",
            evidence_paths=(f"{evidence_path}.schema_version",),
            detail="Extension policy contract parsed successfully",
        ),
    )


def _extract_required_text(
    payload: Mapping[str, Any],
    *,
    key: str,
    evidence_path: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            f"Field '{key}' must be a string",
            evidence_path=evidence_path,
            detail={"value_type": type(value).__name__},
        )
    normalized = _normalize_text(value)
    if not normalized:
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_POLICY_CONTRACT,
            f"Field '{key}' must be non-empty",
            evidence_path=evidence_path,
        )
    return normalized


def _extract_rule_major(rule_id: str) -> str:
    match = _VERSIONED_RULE_ID.match(rule_id)
    if match is None:
        raise ExtensionPolicyContractError(
            ExtensionContractErrorCode.INVALID_RULE_ID,
            f"rule_id '{rule_id}' must match v<major>.<stable-id> format",
            evidence_path="policy_contract.rules.rule_id",
        )
    return match.group("major")


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _normalize_text(value)
    return normalized or None


def _normalize_text(value: str) -> str:
    return value.strip()


def _normalize_sorted_text(values: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    normalized = {
        item.strip()
        for item in values
        if isinstance(item, str) and item.strip()
    }
    return tuple(sorted(normalized))


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
