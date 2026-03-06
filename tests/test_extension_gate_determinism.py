from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from intent_pipeline.extensions.gates import evaluate_extension_gate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _extension_policy_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "extension_mode": "CONTROLLED",
        "rules": [
            {
                "rule_id": "v1.url.allow.secondary",
                "source_kind": "URL",
                "decision": "ALLOW",
                "priority": 30,
                "evidence_paths": [
                    "policy_contract.rules[1]",
                    "policy_contract.extension_mode",
                ],
            },
            {
                "rule_id": "v1.url.allow.primary",
                "source_kind": "URL",
                "decision": "ALLOW",
                "priority": 10,
                "evidence_paths": [
                    "policy_contract.rules[0]",
                    "policy_contract.extension_mode",
                ],
            },
        ],
    }


def _run_gate_in_fresh_process(policy_payload: dict[str, object]) -> bytes:
    code = (
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path.cwd() / 'src'))\n"
        "from intent_pipeline.extensions.gates import evaluate_extension_gate\n"
        "policy = json.loads(sys.argv[1])\n"
        "decision = evaluate_extension_gate(\n"
        "  extension_mode='CONTROLLED',\n"
        "  route_profile='IMPLEMENTATION',\n"
        "  requested_capabilities=('cap.write', 'cap.read', 'cap.read'),\n"
        "  policy_contract=policy,\n"
        ")\n"
        "sys.stdout.write(decision.to_json())\n"
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["TZ"] = "UTC"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    completed = subprocess.run(
        [sys.executable, "-c", code, json.dumps(policy_payload, sort_keys=True)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
        env=env,
    )
    return completed.stdout


def test_gate_decisions_are_byte_stable() -> None:
    outputs = [
        evaluate_extension_gate(
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.write", "cap.read", "cap.read"),
            policy_contract=_extension_policy_payload(),
        )
        .to_json()
        .encode("utf-8")
        for _ in range(25)
    ]

    assert "XDET-01"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1

    payload = json.loads(outputs[0].decode("utf-8"))
    assert payload["matched_rule_ids"] == ["v1.url.allow.primary", "v1.url.allow.secondary"]
    assert payload["requested_capabilities"] == ["cap.read", "cap.write"]
    assert payload["evidence_paths"] == [
        "policy_contract.extension_mode",
        "policy_contract.rules[0]",
    ]


def test_gate_decisions_are_byte_stable_across_processes() -> None:
    outputs = [_run_gate_in_fresh_process(_extension_policy_payload()) for _ in range(10)]

    assert "XDET-01"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1
