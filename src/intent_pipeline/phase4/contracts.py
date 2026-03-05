"""Phase-4 typed validation contracts and coercion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping


PHASE4_VALIDATION_SCHEMA_VERSION = "4.0.0"
SUPPORTED_PHASE4_SCHEMA_MAJOR = "4"
SUPPORTED_ROUTE_SPEC_SCHEMA_MAJOR = "3"
PHASE4_MOCK_SCHEMA_VERSION = "4.0.0"


class ValidationDecision(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"


class ValidationSeverity(str, Enum):
    BLOCKER = "BLOCKER"


class ValidationErrorCode(str, Enum):
    INVALID_ROUTE_SPEC_SCHEMA = "VAL-001-INVALID-ROUTE-SPEC-SCHEMA"
    INVALID_CAPABILITY_MATRIX_SCHEMA = "VAL-002-INVALID-CAPABILITY-MATRIX-SCHEMA"
    INVALID_POLICY_CONTRACT_SCHEMA = "VAL-003-INVALID-POLICY-CONTRACT-SCHEMA"
    FREEFORM_CAPABILITY_METADATA_PATH = "VAL-004-FREEFORM-CAPABILITY-METADATA-PATH"
    ROUTE_PROFILE_UNMAPPED = "VAL-005-ROUTE-PROFILE-UNMAPPED"
    TARGET_TOOL_MISSING = "VAL-006-TARGET-TOOL-MISSING"
    ROUTE_PROFILE_UNSUPPORTED = "VAL-007-ROUTE-PROFILE-UNSUPPORTED"
    REQUIRED_CAPABILITY_MISSING = "VAL-008-REQUIRED-CAPABILITY-MISSING"
    POLICY_RULE_BLOCKED = "VAL-009-POLICY-RULE-BLOCKED"
    ROUTE_DECISION_BLOCKED = "VAL-010-ROUTE-DECISION-BLOCKED"


class MockDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class MockStage(str, Enum):
    PRECHECK = "PRECHECK"
    PLAN = "PLAN"
    SIMULATE = "SIMULATE"
    VERIFY = "VERIFY"


MOCK_STAGE_ORDER: tuple[MockStage, ...] = (
    MockStage.PRECHECK,
    MockStage.PLAN,
    MockStage.SIMULATE,
    MockStage.VERIFY,
)


class MockStepStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


class MockErrorCode(str, Enum):
    VALIDATION_NOT_PASS = "MOCK-001-VALIDATION-NOT-PASS"
    TARGET_TOOL_UNRESOLVED = "MOCK-002-TARGET-TOOL-UNRESOLVED"
    CAPABILITY_EVIDENCE_MISSING = "MOCK-003-CAPABILITY-EVIDENCE-MISSING"
    UNSUPPORTED_STAGE = "MOCK-004-UNSUPPORTED-STAGE"


class ValidationContractError(ValueError):
    """Typed contract coercion error used to fail closed in validator."""

    def __init__(
        self,
        code: ValidationErrorCode,
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
class RouteSpecTarget:
    schema_version: str
    decision: str
    route_profile: str
    dominant_rule_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_ROUTE_SPEC_SCHEMA_MAJOR))
        object.__setattr__(self, "decision", _normalize_text(self.decision))
        object.__setattr__(self, "route_profile", _normalize_text(self.route_profile))
        object.__setattr__(self, "dominant_rule_id", _normalize_text(self.dominant_rule_id))


@dataclass(frozen=True, slots=True)
class ToolCapability:
    tool_id: str
    supported_route_profiles: tuple[str, ...]
    capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "tool_id", _normalize_text(self.tool_id))
        object.__setattr__(self, "supported_route_profiles", _normalize_sorted_text(self.supported_route_profiles))
        object.__setattr__(self, "capabilities", _normalize_sorted_text(self.capabilities))

    def as_payload(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "supported_route_profiles": list(self.supported_route_profiles),
            "capabilities": list(self.capabilities),
        }


@dataclass(frozen=True, slots=True)
class CapabilityMatrix:
    schema_version: str
    tools: tuple[ToolCapability, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE4_SCHEMA_MAJOR))
        ordered = sorted(self.tools, key=lambda entry: entry.tool_id)
        object.__setattr__(self, "tools", tuple(ordered))

    def get_tool(self, tool_id: str) -> ToolCapability | None:
        normalized_tool_id = _normalize_text(tool_id)
        for entry in self.tools:
            if entry.tool_id == normalized_tool_id:
                return entry
        return None

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tools": [entry.as_payload() for entry in self.tools],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class RouteToolBinding:
    route_profile: str
    tool_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_profile", _normalize_text(self.route_profile))
        object.__setattr__(self, "tool_id", _normalize_text(self.tool_id))

    def as_payload(self) -> dict[str, str]:
        return {
            "route_profile": self.route_profile,
            "tool_id": self.tool_id,
        }


@dataclass(frozen=True, slots=True)
class RequiredCapabilityBinding:
    route_profile: str
    capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_profile", _normalize_text(self.route_profile))
        object.__setattr__(self, "capabilities", _normalize_sorted_text(self.capabilities))

    def as_payload(self) -> dict[str, Any]:
        return {
            "route_profile": self.route_profile,
            "capabilities": list(self.capabilities),
        }


@dataclass(frozen=True, slots=True)
class PolicyContract:
    schema_version: str
    route_to_tool: tuple[RouteToolBinding, ...]
    required_capabilities: tuple[RequiredCapabilityBinding, ...]
    blocked_dominant_rule_ids: tuple[str, ...] = ()
    allowed_route_decisions: tuple[str, ...] = ("PASS_ROUTE",)

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE4_SCHEMA_MAJOR))
        object.__setattr__(self, "route_to_tool", tuple(sorted(self.route_to_tool, key=lambda entry: entry.route_profile)))
        object.__setattr__(self, "required_capabilities", tuple(sorted(self.required_capabilities, key=lambda entry: entry.route_profile)))
        object.__setattr__(self, "blocked_dominant_rule_ids", _normalize_sorted_text(self.blocked_dominant_rule_ids))
        object.__setattr__(self, "allowed_route_decisions", _normalize_sorted_text(self.allowed_route_decisions))

    def target_tool_for(self, route_profile: str) -> str | None:
        normalized_profile = _normalize_text(route_profile)
        for binding in self.route_to_tool:
            if binding.route_profile == normalized_profile:
                return binding.tool_id
        return None

    def required_for_profile(self, route_profile: str) -> tuple[str, ...]:
        normalized_profile = _normalize_text(route_profile)
        for binding in self.required_capabilities:
            if binding.route_profile == normalized_profile:
                return binding.capabilities
        return ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "route_to_tool": [entry.as_payload() for entry in self.route_to_tool],
            "required_capabilities": [entry.as_payload() for entry in self.required_capabilities],
            "blocked_dominant_rule_ids": list(self.blocked_dominant_rule_ids),
            "allowed_route_decisions": list(self.allowed_route_decisions),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: ValidationErrorCode
    severity: ValidationSeverity
    message: str
    dominant_rule_id: str
    evidence_paths: tuple[str, ...]
    expected: str | None = None
    actual: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, ValidationErrorCode):
            object.__setattr__(self, "code", ValidationErrorCode(str(self.code)))
        if not isinstance(self.severity, ValidationSeverity):
            object.__setattr__(self, "severity", ValidationSeverity(str(self.severity)))
        object.__setattr__(self, "message", _normalize_text(self.message))
        object.__setattr__(self, "dominant_rule_id", _normalize_text(self.dominant_rule_id))
        canonical_paths = _normalize_sorted_text(self.evidence_paths)
        if self.severity is ValidationSeverity.BLOCKER:
            has_route_path = any(path.startswith("route_spec.") for path in canonical_paths)
            has_capability_path = any(path.startswith("capability_matrix.") for path in canonical_paths)
            if not has_route_path or not has_capability_path:
                raise ValueError("BLOCKER issues must include route_spec and capability_matrix evidence paths")
        object.__setattr__(self, "evidence_paths", canonical_paths)
        object.__setattr__(self, "expected", _normalize_optional_text(self.expected))
        object.__setattr__(self, "actual", _normalize_optional_text(self.actual))

    def as_payload(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "dominant_rule_id": self.dominant_rule_id,
            "evidence_paths": list(self.evidence_paths),
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    schema_version: str
    route_spec_schema_version: str
    decision: ValidationDecision
    can_proceed: bool
    route_profile: str
    target_tool_id: str | None
    dominant_rule_id: str
    checked_capabilities: tuple[str, ...]
    policy_checks: tuple[str, ...]
    applied_rule_ids: tuple[str, ...]
    issues: tuple[ValidationIssue, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE4_SCHEMA_MAJOR))
        object.__setattr__(self, "route_spec_schema_version", _normalize_text(self.route_spec_schema_version))
        if not isinstance(self.decision, ValidationDecision):
            object.__setattr__(self, "decision", ValidationDecision(str(self.decision)))
        object.__setattr__(self, "can_proceed", bool(self.can_proceed))
        object.__setattr__(self, "route_profile", _normalize_text(self.route_profile))
        object.__setattr__(self, "target_tool_id", _normalize_optional_text(self.target_tool_id))
        object.__setattr__(self, "dominant_rule_id", _normalize_text(self.dominant_rule_id))
        object.__setattr__(self, "checked_capabilities", _normalize_sorted_text(self.checked_capabilities))
        object.__setattr__(self, "policy_checks", _normalize_sorted_text(self.policy_checks))
        object.__setattr__(self, "applied_rule_ids", _unique_in_order(self.applied_rule_ids))
        ordered_issues = sorted(
            self.issues,
            key=lambda issue: (
                issue.code.value,
                issue.evidence_paths,
                issue.expected or "",
                issue.actual or "",
                issue.message,
            ),
        )
        object.__setattr__(self, "issues", tuple(ordered_issues))
        if self.decision is ValidationDecision.PASS and self.issues:
            raise ValueError("PASS validation reports cannot include issues")
        if self.decision is ValidationDecision.BLOCK and not self.issues:
            raise ValueError("BLOCK validation reports must include issues")
        if self.decision is ValidationDecision.PASS and not self.can_proceed:
            raise ValueError("PASS reports must allow proceeding")
        if self.decision is ValidationDecision.BLOCK and self.can_proceed:
            raise ValueError("BLOCK reports must fail closed")

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "route_spec_schema_version": self.route_spec_schema_version,
            "decision": self.decision.value,
            "can_proceed": self.can_proceed,
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "dominant_rule_id": self.dominant_rule_id,
            "checked_capabilities": list(self.checked_capabilities),
            "policy_checks": list(self.policy_checks),
            "applied_rule_ids": list(self.applied_rule_ids),
            "issues": [issue.as_payload() for issue in self.issues],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class MockStep:
    stage: MockStage
    status: MockStepStatus
    rule_id: str
    action: str
    evidence_paths: tuple[str, ...]
    produced_artifacts: tuple[str, ...] = ()
    error_code: MockErrorCode | None = None
    details: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage, MockStage):
            object.__setattr__(self, "stage", MockStage(str(self.stage)))
        if not isinstance(self.status, MockStepStatus):
            object.__setattr__(self, "status", MockStepStatus(str(self.status)))
        object.__setattr__(self, "rule_id", _normalize_text(self.rule_id))
        object.__setattr__(self, "action", _normalize_text(self.action))
        object.__setattr__(self, "evidence_paths", _normalize_sorted_text(self.evidence_paths))
        object.__setattr__(self, "produced_artifacts", _normalize_sorted_text(self.produced_artifacts))
        if self.error_code is not None and not isinstance(self.error_code, MockErrorCode):
            object.__setattr__(self, "error_code", MockErrorCode(str(self.error_code)))
        object.__setattr__(self, "details", _normalize_optional_text(self.details))

        if self.status is MockStepStatus.FAIL and self.error_code is None:
            raise ValueError("FAIL mock steps require typed error_code")
        if self.status is not MockStepStatus.FAIL and self.error_code is not None:
            raise ValueError("Only FAIL mock steps can carry error_code")

        if self.status is MockStepStatus.FAIL:
            has_route = any(path.startswith("route_spec.") for path in self.evidence_paths)
            has_capability = any(path.startswith("capability_matrix.") for path in self.evidence_paths)
            has_validation = any(path.startswith("validation_report.") for path in self.evidence_paths)
            has_step = any(path.startswith("mock_trace.steps.") for path in self.evidence_paths)
            if not (has_route and has_capability and has_validation and has_step):
                raise ValueError(
                    "FAIL mock steps must include route_spec, capability_matrix, validation_report, and mock_trace.steps evidence paths"
                )

    def as_payload(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "rule_id": self.rule_id,
            "action": self.action,
            "evidence_paths": list(self.evidence_paths),
            "produced_artifacts": list(self.produced_artifacts),
            "error_code": self.error_code.value if self.error_code is not None else None,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class MockTrace:
    schema_version: str
    decision: MockDecision
    route_profile: str
    target_tool_id: str | None
    dominant_rule_id: str
    applied_rule_ids: tuple[str, ...]
    steps: tuple[MockStep, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", _validate_schema_major(self.schema_version, SUPPORTED_PHASE4_SCHEMA_MAJOR))
        if not isinstance(self.decision, MockDecision):
            object.__setattr__(self, "decision", MockDecision(str(self.decision)))
        object.__setattr__(self, "route_profile", _normalize_text(self.route_profile))
        object.__setattr__(self, "target_tool_id", _normalize_optional_text(self.target_tool_id))
        object.__setattr__(self, "dominant_rule_id", _normalize_text(self.dominant_rule_id))
        object.__setattr__(self, "applied_rule_ids", _unique_in_order(self.applied_rule_ids))

        if len(self.steps) != len(MOCK_STAGE_ORDER):
            raise ValueError("MockTrace must include exactly one step for each fixed stage")
        stage_order = tuple(step.stage for step in self.steps)
        if stage_order != MOCK_STAGE_ORDER:
            raise ValueError("MockTrace step order must follow PRECHECK, PLAN, SIMULATE, VERIFY")

        has_failure = any(step.status is MockStepStatus.FAIL for step in self.steps)
        if self.decision is MockDecision.PASS and has_failure:
            raise ValueError("MockTrace PASS decision cannot include failing steps")
        if self.decision is MockDecision.FAIL and not has_failure:
            raise ValueError("MockTrace FAIL decision must include at least one failing step")

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "route_profile": self.route_profile,
            "target_tool_id": self.target_tool_id,
            "dominant_rule_id": self.dominant_rule_id,
            "applied_rule_ids": list(self.applied_rule_ids),
            "steps": [step.as_payload() for step in self.steps],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


def parse_route_spec_target(route_spec: Mapping[str, Any]) -> RouteSpecTarget:
    if not isinstance(route_spec, Mapping):
        raise ValidationContractError(
            ValidationErrorCode.INVALID_ROUTE_SPEC_SCHEMA,
            "route_spec must be a mapping payload",
            evidence_path="route_spec",
            detail={"payload_type": type(route_spec).__name__},
        )
    schema_version = _extract_required_text(
        route_spec,
        key="schema_version",
        code=ValidationErrorCode.INVALID_ROUTE_SPEC_SCHEMA,
        evidence_path="route_spec.schema_version",
    )
    try:
        normalized_schema = _validate_schema_major(schema_version, SUPPORTED_ROUTE_SPEC_SCHEMA_MAJOR)
    except ValueError as exc:
        raise ValidationContractError(
            ValidationErrorCode.INVALID_ROUTE_SPEC_SCHEMA,
            str(exc),
            evidence_path="route_spec.schema_version",
            detail={"schema_version": schema_version},
        ) from exc
    decision = _extract_required_text(
        route_spec,
        key="decision",
        code=ValidationErrorCode.INVALID_ROUTE_SPEC_SCHEMA,
        evidence_path="route_spec.decision",
    )
    route_profile = _extract_required_text(
        route_spec,
        key="route_profile",
        code=ValidationErrorCode.INVALID_ROUTE_SPEC_SCHEMA,
        evidence_path="route_spec.route_profile",
    )
    dominant_rule_id = _extract_required_text(
        route_spec,
        key="dominant_rule_id",
        code=ValidationErrorCode.INVALID_ROUTE_SPEC_SCHEMA,
        evidence_path="route_spec.dominant_rule_id",
    )
    return RouteSpecTarget(
        schema_version=normalized_schema,
        decision=decision,
        route_profile=route_profile,
        dominant_rule_id=dominant_rule_id,
    )


def parse_capability_matrix(capability_matrix: CapabilityMatrix | Mapping[str, Any]) -> CapabilityMatrix:
    if isinstance(capability_matrix, CapabilityMatrix):
        return capability_matrix
    if not isinstance(capability_matrix, Mapping):
        raise ValidationContractError(
            ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
            "capability_matrix must be a CapabilityMatrix or mapping payload",
            evidence_path="capability_matrix",
            detail={"payload_type": type(capability_matrix).__name__},
        )
    payload = _canonicalize_mapping(capability_matrix)
    allowed_top_level = {"schema_version", "tools"}
    unknown_top_level = sorted(set(payload) - allowed_top_level)
    if unknown_top_level:
        bad_key = unknown_top_level[0]
        raise ValidationContractError(
            ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
            f"Unsupported capability_matrix field '{bad_key}'",
            evidence_path=f"capability_matrix.{bad_key}",
        )

    schema_version = _extract_required_text(
        payload,
        key="schema_version",
        code=ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
        evidence_path="capability_matrix.schema_version",
    )
    try:
        normalized_schema = _validate_schema_major(schema_version, SUPPORTED_PHASE4_SCHEMA_MAJOR)
    except ValueError as exc:
        raise ValidationContractError(
            ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
            str(exc),
            evidence_path="capability_matrix.schema_version",
            detail={"schema_version": schema_version},
        ) from exc

    raw_tools = payload.get("tools")
    if not isinstance(raw_tools, list):
        raise ValidationContractError(
            ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
            "capability_matrix.tools must be a list",
            evidence_path="capability_matrix.tools",
        )

    tools: list[ToolCapability] = []
    seen_tool_ids: set[str] = set()
    for index, raw_tool in enumerate(raw_tools):
        path_prefix = f"capability_matrix.tools[{index}]"
        if not isinstance(raw_tool, Mapping):
            raise ValidationContractError(
                ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
                "Each capability_matrix.tools entry must be a mapping",
                evidence_path=path_prefix,
            )

        allowed_tool_fields = {"tool_id", "supported_route_profiles", "capabilities"}
        unknown_tool_fields = sorted(set(raw_tool) - allowed_tool_fields)
        if unknown_tool_fields:
            bad_field = unknown_tool_fields[0]
            code = (
                ValidationErrorCode.FREEFORM_CAPABILITY_METADATA_PATH
                if bad_field.casefold() == "metadata"
                else ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA
            )
            raise ValidationContractError(
                code,
                f"Unsupported capability metadata path '{bad_field}'",
                evidence_path=f"{path_prefix}.{bad_field}",
            )

        tool_id = _extract_required_text(
            raw_tool,
            key="tool_id",
            code=ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
            evidence_path=f"{path_prefix}.tool_id",
        )
        if tool_id in seen_tool_ids:
            raise ValidationContractError(
                ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
                f"Duplicate tool_id '{tool_id}' in capability_matrix",
                evidence_path=f"{path_prefix}.tool_id",
            )
        seen_tool_ids.add(tool_id)

        supported_route_profiles = _extract_required_text_list(
            raw_tool,
            key="supported_route_profiles",
            code=ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
            evidence_path=f"{path_prefix}.supported_route_profiles",
        )
        capabilities = _extract_required_text_list(
            raw_tool,
            key="capabilities",
            code=ValidationErrorCode.INVALID_CAPABILITY_MATRIX_SCHEMA,
            evidence_path=f"{path_prefix}.capabilities",
        )
        tools.append(
            ToolCapability(
                tool_id=tool_id,
                supported_route_profiles=tuple(supported_route_profiles),
                capabilities=tuple(capabilities),
            )
        )

    return CapabilityMatrix(schema_version=normalized_schema, tools=tuple(tools))


def parse_policy_contract(policy_contract: PolicyContract | Mapping[str, Any]) -> PolicyContract:
    if isinstance(policy_contract, PolicyContract):
        return policy_contract
    if not isinstance(policy_contract, Mapping):
        raise ValidationContractError(
            ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            "policy_contract must be a PolicyContract or mapping payload",
            evidence_path="policy_contract",
            detail={"payload_type": type(policy_contract).__name__},
        )
    payload = _canonicalize_mapping(policy_contract)
    allowed_top_level = {
        "schema_version",
        "route_to_tool",
        "required_capabilities",
        "blocked_dominant_rule_ids",
        "allowed_route_decisions",
    }
    unknown_top_level = sorted(set(payload) - allowed_top_level)
    if unknown_top_level:
        bad_key = unknown_top_level[0]
        raise ValidationContractError(
            ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            f"Unsupported policy_contract field '{bad_key}'",
            evidence_path=f"policy_contract.{bad_key}",
        )

    schema_version = _extract_required_text(
        payload,
        key="schema_version",
        code=ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
        evidence_path="policy_contract.schema_version",
    )
    try:
        normalized_schema = _validate_schema_major(schema_version, SUPPORTED_PHASE4_SCHEMA_MAJOR)
    except ValueError as exc:
        raise ValidationContractError(
            ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            str(exc),
            evidence_path="policy_contract.schema_version",
            detail={"schema_version": schema_version},
        ) from exc

    route_to_tool_entries = _extract_required_mapping_list(
        payload,
        key="route_to_tool",
        code=ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
        evidence_path="policy_contract.route_to_tool",
    )
    route_to_tool: list[RouteToolBinding] = []
    seen_route_profiles: set[str] = set()
    for index, entry in enumerate(route_to_tool_entries):
        path_prefix = f"policy_contract.route_to_tool[{index}]"
        allowed_fields = {"route_profile", "tool_id"}
        unknown_fields = sorted(set(entry) - allowed_fields)
        if unknown_fields:
            bad_field = unknown_fields[0]
            raise ValidationContractError(
                ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
                f"Unsupported route_to_tool field '{bad_field}'",
                evidence_path=f"{path_prefix}.{bad_field}",
            )
        route_profile = _extract_required_text(
            entry,
            key="route_profile",
            code=ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            evidence_path=f"{path_prefix}.route_profile",
        )
        if route_profile in seen_route_profiles:
            raise ValidationContractError(
                ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
                f"Duplicate route_profile '{route_profile}' in policy_contract.route_to_tool",
                evidence_path=f"{path_prefix}.route_profile",
            )
        seen_route_profiles.add(route_profile)
        tool_id = _extract_required_text(
            entry,
            key="tool_id",
            code=ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            evidence_path=f"{path_prefix}.tool_id",
        )
        route_to_tool.append(RouteToolBinding(route_profile=route_profile, tool_id=tool_id))

    required_capability_entries = _extract_required_mapping_list(
        payload,
        key="required_capabilities",
        code=ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
        evidence_path="policy_contract.required_capabilities",
    )
    required_capabilities: list[RequiredCapabilityBinding] = []
    seen_required_profiles: set[str] = set()
    for index, entry in enumerate(required_capability_entries):
        path_prefix = f"policy_contract.required_capabilities[{index}]"
        allowed_fields = {"route_profile", "capabilities"}
        unknown_fields = sorted(set(entry) - allowed_fields)
        if unknown_fields:
            bad_field = unknown_fields[0]
            raise ValidationContractError(
                ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
                f"Unsupported required_capabilities field '{bad_field}'",
                evidence_path=f"{path_prefix}.{bad_field}",
            )
        route_profile = _extract_required_text(
            entry,
            key="route_profile",
            code=ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            evidence_path=f"{path_prefix}.route_profile",
        )
        if route_profile in seen_required_profiles:
            raise ValidationContractError(
                ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
                f"Duplicate route_profile '{route_profile}' in policy_contract.required_capabilities",
                evidence_path=f"{path_prefix}.route_profile",
            )
        seen_required_profiles.add(route_profile)
        capabilities = _extract_required_text_list(
            entry,
            key="capabilities",
            code=ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            evidence_path=f"{path_prefix}.capabilities",
        )
        required_capabilities.append(
            RequiredCapabilityBinding(
                route_profile=route_profile,
                capabilities=tuple(capabilities),
            )
        )

    raw_blocked_rule_ids = payload.get("blocked_dominant_rule_ids", [])
    if not isinstance(raw_blocked_rule_ids, list):
        raise ValidationContractError(
            ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            "policy_contract.blocked_dominant_rule_ids must be a list when provided",
            evidence_path="policy_contract.blocked_dominant_rule_ids",
        )
    blocked_rule_ids = _normalize_sorted_text(raw_blocked_rule_ids)

    raw_allowed_decisions = payload.get("allowed_route_decisions", ["PASS_ROUTE"])
    if not isinstance(raw_allowed_decisions, list):
        raise ValidationContractError(
            ValidationErrorCode.INVALID_POLICY_CONTRACT_SCHEMA,
            "policy_contract.allowed_route_decisions must be a list when provided",
            evidence_path="policy_contract.allowed_route_decisions",
        )
    allowed_route_decisions = _normalize_sorted_text(raw_allowed_decisions)

    return PolicyContract(
        schema_version=normalized_schema,
        route_to_tool=tuple(route_to_tool),
        required_capabilities=tuple(required_capabilities),
        blocked_dominant_rule_ids=blocked_rule_ids,
        allowed_route_decisions=allowed_route_decisions or ("PASS_ROUTE",),
    )


def _extract_required_text(
    payload: Mapping[str, Any],
    *,
    key: str,
    code: ValidationErrorCode,
    evidence_path: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValidationContractError(
            code,
            f"Field '{key}' must be a string",
            evidence_path=evidence_path,
            detail={"value_type": type(value).__name__},
        )
    normalized = _normalize_text(value)
    if not normalized:
        raise ValidationContractError(
            code,
            f"Field '{key}' must be non-empty",
            evidence_path=evidence_path,
        )
    return normalized


def _extract_required_text_list(
    payload: Mapping[str, Any],
    *,
    key: str,
    code: ValidationErrorCode,
    evidence_path: str,
) -> list[str]:
    raw_value = payload.get(key)
    if not isinstance(raw_value, list):
        raise ValidationContractError(
            code,
            f"Field '{key}' must be a list of strings",
            evidence_path=evidence_path,
            detail={"value_type": type(raw_value).__name__},
        )
    if not raw_value:
        raise ValidationContractError(
            code,
            f"Field '{key}' must not be empty",
            evidence_path=evidence_path,
        )
    normalized_values: list[str] = []
    for index, entry in enumerate(raw_value):
        if not isinstance(entry, str):
            raise ValidationContractError(
                code,
                f"Field '{key}' contains non-string value",
                evidence_path=f"{evidence_path}[{index}]",
                detail={"value_type": type(entry).__name__},
            )
        normalized = _normalize_text(entry)
        if not normalized:
            raise ValidationContractError(
                code,
                f"Field '{key}' contains empty string value",
                evidence_path=f"{evidence_path}[{index}]",
            )
        normalized_values.append(normalized)
    return normalized_values


def _extract_required_mapping_list(
    payload: Mapping[str, Any],
    *,
    key: str,
    code: ValidationErrorCode,
    evidence_path: str,
) -> list[Mapping[str, Any]]:
    raw_value = payload.get(key)
    if not isinstance(raw_value, list):
        raise ValidationContractError(
            code,
            f"Field '{key}' must be a list",
            evidence_path=evidence_path,
            detail={"value_type": type(raw_value).__name__},
        )
    if not raw_value:
        raise ValidationContractError(
            code,
            f"Field '{key}' must not be empty",
            evidence_path=evidence_path,
        )
    mappings: list[Mapping[str, Any]] = []
    for index, entry in enumerate(raw_value):
        if not isinstance(entry, Mapping):
            raise ValidationContractError(
                code,
                f"Field '{key}' contains non-mapping value",
                evidence_path=f"{evidence_path}[{index}]",
                detail={"value_type": type(entry).__name__},
            )
        mappings.append(entry)
    return mappings


def _validate_schema_major(schema_version: str, expected_major: str) -> str:
    normalized = _normalize_text(schema_version)
    if not normalized:
        raise ValueError("schema_version is required")
    major = normalized.split(".", 1)[0]
    if major != expected_major:
        raise ValueError(f"Unsupported schema major '{major}', expected {expected_major}.x")
    return normalized


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_optional_text(value: object) -> str | None:
    normalized = _normalize_text(value)
    return normalized or None


def _normalize_sorted_text(values: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    normalized = {
        text
        for text in (_normalize_text(item) for item in values)
        if text
    }
    return tuple(sorted(normalized))


def _unique_in_order(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
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
    "CapabilityMatrix",
    "MockDecision",
    "MockErrorCode",
    "MockStage",
    "MockStep",
    "MockStepStatus",
    "MockTrace",
    "MOCK_STAGE_ORDER",
    "PHASE4_MOCK_SCHEMA_VERSION",
    "PHASE4_VALIDATION_SCHEMA_VERSION",
    "PolicyContract",
    "RequiredCapabilityBinding",
    "RouteSpecTarget",
    "RouteToolBinding",
    "SUPPORTED_PHASE4_SCHEMA_MAJOR",
    "SUPPORTED_ROUTE_SPEC_SCHEMA_MAJOR",
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
]
