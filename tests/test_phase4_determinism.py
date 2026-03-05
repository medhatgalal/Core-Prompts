from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _phase4_input_text() -> str:
    return "\n".join(
        [
            "Primary Objective: implement deterministic phase 4 orchestration.",
            "Secondary Objectives: preserve typed contracts and strict boundaries.",
            "In Scope: validation, dry-run mock execution, deterministic fallback.",
            "Out of Scope: runtime tool execution, output/help rendering.",
            "Must keep canonical JSON byte stability.",
            "Acceptance Criteria: full phase4 artifact remains deterministic across runs.",
        ]
    )


def _phase4_payloads_from_text(input_text: str) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    uplift = run_uplift_engine(input_text)
    route_spec = run_semantic_routing(uplift).route_spec.as_payload()
    route_profile = str(route_spec["route_profile"])
    tool_id = f"tool-{route_profile.lower()}"
    capability_matrix = {
        "schema_version": "4.0.0",
        "tools": [
            {
                "tool_id": tool_id,
                "supported_route_profiles": [route_profile],
                "capabilities": ["cap.read", "cap.write"],
            }
        ],
    }
    policy_contract = {
        "schema_version": "4.0.0",
        "route_to_tool": [{"route_profile": route_profile, "tool_id": tool_id}],
        "required_capabilities": [{"route_profile": route_profile, "capabilities": ["cap.read", "cap.write"]}],
        "blocked_dominant_rule_ids": [],
        "allowed_route_decisions": ["PASS_ROUTE"],
    }
    return route_spec, capability_matrix, policy_contract


def _run_phase4_in_fresh_process(input_text: str) -> bytes:
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path.cwd() / 'src'))\n"
        "from intent_pipeline.uplift.engine import run_uplift_engine\n"
        "from intent_pipeline.routing.engine import run_semantic_routing\n"
        "from intent_pipeline.phase4.engine import run_phase4\n"
        "uplift = run_uplift_engine(sys.argv[1])\n"
        "route_spec = run_semantic_routing(uplift).route_spec.as_payload()\n"
        "route_profile = str(route_spec['route_profile'])\n"
        "tool_id = f\"tool-{route_profile.lower()}\"\n"
        "capability_matrix = {\n"
        "  'schema_version': '4.0.0',\n"
        "  'tools': [{'tool_id': tool_id, 'supported_route_profiles': [route_profile], 'capabilities': ['cap.read', 'cap.write']}],\n"
        "}\n"
        "policy_contract = {\n"
        "  'schema_version': '4.0.0',\n"
        "  'route_to_tool': [{'route_profile': route_profile, 'tool_id': tool_id}],\n"
        "  'required_capabilities': [{'route_profile': route_profile, 'capabilities': ['cap.read', 'cap.write']}],\n"
        "  'blocked_dominant_rule_ids': [],\n"
        "  'allowed_route_decisions': ['PASS_ROUTE'],\n"
        "}\n"
        "sys.stdout.write(run_phase4(route_spec, capability_matrix, policy_contract).to_json())\n"
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["TZ"] = "UTC"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"

    completed = subprocess.run(
        [sys.executable, "-c", code, input_text],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
        env=env,
    )
    return completed.stdout


def test_det_04_phase4_in_process_output_is_byte_identical() -> None:
    route_spec, capability_matrix, policy_contract = _phase4_payloads_from_text(_phase4_input_text())
    outputs = [run_phase4(route_spec, capability_matrix, policy_contract).to_json().encode("utf-8") for _ in range(25)]

    assert "DET-04"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1


def test_det_04_phase4_cross_process_output_is_byte_identical() -> None:
    outputs = [_run_phase4_in_fresh_process(_phase4_input_text()) for _ in range(10)]

    assert "DET-04"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1
