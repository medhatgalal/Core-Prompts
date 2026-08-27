from __future__ import annotations

import datetime as dt
import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .adapters import (
    AdapterError,
    AdapterSpec,
    execute_adapter,
    load_adapter_registry,
    resolve_adapter_cli_sha256,
)
from .attestations import AttestationError, validate_adapter_conformance
from .artifacts import ArtifactError, evaluator_package_hash, write_run_artifacts
from .contracts import PROFILE_TOKEN_CAPS, artifact_hash
from .run_plan import RunPlan, RunPlanError, load_run_plan


ADAPTER_CONFORMANCE_FIELDS = {
    "schema_version",
    "conformance_id",
    "issuer",
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
    "usage_complete",
    "retry_semantics_verified",
    "tool_semantics_verified",
    "session_isolation_verified",
    "authorship_boundary_verified",
    "authentication_verified",
    "fixture_receipt_sha256s",
    "probe_receipt_sha256s",
    "qualified",
    "created_at",
    "expires_at",
    "signature",
}

ADAPTER_CONFORMANCE_GATES = (
    "response_model_resolved",
    "usage_complete",
    "retry_semantics_verified",
    "tool_semantics_verified",
    "session_isolation_verified",
    "authorship_boundary_verified",
)


@dataclass
class TokenLedger:
    cap: int
    reserved: int = 0
    raw: int = 0
    cached: int = 0
    billed: int = 0

    def reserve(self, amount: int) -> None:
        if self.reserved + amount > self.cap:
            raise RunPlanError("token reservation would exceed the preregistered budget")
        self.reserved += amount

    def record(self, usage: Mapping[str, int], reservation: int) -> None:
        if int(usage["raw"]) > reservation:
            raise AdapterError("adapter usage exceeded its reserved per-call token budget")
        self.raw += int(usage["raw"])
        self.cached += int(usage["cached"])
        self.billed += int(usage["billed"])

    def payload(self) -> dict[str, int]:
        return {"reserved": self.reserved, "raw": self.raw, "cached": self.cached, "billed": self.billed}


