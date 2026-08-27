from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .contracts import artifact_hash


class AdapterError(RuntimeError):
    """Raised when an adapter or its response violates the runner contract."""


@dataclass(frozen=True)
class AdapterSpec:
    adapter_id: str
    version: str
    argv: tuple[str, ...]
    parser: str
    environment_allowlist: tuple[str, ...]
    promotion_eligible: bool
    experimental: bool
    source: str | None
    supported_tool_policy_modes: tuple[str, ...]
    hermetic: bool = False
    fixed_environment: tuple[tuple[str, str], ...] = ()
    cli_version_argv: tuple[str, ...] = ()
    cli_version_pattern: str | None = None
    conformance_path: str | None = None
    conformance_sha256: str | None = None
    bootstrap_agent: str | None = None

    def binding(self, repo_root: Path | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.adapter_id,
            "version": self.version,
            "argv": list(self.argv),
            "parser": self.parser,
            "environment_allowlist": list(self.environment_allowlist),
            "promotion_eligible": self.promotion_eligible,
            "experimental": self.experimental,
            "source": self.source,
            "supported_tool_policy_modes": list(self.supported_tool_policy_modes),
            "hermetic": self.hermetic,
            "fixed_environment": dict(self.fixed_environment),
            "cli_version_argv": list(self.cli_version_argv),
            "cli_version_pattern": self.cli_version_pattern,
            "conformance_path": self.conformance_path,
            "conformance_sha256": self.conformance_sha256,
            "bootstrap_agent": self.bootstrap_agent,
        }
        if self.source is not None and repo_root is not None:
            source_path = (repo_root / self.source).resolve()
            if not source_path.is_file():
                raise AdapterError(f"adapter source is missing: {self.source}")
            payload["source_sha256"] = artifact_hash(source_path)
        return payload


@dataclass(frozen=True)
class AdapterResponse:
    output: str
    resolved_model_identifier: str
    model_version: str
    usage: Mapping[str, int]
    raw: Mapping[str, Any]


CONFORMANCE_FIELDS = {
    "schema_version",
    "adapter_id",
    "adapter_version",
    "cli_binding",
    "evidence",
    "checks",
    "promotion_eligible",
    "blockers",
}
CONFORMANCE_CHECK_FIELDS = {
    "argv_help_verified",
    "exact_model_response_derived",
    "complete_token_usage",
    "event_capture",
    "hidden_retry_detection",
    "session_persistence_detection",
    "signed_protected",
}
CONFORMANCE_CLI_FIELDS = {
    "executable",
    "version_argv",
    "observed_version",
    "help_argv",
    "observed_at",
}


