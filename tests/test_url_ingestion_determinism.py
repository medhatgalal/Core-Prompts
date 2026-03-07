from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.ingestion.url_snapshot_store import UrlTransportResponse
from intent_pipeline.pipeline import run_phase1_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
                "evidence_paths": ["policy_contract.rules[0]"],
            }
        ],
    }


def _url_policy_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "rules": [
            {
                "rule_id": "v1.url.docs.allow",
                "allowed_schemes": ["https"],
                "allowed_hosts": ["example.com"],
                "allowed_domains": [],
                "allowed_path_prefixes": ["/docs"],
                "allowed_content_types": ["text/plain"],
                "max_bytes": 4096,
                "redirect_limit": 1,
                "timeout_seconds": 5,
                "priority": 10,
                "evidence_paths": ["url_policy.rules[0]"],
            }
        ],
    }


class _FakeTransport:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def open(self, url: str, *, timeout_seconds: int, max_bytes: int) -> UrlTransportResponse:
        return UrlTransportResponse(
            status_code=200,
            headers={"content-type": "text/plain"},
            body=self.body,
        )


def _run_url_flow_in_fresh_process(tmp_dir: Path, mode: str) -> bytes:
    code = (
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path.cwd() / 'src'))\n"
        "from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError\n"
        "from intent_pipeline.ingestion.url_snapshot_store import UrlTransportResponse\n"
        "import intent_pipeline.ingestion.url_snapshot_store as snapshot_store\n"
        "from intent_pipeline.pipeline import run_phase1_pipeline\n"
        "class FakeTransport:\n"
        "  def __init__(self, body):\n"
        "    self.body = body\n"
        "  def open(self, url, *, timeout_seconds, max_bytes):\n"
        "    return UrlTransportResponse(status_code=200, headers={'content-type': 'text/plain'}, body=self.body)\n"
        "snapshot_store._resolve_host_addresses = lambda _host, _port: ('93.184.216.34',)\n"
        "extension_policy = json.loads(sys.argv[1])\n"
        "url_policy = json.loads(sys.argv[2])\n"
        "snapshot_root = Path(sys.argv[3])\n"
        "mode = sys.argv[4]\n"
        "body = b'Objective: Produce deterministic URL summaries.\\nIn Scope: Snapshot approved URL content.\\nConstraint: Keep snapshot reads immutable.\\n'\n"
        "if mode == 'allow':\n"
        "  result = run_phase1_pipeline('https://example.com/docs/input.txt', extension_mode='CONTROLLED', route_profile='IMPLEMENTATION', requested_capabilities=('cap.read',), extension_policy=extension_policy, url_policy=url_policy, snapshot_root=snapshot_root, url_transport=FakeTransport(body))\n"
        "  sys.stdout.write(result)\n"
        "else:\n"
        "  try:\n"
        "    run_phase1_pipeline('https://example.com/private/input.txt', extension_mode='CONTROLLED', route_profile='IMPLEMENTATION', requested_capabilities=('cap.read',), extension_policy=extension_policy, url_policy=url_policy, snapshot_root=snapshot_root, url_transport=FakeTransport(body))\n"
        "  except UrlSourceRejectedError as exc:\n"
        "    payload = {'code': exc.rejection.code.value, 'detail': exc.rejection.detail, 'evidence_paths': list(exc.rejection.evidence_paths), 'terminal_status': exc.rejection.terminal_status}\n"
        "    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(',', ':')))\n"
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["TZ"] = "UTC"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    return subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            json.dumps(_extension_policy_payload(), sort_keys=True),
            json.dumps(_url_policy_payload(), sort_keys=True),
            str(tmp_dir),
            mode,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
        env=env,
    ).stdout


def test_url_pipeline_outputs_are_byte_stable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda _host, _port: ("93.184.216.34",),
    )
    outputs = [
        run_phase1_pipeline(
            "https://example.com/docs/input.txt",
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
            url_policy=_url_policy_payload(),
            snapshot_root=tmp_path,
            url_transport=_FakeTransport(
                b"Objective: Produce deterministic URL summaries.\n"
                b"In Scope: Snapshot approved URL content.\n"
                b"Constraint: Keep snapshot reads immutable.\n"
            ),
        ).encode("utf-8")
        for _ in range(20)
    ]

    assert len(set(outputs)) == 1
    assert len({hashlib.sha256(output).hexdigest() for output in outputs}) == 1


def test_url_pipeline_approved_and_rejected_flows_are_byte_stable_across_processes(
    tmp_path: Path,
) -> None:
    allowed_outputs = [_run_url_flow_in_fresh_process(tmp_path / "allow", "allow") for _ in range(10)]
    rejected_outputs = [_run_url_flow_in_fresh_process(tmp_path / "reject", "reject") for _ in range(10)]

    assert len(set(allowed_outputs)) == 1
    assert len(set(rejected_outputs)) == 1
    rejected_payload = json.loads(rejected_outputs[0].decode("utf-8"))
    assert rejected_payload["terminal_status"] == "NEEDS_REVIEW"
    assert rejected_payload["evidence_paths"] == ["url_policy.rules.allowed_path_prefixes"]