def run_model_comparison(
    repo_root: Path,
    *,
    slug: str,
    profile: str,
    baseline: Path,
    candidate: Path,
    run_plan_path: Path,
    max_tokens: int | None,
    reports_root: Path | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        plan = load_run_plan(run_plan_path)
    except RunPlanError as exc:
        return _blocked(slug, profile, [str(exc)])
    registry: dict[str, AdapterSpec] = {}
    cases: list[dict[str, str]] = []
    artifact_texts: dict[str, str] = {}
    try:
        registry = load_adapter_registry(repo_root)
    except (OSError, json.JSONDecodeError, AdapterError) as exc:
        blockers.append(f"adapter_registry: {exc}")
    blockers.extend(_preflight(repo_root, plan, slug, profile, baseline, candidate, registry, max_tokens))
    if not blockers:
        for arm, path, expected in (
            ("baseline", baseline, plan.payload["baseline_sha256"]),
            ("candidate", candidate, plan.payload["candidate_sha256"]),
        ):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                blockers.append(f"{arm} artifact cannot be read: {exc}")
                continue
            if artifact_hash(text) != expected:
                blockers.append(f"{arm}_sha256 binding changed during preflight")
                continue
            artifact_texts[arm] = text
    if not blockers:
        try:
            cases = _load_cases(plan, repo_root)
        except RunPlanError as exc:
            blockers.append(str(exc))
    if not blockers:
        expected_calls = len(cases) * int(plan.payload["repetitions"]) * 2 * len(plan.payload["model_cells"])
        required_reservation = expected_calls * int(plan.payload["max_tokens_per_call"])
        if required_reservation > int(plan.payload["token_budget"]):
            blockers.append("token_budget cannot reserve every preregistered call before execution")
    if blockers:
        return _blocked(slug, profile, blockers)

    ledger = TokenLedger(cap=int(plan.payload["token_budget"]))
    trial_records: list[dict[str, Any]] = []
    receipt_payloads: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    completed_pairs = 0
    failure: str | None = None
    call_index = 0
    attempted_calls = 0
    observed_cli_sha256s: dict[str, str] = {}
    trace_commitment = "0" * 64
    for cell in plan.payload["model_cells"]:
        adapter_binding = _cell_adapter_binding(plan.payload, cell)
        tool_policy = _cell_tool_policy(plan.payload, cell)
        credential_binding = dict(cell["credential_binding"])
        spec = registry[str(adapter_binding["id"])]
        for case in cases:
            for repetition in range(int(plan.payload["repetitions"])):
                arms = _paired_order(plan, case["id"], repetition, str(cell["id"]))
                pair_complete = True
                for arm in arms:
                    try:
                        observed_cli_sha256 = resolve_adapter_cli_sha256(spec)
                    except AdapterError as exc:
                        failure = str(exc)
                        pair_complete = False
                        break
                    if observed_cli_sha256 != cell["cli_sha256"]:
                        failure = "adapter CLI binary SHA-256 changed after preflight"
                        pair_complete = False
                        break
                    observed_cli_sha256s[str(cell["id"])] = observed_cli_sha256
                    reservation = int(plan.payload["max_tokens_per_call"])
                    ledger.reserve(reservation)
                    opaque_trial_id = artifact_hash(
                        f"{plan.run_id}\0{cell['id']}\0{case['id']}\0{repetition}\0{arm}"
                    )
                    request = {
                        "schema_version": "EvalAdapterRequest.v1",
                        "run_id": plan.run_id,
                        "trial_id": opaque_trial_id,
                        "prompt": case["prompt"],
                        "artifact": artifact_texts[arm],
                        "artifact_sha256": str(plan.payload[f"{arm}_sha256"]),
                        "resolved_model_identifier": str(cell["resolved_model_identifier"]),
                        "model_version": str(cell["model_version"]),
                        "effort": str(cell["effort"]),
                        "tool_policy": tool_policy,
                        "max_tokens": reservation,
                    }
                    started = _now()
                    monotonic_started = time.monotonic_ns()
                    attempted_calls += 1
                    try:
                        response = execute_adapter(
                            spec,
                            request,
                            repo_root=repo_root,
                            timeout_seconds=int(plan.payload["timeout_seconds"]),
                            max_output_bytes=int(plan.payload["max_output_bytes"]),
                            credential_binding=credential_binding,
                        )
                        if response.model_version != str(cell["model_version"]):
                            raise AdapterError(
                                "adapter response model version does not match the preregistered cell"
                            )
                        if spec.cli_version_argv:
                            normalized = response.raw.get("normalized")
                            if (
                                not isinstance(normalized, Mapping)
                                or normalized.get("cli_version") != cell["cli_version"]
                                or normalized.get("cli_sha256") != observed_cli_sha256
                            ):
                                raise AdapterError(
                                    "adapter runtime CLI version or binary SHA-256 does not match the preregistered cell"
                                )
                        ledger.record(response.usage, reservation)
                    except (AdapterError, OSError) as exc:
                        failure = str(exc)
                        pair_complete = False
                        break
                    completed = _now()
                    trace = {
                        "schema_version": "EvalRawTrace.v1",
                        "request_sha256": artifact_hash(request),
                        "response": dict(response.raw),
                    }
                    traces.append(trace)
                    raw_trace_sha256 = artifact_hash(_render_json(trace))
                    trace_commitment = artifact_hash(f"{trace_commitment}\0{raw_trace_sha256}")
                    trial_records.append(
                        {
                            "schema_version": "EvalTrialRecord.v1",
                            "run_id": plan.run_id,
                            "trial_id": opaque_trial_id,
                            "arm": arm,
                            "repetition": repetition,
                            "order_index": call_index,
                            "input_sha256": artifact_hash(request),
                            "output_sha256": artifact_hash(response.output),
                        }
                    )
                    receipt_payloads.append({
                        "schema_version": "ExecutionReceipt.v1",
                        "receipt_id": artifact_hash(f"receipt\0{opaque_trial_id}"),
                        "issuer": "core-prompts-eval-runner",
                        "run_id": plan.run_id,
                        "cell_id": str(cell["id"]),
                        "trial_id": opaque_trial_id,
                        "repetition": repetition + 1,
                        "planned_repetitions": int(plan.payload["repetitions"]),
                        "order_index": call_index,
                        "host": str(cell["host"]),
                        "adapter_id": spec.adapter_id,
                        "adapter_version": spec.version,
                        "adapter_sha256": str(adapter_binding["sha256"]),
                        "resolved_model_identifier": response.resolved_model_identifier,
                        "model_version": response.model_version,
                        "effort": str(cell["effort"]),
                        "cli_version": str(cell["cli_version"]),
                        "cli_sha256": observed_cli_sha256,
                        "tool_policy_sha256": artifact_hash(tool_policy),
                        "approval_policy_sha256": artifact_hash(dict(plan.payload["approval_policy"])),
                        "credential_descriptor_sha256": str(
                            credential_binding["descriptor_sha256"]
                        ),
                        "runner_identity": str(plan.payload["runner_identity"]),
                        "randomization_seed": int(plan.payload["seed"]),
                        "candidate_sha256": str(plan.payload["candidate_sha256"]),
                        "dataset_sha256": str(dict(plan.payload["dataset"])["sha256"]),
                        "input_sha256": artifact_hash(request),
                        "output_sha256": artifact_hash(response.output),
                        "raw_trace_sha256": raw_trace_sha256,
                        "trace_commitment_sha256": trace_commitment,
                        "trace_complete": True,
                        "result": "INCONCLUSIVE",
                        "token_usage": {**dict(response.usage), "reserved": reservation},
                        "attempts": 1,
                        "latency_ms": max(0, (time.monotonic_ns() - monotonic_started) // 1_000_000),
                        "started_at": started,
                        "completed_at": completed,
                        "expires_at": _expiry(),
                        "derived_evidence_grade": "C",
                    })
                    call_index += 1
                if pair_complete:
                    completed_pairs += 1
                if failure:
                    break
            if failure:
                break
        if failure:
            break

    planned_repetitions = int(plan.payload["repetitions"])
    expected_pairs = len(cases) * planned_repetitions * len(plan.payload["model_cells"])
    completed_repetitions = planned_repetitions if completed_pairs == expected_pairs else 0
    status = "completed" if failure is None and completed_pairs == expected_pairs else "failed"
    manifest = _manifest(
        plan,
        completed_repetitions,
        ledger,
        trial_records,
        observed_cli_sha256s,
    )
    summary = {
        "schema_version": "EvalRunSummary.v1",
        "run_id": plan.run_id,
        "run_plan_sha256": plan.sha256,
        "slug": slug,
        "profile": profile,
        "status": status,
        "promotion_eligible": False,
        "promotion_blocker": "protected signing, scoring, judge verification, and independent reproduction remain external gates",
        "model_calls": attempted_calls,
        "planned_repetitions": planned_repetitions,
        "completed_repetitions": completed_repetitions,
        "token_usage": ledger.payload(),
        "failure": failure,
        "behavioral_claim": "execution_evidence_only",
    }
    output_root = reports_root or repo_root / "reports" / "evals"
    try:
        run_dir = write_run_artifacts(
            output_root,
            run_id=plan.run_id,
            preregistered_plan=plan.payload,
            manifest=manifest,
            trial_records=trial_records,
            receipt_payloads=receipt_payloads,
            traces=traces,
            summary=summary,
        )
    except ArtifactError as exc:
        return {**summary, "status": "failed", "failure": str(exc), "artifact_path": None}
    return {**summary, "artifact_path": str(run_dir)}


def _preflight(
    repo_root: Path,
    plan: RunPlan,
    slug: str,
    profile: str,
    baseline: Path,
    candidate: Path,
    registry: Mapping[str, AdapterSpec],
    max_tokens: int | None,
) -> list[str]:
    blockers: list[str] = []
    payload = plan.payload
    if payload["slug"] != slug:
        blockers.append("slug does not match the preregistered run plan")
    if payload["profile"] != profile:
        blockers.append("profile does not match the preregistered run plan")
    if max_tokens is not None and max_tokens != int(payload["token_budget"]):
        blockers.append("CLI token budget must equal the preregistered token budget")
    for label, path, expected in (
        ("baseline_sha256", baseline, payload["baseline_sha256"]),
        ("candidate_sha256", candidate, payload["candidate_sha256"]),
        ("goal_contract_sha256", repo_root / "evals" / "contracts" / f"{slug}.json", payload["goal_contract_sha256"]),
        ("topology_sha256", repo_root / "evals" / "topologies" / f"{slug}.json", payload["topology_sha256"]),
        (
            "evaluation_policy_sha256",
            _resolve_binding_path(payload["evaluation_policy_path"], repo_root),
            payload["evaluation_policy_sha256"],
        ),
        ("impact_plan_sha256", _resolve_binding_path(payload["impact_plan_path"], repo_root), payload["impact_plan_sha256"]),
        ("scorer_sha256", _resolve_binding_path(payload["scorer_path"], repo_root), payload["scorer_sha256"]),
        (
            "sealed_bundle_attestation_sha256",
            _resolve_binding_path(payload["sealed_bundle_attestation_path"], repo_root),
            payload["sealed_bundle_attestation_sha256"],
        ),
    ):
        resolved_path = path.expanduser().resolve()
        if not resolved_path.exists() or artifact_hash(resolved_path) != expected:
            blockers.append(f"{label} binding is missing or stale")
    for index, binding in enumerate(payload["judge_qualifications"]):
        path = _resolve_binding_path(binding["path"], repo_root)
        if not path.exists() or artifact_hash(path) != binding["sha256"]:
            blockers.append(f"judge_qualifications[{index}] binding is missing or stale")
    if evaluator_package_hash(repo_root) != payload["evaluator_package_sha256"]:
        blockers.append("evaluator_package_sha256 binding is stale")
    cli_path = repo_root / "src" / "core_prompts_eval" / "cli.py"
    if not cli_path.exists() or artifact_hash(cli_path) != payload["cli_sha256"]:
        blockers.append("cli_sha256 binding is stale")
    for cell in payload["model_cells"]:
        adapter_binding = _cell_adapter_binding(payload, cell)
        tool_policy = _cell_tool_policy(payload, cell)
        adapter = registry.get(str(adapter_binding["id"]))
        if adapter is None:
            blockers.append(f"cell {cell['id']} adapter is absent from the checked-in registry")
            continue
        if adapter.version != adapter_binding["version"]:
            blockers.append(f"cell {cell['id']} adapter version does not match its binding")
        try:
            adapter_binding_sha256 = artifact_hash(adapter.binding(repo_root))
        except AdapterError as exc:
            blockers.append(str(exc))
            adapter_binding_sha256 = None
        if adapter_binding_sha256 != adapter_binding["sha256"]:
            blockers.append(f"cell {cell['id']} adapter SHA-256 does not match its binding")
        try:
            observed_cli_sha256 = resolve_adapter_cli_sha256(adapter)
        except AdapterError as exc:
            blockers.append(f"cell {cell['id']} CLI binary cannot be bound: {exc}")
            observed_cli_sha256 = None
        if observed_cli_sha256 != cell["cli_sha256"]:
            blockers.append(f"cell {cell['id']} CLI binary SHA-256 does not match its binding")
        if str(tool_policy["mode"]) not in adapter.supported_tool_policy_modes:
            blockers.append(f"cell {cell['id']} adapter does not enforce its tool-policy mode")
        credential_blockers = _validate_cell_credential_binding(
            repo_root, cell, adapter
        )
        blockers.extend(credential_blockers)
        conformance_blockers = _validate_adapter_conformance_binding(
            repo_root, payload, cell, adapter, adapter_binding, tool_policy
        )
        blockers.extend(conformance_blockers)
        if profile == "promotion" and conformance_blockers:
            blockers.append(
                f"cell {cell['id']} adapter is not promotion eligible without valid conformance"
            )
    if int(payload["token_budget"]) > PROFILE_TOKEN_CAPS[profile]:
        blockers.append("preregistered token budget exceeds the profile hard cap")
    return blockers


def _load_cases(plan: RunPlan, repo_root: Path) -> list[dict[str, str]]:
    binding = dict(plan.payload["dataset"])
    configured_path = Path(str(binding["path"])).expanduser().absolute()
    if _has_symlink_component(configured_path):
        raise RunPlanError("sealed dataset must not use a symlink path")
    path = configured_path.resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        pass
    else:
        raise RunPlanError("sealed dataset must remain outside the repository")
    try:
        encoded = path.read_bytes()
    except OSError as exc:
        raise RunPlanError(f"sealed dataset cannot be read: {exc}") from exc
    if artifact_hash(encoded) != binding["sha256"]:
        raise RunPlanError("sealed dataset binding is missing or stale")
    cases: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        lines = encoded.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise RunPlanError("sealed dataset must be UTF-8 JSONL") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RunPlanError(f"sealed dataset line {line_number} is invalid JSON") from exc
        if not isinstance(raw, Mapping) or not str(raw.get("id") or "") or not str(raw.get("prompt") or ""):
            raise RunPlanError(f"sealed dataset line {line_number} must bind id and prompt")
        case_id = str(raw["id"])
        if case_id in seen:
            raise RunPlanError(f"sealed dataset contains duplicate case id: {case_id}")
        seen.add(case_id)
        cases.append({"id": case_id, "prompt": str(raw["prompt"])})
    if not cases:
        raise RunPlanError("sealed dataset contains no cases")
    return cases


def _validate_adapter_conformance_binding(
    repo_root: Path,
    payload: Mapping[str, Any],
    cell: Mapping[str, Any],
    adapter: AdapterSpec,
    adapter_binding: Mapping[str, Any],
    tool_policy: Mapping[str, Any],
) -> list[str]:
    if cell["required"] is not True:
        return []
    trust_path = _resolve_binding_path(payload["trust_root_path"], repo_root)
    if not trust_path.is_file() or artifact_hash(trust_path) != payload["trust_root_sha256"]:
        return ["adapter conformance trust-root binding is missing or stale"]
    try:
        trust_root = json.loads(trust_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"adapter conformance trust root cannot be loaded: {exc}"]
    if not isinstance(trust_root, Mapping):
        return ["adapter conformance trust root must be an object"]

    blockers: list[str] = []
    binding = cell["adapter_conformance_binding"]
    path = _resolve_binding_path(binding["path"], repo_root)
    if not path.is_file() or artifact_hash(path) != binding["sha256"]:
        return [f"adapter conformance for cell {cell['id']} is missing or stale"]
    try:
        certificate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"adapter conformance for cell {cell['id']} cannot be loaded: {exc}"]
    if not isinstance(certificate, Mapping) or set(certificate) != ADAPTER_CONFORMANCE_FIELDS:
        return [f"adapter conformance for cell {cell['id']} has an invalid closed shape"]
    try:
        verified = validate_adapter_conformance(certificate, trust_root=trust_root)
    except AttestationError as exc:
        return [f"adapter conformance for cell {cell['id']} is untrusted: {exc}"]
    expected = {
        "adapter_id": adapter.adapter_id,
        "adapter_version": adapter.version,
        "adapter_sha256": adapter_binding["sha256"],
        "cli_version": cell["cli_version"],
        "cli_sha256": cell["cli_sha256"],
        "cell_id": cell["id"],
        "host": cell["host"],
        "resolved_model_identifier": cell["resolved_model_identifier"],
        "model_version": cell["model_version"],
        "effort": cell["effort"],
        "tool_policy_sha256": artifact_hash(dict(tool_policy)),
        "approval_policy_sha256": artifact_hash(dict(payload["approval_policy"])),
        "credential_descriptor_sha256": cell["credential_binding"][
            "descriptor_sha256"
        ],
    }
    mismatched = [field for field, value in expected.items() if verified.get(field) != value]
    if mismatched:
        return [f"adapter conformance for cell {cell['id']} mismatches: {', '.join(mismatched)}"]
    if verified.get("qualified") is not True or any(
        verified.get(field) is not True for field in ADAPTER_CONFORMANCE_GATES
    ):
        return [f"adapter conformance for cell {cell['id']} is unqualified"]
    for field in ("fixture_receipt_sha256s", "probe_receipt_sha256s"):
        values = verified.get(field)
        if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or len(value) != 64 for value in values
        ):
            blockers.append(f"adapter conformance for cell {cell['id']} lacks bound {field}")
    return blockers


