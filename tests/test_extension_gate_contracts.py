from __future__ import annotations

from pathlib import Path

import pytest

from intent_pipeline.extensions.contracts import (
    ExtensionContractErrorCode,
    ExtensionGateDecision,
    ExtensionGateReasonCode,
    ExtensionPolicyContractError,
    ExtensionSourceKind,
    parse_extension_policy_contract,
)
from intent_pipeline.ingestion.policy import SourceRejectionCode, validate_local_source


def test_policy_contract_requires_versioned_rule_ids() -> None:
    with pytest.raises(ExtensionPolicyContractError) as exc_info:
        parse_extension_policy_contract(
            {
                "schema_version": "1.0.0",
                "extension_mode": "CONTROLLED",
                "rules": [
                    {
                        "rule_id": "allow-url-source",
                        "source_kind": "URL",
                        "decision": "ALLOW",
                        "priority": 10,
                        "evidence_paths": ["policy_contract.rules[0]"],
                    }
                ],
            }
        )

    assert exc_info.value.code is ExtensionContractErrorCode.INVALID_RULE_ID


def test_policy_contract_rejects_unsupported_schema_major() -> None:
    with pytest.raises(ExtensionPolicyContractError) as exc_info:
        parse_extension_policy_contract(
            {
                "schema_version": "2.0.0",
                "extension_mode": "DISABLED",
                "rules": [],
            }
        )

    assert exc_info.value.code is ExtensionContractErrorCode.UNSUPPORTED_SCHEMA_MAJOR


def test_policy_contract_serialization_and_order_are_deterministic() -> None:
    contract = parse_extension_policy_contract(
        {
            "schema_version": "1.0.0",
            "extension_mode": "CONTROLLED",
            "rules": [
                {
                    "rule_id": "v1.url.allow.secondary",
                    "source_kind": "URL",
                    "decision": "ALLOW",
                    "priority": 20,
                    "evidence_paths": ["policy_contract.rules[1]"],
                },
                {
                    "rule_id": "v1.url.allow.primary",
                    "source_kind": "URL",
                    "decision": "ALLOW",
                    "priority": 10,
                    "evidence_paths": ["policy_contract.rules[0]"],
                },
            ],
        }
    )

    ordered_rule_ids = [rule_payload["rule_id"] for rule_payload in contract.as_payload()["rules"]]
    assert ordered_rule_ids == ["v1.url.allow.primary", "v1.url.allow.secondary"]

    policy_outputs = [contract.to_json() for _ in range(20)]
    assert len(set(policy_outputs)) == 1

    gate_outputs = [contract.evaluate_source_kind(ExtensionSourceKind.URL).to_json() for _ in range(20)]
    assert len(set(gate_outputs)) == 1


def test_policy_gate_fails_closed_when_required_policy_is_missing(tmp_path: Path) -> None:
    source_file = tmp_path / "input.txt"
    source_file.write_text("hello", encoding="utf-8")

    result = validate_local_source(source_file, require_extension_policy=True)

    assert result.accepted is False
    assert result.rejection is not None
    assert result.rejection.code is SourceRejectionCode.EXTENSION_GATE_BLOCK
    assert "fail.closed" in result.rejection.detail
    assert result.extension_gate is not None
    assert result.extension_gate.decision is ExtensionGateDecision.BLOCK
    assert result.extension_gate.reason_code is ExtensionGateReasonCode.FAIL_CLOSED_MISSING_POLICY


def test_policy_gate_returns_typed_needs_review_for_malformed_policy(tmp_path: Path) -> None:
    source_file = tmp_path / "input.txt"
    source_file.write_text("hello", encoding="utf-8")
    malformed_policy = {
        "schema_version": "1.0.0",
        "extension_mode": "CONTROLLED",
        "rules": [
            {
                "rule_id": "rule-without-version-prefix",
                "source_kind": "URL",
                "decision": "ALLOW",
                "priority": 10,
            }
        ],
    }

    result = validate_local_source(
        source_file,
        extension_policy=malformed_policy,
        require_extension_policy=True,
    )

    assert result.accepted is False
    assert result.rejection is not None
    assert result.rejection.code is SourceRejectionCode.EXTENSION_GATE_NEEDS_REVIEW
    assert "fail.closed" in result.rejection.detail
    assert result.extension_gate is not None
    assert result.extension_gate.decision is ExtensionGateDecision.NEEDS_REVIEW
    assert result.extension_gate.reason_code is ExtensionGateReasonCode.FAIL_CLOSED_INVALID_POLICY
