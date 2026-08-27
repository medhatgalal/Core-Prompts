from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from core_prompts_eval.adapters import (
    AdapterError,
    AdapterSpec,
    execute_adapter,
    load_adapter_conformance,
    load_adapter_registry,
    parse_codex_jsonl,
    parse_kiro_stream_json,
    render_adapter_argv,
    resolve_adapter_cli_sha256,
    resolve_adapter_cli_executable,
)
from core_prompts_eval.contracts import artifact_hash

ROOT = Path(__file__).resolve().parents[1]


def test_codex_and_kiro_registry_entries_are_hermetic_and_not_promotion_eligible() -> (
    None
):
    registry = load_adapter_registry(ROOT)
    codex = registry["codex-jsonl-experimental"]
    kiro = registry["kiro-stream-json-experimental"]

    assert codex.argv == (
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--json",
        "-C",
        "{workspace}",
        "-m",
        "{model}",
        "-s",
        "workspace-write",
        "--approve-for-me",
        "-",
    )
    assert kiro.argv == (
        "kiro-cli",
        "chat",
        "--no-interactive",
        "--agent",
        "batman",
        "--model",
        "{model}",
        "--effort",
        "{effort}",
        "--output-format",
        "stream-json",
        "--trust-tools={trusted_tools}",
    )
    assert kiro.bootstrap_agent == "batman"
    assert codex.environment_allowlist == ("OPENAI_API_KEY",)
    assert kiro.environment_allowlist == ()
    for spec in (codex, kiro):
        assert spec.hermetic is True
        assert spec.promotion_eligible is False
        assert spec.experimental is True
        assert spec.cli_version_argv
        assert spec.cli_version_pattern
        report = load_adapter_conformance(ROOT, spec)
        assert report["schema_version"] == "AdapterConformance.v1"
        assert report["promotion_eligible"] is False
        assert report["checks"]["signed_protected"] is False
        assert report["blockers"]


def test_kiro_argv_renders_preregistered_effort_without_shell() -> None:
    spec = load_adapter_registry(ROOT)["kiro-stream-json-experimental"]
    rendered = render_adapter_argv(
        spec,
        {
            "resolved_model_identifier": "gpt-5.6-sol",
            "effort": "high",
            "tool_policy": {"mode": "repo-write-subagents", "allowed": ["spawn_agent"]},
        },
        repo_root=ROOT,
        workspace=ROOT,
        session_dir=ROOT / ".test-session",
    )

    assert rendered[rendered.index("--effort") + 1] == "high"
    assert Path(rendered[0]) == resolve_adapter_cli_executable(spec)


def test_adapter_conformance_is_closed_and_hash_bound(tmp_path: Path) -> None:
    registry = load_adapter_registry(ROOT)
    spec = registry["codex-jsonl-experimental"]
    report_path = ROOT / spec.conformance_path
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["unexpected"] = True
    replacement = tmp_path / "conformance.json"
    replacement.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(AdapterError, match="unsupported fields"):
        load_adapter_conformance(
            ROOT, spec, path_override=replacement, verify_hash=False
        )


def test_codex_parser_captures_delivery_events_and_complete_usage() -> None:
    fixture = (
        ROOT
        / "evals"
        / "fixtures"
        / "adapters"
        / "codex-parser-contract-redacted.jsonl"
    )
    parsed = parse_codex_jsonl(fixture.read_bytes(), expected_model="gpt-5.6-sol")
    normalized = parsed.raw["normalized"]

    assert parsed.output == "Delivered and independently reviewed."
    assert parsed.resolved_model_identifier == "gpt-5.6-sol"
    assert parsed.model_version == "gpt-5.6-sol"
    assert parsed.usage == {"raw": 150, "cached": 40, "billed": 110}
    assert normalized["session_id"] == "thread_redacted"
    assert normalized["attempts"] == 1
    assert normalized["hidden_retry_detected"] is False
    assert [event["name"] for event in normalized["subagent_events"]] == ["spawn_agent"]
    assert [event["name"] for event in normalized["review_events"]] == [
        "adversarial_review"
    ]
    assert {event["agent_id"] for event in normalized["authorship"]} == {
        "implementer_redacted",
        "reviewer_redacted",
    }


def test_codex_parser_rejects_missing_response_model_and_hidden_retry() -> None:
    fixture = (
        ROOT / "evals" / "fixtures" / "adapters" / "codex-native-shape-redacted.jsonl"
    )
    with pytest.raises(AdapterError, match="response-derived model"):
        parse_codex_jsonl(fixture.read_bytes(), expected_model="gpt-5.6-sol")

    events = [
        json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines()
    ]
    events[0]["resolved_model_identifier"] = "gpt-5.6-sol"
    events.insert(2, {"type": "turn.started"})
    retried = ("\n".join(json.dumps(event) for event in events) + "\n").encode()
    with pytest.raises(AdapterError, match="hidden retry"):
        parse_codex_jsonl(retried, expected_model="gpt-5.6-sol")


