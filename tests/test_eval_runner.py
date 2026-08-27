from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import jsonschema
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from core_prompts_eval.adapters import (
    AdapterError,
    AdapterResponse,
    AdapterSpec,
    execute_adapter,
    load_adapter_registry,
    parse_claude_json,
    resolve_adapter_cli_sha256,
)
from core_prompts_eval.artifacts import verify_artifact_chain
from core_prompts_eval.attestations import signature_message
from core_prompts_eval.contracts import artifact_hash
from core_prompts_eval.evaluator import compare
from core_prompts_eval.run_plan import RunPlanError, load_run_plan

ROOT = Path(__file__).resolve().parents[1]


def _nested_strings(value: object) -> list[str]:
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _nested_strings(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in _nested_strings(nested)]
    return [value] if isinstance(value, str) else []
HEX = "a" * 64


def _write_dataset(path: Path) -> None:
    path.write_text(
        json.dumps({"id": "case-1", "prompt": "Deliver the requested change."}) + "\n",
        encoding="utf-8",
    )


def _plan(tmp_path: Path, *, profile: str = "canary", adapter_id: str = "fake") -> Path:
    baseline = tmp_path / "baseline.md"
    candidate = tmp_path / "candidate.md"
    dataset = tmp_path / "sealed-cases.jsonl"
    baseline.write_text("baseline", encoding="utf-8")
    candidate.write_text("candidate", encoding="utf-8")
    _write_dataset(dataset)
    from core_prompts_eval.artifacts import evaluator_package_hash
    from core_prompts_eval.contracts import artifact_hash

    registry = load_adapter_registry(ROOT)
    evidence_paths = {
        name: tmp_path / f"{name}.json"
        for name in ("evaluation-policy", "impact-plan", "judge-qualification", "sealed-attestation", "scorer")
    }
    for name, path in evidence_paths.items():
        path.write_text(json.dumps({"fixture": name}) + "\n", encoding="utf-8")
    private = Ed25519PrivateKey.from_private_bytes(bytes([7]) * 32)
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    trust_root = tmp_path / "adapter-conformance-trust-root.json"
    trust_root.write_text(
        json.dumps(
            {
                "schema_version": "ProtectedTrustRoot.v1",
                "key_id": "test-adapter-conformance",
                "algorithm": "Ed25519",
                "public_key_base64": base64.b64encode(public).decode("ascii"),
                "purposes": ["adapter_conformance"],
                "not_before": "2020-01-01T00:00:00Z",
                "expires_at": "2037-01-01T00:00:00Z",
                "revoked_at": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    credential_descriptor = tmp_path / "credential-descriptor-none.json"
    credential_descriptor.write_text(
        json.dumps(
            {
                "schema_version": "CredentialDescriptor.v1",
                "kind": "none",
                "name": None,
                "format": None,
                "issuer": "fixture",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "schema_version": "EvalRunPlan.v1",
        "preregistration_status": "locked",
        "run_id": "batman-canary-001",
        "slug": "batman",
        "profile": profile,
        "baseline_revision": "base-rev",
        "candidate_revision": "candidate-rev",
        "baseline_sha256": artifact_hash(baseline),
        "candidate_sha256": artifact_hash(candidate),
        "goal_contract_sha256": artifact_hash(ROOT / "evals" / "contracts" / "batman.json"),
        "topology_sha256": artifact_hash(ROOT / "evals" / "topologies" / "batman.json"),
        "evaluation_policy_sha256": artifact_hash(evidence_paths["evaluation-policy"]),
        "evaluation_policy_path": str(evidence_paths["evaluation-policy"]),
        "impact_plan_sha256": artifact_hash(evidence_paths["impact-plan"]),
        "impact_plan_path": str(evidence_paths["impact-plan"]),
        "judge_qualification_sha256": artifact_hash(evidence_paths["judge-qualification"]),
        "judge_qualifications": [
            {"path": str(evidence_paths["judge-qualification"]), "sha256": artifact_hash(evidence_paths["judge-qualification"])}
        ],
        "sealed_bundle_attestation_sha256": artifact_hash(evidence_paths["sealed-attestation"]),
        "sealed_bundle_attestation_path": str(evidence_paths["sealed-attestation"]),
        "evaluator_package_sha256": evaluator_package_hash(ROOT),
        "dataset": {"path": str(dataset), "sha256": artifact_hash(dataset)},
        "scorer_sha256": artifact_hash(evidence_paths["scorer"]),
        "scorer_path": str(evidence_paths["scorer"]),
        "adapter": {
            "id": adapter_id,
            "version": registry[adapter_id].version,
            "sha256": artifact_hash(registry[adapter_id].binding(ROOT)),
        },
        "cli_versions": {"capability-eval": "1"},
        "cli_sha256": artifact_hash(ROOT / "src" / "core_prompts_eval" / "cli.py"),
        "trust_root_path": str(trust_root),
        "trust_root_sha256": artifact_hash(trust_root),
        "model_cells": [
            {
                "id": "anchor",
                "host": "fixture-host",
                "provider": "fixture" if adapter_id == "fake" else "anthropic",
                "resolved_model_identifier": "fixture-model-v1" if adapter_id == "fake" else "claude-sonnet-4-20250514",
                "model_version": "1",
                "effort": "low",
                "cli_version": "fixture-cli-1",
                "cli_sha256": resolve_adapter_cli_sha256(registry[adapter_id]),
                "required": profile == "promotion",
                "credential_binding": {
                    "kind": "none",
                    "descriptor_path": str(credential_descriptor),
                    "descriptor_sha256": artifact_hash(credential_descriptor),
                },
            }
        ],
        "tool_policy": {"mode": "none", "allowed": []},
        "approval_policy": {"model_calls": "explicit_cli_flag", "human_reviewed": True},
        "seed": 17,
        "runner_identity": "fixture-runner-primary",
        "order": "seeded_balanced",
        "repetitions": 2,
        "max_tokens_per_call": 64,
        "token_budget": 512,
        "timeout_seconds": 5,
        "max_output_bytes": 16384,
        "stopping_rule": {"kind": "fixed_repetitions", "repetitions": 2},
        "independent_reproduction_required": True,
        "created_at": "2026-08-27T00:00:00Z",
    }
    path = tmp_path / "run-plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _bind_signed_adapter_conformance(
    plan_path: Path,
    *,
    cell_index: int = 0,
    qualified: bool = True,
    updates: dict[str, object] | None = None,
) -> Path:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    cell = plan["model_cells"][cell_index]
    adapter = cell.get("adapter", plan.get("adapter"))
    tool_policy = cell.get("tool_policy", plan.get("tool_policy"))
    unsigned = {
        "schema_version": "AdapterConformance.v1",
        "conformance_id": "fixture-conformance-1",
        "issuer": "protected-fixture",
        "adapter_id": adapter["id"],
        "adapter_version": adapter["version"],
        "adapter_sha256": adapter["sha256"],
        "cli_version": cell["cli_version"],
        "cli_sha256": cell["cli_sha256"],
        "cell_id": cell["id"],
        "host": cell["host"],
        "resolved_model_identifier": cell["resolved_model_identifier"],
        "model_version": cell["model_version"],
        "effort": cell["effort"],
        "tool_policy_sha256": artifact_hash(tool_policy),
        "approval_policy_sha256": artifact_hash(plan["approval_policy"]),
        "credential_descriptor_sha256": cell["credential_binding"]["descriptor_sha256"],
        "authentication_verified": True,
        "response_model_resolved": True,
        "usage_complete": True,
        "retry_semantics_verified": True,
        "tool_semantics_verified": True,
        "session_isolation_verified": True,
        "authorship_boundary_verified": True,
        "fixture_receipt_sha256s": ["e" * 64],
        "probe_receipt_sha256s": ["f" * 64],
        "qualified": qualified,
        "created_at": "2026-08-27T00:00:00Z",
        "expires_at": "2036-01-01T00:00:00Z",
    }
    unsigned.update(updates or {})
    private = Ed25519PrivateKey.from_private_bytes(bytes([7]) * 32)
    signature = private.sign(signature_message(unsigned))
    certificate = {
        **unsigned,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": "test-adapter-conformance",
            "purpose": "adapter_conformance",
            "signed_at": "2026-08-27T00:00:00Z",
            "payload_sha256": artifact_hash(unsigned),
            "value_base64": base64.b64encode(signature).decode("ascii"),
        },
    }
    path = plan_path.with_name(f"adapter-conformance-{cell['id']}.json")
    path.write_text(json.dumps(certificate), encoding="utf-8")
    cell["adapter_conformance_binding"] = {"path": str(path), "sha256": artifact_hash(path)}
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    return path


def _multi_adapter_promotion_plan(tmp_path: Path) -> Path:
    plan_path = _plan(tmp_path, profile="promotion")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    registry = load_adapter_registry(ROOT)
    tool_policy = {
        "mode": "repo-write-subagents",
        "allowed": ["spawn_agent", "adversarial_review"],
    }
    cells = []
    for adapter_id, host, cli_version in (
        ("codex-jsonl-experimental", "codex", "codex-cli 0.150.1"),
        ("kiro-stream-json-experimental", "kiro", "kiro-cli 2.20.0"),
    ):
        spec = registry[adapter_id]
        descriptor = tmp_path / f"credential-descriptor-{host}.json"
        descriptor_payload = {
            "schema_version": "CredentialDescriptor.v1",
            "kind": "protected_env" if host == "codex" else "protected_service_file",
            "name": "OPENAI_API_KEY" if host == "codex" else "KIRO_SERVICE_CREDENTIAL_FILE",
            "format": "opaque-env-v1" if host == "codex" else "kiro-service-credential-v1",
            "issuer": "protected-fixture",
        }
        descriptor.write_text(json.dumps(descriptor_payload) + "\n", encoding="utf-8")
        credential_binding: dict[str, object] = {
            "kind": descriptor_payload["kind"],
            "name": descriptor_payload["name"],
            "descriptor_path": str(descriptor),
            "descriptor_sha256": artifact_hash(descriptor),
        }
        if host == "kiro":
            source = tmp_path / "kiro-service-credential.json"
            source.write_text('{"service":"fixture"}\n', encoding="utf-8")
            source.chmod(0o600)
            credential_binding.update(
                {
                    "format": "kiro-service-credential-v1",
                    "source_path": str(source),
                    "source_sha256": artifact_hash(source),
                }
            )
        cells.append(
            {
                "id": f"{host}-anchor",
                "host": host,
                "provider": host,
                "resolved_model_identifier": "gpt-5.6-sol-2026-08-01",
                "model_version": "2026-08-01",
                "effort": "high",
                "cli_version": cli_version,
                "cli_sha256": resolve_adapter_cli_sha256(spec),
                "required": True,
                "adapter": {
                    "id": adapter_id,
                    "version": spec.version,
                    "sha256": artifact_hash(spec.binding(ROOT)),
                },
                "tool_policy": tool_policy,
                "credential_binding": credential_binding,
            }
        )
    plan.pop("adapter")
    plan.pop("tool_policy")
    plan["model_cells"] = cells
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    for index in range(len(cells)):
        _bind_signed_adapter_conformance(plan_path, cell_index=index)
    return plan_path


def test_run_plan_rejects_unlocked_or_unresolved_bindings(tmp_path: Path) -> None:
    path = _plan(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["preregistration_status"] = "draft"
    payload["model_cells"][0]["resolved_model_identifier"] = "latest"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RunPlanError, match="locked"):
        load_run_plan(path)


def test_static_compare_accepts_explicit_baseline_without_run_plan(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.md"
    candidate = tmp_path / "candidate.md"
    baseline.write_text("---\nname: batman\n---\nbase\n", encoding="utf-8")
    candidate.write_text("---\nname: batman\n---\ncandidate\n", encoding="utf-8")

    result = compare(
        ROOT,
        "batman",
        candidate,
        "static",
        allow_model_calls=False,
        max_tokens=0,
        baseline=baseline,
        run_plan=None,
    )

    assert result["status"] == "structural_ready"
    assert result["before"]["words"] == 5
    assert result["model_calls"] == 0


def test_model_profile_requires_permission_and_plan_before_adapter_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = tmp_path / "candidate.md"
    candidate.write_text((ROOT / "ssot" / "batman.md").read_text(encoding="utf-8"), encoding="utf-8")
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.evaluator.run_model_comparison", lambda *args, **kwargs: calls.append(args))

    denied = compare(ROOT, "batman", candidate, "promotion", allow_model_calls=False, max_tokens=None)
    missing = compare(ROOT, "batman", candidate, "promotion", allow_model_calls=True, max_tokens=None)

    assert denied["reason"] == "model-mediated profile requires explicit --allow-model-calls"
    assert missing["reason"] == "model-mediated profile requires a validated preregistered --run-plan"
    assert calls == []


def test_all_preflight_failures_happen_before_adapter_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan_path = _plan(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    baseline = Path(plan["dataset"]["path"]).with_name("baseline.md")
    candidate = Path(plan["dataset"]["path"]).with_name("candidate.md")
    plan["candidate_sha256"] = "f" * 64
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    Path(plan["evaluation_policy_path"]).write_text("stale\n", encoding="utf-8")
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        candidate,
        "canary",
        allow_model_calls=True,
        max_tokens=512,
        baseline=baseline,
        run_plan=plan_path,
    )

    assert result["status"] == "blocked_preflight"
    assert any("candidate_sha256" in blocker for blocker in result["blockers"])
    assert any("evaluation_policy_sha256" in blocker for blocker in result["blockers"])
    assert result["model_calls"] == 0
    assert calls == []


def test_fake_adapter_is_ineligible_for_promotion_and_is_not_invoked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan_path = _plan(tmp_path, profile="promotion", adapter_id="fake")
    baseline = tmp_path / "baseline.md"
    candidate = tmp_path / "candidate.md"
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        candidate,
        "promotion",
        allow_model_calls=True,
        max_tokens=512,
        baseline=baseline,
        run_plan=plan_path,
    )

    assert result["status"] == "blocked_preflight"
    assert "conformance" in " ".join(result["blockers"])
    assert calls == []


@pytest.mark.parametrize("mode", ["stale", "unqualified", "mismatch"])
def test_promotion_conformance_binding_fails_closed_before_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    plan_path = _plan(tmp_path, profile="promotion")
    certificate = _bind_signed_adapter_conformance(
        plan_path,
        qualified=mode != "unqualified",
        updates={"effort": "xhigh"} if mode == "mismatch" else None,
    )
    if mode == "stale":
        certificate.write_text(certificate.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "promotion",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
    )

    assert result["status"] == "blocked_preflight"
    assert "conformance" in " ".join(result["blockers"])
    assert calls == []


def test_signed_matching_conformance_overrides_registry_execution_block_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path = _plan(tmp_path, profile="promotion")
    _bind_signed_adapter_conformance(plan_path)
    jsonschema.validate(
        json.loads(plan_path.read_text(encoding="utf-8")),
        json.loads((ROOT / "evals" / "schemas" / "eval-run-plan.schema.json").read_text(encoding="utf-8")),
    )
    calls: list[dict[str, object]] = []

    def fake_execute(spec: AdapterSpec, request: dict[str, object], **kwargs: object) -> AdapterResponse:
        calls.append(request)
        return AdapterResponse(
            output="fixture response",
            resolved_model_identifier=str(request["resolved_model_identifier"]),
            model_version=str(request["model_version"]),
            usage={"raw": 1, "cached": 0, "billed": 1},
            raw={"schema_version": "EvalAdapterResponse.v1", "fixture": True},
        )

    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", fake_execute)
    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "promotion",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
        reports_root=tmp_path / "reports",
    )

    assert result["status"] == "completed"
    assert result["promotion_eligible"] is False
    assert len(calls) == 4


def test_multi_cell_plan_rejects_ambiguous_global_adapter(tmp_path: Path) -> None:
    plan_path = _plan(tmp_path, profile="canary")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    second = {**plan["model_cells"][0], "id": "second", "host": "second-host"}
    plan["model_cells"].append(second)
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(RunPlanError, match="per-cell adapter"):
        load_run_plan(plan_path)


def test_codex_and_kiro_cells_dispatch_their_own_bound_adapters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "protected-fixture-secret")
    plan_path = _multi_adapter_promotion_plan(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    calls: list[tuple[str, str, dict[str, object]]] = []

    def fake_execute(spec: AdapterSpec, request: dict[str, object], **kwargs: object) -> AdapterResponse:
        cell = next(
            cell for cell in plan["model_cells"] if cell["adapter"]["id"] == spec.adapter_id
        )
        calls.append((spec.adapter_id, str(request["effort"]), dict(request["tool_policy"])))
        return AdapterResponse(
            output="fixture response",
            resolved_model_identifier=str(request["resolved_model_identifier"]),
            model_version=str(request["model_version"]),
            usage={"raw": 1, "cached": 0, "billed": 1},
            raw={
                "normalized": {
                    "cli_version": cell["cli_version"],
                    "cli_sha256": cell["cli_sha256"],
                }
            },
        )

    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", fake_execute)
    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "promotion",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
        reports_root=tmp_path / "reports",
    )

    assert result["status"] == "completed"
    assert {adapter_id for adapter_id, _effort, _policy in calls} == {
        "codex-jsonl-experimental",
        "kiro-stream-json-experimental",
    }
    assert {effort for _adapter_id, effort, _policy in calls} == {"high"}
    assert all(policy["mode"] == "repo-write-subagents" for _adapter_id, _effort, policy in calls)
    manifest = json.loads(
        (tmp_path / "reports" / plan["run_id"] / "manifest.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(
        manifest,
        json.loads((ROOT / "evals" / "schemas" / "eval-run-manifest.schema.json").read_text(encoding="utf-8")),
    )
    assert set(manifest["adapter_versions"]) == {
        "codex-jsonl-experimental",
        "kiro-stream-json-experimental",
    }


def test_missing_protected_codex_credential_blocks_all_cells_before_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    plan_path = _multi_adapter_promotion_plan(tmp_path)
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "promotion",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
    )

    assert result["status"] == "blocked_preflight"
    assert any("protected Codex credential" in blocker for blocker in result["blockers"])
    assert calls == []


def test_adapter_must_enforce_preregistered_tool_policy_before_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path = _plan(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["tool_policy"] = {"mode": "repo-write-subagents", "allowed": ["subagents"]}
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "canary",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
    )

    assert result["status"] == "blocked_preflight"
    assert any("tool-policy" in blocker for blocker in result["blockers"])
    assert calls == []


def test_stale_provider_cli_binary_hash_blocks_before_adapter_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path = _plan(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["model_cells"][0]["cli_sha256"] = "0" * 64
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "canary",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
    )

    assert result["status"] == "blocked_preflight"
    assert any("CLI binary SHA-256" in blocker for blocker in result["blockers"])
    assert calls == []


def test_provider_cli_binary_replacement_after_preflight_prevents_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path = _plan(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    expected = plan["model_cells"][0]["cli_sha256"]
    observations = iter((expected, "f" * 64))
    calls: list[object] = []
    monkeypatch.setattr(
        "core_prompts_eval.runner.resolve_adapter_cli_sha256",
        lambda spec: next(observations),
    )
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "canary",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
        reports_root=tmp_path / "reports",
    )

    assert result["status"] == "failed"
    assert "changed after preflight" in result["failure"]
    assert calls == []


def test_runner_passes_preregistered_effort_to_adapter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan_path = _plan(tmp_path)
    captured: list[dict[str, object]] = []

    def fake_execute(spec: AdapterSpec, request: dict[str, object], **kwargs: object) -> AdapterResponse:
        captured.append(request)
        return AdapterResponse(
            output="fixture response",
            resolved_model_identifier=str(request["resolved_model_identifier"]),
            model_version=str(request["model_version"]),
            usage={"raw": 1, "cached": 0, "billed": 1},
            raw={"schema_version": "EvalAdapterResponse.v1", "fixture": True},
        )

    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", fake_execute)
    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "canary",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
        reports_root=tmp_path / "reports",
    )

    assert result["status"] == "completed"
    assert captured
    assert {request["effort"] for request in captured} == {"low"}


