from __future__ import annotations

import base64
import json
import stat
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from core_prompts_eval.attestations import (
    signature_message as canonical_signature_message,
)
from core_prompts_eval.attestations import (
    validate_global_token_ledger,
    validate_signed_attestation,
)

ROOT = Path(__file__).resolve().parents[1]
TOOLING = ROOT / "tooling" / "protected-evaluator"
sys.path.insert(0, str(TOOLING))

from protected_runner import (
    ConfigError,
    ProtectedRunner,
    _contains_private_key,
    artifact_hash,
    load_config,
    validate_adapter_probe_evidence,
    validate_phase_signing,
    verify_reproduction_independence,
)


def test_phase_minimal_signing_rejects_keys_in_model_jobs_and_requires_exact_purpose(
    tmp_path: Path,
) -> None:
    key = tmp_path / "signing.key"
    key.write_text("fixture\n", encoding="utf-8")
    validate_phase_signing("model-primary-codex", None, None)
    with pytest.raises(ConfigError, match="rejects every signing-key"):
        validate_phase_signing("model-primary-codex", "execution_receipt", key)
    validate_phase_signing("sign-verdict", "promotion_verdict", key)
    with pytest.raises(ConfigError, match="exactly one promotion_verdict"):
        validate_phase_signing("sign-verdict", "execution_receipt", key)
    with pytest.raises(ConfigError, match="exactly one promotion_verdict"):
        validate_phase_signing("sign-verdict", None, None)


def test_every_ci_phase_loads_with_only_its_exact_protected_variables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _config(tmp_path)
    trust_store = str(payload["evaluator_trust_store"]["path"])
    payload["evaluator_trust_store"] = {
        **payload["evaluator_trust_store"],
        "path": "env:EVALUATOR_TRUST_STORE_FILE",
    }
    payload["adapter_conformance_runner_identity"] = "env:CONFORMANCE_RUNNER_IDENTITY"
    payload["budget_authorizer_runner_identity"] = "env:BUDGET_AUTHORIZER_RUNNER_IDENTITY"
    config_path = _write_json(tmp_path / "phase-config.json", payload)
    for variable in (
        "EVALUATOR_TRUST_STORE_FILE",
        "CONFORMANCE_RUNNER_IDENTITY",
        "BUDGET_AUTHORIZER_RUNNER_IDENTITY",
    ):
        monkeypatch.delenv(variable, raising=False)
    for phase in sorted(set(payload["phase_commands"])):
        for variable in (
            "EVALUATOR_TRUST_STORE_FILE",
            "CONFORMANCE_RUNNER_IDENTITY",
            "BUDGET_AUTHORIZER_RUNNER_IDENTITY",
        ):
            monkeypatch.delenv(variable, raising=False)
        if phase.startswith("adapter-probe-"):
            monkeypatch.setenv("CONFORMANCE_RUNNER_IDENTITY", "conformance-runner-c")
        if phase in {
            "authorize-budget",
            "reconcile-conformance-ledger",
            "reconcile-primary-ledger",
            "reconcile-reproduction-ledger",
            "finalize-ledger",
        }:
            monkeypatch.setenv("BUDGET_AUTHORIZER_RUNNER_IDENTITY", "budget-runner-d")
        if phase in {
            "authorize-budget",
            "sign-adapter-conformance",
            "reconcile-conformance-ledger",
            "reconcile-primary-ledger",
            "reconcile-reproduction-ledger",
            "sign-execution-receipts",
            "sign-judge-qualification",
            "sign-sealed-attestation",
            "finalize-ledger",
            "sign-verdict",
        }:
            monkeypatch.setenv("EVALUATOR_TRUST_STORE_FILE", trust_store)
        loaded = load_config(config_path, phase=phase)
        assert loaded["phase_commands"][phase]


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _key(tmp_path: Path, purpose: str, index: int) -> tuple[Path, Path]:
    private = Ed25519PrivateKey.from_private_bytes(bytes([index]) * 32)
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    key = tmp_path / "keys" / f"{purpose}.key"
    root = tmp_path / "keys" / f"{purpose}.json"
    key.parent.mkdir(parents=True, exist_ok=True)
    key.write_text(base64.b64encode(bytes([index]) * 32).decode("ascii") + "\n", encoding="ascii")
    key.chmod(0o600)
    _write_json(
        root,
        {
            "schema_version": "ProtectedTrustRoot.v1",
            "key_id": f"test-{purpose}",
            "algorithm": "Ed25519",
            "public_key_base64": base64.b64encode(public).decode("ascii"),
            "purposes": [purpose],
            "not_before": "2026-08-01T00:00:00Z",
            "expires_at": "2027-08-01T00:00:00Z",
            "revoked_at": None,
        },
    )
    return key, root


