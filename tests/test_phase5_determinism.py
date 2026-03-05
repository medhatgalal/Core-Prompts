from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _phase5_input_text() -> str:
    return "\n".join(
        [
            "Primary Objective: enforce deterministic phase 5 orchestration outputs.",
            "Secondary Objectives: preserve typed runtime/output/help contracts.",
            "In Scope: runtime preflight checks, output generation, help generation.",
            "Out of Scope: real execution, auto-remediation, network access.",
            "Must keep canonical serialization and stable ordering.",
            "Acceptance Criteria: repeated and cross-process byte-stable artifacts.",
        ]
    )


def _phase5_dependency_specs() -> tuple[dict[str, str], ...]:
    return (
        {
            "dependency_id": "dep.required.json",
            "classification": "required",
            "probe_type": "python_module",
            "target": "json",
        },
        {
            "dependency_id": "dep.optional.missing",
            "classification": "optional",
            "probe_type": "python_module",
            "target": "__phase5_missing_optional__",
        },
    )


def _build_phase4_result():
    uplift = run_uplift_engine(_phase5_input_text())
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
    return run_phase4(route_spec, capability_matrix, policy_contract)


def _run_phase5_in_fresh_process(input_text: str) -> bytes:
    code = (
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path.cwd() / 'src'))\n"
        "from intent_pipeline.uplift.engine import run_uplift_engine\n"
        "from intent_pipeline.routing.engine import run_semantic_routing\n"
        "from intent_pipeline.phase4.engine import run_phase4\n"
        "from intent_pipeline.phase5.engine import run_phase5\n"
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
        "dependency_specs = [\n"
        "  {'dependency_id': 'dep.required.json', 'classification': 'required', 'probe_type': 'python_module', 'target': 'json'},\n"
        "  {'dependency_id': 'dep.optional.missing', 'classification': 'optional', 'probe_type': 'python_module', 'target': '__phase5_missing_optional__'},\n"
        "]\n"
        "phase4_result = run_phase4(route_spec, capability_matrix, policy_contract)\n"
        "sys.stdout.write(run_phase5(phase4_result, dependency_specs=dependency_specs).to_json())\n"
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


def test_det_05_phase5_in_process_artifacts_are_byte_identical() -> None:
    phase4_result = _build_phase4_result()
    outputs = [
        run_phase5(phase4_result, dependency_specs=_phase5_dependency_specs()).to_json().encode("utf-8")
        for _ in range(25)
    ]

    assert "DET-05"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1


def test_det_05_phase5_cross_process_artifacts_are_byte_identical() -> None:
    outputs = [_run_phase5_in_fresh_process(_phase5_input_text()) for _ in range(10)]

    assert "DET-05"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1