def test_kiro_parser_captures_subagent_review_tool_authorship_and_usage() -> None:
    fixture = (
        ROOT / "evals" / "fixtures" / "adapters" / "kiro-parser-contract-redacted.jsonl"
    )
    parsed = parse_kiro_stream_json(fixture.read_bytes(), expected_model="gpt-5.6-sol")
    normalized = parsed.raw["normalized"]

    assert parsed.output == "Delivered and independently reviewed."
    assert parsed.resolved_model_identifier == "gpt-5.6-sol"
    assert parsed.model_version == "gpt-5.6-sol"
    assert parsed.usage == {"raw": 150, "cached": 40, "billed": 110}
    assert normalized["session_id"] == "session_redacted"
    assert normalized["attempts"] == 1
    assert [event["name"] for event in normalized["subagent_events"]] == [
        "orchestrate_subagent"
    ]
    assert [event["name"] for event in normalized["review_events"]] == [
        "adversarial_review"
    ]
    assert {event["agent_id"] for event in normalized["authorship"]} == {
        "implementer_redacted",
        "reviewer_redacted",
    }


def test_kiro_parser_rejects_incomplete_usage_and_session_reuse() -> None:
    fixture = (
        ROOT / "evals" / "fixtures" / "adapters" / "kiro-parser-contract-redacted.jsonl"
    )
    events = [
        json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines()
    ]
    events = [
        event
        for event in events
        if event.get("payload", {}).get("kind") != "usage_summary"
    ]
    with pytest.raises(AdapterError, match="complete token usage"):
        parse_kiro_stream_json(
            ("\n".join(json.dumps(event) for event in events) + "\n").encode(),
            expected_model="gpt-5.6-sol",
        )

    events = [
        json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines()
    ]
    events[0]["payload"]["resumed"] = True
    with pytest.raises(AdapterError, match="persisted session"):
        parse_kiro_stream_json(
            ("\n".join(json.dumps(event) for event in events) + "\n").encode(),
            expected_model="gpt-5.6-sol",
        )