def load_adapter_registry(repo_root: Path) -> dict[str, AdapterSpec]:
    path = repo_root / "evals" / "adapters" / "registry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "EvalAdapterRegistry.v1" or not isinstance(
        payload.get("adapters"), list
    ):
        raise AdapterError("invalid adapter registry")
    registry: dict[str, AdapterSpec] = {}
    for raw in payload["adapters"]:
        if not isinstance(raw, dict):
            raise AdapterError("adapter registry entries must be objects")
        adapter_id = str(raw.get("id") or "")
        argv = raw.get("argv")
        if not adapter_id or adapter_id in registry:
            raise AdapterError("adapter registry IDs must be non-empty and unique")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(item, str) for item in argv)
            or not argv[0]
        ):
            raise AdapterError("adapter registry entry must bind an id and argv array")
        version = str(raw.get("version") or "")
        parser = str(raw.get("parser") or "")
        modes = tuple(str(item) for item in raw.get("supported_tool_policy_modes", []))
        if not version or not parser or not modes:
            raise AdapterError(
                "adapter registry entry must bind version, parser, and supported tool policies"
            )
        fixed_environment = raw.get("fixed_environment", {})
        if not isinstance(fixed_environment, Mapping) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in fixed_environment.items()
        ):
            raise AdapterError("adapter fixed_environment must be a string map")
        cli_version_argv = raw.get("cli_version_argv", [])
        cli_version_pattern = raw.get("cli_version_pattern")
        if not isinstance(cli_version_argv, list) or not all(
            isinstance(item, str) and item for item in cli_version_argv
        ):
            raise AdapterError("adapter cli_version_argv must be an argv array")
        if bool(cli_version_argv) != bool(cli_version_pattern):
            raise AdapterError(
                "adapter CLI version argv and pattern must be configured together"
            )
        conformance_path = raw.get("conformance_path")
        conformance_sha256 = raw.get("conformance_sha256")
        if bool(conformance_path) != bool(conformance_sha256):
            raise AdapterError(
                "adapter conformance path and SHA-256 must be configured together"
            )
        if conformance_sha256 is not None and not re.fullmatch(
            r"[0-9a-f]{64}", str(conformance_sha256)
        ):
            raise AdapterError(
                "adapter conformance_sha256 must be a lowercase SHA-256 digest"
            )
        registry[adapter_id] = AdapterSpec(
            adapter_id=adapter_id,
            version=version,
            argv=tuple(argv),
            parser=parser,
            environment_allowlist=tuple(
                str(item) for item in raw.get("environment_allowlist", [])
            ),
            promotion_eligible=raw.get("promotion_eligible") is True,
            experimental=raw.get("experimental") is True,
            source=str(raw["source"]) if raw.get("source") is not None else None,
            supported_tool_policy_modes=modes,
            hermetic=raw.get("hermetic") is True,
            fixed_environment=tuple(
                sorted(
                    (str(key), str(value)) for key, value in fixed_environment.items()
                )
            ),
            cli_version_argv=tuple(cli_version_argv),
            cli_version_pattern=str(cli_version_pattern)
            if cli_version_pattern is not None
            else None,
            conformance_path=str(conformance_path)
            if conformance_path is not None
            else None,
            conformance_sha256=str(conformance_sha256)
            if conformance_sha256 is not None
            else None,
            bootstrap_agent=str(raw["bootstrap_agent"])
            if raw.get("bootstrap_agent") is not None
            else None,
        )
    return registry