def _cell_adapter_binding(payload: Mapping[str, Any], cell: Mapping[str, Any]) -> dict[str, Any]:
    return dict(cell.get("adapter") or payload["adapter"])


def _cell_tool_policy(payload: Mapping[str, Any], cell: Mapping[str, Any]) -> dict[str, Any]:
    return dict(cell.get("tool_policy") or payload["tool_policy"])


def _validate_cell_credential_binding(
    repo_root: Path,
    cell: Mapping[str, Any],
    adapter: AdapterSpec,
) -> list[str]:
    binding = dict(cell["credential_binding"])
    descriptor_path = _resolve_binding_path(binding["descriptor_path"], repo_root)
    if not descriptor_path.is_file() or artifact_hash(descriptor_path) != binding["descriptor_sha256"]:
        return [f"cell {cell['id']} credential descriptor is missing or stale"]
    try:
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cell {cell['id']} credential descriptor cannot be loaded: {exc}"]
    if not isinstance(descriptor, Mapping) or set(descriptor) != {
        "schema_version",
        "kind",
        "name",
        "format",
        "issuer",
    }:
        return [f"cell {cell['id']} credential descriptor has an invalid redacted shape"]
    if descriptor.get("schema_version") != "CredentialDescriptor.v1" or descriptor.get("kind") != binding["kind"]:
        return [f"cell {cell['id']} credential descriptor identity is stale"]
    kind = binding["kind"]
    if kind == "none":
        return []
    if descriptor.get("name") != binding.get("name"):
        return [f"cell {cell['id']} credential descriptor name is stale"]
    if kind == "protected_env":
        if adapter.adapter_id != "codex-jsonl-experimental" or not os.environ.get("OPENAI_API_KEY"):
            return [f"cell {cell['id']} protected Codex credential is unavailable"]
        return []
    if (
        adapter.adapter_id != "kiro-stream-json-experimental"
        or descriptor.get("format") != binding.get("format")
    ):
        return [f"cell {cell['id']} Kiro credential format is unsupported"]
    source = Path(str(binding["source_path"])).expanduser().absolute()
    if _has_symlink_component(source):
        return [f"cell {cell['id']} Kiro credential cannot use a symlink path"]
    try:
        resolved = source.resolve(strict=True)
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        pass
    except OSError:
        return [f"cell {cell['id']} Kiro credential is missing"]
    else:
        return [f"cell {cell['id']} Kiro credential must remain outside the repository"]
    if (
        not resolved.is_file()
        or artifact_hash(resolved) != binding["source_sha256"]
        or resolved.stat().st_mode & 0o077
    ):
        return [f"cell {cell['id']} Kiro credential binding or permissions are invalid"]
    return []


