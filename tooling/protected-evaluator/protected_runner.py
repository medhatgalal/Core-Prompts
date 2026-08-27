"""Fail-closed orchestration for a private Core-Prompts promotion evaluator.

This module is intentionally free of candidate imports.  It accepts commands only
from the protected configuration and executes them as argv arrays without a shell.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import importlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import jsonschema
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

REVISION_RE = re.compile(r"[0-9a-f]{40}")
HASH_RE = re.compile(r"[0-9a-f]{64}")
PUBLIC_TRUST_ROOT_FIELDS = {
    "schema_version",
    "key_id",
    "algorithm",
    "public_key_base64",
    "purposes",
    "not_before",
    "expires_at",
    "revoked_at",
}
PURPOSES = (
    "adapter_conformance",
    "execution_receipt",
    "global_token_ledger",
    "judge_qualification",
    "sealed_bundle",
    "promotion_verdict",
)
TOP_FIELDS = {
    "schema_version",
    "evaluator",
    "artifacts",
    "submission_trust_root",
    "evaluator_trust_store",
    "candidate_submission_schema",
    "primary",
    "reproduction",
    "sealed_bundle",
    "sealed_attestation",
    "capability_eval_command",
    "score_command",
    "judge_commands",
    "verdict_command",
    "adapter_conformance_command",
    "adapter_conformance_runner_identity",
    "budget_authorizer_runner_identity",
    "adapter_credentials",
    "registered_trial_tool_policy",
    "global_token_budget",
    "signing",
    "limits",
}


class ConfigError(RuntimeError):
    """Raised when protected configuration or evidence fails closed."""


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def artifact_hash(value: object) -> str:
    if isinstance(value, Path):
        encoded = value.read_bytes()
    elif isinstance(value, bytes):
        encoded = value
    elif isinstance(value, str):
        encoded = value.encode("utf-8")
    else:
        encoded = canonical_json(value).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be an object")
    return value


def _closed(payload: Mapping[str, Any], allowed: set[str], label: str) -> None:
    extra = sorted(set(payload) - allowed)
    if extra:
        raise ConfigError(f"{label} contains unsupported fields: {', '.join(extra)}")
    missing = sorted(allowed - set(payload))
    if missing:
        raise ConfigError(f"{label} is missing required fields: {', '.join(missing)}")


def _argv(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise ConfigError(f"{label} must be a non-empty argv array")
    return list(value)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot load {label}") from exc
    return _object(payload, label)


def _configured_path(value: object, label: str) -> Path:
    raw = str(value)
    if raw.startswith("env:"):
        variable = raw.removeprefix("env:")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", variable) or not os.environ.get(variable):
            raise ConfigError(f"protected file variable is missing for {label}")
        raw = os.environ[variable]
    return Path(raw).expanduser().resolve()


def _configured_identity(value: object, label: str) -> str:
    raw = str(value)
    if raw.startswith("env:"):
        variable = raw.removeprefix("env:")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", variable) or not os.environ.get(variable):
            raise ConfigError(f"protected identity variable is missing for {label}")
        raw = os.environ[variable]
    if not raw.strip():
        raise ConfigError(f"{label} must not be empty")
    return raw


def load_config(path: Path) -> dict[str, Any]:
    payload = _read_json(path.resolve(), "protected evaluator config")
    _closed(payload, TOP_FIELDS, "protected evaluator config")
    if payload["schema_version"] != "ProtectedEvaluatorConfig.v1":
        raise ConfigError("unsupported protected evaluator config schema")
    evaluator = _object(payload["evaluator"], "evaluator")
    _closed(evaluator, {"repository", "revision"}, "evaluator")
    artifacts = _object(payload["artifacts"], "artifacts")
    _closed(
        artifacts,
        {"repository", "baseline_revision", "candidate_revision", "skill_path"},
        "artifacts",
    )
    for field, revision in (
        ("evaluator.revision", evaluator["revision"]),
        ("artifacts.baseline_revision", artifacts["baseline_revision"]),
        ("artifacts.candidate_revision", artifacts["candidate_revision"]),
    ):
        if not REVISION_RE.fullmatch(str(revision)):
            raise ConfigError(f"{field} must be a full immutable Git commit")
    skill_path = Path(str(artifacts["skill_path"]))
    if skill_path.is_absolute() or ".." in skill_path.parts:
        raise ConfigError("artifacts.skill_path must be a safe repository-relative path")
    for label in ("primary", "reproduction"):
        section = _object(payload[label], label)
        _closed(section, {"run_plan", "runner_identity"}, label)
        if not str(section["runner_identity"]).strip():
            raise ConfigError(f"{label}.runner_identity must not be empty")
    for field in (
        "adapter_conformance_command",
        "capability_eval_command",
        "score_command",
        "verdict_command",
    ):
        payload[field] = _argv(payload[field], field)
    if not Path(payload["adapter_conformance_command"][0]).is_absolute():
        raise ConfigError("adapter_conformance_command must use an absolute protected executable path")
    _configured_identity(
        payload["adapter_conformance_runner_identity"],
        "adapter conformance runner identity",
    )
    _configured_identity(
        payload["budget_authorizer_runner_identity"],
        "budget authorizer runner identity",
    )
    credentials = _object(payload["adapter_credentials"], "adapter_credentials")
    _closed(credentials, {"codex", "kiro"}, "adapter_credentials")
    codex_credential = _object(credentials["codex"], "adapter_credentials.codex")
    _closed(codex_credential, {"kind", "variable"}, "adapter_credentials.codex")
    if codex_credential != {"kind": "environment", "variable": "OPENAI_API_KEY"}:
        raise ConfigError("Codex credential must be the protected OPENAI_API_KEY environment variable")
    kiro_credential = _object(credentials["kiro"], "adapter_credentials.kiro")
    _closed(
        kiro_credential,
        {"kind", "variable", "documentation_reference"},
        "adapter_credentials.kiro",
    )
    if (
        kiro_credential.get("kind") != "file"
        or kiro_credential.get("variable") != "KIRO_SERVICE_CREDENTIAL_FILE"
        or not str(kiro_credential.get("documentation_reference") or "").strip()
    ):
        raise ConfigError("Kiro credential must bind a documented protected service credential file")
    tool_policy = _object(payload["registered_trial_tool_policy"], "registered_trial_tool_policy")
    if set(tool_policy) != {"mode", "allowed"} or tool_policy.get("mode") != "repo-write-subagents":
        raise ConfigError("registered_trial_tool_policy must use repo-write-subagents with an explicit allowlist")
    allowed_tools = tool_policy.get("allowed")
    if (
        not isinstance(allowed_tools, list)
        or not allowed_tools
        or len(set(allowed_tools)) != len(allowed_tools)
        or any(
            not isinstance(tool, str)
            or not re.fullmatch(r"[A-Za-z0-9_.:@/-]+", tool)
            for tool in allowed_tools
        )
    ):
        raise ConfigError("registered_trial_tool_policy must use a safe unique non-empty allowlist")
    global_budget = _object(payload["global_token_budget"], "global_token_budget")
    _closed(
        global_budget,
        {
            "cap",
            "allocations",
            "conformance_max_tokens_per_probe",
            "judge_max_tokens_per_call",
        },
        "global_token_budget",
    )
    if global_budget.get("cap") != 5_000_000:
        raise ConfigError("global raw-token cap must be exactly 5000000")
    allocations = _object(global_budget["allocations"], "global_token_budget.allocations")
    allocation_fields = {
        "adapter_conformance",
        "primary",
        "reproduction",
        "judge_adjudication",
    }
    _closed(allocations, allocation_fields, "global_token_budget.allocations")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in allocations.values()):
        raise ConfigError("global token allocations must be non-negative integers")
    if sum(allocations.values()) > global_budget["cap"]:
        raise ConfigError("global token allocations exceed the 5000000 raw-token cap")
    for field in ("conformance_max_tokens_per_probe", "judge_max_tokens_per_call"):
        value = global_budget[field]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigError(f"global_token_budget.{field} must be a positive integer")
    if global_budget["conformance_max_tokens_per_probe"] * 2 > allocations["adapter_conformance"]:
        raise ConfigError("conformance probe reservations exceed their global allocation")
    judges = payload["judge_commands"]
    if not isinstance(judges, list) or not judges:
        raise ConfigError("judge_commands must contain at least one protected judge")
    seen_judges: set[str] = set()
    for index, raw in enumerate(judges):
        judge = _object(raw, f"judge_commands[{index}]")
        _closed(judge, {"judge_id", "command"}, f"judge_commands[{index}]")
        judge_id = str(judge["judge_id"])
        if not judge_id or judge_id in seen_judges:
            raise ConfigError("judge_commands must use unique non-empty judge IDs")
        seen_judges.add(judge_id)
        judge["command"] = _argv(judge["command"], f"judge_commands[{index}].command")
    limits = _object(payload["limits"], "limits")
    _closed(limits, {"timeout_seconds", "max_public_bytes", "raw_token_cap"}, "limits")
    for field in ("timeout_seconds", "max_public_bytes", "raw_token_cap"):
        value = limits[field]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigError(f"limits.{field} must be a positive integer")
    trust_store_binding = _object(payload["evaluator_trust_store"], "evaluator_trust_store")
    _closed(trust_store_binding, {"path", "sha256"}, "evaluator_trust_store")
    trust_store_path = _configured_path(trust_store_binding["path"], "evaluator trust store")
    expected_store_hash = str(trust_store_binding["sha256"])
    if (
        not HASH_RE.fullmatch(expected_store_hash)
        or not trust_store_path.is_file()
        or artifact_hash(trust_store_path) != expected_store_hash
    ):
        raise ConfigError("evaluator trust store binding is missing or stale")
    trust_store = _read_json(trust_store_path, "evaluator trust store")
    if set(trust_store) != {"schema_version", "keys"} or trust_store.get("schema_version") != "ProtectedTrustStore.v1":
        raise ConfigError("evaluator trust store has an invalid closed shape")
    store_keys = trust_store.get("keys")
    if not isinstance(store_keys, list) or len(store_keys) != len(PURPOSES):
        raise ConfigError("evaluator trust store must contain every purpose-separated verification key")
    roots_by_purpose: dict[str, dict[str, Any]] = {}
    for raw_root in store_keys:
        root = _object(raw_root, "evaluator trust-store key")
        if set(root) != PUBLIC_TRUST_ROOT_FIELDS or root.get("schema_version") != "ProtectedTrustRoot.v1":
            raise ConfigError("evaluator trust store contains a non-public or invalid root")
        purposes = root.get("purposes")
        if (
            not isinstance(purposes, list)
            or len(purposes) != 1
            or purposes[0] not in PURPOSES
            or purposes[0] in roots_by_purpose
        ):
            raise ConfigError("evaluator trust store must contain five unique one-purpose roots")
        roots_by_purpose[purposes[0]] = root
    if set(roots_by_purpose) != set(PURPOSES):
        raise ConfigError("evaluator trust store must contain every evaluator signing purpose")
    signing = _object(payload["signing"], "signing")
    _closed(signing, set(PURPOSES), "signing")
    private_paths: list[Path] = []
    key_ids: list[str] = []
    for purpose in PURPOSES:
        binding = _object(signing[purpose], f"signing.{purpose}")
        _closed(binding, {"private_key", "key_id"}, f"signing.{purpose}")
        private_paths.append(_configured_path(binding["private_key"], f"{purpose} private key"))
        key_id = str(binding["key_id"])
        if not key_id or roots_by_purpose[purpose].get("key_id") != key_id:
            raise ConfigError("signing key ID does not match its purpose-separated trust-store root")
        key_ids.append(key_id)
    if len(set(private_paths)) != len(PURPOSES) or len(set(key_ids)) != len(PURPOSES):
        raise ConfigError("signing keys and key IDs must be purpose-separated")
    return payload


def verify_reproduction_independence(
    primary: Mapping[str, Any],
    reproduction: Mapping[str, Any],
    primary_identity: str,
    reproduction_identity: str,
) -> None:
    if str(primary.get("run_id") or "") == str(reproduction.get("run_id") or ""):
        raise ConfigError("independent reproduction requires a distinct run_id")
    if primary.get('seed') == reproduction.get('seed'):
        raise ConfigError("independent reproduction requires a distinct seed")
    if primary_identity == reproduction_identity:
        raise ConfigError("independent reproduction requires a distinct runner identity")


PROBE_FIELDS = {
    "schema_version",
    "adapter_id",
    "adapter_version",
    "adapter_sha256",
    "cli_version",
    "cli_sha256",
    "cell_id",
    "host",
    "resolved_model_identifier",
    "model_version",
    "effort",
    "tool_policy_sha256",
    "approval_policy_sha256",
    "credential_descriptor_sha256",
    "authentication_verified",
    "response_model_resolved",
    "usage",
    "attempts",
    "retry_semantics_verified",
    "session_id",
    "session_isolation_verified",
    "tool_semantics_verified",
    "tool_events",
    "authorship_boundary_verified",
    "controller_id",
    "implementation_author_ids",
    "reviewer_ids",
    "fixture_receipt_sha256s",
    "probe_receipt_sha256s",
    "raw_trace_sha256",
    "raw_trace_complete",
}


def validate_adapter_probe_evidence(
    evidence: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    if set(evidence) != PROBE_FIELDS or evidence.get("schema_version") != "AdapterProbeEvidence.v1":
        raise ConfigError("adapter probe evidence must use the closed AdapterProbeEvidence.v1 shape")
    stale = [field for field, value in expected.items() if evidence.get(field) != value]
    if stale or not evidence.get("response_model_resolved"):
        raise ConfigError("adapter probe model or immutable binding is unresolved")
    if evidence.get("authentication_verified") is not True:
        raise ConfigError("adapter probe authentication is not verified")
    usage = _object(evidence.get("usage"), "adapter probe usage")
    if set(usage) != {"raw", "cached", "billed", "complete"} or usage.get("complete") is not True:
        raise ConfigError("adapter probe usage is incomplete")
    if any(isinstance(usage.get(field), bool) or not isinstance(usage.get(field), int) for field in ("raw", "cached", "billed")):
        raise ConfigError("adapter probe usage is incomplete")
    if usage["raw"] <= 0 or usage["cached"] < 0 or usage["billed"] < 0 or usage["cached"] > usage["raw"] or usage["billed"] > usage["raw"]:
        raise ConfigError("adapter probe usage is incomplete")
    if evidence.get("attempts") != 1 or evidence.get("retry_semantics_verified") is not True:
        raise ConfigError("adapter probe retry semantics are not verified")
    if not str(evidence.get("session_id") or "") or evidence.get("session_isolation_verified") is not True:
        raise ConfigError("adapter probe session isolation is not verified")
    events = evidence.get("tool_events")
    required_events = {"subagent_dispatch", "implementation_write", "test_execution", "milestone_review"}
    if (
        evidence.get("tool_semantics_verified") is not True
        or not isinstance(events, list)
        or {str(item.get("kind") or "") for item in events if isinstance(item, Mapping)} != required_events
    ):
        raise ConfigError("adapter probe tool semantics are incomplete")
    controller = str(evidence.get("controller_id") or "")
    implementers = evidence.get("implementation_author_ids")
    reviewers = evidence.get("reviewer_ids")
    if (
        evidence.get("authorship_boundary_verified") is not True
        or not controller
        or not isinstance(implementers, list)
        or not implementers
        or not isinstance(reviewers, list)
        or not reviewers
        or controller in implementers
        or controller in reviewers
        or set(implementers) & set(reviewers)
    ):
        raise ConfigError("adapter probe authorship boundary is not verified")
    for field in ("fixture_receipt_sha256s", "probe_receipt_sha256s"):
        values = evidence.get(field)
        if not isinstance(values, list) or not values or len(set(values)) != len(values) or any(not HASH_RE.fullmatch(str(value)) for value in values):
            raise ConfigError("adapter probe receipt bindings are incomplete")
    if not HASH_RE.fullmatch(str(evidence.get("raw_trace_sha256") or "")) or evidence.get("raw_trace_complete") is not True:
        raise ConfigError("adapter probe trace is incomplete")


class ProtectedRunner:
    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        work_root: Path,
        public_root: Path,
        private_root: Path,
    ) -> None:
        self.config = dict(config)
        self.work_root = work_root.resolve()
        self.public_root = public_root.resolve()
        self.private_root = private_root.resolve()
        self.timeout = int(dict(config["limits"])["timeout_seconds"])
        self.raw_token_cap = int(dict(config["limits"])["raw_token_cap"])
        self.evaluator_root: Path | None = None
        self.evaluator_trust_store_path: Path | None = None
        self._attestations: Any | None = None
        self.work_root.mkdir(parents=True, exist_ok=True)
        self.public_root.mkdir(parents=True, exist_ok=True)
        self.private_root.mkdir(parents=True, exist_ok=True)

    def checkout_read_only(self, repository: str, revision: str, label: str) -> Path:
        if not REVISION_RE.fullmatch(revision):
            raise ConfigError(f"{label} revision must be a full immutable Git commit")
        destination = self.work_root / label
        if destination.exists():
            raise ConfigError(f"isolated checkout already exists for {label}")
        self._run(["git", "clone", "--no-checkout", "--", repository, str(destination)], stage=f"clone_{label}")
        self._run(["git", "checkout", "--detach", revision], cwd=destination, stage=f"checkout_{label}")
        actual = self._run(["git", "rev-parse", "HEAD"], cwd=destination, stage=f"verify_{label}").stdout.strip()
        if actual != revision:
            raise ConfigError(f"{label} checkout did not resolve to the pinned revision")
        # Files are immutable to the evaluator process. Directories remain traversable
        # and allow the evaluator's dedicated report directory to be created.
        for path in destination.rglob("*"):
            if path.is_file() and not path.is_symlink():
                path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        return destination

    def _env(
        self,
        *,
        authority: str = "tools-off",
        tool_policy: Mapping[str, Any] | None = None,
    ) -> dict[str, str]:
        env_home = self.work_root / "hermetic-home"
        env_tmp = self.work_root / "tmp"
        env_home.mkdir(exist_ok=True)
        env_tmp.mkdir(exist_ok=True)
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "HOME": str(env_home),
            "TMPDIR": str(env_tmp),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "CORE_PROMPTS_EVAL_TOOLS": "off",
            "CORE_PROMPTS_EVAL_APPROVALS": "deny",
            "CORE_PROMPTS_EVAL_REMOTE_ACCESS": "deny",
            "GIT_TERMINAL_PROMPT": "0",
        }
        if authority == "repo-write-subagents":
            registered = dict(self.config["registered_trial_tool_policy"])
            if not isinstance(tool_policy, Mapping) or dict(tool_policy) != registered:
                raise ConfigError("unregistered tool policy is forbidden")
            env["CORE_PROMPTS_EVAL_TOOLS"] = "repo-write-subagents"
            env["CORE_PROMPTS_EVAL_TOOL_ALLOWLIST"] = ",".join(registered["allowed"])
            env["CORE_PROMPTS_EVAL_APPROVALS"] = "bounded"
        elif authority != "tools-off" or tool_policy is not None:
            raise ConfigError("unregistered tool policy is forbidden")
        return env

    def adapter_credential_environment(self, host: str) -> dict[str, str]:
        credentials = _object(self.config["adapter_credentials"], "adapter_credentials")
        if host == "codex":
            variable = str(_object(credentials["codex"], "Codex credential")["variable"])
            value = os.environ.get(variable)
            if not value:
                raise ConfigError("Codex protected credential is absent")
            return {variable: value}
        if host == "kiro":
            binding = _object(credentials["kiro"], "Kiro credential")
            variable = str(binding["variable"])
            configured = os.environ.get(variable)
            if not configured:
                raise ConfigError("Kiro protected service credential file is absent")
            path = Path(configured).expanduser()
            if not path.is_absolute() or path.is_symlink() or not path.is_file():
                raise ConfigError("Kiro protected service credential file is missing or unsafe")
            resolved = path.resolve()
            try:
                resolved.relative_to(Path.home().resolve())
            except ValueError:
                pass
            else:
                raise ConfigError("Kiro protected service credential must not use personal configuration")
            if resolved.stat().st_mode & 0o077:
                raise ConfigError("Kiro protected service credential permissions are too broad")
            return {variable: str(resolved)}
        raise ConfigError("unsupported protected adapter credential host")

    def adapter_credential_binding_sha256(self, host: str) -> str:
        return str(self.materialize_credential_binding(host)["descriptor_sha256"])

    def materialize_credential_binding(self, host: str) -> dict[str, Any]:
        credential_environment = self.adapter_credential_environment(host)
        descriptor_dir = self.private_root / "credential-descriptors"
        descriptor_path = descriptor_dir / f"{host}.json"
        if host == "codex":
            descriptor = {
                "schema_version": "CredentialDescriptor.v1",
                "kind": "protected_env",
                "name": "OPENAI_API_KEY",
                "format": "opaque-env-v1",
                "issuer": "protected-core-prompts-evaluator",
            }
            binding: dict[str, Any] = {
                "kind": "protected_env",
                "name": "OPENAI_API_KEY",
            }
        elif host == "kiro":
            source = Path(credential_environment["KIRO_SERVICE_CREDENTIAL_FILE"])
            descriptor = {
                "schema_version": "CredentialDescriptor.v1",
                "kind": "protected_service_file",
                "name": "KIRO_SERVICE_CREDENTIAL_FILE",
                "format": "kiro-service-credential-v1",
                "issuer": "protected-core-prompts-evaluator",
            }
            binding = {
                "kind": "protected_service_file",
                "name": "KIRO_SERVICE_CREDENTIAL_FILE",
                "format": "kiro-service-credential-v1",
                "source_path": str(source),
                "source_sha256": artifact_hash(source),
            }
        else:
            raise ConfigError("unsupported protected adapter credential host")
        if descriptor_path.exists():
            existing = _read_json(descriptor_path, "credential descriptor")
            if existing != descriptor:
                raise ConfigError("credential descriptor is stale")
        else:
            _exclusive_json(descriptor_path, descriptor)
        return {
            **binding,
            "descriptor_path": str(descriptor_path),
            "descriptor_sha256": artifact_hash(descriptor_path),
        }

    def _run(
        self,
        argv: Sequence[str],
        *,
        stage: str,
        cwd: Path | None = None,
        extra_env: Mapping[str, str] | None = None,
        authority: str = "tools-off",
        tool_policy: Mapping[str, Any] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if not argv or any(not isinstance(item, str) or not item for item in argv):
            raise ConfigError(f"{stage} command must be a non-empty argv array")
        try:
            environment = self._env(authority=authority, tool_policy=tool_policy)
            forbidden_overrides = {
                "CORE_PROMPTS_EVAL_TOOLS",
                "CORE_PROMPTS_EVAL_TOOL_ALLOWLIST",
                "CORE_PROMPTS_EVAL_APPROVALS",
                "CORE_PROMPTS_EVAL_REMOTE_ACCESS",
            }
            if set(extra_env or {}) & forbidden_overrides:
                raise ConfigError("protected authority environment cannot be overridden")
            environment.update(dict(extra_env or {}))
            return subprocess.run(
                list(argv),
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=True,
                shell=False,
                timeout=self.timeout,
                start_new_session=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ConfigError(f"protected stage failed: {stage}") from exc

    def run_json_command(
        self,
        argv: Sequence[str],
        *,
        stage: str,
        cwd: Path | None = None,
        authority: str = "tools-off",
        tool_policy: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        completed = self._run(
            argv,
            stage=stage,
            cwd=cwd,
            authority=authority,
            tool_policy=tool_policy,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"protected stage did not emit one JSON object: {stage}") from exc
        return _object(payload, f"{stage} output")

    def run_output_command(
        self,
        argv: Sequence[str],
        *,
        stage: str,
        output: Path,
        cwd: Path | None = None,
        extra_env: Mapping[str, str] | None = None,
        authority: str = "tools-off",
        tool_policy: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if output.exists():
            raise ConfigError(f"immutable output already exists for {stage}")
        completed = self._run(
            argv,
            stage=stage,
            cwd=cwd,
            extra_env=extra_env,
            authority=authority,
            tool_policy=tool_policy,
        )
        if output.exists():
            return _read_json(output, f"{stage} output")
        try:
            return _object(json.loads(completed.stdout), f"{stage} output")
        except json.JSONDecodeError as exc:
            raise ConfigError(f"protected stage emitted no JSON output: {stage}") from exc

    def non_promote(self, reason_code: str, _private_detail: str | None = None) -> dict[str, Any]:
        if not re.fullmatch(r"[a-z0-9_]+", reason_code):
            reason_code = "protected_failure"
        return {
            "schema_version": "ProtectedEvaluationPublicResult.v1",
            "status": "inconclusive",
            "promotion_allowed": False,
            "reason_codes": [reason_code],
        }

    def validate_submission(self, submission_path: Path, evaluator_root: Path) -> dict[str, Any]:
        submission = _read_json(submission_path, "candidate submission")
        schema_path = evaluator_root / str(self.config["candidate_submission_schema"])
        try:
            jsonschema.validate(submission, _read_json(schema_path, "candidate submission schema"))
        except jsonschema.ValidationError as exc:
            raise ConfigError("candidate submission failed schema validation") from exc
        trust_root = _read_json(
            _configured_path(self.config["submission_trust_root"], "submission trust root"),
            "submission trust root",
        )
        self.validate_signed(submission, trust_root, "candidate_submission")
        return submission

    def protect_run(
        self,
        run_dir: Path,
        *,
        label: str,
        signing: Mapping[str, Any],
        receipt_results: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        try:
            chain = verify_hash_chain(run_dir)
        except ConfigError:
            return self.non_promote("invalid_hash_chain")
        manifest = _read_json(run_dir / "manifest.json", f"{label} manifest")
        raw_usage = dict(manifest.get("token_usage") or {}).get("raw")
        if isinstance(raw_usage, bool) or not isinstance(raw_usage, int) or raw_usage > self.raw_token_cap:
            return self.non_promote("token_cap_breach")
        receipts_path = run_dir / "trials" / "receipt-payloads.jsonl"
        if not receipts_path.is_file():
            return self.non_promote("missing_receipts")
        receipts = _read_jsonl(receipts_path, f"{label} receipts")
        if not receipts:
            return self.non_promote("missing_receipts")
        if receipt_results is None:
            return {
                "promotion_allowed": True,
                "manifest": manifest,
                "manifest_path": run_dir / "manifest.json",
                "receipt_payloads": receipts,
                "chain_root_sha256": chain["root_sha256"],
            }
        signed_receipts: list[dict[str, Any]] = []
        for receipt in receipts:
            receipt_id = str(receipt.get("receipt_id") or "")
            scored = receipt_results.get(receipt_id)
            if not isinstance(scored, Mapping):
                raise ConfigError("protected scoring omitted an execution receipt")
            if scored.get("run_id") != receipt.get("run_id") or scored.get("result") != "PASS":
                raise ConfigError("protected scoring did not pass every execution receipt")
            updated = {
                **receipt,
                "result": scored["result"],
                "derived_evidence_grade": scored["derived_evidence_grade"],
            }
            signed_receipts.append(self.sign_inline(updated, "execution_receipt", signing))
        for receipt in signed_receipts:
            self._validate_canonical_schema(receipt, "execution-receipt.schema.json", "execution receipt")
        protected_dir = self.private_root / label
        protected_dir.mkdir(parents=True, exist_ok=True)
        _exclusive_jsonl(protected_dir / "signed-receipts.jsonl", signed_receipts)
        receipt_paths: list[Path] = []
        seen_receipts: set[str] = set()
        for receipt in signed_receipts:
            receipt_id = str(receipt.get("receipt_id") or "")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", receipt_id):
                raise ConfigError("execution receipt ID is not filesystem safe")
            if receipt_id in seen_receipts:
                raise ConfigError("execution receipt IDs must be unique")
            if receipt.get("run_id") != manifest.get("run_id"):
                raise ConfigError("execution receipt has a stale run ID")
            seen_receipts.add(receipt_id)
            receipt_path = protected_dir / "receipts" / f"{receipt_id}.json"
            _exclusive_json(receipt_path, receipt)
            receipt_paths.append(receipt_path)
        return {
            "promotion_allowed": True,
            "manifest": manifest,
            "manifest_path": run_dir / "manifest.json",
            "receipt_path": protected_dir / "signed-receipts.jsonl",
            "receipt_paths": receipt_paths,
            "chain_root_sha256": chain["root_sha256"],
        }

    def sign_inline(
        self,
        payload: Mapping[str, Any],
        purpose: str,
        signing: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if "signature" in payload:
            raise ConfigError("refusing to replace an existing artifact signature")
        material = dict((signing or self.config["signing"])[purpose])
        root = self._trust_root_for_purpose(purpose, str(material["key_id"]))
        key = _load_signer(material, purpose, root)
        unsigned = dict(payload)
        attestations = self._canonical_attestation_module()
        signature = key.sign(attestations.signature_message(unsigned))
        signed = {
            **unsigned,
            "signature": {
                "algorithm": "Ed25519",
                "key_id": root["key_id"],
                "purpose": purpose,
                "signed_at": _now(),
                "payload_sha256": attestations.artifact_hash(unsigned),
                "value_base64": base64.b64encode(signature).decode("ascii"),
            },
        }
        self.validate_signed(signed, root, purpose)
        return signed

    def _canonical_attestation_module(self) -> Any:
        if self._attestations is not None:
            return self._attestations
        if self.evaluator_root is None:
            raise ConfigError("pinned evaluator is unavailable for canonical attestation signing")
        source_root = (self.evaluator_root / "src").resolve()
        sys.path.insert(0, str(source_root))
        previous_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            module = importlib.import_module("core_prompts_eval.attestations")
        finally:
            sys.dont_write_bytecode = previous_bytecode
            try:
                sys.path.remove(str(source_root))
            except ValueError:
                pass
        module_path = Path(str(module.__file__)).resolve()
        try:
            module_path.relative_to(source_root)
        except ValueError as exc:
            raise ConfigError("canonical attestation module did not load from the pinned evaluator") from exc
        self._attestations = module
        return module

    def signature_message(self, payload: Mapping[str, Any]) -> bytes:
        return self._canonical_attestation_module().signature_message(payload)

    def validate_signed(
        self,
        payload: Mapping[str, Any],
        trust_root: Mapping[str, Any],
        purpose: str,
    ) -> None:
        try:
            self._canonical_attestation_module().validate_signed_attestation(
                payload,
                trust_root=trust_root,
                expected_purpose=purpose,
            )
        except ValueError as exc:
            raise ConfigError("canonical attestation validation failed") from exc

    def _validate_canonical_schema(self, payload: Mapping[str, Any], filename: str, label: str) -> None:
        if self.evaluator_root is None:
            raise ConfigError(f"pinned evaluator is unavailable for {label} schema validation")
        schema = _read_json(
            self.evaluator_root / "evals" / "schemas" / filename,
            f"{label} schema",
        )
        try:
            jsonschema.validate(dict(payload), schema)
        except jsonschema.ValidationError as exc:
            raise ConfigError(f"{label} failed canonical schema validation") from exc

    def execute_phase(
        self,
        phase: str,
        submission_path: Path,
        sealed_bundle_override: Path | None = None,
    ) -> dict[str, Any]:
        """Execute one CI phase while carrying private artifacts between jobs."""
        try:
            if phase == "validate":
                evaluator = self._prepare_evaluator_only()
                submission = self.validate_submission(submission_path, evaluator)
                return _phase_complete("validate", str(submission["submission_id"]))
            if phase == "authorize-budget":
                expected = _configured_identity(
                    self.config["budget_authorizer_runner_identity"],
                    "budget authorizer runner identity",
                )
                if os.environ.get("CI_RUNNER_ID") != expected:
                    raise ConfigError("budget authorization did not run on its protected runner identity")
                self._prepare_evaluator_only()
                primary_path = _configured_path(dict(self.config["primary"])["run_plan"], "primary run plan")
                reproduction_path = _configured_path(
                    dict(self.config["reproduction"])["run_plan"],
                    "reproduction run plan",
                )
                primary_plan = _read_json(primary_path, "primary run plan")
                reproduction_plan = _read_json(reproduction_path, "reproduction run plan")
                budget = _object(self.config["global_token_budget"], "global token budget")
                allocations = _object(budget["allocations"], "global token allocations")
                reservations = [
                    {
                        "entry_id": "conformance",
                        "phase": "adapter_conformance",
                        "run_id": "adapter-probes",
                        "receipt_sha256s": [artifact_hash(primary_path)],
                        "reserved": int(allocations["adapter_conformance"]),
                    },
                    {
                        "entry_id": "primary",
                        "phase": "primary",
                        "run_id": str(primary_plan["run_id"]),
                        "receipt_sha256s": [artifact_hash(primary_path)],
                        "reserved": int(primary_plan["token_budget"]),
                    },
                    {
                        "entry_id": "reproduction",
                        "phase": "reproduction",
                        "run_id": str(reproduction_plan["run_id"]),
                        "receipt_sha256s": [artifact_hash(reproduction_path)],
                        "reserved": int(reproduction_plan["token_budget"]),
                    },
                    {
                        "entry_id": "judge",
                        "phase": "adjudication",
                        "run_id": f"judge-{primary_plan['run_id']}",
                        "receipt_sha256s": [artifact_hash({"judges": self.config["judge_commands"]})],
                        "reserved": min(
                            int(allocations["judge_adjudication"]),
                            int(budget["judge_max_tokens_per_call"])
                            * len(self.config["judge_commands"]),
                        ),
                    },
                ]
                ledger = self.create_reserved_global_token_ledger(
                    f"{primary_plan['slug']}-{primary_plan['run_id']}",
                    reservations,
                )
                return _phase_complete("authorize-budget", str(ledger["ledger_id"]))
            (
                evaluator,
                baseline_path,
                candidate_path,
                submission,
                primary_plan_path,
                primary_plan,
                reproduction_plan_path,
                reproduction_plan,
                sealed_bundle,
            ) = self._prepare(submission_path, sealed_bundle_override)
            if phase == "conformance":
                self._require_reserved_global_token_ledger("conformance")
                actual_runner = os.environ.get("CI_RUNNER_ID")
                expected_runner = _configured_identity(
                    self.config["adapter_conformance_runner_identity"],
                    "adapter conformance runner identity",
                )
                if not actual_runner or actual_runner != expected_runner:
                    raise ConfigError("adapter conformance did not run on its protected runner identity")
                certificates = self.run_adapter_conformance(
                    evaluator,
                    primary_plan,
                    reproduction_plan,
                )
                self.bind_adapter_conformance(primary_plan_path, primary_plan, certificates, "primary")
                self.bind_adapter_conformance(
                    reproduction_plan_path,
                    reproduction_plan,
                    certificates,
                    "reproduction",
                )
                return _phase_complete("conformance", artifact_hash(certificates))
            if phase == "primary":
                self._require_reserved_global_token_ledger("primary")
                self._require_runner_identity("primary")
                self.require_adapter_conformance(primary_plan)
                self._sign_sealed_attestation(sealed_bundle, primary_plan)
                run_dir = self._evaluate(
                    evaluator,
                    baseline_path,
                    candidate_path,
                    primary_plan_path,
                    primary_plan,
                    "primary",
                )
                protected = self.protect_run(run_dir, label="primary", signing=self.config["signing"])
                if protected.get("promotion_allowed") is not True:
                    return protected
                self._persist_run(run_dir, "primary")
                return _phase_complete("primary", str(primary_plan["run_id"]))
            if phase == "reproduction":
                self._require_reserved_global_token_ledger("reproduction")
                self._require_runner_identity("reproduction")
                self.require_adapter_conformance(reproduction_plan)
                primary_run = self.private_root / "runs" / "primary"
                if not primary_run.is_dir():
                    return self.non_promote("missing_primary")
                verify_hash_chain(primary_run)
                self._require_existing_sealed_attestation()
                run_dir = self._evaluate(
                    evaluator,
                    baseline_path,
                    candidate_path,
                    reproduction_plan_path,
                    reproduction_plan,
                    "reproduction",
                )
                protected = self.protect_run(run_dir, label="reproduction", signing=self.config["signing"])
                if protected.get("promotion_allowed") is not True:
                    return protected
                self._persist_run(run_dir, "reproduction")
                return _phase_complete("reproduction", str(reproduction_plan["run_id"]))
            if phase == "finalize":
                primary_run = self.private_root / "runs" / "primary"
                reproduction_run = self.private_root / "runs" / "reproduction"
                if not primary_run.is_dir():
                    return self.non_promote("missing_primary")
                if not reproduction_run.is_dir():
                    return self.non_promote("missing_reproduction")
                self._require_existing_sealed_attestation()
                score = self._score(evaluator, primary_run, reproduction_run, sealed_bundle)
                receipt_results = self._receipt_results(score)
                primary = self.protect_run(
                    primary_run,
                    label="primary-final",
                    signing=self.config["signing"],
                    receipt_results=receipt_results,
                )
                reproduction = self.protect_run(
                    reproduction_run,
                    label="reproduction-final",
                    signing=self.config["signing"],
                    receipt_results=receipt_results,
                )
                if primary.get("promotion_allowed") is not True:
                    return primary
                if reproduction.get("promotion_allowed") is not True:
                    return reproduction
                qualifications = self._qualify(primary_run, reproduction_run, sealed_bundle)
                final_ledger = self._finalize_ledger_from_artifacts(
                    primary_run,
                    reproduction_run,
                    qualifications,
                    primary,
                    reproduction,
                )
                verdict = self._verdict(
                    submission,
                    primary_run,
                    reproduction_run,
                    score,
                    qualifications,
                    primary,
                    reproduction,
                    final_ledger,
                )
                self._publish(verdict, score, qualifications, primary, reproduction)
                return {
                    "schema_version": "ProtectedEvaluationPublicResult.v1",
                    "phase": "finalize",
                    "status": str(verdict.get("status") or "inconclusive"),
                    "promotion_allowed": verdict.get("status") == "promote",
                    "reason_codes": [],
                }
            raise ConfigError("unsupported protected evaluator phase")
        except ConfigError as exc:
            reason = "adapter_conformance_inconclusive" if phase == "conformance" else "protected_failure"
            return self.non_promote(reason, str(exc))

    def _prepare_evaluator_only(self) -> Path:
        evaluator_cfg = dict(self.config["evaluator"])
        evaluator = self.checkout_read_only(
            str(evaluator_cfg["repository"]),
            str(evaluator_cfg["revision"]),
            "evaluator",
        )
        self.evaluator_root = evaluator
        self._materialize_evaluator_trust_store()
        return evaluator

    def _prepare(
        self,
        submission_path: Path,
        sealed_bundle_override: Path | None,
    ) -> tuple[Path, Path, Path, dict[str, Any], Path, dict[str, Any], Path, dict[str, Any], Path]:
        evaluator_cfg = dict(self.config["evaluator"])
        artifact_cfg = dict(self.config["artifacts"])
        evaluator = self.checkout_read_only(
            str(evaluator_cfg["repository"]), str(evaluator_cfg["revision"]), "evaluator"
        )
        self.evaluator_root = evaluator
        self._materialize_evaluator_trust_store()
        baseline = self.checkout_read_only(
            str(artifact_cfg["repository"]), str(artifact_cfg["baseline_revision"]), "baseline"
        )
        candidate = self.checkout_read_only(
            str(artifact_cfg["repository"]), str(artifact_cfg["candidate_revision"]), "candidate"
        )
        submission = self.validate_submission(submission_path, evaluator)
        baseline_path = baseline / str(artifact_cfg["skill_path"])
        candidate_path = candidate / str(artifact_cfg["skill_path"])
        _require_hash(baseline_path, str(submission["baseline_sha256"]), "baseline")
        _require_hash(candidate_path, str(submission["candidate_sha256"]), "candidate")
        bound_primary = self.private_root / "run-plans" / "primary.json"
        bound_reproduction = self.private_root / "run-plans" / "reproduction.json"
        use_bound = bound_primary.is_file() or bound_reproduction.is_file()
        if use_bound and not (bound_primary.is_file() and bound_reproduction.is_file()):
            raise ConfigError("protected adapter conformance run-plan bindings are incomplete")
        primary_plan_path = (
            bound_primary
            if use_bound
            else _configured_path(dict(self.config["primary"])["run_plan"], "primary run plan")
        )
        reproduction_plan_path = (
            bound_reproduction
            if use_bound
            else _configured_path(
                dict(self.config["reproduction"])["run_plan"],
                "reproduction run plan",
            )
        )
        primary_plan = _read_json(primary_plan_path, "primary run plan")
        reproduction_plan = _read_json(reproduction_plan_path, "reproduction run plan")
        verify_reproduction_independence(
            primary_plan,
            reproduction_plan,
            _configured_identity(
                dict(self.config["primary"])["runner_identity"],
                "primary runner identity",
            ),
            _configured_identity(
                dict(self.config["reproduction"])["runner_identity"],
                "reproduction runner identity",
            ),
        )
        self._validate_plan_bindings(primary_plan, submission, phase="primary")
        self._validate_plan_bindings(reproduction_plan, submission, phase="reproduction")
        sealed_bundle = (
            sealed_bundle_override.resolve()
            if sealed_bundle_override
            else _configured_path(self.config["sealed_bundle"], "sealed bundle")
        )
        self._validate_protected_path(sealed_bundle, evaluator, baseline, candidate)
        for plan in (primary_plan, reproduction_plan):
            dataset = _object(plan.get("dataset"), "run plan dataset")
            _require_hash(sealed_bundle, str(dataset.get("sha256") or ""), "sealed bundle")
        return (
            evaluator,
            baseline_path,
            candidate_path,
            submission,
            primary_plan_path,
            primary_plan,
            reproduction_plan_path,
            reproduction_plan,
            sealed_bundle,
        )

    def run_adapter_conformance(
        self,
        evaluator: Path,
        primary_plan: Mapping[str, Any],
        reproduction_plan: Mapping[str, Any],
    ) -> dict[str, Path]:
        if self.private_root.joinpath("adapter-conformance").exists():
            raise ConfigError("immutable adapter conformance output already exists")
        signing = dict(dict(self.config["signing"])["adapter_conformance"])
        trust_root_payload = self._trust_root_for_purpose(
            "adapter_conformance",
            str(signing["key_id"]),
        )
        primary_cells = {str(cell["id"]): dict(cell) for cell in primary_plan["model_cells"]}
        reproduction_cells = {str(cell["id"]): dict(cell) for cell in reproduction_plan["model_cells"]}
        if primary_cells != reproduction_cells:
            raise ConfigError("primary and reproduction must preregister the same adapter cells")
        registry = _read_json(evaluator / "evals" / "adapters" / "registry.json", "adapter registry")
        adapters = {
            str(item["id"]): dict(item)
            for item in registry.get("adapters", [])
            if isinstance(item, Mapping)
        }
        host_adapters = {
            "codex": "codex-jsonl-experimental",
            "kiro": "kiro-stream-json-experimental",
        }
        if {str(cell.get("host") or "") for cell in primary_cells.values()} != set(host_adapters):
            raise ConfigError("protected promotion requires exactly one Codex and one Kiro conformance cell")
        certificates: dict[str, Path] = {}
        for cell_id, cell in primary_cells.items():
            host = str(cell["host"])
            adapter_id = host_adapters[host]
            adapter = adapters.get(adapter_id)
            if adapter is None:
                raise ConfigError("protected adapter registry is missing Codex or Kiro")
            adapter_sha256 = _adapter_binding_hash(evaluator, adapter)
            executable = shutil.which(str(next(iter(adapter["cli_version_argv"]))))
            if executable is None:
                raise ConfigError("protected adapter CLI is unavailable")
            cli_sha256 = artifact_hash(Path(executable).resolve())
            cell_tool_policy = _cell_tool_policy(primary_plan, cell)
            tool_policy_sha256 = artifact_hash(cell_tool_policy)
            approval_policy_sha256 = artifact_hash(dict(primary_plan["approval_policy"]))
            credential_binding = self.materialize_credential_binding(host)
            evidence_dir = self.private_root / "adapter-conformance" / cell_id
            evidence_path = evidence_dir / "probe-evidence.json"
            raw_trace_path = evidence_dir / "raw-trace.jsonl"
            probe_root = self.work_root / "adapter-probes" / cell_id
            workspace = probe_root / "workspace"
            session_root = probe_root / "session"
            workspace.mkdir(parents=True)
            session_root.mkdir(parents=True)
            self._initialize_microrepo(workspace)
            command = list(self.config["adapter_conformance_command"])
            command.extend(
                [
                    "--evaluator-root",
                    str(evaluator),
                    "--adapter-id",
                    adapter_id,
                    "--cell-id",
                    cell_id,
                    "--model",
                    str(cell["resolved_model_identifier"]),
                    "--model-version",
                    str(cell["model_version"]),
                    "--effort",
                    str(cell["effort"]),
                    "--tool-policy-json",
                    canonical_json(cell_tool_policy),
                    "--credential-descriptor",
                    str(credential_binding["descriptor_path"]),
                    "--workspace",
                    str(workspace),
                    "--session-root",
                    str(session_root),
                    "--output",
                    str(evidence_path),
                    "--raw-trace",
                    str(raw_trace_path),
                ]
            )
            evidence = self.run_output_command(
                command,
                stage=f"adapter_conformance_{host}",
                output=evidence_path,
                cwd=workspace,
                extra_env={
                    "HOME": str(session_root),
                    "TMPDIR": str(session_root),
                    "CODEX_HOME": str(session_root),
                    "KIRO_HOME": str(session_root),
                    "PROTECTED_PROBE_WORKSPACE": str(workspace),
                },
                authority="repo-write-subagents",
                tool_policy=cell_tool_policy,
            )
            expected = {
                "adapter_id": adapter_id,
                "adapter_version": str(adapter["version"]),
                "adapter_sha256": adapter_sha256,
                "cli_sha256": cli_sha256,
                "cell_id": cell_id,
                "host": host,
                "resolved_model_identifier": str(cell["resolved_model_identifier"]),
                "model_version": str(cell["model_version"]),
                "effort": str(cell["effort"]),
                "tool_policy_sha256": tool_policy_sha256,
                "approval_policy_sha256": approval_policy_sha256,
                "credential_descriptor_sha256": credential_binding["descriptor_sha256"],
            }
            validate_adapter_probe_evidence(evidence, expected)
            version_pattern = str(adapter.get("cli_version_pattern") or "")
            if not version_pattern or re.fullmatch(version_pattern, str(evidence["cli_version"])) is None:
                raise ConfigError("adapter probe CLI version does not match its pinned registry pattern")
            if not raw_trace_path.is_file() or artifact_hash(raw_trace_path) != evidence["raw_trace_sha256"]:
                raise ConfigError("adapter probe raw trace commitment is stale")
            for receipt_kind, field in (
                ("fixture-receipts", "fixture_receipt_sha256s"),
                ("probe-receipts", "probe_receipt_sha256s"),
            ):
                for digest in evidence[field]:
                    receipt_path = evidence_dir / receipt_kind / f"{digest}.json"
                    if not receipt_path.is_file() or artifact_hash(receipt_path) != digest:
                        raise ConfigError("adapter conformance evidence receipt is missing or stale")
            usage = _object(evidence["usage"], "adapter conformance usage")
            _exclusive_json(
                evidence_dir / "token-usage.json",
                {
                    "schema_version": "ProtectedTokenUsage.v1",
                    "raw": usage["raw"],
                    "cached": usage["cached"],
                    "billed": usage["billed"],
                    "receipt_sha256s": [
                        *evidence["fixture_receipt_sha256s"],
                        *evidence["probe_receipt_sha256s"],
                    ],
                },
            )
            now = dt.datetime.now(dt.timezone.utc)
            unsigned = {
                "schema_version": "AdapterConformance.v1",
                "conformance_id": artifact_hash(f"{cell_id}\0{evidence['raw_trace_sha256']}")[:32],
                "issuer": "protected-core-prompts-evaluator",
                **expected,
                "cli_version": evidence["cli_version"],
                "authentication_verified": evidence["authentication_verified"],
                "response_model_resolved": True,
                "usage_complete": True,
                "retry_semantics_verified": True,
                "tool_semantics_verified": True,
                "session_isolation_verified": True,
                "authorship_boundary_verified": True,
                "fixture_receipt_sha256s": list(evidence["fixture_receipt_sha256s"]),
                "probe_receipt_sha256s": list(evidence["probe_receipt_sha256s"]),
                "qualified": True,
                "created_at": now.isoformat().replace("+00:00", "Z"),
                "expires_at": (now + dt.timedelta(days=30)).isoformat().replace("+00:00", "Z"),
            }
            signed = self.sign_inline(unsigned, "adapter_conformance")
            self.validate_signed(signed, trust_root_payload, "adapter_conformance")
            self._validate_canonical_schema(
                signed,
                "adapter-conformance.schema.json",
                "adapter conformance",
            )
            certificate_path = evidence_dir / "adapter-conformance.json"
            _exclusive_json(certificate_path, signed)
            public_path = self.public_root / "adapter-conformance" / f"{cell_id}.json"
            _exclusive_json(public_path, signed)
            certificates[cell_id] = certificate_path
        _exclusive_json(
            self.private_root / "adapter-conformance" / "index.json",
            {
                "schema_version": "AdapterConformanceIndex.v1",
                "bindings": {
                    cell_id: _path_binding(path) for cell_id, path in sorted(certificates.items())
                },
            },
        )
        return certificates

    def _initialize_microrepo(self, workspace: Path) -> None:
        self._run(["git", "init", "-b", "main"], stage="initialize_microrepo", cwd=workspace)
        self._run(
            ["git", "config", "--local", "user.name", "Protected Evaluator"],
            stage="configure_microrepo_name",
            cwd=workspace,
        )
        self._run(
            ["git", "config", "--local", "user.email", "protected-evaluator.invalid"],
            stage="configure_microrepo_email",
            cwd=workspace,
        )
        remotes = self._run(["git", "remote"], stage="verify_microrepo_remotes", cwd=workspace)
        if remotes.stdout.strip():
            raise ConfigError("protected Batman microrepo must not contain remotes")

    def bind_adapter_conformance(
        self,
        source_path: Path,
        plan: Mapping[str, Any],
        certificates: Mapping[str, Path],
        label: str,
    ) -> Path:
        cells = []
        for raw in plan["model_cells"]:
            cell = dict(raw)
            cell_id = str(cell["id"])
            certificate = certificates.get(cell_id)
            if certificate is None:
                raise ConfigError("adapter conformance is missing for a run-plan cell")
            cell["adapter_conformance_binding"] = _path_binding(certificate)
            certificate_payload = _read_json(certificate, "adapter conformance certificate")
            cell["adapter"] = {
                "id": certificate_payload["adapter_id"],
                "version": certificate_payload["adapter_version"],
                "sha256": certificate_payload["adapter_sha256"],
            }
            cell["cli_version"] = certificate_payload["cli_version"]
            cell["cli_sha256"] = certificate_payload["cli_sha256"]
            cell["tool_policy"] = dict(self.config["registered_trial_tool_policy"])
            cell["credential_binding"] = self.materialize_credential_binding(str(cell["host"]))
            cells.append(cell)
        bound = {**plan, "model_cells": cells}
        if len(cells) > 1:
            bound.pop("adapter", None)
            bound.pop("tool_policy", None)
        trust_root = self.evaluator_trust_store_path
        if trust_root is None:
            raise ConfigError("portable evaluator trust store is missing")
        bound["trust_root_path"] = str(trust_root)
        bound["trust_root_sha256"] = artifact_hash(trust_root)
        if self.evaluator_root is None:
            raise ConfigError("pinned evaluator is unavailable for run-plan validation")
        schema = _read_json(
            self.evaluator_root / "evals" / "schemas" / "eval-run-plan.schema.json",
            "evaluation run-plan schema",
        )
        try:
            jsonschema.validate(bound, schema)
        except jsonschema.ValidationError as exc:
            raise ConfigError("adapter-bound run plan failed canonical schema validation") from exc
        destination = self.private_root / "run-plans" / f"{label}.json"
        _exclusive_json(destination, bound)
        return destination

    def _materialize_evaluator_trust_store(self) -> Path:
        binding = _object(self.config["evaluator_trust_store"], "evaluator_trust_store")
        source = _configured_path(binding["path"], "evaluator trust store")
        expected = str(binding["sha256"])
        if not source.is_file() or artifact_hash(source) != expected:
            raise ConfigError("evaluator trust store binding is missing or stale")
        if source.stat().st_size > int(dict(self.config["limits"])["max_public_bytes"]):
            raise ConfigError("evaluator trust store exceeds the public artifact size cap")
        private = self.private_root / "trust-stores" / "evaluator-trust-store.json"
        public = self.public_root / "evaluator-trust-store.json"
        for destination in (private, public):
            if destination.exists():
                if artifact_hash(destination) != expected:
                    raise ConfigError("materialized evaluator trust store is stale")
                continue
            _exclusive_bytes(destination, source.read_bytes())
        self.evaluator_trust_store_path = private
        return private

    def _trust_store_payload(self) -> dict[str, Any]:
        path = self.evaluator_trust_store_path
        if path is None:
            binding = _object(self.config["evaluator_trust_store"], "evaluator_trust_store")
            path = _configured_path(binding["path"], "evaluator trust store")
        return _read_json(path, "evaluator trust store")

    def _trust_root_for_purpose(self, purpose: str, key_id: str) -> dict[str, Any]:
        store = self._trust_store_payload()
        matches = [
            dict(root)
            for root in store.get("keys", [])
            if isinstance(root, Mapping)
            and root.get("key_id") == key_id
            and root.get("purposes") == [purpose]
        ]
        if len(matches) != 1:
            raise ConfigError("signing key is not uniquely bound in the evaluator trust store")
        return matches[0]

    def create_reserved_global_token_ledger(
        self,
        experiment_id: str,
        reservations: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        ledger_dir = self.private_root / "token-ledger"
        if ledger_dir.exists():
            raise ConfigError("global token ledger already exists")
        budget = _object(self.config["global_token_budget"], "global_token_budget")
        allocations = _object(budget["allocations"], "global token allocations")
        phase_allocation = {
            "adapter_conformance": "adapter_conformance",
            "primary": "primary",
            "reproduction": "reproduction",
            "adjudication": "judge_adjudication",
        }
        entries: list[dict[str, Any]] = []
        reserved_by_phase = {phase: 0 for phase in phase_allocation}
        now = _now()
        seen: set[str] = set()
        for raw in reservations:
            entry = dict(raw)
            entry_id = str(entry.get("entry_id") or "")
            phase = str(entry.get("phase") or "")
            reserved = entry.get("reserved")
            hashes = entry.get("receipt_sha256s")
            if (
                not entry_id
                or entry_id in seen
                or phase not in phase_allocation
                or isinstance(reserved, bool)
                or not isinstance(reserved, int)
                or reserved <= 0
                or not isinstance(hashes, list)
                or not hashes
                or any(not HASH_RE.fullmatch(str(value)) for value in hashes)
            ):
                raise ConfigError("global token reservation is invalid")
            seen.add(entry_id)
            reserved_by_phase[phase] += reserved
            entries.append(
                {
                    **entry,
                    "raw": 0,
                    "cached": 0,
                    "billed": 0,
                    "recorded_at": now,
                }
            )
        for phase, reserved in reserved_by_phase.items():
            if reserved > int(allocations[phase_allocation[phase]]):
                raise ConfigError("global token reservation exceeds its preregistered phase allocation")
        total_reserved = sum(reserved_by_phase.values())
        if total_reserved > int(budget["cap"]):
            raise ConfigError("global token reservations exceed the 5M cap")
        unsigned = {
            "schema_version": "GlobalTokenLedger.v1",
            "ledger_id": artifact_hash(f"{experiment_id}\0global-token-ledger")[:32],
            "issuer": "protected-core-prompts-evaluator",
            "experiment_id": experiment_id,
            "profile": "promotion",
            "token_cap": 5_000_000,
            "sequence": 0,
            "previous_ledger_sha256": None,
            "entries": entries,
            "totals": {"reserved": total_reserved, "raw": 0, "cached": 0, "billed": 0},
            "remaining_raw_tokens": 5_000_000,
            "status": "open",
            "created_at": now,
            "updated_at": now,
            "expires_at": _days_from_now(30),
        }
        signed = self.sign_inline(unsigned, "global_token_ledger")
        self._validate_canonical_schema(
            signed,
            "global-token-ledger.schema.json",
            "global token ledger",
        )
        self._validate_global_token_ledger(signed)
        _exclusive_json(ledger_dir / "000000.json", signed)
        return signed

    def finalize_global_token_ledger(
        self,
        observed: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        ledger_dir = self.private_root / "token-ledger"
        previous_path = ledger_dir / "000000.json"
        previous = _read_json(previous_path, "reserved global token ledger")
        self._validate_global_token_ledger(previous)
        entries: list[dict[str, Any]] = []
        for raw_entry in previous["entries"]:
            entry = dict(raw_entry)
            usage = observed.get(str(entry["entry_id"]))
            if not isinstance(usage, Mapping):
                raise ConfigError("global token ledger is missing observed usage")
            values = {field: usage.get(field) for field in ("raw", "cached", "billed")}
            if (
                any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values.values())
                or values["raw"] > int(entry["reserved"])
                or values["cached"] > values["raw"]
                or values["billed"] > values["raw"]
            ):
                raise ConfigError("global token ledger observed usage is invalid")
            hashes = usage.get("receipt_sha256s")
            if not isinstance(hashes, list) or not hashes or any(not HASH_RE.fullmatch(str(value)) for value in hashes):
                raise ConfigError("global token ledger observed receipt hashes are invalid")
            entries.append(
                {
                    **entry,
                    **values,
                    "receipt_sha256s": list(hashes),
                    "recorded_at": _now(),
                }
            )
        totals = {
            field: sum(int(entry[field]) for entry in entries)
            for field in ("reserved", "raw", "cached", "billed")
        }
        if totals["raw"] > 5_000_000:
            raise ConfigError("global raw-token ledger exceeds 5000000")
        unsigned = {
            **{key: value for key, value in previous.items() if key != "signature"},
            "sequence": 1,
            "previous_ledger_sha256": artifact_hash(previous_path),
            "entries": entries,
            "totals": totals,
            "remaining_raw_tokens": 5_000_000 - totals["raw"],
            "status": "final",
            "updated_at": _now(),
        }
        signed = self.sign_inline(unsigned, "global_token_ledger")
        self._validate_canonical_schema(
            signed,
            "global-token-ledger.schema.json",
            "global token ledger",
        )
        self._validate_global_token_ledger(
            signed,
            expected_previous_sha256=artifact_hash(previous_path),
        )
        _exclusive_json(ledger_dir / "000001.json", signed)
        _exclusive_json(self.public_root / "global-token-ledger.json", signed)
        return signed

    def _require_reserved_global_token_ledger(self, entry_id: str) -> dict[str, Any]:
        path = self.private_root / "token-ledger" / "000000.json"
        ledger = _read_json(path, "reserved global token ledger")
        self._validate_global_token_ledger(ledger)
        matches = [entry for entry in ledger["entries"] if entry.get("entry_id") == entry_id]
        if len(matches) != 1 or matches[0].get("reserved", 0) <= 0 or matches[0].get("raw") != 0:
            raise ConfigError("required global token reservation is missing or already consumed")
        return matches[0]

    def _validate_global_token_ledger(
        self,
        payload: Mapping[str, Any],
        *,
        expected_previous_sha256: str | None = None,
    ) -> None:
        try:
            self._canonical_attestation_module().validate_global_token_ledger(
                payload,
                trust_root=self._trust_store_payload(),
                expected_previous_sha256=expected_previous_sha256,
            )
        except ValueError as exc:
            raise ConfigError("canonical global token ledger validation failed") from exc

    def require_adapter_conformance(self, plan: Mapping[str, Any]) -> None:
        trust_path = Path(str(plan.get("trust_root_path") or "")).resolve()
        if not trust_path.is_file() or plan.get("trust_root_sha256") != artifact_hash(trust_path):
            raise ConfigError("adapter conformance trust-root binding is missing or stale")
        trust_root = _read_json(
            trust_path,
            "adapter conformance trust root",
        )
        seen_hosts: set[str] = set()
        for raw in plan.get("model_cells", []):
            cell = _object(raw, "run-plan cell")
            binding = cell.get("adapter_conformance_binding")
            if not isinstance(binding, Mapping):
                raise ConfigError("adapter conformance binding is missing from a run-plan cell")
            path = Path(str(binding.get("path") or "")).resolve()
            if not path.is_file() or binding.get("sha256") != artifact_hash(path):
                raise ConfigError("adapter conformance binding is missing or stale")
            certificate = _read_json(path, "adapter conformance certificate")
            self.validate_signed(certificate, trust_root, "adapter_conformance")
            self._validate_canonical_schema(
                certificate,
                "adapter-conformance.schema.json",
                "adapter conformance",
            )
            expected_cell = {
                "cell_id": cell.get("id"),
                "host": cell.get("host"),
                "resolved_model_identifier": cell.get("resolved_model_identifier"),
                "model_version": cell.get("model_version"),
                "effort": cell.get("effort"),
            }
            for field, expected in expected_cell.items():
                if certificate.get(field) != expected:
                    raise ConfigError("adapter conformance certificate has stale cell bindings")
            if certificate.get("qualified") is not True:
                raise ConfigError("adapter conformance certificate is inconclusive")
            seen_hosts.add(str(cell["host"]))
        if seen_hosts != {"codex", "kiro"}:
            raise ConfigError("adapter conformance requires qualified Codex and Kiro certificates")

    def _require_runner_identity(self, label: str) -> None:
        expected = _configured_identity(
            dict(self.config[label])["runner_identity"],
            f"{label} runner identity",
        )
        actual = os.environ.get("CI_RUNNER_ID")
        if not actual or actual != expected:
            raise ConfigError(f"{label} did not execute on its preregistered protected runner identity")

    def _persist_run(self, run_dir: Path, label: str) -> Path:
        destination = self.private_root / "runs" / label
        if destination.exists():
            raise ConfigError(f"immutable {label} run already exists")
        shutil.copytree(run_dir, destination, symlinks=False)
        verify_hash_chain(destination)
        return destination

    def _require_existing_sealed_attestation(self) -> dict[str, Any]:
        path = self.private_root / "sealed-bundle-attestation.json"
        payload = _read_json(path, "signed sealed bundle attestation")
        self.validate_signed(payload, self._trust_store_payload(), "sealed_bundle")
        return payload

    def _validate_protected_path(self, path: Path, *candidate_readable_roots: Path) -> None:
        if not path.is_file() or any(component.is_symlink() for component in (path, *path.parents)):
            raise ConfigError("sealed bundle path is missing or uses a symlink")
        for root in (*candidate_readable_roots, self.work_root, self.public_root):
            try:
                path.relative_to(root.resolve())
            except ValueError:
                continue
            raise ConfigError("sealed bundle is inside a candidate-readable or public root")

    def _validate_plan_bindings(
        self,
        plan: Mapping[str, Any],
        submission: Mapping[str, Any],
        *,
        phase: str | None = None,
    ) -> None:
        if plan.get("profile") != "promotion" or plan.get("independent_reproduction_required") is not True:
            raise ConfigError("protected runs require a promotion plan with independent reproduction")
        for field in (
            "baseline_sha256",
            "candidate_sha256",
            "goal_contract_sha256",
            "topology_sha256",
            "evaluation_policy_sha256",
        ):
            if plan.get(field) != submission.get(field):
                raise ConfigError(f"run plan has stale {field}")
        if plan.get("slug") != submission.get("slug"):
            raise ConfigError("run plan has stale slug")
        artifacts = dict(self.config["artifacts"])
        if (
            plan.get("baseline_revision") != artifacts["baseline_revision"]
            or plan.get("candidate_revision") != artifacts["candidate_revision"]
        ):
            raise ConfigError("run plan has stale baseline or candidate revision")
        registered_policy = dict(self.config["registered_trial_tool_policy"])
        cells = plan.get("model_cells")
        if not isinstance(cells, list) or not cells:
            raise ConfigError("protected promotion requires resolved model cells")
        for cell in cells:
            if _cell_tool_policy(plan, _object(cell, "run-plan cell")) != registered_policy:
                raise ConfigError("protected promotion contains an unregistered tool policy")
        budget = plan.get("token_budget")
        if isinstance(budget, bool) or not isinstance(budget, int) or budget > self.raw_token_cap:
            raise ConfigError("run plan exceeds the protected raw-token cap")
        if phase is not None:
            allocations = _object(
                _object(self.config["global_token_budget"], "global token budget")["allocations"],
                "global token allocations",
            )
            if phase not in {"primary", "reproduction"} or budget > int(allocations[phase]):
                raise ConfigError("run plan exceeds its preregistered global token allocation")

    def _sign_sealed_attestation(self, sealed_bundle: Path, plan: Mapping[str, Any]) -> Path:
        payload = _read_json(
            _configured_path(self.config["sealed_attestation"], "sealed bundle attestation"),
            "sealed bundle attestation",
        )
        dataset = _object(plan.get("dataset"), "run plan dataset")
        if payload.get("bundle_sha256") != artifact_hash(sealed_bundle):
            raise ConfigError("sealed bundle attestation has a stale bundle hash")
        if payload.get("dataset_sha256") != dataset.get("sha256") or payload.get("candidate_visible") is not False:
            raise ConfigError("sealed bundle attestation is stale or not candidate blind")
        signed = self.sign_inline(payload, "sealed_bundle")
        self._validate_canonical_schema(
            signed,
            "sealed-bundle-attestation.schema.json",
            "sealed bundle attestation",
        )
        path = self.private_root / "sealed-bundle-attestation.json"
        _exclusive_json(path, signed)
        return path

    def _evaluate(
        self,
        evaluator: Path,
        baseline: Path,
        candidate: Path,
        plan_path: Path,
        plan: Mapping[str, Any],
        label: str,
    ) -> Path:
        reports = evaluator / "reports" / "evals"
        command = list(self.config["capability_eval_command"])
        command.extend(
            [
                "--repo-root",
                str(evaluator),
                "compare",
                "--skill",
                str(plan["slug"]),
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--run-plan",
                str(plan_path),
                "--profile",
                "promotion",
                "--allow-model-calls",
                "--max-tokens",
                str(plan["token_budget"]),
            ]
        )
        result = self.run_json_command(
            command,
            stage=f"evaluate_{label}",
            cwd=evaluator,
            authority="repo-write-subagents",
            tool_policy=dict(self.config["registered_trial_tool_policy"]),
        )
        if result.get("status") != "completed" or result.get("run_id") not in (None, plan["run_id"]):
            raise ConfigError(f"{label} evaluation did not complete")
        reported = result.get("artifact_path")
        run_dir = Path(str(reported)).resolve() if reported else reports / str(plan["run_id"])
        if not run_dir.is_dir():
            raise ConfigError(f"{label} evaluation did not emit an immutable run directory")
        return run_dir

    def _score(
        self,
        evaluator: Path,
        primary: Path,
        reproduction: Path,
        sealed_bundle: Path,
    ) -> dict[str, Any]:
        output = self.private_root / "score-report.unsigned.json"
        command = list(self.config["score_command"])
        command.extend(
            [
                "--primary-run",
                str(primary),
                "--reproduction-run",
                str(reproduction),
                "--sealed-bundle",
                str(sealed_bundle),
                "--output",
                str(output),
            ]
        )
        score = self.run_output_command(command, stage="protected_scoring", output=output)
        schema = _read_json(
            evaluator / "evals" / "schemas" / "protected-score-report.schema.json",
            "protected score report schema",
        )
        try:
            jsonschema.validate(score, schema)
        except jsonschema.ValidationError as exc:
            raise ConfigError("protected score report failed closed-schema validation") from exc
        self._validate_score_report(score, primary, reproduction)
        path = self.private_root / "score-report.json"
        _exclusive_json(path, score)
        return score

    def _validate_score_report(self, score: Mapping[str, Any], primary: Path, reproduction: Path) -> None:
        primary_manifest = _read_json(primary / "manifest.json", "primary manifest")
        reproduction_manifest = _read_json(reproduction / "manifest.json", "reproduction manifest")
        expected = {
            "run_id": primary_manifest.get("run_id"),
            "reproduction_run_id": reproduction_manifest.get("run_id"),
            "baseline_sha256": primary_manifest.get("baseline_sha256"),
            "candidate_sha256": primary_manifest.get("candidate_sha256"),
            "dataset_sha256": primary_manifest.get("dataset_sha256"),
            "scorer_sha256": primary_manifest.get("scorer_sha256"),
            "primary_manifest_sha256": artifact_hash(primary / "manifest.json"),
            "reproduction_manifest_sha256": artifact_hash(reproduction / "manifest.json"),
        }
        stale = [field for field, expected_value in expected.items() if score.get(field) != expected_value]
        if stale:
            raise ConfigError("protected score report has stale run or artifact bindings")
        for field in ("baseline_sha256", "candidate_sha256", "dataset_sha256", "scorer_sha256"):
            if reproduction_manifest.get(field) != primary_manifest.get(field):
                raise ConfigError("primary and reproduction manifests do not bind the same experiment")
        trials = _object(score.get("trial_completeness"), "trial completeness")
        repetitions = _object(score.get("repetition_completeness"), "repetition completeness")
        if (
            trials["completed"] != trials["planned"]
            or trials["missing"] != 0
            or trials["missing"] != trials["planned"] - trials["completed"]
        ):
            raise ConfigError("protected scoring has incomplete trials")
        if repetitions["completed"] != repetitions["planned"]:
            raise ConfigError("protected scoring has incomplete repetitions")
        usage = _object(score.get("token_totals"), "protected score token totals")
        expected_usage = {
            field: int(dict(primary_manifest["token_usage"])[field])
            + int(dict(reproduction_manifest["token_usage"])[field])
            for field in ("raw", "cached", "billed")
        }
        if (
            any(usage[field] != expected_usage[field] for field in expected_usage)
            or usage["cached"] > usage["raw"]
            or usage["billed"] > usage["raw"]
            or usage["raw"] > usage["cap"]
            or usage["cap"] > self.raw_token_cap
        ):
            raise ConfigError("protected score token totals are stale or exceed the cap")
        gates = _object(score.get("hard_gates"), "protected score hard gates")
        if not gates or any(value is not True for value in gates.values()):
            raise ConfigError("protected scoring has a failed hard gate")
        if any(
            metric.get("passed") is not True
            or abs(float(metric["candidate"]) - float(metric["baseline"]) - float(metric["delta"])) > 1e-9
            for metric in score["metrics"]
        ):
            raise ConfigError("protected scoring has a failed metric")
        mutation = _object(score.get("mutation_summary"), "mutation summary")
        if (
            mutation["critical_total"] <= 0
            or mutation["critical_killed"] != mutation["critical_total"]
            or mutation["overall_total"] <= 0
            or mutation["overall_killed"] > mutation["overall_total"]
            or mutation["overall_killed"] / mutation["overall_total"] < 0.95
        ):
            raise ConfigError("protected scoring failed mutation thresholds")
        if score["critical_invariant_violations"] != 0 or score["protected_regression_count"] != 0:
            raise ConfigError("protected scoring found a critical or protected regression")
        expected_receipts = {
            str(receipt["receipt_id"]): str(receipt["run_id"])
            for run_dir in (primary, reproduction)
            for receipt in _read_jsonl(run_dir / "trials" / "receipt-payloads.jsonl", "receipt payloads")
        }
        scored_receipts = self._receipt_results(score)
        if set(scored_receipts) != set(expected_receipts):
            raise ConfigError("protected score report does not cover every execution receipt exactly once")
        for receipt_id, run_id in expected_receipts.items():
            result = scored_receipts[receipt_id]
            if result.get("run_id") != run_id or result.get("result") != "PASS":
                raise ConfigError("protected score report contains a stale or non-passing execution receipt")

    @staticmethod
    def _receipt_results(score: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        results: dict[str, Mapping[str, Any]] = {}
        for raw in score.get("receipt_results", []):
            if not isinstance(raw, Mapping):
                raise ConfigError("protected receipt result must be an object")
            receipt_id = str(raw.get("receipt_id") or "")
            if not receipt_id or receipt_id in results:
                raise ConfigError("protected receipt results require unique receipt IDs")
            results[receipt_id] = raw
        return results

    def _qualify(self, primary: Path, reproduction: Path, sealed_bundle: Path) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for raw in self.config["judge_commands"]:
            judge = dict(raw)
            output = self.private_root / f"judge-{judge['judge_id']}.unsigned.json"
            usage_output = self.private_root / f"judge-{judge['judge_id']}.token-usage.json"
            command = list(judge["command"])
            command.extend(
                [
                    "--judge-id",
                    str(judge["judge_id"]),
                    "--primary-run",
                    str(primary),
                    "--reproduction-run",
                    str(reproduction),
                    "--sealed-bundle",
                    str(sealed_bundle),
                    "--output",
                    str(output),
                    "--usage-output",
                    str(usage_output),
                    "--max-tokens",
                    str(dict(self.config["global_token_budget"])["judge_max_tokens_per_call"]),
                ]
            )
            qualification = self.run_output_command(
                command,
                stage=f"qualify_{judge['judge_id']}",
                output=output,
            )
            if (
                qualification.get("schema_version") != "JudgeQualification.v1"
                or qualification.get("judge_id") != judge["judge_id"]
                or qualification.get("qualified") is not True
            ):
                raise ConfigError("a semantic judge is missing or unqualified")
            signed = self.sign_inline(qualification, "judge_qualification")
            self._validate_canonical_schema(
                signed,
                "judge-qualification.schema.json",
                "judge qualification",
            )
            _exclusive_json(self.private_root / f"judge-{judge['judge_id']}.json", signed)
            usage = _read_json(usage_output, "judge token usage")
            if set(usage) != {
                "schema_version",
                "raw",
                "cached",
                "billed",
                "receipt_sha256s",
            } or usage.get("schema_version") != "ProtectedTokenUsage.v1":
                raise ConfigError("judge token usage has an invalid closed shape")
            self._validate_usage_record(usage, "judge")
            results.append(signed)
        return results

    @staticmethod
    def _validate_usage_record(usage: Mapping[str, Any], label: str) -> None:
        values = [usage.get(field) for field in ("raw", "cached", "billed")]
        if (
            any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values)
            or usage["cached"] > usage["raw"]
            or usage["billed"] > usage["raw"]
            or not isinstance(usage.get("receipt_sha256s"), list)
            or not usage["receipt_sha256s"]
            or len(usage["receipt_sha256s"]) != len(set(usage["receipt_sha256s"]))
            or any(not HASH_RE.fullmatch(str(value)) for value in usage["receipt_sha256s"])
        ):
            raise ConfigError(f"{label} token usage is incomplete or invalid")

    def _finalize_ledger_from_artifacts(
        self,
        primary_run: Path,
        reproduction_run: Path,
        qualifications: Sequence[Mapping[str, Any]],
        protected_primary: Mapping[str, Any],
        protected_reproduction: Mapping[str, Any],
    ) -> dict[str, Any]:
        conformance_records = [
            _read_json(path, "adapter conformance token usage")
            for path in sorted((self.private_root / "adapter-conformance").glob("*/token-usage.json"))
        ]
        if len(conformance_records) != 2:
            raise ConfigError("global token ledger requires Codex and Kiro conformance usage")
        for record in conformance_records:
            self._validate_usage_record(record, "adapter conformance")
        primary_manifest = _read_json(primary_run / "manifest.json", "primary manifest")
        reproduction_manifest = _read_json(reproduction_run / "manifest.json", "reproduction manifest")
        judge_records = [
            _read_json(
                self.private_root / f"judge-{qualification['judge_id']}.token-usage.json",
                "judge token usage",
            )
            for qualification in qualifications
        ]
        for record in judge_records:
            self._validate_usage_record(record, "judge")

        def summed(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
            return {
                field: sum(int(record[field]) for record in records)
                for field in ("raw", "cached", "billed")
            } | {
                "receipt_sha256s": sorted(
                    {
                        str(digest)
                        for record in records
                        for digest in record["receipt_sha256s"]
                    }
                )
            }

        primary_usage = dict(primary_manifest["token_usage"])
        reproduction_usage = dict(reproduction_manifest["token_usage"])
        observed = {
            "conformance": summed(conformance_records),
            "primary": {
                **{field: int(primary_usage[field]) for field in ("raw", "cached", "billed")},
                "receipt_sha256s": [artifact_hash(Path(path)) for path in protected_primary["receipt_paths"]],
            },
            "reproduction": {
                **{field: int(reproduction_usage[field]) for field in ("raw", "cached", "billed")},
                "receipt_sha256s": [
                    artifact_hash(Path(path)) for path in protected_reproduction["receipt_paths"]
                ],
            },
            "judge": summed(judge_records),
        }
        return self.finalize_global_token_ledger(observed)

    def _verdict(
        self,
        submission: Mapping[str, Any],
        primary: Path,
        reproduction: Path,
        score: Mapping[str, Any],
        qualifications: Sequence[Mapping[str, Any]],
        protected_primary: Mapping[str, Any],
        protected_reproduction: Mapping[str, Any],
        global_token_ledger: Mapping[str, Any],
    ) -> dict[str, Any]:
        input_path = self.private_root / "verdict-input.json"
        _exclusive_json(
            input_path,
            {
                "schema_version": "ProtectedVerdictInput.v1",
                "submission_sha256": artifact_hash(dict(submission)),
                "primary_manifest_sha256": artifact_hash(primary / "manifest.json"),
                "reproduction_manifest_sha256": artifact_hash(reproduction / "manifest.json"),
                "score_report_sha256": artifact_hash(dict(score)),
                "judge_qualification_sha256": [artifact_hash(dict(item)) for item in qualifications],
                "evaluator_trust_store": _path_binding(self._require_evaluator_trust_store()),
                "global_token_ledger": _path_binding(
                    self.private_root / "token-ledger" / "000001.json"
                ),
                "auxiliary_receipts": [
                    *[
                        {
                            "phase": "adapter_conformance",
                            "run_id": "adapter-probes",
                            **_path_binding(path),
                        }
                        for path in sorted(
                            (self.private_root / "adapter-conformance").glob("*/token-usage.json")
                        )
                    ],
                    *[
                        {
                            "phase": "adjudication",
                            "run_id": f"judge-{_read_json(primary / 'manifest.json', 'primary manifest')['run_id']}",
                            **_path_binding(
                                self.private_root / f"judge-{item['judge_id']}.token-usage.json"
                            ),
                        }
                        for item in qualifications
                    ],
                ],
                "sealed_bundle_attestation": _path_binding(
                    self.private_root / "sealed-bundle-attestation.json"
                ),
                "primary_receipts": [
                    _receipt_binding(Path(path)) for path in protected_primary["receipt_paths"]
                ],
                "reproduction_receipts": [
                    _receipt_binding(Path(path)) for path in protected_reproduction["receipt_paths"]
                ],
                "primary_manifest": _path_binding(primary / "manifest.json"),
                "reproduction_manifest": _path_binding(reproduction / "manifest.json"),
                "score_report": _path_binding(self.private_root / "score-report.json"),
                "judge_qualifications": [
                    {
                        "judge_id": str(item["judge_id"]),
                        **_path_binding(self.private_root / f"judge-{item['judge_id']}.json"),
                    }
                    for item in qualifications
                ],
            },
        )
        output = self.private_root / "verdict.unsigned.json"
        command = list(self.config["verdict_command"])
        command.extend(["--input", str(input_path), "--output", str(output)])
        verdict = self.run_output_command(command, stage="build_verdict", output=output)
        if verdict.get("schema_version") != "PromotionVerdict.v1":
            raise ConfigError("verdict command did not emit PromotionVerdict.v1")
        if verdict.get("status") != "promote":
            raise ConfigError("protected evidence did not authorize promotion")
        self._validate_verdict_bindings(
            verdict,
            submission,
            primary,
            reproduction,
            score,
            qualifications,
            protected_primary,
            protected_reproduction,
        )
        signed = self.sign_inline(verdict, "promotion_verdict")
        trust_store = _read_json(self._require_evaluator_trust_store(), "evaluator trust store")
        self.validate_signed(signed, trust_store, "promotion_verdict")
        self._validate_canonical_schema(signed, "promotion-verdict.schema.json", "promotion verdict")
        _exclusive_json(self.private_root / "promotion-verdict.json", signed)
        return signed

    def _validate_verdict_bindings(
        self,
        verdict: Mapping[str, Any],
        submission: Mapping[str, Any],
        primary: Path,
        reproduction: Path,
        score: Mapping[str, Any],
        qualifications: Sequence[Mapping[str, Any]],
        protected_primary: Mapping[str, Any],
        protected_reproduction: Mapping[str, Any],
    ) -> None:
        primary_manifest = _read_json(primary / "manifest.json", "primary manifest")
        reproduction_manifest = _read_json(reproduction / "manifest.json", "reproduction manifest")
        expected = {
            "run_id": primary_manifest["run_id"],
            "slug": submission["slug"],
            "baseline_revision": primary_manifest["baseline_revision"],
            "candidate_revision": primary_manifest["candidate_revision"],
            "baseline_sha256": submission["baseline_sha256"],
            "candidate_sha256": submission["candidate_sha256"],
            "goal_contract_sha256": submission["goal_contract_sha256"],
            "topology_sha256": submission["topology_sha256"],
            "dataset_sha256": primary_manifest["dataset_sha256"],
            "scorer_sha256": primary_manifest["scorer_sha256"],
            "run_manifest_sha256": artifact_hash(primary / "manifest.json"),
            "trust_root_sha256": artifact_hash(self._require_evaluator_trust_store()),
        }
        if any(verdict.get(field) != value for field, value in expected.items()):
            raise ConfigError("promotion verdict has stale submission or run bindings")
        _require_binding_hash(
            verdict.get("sealed_bundle_attestation_binding"),
            self.private_root / "sealed-bundle-attestation.json",
            "sealed bundle attestation",
        )
        score_path = self.private_root / "score-report.json"
        _require_binding_hash(verdict.get("score_report_binding"), score_path, "score report")
        if artifact_hash(score_path) != artifact_hash(dict(score)):
            raise ConfigError("protected score report changed before verdict construction")
        ledger_path = self.private_root / "token-ledger" / "000001.json"
        _require_binding_hash(verdict.get("token_ledger_binding"), ledger_path, "global token ledger")
        ledger = _read_json(ledger_path, "global token ledger")
        self._validate_global_token_ledger(ledger)
        ledger_usage = {
            field: int(dict(ledger["totals"])[field])
            for field in ("raw", "cached", "billed")
        }
        if verdict.get("token_usage") != ledger_usage:
            raise ConfigError("promotion verdict token usage does not match the global ledger")
        expected_judges = {
            str(item["judge_id"]): artifact_hash(self.private_root / f"judge-{item['judge_id']}.json")
            for item in qualifications
        }
        actual_judges = {
            str(item.get("judge_id") or ""): str(item.get("sha256") or "")
            for item in verdict.get("judge_qualification_bindings", [])
            if isinstance(item, Mapping)
        }
        if actual_judges != expected_judges:
            raise ConfigError("promotion verdict has stale judge qualification bindings")
        expected_primary_receipts = {
            _read_json(Path(path), "primary receipt")["receipt_id"]: artifact_hash(Path(path))
            for path in protected_primary["receipt_paths"]
        }
        actual_primary_receipts = {
            str(item.get("receipt_id") or ""): str(item.get("sha256") or "")
            for item in verdict.get("receipt_bindings", [])
            if isinstance(item, Mapping)
        }
        if actual_primary_receipts != expected_primary_receipts:
            raise ConfigError("promotion verdict has stale primary receipt bindings")
        reproduction_bindings = verdict.get("reproduction_manifest_bindings")
        if not isinstance(reproduction_bindings, list) or len(reproduction_bindings) != 1:
            raise ConfigError("promotion verdict must bind exactly one independent reproduction")
        reproduction_binding = _object(reproduction_bindings[0], "reproduction binding")
        if (
            reproduction_binding.get("run_id") != reproduction_manifest["run_id"]
            or reproduction_binding.get("sha256") != artifact_hash(reproduction / "manifest.json")
        ):
            raise ConfigError("promotion verdict has a stale reproduction manifest binding")
        expected_reproduction_receipts = {
            _read_json(Path(path), "reproduction receipt")["receipt_id"]: artifact_hash(Path(path))
            for path in protected_reproduction["receipt_paths"]
        }
        actual_reproduction_receipts = {
            str(item.get("receipt_id") or ""): str(item.get("sha256") or "")
            for item in reproduction_binding.get("receipt_bindings", [])
            if isinstance(item, Mapping)
        }
        if actual_reproduction_receipts != expected_reproduction_receipts:
            raise ConfigError("promotion verdict has stale reproduction receipt bindings")
        gates = _object(verdict.get("hard_gates"), "promotion hard gates")
        if not gates or any(value is not True for value in gates.values()):
            raise ConfigError("promotion verdict contains a failed hard gate")
        if verdict.get("profile") != "promotion" or verdict.get("token_cap") != self.raw_token_cap:
            raise ConfigError("promotion verdict has a stale profile or token cap")

    def _require_evaluator_trust_store(self) -> Path:
        path = self.evaluator_trust_store_path
        if path is None or not path.is_file():
            raise ConfigError("materialized evaluator trust store is missing")
        expected = str(_object(self.config["evaluator_trust_store"], "evaluator_trust_store")["sha256"])
        if artifact_hash(path) != expected:
            raise ConfigError("materialized evaluator trust store is stale")
        return path

    def _publish(
        self,
        verdict: Mapping[str, Any],
        score: Mapping[str, Any],
        qualifications: Sequence[Mapping[str, Any]],
        primary: Mapping[str, Any],
        reproduction: Mapping[str, Any],
    ) -> None:
        artifacts: dict[str, object] = {
            "promotion-verdict.json": verdict,
            "score-report.json": score,
            "primary-manifest.json": _read_json(Path(primary["manifest_path"]), "primary manifest"),
            "reproduction-manifest.json": _read_json(
                Path(reproduction["manifest_path"]), "reproduction manifest"
            ),
            "sealed-bundle-attestation.json": _read_json(
                self.private_root / "sealed-bundle-attestation.json", "sealed bundle attestation"
            ),
        }
        for qualification in qualifications:
            artifacts[f"judge-{qualification['judge_id']}.json"] = qualification
        total = sum(len(canonical_json(value).encode("utf-8")) for value in artifacts.values())
        total += self._require_evaluator_trust_store().stat().st_size
        if total > int(dict(self.config["limits"])["max_public_bytes"]):
            raise ConfigError("redacted public artifact size cap exceeded")
        for name, payload in artifacts.items():
            if _contains_private_key(payload):
                raise ConfigError("public artifact contains a private path or trace field")
            _exclusive_json(self.public_root / name, _object(payload, name))
        for label, protected in (("primary", primary), ("reproduction", reproduction)):
            for receipt_path in protected["receipt_paths"]:
                receipt = _read_json(Path(receipt_path), f"{label} signed receipt")
                if _contains_private_key(receipt):
                    raise ConfigError("public receipt artifact contains protected content")
                _exclusive_json(
                    self.public_root / label / "receipts" / Path(receipt_path).name,
                    receipt,
                )


def _load_signer(
    binding: Mapping[str, Any],
    purpose: str,
    root: Mapping[str, Any],
) -> Ed25519PrivateKey:
    private_path = _configured_path(binding["private_key"], f"{purpose} private key")
    if private_path.stat().st_mode & 0o077:
        raise ConfigError("private signing key permissions are too broad")
    try:
        raw = base64.b64decode(private_path.read_text(encoding="ascii").strip(), validate=True)
        key = Ed25519PrivateKey.from_private_bytes(raw)
    except (OSError, ValueError) as exc:
        raise ConfigError("cannot load protected signing key") from exc
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    if root.get("public_key_base64") != base64.b64encode(public).decode("ascii"):
        raise ConfigError("protected signing key does not match its trust root")
    if root.get("purposes") != [purpose]:
        raise ConfigError("protected trust root is not purpose separated")
    if root.get("key_id") != binding.get("key_id"):
        raise ConfigError("private signing key ID does not match the evaluator trust store")
    return key
def verify_hash_chain(run_dir: Path) -> dict[str, Any]:
    chain = _read_json(run_dir / "hash-chain.json", "artifact hash chain")
    entries = chain.get("entries")
    if chain.get("schema_version") != "EvalArtifactChain.v1" or not isinstance(entries, list):
        raise ConfigError("invalid artifact hash chain")
    previous = "0" * 64
    listed: set[str] = set()
    for raw in entries:
        entry = _object(raw, "artifact chain entry")
        relative = Path(str(entry.get("path") or ""))
        if relative.is_absolute() or ".." in relative.parts:
            raise ConfigError("artifact chain contains an unsafe path")
        path = run_dir / relative
        if relative.as_posix() in listed:
            raise ConfigError("artifact chain contains a duplicate path")
        listed.add(relative.as_posix())
        digest = artifact_hash(path)
        if digest != entry.get("sha256"):
            raise ConfigError("artifact chain contains a stale digest")
        previous = artifact_hash(f"{previous}\0{relative.as_posix()}\0{digest}")
        if previous != entry.get("chain_sha256"):
            raise ConfigError("artifact chain commitment is stale")
    if previous != chain.get("root_sha256"):
        raise ConfigError("artifact chain root is stale")
    actual = {
        path.relative_to(run_dir).as_posix()
        for path in run_dir.rglob("*")
        if path.is_file() and path.name != "hash-chain.json"
    }
    if listed != actual:
        raise ConfigError("artifact chain does not cover every run artifact")
    return {"root_sha256": previous, "files": len(entries)}


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not HASH_RE.fullmatch(expected) or not path.is_file() or artifact_hash(path) != expected:
        raise ConfigError(f"{label} hash binding is missing or stale")


def _adapter_binding_hash(repo_root: Path, raw: Mapping[str, Any]) -> str:
    source = raw.get("source")
    payload: dict[str, Any] = {
        "id": str(raw["id"]),
        "version": str(raw["version"]),
        "argv": list(raw["argv"]),
        "parser": str(raw["parser"]),
        "environment_allowlist": list(raw.get("environment_allowlist", [])),
        "promotion_eligible": raw.get("promotion_eligible") is True,
        "experimental": raw.get("experimental") is True,
        "source": source,
        "supported_tool_policy_modes": list(raw["supported_tool_policy_modes"]),
        "hermetic": raw.get("hermetic") is True,
        "fixed_environment": dict(sorted(dict(raw.get("fixed_environment", {})).items())),
        "cli_version_argv": list(raw.get("cli_version_argv", [])),
        "cli_version_pattern": raw.get("cli_version_pattern"),
        "conformance_path": raw.get("conformance_path"),
        "conformance_sha256": raw.get("conformance_sha256"),
        "bootstrap_agent": raw.get("bootstrap_agent"),
    }
    if source is not None:
        source_path = repo_root / str(source)
        if not source_path.is_file():
            raise ConfigError("adapter source is missing")
        payload["source_sha256"] = artifact_hash(source_path)
    return artifact_hash(payload)


def _cell_tool_policy(plan: Mapping[str, Any], cell: Mapping[str, Any]) -> dict[str, Any]:
    value = cell.get("tool_policy", plan.get("tool_policy"))
    if not isinstance(value, Mapping):
        raise ConfigError("protected run-plan cell is missing its tool policy")
    return dict(value)


def _path_binding(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": artifact_hash(path)}


def _receipt_binding(path: Path) -> dict[str, str]:
    payload = _read_json(path, "signed execution receipt")
    return {
        "receipt_id": str(payload["receipt_id"]),
        "path": str(path),
        "sha256": artifact_hash(path),
    }


def _require_binding_hash(binding: object, path: Path, label: str) -> None:
    if not isinstance(binding, Mapping) or binding.get("sha256") != artifact_hash(path):
        raise ConfigError(f"promotion verdict has a stale {label} binding")


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [_object(json.loads(line), label) for line in lines if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot load {label}") from exc


def _exclusive_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        os.close(descriptor)


def _exclusive_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def _exclusive_jsonl(path: Path, payloads: Sequence[Mapping[str, Any]]) -> None:
    encoded = "".join(canonical_json(dict(payload)) + "\n" for payload in payloads).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, encoded)
    finally:
        os.close(descriptor)


def _contains_private_key(payload: object) -> bool:
    forbidden_names = {"prompt", "response", "raw_trace", "raw_traces", "sealed_cases", "labels"}
    if isinstance(payload, Mapping):
        return any(str(key).lower() in forbidden_names or _contains_private_key(value) for key, value in payload.items())
    if isinstance(payload, list):
        return any(_contains_private_key(value) for value in payload)
    if isinstance(payload, str):
        return payload.startswith("/") or "/protected/" in payload
    return False


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _days_from_now(days: int) -> str:
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _phase_complete(phase: str, run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "ProtectedEvaluationPublicResult.v1",
        "phase": phase,
        "status": f"{phase}_complete",
        "promotion_allowed": False,
        "run_id": run_id,
        "reason_codes": [],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a protected Core-Prompts behavioral evaluation.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--sealed-bundle", type=Path)
    parser.add_argument(
        "--phase",
        choices=("validate", "authorize-budget", "conformance", "primary", "reproduction", "finalize"),
        required=True,
    )
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        with tempfile.TemporaryDirectory(prefix="protected-evaluator-") as temporary:
            runner = ProtectedRunner(
                config,
                work_root=Path(temporary),
                public_root=args.public_output,
                private_root=args.private_output,
            )
            result = runner.execute_phase(args.phase, args.submission, args.sealed_bundle)
            _exclusive_json(args.public_output / f"result-{args.phase}.json", result)
            return 0 if result.get("promotion_allowed") is True or result.get("status", "").endswith("_complete") else 2
    except Exception:  # noqa: BLE001 - the public failure path must redact every unexpected error
        # Never print exception bodies: config paths, commands, or protected material
        # may be present. CI receives a stable non-promotion result only.
        args.public_output.mkdir(parents=True, exist_ok=True)
        result = {
            "schema_version": "ProtectedEvaluationPublicResult.v1",
            "status": "inconclusive",
            "promotion_allowed": False,
            "reason_codes": ["protected_failure"],
        }
        try:
            _exclusive_json(args.public_output / f"result-{args.phase}.json", result)
        except FileExistsError:
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
