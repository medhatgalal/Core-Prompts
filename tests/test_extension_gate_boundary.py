from __future__ import annotations

import pytest

from intent_pipeline.extensions.gates import (
    ExtensionGateOutcome,
    ExtensionGateReasonCode,
    evaluate_extension_gate,
)
from intent_pipeline.pipeline import ExtensionGateBlockedError, run_phase1_pipeline


def _extension_policy_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "extension_mode": "CONTROLLED",
        "rules": [
            {
                "rule_id": "v1.url.allow",
                "source_kind": "URL",
                "decision": "ALLOW",
                "priority": 10,
            },
            {
                "rule_id": "v1.local.allow",
                "source_kind": "LOCAL_FILE",
                "decision": "ALLOW",
                "priority": 30,
            },
        ],
    }


def test_unknown_modes_fail_closed() -> None:
    decision = evaluate_extension_gate(
        extension_mode="UNSUPPORTED_MODE",
        route_profile="IMPLEMENTATION",
        requested_capabilities=("cap.read",),
        policy_contract=_extension_policy_payload(),
    )

    assert decision.outcome is ExtensionGateOutcome.BLOCK
    assert decision.reason_code is ExtensionGateReasonCode.UNKNOWN_MODE


def test_unknown_route_profiles_fail_closed() -> None:
    decision = evaluate_extension_gate(
        extension_mode="CONTROLLED",
        route_profile="UNKNOWN_PROFILE",
        requested_capabilities=("cap.read",),
        policy_contract=_extension_policy_payload(),
    )

    assert decision.outcome is ExtensionGateOutcome.BLOCK
    assert decision.reason_code is ExtensionGateReasonCode.UNKNOWN_ROUTE_PROFILE


def test_unknown_capabilities_fail_closed() -> None:
    decision = evaluate_extension_gate(
        extension_mode="CONTROLLED",
        route_profile="IMPLEMENTATION",
        requested_capabilities=("cap.read", "cap.unknown"),
        policy_contract=_extension_policy_payload(),
    )

    assert decision.outcome is ExtensionGateOutcome.BLOCK
    assert decision.reason_code is ExtensionGateReasonCode.UNKNOWN_CAPABILITY


def test_extensions_disabled_preserve_local_only_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fail_if_gate_called(**_: object) -> object:
        raise AssertionError("evaluate_extension_gate must not execute for disabled default mode")

    monkeypatch.setattr("intent_pipeline.pipeline.evaluate_extension_gate", fail_if_gate_called)
    monkeypatch.setattr(
        "intent_pipeline.pipeline.read_local_file_text",
        lambda _source: calls.append("ingest") or "raw",
    )
    monkeypatch.setattr(
        "intent_pipeline.pipeline.sanitize_two_pass",
        lambda raw_text: calls.append("sanitize") or f"sanitized::{raw_text}",
    )
    monkeypatch.setattr(
        "intent_pipeline.pipeline.render_intent_summary",
        lambda text: calls.append("summary") or f"summary::{text}",
    )

    result = run_phase1_pipeline("local.txt")

    assert result == "summary::sanitized::raw"
    assert calls == ["ingest", "sanitize", "summary"]


def test_pipeline_unknown_mode_blocks_before_local_ingestion(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_ingest_called(_source: object) -> str:
        raise AssertionError("local ingestion should not run for blocked extension modes")

    monkeypatch.setattr("intent_pipeline.pipeline.read_local_file_text", fail_if_ingest_called)

    with pytest.raises(ExtensionGateBlockedError) as exc_info:
        run_phase1_pipeline(
            "local.txt",
            extension_mode="UNSUPPORTED_MODE",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
        )

    assert exc_info.value.decision.outcome is ExtensionGateOutcome.BLOCK
    assert exc_info.value.decision.reason_code is ExtensionGateReasonCode.UNKNOWN_MODE
