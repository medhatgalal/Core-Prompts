from __future__ import annotations

from dataclasses import replace
from copy import deepcopy

from intent_pipeline.phase4.contracts import (
    FALLBACK_TIER_ORDER,
    FallbackDecision,
    FallbackErrorCode,
    FallbackTier,
    MockDecision,
)
from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase4.fallback import resolve_fallback
from intent_pipeline.phase4.mock_executor import run_mock_execution
from intent_pipeline.phase4.validator import validate_target


def test_fallback_01_fixed_tier_order_and_deterministic_attempted_chain(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    validation_pass = validate_target(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        deepcopy(phase4_policy_contract_payload),
    )
    # Force deterministic mock-stage failure while keeping validation pass.
    mock_failure_input = replace(validation_pass, checked_capabilities=())
    mock_trace = run_mock_execution(mock_failure_input)
    outcome = resolve_fallback(mock_failure_input, mock_trace)

    assert "FALLBACK-01"
    assert mock_trace.decision is MockDecision.FAIL
    assert outcome.decision is FallbackDecision.DEGRADED
    assert outcome.chosen_tier is FallbackTier.DEGRADED_MOCK_SAFE
    attempted_tiers = tuple(entry.tier for entry in outcome.attempted_tiers)
    assert attempted_tiers == FALLBACK_TIER_ORDER[:2]
    assert outcome.attempted_tiers[0].accepted is False
    assert outcome.attempted_tiers[0].reason_code is FallbackErrorCode.PRIMARY_BLOCKED_BY_MOCK
    assert outcome.attempted_tiers[1].accepted is True


def test_fallback_02_terminal_state_is_deterministic_needs_review(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    blocking_policy = deepcopy(phase4_policy_contract_payload)
    blocking_policy["required_capabilities"][0]["capabilities"] = ["cap.read", "cap.write", "cap.execute"]
    validation_block = validate_target(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        blocking_policy,
    )
    mock_trace = run_mock_execution(validation_block)
    outcome = resolve_fallback(validation_block, mock_trace)

    assert "FALLBACK-02"
    assert outcome.decision is FallbackDecision.NEEDS_REVIEW
    assert outcome.chosen_tier is FallbackTier.TERMINAL_REVIEW
    assert outcome.terminal_code is FallbackErrorCode.TERMINAL_NEEDS_REVIEW
    assert tuple(entry.tier for entry in outcome.attempted_tiers) == FALLBACK_TIER_ORDER
    rejection_codes = tuple(entry.reason_code for entry in outcome.attempted_tiers[:-1])
    assert rejection_codes == (
        FallbackErrorCode.PRIMARY_BLOCKED_BY_VALIDATION,
        FallbackErrorCode.DEGRADED_INELIGIBLE_VALIDATION,
    )
    terminal_attempt = outcome.attempted_tiers[-1]
    assert terminal_attempt.accepted is True
    assert terminal_attempt.reason_code is FallbackErrorCode.TERMINAL_NEEDS_REVIEW
    assert any(path.startswith("route_spec.") for path in outcome.evidence_paths)
    assert any(path.startswith("capability_matrix.") for path in outcome.evidence_paths)


def test_fallback_01_engine_flow_invokes_validate_mock_fallback_in_order(
    monkeypatch,
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
    phase4_policy_contract_payload: dict[str, object],
) -> None:
    calls: list[str] = []

    from intent_pipeline.phase4 import engine as phase4_engine

    original_validate_target = phase4_engine.validate_target
    original_run_mock_execution = phase4_engine.run_mock_execution
    original_resolve_fallback = phase4_engine.resolve_fallback

    def tracked_validate_target(route_spec, capability_matrix, policy_contract):
        calls.append("validate_target")
        return original_validate_target(route_spec, capability_matrix, policy_contract)

    def tracked_run_mock_execution(validation_report):
        calls.append("run_mock_execution")
        return original_run_mock_execution(validation_report)

    def tracked_resolve_fallback(validation_report, mock_trace):
        calls.append("resolve_fallback")
        return original_resolve_fallback(validation_report, mock_trace)

    monkeypatch.setattr(phase4_engine, "validate_target", tracked_validate_target)
    monkeypatch.setattr(phase4_engine, "run_mock_execution", tracked_run_mock_execution)
    monkeypatch.setattr(phase4_engine, "resolve_fallback", tracked_resolve_fallback)

    result = run_phase4(
        deepcopy(phase4_route_spec_payload),
        deepcopy(phase4_capability_matrix_payload),
        deepcopy(phase4_policy_contract_payload),
    )

    assert "FALLBACK-01"
    assert calls == ["validate_target", "run_mock_execution", "resolve_fallback"]
    assert result.pipeline_order == ("validate_target", "run_mock_execution", "resolve_fallback")
