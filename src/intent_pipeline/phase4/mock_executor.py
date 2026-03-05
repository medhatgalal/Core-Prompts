"""Phase-4 deterministic dry-run mock execution."""

from __future__ import annotations

from intent_pipeline.phase4.contracts import (
    MOCK_STAGE_ORDER,
    PHASE4_MOCK_SCHEMA_VERSION,
    MockDecision,
    MockErrorCode,
    MockStage,
    MockStep,
    MockStepStatus,
    MockTrace,
    ValidationDecision,
    ValidationReport,
)


_STAGE_RULE_IDS: dict[MockStage, str] = {
    MockStage.PRECHECK: "MOCK-RULE-001-PRECHECK",
    MockStage.PLAN: "MOCK-RULE-002-PLAN",
    MockStage.SIMULATE: "MOCK-RULE-003-SIMULATE",
    MockStage.VERIFY: "MOCK-RULE-004-VERIFY",
}


def run_mock_execution(validation_report: ValidationReport) -> MockTrace:
    """Generate deterministic side-effect-free mock trace from validation output."""
    if not isinstance(validation_report, ValidationReport):
        raise TypeError("run_mock_execution expects ValidationReport input")

    steps: list[MockStep] = []
    terminal_failure = False

    for stage in MOCK_STAGE_ORDER:
        if terminal_failure:
            steps.append(_build_skip_step(stage, validation_report))
            continue
        step = _run_stage(stage, validation_report)
        steps.append(step)
        if step.status is MockStepStatus.FAIL:
            terminal_failure = True

    decision = MockDecision.FAIL if terminal_failure else MockDecision.PASS
    applied_rule_ids = _unique_in_order(
        (
            _STAGE_RULE_IDS[MockStage.PRECHECK],
            _STAGE_RULE_IDS[MockStage.PLAN],
            _STAGE_RULE_IDS[MockStage.SIMULATE],
            _STAGE_RULE_IDS[MockStage.VERIFY],
            validation_report.dominant_rule_id,
        )
    )

    return MockTrace(
        schema_version=PHASE4_MOCK_SCHEMA_VERSION,
        decision=decision,
        route_profile=validation_report.route_profile,
        target_tool_id=validation_report.target_tool_id,
        dominant_rule_id=validation_report.dominant_rule_id,
        applied_rule_ids=applied_rule_ids,
        steps=tuple(steps),
    )


def _run_stage(stage: MockStage, validation_report: ValidationReport) -> MockStep:
    if stage is MockStage.PRECHECK:
        if validation_report.decision is not ValidationDecision.PASS or not validation_report.can_proceed:
            return _build_fail_step(
                stage=stage,
                validation_report=validation_report,
                error_code=MockErrorCode.VALIDATION_NOT_PASS,
                details=f"validation decision={validation_report.decision.value}; can_proceed={validation_report.can_proceed}",
            )
        return MockStep(
            stage=stage,
            status=MockStepStatus.PASS,
            rule_id=_STAGE_RULE_IDS[stage],
            action="dry-run precheck over validated target",
            evidence_paths=_base_evidence_paths(stage, validation_report),
            produced_artifacts=("dry-run:precheck-ready",),
        )

    if stage is MockStage.PLAN:
        if not validation_report.target_tool_id:
            return _build_fail_step(
                stage=stage,
                validation_report=validation_report,
                error_code=MockErrorCode.TARGET_TOOL_UNRESOLVED,
                details="validation_report.target_tool_id is empty",
            )
        return MockStep(
            stage=stage,
            status=MockStepStatus.PASS,
            rule_id=_STAGE_RULE_IDS[stage],
            action="dry-run execution plan generation",
            evidence_paths=_base_evidence_paths(stage, validation_report),
            produced_artifacts=(
                f"dry-run:plan:profile:{validation_report.route_profile}",
                f"dry-run:plan:tool:{validation_report.target_tool_id}",
            ),
        )

    if stage is MockStage.SIMULATE:
        if not validation_report.checked_capabilities:
            return _build_fail_step(
                stage=stage,
                validation_report=validation_report,
                error_code=MockErrorCode.CAPABILITY_EVIDENCE_MISSING,
                details="validation_report.checked_capabilities is empty",
            )
        artifacts = tuple(
            sorted(f"dry-run:simulate:{capability}" for capability in validation_report.checked_capabilities)
        )
        return MockStep(
            stage=stage,
            status=MockStepStatus.PASS,
            rule_id=_STAGE_RULE_IDS[stage],
            action="dry-run deterministic simulation",
            evidence_paths=_base_evidence_paths(stage, validation_report),
            produced_artifacts=artifacts,
        )

    if stage is MockStage.VERIFY:
        return MockStep(
            stage=stage,
            status=MockStepStatus.PASS,
            rule_id=_STAGE_RULE_IDS[stage],
            action="dry-run verification of simulated artifacts",
            evidence_paths=_base_evidence_paths(stage, validation_report),
            produced_artifacts=("dry-run:verify:trace-consistent",),
        )

    return _build_fail_step(
        stage=stage,
        validation_report=validation_report,
        error_code=MockErrorCode.UNSUPPORTED_STAGE,
        details=f"unsupported stage {stage.value}",
    )


def _build_skip_step(stage: MockStage, validation_report: ValidationReport) -> MockStep:
    return MockStep(
        stage=stage,
        status=MockStepStatus.SKIP,
        rule_id=_STAGE_RULE_IDS[stage],
        action="dry-run skipped due to earlier stage failure",
        evidence_paths=_base_evidence_paths(stage, validation_report),
        produced_artifacts=(),
    )


def _build_fail_step(
    *,
    stage: MockStage,
    validation_report: ValidationReport,
    error_code: MockErrorCode,
    details: str,
) -> MockStep:
    return MockStep(
        stage=stage,
        status=MockStepStatus.FAIL,
        rule_id=_STAGE_RULE_IDS[stage],
        action="dry-run stage failure",
        evidence_paths=_base_evidence_paths(stage, validation_report),
        produced_artifacts=(),
        error_code=error_code,
        details=details,
    )


def _base_evidence_paths(stage: MockStage, validation_report: ValidationReport) -> tuple[str, ...]:
    tool_id = validation_report.target_tool_id or "unknown"
    return (
        f"capability_matrix.tools::{tool_id}",
        "route_spec.route_profile",
        "validation_report.can_proceed",
        "validation_report.checked_capabilities",
        "validation_report.decision",
        f"mock_trace.steps.{stage.value}.status",
    )


def _unique_in_order(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for entry in values:
        normalized = " ".join(entry.split()).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


__all__ = ["run_mock_execution"]
