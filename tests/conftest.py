from __future__ import annotations

from copy import deepcopy
import sys
from pathlib import Path

import pytest

from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture(name="routing_uplift_input_text")
def fixture_routing_uplift_input_text() -> str:
    return "\n".join(
        [
            "Primary Objective: build deterministic semantic routing inputs.",
            "Secondary Objectives: preserve schema-major boundaries and explicit evidence.",
            "In Scope: routing contracts, signal normalization, deterministic tests.",
            "Out of Scope: tool validation, execution, output generation.",
            "Must keep deterministic canonical serialization.",
            "Acceptance Criteria: routing signals include missing evidence explicitly.",
        ]
    )


@pytest.fixture(name="routing_uplift_contract")
def fixture_routing_uplift_contract(routing_uplift_input_text: str):
    return run_uplift_engine(routing_uplift_input_text)


@pytest.fixture(name="routing_uplift_payload")
def fixture_routing_uplift_payload(routing_uplift_contract):
    return deepcopy(routing_uplift_contract.as_payload())


@pytest.fixture(name="phase4_route_spec_payload")
def fixture_phase4_route_spec_payload(routing_uplift_payload: dict[str, object]) -> dict[str, object]:
    routing_result = run_semantic_routing(routing_uplift_payload)
    return deepcopy(routing_result.route_spec.as_payload())


@pytest.fixture(name="phase4_capability_matrix_payload")
def fixture_phase4_capability_matrix_payload(phase4_route_spec_payload: dict[str, object]) -> dict[str, object]:
    route_profile = str(phase4_route_spec_payload["route_profile"])
    normalized_profile = route_profile.lower().replace("_", "-")
    tool_id = f"tool-{normalized_profile}"
    return {
        "schema_version": "4.0.0",
        "tools": [
            {
                "tool_id": tool_id,
                "supported_route_profiles": [route_profile],
                "capabilities": ["cap.read", "cap.write"],
            }
        ],
    }


@pytest.fixture(name="phase4_policy_contract_payload")
def fixture_phase4_policy_contract_payload(
    phase4_route_spec_payload: dict[str, object],
    phase4_capability_matrix_payload: dict[str, object],
) -> dict[str, object]:
    route_profile = str(phase4_route_spec_payload["route_profile"])
    tool_id = str(phase4_capability_matrix_payload["tools"][0]["tool_id"])
    return {
        "schema_version": "4.0.0",
        "route_to_tool": [
            {
                "route_profile": route_profile,
                "tool_id": tool_id,
            }
        ],
        "required_capabilities": [
            {
                "route_profile": route_profile,
                "capabilities": ["cap.read", "cap.write"],
            }
        ],
        "blocked_dominant_rule_ids": [],
        "allowed_route_decisions": ["PASS_ROUTE"],
    }