def test_execute_adapter_uses_hermetic_workspace_sanitized_env_and_session_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    code = """
import json, os, pathlib, subprocess, sys
request = json.load(sys.stdin)
pathlib.Path(os.environ['HOME'], 'session-marker').write_text('redacted')
agent = json.loads(pathlib.Path(os.environ['HOME'], 'agents', 'batman.json').read_text())
payload = {
    'schema_version': 'EvalAdapterResponse.v1',
    'output': json.dumps({
        'cwd_is_repo': pathlib.Path.cwd() == pathlib.Path(request['real_repo']),
        'has_git': (pathlib.Path.cwd() / '.git').exists(),
        'git_remotes': subprocess.run(['git', 'remote'], capture_output=True, text=True, check=True).stdout.splitlines(),
        'environment_keys': sorted(os.environ),
        'agent_prompt': agent['prompt'],
        'agent_tools': agent['tools'],
    }),
    'resolved_model_identifier': request['resolved_model_identifier'],
    'model_version': request['model_version'],
    'usage': {'raw': 1, 'cached': 0, 'billed': 1},
}
print(json.dumps(payload))
"""
    spec = AdapterSpec(
        adapter_id="hermetic-fixture",
        version="1",
        argv=(sys.executable, "-c", code),
        parser="eval-adapter-json-v1",
        environment_allowlist=(),
        promotion_eligible=False,
        experimental=True,
        source=None,
        supported_tool_policy_modes=("none",),
        hermetic=True,
        fixed_environment=(("HOME", "{session_dir}"), ("TMPDIR", "{session_dir}")),
        bootstrap_agent="batman",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leak")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "must-not-leak")
    response = execute_adapter(
        spec,
        {
            "resolved_model_identifier": "fixture-model",
            "model_version": "fixture-version",
            "tool_policy": {
                "mode": "repo-write-subagents",
                "allowed": ["spawn_agent", "adversarial_review"],
            },
            "artifact": "# Batman\n\nHermetic candidate body.",
            "real_repo": str(ROOT),
        },
        repo_root=ROOT,
        timeout_seconds=3,
        max_output_bytes=8192,
    )
    output = json.loads(response.output)

    assert output["cwd_is_repo"] is False
    assert output["has_git"] is True
    assert output["git_remotes"] == []
    assert "OPENAI_API_KEY" not in output["environment_keys"]
    assert "AWS_SECRET_ACCESS_KEY" not in output["environment_keys"]
    assert output["agent_prompt"] == "# Batman\n\nHermetic candidate body."
    assert output["agent_tools"] == ["spawn_agent", "adversarial_review"]
    assert response.raw["normalized"]["workspace_is_hermetic"] is True
    assert response.raw["normalized"]["session_persistence_detected"] is True
    assert response.raw["normalized"]["session_files"] == ["session-marker"]


def test_hermetic_adapter_rejects_remote_added_during_trial() -> None:
    code = """
import json, subprocess, sys
request = json.load(sys.stdin)
subprocess.run(['git', 'remote', 'add', 'forbidden', 'https://example.invalid/repo.git'], check=True)
print(json.dumps({
    'schema_version': 'EvalAdapterResponse.v1',
    'output': 'invalid remote mutation',
    'resolved_model_identifier': request['resolved_model_identifier'],
    'model_version': request['model_version'],
    'usage': {'raw': 1, 'cached': 0, 'billed': 1},
}))
"""
    spec = AdapterSpec(
        adapter_id="remote-fixture",
        version="1",
        argv=(sys.executable, "-c", code),
        parser="eval-adapter-json-v1",
        environment_allowlist=(),
        promotion_eligible=False,
        experimental=True,
        source=None,
        supported_tool_policy_modes=("none",),
        hermetic=True,
        fixed_environment=(("HOME", "{session_dir}"),),
    )

    with pytest.raises(AdapterError, match="zero Git remotes"):
        execute_adapter(
            spec,
            {
                "resolved_model_identifier": "fixture-model",
                "model_version": "fixture-version",
                "tool_policy": {"mode": "none", "allowed": []},
            },
            repo_root=ROOT,
            timeout_seconds=3,
            max_output_bytes=8192,
        )


def test_cli_binary_hash_resolves_symlink_target_and_detects_same_version_replacement(
    tmp_path: Path,
) -> None:
    target = tmp_path / "provider-cli-real"
    target.write_bytes(b"provider-cli-build-one")
    target.chmod(0o755)
    launcher = tmp_path / "provider-cli"
    launcher.symlink_to(target)
    spec = AdapterSpec(
        adapter_id="binary-fixture",
        version="same-version",
        argv=(str(launcher),),
        parser="eval-adapter-json-v1",
        environment_allowlist=(),
        promotion_eligible=False,
        experimental=True,
        source=None,
        supported_tool_policy_modes=("none",),
    )

    first = resolve_adapter_cli_sha256(spec)
    assert first == artifact_hash(target)
    rendered = render_adapter_argv(
        spec,
        {"resolved_model_identifier": "fixture", "tool_policy": {"mode": "none", "allowed": []}},
        repo_root=ROOT,
        workspace=tmp_path,
        session_dir=tmp_path,
    )
    assert Path(rendered[0]) == target.resolve()

    target.write_bytes(b"provider-cli-build-two")
    target.chmod(0o755)
    second = resolve_adapter_cli_sha256(spec)
    assert second == artifact_hash(target)
    assert second != first


def test_kiro_service_credential_is_copied_into_isolated_home_without_path_leak(
    tmp_path: Path,
) -> None:
    source = tmp_path / "protected-service-credential.json"
    source.write_text('{"service":"fixture"}\n', encoding="utf-8")
    source.chmod(0o600)
    code = """
import json, os, pathlib, stat, sys
request = json.load(sys.stdin)
path = pathlib.Path(os.environ['KIRO_SERVICE_CREDENTIAL_FILE'])
home = pathlib.Path(os.environ['KIRO_HOME'])
inside = path.is_relative_to(home)
mode = stat.S_IMODE(path.stat().st_mode)
print(json.dumps({
    'schema_version': 'EvalAdapterResponse.v1',
    'output': json.dumps({'inside_kiro_home': inside, 'mode': mode, 'source_path_leaked': str(path) == request.get('source_path')}),
    'resolved_model_identifier': request['resolved_model_identifier'],
    'model_version': request['model_version'],
    'usage': {'raw': 1, 'cached': 0, 'billed': 1},
}))
"""
    spec = AdapterSpec(
        adapter_id="kiro-credential-fixture",
        version="1",
        argv=(sys.executable, "-c", code),
        parser="eval-adapter-json-v1",
        environment_allowlist=(),
        promotion_eligible=False,
        experimental=True,
        source=None,
        supported_tool_policy_modes=("none",),
        hermetic=True,
        fixed_environment=(
            ("HOME", "{session_dir}"),
            ("KIRO_HOME", "{session_dir}"),
        ),
    )

    response = execute_adapter(
        spec,
        {
            "resolved_model_identifier": "fixture-model",
            "model_version": "fixture-version",
            "tool_policy": {"mode": "none", "allowed": []},
        },
        credential_binding={
            "kind": "protected_service_file",
            "name": "KIRO_SERVICE_CREDENTIAL_FILE",
            "format": "kiro-service-credential-v1",
            "source_path": str(source),
            "source_sha256": artifact_hash(source),
        },
        repo_root=ROOT,
        timeout_seconds=3,
        max_output_bytes=8192,
    )
    output = json.loads(response.output)
    assert output == {"inside_kiro_home": True, "mode": 0o600, "source_path_leaked": False}