def load_adapter_conformance(
    repo_root: Path,
    spec: AdapterSpec,
    *,
    path_override: Path | None = None,
    verify_hash: bool = True,
) -> dict[str, Any]:
    if spec.conformance_path is None or spec.conformance_sha256 is None:
        raise AdapterError(f"adapter {spec.adapter_id} has no conformance binding")
    path = path_override or (repo_root / spec.conformance_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError(f"cannot load adapter conformance: {exc}") from exc
    if not isinstance(payload, dict):
        raise AdapterError("adapter conformance must be an object")
    unexpected = sorted(set(payload) - CONFORMANCE_FIELDS)
    missing = sorted(CONFORMANCE_FIELDS - set(payload))
    if unexpected:
        raise AdapterError(
            f"adapter conformance contains unsupported fields: {', '.join(unexpected)}"
        )
    if missing:
        raise AdapterError(
            f"adapter conformance is missing required fields: {', '.join(missing)}"
        )
    if payload["schema_version"] != "AdapterConformance.v1":
        raise AdapterError("unsupported adapter conformance schema")
    if (
        payload["adapter_id"] != spec.adapter_id
        or payload["adapter_version"] != spec.version
    ):
        raise AdapterError(
            "adapter conformance identity does not match its registry binding"
        )
    checks = payload["checks"]
    if not isinstance(checks, Mapping) or set(checks) != CONFORMANCE_CHECK_FIELDS:
        raise AdapterError(
            "adapter conformance checks must use the closed AdapterConformance.v1 shape"
        )
    if not all(isinstance(checks[field], bool) for field in CONFORMANCE_CHECK_FIELDS):
        raise AdapterError("adapter conformance checks must be booleans")
    if payload["promotion_eligible"] is not False or spec.promotion_eligible:
        raise AdapterError("unsigned adapter conformance cannot authorize promotion")
    if (
        not isinstance(payload["blockers"], list)
        or not payload["blockers"]
        or not all(
            isinstance(item, str) and item.strip() for item in payload["blockers"]
        )
    ):
        raise AdapterError("ineligible adapter conformance must list blockers")
    cli_binding = payload["cli_binding"]
    if (
        not isinstance(cli_binding, Mapping)
        or set(cli_binding) != CONFORMANCE_CLI_FIELDS
    ):
        raise AdapterError(
            "adapter conformance CLI binding must use the closed AdapterConformance.v1 shape"
        )
    if cli_binding["version_argv"] != list(spec.cli_version_argv):
        raise AdapterError(
            "adapter conformance version argv does not match its registry binding"
        )
    if not isinstance(cli_binding["help_argv"], list) or not all(
        isinstance(item, str) and item for item in cli_binding["help_argv"]
    ):
        raise AdapterError("adapter conformance help argv must be an argv array")
    evidence = payload["evidence"]
    if not isinstance(evidence, Mapping) or set(evidence) != {
        "fixture_path",
        "fixture_sha256",
        "fixture_kind",
        "redacted",
    }:
        raise AdapterError(
            "adapter conformance evidence must use the closed AdapterConformance.v1 shape"
        )
    fixture_path = _repo_relative(
        repo_root, str(evidence["fixture_path"]), "adapter conformance fixture"
    )
    if (
        not fixture_path.is_file()
        or artifact_hash(fixture_path) != evidence["fixture_sha256"]
    ):
        raise AdapterError("adapter conformance fixture binding is missing or stale")
    if evidence["redacted"] is not True:
        raise AdapterError("checked-in adapter conformance fixtures must be redacted")
    if verify_hash and artifact_hash(path) != spec.conformance_sha256:
        raise AdapterError("adapter conformance binding is stale")
    return payload


def _repo_relative(repo_root: Path, configured: str, label: str) -> Path:
    relative = Path(configured)
    if relative.is_absolute() or ".." in relative.parts:
        raise AdapterError(f"{label} must be repo-relative")
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise AdapterError(f"{label} escapes the repository") from exc
    return resolved


def execute_adapter(
    spec: AdapterSpec,
    request: Mapping[str, Any],
    *,
    repo_root: Path,
    timeout_seconds: int,
    max_output_bytes: int,
    credential_binding: Mapping[str, Any] | None = None,
) -> AdapterResponse:
    with tempfile.TemporaryDirectory(prefix="core-prompts-eval-") as temporary:
        isolation_root = Path(temporary)
        workspace = (
            isolation_root / "workspace" if spec.hermetic else repo_root.resolve()
        )
        session_dir = isolation_root / "session"
        workspace.mkdir(parents=True, exist_ok=True)
        session_dir.mkdir(parents=True, exist_ok=True)
        replacements = _adapter_replacements(request, repo_root, workspace, session_dir)
        environment = _adapter_environment(spec, replacements)
        argv = render_adapter_argv(
            spec,
            request,
            repo_root=repo_root,
            workspace=workspace,
            session_dir=session_dir,
            environment=environment,
        )
        _configure_protected_credential(
            spec,
            credential_binding,
            repo_root=repo_root,
            session_dir=session_dir,
            environment=environment,
        )
        observed_cli_sha256 = resolve_adapter_cli_sha256(
            spec, environment=environment
        )
        if spec.hermetic:
            _initialize_hermetic_microrepo(
                workspace, session_dir, environment, timeout_seconds
            )
        cli_version = _probe_cli_version(spec, environment, workspace, timeout_seconds)
        _bootstrap_hermetic_agent(spec, request, session_dir)
        preexisting_session_files = _relative_files(session_dir)
        encoded_request = json.dumps(dict(request), sort_keys=True).encode("utf-8")
        process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=environment,
            cwd=workspace,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(
                input=encoded_request, timeout=timeout_seconds
            )
        except subprocess.TimeoutExpired as exc:
            _terminate_process_group(process)
            stdout, stderr = process.communicate()
            raise AdapterError(f"adapter timed out after {timeout_seconds}s") from exc
        if len(stdout) > max_output_bytes or len(stderr) > max_output_bytes:
            raise AdapterError("adapter output exceeded the configured byte bound")
        if process.returncode != 0:
            message = stderr.decode("utf-8", errors="replace")[:1000]
            raise AdapterError(f"adapter exited with {process.returncode}: {message}")
        if spec.hermetic:
            _assert_zero_git_remotes(workspace, environment, timeout_seconds)
        response = _parse_response(
            spec, stdout, expected_model=str(request["resolved_model_identifier"])
        )
        session_files = sorted(
            set(_relative_files(session_dir)) - set(preexisting_session_files)
        )
        raw = dict(response.raw)
        normalized = dict(raw.get("normalized", {}))
        normalized.update(
            {
                "cli_version": cli_version,
                "cli_sha256": observed_cli_sha256,
                "session_persistence_detected": bool(session_files),
                "session_files": session_files,
                "workspace_is_hermetic": spec.hermetic,
            }
        )
        raw["normalized"] = normalized
        return replace(response, raw=raw)


def _relative_files(root: Path) -> list[str]:
    return sorted(
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
    )


def _initialize_hermetic_microrepo(
    workspace: Path,
    session_dir: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> None:
    template_dir = session_dir / "empty-git-template"
    template_dir.mkdir()
    git_environment = {
        **dict(environment),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TEMPLATE_DIR": str(template_dir),
    }
    initialized = subprocess.run(
        ["git", "init", "--quiet", "-b", "main"],
        cwd=workspace,
        env=git_environment,
        capture_output=True,
        shell=False,
        timeout=timeout_seconds,
        check=False,
    )
    if initialized.returncode != 0:
        raise AdapterError("hermetic adapter workspace Git initialization failed")
    _assert_zero_git_remotes(workspace, git_environment, timeout_seconds)


def _assert_zero_git_remotes(
    workspace: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> None:
    remotes = subprocess.run(
        ["git", "remote"],
        cwd=workspace,
        env=dict(environment),
        capture_output=True,
        shell=False,
        timeout=timeout_seconds,
        check=False,
    )
    if remotes.returncode != 0 or remotes.stdout.strip():
        raise AdapterError("hermetic adapter workspace must contain zero Git remotes")


def _bootstrap_hermetic_agent(
    spec: AdapterSpec, request: Mapping[str, Any], session_dir: Path
) -> None:
    if spec.bootstrap_agent is None:
        return
    if not spec.hermetic:
        raise AdapterError("adapter agent bootstrap requires a hermetic workspace")
    artifact = request.get("artifact")
    tool_policy = request.get("tool_policy")
    if not isinstance(artifact, str) or not artifact.strip():
        raise AdapterError(
            "adapter agent bootstrap requires the bound capability artifact"
        )
    if not isinstance(tool_policy, Mapping) or not isinstance(
        tool_policy.get("allowed"), list
    ):
        raise AdapterError("adapter agent bootstrap requires a bounded tool allowlist")
    agent_dir = session_dir / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_payload = {
        "name": spec.bootstrap_agent,
        "description": "Hermetic evaluation agent generated from the preregistered arm artifact.",
        "prompt": artifact,
        "resources": [],
        "hooks": {},
        "tools": list(tool_policy["allowed"]),
    }
    (agent_dir / f"{spec.bootstrap_agent}.json").write_text(
        json.dumps(agent_payload, sort_keys=True) + "\n", encoding="utf-8"
    )


def _adapter_replacements(
    request: Mapping[str, Any], repo_root: Path, workspace: Path, session_dir: Path
) -> dict[str, str]:
    tool_policy = request.get("tool_policy", {})
    allowed = tool_policy.get("allowed", []) if isinstance(tool_policy, Mapping) else []
    if not isinstance(allowed, list) or not all(
        isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_.:@/-]+", item)
        for item in allowed
    ):
        raise AdapterError("tool policy allowed list is not safe for argv rendering")
    return {
        "{python}": sys.executable,
        "{repo_root}": str(repo_root.resolve()),
        "{workspace}": str(workspace),
        "{session_dir}": str(session_dir),
        "{model}": str(request["resolved_model_identifier"]),
        "{effort}": str(request.get("effort") or ""),
        "{trusted_tools}": ",".join(allowed),
    }


def render_adapter_argv(
    spec: AdapterSpec,
    request: Mapping[str, Any],
    *,
    repo_root: Path,
    workspace: Path,
    session_dir: Path,
    environment: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Render one validated argv tuple without invoking a shell or process."""

    replacements = _adapter_replacements(request, repo_root, workspace, session_dir)
    rendered = tuple(_replace_placeholders(item, replacements) for item in spec.argv)
    executable = resolve_adapter_cli_executable(
        spec, command=rendered[0], environment=environment
    )
    return (str(executable), *rendered[1:])


def _replace_placeholders(value: str, replacements: Mapping[str, str]) -> str:
    rendered = value
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)
    unresolved = re.findall(r"\{[a-z_]+\}", rendered)
    if unresolved or rendered == "":
        raise AdapterError(
            f"adapter argv has an unresolved or empty value: {', '.join(unresolved)}"
        )
    return rendered


def _adapter_environment(
    spec: AdapterSpec, replacements: Mapping[str, str]
) -> dict[str, str]:
    environment = {"PATH": os.environ.get("PATH", "")}
    for name in spec.environment_allowlist:
        if name in os.environ:
            environment[name] = os.environ[name]
    for name, value in spec.fixed_environment:
        environment[name] = _replace_placeholders(value, replacements)
    return environment


def _configure_protected_credential(
    spec: AdapterSpec,
    binding: Mapping[str, Any] | None,
    *,
    repo_root: Path,
    session_dir: Path,
    environment: dict[str, str],
) -> None:
    if binding is None or binding.get("kind") == "none":
        return
    kind = binding.get("kind")
    name = str(binding.get("name") or "")
    if kind == "protected_env":
        if name != "OPENAI_API_KEY" or name not in spec.environment_allowlist:
            raise AdapterError("protected environment credential is not allowed for this adapter")
        if not environment.get(name):
            raise AdapterError("protected environment credential is missing")
        return
    if kind != "protected_service_file":
        raise AdapterError("unknown protected credential kind")
    if name != "KIRO_SERVICE_CREDENTIAL_FILE" or binding.get("format") != "kiro-service-credential-v1":
        raise AdapterError("unknown Kiro service credential format")
    source = Path(str(binding.get("source_path") or "")).expanduser().absolute()
    if any(component.is_symlink() for component in (source, *source.parents)):
        raise AdapterError("protected service credential cannot use a symlink path")
    try:
        resolved = source.resolve(strict=True)
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        pass
    except OSError as exc:
        raise AdapterError("protected service credential is missing") from exc
    else:
        raise AdapterError("protected service credential must remain outside the repository")
    if not resolved.is_file() or artifact_hash(resolved) != binding.get("source_sha256"):
        raise AdapterError("protected service credential binding is missing or stale")
    if resolved.stat().st_mode & 0o077:
        raise AdapterError("protected service credential permissions are too broad")
    destination_dir = session_dir / "credentials"
    destination_dir.mkdir(mode=0o700)
    destination = destination_dir / "kiro-service-credential.json"
    shutil.copyfile(resolved, destination)
    destination.chmod(0o600)
    environment[name] = str(destination)


def _probe_cli_version(
    spec: AdapterSpec,
    environment: Mapping[str, str],
    workspace: Path,
    timeout_seconds: int,
) -> str | None:
    if not spec.cli_version_argv:
        return None
    result = subprocess.run(
        spec.cli_version_argv,
        capture_output=True,
        shell=False,
        env=dict(environment),
        cwd=workspace,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        raise AdapterError("adapter CLI version probe failed")
    version = result.stdout.decode("utf-8", errors="replace").strip()
    if (
        spec.cli_version_pattern is None
        or re.fullmatch(spec.cli_version_pattern, version) is None
    ):
        raise AdapterError(f"adapter CLI version does not match its binding: {version}")
    return version


def resolve_adapter_cli_sha256(
    spec: AdapterSpec,
    *,
    environment: Mapping[str, str] | None = None,
) -> str:
    """Hash the final executable file that this adapter resolves through PATH/symlinks."""

    return artifact_hash(resolve_adapter_cli_executable(spec, environment=environment))


def resolve_adapter_cli_executable(
    spec: AdapterSpec,
    *,
    command: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> Path:
    """Resolve the exact executable path used for provider invocation."""

    command = command or spec.argv[0]
    if command == "{python}":
        command = sys.executable
    if "{" in command or "}" in command:
        raise AdapterError("adapter executable contains an unresolved placeholder")
    path_value = dict(environment or {}).get("PATH", os.environ.get("PATH", ""))
    located = command if Path(command).is_absolute() else shutil.which(command, path=path_value)
    if not located:
        raise AdapterError(f"adapter CLI executable is unavailable: {command}")
    try:
        executable = Path(located).resolve(strict=True)
    except OSError as exc:
        raise AdapterError(f"adapter CLI executable cannot be resolved: {command}") from exc
    if not executable.is_file():
        raise AdapterError(f"adapter CLI executable is not a file: {command}")
    return executable


def _parse_response(
    spec: AdapterSpec, stdout: bytes, *, expected_model: str
) -> AdapterResponse:
    if spec.parser == "eval-adapter-json-v1":
        return parse_adapter_json(stdout, expected_model=expected_model)
    if spec.parser == "claude-json-v1":
        return parse_claude_json(stdout, expected_model=expected_model)
    if spec.parser == "codex-jsonl-v1":
        return parse_codex_jsonl(stdout, expected_model=expected_model)
    if spec.parser == "kiro-stream-json-v1":
        return parse_kiro_stream_json(stdout, expected_model=expected_model)
    raise AdapterError(f"unsupported adapter parser: {spec.parser}")


def parse_adapter_json(raw_bytes: bytes, *, expected_model: str) -> AdapterResponse:
    payload = _json_object(raw_bytes)
    if payload.get("schema_version") != "EvalAdapterResponse.v1":
        raise AdapterError("unsupported adapter response schema")
    usage = _usage(payload.get("usage"))
    return _response(
        payload,
        output=payload.get("output"),
        model=payload.get("resolved_model_identifier"),
        model_version=payload.get("model_version"),
        usage=usage,
        expected_model=expected_model,
    )


def parse_claude_json(raw_bytes: bytes, *, expected_model: str) -> AdapterResponse:
    payload = _json_object(raw_bytes)
    usage_raw = payload.get("usage")
    if not isinstance(usage_raw, Mapping):
        raise AdapterError("Claude response omits usage")
    input_tokens = _nonnegative_int(usage_raw.get("input_tokens"), "usage.input_tokens")
    output_tokens = _nonnegative_int(
        usage_raw.get("output_tokens"), "usage.output_tokens"
    )
    cached = _nonnegative_int(
        usage_raw.get("cache_read_input_tokens", 0), "usage.cache_read_input_tokens"
    )
    raw = input_tokens + output_tokens
    usage = {"raw": raw, "cached": cached, "billed": max(0, raw - cached)}
    model = payload.get("model")
    model_version = payload.get("model_version") or model
    return _response(
        payload,
        output=payload.get("result"),
        model=model,
        model_version=model_version,
        usage=usage,
        expected_model=expected_model,
    )


def parse_codex_jsonl(raw_bytes: bytes, *, expected_model: str) -> AdapterResponse:
    events = _json_lines(raw_bytes, "Codex")
    event_types = [str(event.get("type") or "") for event in events]
    if event_types.count("turn.started") != 1:
        if event_types.count("turn.started") > 1:
            raise AdapterError("Codex stream reveals a hidden retry")
        raise AdapterError("Codex stream omits the turn start event")
    if event_types.count("turn.completed") != 1:
        raise AdapterError("Codex stream must contain exactly one completed turn")
    if "turn.failed" in event_types or "error" in event_types:
        raise AdapterError("Codex stream reports a failed turn")
    thread_events = [event for event in events if event.get("type") == "thread.started"]
    if len(thread_events) != 1 or not str(thread_events[0].get("thread_id") or ""):
        raise AdapterError("Codex stream omits a unique session identity")
    model, model_version = _response_model(events, expected_model, provider="Codex")
    terminal = next(event for event in events if event.get("type") == "turn.completed")
    usage = _native_usage(terminal.get("usage"), provider="Codex")
    output = _codex_output(events)
    normalized = _normalize_codex_events(events)
    normalized.update(
        {
            "event_types": event_types,
            "session_id": str(thread_events[0]["thread_id"]),
            "attempts": event_types.count("turn.started"),
            "hidden_retry_detected": False,
        }
    )
    return AdapterResponse(
        output=output,
        resolved_model_identifier=model,
        model_version=model_version,
        usage=usage,
        raw={
            "schema_version": "NativeAdapterTrace.v1",
            "provider": "codex",
            "events": events,
            "normalized": normalized,
        },
    )


def parse_kiro_stream_json(raw_bytes: bytes, *, expected_model: str) -> AdapterResponse:
    events = _json_lines(raw_bytes, "Kiro")
    payloads = [event.get("payload") for event in events]
    if not all(isinstance(payload, Mapping) for payload in payloads):
        raise AdapterError("Kiro stream events must contain object payloads")
    typed_payloads = [
        dict(payload) for payload in payloads if isinstance(payload, Mapping)
    ]
    kinds = [
        str(payload.get("kind") or payload.get("type") or "")
        for payload in typed_payloads
    ]
    starts = kinds.count("turn_start")
    if starts != 1:
        if starts > 1:
            raise AdapterError("Kiro stream reveals a hidden retry")
        raise AdapterError("Kiro stream omits the turn start event")
    if kinds.count("turn_end") != 1:
        raise AdapterError("Kiro stream must contain exactly one completed turn")
    if any(payload.get("resumed") is True for payload in typed_payloads):
        raise AdapterError("Kiro adapter loaded a persisted session")
    session_ids = {
        str(payload.get("sessionId") or payload.get("session_id"))
        for payload in typed_payloads
        if payload.get("sessionId") or payload.get("session_id")
    }
    if len(session_ids) != 1:
        raise AdapterError("Kiro stream omits a unique session identity")
    model, model_version = _response_model(
        typed_payloads, expected_model, provider="Kiro"
    )
    usage_payloads = [
        payload.get("usage")
        for payload in typed_payloads
        if (payload.get("kind") or payload.get("type")) == "usage_summary"
    ]
    if len(usage_payloads) != 1:
        raise AdapterError("Kiro stream omits complete token usage")
    usage = _native_usage(usage_payloads[0], provider="Kiro")
    output_candidates = [
        payload.get("content") or payload.get("text")
        for payload in typed_payloads
        if (payload.get("kind") or payload.get("type"))
        in {"assistant", "agent_message"}
    ]
    output = next(
        (str(value) for value in reversed(output_candidates) if isinstance(value, str)),
        None,
    )
    if output is None:
        raise AdapterError("Kiro stream omits textual output")
    normalized = _normalize_kiro_events(typed_payloads)
    normalized.update(
        {
            "event_types": kinds,
            "session_id": next(iter(session_ids)),
            "attempts": starts,
            "hidden_retry_detected": False,
        }
    )
    return AdapterResponse(
        output=output,
        resolved_model_identifier=model,
        model_version=model_version,
        usage=usage,
        raw={
            "schema_version": "NativeAdapterTrace.v1",
            "provider": "kiro",
            "events": events,
            "normalized": normalized,
        },
    )


def _json_lines(raw_bytes: bytes, provider: str) -> list[dict[str, Any]]:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdapterError(f"{provider} stream is not UTF-8") from exc
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdapterError(
                f"{provider} stream line {line_number} is not valid JSON"
            ) from exc
        if not isinstance(event, dict):
            raise AdapterError(f"{provider} stream line {line_number} is not an object")
        events.append(event)
    if not events:
        raise AdapterError(f"{provider} stream is empty")
    return events


def _response_model(
    records: list[dict[str, Any]], expected_model: str, *, provider: str
) -> tuple[str, str]:
    model_fields = ("resolved_model_identifier", "modelId", "model_id", "model")
    version_fields = ("model_version", "modelVersion")
    models = {
        str(record[field])
        for record in records
        for field in model_fields
        if record.get(field)
    }
    versions = {
        str(record[field])
        for record in records
        for field in version_fields
        if record.get(field)
    }
    if not models:
        raise AdapterError(
            f"{provider} stream omits a response-derived model identifier"
        )
    if models != {expected_model}:
        raise AdapterError(
            f"{provider} response model identifier does not match the preregistered model"
        )
    if len(versions) > 1:
        raise AdapterError(f"{provider} stream reports conflicting model versions")
    return expected_model, next(iter(versions), expected_model)


def _native_usage(value: object, *, provider: str) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise AdapterError(f"{provider} stream omits complete token usage")
    required = (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    if any(field not in value for field in required):
        raise AdapterError(f"{provider} stream omits complete token usage")
    counts = {
        field: _nonnegative_int(value[field], f"usage.{field}") for field in required
    }
    if counts["cached_input_tokens"] > counts["input_tokens"]:
        raise AdapterError(f"{provider} cached input tokens exceed total input tokens")
    raw = counts["input_tokens"] + counts["output_tokens"]
    return {
        "raw": raw,
        "cached": counts["cached_input_tokens"],
        "billed": raw - counts["cached_input_tokens"],
    }


def _codex_output(events: list[dict[str, Any]]) -> str:
    outputs = []
    for event in events:
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, Mapping)
            and item.get("type") == "agent_message"
        ):
            outputs.append(item.get("text"))
    output = next(
        (str(value) for value in reversed(outputs) if isinstance(value, str)), None
    )
    if output is None:
        raise AdapterError("Codex stream omits textual output")
    return output


def _normalize_codex_events(
    events: list[dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    tools: list[dict[str, str]] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, Mapping) or item.get("type") not in {
            "mcp_tool_call",
            "command_execution",
            "tool_call",
        }:
            continue
        name = str(
            item.get("tool")
            or item.get("name")
            or item.get("command")
            or item.get("type")
        )
        tools.append(
            {
                "name": name,
                "type": str(item.get("type")),
                "status": str(item.get("status") or "unknown"),
                "agent_id": str(item.get("agent_id") or item.get("agentId") or ""),
            }
        )
    return _classify_delivery_events(tools)


def _normalize_kiro_events(
    payloads: list[dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    tools: list[dict[str, str]] = []
    for payload in payloads:
        kind = str(payload.get("kind") or payload.get("type") or "")
        if kind not in {
            "tool_call",
            "tool_result",
            "sub_agent_start",
            "sub_agent_complete",
        }:
            continue
        tools.append(
            {
                "name": str(
                    payload.get("toolName") or payload.get("tool_name") or kind
                ),
                "type": kind,
                "status": str(payload.get("status") or "unknown"),
                "agent_id": str(
                    payload.get("agentSubtaskId") or payload.get("agent_id") or ""
                ),
            }
        )
    return _classify_delivery_events(tools)


def _classify_delivery_events(
    tools: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    def contains(event: Mapping[str, str], terms: tuple[str, ...]) -> bool:
        haystack = f"{event.get('name', '')} {event.get('type', '')}".lower()
        return any(term in haystack for term in terms)

    return {
        "tool_events": tools,
        "subagent_events": [
            event
            for event in tools
            if contains(event, ("subagent", "sub_agent", "spawn_agent"))
        ],
        "review_events": [
            event for event in tools if contains(event, ("review", "adversarial"))
        ],
        "authorship": [event for event in tools if event.get("agent_id")],
    }


def _response(
    payload: Mapping[str, Any],
    *,
    output: object,
    model: object,
    model_version: object,
    usage: Mapping[str, int],
    expected_model: str,
) -> AdapterResponse:
    if not isinstance(output, str):
        raise AdapterError("adapter response omits textual output")
    if str(model or "") != expected_model:
        raise AdapterError(
            "adapter response model identifier does not match the preregistered model"
        )
    if not str(model_version or ""):
        raise AdapterError("adapter response omits model version")
    return AdapterResponse(
        output=output,
        resolved_model_identifier=expected_model,
        model_version=str(model_version),
        usage=usage,
        raw=dict(payload),
    )


def _usage(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise AdapterError("adapter response omits usage")
    usage = {
        field: _nonnegative_int(value.get(field), f"usage.{field}")
        for field in ("raw", "cached", "billed")
    }
    if usage["cached"] > usage["raw"] or usage["billed"] > usage["raw"]:
        raise AdapterError(
            "adapter usage cached and billed counts cannot exceed raw tokens"
        )
    return usage


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AdapterError(f"{field} must be a nonnegative integer")
    return value


def _json_object(raw_bytes: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("adapter did not emit one valid JSON object") from exc
    if not isinstance(payload, dict):
        raise AdapterError("adapter response must be a JSON object")
    return payload


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=1)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


__all__ = [
    "AdapterError",
    "AdapterResponse",
    "AdapterSpec",
    "execute_adapter",
    "load_adapter_conformance",
    "load_adapter_registry",
    "parse_adapter_json",
    "parse_claude_json",
    "parse_codex_jsonl",
    "parse_kiro_stream_json",
    "render_adapter_argv",
    "resolve_adapter_cli_sha256",
    "resolve_adapter_cli_executable",
]
