"""Phase-4 deterministic fail-closed target validation gate."""

from __future__ import annotations

from typing import Any, Mapping

from intent_pipeline.phase4.contracts import (
    CapabilityMatrix,
    PHASE4_VALIDATION_SCHEMA_VERSION,
    PolicyContract,
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


_VALIDATION_RULE_IDS: tuple[str, ...] = (
    "VAL-RULE-001-SCHEMA-CHECKS",
    "VAL-RULE-002-TARGET-MAPPING",
    "VAL-RULE-003-CAPABILITY-COVERAGE",
    "VAL-RULE-004-POLICY-GATES",
)

_POLICY_CHECKS: tuple[str, ...] = (
    "schema_contracts",
    "route_to_tool_mapping",
    "tool_profile_support",
    "required_capabilities",
    "policy_decision_gate",
    "policy_rule_gate",
)


def validate_target(
    route_spec: Mapping[str, Any] | Any,
    capability_matrix: CapabilityMatrix | Mapping[str, Any],
    policy_contract: PolicyContract | Mapping[str, Any],
) -> ValidationReport:
    """Validate Phase-3 route target against typed capability + policy contracts."""
    issues: list[ValidationIssue] = []
    route_target = None
    matrix = None
    policy = None

    try:
        route_payload = _coerce_route_spec_payload(route_spec)
        route_target = parse_route_spec_target(route_payload)
    except ValidationContractError as error:
        issues.append(
            _build_block_issue(
                code=error.code,
                message=str(error),
                dominant_rule_id="UNKNOWN",
                evidence_paths=(
                    error.evidence_path,
                    "capability_matrix.tools",
                ),
                actual=_detail_value(error.detail, "schema_version"),
            )
        )
        route_payload = {}

    try:
        matrix = parse_capability_matrix(capability_matrix)
    except ValidationContractError as error:
        dominant_rule_id = route_target.dominant_rule_id if route_target is not None else "UNKNOWN"
        issues.append(
            _build_block_issue(
                code=error.code,
                message=str(error),
                dominant_rule_id=dominant_rule_id,
                evidence_paths=(
                    _route_evidence_path(route_target, fallback="route_spec.route_profile"),
                    error.evidence_path,
                ),
                actual=_detail_value(error.detail, "schema_version"),
            )
        )

    try:
        policy = parse_policy_contract(policy_contract)
    except ValidationContractError as error:
        dominant_rule_id = route_target.dominant_rule_id if route_target is not None else "UNKNOWN"
        issues.append(
            _build_block_issue(
                code=error.code,
                message=str(error),
                dominant_rule_id=dominant_rule_id,
                evidence_paths=(
                    _route_evidence_path(route_target, fallback="route_spec.route_profile"),
                    "capability_matrix.tools",
                ),
                actual=_detail_value(error.detail, "schema_version"),
            )
        )

    target_tool_id: str | None = None
    checked_capabilities: tuple[str, ...] = ()

    if route_target is not None and matrix is not None and policy is not None:
        route_profile = route_target.route_profile
        dominant_rule_id = route_target.dominant_rule_id

        target_tool_id = policy.target_tool_for(route_profile)
        if not target_tool_id:
            issues.append(
                _build_block_issue(
                    code=ValidationErrorCode.ROUTE_PROFILE_UNMAPPED,
                    message="No target tool mapping exists for route_profile",
                    dominant_rule_id=dominant_rule_id,
                    evidence_paths=(
                        "route_spec.route_profile",
                        "capability_matrix.tools",
                        f"policy_contract.route_to_tool::{route_profile}",
                    ),
                    expected="route_profile -> tool_id mapping",
                    actual=route_profile,
                )
            )
        else:
            tool = matrix.get_tool(target_tool_id)
            if tool is None:
                issues.append(
                    _build_block_issue(
                        code=ValidationErrorCode.TARGET_TOOL_MISSING,
                        message="Mapped target tool does not exist in capability_matrix",
                        dominant_rule_id=dominant_rule_id,
                        evidence_paths=(
                            "route_spec.route_profile",
                            f"capability_matrix.tools::{target_tool_id}",
                            f"policy_contract.route_to_tool::{route_profile}",
                        ),
                        expected=target_tool_id,
                        actual="missing",
                    )
                )
            else:
                checked_capabilities = policy.required_for_profile(route_profile)
                if route_profile not in tool.supported_route_profiles:
                    issues.append(
                        _build_block_issue(
                            code=ValidationErrorCode.ROUTE_PROFILE_UNSUPPORTED,
                            message="Target tool does not support route_profile",
                            dominant_rule_id=dominant_rule_id,
                            evidence_paths=(
                                "route_spec.route_profile",
                                f"capability_matrix.tools::{tool.tool_id}.supported_route_profiles",
                            ),
                            expected=route_profile,
                            actual=",".join(tool.supported_route_profiles),
                        )
                    )

                missing_capabilities = sorted(
                    capability for capability in checked_capabilities if capability not in tool.capabilities
                )
                for capability in missing_capabilities:
                    issues.append(
                        _build_block_issue(
                            code=ValidationErrorCode.REQUIRED_CAPABILITY_MISSING,
                            message="Required capability is missing from target tool",
                            dominant_rule_id=dominant_rule_id,
                            evidence_paths=(
                                "route_spec.route_profile",
                                f"capability_matrix.tools::{tool.tool_id}.capabilities::{capability}",
                                f"policy_contract.required_capabilities::{route_profile}",
                            ),
                            expected=capability,
                            actual="missing",
                        )
                    )

        if route_target.decision not in policy.allowed_route_decisions:
            capability_evidence = (
                f"capability_matrix.tools::{target_tool_id}"
                if target_tool_id
                else "capability_matrix.tools"
            )
            issues.append(
                _build_block_issue(
                    code=ValidationErrorCode.ROUTE_DECISION_BLOCKED,
                    message="Route decision is blocked by policy_contract",
                    dominant_rule_id=dominant_rule_id,
                    evidence_paths=(
                        "route_spec.decision",
                        capability_evidence,
                        "policy_contract.allowed_route_decisions",
                    ),
                    expected=",".join(policy.allowed_route_decisions),
                    actual=route_target.decision,
                )
            )

        if route_target.dominant_rule_id in set(policy.blocked_dominant_rule_ids):
            capability_evidence = (
                f"capability_matrix.tools::{target_tool_id}"
                if target_tool_id
                else "capability_matrix.tools"
            )
            issues.append(
                _build_block_issue(
                    code=ValidationErrorCode.POLICY_RULE_BLOCKED,
                    message="Dominant route rule is blocked by policy_contract",
                    dominant_rule_id=dominant_rule_id,
                    evidence_paths=(
                        "route_spec.dominant_rule_id",
                        capability_evidence,
                        "policy_contract.blocked_dominant_rule_ids",
                    ),
                    expected="not in blocked_dominant_rule_ids",
                    actual=route_target.dominant_rule_id,
                )
            )

    route_spec_schema_version = route_target.schema_version if route_target is not None else _coerce_text(route_payload.get("schema_version", ""))
    route_profile = route_target.route_profile if route_target is not None else _coerce_text(route_payload.get("route_profile", ""))
    dominant_rule_id = route_target.dominant_rule_id if route_target is not None else _coerce_text(route_payload.get("dominant_rule_id", "")) or "UNKNOWN"

    decision = ValidationDecision.BLOCK if issues else ValidationDecision.PASS
    can_proceed = decision is ValidationDecision.PASS
    applied_rule_ids = _unique_in_order((*_VALIDATION_RULE_IDS, dominant_rule_id))

    return ValidationReport(
        schema_version=PHASE4_VALIDATION_SCHEMA_VERSION,
        route_spec_schema_version=route_spec_schema_version or "unknown",
        decision=decision,
        can_proceed=can_proceed,
        route_profile=route_profile or "unknown",
        target_tool_id=target_tool_id,
        dominant_rule_id=dominant_rule_id,
        checked_capabilities=checked_capabilities,
        policy_checks=_POLICY_CHECKS,
        applied_rule_ids=applied_rule_ids,
        issues=tuple(issues),
    )


def _build_block_issue(
    *,
    code: ValidationErrorCode,
    message: str,
    dominant_rule_id: str,
    evidence_paths: tuple[str, ...],
    expected: str | None = None,
    actual: str | None = None,
) -> ValidationIssue:
    normalized_paths = tuple(path for path in (_coerce_text(entry) for entry in evidence_paths) if path)
    capability_paths = tuple(path for path in normalized_paths if path.startswith("capability_matrix."))
    route_paths = tuple(path for path in normalized_paths if path.startswith("route_spec."))

    if not capability_paths:
        capability_paths = ("capability_matrix.tools",)
    if not route_paths:
        route_paths = ("route_spec.route_profile",)

    return ValidationIssue(
        code=code,
        severity=ValidationSeverity.BLOCKER,
        message=message,
        dominant_rule_id=dominant_rule_id,
        evidence_paths=tuple((*route_paths, *capability_paths, *normalized_paths)),
        expected=expected,
        actual=actual,
    )


def _coerce_route_spec_payload(route_spec: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(route_spec, Mapping):
        return route_spec
    as_payload = getattr(route_spec, "as_payload", None)
    if callable(as_payload):
        payload = as_payload()
        if isinstance(payload, Mapping):
            return payload
    raise ValidationContractError(
        ValidationErrorCode.INVALID_ROUTE_SPEC_SCHEMA,
        "route_spec must be a mapping or support as_payload()",
        evidence_path="route_spec",
        detail={"payload_type": type(route_spec).__name__},
    )


def _detail_value(detail: Mapping[str, Any], key: str) -> str | None:
    value = detail.get(key)
    return value if isinstance(value, str) else None


def _route_evidence_path(route_target, *, fallback: str) -> str:
    if route_target is None:
        return fallback
    if route_target.route_profile:
        return "route_spec.route_profile"
    if route_target.dominant_rule_id:
        return "route_spec.dominant_rule_id"
    return fallback


def _coerce_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _unique_in_order(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for entry in values:
        normalized = _coerce_text(entry)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


__all__ = ["validate_target"]