def _config(tmp_path: Path) -> dict[str, object]:
    purposes = (
        "adapter_conformance",
        "execution_receipt",
        "global_token_ledger",
        "judge_qualification",
        "sealed_bundle",
        "promotion_verdict",
    )
    keys = {}
    roots = {}
    for index, purpose in enumerate(purposes, start=1):
        key, root = _key(tmp_path, purpose, index)
        root_payload = json.loads(root.read_text(encoding="utf-8"))
        keys[purpose] = {"private_key": str(key), "key_id": root_payload["key_id"]}
        roots[purpose] = root_payload
    trust_store = _write_json(
        tmp_path / "keys" / "evaluator-trust-store.json",
        {
            "schema_version": "ProtectedTrustStore.v1",
            "keys": [
                roots[purpose] for purpose in purposes
            ],
        },
    )
    return {
        "schema_version": "ProtectedEvaluatorConfig.v1",
        "evaluator": {"repository": str(tmp_path / "evaluator.git"), "revision": "a" * 40},
        "artifacts": {
            "repository": str(tmp_path / "artifacts.git"),
            "baseline_revision": "b" * 40,
            "candidate_revision": "c" * 40,
            "skill_path": "ssot/batman.md",
        },
        "submission_trust_root": str(tmp_path / "submission-root.json"),
        "evaluator_trust_store": {
            "path": str(trust_store),
            "sha256": artifact_hash(trust_store),
        },
        "candidate_submission_schema": "evals/schemas/candidate-submission.schema.json",
        "primary": {
            "run_plan": str(tmp_path / "protected" / "primary-plan.json"),
            "runner_identity": "protected-primary-a",
        },
        "reproduction": {
            "run_plan": str(tmp_path / "protected" / "reproduction-plan.json"),
            "runner_identity": "protected-reproduction-b",
        },
        "sealed_bundle": str(tmp_path / "protected" / "sealed.jsonl"),
        "sealed_attestation": str(tmp_path / "protected" / "sealed-attestation.json"),
        "capability_eval_command": [sys.executable, str(tmp_path / "fake-eval.py")],
        "score_command": [sys.executable, str(tmp_path / "fake-score.py")],
        "judge_commands": [
            {"judge_id": "judge-a", "command": [sys.executable, str(tmp_path / "fake-judge.py")]}
        ],
        "verdict_command": [sys.executable, str(tmp_path / "fake-verdict.py")],
        "adapter_conformance_command": [sys.executable, str(tmp_path / "fake-conformance.py")],
        "adapter_conformance_runner_identity": "conformance-runner-c",
        "budget_authorizer_runner_identity": "budget-runner-d",
        "phase_commands": {
            phase: [sys.executable, str(tmp_path / f"fake-{phase}.py")]
            for phase in (
                "validate",
                "adapter-probe-codex",
                "adapter-probe-kiro",
                "prepare-prompts",
                "prepare-gold",
                "model-primary-codex",
                "model-primary-kiro",
                "model-reproduction-codex",
                "model-reproduction-kiro",
                "score-judge",
                "authorize-budget",
                "sign-adapter-conformance",
                "reconcile-conformance-ledger",
                "reconcile-primary-ledger",
                "reconcile-reproduction-ledger",
                "sign-execution-receipts",
                "sign-judge-qualification",
                "sign-sealed-attestation",
                "finalize-ledger",
                "sign-verdict",
            )
        },
        "adapter_credentials": {
            "codex": {
                "kind": "environment",
                "variable": "OPENAI_API_KEY",
            },
            "kiro": {
                "kind": "file",
                "variable": "KIRO_SERVICE_CREDENTIAL_FILE",
                "documentation_reference": "protected://kiro-service-credential",
            },
        },
        "registered_trial_tool_policy": {
            "mode": "repo-write-subagents",
            "allowed": ["subagents"],
        },
        "signing_key_ids": {
            purpose: str(keys[purpose]["key_id"]) for purpose in purposes
        },
        "limits": {"timeout_seconds": 60, "max_public_bytes": 1_000_000, "raw_token_cap": 5_000_000},
        "global_token_budget": {
            "cap": 5_000_000,
            "allocations": {
                "adapter_conformance": 100_000,
                "primary": 2_000_000,
                "reproduction": 2_000_000,
                "judge_adjudication": 900_000,
            },
            "conformance_max_tokens_per_probe": 50_000,
            "judge_max_tokens_per_call": 100_000,
        },
    }


