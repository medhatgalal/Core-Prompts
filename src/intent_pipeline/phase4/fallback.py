"""Phase-4 deterministic fallback degradation resolver."""

from __future__ import annotations

from intent_pipeline.phase4.contracts import (
    FALLBACK_TIER_ORDER,
    PHASE4_FALLBACK_SCHEMA_VERSION,
    FallbackAttempt,
    FallbackDecision,
    FallbackErrorCode,
    FallbackOutcome,
    FallbackTier,
    MockDecision,
    MockTrace,
    ValidationDecision,
    ValidationReport,
)


_FALLBACK_RULE_IDS: dict[FallbackTier, str] = {
    FallbackTier.PRIMARY_ROUTE: "FALLBACK-RULE-001-PRIMARY",
    FallbackTier.DEGRADED_MOCK_SAFE: "FALLBACK-RULE-002-DEGRADED",
    FallbackTier.TERMINAL_REVIEW: "FALLBACK-RULE-003-TERMINAL",
}


def resolve_fallback(validation_report: ValidationReport, mock_trace: MockTrace) -> FallbackOutcome:
    """Resolve deterministic fixed-order fallback tier selection."""
    if not isinstance(validation_report, ValidationReport):
        raise TypeError("resolve_fallback expects ValidationReport input")
    if not isinstance(mock_trace, MockTrace):
        raise TypeError("resolve_fallback expects MockTrace input")

    attempts: list[FallbackAttempt] = []

    primary_accepted = (
        validation_report.decision is ValidationDecision.PASS
        and validation_report.can_proceed
        and mock_trace.decision is MockDecision.PASS
    )
    if primary_accepted:
        attempts.append(_build_attempt(FallbackTier.PRIMARY_ROUTE, validation_report, mock_trace, accepted=True))
        return _build_outcome(
            decision=FallbackDecision.USE_PRIMARY,
            chosen_tier=FallbackTier.PRIMARY_ROUTE,
            terminal_code=None,
            attempts=attempts,
            validation_report=validation_report,
        )

    if validation_report.decision is ValidationDecision.BLOCK or not validation_report.can_proceed:
        attempts.append(
            _build_attempt(
                FallbackTier.PRIMARY_ROUTE,
                validation_report,
                mock_trace,
                accepted=False,
                reason_code=FallbackErrorCode.PRIMARY_BLOCKED_BY_VALIDATION,
                details="primary route requires validation PASS + can_proceed",
            )
        )
        attempts.append(
            _build_attempt(
                FallbackTier.DEGRADED_MOCK_SAFE,
                validation_report,
                mock_trace,
                accepted=False,
                reason_code=FallbackErrorCode.DEGRADED_INELIGIBLE_VALIDATION,
                details="degraded mock-safe tier ineligible when validation blocks",
            )
        )
        attempts.append(
            _build_attempt(
                FallbackTier.TERMINAL_REVIEW,
                validation_report,
                mock_trace,
                accepted=True,
                reason_code=FallbackErrorCode.TERMINAL_NEEDS_REVIEW,
                details="all eligible fallback tiers exhausted; deterministic terminal state",
            )
        )
        return _build_outcome(
            decision=FallbackDecision.NEEDS_REVIEW,
            chosen_tier=FallbackTier.TERMINAL_REVIEW,
            terminal_code=FallbackErrorCode.TERMINAL_NEEDS_REVIEW,
            attempts=attempts,
            validation_report=validation_report,
        )

    attempts.append(
        _build_attempt(
            FallbackTier.PRIMARY_ROUTE,
            validation_report,
            mock_trace,
            accepted=False,
            reason_code=FallbackErrorCode.PRIMARY_BLOCKED_BY_MOCK,
            details="primary route requires mock PASS",
        )
    )

    degraded_accepted = mock_trace.decision is MockDecision.FAIL and validation_report.decision is ValidationDecision.PASS
    if degraded_accepted:
        attempts.append(_build_attempt(FallbackTier.DEGRADED_MOCK_SAFE, validation_report, mock_trace, accepted=True))
        return _build_outcome(
            decision=FallbackDecision.DEGRADED,
            chosen_tier=FallbackTier.DEGRADED_MOCK_SAFE,
            terminal_code=None,
            attempts=attempts,
            validation_report=validation_report,
        )

    attempts.append(
        _build_attempt(
            FallbackTier.DEGRADED_MOCK_SAFE,
            validation_report,
            mock_trace,
            accepted=False,
            reason_code=FallbackErrorCode.DEGRADED_NOT_REQUIRED,
            details="degraded tier only used for mock FAIL with validation PASS",
        )
    )
    attempts.append(
        _build_attempt(
            FallbackTier.TERMINAL_REVIEW,
            validation_report,
            mock_trace,
            accepted=True,
            reason_code=FallbackErrorCode.TERMINAL_NEEDS_REVIEW,
            details="no deterministic tier selected before terminal",
        )
    )
    return _build_outcome(
        decision=FallbackDecision.NEEDS_REVIEW,
        chosen_tier=FallbackTier.TERMINAL_REVIEW,
        terminal_code=FallbackErrorCode.TERMINAL_NEEDS_REVIEW,
        attempts=attempts,
        validation_report=validation_report,
    )


def _build_attempt(
    tier: FallbackTier,
    validation_report: ValidationReport,
    mock_trace: MockTrace,
    *,
    accepted: bool,
    reason_code: FallbackErrorCode | None = None,
    details: str | None = None,
) -> FallbackAttempt:
    return FallbackAttempt(
        tier=tier,
        accepted=accepted,
        reason_code=reason_code,
        evidence_paths=_attempt_evidence_paths(tier, validation_report, mock_trace),
        details=details,
    )


def _attempt_evidence_paths(
    tier: FallbackTier,
    validation_report: ValidationReport,
    mock_trace: MockTrace,
) -> tuple[str, ...]:
    tool_id = validation_report.target_tool_id or "unknown"
    return (
        f"fallback.attempted_tiers.{tier.value}.accepted",
        f"capability_matrix.tools::{tool_id}",
        "route_spec.route_profile",
        "validation_report.decision",
        "validation_report.can_proceed",
        "mock_trace.decision",
    )


def _build_outcome(
    *,
    decision: FallbackDecision,
    chosen_tier: FallbackTier,
    terminal_code: FallbackErrorCode | None,
    attempts: list[FallbackAttempt],
    validation_report: ValidationReport,
) -> FallbackOutcome:
    applied_rule_ids = _unique_in_order(
        tuple(_FALLBACK_RULE_IDS[attempt.tier] for attempt in attempts) + (validation_report.dominant_rule_id,)
    )
    evidence_paths = _unique_sorted(
        tuple(path for attempt in attempts for path in attempt.evidence_paths)
        + (
            "fallback.decision",
            "fallback.chosen_tier",
            "fallback.attempted_tiers",
            "route_spec.dominant_rule_id",
        )
    )
    return FallbackOutcome(
        schema_version=PHASE4_FALLBACK_SCHEMA_VERSION,
        decision=decision,
        chosen_tier=chosen_tier,
        terminal_code=terminal_code,
        attempted_tiers=tuple(attempts),
        dominant_rule_id=validation_report.dominant_rule_id,
        evidence_paths=evidence_paths,
        applied_rule_ids=applied_rule_ids,
    )


def _unique_sorted(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = {" ".join(value.split()).strip() for value in values if isinstance(value, str) and value.strip()}
    return tuple(sorted(normalized))


def _unique_in_order(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = " ".join(value.split()).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


__all__ = ["resolve_fallback"]
