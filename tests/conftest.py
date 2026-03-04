from __future__ import annotations

from copy import deepcopy
import sys
from pathlib import Path

import pytest

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
