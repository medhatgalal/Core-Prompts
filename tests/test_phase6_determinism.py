from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

from intent_pipeline.phase4.engine import run_phase4
from intent_pipeline.phase5.engine import run_phase5
from intent_pipeline.phase6.contracts import ApprovalMode, ExecutionApprovalContract, ExecutionRequest
from intent_pipeline.phase6.engine import run_phase6


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_result(root: Path) -> bytes:
    uplift_text = "\n".join(
        [
            "Primary Objective: prove phase6 deterministic execution contracts.",
            "In Scope: simulate-first authorizer, hermetic adapter, journal evidence.",
            "Out of Scope: dynamic tools and external side effects.",
            "Acceptance Criteria: repeated runs are byte stable.",
        ]
    )
    code = (
        "from intent_pipeline.uplift.engine import run_uplift_engine\n"
        "from intent_pipeline.routing.engine import run_semantic_routing\n"
        "from intent_pipeline.phase4.engine import run_phase4\n"
        "from intent_pipeline.phase5.engine import run_phase5\n"
        "from intent_pipeline.phase6.contracts import ApprovalMode, ExecutionApprovalContract, ExecutionRequest\n"
        "from intent_pipeline.phase6.engine import run_phase6\n"
        f"uplift = run_uplift_engine({uplift_text!r})\n"
        "route_spec = run_semantic_routing(uplift).route_spec.as_payload()\n"
        "route_profile = str(route_spec['route_profile'])\n"
        "tool_id = f'tool-{route_profile.lower()}'\n"
        "capability_matrix = {'schema_version': '4.0.0', 'tools': [{'tool_id': tool_id, 'supported_route_profiles': [route_profile], 'capabilities': ['cap.read', 'cap.write']}]}\n"
        "policy_contract = {'schema_version': '4.0.0', 'route_to_tool': [{'route_profile': route_profile, 'tool_id': tool_id}], 'required_capabilities': [{'route_profile': route_profile, 'capabilities': ['cap.read', 'cap.write']}], 'blocked_dominant_rule_ids': [], 'allowed_route_decisions': ['PASS_ROUTE']}\n"
        "phase4_result = run_phase4(route_spec, capability_matrix, policy_contract)\n"
        "phase5_result = run_phase5(phase4_result)\n"
        "request = ExecutionRequest.from_phase_results(phase4_result, phase5_result, policy_schema_version='4.0.0', policy_rule_ids=('POLICY-RULE-001',))\n"
        "approval = ExecutionApprovalContract(schema_version='6.0.0', approval_mode=ApprovalMode.SIMULATE_ONLY, approval_id='approval-det', approved_by='qa@example.com', approved_at='2026-03-09T10:00:00Z', expires_at='2026-03-10T10:00:00Z', idempotency_key='idem-det', route_profile=request.route_profile, target_tool_id=request.target_tool_id, dominant_rule_id=request.dominant_rule_id, required_capabilities=request.required_capabilities, policy_schema_version=request.policy_schema_version, policy_rule_ids=request.policy_rule_ids)\n"
        "registry = {'schema_version': '6.0.0', 'entries': [{'adapter_id': 'hermetic-adapter', 'route_profile': request.route_profile, 'target_tool_id': request.target_tool_id, 'capabilities': list(request.required_capabilities), 'supports_simulation': True, 'supports_execution': False, 'rule_id': 'REGISTRY-RULE-001'}]}\n"
        f"result = run_phase6(request, approval, registry, journal_root={str(root)!r})\n"
        "print(result.to_json(), end='')\n"
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["TZ"] = "UTC"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    completed = subprocess.run(
        [sys.executable, "-c", f"import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd() / 'src')); {code}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
        env=env,
    )
    return completed.stdout


def test_phase6_outputs_are_byte_stable(tmp_path) -> None:
    outputs = [_build_result(tmp_path / f"run-{index}") for index in range(10)]

    assert "DET-06"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1