def test_sealed_dataset_symlink_is_rejected_before_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan_path = _plan(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    target = Path(plan["dataset"]["path"])
    link = tmp_path / "sealed-link.jsonl"
    link.symlink_to(target)
    plan["dataset"]["path"] = str(link)
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    calls: list[object] = []
    monkeypatch.setattr("core_prompts_eval.runner.execute_adapter", lambda *args, **kwargs: calls.append(args))

    result = compare(
        ROOT,
        "batman",
        tmp_path / "candidate.md",
        "canary",
        allow_model_calls=True,
        max_tokens=512,
        baseline=tmp_path / "baseline.md",
        run_plan=plan_path,
    )

    assert result["status"] == "blocked_preflight"
    assert any("symlink" in blocker for blocker in result["blockers"])
    assert calls == []


def test_fake_adapter_executes_deterministic_paired_trials_and_writes_atomic_chain(tmp_path: Path) -> None:
    plan_path = _plan(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    baseline = tmp_path / "baseline.md"
    candidate = tmp_path / "candidate.md"
    reports_root = tmp_path / "reports" / "evals"

    result = compare(
        ROOT,
        "batman",
        candidate,
        "canary",
        allow_model_calls=True,
        max_tokens=512,
        baseline=baseline,
        run_plan=plan_path,
        reports_root=reports_root,
    )

    run_dir = reports_root / plan["run_id"]
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in (run_dir / "trials" / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    receipt_payloads = [
        json.loads(line)
        for line in (run_dir / "trials" / "receipt-payloads.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert result["status"] == "completed"
    assert result["promotion_eligible"] is False
    assert result["model_calls"] == 4
    assert manifest["planned_repetitions"] == manifest["completed_repetitions"] == 2
    assert [record["arm"] for record in records[:2]] in (["baseline", "candidate"], ["candidate", "baseline"])
    assert all(receipt["token_usage"]["reserved"] == 64 for receipt in receipt_payloads)
    assert all(receipt["resolved_model_identifier"] == "fixture-model-v1" for receipt in receipt_payloads)
    assert all(receipt["cli_version"] == "fixture-cli-1" for receipt in receipt_payloads)
    assert all(receipt["cli_sha256"] == plan["model_cells"][0]["cli_sha256"] for receipt in receipt_payloads)
    assert all(receipt["tool_policy_sha256"] == artifact_hash(plan["tool_policy"]) for receipt in receipt_payloads)
    assert all("case_id" not in receipt and "arm" not in receipt for receipt in receipt_payloads)
    assert [receipt["raw_trace_sha256"] for receipt in receipt_payloads] == manifest["raw_trace_hashes"]
    assert manifest["provider_cli_sha256s"] == {
        "anchor": plan["model_cells"][0]["cli_sha256"]
    }
    public_cell = manifest["model_cells"][0]
    assert public_cell["credential_binding"] == {
        "kind": "none",
        "descriptor_sha256": plan["model_cells"][0]["credential_binding"]["descriptor_sha256"],
    }
    assert "descriptor_path" not in public_cell["credential_binding"]
    assert "source_path" not in public_cell["credential_binding"]
    assert "path" not in public_cell.get("adapter_conformance_binding", {})
    assert not any(
        value.startswith("/")
        for value in _nested_strings(manifest["model_cells"])
    )
    assert (run_dir / "preregistered-plan.json").exists()
    assert (run_dir / "scores.jsonl").exists()
    assert verify_artifact_chain(run_dir)["status"] == "valid"

    run_plan_schema = json.loads((ROOT / "evals" / "schemas" / "eval-run-plan.schema.json").read_text(encoding="utf-8"))
    manifest_schema = json.loads((ROOT / "evals" / "schemas" / "eval-run-manifest.schema.json").read_text(encoding="utf-8"))
    receipt_schema = json.loads((ROOT / "evals" / "schemas" / "execution-receipt.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(plan, run_plan_schema)
    jsonschema.validate(manifest, manifest_schema)
    signed_shape = {
        **receipt_payloads[0],
        "signature": {
            "algorithm": "Ed25519",
            "key_id": "fixture-only",
            "purpose": "execution_receipt",
            "signed_at": "2026-08-27T00:00:00Z",
            "payload_sha256": "f" * 64,
            "value_base64": base64.b64encode(b"fixture-only").decode("ascii"),
        },
    }
    jsonschema.validate(signed_shape, receipt_schema)


def test_registry_uses_argv_and_disallows_fake_promotion() -> None:
    registry = load_adapter_registry(ROOT)
    fake = registry["fake"]
    claude = registry["claude-json-experimental"]

    assert isinstance(fake.argv, tuple)
    assert fake.promotion_eligible is False
    assert claude.experimental is True
    assert claude.promotion_eligible is False


def test_claude_json_fixture_parser_is_conformant_without_provider_call() -> None:
    fixture = ROOT / "evals" / "fixtures" / "adapters" / "claude-success.json"
    parsed = parse_claude_json(fixture.read_bytes(), expected_model="claude-sonnet-4-20250514")

    assert parsed.output == "fixture response"
    assert parsed.resolved_model_identifier == "claude-sonnet-4-20250514"
    assert parsed.usage == {"raw": 15, "cached": 3, "billed": 12}


def test_claude_json_parser_rejects_model_drift() -> None:
    fixture = ROOT / "evals" / "fixtures" / "adapters" / "claude-success.json"

    with pytest.raises(AdapterError, match="model identifier"):
        parse_claude_json(fixture.read_bytes(), expected_model="claude-opus-pinned")


def test_claude_json_parser_rejects_incomplete_usage() -> None:
    fixture = ROOT / "evals" / "fixtures" / "adapters" / "claude-missing-usage.json"

    with pytest.raises(AdapterError, match="usage"):
        parse_claude_json(fixture.read_bytes(), expected_model="claude-sonnet-4-20250514")


def test_adapter_subprocess_enforces_timeout_and_output_bound() -> None:
    common = {
        "adapter_id": "fixture-process",
        "version": "1",
        "parser": "eval-adapter-json-v1",
        "environment_allowlist": (),
        "promotion_eligible": False,
        "experimental": False,
        "source": None,
        "supported_tool_policy_modes": ("none",),
    }
    request = {"resolved_model_identifier": "fixture-model"}
    oversized = AdapterSpec(
        argv=(sys.executable, "-c", "import sys; sys.stdin.read(); sys.stdout.write('x' * 1000)"),
        **common,
    )
    sleeping = AdapterSpec(
        argv=(sys.executable, "-c", "import sys,time; sys.stdin.read(); time.sleep(2)"),
        **common,
    )

    with pytest.raises(AdapterError, match="byte bound"):
        execute_adapter(oversized, request, repo_root=ROOT, timeout_seconds=2, max_output_bytes=32)
    with pytest.raises(AdapterError, match="timed out"):
        execute_adapter(sleeping, request, repo_root=ROOT, timeout_seconds=1, max_output_bytes=32)
