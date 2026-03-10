from __future__ import annotations

import pytest

from intent_pipeline.phase6.contracts import ExecutionDecisionCode, Phase6ContractError
from intent_pipeline.phase6.executor_registry import parse_executor_registry


def test_registry_rejects_duplicate_route_tool_bindings() -> None:
    payload = {
        "schema_version": "6.0.0",
        "entries": [
            {
                "adapter_id": "adapter-a",
                "route_profile": "IMPLEMENTATION",
                "target_tool_id": "tool-implementation",
                "capabilities": ["cap.read", "cap.write"],
                "supports_simulation": True,
                "supports_execution": True,
                "rule_id": "REGISTRY-RULE-001",
            },
            {
                "adapter_id": "adapter-b",
                "route_profile": "IMPLEMENTATION",
                "target_tool_id": "tool-implementation",
                "capabilities": ["cap.read", "cap.write"],
                "supports_simulation": True,
                "supports_execution": True,
                "rule_id": "REGISTRY-RULE-002",
            },
        ],
    }

    assert "PHASE6-REGISTRY-01"
    with pytest.raises(Phase6ContractError) as exc_info:
        parse_executor_registry(payload)
    assert exc_info.value.code is ExecutionDecisionCode.REGISTRY_DUPLICATE


def test_registry_resolves_single_closed_mapping() -> None:
    payload = {
        "schema_version": "6.0.0",
        "entries": [
            {
                "adapter_id": "adapter-a",
                "route_profile": "IMPLEMENTATION",
                "target_tool_id": "tool-implementation",
                "capabilities": ["cap.read", "cap.write"],
                "supports_simulation": True,
                "supports_execution": True,
                "rule_id": "REGISTRY-RULE-001",
            }
        ],
    }

    registry = parse_executor_registry(payload)

    assert "PHASE6-REGISTRY-02"
    entry = registry.resolve("IMPLEMENTATION", "tool-implementation")
    assert entry.adapter_id == "adapter-a"
    assert entry.capabilities == ("cap.read", "cap.write")