def test_config_is_closed_and_requires_argv_commands_and_separate_keys(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    config_path = _write_json(tmp_path / "config.json", payload)
    config = load_config(config_path)
    assert config["capability_eval_command"][0] == sys.executable
    assert config["evaluator_trust_store"]["sha256"] == artifact_hash(
        Path(config["evaluator_trust_store"]["path"])
    )

    _write_json(config_path, {**payload, "candidate_command": ["malicious"]})
    with pytest.raises(ConfigError, match="unsupported fields"):
        load_config(config_path)

    bad = dict(payload)
    bad["capability_eval_command"] = "python fake-eval.py"
    _write_json(config_path, bad)
    with pytest.raises(ConfigError, match="argv array"):
        load_config(config_path)

    shared = dict(payload)
    signing_key_ids = dict(shared["signing_key_ids"])
    signing_key_ids["promotion_verdict"] = signing_key_ids["execution_receipt"]
    shared["signing_key_ids"] = signing_key_ids
    _write_json(config_path, shared)
    with pytest.raises(ConfigError, match="purpose-separated"):
        load_config(config_path)

    stale_store = dict(payload)
    stale_store["evaluator_trust_store"] = {
        **payload["evaluator_trust_store"],
        "sha256": "0" * 64,
    }
    _write_json(config_path, stale_store)
    with pytest.raises(ConfigError, match="trust store"):
        load_config(config_path)


def test_protected_signatures_use_canonical_domain_separated_message(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(
        payload,
        work_root=tmp_path / "work",
        public_root=tmp_path / "public",
        private_root=tmp_path / "private",
        signing_purpose="adapter_conformance",
        signing_key=tmp_path / "keys" / "adapter_conformance.key",
    )
    runner.evaluator_root = ROOT
    unsigned = {
        "schema_version": "AdapterConformance.v1",
        "expires_at": "2027-01-01T00:00:00Z",
        "value": "domain-separated",
    }
    signed = runner.sign_inline(unsigned, "adapter_conformance")
    trust_store = json.loads(
        Path(payload["evaluator_trust_store"]["path"]).read_text(encoding="utf-8")
    )
    assert runner.signature_message(unsigned) == canonical_signature_message(unsigned)
    assert validate_signed_attestation(
        signed,
        trust_root=trust_store,
        expected_purpose="adapter_conformance",
    ) == unsigned


def test_evaluator_trust_store_is_copied_exactly_to_public_output(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(
        payload,
        work_root=tmp_path / "work",
        public_root=tmp_path / "public",
        private_root=tmp_path / "private",
        signing_purpose="global_token_ledger",
        signing_key=tmp_path / "keys" / "global_token_ledger.key",
    )
    materialized = runner._materialize_evaluator_trust_store()
    public = tmp_path / "public" / "evaluator-trust-store.json"
    assert artifact_hash(materialized) == payload["evaluator_trust_store"]["sha256"]
    assert artifact_hash(public) == payload["evaluator_trust_store"]["sha256"]
    assert json.loads(public.read_text(encoding="utf-8"))["schema_version"] == "ProtectedTrustStore.v1"


def test_signed_global_ledger_reserves_once_and_finalizes_exact_cumulative_usage(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(
        payload,
        work_root=tmp_path / "work",
        public_root=tmp_path / "public",
        private_root=tmp_path / "private",
        signing_purpose="global_token_ledger",
        signing_key=tmp_path / "keys" / "global_token_ledger.key",
    )
    runner.evaluator_root = ROOT
    runner._materialize_evaluator_trust_store()
    reservations = [
        {"entry_id": "conformance", "phase": "adapter_conformance", "run_id": "adapter-probes", "receipt_sha256s": ["1" * 64], "reserved": 100_000},
        {"entry_id": "primary", "phase": "primary", "run_id": "primary-run", "receipt_sha256s": ["2" * 64], "reserved": 2_000_000},
        {"entry_id": "reproduction", "phase": "reproduction", "run_id": "reproduction-run", "receipt_sha256s": ["3" * 64], "reserved": 2_000_000},
        {"entry_id": "judge", "phase": "adjudication", "run_id": "judge-run", "receipt_sha256s": ["4" * 64], "reserved": 900_000},
    ]
    reserved = runner.create_reserved_global_token_ledger("batman-promotion", reservations)
    trust_store = json.loads(Path(payload["evaluator_trust_store"]["path"]).read_text(encoding="utf-8"))
    assert validate_global_token_ledger(reserved, trust_root=trust_store)["totals"]["reserved"] == 5_000_000
    final = runner.finalize_global_token_ledger(
        {
            "conformance": {"raw": 80_000, "cached": 1_000, "billed": 79_000, "receipt_sha256s": ["a" * 64]},
            "primary": {"raw": 1_500_000, "cached": 100_000, "billed": 1_400_000, "receipt_sha256s": ["b" * 64]},
            "reproduction": {"raw": 1_400_000, "cached": 90_000, "billed": 1_310_000, "receipt_sha256s": ["c" * 64]},
            "judge": {"raw": 400_000, "cached": 0, "billed": 400_000, "receipt_sha256s": ["d" * 64]},
        }
    )
    verified = validate_global_token_ledger(final, trust_root=trust_store)
    assert verified["status"] == "final"
    assert verified["totals"] == {
        "reserved": 5_000_000,
        "raw": 3_380_000,
        "cached": 191_000,
        "billed": 3_189_000,
    }
    assert verified["remaining_raw_tokens"] == 1_620_000
    assert verified["previous_ledger_sha256"] == artifact_hash(
        tmp_path / "private" / "token-ledger" / "000000.json"
    )


def test_tools_off_and_registered_trial_authority_are_separate(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    script = tmp_path / "authority.py"
    script.write_text(
        "import json, os\n"
        "print(json.dumps({k: os.environ.get(k) for k in "
        "['CORE_PROMPTS_EVAL_TOOLS','CORE_PROMPTS_EVAL_TOOL_ALLOWLIST','CORE_PROMPTS_EVAL_REMOTE_ACCESS']}))\n",
        encoding="utf-8",
    )
    tools_off = runner.run_json_command([sys.executable, str(script)], stage="tools_off")
    assert tools_off == {
        "CORE_PROMPTS_EVAL_TOOLS": "off",
        "CORE_PROMPTS_EVAL_TOOL_ALLOWLIST": None,
        "CORE_PROMPTS_EVAL_REMOTE_ACCESS": "deny",
    }
    bounded = runner.run_json_command(
        [sys.executable, str(script)],
        stage="bounded_trial",
        authority="repo-write-subagents",
        tool_policy=payload["registered_trial_tool_policy"],
    )
    assert bounded == {
        "CORE_PROMPTS_EVAL_TOOLS": "repo-write-subagents",
        "CORE_PROMPTS_EVAL_TOOL_ALLOWLIST": "subagents",
        "CORE_PROMPTS_EVAL_REMOTE_ACCESS": "deny",
    }
    with pytest.raises(ConfigError, match="unregistered tool policy"):
        runner.run_json_command(
            [sys.executable, str(script)],
            stage="unregistered",
            authority="repo-write-subagents",
            tool_policy={"mode": "repo-write-subagents", "allowed": ["shell"]},
        )


def test_adapter_credentials_are_explicit_and_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("KIRO_SERVICE_CREDENTIAL_FILE", raising=False)
    with pytest.raises(ConfigError, match="Codex protected credential"):
        runner.adapter_credential_environment("codex")
    with pytest.raises(ConfigError, match="Kiro protected service credential"):
        runner.adapter_credential_environment("kiro")

    monkeypatch.setenv("OPENAI_API_KEY", "test-protected-token")
    kiro_credential = tmp_path / "kiro-service-credential.json"
    kiro_credential.write_text('{"service":"test"}\n', encoding="utf-8")
    kiro_credential.chmod(0o600)
    monkeypatch.setenv("KIRO_SERVICE_CREDENTIAL_FILE", str(kiro_credential))
    with pytest.raises(ConfigError, match="broker and OS isolation"):
        runner.adapter_credential_environment("codex")
    assert runner.adapter_credential_environment("kiro") == {
        "KIRO_SERVICE_CREDENTIAL_FILE": str(kiro_credential.resolve())
    }


def test_protected_plan_rejects_tools_off_or_unregistered_cell_policy(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    submission = {
        "slug": "batman",
        "baseline_sha256": "a" * 64,
        "candidate_sha256": "b" * 64,
        "goal_contract_sha256": "c" * 64,
        "topology_sha256": "d" * 64,
        "evaluation_policy_sha256": "e" * 64,
    }
    plan = {
        "profile": "promotion",
        "independent_reproduction_required": True,
        "slug": "batman",
        "baseline_revision": payload["artifacts"]["baseline_revision"],
        "candidate_revision": payload["artifacts"]["candidate_revision"],
        "baseline_sha256": "a" * 64,
        "candidate_sha256": "b" * 64,
        "goal_contract_sha256": "c" * 64,
        "topology_sha256": "d" * 64,
        "evaluation_policy_sha256": "e" * 64,
        "model_cells": [{"id": "codex-anchor"}],
        "tool_policy": payload["registered_trial_tool_policy"],
        "token_budget": 100,
    }
    runner._validate_plan_bindings(plan, submission)
    with pytest.raises(ConfigError, match="unregistered tool policy"):
        runner._validate_plan_bindings(
            {**plan, "tool_policy": {"mode": "none", "allowed": []}},
            submission,
        )


def _probe_evidence(adapter_id: str = "codex-jsonl-experimental") -> dict[str, object]:
    return {
        "schema_version": "AdapterProbeEvidence.v1",
        "adapter_id": adapter_id,
        "adapter_version": "0.1.0",
        "adapter_sha256": "a" * 64,
        "cli_version": "codex-cli 0.150.1" if adapter_id.startswith("codex") else "kiro-cli 2.20.0",
        "cli_sha256": "b" * 64,
        "cell_id": "codex-anchor" if adapter_id.startswith("codex") else "kiro-anchor",
        "host": "codex" if adapter_id.startswith("codex") else "kiro",
        "resolved_model_identifier": "gpt-5.6-sol-2026-08-01",
        "model_version": "2026-08-01",
        "effort": "high",
        "tool_policy_sha256": "c" * 64,
        "approval_policy_sha256": "d" * 64,
        "credential_descriptor_sha256": "9" * 64,
        "authentication_verified": True,
        "response_model_resolved": True,
        "usage": {"raw": 100, "cached": 0, "billed": 100, "complete": True},
        "attempts": 1,
        "retry_semantics_verified": True,
        "session_id": "opaque-session-1",
        "session_isolation_verified": True,
        "tool_semantics_verified": True,
        "tool_events": [
            {"kind": "subagent_dispatch", "actor_id": "controller"},
            {"kind": "implementation_write", "actor_id": "implementer"},
            {"kind": "test_execution", "actor_id": "implementer"},
            {"kind": "milestone_review", "actor_id": "reviewer"},
        ],
        "authorship_boundary_verified": True,
        "controller_id": "controller",
        "implementation_author_ids": ["implementer"],
        "reviewer_ids": ["reviewer"],
        "fixture_receipt_sha256s": ["e" * 64],
        "probe_receipt_sha256s": ["f" * 64],
        "raw_trace_sha256": "1" * 64,
        "raw_trace_complete": True,
    }


def test_adapter_probe_evidence_requires_exact_model_usage_retry_session_tools_and_authorship() -> None:
    evidence = _probe_evidence()
    expected = {
        key: evidence[key]
        for key in (
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
        )
    }
    validate_adapter_probe_evidence(evidence, expected)

    failures = (
        ({"resolved_model_identifier": "latest"}, "model"),
        ({"usage": {"raw": 100, "cached": 0, "billed": 100, "complete": False}}, "usage"),
        ({"attempts": 2}, "retry"),
        ({"session_isolation_verified": False}, "session"),
        ({"tool_events": evidence["tool_events"][:-1]}, "tool"),
        ({"implementation_author_ids": ["controller"]}, "authorship"),
        ({"raw_trace_complete": False}, "trace"),
    )
    for update, message in failures:
        with pytest.raises(ConfigError, match=message):
            validate_adapter_probe_evidence({**evidence, **update}, expected)


def test_primary_phase_requires_two_signed_adapter_conformance_certificates(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    plan = {
        "model_cells": [
            {"id": "codex-anchor", "host": "codex"},
            {"id": "kiro-anchor", "host": "kiro"},
        ]
    }
    with pytest.raises(ConfigError, match="adapter conformance"):
        runner.require_adapter_conformance(plan)


def test_qualified_signed_codex_and_kiro_certificates_unblock_cells(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(
        payload,
        work_root=tmp_path / "work",
        public_root=tmp_path / "public",
        private_root=tmp_path / "private",
        signing_purpose="adapter_conformance",
        signing_key=tmp_path / "keys" / "adapter_conformance.key",
    )
    runner.evaluator_root = ROOT
    cells = []
    for adapter_id in ("codex-jsonl-experimental", "kiro-stream-json-experimental"):
        evidence = _probe_evidence(adapter_id)
        unsigned = {
            "schema_version": "AdapterConformance.v1",
            "conformance_id": f"cert-{evidence['cell_id']}",
            "issuer": "protected-test",
            **{
                field: evidence[field]
                for field in (
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
                    "retry_semantics_verified",
                    "tool_semantics_verified",
                    "session_isolation_verified",
                    "authorship_boundary_verified",
                    "fixture_receipt_sha256s",
                    "probe_receipt_sha256s",
                )
            },
            "usage_complete": True,
            "qualified": True,
            "created_at": "2026-08-27T00:00:00Z",
            "expires_at": "2027-01-01T00:00:00Z",
        }
        signed = runner.sign_inline(unsigned, "adapter_conformance")
        certificate = _write_json(tmp_path / "certificates" / f"{evidence['cell_id']}.json", signed)
        cells.append(
            {
                "id": evidence["cell_id"],
                "host": evidence["host"],
                "resolved_model_identifier": evidence["resolved_model_identifier"],
                "model_version": evidence["model_version"],
                "effort": evidence["effort"],
                "adapter_conformance_binding": {
                    "path": str(certificate),
                    "sha256": artifact_hash(certificate),
                },
            }
        )
    trust_root = Path(payload["evaluator_trust_store"]["path"])
    runner.require_adapter_conformance(
        {
            "trust_root_path": str(trust_root),
            "trust_root_sha256": artifact_hash(trust_root),
            "model_cells": cells,
        }
    )


def test_reproduction_requires_distinct_run_seed_and_runner_identity() -> None:
    primary = {"run_id": "primary", "seed": 11}
    reproduction = {"run_id": "repro", "seed": 12}
    verify_reproduction_independence(primary, reproduction, "runner-a", "runner-b")

    for update, message in (
        ({"run_id": "primary"}, "run_id"),
        ({"seed": 11}, "seed"),
    ):
        with pytest.raises(ConfigError, match=message):
            verify_reproduction_independence(primary, {**reproduction, **update}, "runner-a", "runner-b")
    with pytest.raises(ConfigError, match="runner identity"):
        verify_reproduction_independence(primary, reproduction, "runner-a", "runner-a")


def test_command_execution_never_uses_a_shell_and_hides_secret_environment(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    marker = tmp_path / "pwned"
    script = tmp_path / "argv.py"
    script.write_text(
        "import json, os, sys\n"
        "print(json.dumps({'argv': sys.argv[1:], 'secret_visible': 'SECRET_TOKEN' in os.environ}))\n",
        encoding="utf-8",
    )
    result = runner.run_json_command([sys.executable, str(script), f";touch {marker}"], stage="test")
    assert result == {"argv": [f";touch {marker}"], "secret_visible": False}
    assert not marker.exists()


def test_redacted_public_failure_contains_no_paths_commands_or_secrets(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    result = runner.non_promote("missing_reproduction", "do not expose /protected/secret or token abc")
    encoded = json.dumps(result)
    assert result["promotion_allowed"] is False
    assert result["status"] == "inconclusive"
    assert result["reason_codes"] == ["missing_reproduction"]
    assert "/protected" not in encoded
    assert "abc" not in encoded


def test_publication_accepts_hash_only_credential_evidence_and_rejects_private_paths() -> None:
    assert not _contains_private_key(
        {
            "credential_binding": {
                "kind": "protected_service_file",
                "name": "KIRO_SERVICE_CREDENTIAL_FILE",
                "format": "kiro-service-credential-v1",
                "descriptor_sha256": "a" * 64,
            },
            "adapter_conformance_binding": {"sha256": "b" * 64},
        }
    )
    assert _contains_private_key(
        {
            "credential_binding": {
                "source_path": "/protected/kiro-service-credential.json",
                "descriptor_sha256": "a" * 64,
            }
        }
    )


def test_read_only_checkout_verifies_exact_commit(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=source, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=source, check=True)
    (source / "artifact.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "add", "artifact.txt"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-m", "one"], cwd=source, check=True, capture_output=True)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source, check=True, capture_output=True, text=True
    ).stdout.strip()

    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    checkout = runner.checkout_read_only(str(source), revision, "exact")
    assert subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=checkout, check=True, capture_output=True, text=True
    ).stdout.strip() == revision
    assert not (checkout / "artifact.txt").stat().st_mode & stat.S_IWUSR

    with pytest.raises(ConfigError, match="full immutable Git commit"):
        runner.checkout_read_only(str(source), "main", "mutable")


def test_missing_receipts_stops_before_scoring(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    called = tmp_path / "score-called"
    scorer = tmp_path / "fake-score.py"
    scorer.write_text(f"from pathlib import Path\nPath({str(called)!r}).touch()\n", encoding="utf-8")
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    run_dir = tmp_path / "private" / "primary"
    run_dir.mkdir(parents=True)
    _write_json(run_dir / "manifest.json", {"run_id": "primary", "token_usage": {"raw": 0}})
    digest = artifact_hash(run_dir / "manifest.json")
    root = artifact_hash(f"{'0' * 64}\0manifest.json\0{digest}")
    _write_json(
        run_dir / "hash-chain.json",
        {
            "schema_version": "EvalArtifactChain.v1",
            "entries": [{"path": "manifest.json", "sha256": digest, "chain_sha256": root}],
            "root_sha256": root,
        },
    )
    result = runner.protect_run(run_dir, label="primary")
    assert result["promotion_allowed"] is False
    assert result["reason_codes"] == ["missing_receipts"]
    assert not called.exists()


def test_gitlab_template_orders_primary_reproduction_and_finalize() -> None:
    template = (TOOLING / "gitlab-ci.template.yml").read_text(encoding="utf-8")
    assert "evaluate-primary-codex:" in template
    assert "adapter-conformance-codex:" in template
    assert "needs: [adapter-conformance-codex, adapter-conformance-kiro]" in template
    assert "evaluate-reproduction-codex:" in template
    assert "finalize-protected-verdict:" in template
    assert "needs: [validate-submission]" in template
    assert "needs: [reconcile-primary-ledger]" in template
    assert "evaluate-reproduction-kiro" in template
    assert "access: maintainer" in template
    assert "public-output/" in template
    assert "protected-output/" in template
    assert "EVALUATOR_TRUST_STORE_FILE" in template
    assert "ADAPTER_CONFORMANCE_TRUST_ROOT_FILE" not in template
    assert "EXECUTION_RECEIPT_TRUST_ROOT_FILE" not in template
    assert "PROMOTION_VERDICT_TRUST_ROOT_FILE" not in template


def test_gitlab_pipeline_separates_model_seal_score_and_signing_trust_domains() -> None:
    template = (TOOLING / "gitlab-ci.template.yml").read_text(encoding="utf-8")
    for job in (
        "validate-submission",
        "authorize-global-budget",
        "adapter-conformance-codex",
        "adapter-conformance-kiro",
        "sign-adapter-conformance",
        "prepare-sealed-cases",
        "evaluate-primary-codex",
        "evaluate-primary-kiro",
        "reconcile-primary-ledger",
        "evaluate-reproduction-codex",
        "evaluate-reproduction-kiro",
        "reconcile-reproduction-ledger",
        "score-and-judge",
        "finalize-protected-verdict",
    ):
        assert f"{job}:" in template
    default_block = template.split("validate-submission:", 1)[0]
    for secret in ("SEALED_BUNDLE_FILE", "SIGNING_KEY_FILE", "OPENAI_API_KEY", "KIRO_SERVICE_CREDENTIAL_FILE"):
        assert secret not in default_block
    codex_conformance = template.split("adapter-conformance-codex:", 1)[1].split("adapter-conformance-kiro:", 1)[0]
    kiro_conformance = template.split("adapter-conformance-kiro:", 1)[1].split("sign-adapter-conformance:", 1)[0]
    assert "OPENAI_API_KEY" not in codex_conformance
    assert "KIRO_SERVICE_CREDENTIAL_FILE" not in codex_conformance
    assert "KIRO_SERVICE_CREDENTIAL_FILE" in kiro_conformance
    assert "OPENAI_API_KEY" not in kiro_conformance
    for conformance in (codex_conformance, kiro_conformance):
        assert "SEALED_BUNDLE_FILE" not in conformance
        assert "_KEY_FILE" not in conformance
    for job, next_job in (
        ("evaluate-primary-codex:", "evaluate-primary-kiro:"),
        ("evaluate-primary-kiro:", "reconcile-primary-ledger:"),
        ("evaluate-reproduction-codex:", "evaluate-reproduction-kiro:"),
        ("evaluate-reproduction-kiro:", "reconcile-reproduction-ledger:"),
    ):
        block = template.split(job, 1)[1].split(next_job, 1)[0]
        assert "SEALED_BUNDLE_FILE" not in block
        assert "_KEY_FILE" not in block
        assert "prompt-inputs/" in block
    score = template.split("score-and-judge:", 1)[1].split("sign-execution-receipts:", 1)[0]
    assert "gold-evidence/" in score
    assert "_KEY_FILE" not in score
    finalize = template.split("finalize-protected-verdict:", 1)[1]
    assert "PROMOTION_VERDICT_KEY_FILE" in finalize
    assert "OPENAI_API_KEY" not in finalize
    assert "KIRO_SERVICE_CREDENTIAL_FILE" not in finalize


def test_gitlab_pipeline_uses_one_runner_ssot_and_phase_minimal_signing() -> None:
    template = (TOOLING / "gitlab-ci.template.yml").read_text(encoding="utf-8")
    command_lines = [line.strip() for line in template.splitlines() if line.strip().startswith("- ./protected-")]
    assert command_lines
    assert all(line.startswith("- ./protected-runner ") for line in command_lines)
    for phase in (
        "adapter-probe-codex",
        "adapter-probe-kiro",
        "model-primary-codex",
        "model-primary-kiro",
        "model-reproduction-codex",
        "model-reproduction-kiro",
        "score-judge",
    ):
        line = next(item for item in command_lines if f"--phase {phase} " in item)
        assert "--signing-key" not in line
        assert "--signing-purpose" not in line
    expected_signers = {
        "sign-adapter-conformance": "adapter_conformance",
        "reconcile-conformance-ledger": "global_token_ledger",
        "reconcile-primary-ledger": "global_token_ledger",
        "reconcile-reproduction-ledger": "global_token_ledger",
        "sign-execution-receipts": "execution_receipt",
        "sign-judge-qualification": "judge_qualification",
        "sign-sealed-attestation": "sealed_bundle",
        "finalize-ledger": "global_token_ledger",
        "sign-verdict": "promotion_verdict",
    }
    for phase, purpose in expected_signers.items():
        line = next(item for item in command_lines if f"--phase {phase} " in item)
        assert line.count("--signing-key") == 1
        assert f"--signing-purpose {purpose}" in line


def _score_report(primary_manifest: Path, reproduction_manifest: Path) -> dict[str, object]:
    primary = json.loads(primary_manifest.read_text(encoding="utf-8"))
    reproduction = json.loads(reproduction_manifest.read_text(encoding="utf-8"))
    return {
        "schema_version": "ProtectedScoreReport.v1",
        "run_id": primary["run_id"],
        "reproduction_run_id": reproduction["run_id"],
        "baseline_sha256": primary["baseline_sha256"],
        "candidate_sha256": primary["candidate_sha256"],
        "dataset_sha256": primary["dataset_sha256"],
        "scorer_sha256": primary["scorer_sha256"],
        "primary_manifest_sha256": artifact_hash(primary_manifest),
        "reproduction_manifest_sha256": artifact_hash(reproduction_manifest),
        "scoring_status": "completed",
        "trial_completeness": {"planned": 10, "completed": 10, "missing": 0},
        "repetition_completeness": {"planned": 3, "completed": 3},
        "token_totals": {"raw": 200, "cached": 0, "billed": 200, "cap": 5_000_000},
        "metrics": [
            {"id": "paired-success", "baseline": 0.7, "candidate": 0.9, "delta": 0.2, "threshold": 0.08, "passed": True}
        ],
        "receipt_results": [
            {"receipt_id": "receipt-primary", "run_id": primary["run_id"], "result": "PASS", "derived_evidence_grade": "A"},
            {"receipt_id": "receipt-reproduction", "run_id": reproduction["run_id"], "result": "PASS", "derived_evidence_grade": "A"},
        ],
        "mutation_summary": {"critical_total": 2, "critical_killed": 2, "overall_total": 20, "overall_killed": 19},
        "critical_invariant_violations": 0,
        "protected_regression_count": 0,
        "hard_gates": {
            "critical_invariant_zero": True,
            "primary_outcome_pass": True,
            "secondary_outcomes_pass": True,
            "mutation_thresholds_pass": True,
            "protected_noninferiority_pass": True,
            "trial_completeness_pass": True,
            "repetition_completeness_pass": True,
            "token_cap_pass": True,
        },
    }


def test_protected_score_report_is_closed_bound_and_fail_closed(tmp_path: Path) -> None:
    schema = json.loads(
        (ROOT / "evals" / "schemas" / "protected-score-report.schema.json").read_text(encoding="utf-8")
    )
    primary = _write_json(
        tmp_path / "primary" / "manifest.json",
        {
            "run_id": "primary-run",
            "baseline_sha256": "a" * 64,
            "candidate_sha256": "b" * 64,
            "dataset_sha256": "c" * 64,
            "scorer_sha256": "d" * 64,
            "token_usage": {"raw": 100, "cached": 0, "billed": 100},
        },
    )
    reproduction = _write_json(
        tmp_path / "reproduction" / "manifest.json",
        {
            "run_id": "reproduction-run",
            "baseline_sha256": "a" * 64,
            "candidate_sha256": "b" * 64,
            "dataset_sha256": "c" * 64,
            "scorer_sha256": "d" * 64,
            "token_usage": {"raw": 100, "cached": 0, "billed": 100},
        },
    )
    for run_dir, receipt_id, run_id in (
        (primary.parent, "receipt-primary", "primary-run"),
        (reproduction.parent, "receipt-reproduction", "reproduction-run"),
    ):
        receipt_path = run_dir / "trials" / "receipt-payloads.jsonl"
        receipt_path.parent.mkdir(parents=True)
        receipt_path.write_text(
            json.dumps({"receipt_id": receipt_id, "run_id": run_id}) + "\n",
            encoding="utf-8",
        )
    score = _score_report(primary, reproduction)
    jsonschema.validate(score, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**score, "raw_labels": ["secret"]}, schema)

    payload = _config(tmp_path)
    runner = ProtectedRunner(payload, work_root=tmp_path / "work", public_root=tmp_path / "public", private_root=tmp_path / "private")
    runner._validate_score_report(score, primary.parent, reproduction.parent)
    failed = dict(score)
    failed["hard_gates"] = {**score["hard_gates"], "primary_outcome_pass": False}
    with pytest.raises(ConfigError, match="failed hard gate"):
        runner._validate_score_report(failed, primary.parent, reproduction.parent)


def test_scored_receipt_gets_canonical_embedded_signature(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    runner = ProtectedRunner(
        payload,
        work_root=tmp_path / "work",
        public_root=tmp_path / "public",
        private_root=tmp_path / "private",
        signing_purpose="execution_receipt",
        signing_key=tmp_path / "keys" / "execution_receipt.key",
    )
    runner.evaluator_root = ROOT
    run_dir = tmp_path / "run"
    manifest = _write_json(
        run_dir / "manifest.json",
        {"run_id": "run-primary", "token_usage": {"raw": 100}},
    )
    receipt = {
        "schema_version": "ExecutionReceipt.v1",
        "receipt_id": "receipt-primary",
        "issuer": "protected-evaluator",
        "run_id": "run-primary",
        "runner_identity": "protected-primary-a",
        "randomization_seed": 11,
        "cell_id": "critical-codex",
        "trial_id": "trial-opaque-1",
        "repetition": 1,
        "planned_repetitions": 1,
        "order_index": 0,
        "host": "codex",
        "adapter_id": "fake-adapter",
        "adapter_version": "1.0.0",
        "adapter_sha256": "a" * 64,
        "resolved_model_identifier": "fake-model-2026-08-01",
        "model_version": "2026-08-01",
        "effort": "high",
        "cli_version": "1.0.0",
        "cli_sha256": "b" * 64,
        "tool_policy_sha256": "c" * 64,
        "approval_policy_sha256": "d" * 64,
        "credential_descriptor_sha256": "9" * 64,
        "candidate_sha256": "e" * 64,
        "dataset_sha256": "f" * 64,
        "input_sha256": "1" * 64,
        "output_sha256": "2" * 64,
        "raw_trace_sha256": "3" * 64,
        "trace_commitment_sha256": "4" * 64,
        "trace_complete": True,
        "result": "INCONCLUSIVE",
        "token_usage": {"raw": 100, "cached": 0, "billed": 100, "reserved": 100},
        "attempts": 1,
        "latency_ms": 1,
        "started_at": "2026-08-27T10:00:00Z",
        "completed_at": "2026-08-27T10:01:00Z",
        "expires_at": "2027-01-01T00:00:00Z",
        "derived_evidence_grade": "C",
    }
    receipt_path = run_dir / "trials" / "receipt-payloads.jsonl"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    entries = []
    previous = "0" * 64
    for path in sorted((manifest, receipt_path)):
        relative = path.relative_to(run_dir).as_posix()
        digest = artifact_hash(path)
        previous = artifact_hash(f"{previous}\0{relative}\0{digest}")
        entries.append({"path": relative, "sha256": digest, "chain_sha256": previous})
    _write_json(
        run_dir / "hash-chain.json",
        {"schema_version": "EvalArtifactChain.v1", "entries": entries, "root_sha256": previous},
    )
    protected = runner.protect_run(
        run_dir,
        label="primary",
        receipt_results={
            "receipt-primary": {
                "receipt_id": "receipt-primary",
                "run_id": "run-primary",
                "result": "PASS",
                "derived_evidence_grade": "A",
            }
        },
    )
    signed = json.loads(Path(protected["receipt_paths"][0]).read_text(encoding="utf-8"))
    assert signed["result"] == "PASS"
    assert signed["derived_evidence_grade"] == "A"
    assert signed["signature"]["purpose"] == "execution_receipt"
    schema = json.loads((ROOT / "evals" / "schemas" / "execution-receipt.schema.json").read_text())
    jsonschema.validate(signed, schema)