def _paired_order(plan: RunPlan, case_id: str, repetition: int, cell_id: str) -> tuple[str, str]:
    order = str(plan.payload["order"])
    if order == "baseline_first":
        return ("baseline", "candidate")
    if order == "candidate_first":
        return ("candidate", "baseline")
    discriminator = artifact_hash(f"{plan.payload['seed']}\0{case_id}\0{repetition}\0{cell_id}")
    seeded = random.Random(int(discriminator[:16], 16))
    return ("baseline", "candidate") if seeded.randrange(2) == 0 else ("candidate", "baseline")


def _has_symlink_component(path: Path) -> bool:
    return any(component.is_symlink() for component in (path, *path.parents))


def _resolve_binding_path(value: object, repo_root: Path) -> Path:
    path = Path(str(value)).expanduser()
    return (path if path.is_absolute() else repo_root / path).resolve()


def _manifest(
    plan: RunPlan,
    completed_repetitions: int,
    ledger: TokenLedger,
    trial_records: list[dict[str, Any]],
    observed_cli_sha256s: Mapping[str, str],
) -> dict[str, Any]:
    payload = plan.payload
    adapter_bindings = [
        _cell_adapter_binding(payload, cell) for cell in payload["model_cells"]
    ]
    return {
        "schema_version": "EvalRunManifest.v1",
        "run_id": plan.run_id,
        "run_plan_sha256": plan.sha256,
        "repo_head": str(payload["candidate_revision"]),
        "baseline_revision": str(payload["baseline_revision"]),
        "candidate_revision": str(payload["candidate_revision"]),
        "baseline_sha256": str(payload["baseline_sha256"]),
        "candidate_sha256": str(payload["candidate_sha256"]),
        "goal_contract_sha256": str(payload["goal_contract_sha256"]),
        "topology_sha256": str(payload["topology_sha256"]),
        "dataset_sha256": str(dict(payload["dataset"])["sha256"]),
        "scorer_sha256": str(payload["scorer_sha256"]),
        "evaluation_policy_sha256": str(payload["evaluation_policy_sha256"]),
        "impact_plan_sha256": str(payload["impact_plan_sha256"]),
        "judge_qualification_sha256": str(payload["judge_qualification_sha256"]),
        "sealed_bundle_attestation_sha256": str(payload["sealed_bundle_attestation_sha256"]),
        "evaluator_package_sha256": str(payload["evaluator_package_sha256"]),
        "adapter_versions": {
            str(binding["id"]): str(binding["version"]) for binding in adapter_bindings
        },
        "adapter_sha256s": {
            str(binding["id"]): str(binding["sha256"]) for binding in adapter_bindings
        },
        "cli_versions": dict(payload["cli_versions"]),
        "cli_sha256": str(payload["cli_sha256"]),
        "trust_root_sha256": str(payload["trust_root_sha256"]),
        "provider_cli_sha256s": dict(observed_cli_sha256s),
        "credential_descriptor_sha256s": {
            str(cell["id"]): str(cell["credential_binding"]["descriptor_sha256"])
            for cell in payload["model_cells"]
        },
        "runner_identity": str(payload["runner_identity"]),
        "randomization_seed": int(payload["seed"]),
        "model_cells": list(payload["model_cells"]),
        "tool_policies": {
            str(cell["id"]): _cell_tool_policy(payload, cell)
            for cell in payload["model_cells"]
        },
        "approval_policy": dict(payload["approval_policy"]),
        "order": str(payload["order"]),
        "seed": int(payload["seed"]),
        "repetitions": int(payload["repetitions"]),
        "planned_repetitions": int(payload["repetitions"]),
        "completed_repetitions": completed_repetitions,
        "stopping_rule": dict(payload["stopping_rule"]),
        "independent_reproduction_required": bool(payload["independent_reproduction_required"]),
        "token_budget": int(payload["token_budget"]),
        "token_usage": ledger.payload(),
        "raw_trace_hashes": [],
        "scoring_status": "not_run",
        "mutation_summary": {
            "critical_total": 0,
            "critical_killed": 0,
            "overall_total": 0,
            "overall_killed": 0,
        },
        "protected_regression_count": 0,
        "paired_order_commitment_sha256": artifact_hash(
            {
                "ordered_trials": [
                    {"trial_id": record["trial_id"], "order_index": record["order_index"]}
                    for record in trial_records
                ]
            }
        ),
    }


def _blocked(slug: str, profile: str, blockers: list[str]) -> dict[str, Any]:
    return {
        "status": "blocked_preflight",
        "slug": slug,
        "profile": profile,
        "blockers": blockers,
        "model_calls": 0,
        "behavioral_claim": "none",
    }


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _expiry() -> str:
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)).isoformat()


def _render_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"


__all__ = ["TokenLedger", "run_model_comparison"]
