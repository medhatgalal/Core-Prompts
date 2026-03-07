"""Typed URL admission policy contracts and deterministic rejection logic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping

from .source_resolver import ResolvedSource, ResolvedSourceKind


URL_POLICY_SCHEMA_VERSION = "1.0.0"
SUPPORTED_URL_POLICY_SCHEMA_MAJOR = "1"


class UrlPolicyErrorCode(str, Enum):
    INVALID_POLICY_CONTRACT = "URL-POLICY-001-INVALID-CONTRACT"
    UNSUPPORTED_SCHEMA_MAJOR = "URL-POLICY-002-UNSUPPORTED-SCHEMA-MAJOR"
    INVALID_RULE_ID = "URL-POLICY-003-INVALID-RULE-ID"
    DUPLICATE_RULE_ID = "URL-POLICY-004-DUPLICATE-RULE-ID"
    INVALID_RULE_FIELD = "URL-POLICY-005-INVALID-RULE-FIELD"


class UrlRejectionCode(str, Enum):
    POLICY_REQUIRED = "URL-INGEST-001-POLICY-REQUIRED"
    INVALID_POLICY = "URL-INGEST-002-INVALID-POLICY"
    SOURCE_KIND_NOT_URL = "URL-INGEST-003-SOURCE-KIND-NOT-URL"
    DISALLOWED_SCHEME = "URL-INGEST-004-DISALLOWED-SCHEME"
    DISALLOWED_HOST = "URL-INGEST-005-DISALLOWED-HOST"
    DISALLOWED_PATH = "URL-INGEST-006-DISALLOWED-PATH"
    PRIVATE_ADDRESS_NOT_ALLOWED = "URL-INGEST-007-PRIVATE-ADDRESS-NOT-ALLOWED"
    CONTENT_TYPE_NOT_ALLOWED = "URL-INGEST-008-CONTENT-TYPE-NOT-ALLOWED"
    RESPONSE_TOO_LARGE = "URL-INGEST-009-RESPONSE-TOO-LARGE"
    REDIRECT_LIMIT_EXCEEDED = "URL-INGEST-010-REDIRECT-LIMIT-EXCEEDED"
    FETCH_FAILED = "URL-INGEST-011-FETCH-FAILED"
    TIMEOUT_LIMIT_EXCEEDED = "URL-INGEST-012-TIMEOUT-LIMIT-EXCEEDED"
    UNSUITABLE_CONTENT = "URL-INGEST-013-UNSUITABLE-CONTENT"


class UrlPolicyContractError(ValueError):
    """Typed URL policy parsing error."""

    def __init__(
        self,
        code: UrlPolicyErrorCode,
        message: str,
        *,
        evidence_path: str,
    ) -> None:
        normalized = _normalize_text(message) or code.value
        super().__init__(f"{code.value}: {normalized}")
        self.code = code
        self.evidence_path = _normalize_text(evidence_path)


@dataclass(frozen=True, slots=True)
class UrlRejection:
    code: UrlRejectionCode
    detail: str
    evidence_paths: tuple[str, ...] = ()
    normalized_source: str | None = None
    matched_rule_id: str | None = None
    terminal_status: str = "NEEDS_REVIEW"


class UrlSourceRejectedError(ValueError):
    """Raised when a URL source is rejected by deterministic admission policy."""

    def __init__(self, rejection: UrlRejection) -> None:
        super().__init__(f"{rejection.code.value}: {rejection.detail}")
        self.rejection = rejection


@dataclass(frozen=True, slots=True)
class UrlPolicyRule:
    rule_id: str
    allowed_schemes: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    allowed_path_prefixes: tuple[str, ...]
    allowed_content_types: tuple[str, ...]
    max_bytes: int
    redirect_limit: int
    timeout_seconds: int
    priority: int = 100
    evidence_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", _normalize_text(self.rule_id))
        object.__setattr__(self, "allowed_schemes", _normalize_lower_sorted(self.allowed_schemes))
        object.__setattr__(self, "allowed_hosts", _normalize_lower_sorted(self.allowed_hosts))
        object.__setattr__(self, "allowed_domains", _normalize_domain_suffixes(self.allowed_domains))
        object.__setattr__(self, "allowed_path_prefixes", _normalize_paths(self.allowed_path_prefixes))
        object.__setattr__(self, "allowed_content_types", _normalize_lower_sorted(self.allowed_content_types))
        object.__setattr__(self, "priority", int(self.priority))
        object.__setattr__(self, "max_bytes", int(self.max_bytes))
        object.__setattr__(self, "redirect_limit", int(self.redirect_limit))
        object.__setattr__(self, "timeout_seconds", int(self.timeout_seconds))
        object.__setattr__(self, "evidence_paths", tuple(sorted({_normalize_text(path) for path in self.evidence_paths if _normalize_text(path)})))
        if not self.rule_id:
            raise ValueError("rule_id is required")
        if not self.allowed_schemes:
            raise ValueError("allowed_schemes is required")
        if not self.allowed_content_types:
            raise ValueError("allowed_content_types is required")
        if not self.allowed_hosts and not self.allowed_domains:
            raise ValueError("At least one allowed_hosts or allowed_domains entry is required")
        if self.max_bytes <= 0:
            raise ValueError("max_bytes must be > 0")
        if self.redirect_limit < 0:
            raise ValueError("redirect_limit must be >= 0")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")

    def matches_source(self, source: ResolvedSource) -> bool:
        if source.kind is not ResolvedSourceKind.URL:
            return False
        assert source.scheme is not None
        assert source.host is not None
        path = source.path or "/"
        if source.scheme not in self.allowed_schemes:
            return False
        if not self._matches_host(source.host):
            return False
        if self.allowed_path_prefixes and not any(path.startswith(prefix) for prefix in self.allowed_path_prefixes):
            return False
        return True

    def allows_content_type(self, content_type: str) -> bool:
        normalized = _normalize_content_type(content_type)
        return normalized in self.allowed_content_types

    def _matches_host(self, host: str) -> bool:
        if host in self.allowed_hosts:
            return True
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    def as_payload(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "allowed_schemes": list(self.allowed_schemes),
            "allowed_hosts": list(self.allowed_hosts),
            "allowed_domains": list(self.allowed_domains),
            "allowed_path_prefixes": list(self.allowed_path_prefixes),
            "allowed_content_types": list(self.allowed_content_types),
            "max_bytes": self.max_bytes,
            "redirect_limit": self.redirect_limit,
            "timeout_seconds": self.timeout_seconds,
            "priority": self.priority,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass(frozen=True, slots=True)
class UrlPolicyContract:
    schema_version: str
    rules: tuple[UrlPolicyRule, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", validate_url_policy_schema_version(self.schema_version))
        object.__setattr__(self, "rules", tuple(sorted(self.rules, key=lambda rule: (rule.priority, rule.rule_id))))

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "rules": [rule.as_payload() for rule in self.rules],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class UrlPolicyEvaluation:
    accepted: bool
    rule: UrlPolicyRule | None = None
    rejection: UrlRejection | None = None

    def require_rule(self) -> UrlPolicyRule:
        if self.rule is None:
            if self.rejection is None:
                raise RuntimeError("Rejected evaluation requires rejection detail.")
            raise UrlSourceRejectedError(self.rejection)
        return self.rule


def validate_url_policy_schema_version(schema_version: str) -> str:
    if not isinstance(schema_version, str):
        raise ValueError(f"schema_version must be str, got {type(schema_version).__name__}")
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise ValueError("schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != SUPPORTED_URL_POLICY_SCHEMA_MAJOR:
        raise ValueError(
            f"Unsupported schema major version '{major}'. Expected {SUPPORTED_URL_POLICY_SCHEMA_MAJOR}.x"
        )
    return normalized


def parse_url_policy_contract(policy_contract: UrlPolicyContract | Mapping[str, Any]) -> UrlPolicyContract:
    if isinstance(policy_contract, UrlPolicyContract):
        return policy_contract
    if not isinstance(policy_contract, Mapping):
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.INVALID_POLICY_CONTRACT,
            "policy_contract must be UrlPolicyContract or mapping payload",
            evidence_path="url_policy",
        )

    payload = _canonicalize_mapping(policy_contract)
    allowed_keys = {"schema_version", "rules"}
    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.INVALID_POLICY_CONTRACT,
            f"Unsupported policy_contract field '{unknown_keys[0]}'",
            evidence_path=f"url_policy.{unknown_keys[0]}",
        )

    schema_version = _extract_required_text(
        payload,
        key="schema_version",
        evidence_path="url_policy.schema_version",
    )
    try:
        normalized_schema = validate_url_policy_schema_version(schema_version)
    except ValueError as exc:
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.UNSUPPORTED_SCHEMA_MAJOR,
            str(exc),
            evidence_path="url_policy.schema_version",
        ) from exc

    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.INVALID_POLICY_CONTRACT,
            "url_policy.rules must be a non-empty list",
            evidence_path="url_policy.rules",
        )

    parsed_rules: list[UrlPolicyRule] = []
    seen_rule_ids: set[str] = set()
    for index, raw_rule in enumerate(raw_rules):
        path_prefix = f"url_policy.rules[{index}]"
        if not isinstance(raw_rule, Mapping):
            raise UrlPolicyContractError(
                UrlPolicyErrorCode.INVALID_RULE_FIELD,
                "Each url_policy.rules entry must be a mapping",
                evidence_path=path_prefix,
            )
        allowed_rule_fields = {
            "rule_id",
            "allowed_schemes",
            "allowed_hosts",
            "allowed_domains",
            "allowed_path_prefixes",
            "allowed_content_types",
            "max_bytes",
            "redirect_limit",
            "timeout_seconds",
            "priority",
            "evidence_paths",
        }
        unknown_rule_fields = sorted(set(raw_rule) - allowed_rule_fields)
        if unknown_rule_fields:
            raise UrlPolicyContractError(
                UrlPolicyErrorCode.INVALID_RULE_FIELD,
                f"Unsupported rule field '{unknown_rule_fields[0]}'",
                evidence_path=f"{path_prefix}.{unknown_rule_fields[0]}",
            )

        rule_id = _extract_required_text(raw_rule, key="rule_id", evidence_path=f"{path_prefix}.rule_id")
        if not rule_id.startswith(f"v{normalized_schema.split('.', 1)[0]}."):
            raise UrlPolicyContractError(
                UrlPolicyErrorCode.INVALID_RULE_ID,
                f"rule_id '{rule_id}' must match schema major v{normalized_schema.split('.', 1)[0]}",
                evidence_path=f"{path_prefix}.rule_id",
            )
        if rule_id in seen_rule_ids:
            raise UrlPolicyContractError(
                UrlPolicyErrorCode.DUPLICATE_RULE_ID,
                f"Duplicate rule_id '{rule_id}'",
                evidence_path=f"{path_prefix}.rule_id",
            )
        seen_rule_ids.add(rule_id)
        try:
            parsed_rules.append(
                UrlPolicyRule(
                    rule_id=rule_id,
                    allowed_schemes=_extract_text_sequence(raw_rule, key="allowed_schemes", evidence_path=f"{path_prefix}.allowed_schemes"),
                    allowed_hosts=_extract_optional_text_sequence(raw_rule, key="allowed_hosts", evidence_path=f"{path_prefix}.allowed_hosts"),
                    allowed_domains=_extract_optional_text_sequence(raw_rule, key="allowed_domains", evidence_path=f"{path_prefix}.allowed_domains"),
                    allowed_path_prefixes=_extract_optional_text_sequence(raw_rule, key="allowed_path_prefixes", evidence_path=f"{path_prefix}.allowed_path_prefixes"),
                    allowed_content_types=_extract_text_sequence(raw_rule, key="allowed_content_types", evidence_path=f"{path_prefix}.allowed_content_types"),
                    max_bytes=_extract_int(raw_rule, key="max_bytes", evidence_path=f"{path_prefix}.max_bytes"),
                    redirect_limit=_extract_int(raw_rule, key="redirect_limit", evidence_path=f"{path_prefix}.redirect_limit"),
                    timeout_seconds=_extract_int(raw_rule, key="timeout_seconds", evidence_path=f"{path_prefix}.timeout_seconds"),
                    priority=int(raw_rule.get("priority", 100)),
                    evidence_paths=_extract_optional_text_sequence(raw_rule, key="evidence_paths", evidence_path=f"{path_prefix}.evidence_paths"),
                )
            )
        except (TypeError, ValueError) as exc:
            raise UrlPolicyContractError(
                UrlPolicyErrorCode.INVALID_RULE_FIELD,
                str(exc),
                evidence_path=path_prefix,
            ) from exc

    return UrlPolicyContract(schema_version=normalized_schema, rules=tuple(parsed_rules))


def parse_url_policy_contract_fail_closed(
    policy_contract: UrlPolicyContract | Mapping[str, Any] | None,
    *,
    normalized_source: str,
) -> tuple[UrlPolicyContract | None, UrlRejection | None]:
    if policy_contract is None:
        return (
            None,
            UrlRejection(
                code=UrlRejectionCode.POLICY_REQUIRED,
                detail="fail.closed: url policy artifact is missing",
                evidence_paths=("url_policy",),
                normalized_source=normalized_source,
            ),
        )

    try:
        parsed = parse_url_policy_contract(policy_contract)
    except UrlPolicyContractError as exc:
        return (
            None,
            UrlRejection(
                code=UrlRejectionCode.INVALID_POLICY,
                detail=f"fail.closed: {exc.code.value}",
                evidence_paths=(exc.evidence_path,),
                normalized_source=normalized_source,
            ),
        )
    return parsed, None


def evaluate_url_policy(
    source: ResolvedSource,
    policy_contract: UrlPolicyContract | Mapping[str, Any] | None,
) -> UrlPolicyEvaluation:
    if source.kind is not ResolvedSourceKind.URL:
        return UrlPolicyEvaluation(
            accepted=False,
            rejection=UrlRejection(
                code=UrlRejectionCode.SOURCE_KIND_NOT_URL,
                detail="Resolved source kind must be URL.",
                evidence_paths=("source.kind",),
                normalized_source=source.normalized_source,
            ),
        )

    policy, rejection = parse_url_policy_contract_fail_closed(
        policy_contract,
        normalized_source=source.normalized_source,
    )
    if rejection is not None:
        return UrlPolicyEvaluation(accepted=False, rejection=rejection)

    assert policy is not None
    assert source.scheme is not None
    assert source.host is not None

    scheme_rules = [rule for rule in policy.rules if source.scheme in rule.allowed_schemes]
    if not scheme_rules:
        return UrlPolicyEvaluation(
            accepted=False,
            rejection=UrlRejection(
                code=UrlRejectionCode.DISALLOWED_SCHEME,
                detail=f"Scheme '{source.scheme}' is not allowed.",
                evidence_paths=("url_policy.rules.allowed_schemes",),
                normalized_source=source.normalized_source,
            ),
        )

    host_rules = [rule for rule in scheme_rules if rule._matches_host(source.host)]
    if not host_rules:
        return UrlPolicyEvaluation(
            accepted=False,
            rejection=UrlRejection(
                code=UrlRejectionCode.DISALLOWED_HOST,
                detail=f"Host '{source.host}' is not allowed.",
                evidence_paths=("url_policy.rules.allowed_hosts", "url_policy.rules.allowed_domains"),
                normalized_source=source.normalized_source,
            ),
        )

    path_rules = [rule for rule in host_rules if rule.matches_source(source)]
    if not path_rules:
        return UrlPolicyEvaluation(
            accepted=False,
            rejection=UrlRejection(
                code=UrlRejectionCode.DISALLOWED_PATH,
                detail=f"Path '{source.path or '/'}' is not allowed.",
                evidence_paths=("url_policy.rules.allowed_path_prefixes",),
                normalized_source=source.normalized_source,
            ),
        )

    return UrlPolicyEvaluation(accepted=True, rule=path_rules[0])


def reject_private_address(source: ResolvedSource, address: str, *, matched_rule_id: str) -> UrlRejection:
    return UrlRejection(
        code=UrlRejectionCode.PRIVATE_ADDRESS_NOT_ALLOWED,
        detail=f"Resolved address '{address}' is not allowed for URL ingestion.",
        evidence_paths=("url_resolution.addresses",),
        normalized_source=source.normalized_source,
        matched_rule_id=matched_rule_id,
    )


def reject_content_type(source: ResolvedSource, content_type: str, *, matched_rule_id: str) -> UrlRejection:
    return UrlRejection(
        code=UrlRejectionCode.CONTENT_TYPE_NOT_ALLOWED,
        detail=f"Content type '{content_type}' is not allowed.",
        evidence_paths=("response.headers.content-type",),
        normalized_source=source.normalized_source,
        matched_rule_id=matched_rule_id,
    )


def reject_response_too_large(source: ResolvedSource, size: int, *, matched_rule_id: str) -> UrlRejection:
    return UrlRejection(
        code=UrlRejectionCode.RESPONSE_TOO_LARGE,
        detail=f"Response exceeded allowed size: {size} bytes.",
        evidence_paths=("response.body",),
        normalized_source=source.normalized_source,
        matched_rule_id=matched_rule_id,
    )


def reject_redirect_limit(source: ResolvedSource, *, matched_rule_id: str) -> UrlRejection:
    return UrlRejection(
        code=UrlRejectionCode.REDIRECT_LIMIT_EXCEEDED,
        detail="Redirect limit exceeded.",
        evidence_paths=("response.redirect",),
        normalized_source=source.normalized_source,
        matched_rule_id=matched_rule_id,
    )


def reject_fetch_failed(source: ResolvedSource, detail: str, *, matched_rule_id: str | None = None) -> UrlRejection:
    return UrlRejection(
        code=UrlRejectionCode.FETCH_FAILED,
        detail=detail,
        evidence_paths=("url_fetch",),
        normalized_source=source.normalized_source,
        matched_rule_id=matched_rule_id,
    )


def reject_timeout_limit(source: ResolvedSource, *, matched_rule_id: str | None = None) -> UrlRejection:
    return UrlRejection(
        code=UrlRejectionCode.TIMEOUT_LIMIT_EXCEEDED,
        detail="Fetch timeout exceeded configured limit.",
        evidence_paths=("url_fetch.timeout_seconds",),
        normalized_source=source.normalized_source,
        matched_rule_id=matched_rule_id,
    )


def reject_unsuitable_content(
    source: ResolvedSource,
    detail: str,
    *,
    matched_rule_id: str | None = None,
    evidence_paths: tuple[str, ...] = ("source_suitability",),
) -> UrlRejection:
    return UrlRejection(
        code=UrlRejectionCode.UNSUITABLE_CONTENT,
        detail=detail,
        evidence_paths=evidence_paths,
        normalized_source=source.normalized_source,
        matched_rule_id=matched_rule_id,
        terminal_status="REJECTED",
    )


def _extract_required_text(payload: Mapping[str, Any], *, key: str, evidence_path: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not _normalize_text(value):
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.INVALID_POLICY_CONTRACT,
            f"Field '{key}' must be a non-empty string",
            evidence_path=evidence_path,
        )
    return _normalize_text(value)


def _extract_text_sequence(payload: Mapping[str, Any], *, key: str, evidence_path: str) -> tuple[str, ...]:
    values = payload.get(key)
    if not isinstance(values, (list, tuple)) or not values:
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.INVALID_RULE_FIELD,
            f"Field '{key}' must be a non-empty list",
            evidence_path=evidence_path,
        )
    return tuple(str(value) for value in values)


def _extract_optional_text_sequence(
    payload: Mapping[str, Any],
    *,
    key: str,
    evidence_path: str,
) -> tuple[str, ...]:
    values = payload.get(key, ())
    if values == ():
        return ()
    if not isinstance(values, (list, tuple)):
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.INVALID_RULE_FIELD,
            f"Field '{key}' must be a list when provided",
            evidence_path=evidence_path,
        )
    return tuple(str(value) for value in values)


def _extract_int(payload: Mapping[str, Any], *, key: str, evidence_path: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise UrlPolicyContractError(
            UrlPolicyErrorCode.INVALID_RULE_FIELD,
            f"Field '{key}' must be an integer",
            evidence_path=evidence_path,
        )
    return value


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_lower_sorted(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(sorted({_normalize_text(value).lower() for value in values if _normalize_text(value)}))


def _normalize_domain_suffixes(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized: set[str] = set()
    for value in values:
        text = _normalize_text(value).lower().lstrip(".")
        if text:
            normalized.add(text)
    return tuple(sorted(normalized))


def _normalize_paths(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized: set[str] = set()
    for value in values:
        text = _normalize_text(value)
        if not text:
            continue
        normalized.add(text if text.startswith("/") else f"/{text}")
    return tuple(sorted(normalized))


def _normalize_content_type(value: str) -> str:
    return _normalize_text(value).split(";", 1)[0].lower()


def _canonicalize_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {key: _canonicalize_value(data[key]) for key in sorted(data)}


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _canonicalize_mapping(value)
    if isinstance(value, list):
        return [_canonicalize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_canonicalize_value(item) for item in value]
    return value


__all__ = [
    "URL_POLICY_SCHEMA_VERSION",
    "SUPPORTED_URL_POLICY_SCHEMA_MAJOR",
    "UrlPolicyContract",
    "UrlPolicyContractError",
    "UrlPolicyErrorCode",
    "UrlPolicyEvaluation",
    "UrlPolicyRule",
    "UrlRejection",
    "UrlRejectionCode",
    "UrlSourceRejectedError",
    "evaluate_url_policy",
    "parse_url_policy_contract",
    "parse_url_policy_contract_fail_closed",
    "reject_content_type",
    "reject_fetch_failed",
    "reject_private_address",
    "reject_redirect_limit",
    "reject_response_too_large",
    "reject_timeout_limit",
    "reject_unsuitable_content",
]
