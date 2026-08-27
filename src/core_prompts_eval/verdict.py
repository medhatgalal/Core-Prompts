from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from .attestations import (
    AttestationError,
    validate_adapter_conformance,
    validate_execution_receipt,
    validate_global_token_ledger,
    validate_judge_qualification,
    validate_sealed_bundle_attestation,
    validate_signed_attestation,
)
from .contracts import (
    EVIDENCE_STATUSES,
    PROFILE_TOKEN_CAPS,
    PROMOTION_ALLOWED,
    PROMOTION_REQUIRED,
    REQUIRED_PROMOTION_GATES,
    artifact_hash,
    load_json,
)
from .provenance import ProvenanceError, validate_cell_provenance
from .qualification import QualificationError, validate_qualification_binding


SHA256_RE = re.compile(r"[0-9a-f]{64}")
REVISION_RE = re.compile(r"[0-9a-f]{40}")
PROMOTION_TRUST_PURPOSES = frozenset(
    {
        "adapter_conformance",
        "execution_receipt",
        "global_token_ledger",
        "judge_qualification",
        "promotion_verdict",
        "sealed_bundle",
    }
)


class VerdictError(ValueError):
    """Raised when a promotion verdict is untrusted, stale, or incompletely bound."""


def _coerce_now(value: str | dt.datetime | None) -> dt.datetime | None:
    if value is None or isinstance(value, dt.datetime):
        return value
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerdictError("now must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise VerdictError("now must include a timezone")
    return parsed


def _load_trust_root(trust_root: Mapping[str, Any] | Path) -> tuple[Mapping[str, Any], str]:
    if isinstance(trust_root, Path):
        return load_json(trust_root), artifact_hash(trust_root)
    return trust_root, artifact_hash(trust_root)


def _resolve_artifact(repo_root: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise VerdictError(f"{label} evidence path is missing")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise VerdictError(f"{label} evidence path must be repository-relative")
    lexical = repo_root / relative
    if lexical.is_symlink():
        raise VerdictError(f"{label} evidence path must not be a symlink")
    try:
        root = repo_root.resolve(strict=True)
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise VerdictError(f"{label} evidence is missing or outside the repository") from exc
    if not resolved.is_file():
        raise VerdictError(f"{label} evidence must be a regular file")
    return resolved


def _bound_path(repo_root: Path, binding: object, label: str) -> Path:
    if not isinstance(binding, Mapping) or not {"path", "sha256"} <= set(binding):
        raise VerdictError(f"{label} binding must contain path and sha256")
    expected = binding.get("sha256")
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        raise VerdictError(f"{label} binding sha256 is invalid")
    path = _resolve_artifact(repo_root, binding.get("path"), label)
    if artifact_hash(path) != expected:
        raise VerdictError(f"{label} binding hash does not match {path.name}")
    return path


def _direct_bound_path(repo_root: Path, payload: Mapping[str, Any], path_field: str, hash_field: str) -> Path:
    path = _resolve_artifact(repo_root, payload.get(path_field), path_field)
    expected = payload.get(hash_field)
    if not isinstance(expected, str) or artifact_hash(path) != expected:
        raise VerdictError(f"{hash_field} does not match {path.name}")
    return path


def _validate_verdict_body(payload: Mapping[str, Any]) -> None:
    missing = [field for field in PROMOTION_REQUIRED if field not in payload]
    if missing:
        raise VerdictError(f"PromotionVerdict.v2 missing required fields: {', '.join(missing)}")
    unknown = sorted(set(payload) - PROMOTION_ALLOWED)
    if unknown:
        raise VerdictError(f"PromotionVerdict.v2 contains unknown fields: {', '.join(unknown)}")
    if payload.get("schema_version") != "PromotionVerdict.v2":
        raise VerdictError("unsupported promotion verdict schema")
    if payload.get("status") not in EVIDENCE_STATUSES:
        raise VerdictError("invalid promotion verdict status")
    for field in (
        "baseline_sha256",
        "candidate_sha256",
        "goal_contract_sha256",
        "topology_sha256",
        "dataset_sha256",
        "scorer_sha256",
        "run_manifest_sha256",
        "evaluation_policy_sha256",
        "impact_plan_sha256",
        "evaluator_sha256",
        "trust_root_sha256",
    ):
        if not SHA256_RE.fullmatch(str(payload.get(field) or "")):
            raise VerdictError(f"{field} must be a lowercase SHA-256 digest")
    for field in ("baseline_revision", "candidate_revision"):
        if not REVISION_RE.fullmatch(str(payload.get(field) or "")):
            raise VerdictError(f"{field} must be a full Git commit ID")
    if payload.get("status") == "promote":
        gates = payload.get("hard_gates")
        if not isinstance(gates, Mapping):
            raise VerdictError("promotion hard gates must be an object")
        failed = [name for name in REQUIRED_PROMOTION_GATES if gates.get(name) is not True]
        if failed:
            raise VerdictError(f"promotion has failed hard gates: {', '.join(failed)}")
        profile = str(payload.get("profile") or "")
        if profile not in PROFILE_TOKEN_CAPS or payload.get("token_cap") != PROFILE_TOKEN_CAPS[profile]:
            raise VerdictError("promotion token cap does not match its profile")


def _parse_policy_time(value: object, field: str) -> dt.datetime:
    parsed = _coerce_now(str(value) if value is not None else None)
    if parsed is None:
        raise VerdictError(f"{field} is required")
    return parsed.astimezone(dt.timezone.utc)


def _validate_approved_trust_policy(
    verdict: Mapping[str, Any],
    *,
    trust_store: Mapping[str, Any],
    repo_root: Path,
    approved_sha256: str,
    approved_revision: str,
    now: dt.datetime | None,
) -> Mapping[str, Any]:
    binding = verdict.get("approved_trust_policy_binding")
    if not isinstance(binding, Mapping):
        raise VerdictError("approved trust policy binding is missing")
    if binding.get("sha256") != approved_sha256 or binding.get("revision") != approved_revision:
        raise VerdictError("approved trust policy does not match explicit operator approval")
    if not SHA256_RE.fullmatch(approved_sha256) or not REVISION_RE.fullmatch(approved_revision):
        raise VerdictError("approved trust policy hash or revision is invalid")
    if approved_revision == verdict.get("candidate_revision"):
        raise VerdictError("candidate revision cannot self-authorize its trust policy")
    path = _bound_path(repo_root, binding, "approved trust policy")
    relative_path = path.relative_to(repo_root.resolve()).as_posix()
    try:
        resolved_revision = subprocess.run(
            ["git", "rev-parse", "--verify", f"{approved_revision}^{{commit}}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        historical = subprocess.run(
            ["git", "show", f"{approved_revision}:{relative_path}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        ).stdout
        protected_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", approved_revision, str(verdict.get("baseline_revision") or "")],
            cwd=repo_root,
            check=False,
            capture_output=True,
        ).returncode
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise VerdictError("approved trust policy is not present at its protected revision") from exc
    if resolved_revision != approved_revision or artifact_hash(historical) != approved_sha256:
        raise VerdictError("approved trust policy protected-revision hash is stale")
    if protected_ancestor != 0:
        raise VerdictError("approved trust policy revision is not on the baseline ancestry")
    try:
        policy = json.loads(historical)
    except json.JSONDecodeError as exc:
        raise VerdictError("approved trust policy is not valid JSON") from exc
    required_fields = {
        "schema_version",
        "policy_id",
        "status",
        "trust_store_sha256",
        "authorized_keys",
        "approved_at",
        "expires_at",
    }
    if not isinstance(policy, Mapping) or set(policy) != required_fields:
        raise VerdictError("approved trust policy has an invalid closed shape")
    if policy.get("schema_version") != "ApprovedTrustPolicy.v1" or policy.get("status") != "approved":
        raise VerdictError("approved trust policy is not approved")
    if policy.get("trust_store_sha256") != verdict.get("trust_root_sha256"):
        raise VerdictError("approved trust policy does not bind the selected trust store")
    effective_now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    approved_at = _parse_policy_time(policy.get("approved_at"), "approved trust policy approved_at")
    expires_at = _parse_policy_time(policy.get("expires_at"), "approved trust policy expires_at")
    if approved_at > effective_now or expires_at <= effective_now:
        raise VerdictError("approved trust policy is not currently valid")
    authorized = policy.get("authorized_keys")
    if not isinstance(authorized, list) or len(authorized) != len(PROMOTION_TRUST_PURPOSES):
        raise VerdictError("approved trust policy must authorize every promotion evidence purpose exactly once")
    policy_keys = {
        (str(item.get("purpose") or ""), str(item.get("key_id") or ""))
        for item in authorized
        if isinstance(item, Mapping)
    }
    store_keys = {
        (str(root.get("purposes", [""])[0]), str(root.get("key_id") or ""))
        for root in trust_store.get("keys", [])
        if isinstance(root, Mapping) and isinstance(root.get("purposes"), list) and len(root["purposes"]) == 1
    }
    if {purpose for purpose, _key_id in policy_keys} != PROMOTION_TRUST_PURPOSES or policy_keys != store_keys:
        raise VerdictError("approved trust policy key-purpose bindings do not match the trust store")
    return policy


def validate_signed_verdict(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any] | Path,
    now: str | dt.datetime | None = None,
) -> dict[str, Any]:
    root, root_hash = _load_trust_root(trust_root)
    unsigned = validate_signed_attestation(
        payload,
        trust_root=root,
        expected_purpose="promotion_verdict",
        now=_coerce_now(now),
    )
    _validate_verdict_body({**unsigned, "signature": payload["signature"]})
    if unsigned.get("trust_root_sha256") != root_hash:
        raise VerdictError("promotion trust root is missing or stale")
    return unsigned


def _validate_manifest_bindings(
    manifest: Mapping[str, Any],
    verdict: Mapping[str, Any],
    *,
    run_id: str,
    label: str,
) -> None:
    expected = {
        "run_id": run_id,
        "baseline_revision": verdict["baseline_revision"],
        "candidate_revision": verdict["candidate_revision"],
        "baseline_sha256": verdict["baseline_sha256"],
        "candidate_sha256": verdict["candidate_sha256"],
        "goal_contract_sha256": verdict["goal_contract_sha256"],
        "topology_sha256": verdict["topology_sha256"],
        "dataset_sha256": verdict["dataset_sha256"],
        "scorer_sha256": verdict["scorer_sha256"],
        "evaluation_policy_sha256": verdict["evaluation_policy_sha256"],
        "impact_plan_sha256": verdict["impact_plan_sha256"],
        "evaluator_package_sha256": verdict["evaluator_sha256"],
        "trust_root_sha256": verdict["trust_root_sha256"],
    }
    mismatched = [field for field, value in expected.items() if manifest.get(field) != value]
    if mismatched:
        raise VerdictError(f"{label} manifest has stale bindings: {', '.join(mismatched)}")


def _verify_receipt_binding(
    binding: Mapping[str, Any],
    *,
    repo_root: Path,
    trust_root: Mapping[str, Any],
    verdict: Mapping[str, Any],
    run_id: str,
    now: dt.datetime | None,
    critical: bool,
) -> tuple[dict[str, Any], str]:
    path = _bound_path(repo_root, binding, "execution receipt")
    receipt = validate_execution_receipt(load_json(path), trust_root=trust_root, now=now)
    if binding.get("receipt_id") != receipt.get("receipt_id"):
        raise VerdictError("execution receipt binding identity does not match its artifact")
    for field, expected in (
        ("run_id", run_id),
        ("candidate_sha256", verdict["candidate_sha256"]),
        ("dataset_sha256", verdict["dataset_sha256"]),
    ):
        if receipt.get(field) != expected:
            raise VerdictError(f"execution receipt has stale {field} binding")
    grade = validate_cell_provenance(receipt, signature_verified=True, critical=critical)
    return receipt, grade


def _derive_primary_cells(
    verdict: Mapping[str, Any], receipts: Mapping[str, tuple[Mapping[str, Any], str]]
) -> list[dict[str, Any]]:
    derived: list[dict[str, Any]] = []
    bound_ids: set[str] = set()
    for cell in verdict.get("required_cells", []):
        if not isinstance(cell, Mapping):
            raise VerdictError("required runtime cells must be objects")
        receipt_ids = cell.get("receipt_ids")
        if not isinstance(receipt_ids, list) or not receipt_ids or len(set(receipt_ids)) != len(receipt_ids):
            raise VerdictError("required runtime cell must bind a non-empty unique receipt_ids list")
        if any(not isinstance(receipt_id, str) or receipt_id not in receipts for receipt_id in receipt_ids):
            raise VerdictError("required runtime cell has a missing execution receipt binding")
        bound_ids.update(receipt_ids)
        bound = [receipts[receipt_id] for receipt_id in receipt_ids]
        receipt_values = [item[0] for item in bound]
        grades = [item[1] for item in bound]
        if any(cell.get("host") != receipt.get("host") for receipt in receipt_values):
            raise VerdictError("required runtime cell host does not match every receipt")
        if any(str(receipt.get("result") or "") != "PASS" for receipt in receipt_values):
            raise VerdictError("required runtime cell contains a non-passing receipt")
        if str(cell.get("result") or "").upper() != "PASS":
            raise VerdictError("required runtime cell result is not PASS")
        if any(
            cell.get("resolved_model_identifier") != receipt.get("resolved_model_identifier")
            for receipt in receipt_values
        ):
            raise VerdictError("required runtime cell model does not match every receipt")
        grade_order = {"NOT_RUN": 0, "C": 1, "B": 2, "A": 3}
        grade = min(grades, key=grade_order.__getitem__)
        if cell.get("evidence_grade") != grade:
            raise VerdictError("verdict evidence grade does not match receipt-derived provenance")
        derived.append(dict(cell))
    if bound_ids != set(receipts):
        raise VerdictError("required runtime cells do not bind every signed execution receipt")
    return derived


def _sum_usage(receipts: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    totals = {"raw": 0, "cached": 0, "billed": 0}
    for receipt in receipts:
        usage = receipt.get("token_usage")
        if not isinstance(usage, Mapping):
            raise VerdictError("execution receipt token_usage is missing")
        for field in totals:
            value = usage.get(field)
            if not isinstance(value, int) or value < 0:
                raise VerdictError("execution receipt token usage must be non-negative integers")
            totals[field] += value
    return totals


def validate_adapter_conformance_bindings(
    bindings: Sequence[Mapping[str, Any]],
    *,
    trust_root: Mapping[str, Any],
    repo_root: Path,
    receipts: Sequence[Mapping[str, Any]],
    now: dt.datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Verify signed adapter certificates and bind each one to its execution receipts."""

    certificates: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        path = _bound_path(repo_root, binding, "adapter conformance")
        certificate = validate_adapter_conformance(load_json(path), trust_root=trust_root, now=now)
        if binding.get("adapter_id") != certificate.get("adapter_id"):
            raise VerdictError("adapter conformance identity does not match its binding")
        if binding.get("version") != certificate.get("adapter_version"):
            raise VerdictError("adapter conformance version does not match its binding")
        cell_id = str(certificate.get("cell_id") or "")
        if not cell_id or cell_id in certificates:
            raise VerdictError("adapter conformance certificates must bind unique cell IDs")
        certificates[cell_id] = certificate

    seen_cells: set[str] = set()
    for receipt in receipts:
        cell_id = str(receipt.get("cell_id") or "")
        certificate = certificates.get(cell_id)
        if certificate is None:
            raise VerdictError("execution receipt lacks a signed adapter conformance certificate")
        seen_cells.add(cell_id)
        expected = {
            "host": receipt.get("host"),
            "adapter_id": receipt.get("adapter_id"),
            "adapter_version": receipt.get("adapter_version"),
            "adapter_sha256": receipt.get("adapter_sha256"),
            "cli_version": receipt.get("cli_version"),
            "cli_sha256": receipt.get("cli_sha256"),
            "resolved_model_identifier": receipt.get("resolved_model_identifier"),
            "model_version": receipt.get("model_version"),
            "effort": receipt.get("effort"),
            "tool_policy_sha256": receipt.get("tool_policy_sha256"),
            "approval_policy_sha256": receipt.get("approval_policy_sha256"),
            "credential_descriptor_sha256": receipt.get("credential_descriptor_sha256"),
        }
        stale = [field for field, value in expected.items() if certificate.get(field) != value]
        if stale:
            raise VerdictError(f"adapter conformance has stale receipt bindings: {', '.join(stale)}")
    if seen_cells != set(certificates):
        raise VerdictError("one or more adapter conformance certificates have no execution receipts")
    return certificates


def _derive_contract_gates(goal: Mapping[str, Any], topology: Mapping[str, Any]) -> dict[str, bool]:
    coverage = topology.get("normative_clause_coverage")
    complete_coverage = False
    if isinstance(coverage, Mapping):
        try:
            complete_coverage = int(coverage.get("mapped", 0)) + int(coverage.get("waived", 0)) == int(
                coverage.get("total", -1)
            )
        except (TypeError, ValueError):
            complete_coverage = False
    invariants = topology.get("protected_invariants")
    critical_coverage = isinstance(invariants, list) and bool(invariants) and all(
        isinstance(item, Mapping) and (bool(item.get("mapped_to")) or isinstance(item.get("waiver"), Mapping))
        for item in invariants
    )
    ambiguities = topology.get("known_ambiguities")
    return {
        "goal_contract_complete": goal.get("review_status") == "human_reviewed",
        "topology_complete": topology.get("review_status") == "human_reviewed" and complete_coverage,
        "no_unresolved_contradiction": isinstance(ambiguities, list) and not ambiguities,
        "critical_invariant_coverage_100_percent": critical_coverage,
    }


def _derive_run_gates(
    manifest: Mapping[str, Any],
    *,
    score_report: Mapping[str, Any],
    run_manifest_path: Path,
    repo_root: Path,
    token_usage: Mapping[str, int],
    token_cap: int,
    receipts: Sequence[Mapping[str, Any]],
) -> dict[str, bool]:
    mutations = score_report.get("mutation_summary")
    critical_killed = False
    overall_killed = False
    if isinstance(mutations, Mapping):
        try:
            critical_total = int(mutations.get("critical_total", 0))
            critical_count = int(mutations.get("critical_killed", -1))
            overall_total = int(mutations.get("overall_total", 0))
            overall_count = int(mutations.get("overall_killed", -1))
            critical_killed = critical_total > 0 and critical_count == critical_total
            overall_killed = overall_total > 0 and overall_count / overall_total >= 0.95
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    preregistered = False
    prereg_hash = manifest.get("run_plan_sha256")
    if isinstance(prereg_hash, str):
        try:
            prereg_path = run_manifest_path.parent / "preregistered-plan.json"
            prereg_path = _resolve_artifact(repo_root, prereg_path.relative_to(repo_root).as_posix(), "preregistration")
            prereg = load_json(prereg_path)
            preregistered = (
                artifact_hash(prereg_path) == prereg_hash
                and isinstance(manifest.get("stopping_rule"), Mapping)
                and int(manifest.get("completed_repetitions", -1)) == int(manifest.get("planned_repetitions", -2))
            )
        except (VerdictError, TypeError, ValueError):
            preregistered = False
    return {
        "critical_mutant_kill_100_percent": critical_killed,
        "overall_mutant_kill_at_least_95_percent": overall_killed,
        "no_protected_regression": score_report.get("protected_regression_count") == 0,
        "no_required_not_run_cells": all(str(receipt.get("result") or "").upper() != "NOT_RUN" for receipt in receipts),
        "preregistered_stopping_rule": preregistered,
        "token_budget_observed": int(token_usage.get("raw", token_cap + 1)) <= token_cap,
    }


def validate_signed_promotion_evidence(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any] | Path,
    repo_root: Path,
    approved_trust_policy_sha256: str,
    approved_trust_policy_revision: str,
    now: str | dt.datetime | None = None,
) -> dict[str, Any]:
    """Validate the complete signed, independently reproduced promotion evidence chain."""

    try:
        root, _ = _load_trust_root(trust_root)
        current = _coerce_now(now)
        _validate_approved_trust_policy(
            payload,
            trust_store=root,
            repo_root=repo_root,
            approved_sha256=approved_trust_policy_sha256,
            approved_revision=approved_trust_policy_revision,
            now=current,
        )
        verdict = validate_signed_verdict(payload, trust_root=trust_root, now=current)

        goal = repo_root / "evals" / "contracts" / f"{verdict['slug']}.json"
        topology = repo_root / "evals" / "topologies" / f"{verdict['slug']}.json"
        if artifact_hash(goal) != verdict["goal_contract_sha256"]:
            raise VerdictError("goal_contract_sha256 is stale")
        if artifact_hash(topology) != verdict["topology_sha256"]:
            raise VerdictError("topology_sha256 is stale")

        goal_payload = load_json(goal)
        topology_payload = load_json(topology)
        contract_gates = _derive_contract_gates(goal_payload, topology_payload)

        run_path = _direct_bound_path(repo_root, verdict, "run_manifest_path", "run_manifest_sha256")
        run_manifest = load_json(run_path)
        _validate_manifest_bindings(run_manifest, verdict, run_id=str(verdict["run_id"]), label="primary")

        score_path = _bound_path(repo_root, verdict.get("score_report_binding"), "protected score report")
        score_report = load_json(score_path)
        expected_score_bindings = {
            "schema_version": "ProtectedScoreReport.v1",
            "run_id": verdict["run_id"],
            "candidate_sha256": verdict["candidate_sha256"],
            "dataset_sha256": verdict["dataset_sha256"],
            "scorer_sha256": verdict["scorer_sha256"],
            "scoring_status": "completed",
        }
        stale_score_fields = [
            field for field, expected in expected_score_bindings.items() if score_report.get(field) != expected
        ]
        if stale_score_fields:
            raise VerdictError(f"protected score report has stale bindings: {', '.join(stale_score_fields)}")

        sealed_path = _bound_path(
            repo_root, verdict.get("sealed_bundle_attestation_binding"), "sealed bundle attestation"
        )
        sealed = validate_sealed_bundle_attestation(load_json(sealed_path), trust_root=root, now=current)
        if sealed.get("dataset_sha256") != verdict["dataset_sha256"] or sealed.get("scorer_sha256") != verdict["scorer_sha256"]:
            raise VerdictError("sealed bundle attestation has stale dataset or scorer bindings")

        qualifications = verdict.get("judge_qualification_bindings")
        if not isinstance(qualifications, list) or not qualifications:
            raise VerdictError("judge qualification bindings must be non-empty")
        judge_qualified = True
        for binding in qualifications:
            if not isinstance(binding, Mapping):
                raise VerdictError("judge qualification binding must be an object")
            path = _bound_path(repo_root, binding, "judge qualification")
            qualification = validate_judge_qualification(load_json(path), trust_root=root, now=current)
            if binding.get("judge_id") != qualification.get("judge_id"):
                raise VerdictError("judge qualification identity does not match its binding")
            if binding.get("gold_set_commitment_sha256") == verdict["dataset_sha256"]:
                raise VerdictError("judge gold-set commitment must be distinct from the promotion dataset")
            validate_qualification_binding(
                qualification,
                judge_model_sha256=str(binding.get("judge_model_sha256") or ""),
                judge_prompt_sha256=str(binding.get("judge_prompt_sha256") or ""),
                judge_rubric_sha256=str(binding.get("judge_rubric_sha256") or ""),
                judge_tool_policy_sha256=str(binding.get("judge_tool_policy_sha256") or ""),
                judge_preregistration_sha256=str(binding.get("judge_preregistration_sha256") or ""),
                gold_set_commitment_sha256=str(binding.get("gold_set_commitment_sha256") or ""),
            )

        _direct_bound_path(
            repo_root, verdict, "evaluation_policy_path", "evaluation_policy_sha256"
        )
        _direct_bound_path(repo_root, verdict, "impact_plan_path", "impact_plan_sha256")
        _direct_bound_path(repo_root, verdict, "evaluator_path", "evaluator_sha256")
        adapters = verdict.get("adapter_bindings")
        if not isinstance(adapters, list) or not adapters:
            raise VerdictError("adapter bindings must be non-empty")
        primary_runner_identity = str(verdict.get("primary_runner_identity_sha256") or "")
        if not SHA256_RE.fullmatch(primary_runner_identity):
            raise VerdictError("primary runner identity is invalid")
        primary_adapters = [
            binding
            for binding in adapters
            if isinstance(binding, Mapping) and binding.get("phase") == "primary"
        ]
        if not primary_adapters or any(
            binding.get("runner_identity_sha256") != primary_runner_identity for binding in primary_adapters
        ):
            raise VerdictError("primary adapter bindings do not match the primary runner identity")

        auxiliary_bindings = verdict.get("auxiliary_receipt_bindings")
        if not isinstance(auxiliary_bindings, list) or not auxiliary_bindings:
            raise VerdictError("promotion requires auxiliary conformance and adjudication receipt bindings")
        auxiliary_usage: dict[tuple[str, str], dict[str, Any]] = {}
        auxiliary_totals = {"raw": 0, "cached": 0, "billed": 0}
        for binding in auxiliary_bindings:
            if not isinstance(binding, Mapping):
                raise VerdictError("auxiliary receipt binding must be an object")
            phase = str(binding.get("phase") or "")
            run_id = str(binding.get("run_id") or "")
            key = (phase, run_id)
            if phase not in {"adapter_conformance", "adjudication"} or not run_id:
                raise VerdictError("auxiliary receipt binding has an invalid phase or run ID")
            usage_path = _bound_path(repo_root, binding, "auxiliary receipt record")
            usage = load_json(usage_path)
            expected_usage_fields = {
                "schema_version",
                "raw",
                "cached",
                "billed",
                "receipt_sha256s",
            }
            if set(usage) != expected_usage_fields or usage.get("schema_version") != "ProtectedTokenUsage.v1":
                raise VerdictError("auxiliary receipt record has an invalid closed shape")
            hashes = usage.get("receipt_sha256s")
            if (
                not isinstance(hashes, list)
                or not hashes
                or len(hashes) != len(set(hashes))
                or any(not SHA256_RE.fullmatch(str(value)) for value in hashes)
            ):
                raise VerdictError("auxiliary receipt record has invalid receipt hashes")
            values = {field: usage.get(field) for field in auxiliary_totals}
            if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values.values()):
                raise VerdictError("auxiliary receipt record has invalid token usage")
            if key in auxiliary_usage:
                existing = auxiliary_usage[key]
                existing["receipt_sha256s"].extend(str(value) for value in hashes)
                for field, value in values.items():
                    existing[field] += int(value)
            else:
                auxiliary_usage[key] = {
                    **{field: int(value) for field, value in values.items()},
                    "receipt_sha256s": [str(value) for value in hashes],
                }
            for field, value in values.items():
                auxiliary_totals[field] += int(value)
        if {phase for phase, _run_id in auxiliary_usage} != {"adapter_conformance", "adjudication"}:
            raise VerdictError("promotion requires both conformance and adjudication receipt coverage")

        receipt_bindings = verdict.get("receipt_bindings")
        if not isinstance(receipt_bindings, list) or not receipt_bindings:
            raise VerdictError("execution receipt bindings must be non-empty")
        critical_by_receipt = {
            str(receipt_id): cell.get("critical") is True
            for cell in verdict.get("required_cells", [])
            if isinstance(cell, Mapping) and isinstance(cell.get("receipt_ids"), list)
            for receipt_id in cell["receipt_ids"]
        }
        primary_receipts: dict[str, tuple[Mapping[str, Any], str]] = {}
        for binding in receipt_bindings:
            if not isinstance(binding, Mapping):
                raise VerdictError("execution receipt binding must be an object")
            receipt_id = str(binding.get("receipt_id") or "")
            if not receipt_id or receipt_id in primary_receipts:
                raise VerdictError("execution receipt bindings must have unique receipt IDs")
            primary_receipts[receipt_id] = _verify_receipt_binding(
                binding,
                repo_root=repo_root,
                trust_root=root,
                verdict=verdict,
                run_id=str(verdict["run_id"]),
                now=current,
                critical=critical_by_receipt.get(receipt_id, False),
            )
        manifest_trace_hashes = run_manifest.get("raw_trace_hashes")
        receipt_trace_hashes = [str(item[0].get("raw_trace_sha256") or "") for item in primary_receipts.values()]
        if manifest_trace_hashes != receipt_trace_hashes:
            raise VerdictError("primary receipt trace commitments do not match the run manifest")
        if any(
            artifact_hash(str(receipt.get("runner_identity") or "")) != primary_runner_identity
            or receipt.get("randomization_seed") != run_manifest.get("seed")
            for receipt, _grade in primary_receipts.values()
        ):
            raise VerdictError("primary receipts do not match the primary runner identity and seed")
        validate_adapter_conformance_bindings(
            primary_adapters,
            trust_root=root,
            repo_root=repo_root,
            receipts=[item[0] for item in primary_receipts.values()],
            now=current,
        )
        critical_cell_ids = {
            str(receipt.get("cell_id") or "")
            for receipt_id, (receipt, _grade) in primary_receipts.items()
            if critical_by_receipt.get(receipt_id, False)
        }

        reproduction_bindings = verdict.get("reproduction_manifest_bindings")
        if not isinstance(reproduction_bindings, list) or not reproduction_bindings:
            raise VerdictError("independent reproduction manifest bindings must be non-empty")
        reproduction_complete = True
        primary_seed = run_manifest.get("seed")
        if not isinstance(primary_seed, int):
            raise VerdictError("primary run manifest lacks its preregistered seed")
        reproduction_run_ids: set[str] = set()
        all_reproduction_receipts: list[Mapping[str, Any]] = []
        reproduction_receipt_hashes_by_run: dict[str, list[str]] = {}
        for binding in reproduction_bindings:
            if not isinstance(binding, Mapping):
                raise VerdictError("reproduction manifest binding must be an object")
            reproduction_path = _bound_path(repo_root, binding, "reproduction manifest")
            reproduction = load_json(reproduction_path)
            run_id = str(binding.get("run_id") or "")
            if not run_id or run_id == verdict["run_id"] or run_id in reproduction_run_ids:
                raise VerdictError("independent reproduction requires distinct full run IDs")
            reproduction_run_ids.add(run_id)
            reproduction_seed = binding.get("seed")
            if (
                not isinstance(reproduction_seed, int)
                or reproduction.get("seed") != reproduction_seed
                or reproduction_seed == primary_seed
            ):
                raise VerdictError("independent reproduction requires a distinct preregistered seed")
            runner_identity = str(binding.get("runner_identity_sha256") or "")
            if not SHA256_RE.fullmatch(runner_identity) or runner_identity == primary_runner_identity:
                raise VerdictError("independent reproduction requires a distinct runner identity")
            _validate_manifest_bindings(reproduction, verdict, run_id=run_id, label="reproduction")
            reproduction_receipts = binding.get("receipt_bindings")
            if not isinstance(reproduction_receipts, list) or not reproduction_receipts:
                raise VerdictError("reproduction manifest lacks signed receipt bindings")
            reproduction_receipt_values: list[Mapping[str, Any]] = []
            reproduction_receipt_hashes_by_run[run_id] = [
                str(receipt_binding.get("sha256") or "")
                for receipt_binding in reproduction_receipts
                if isinstance(receipt_binding, Mapping)
            ]
            for receipt_binding in reproduction_receipts:
                if not isinstance(receipt_binding, Mapping):
                    raise VerdictError("reproduction receipt binding must be an object")
                receipt, grade = _verify_receipt_binding(
                    receipt_binding,
                    repo_root=repo_root,
                    trust_root=root,
                    verdict=verdict,
                    run_id=run_id,
                    now=current,
                    critical=False,
                )
                if str(receipt.get("cell_id") or "") in critical_cell_ids and grade != "A":
                    raise VerdictError("critical reproduction cells require Grade A evidence")
                if receipt.get("result") != "PASS":
                    raise VerdictError("independent reproduction contains a non-passing receipt")
                reproduction_receipt_values.append(receipt)
            all_reproduction_receipts.extend(reproduction_receipt_values)
            if any(
                artifact_hash(str(receipt.get("runner_identity") or "")) != runner_identity
                or receipt.get("randomization_seed") != reproduction_seed
                for receipt in reproduction_receipt_values
            ):
                raise VerdictError("reproduction receipts do not match the bound runner identity and seed")
            reproduction_trace_hashes = [
                str(receipt.get("raw_trace_sha256") or "") for receipt in reproduction_receipt_values
            ]
            if reproduction.get("raw_trace_hashes") != reproduction_trace_hashes:
                raise VerdictError("reproduction receipt trace commitments do not match its run manifest")
            if set(reproduction_trace_hashes) & set(receipt_trace_hashes):
                raise VerdictError("independent reproduction must produce distinct trace commitments")
            primary_trials = Counter(
                (
                    str(receipt.get("cell_id") or ""),
                    int(receipt.get("repetition", -1)),
                    int(receipt.get("order_index", -1)),
                    str(receipt.get("input_sha256") or ""),
                )
                for receipt, _grade in primary_receipts.values()
            )
            reproduction_trials = Counter(
                (
                    str(receipt.get("cell_id") or ""),
                    int(receipt.get("repetition", -1)),
                    int(receipt.get("order_index", -1)),
                    str(receipt.get("input_sha256") or ""),
                )
                for receipt in reproduction_receipt_values
            )
            if reproduction_trials != primary_trials:
                raise VerdictError("independent reproduction does not reproduce every runtime trial")
            reproduction_adapters = [
                adapter
                for adapter in adapters
                if isinstance(adapter, Mapping)
                and adapter.get("phase") == "reproduction"
                and adapter.get("runner_identity_sha256") == runner_identity
            ]
            if not reproduction_adapters:
                raise VerdictError("independent reproduction lacks runner-bound adapter conformance")
            validate_adapter_conformance_bindings(
                reproduction_adapters,
                trust_root=root,
                repo_root=repo_root,
                receipts=reproduction_receipt_values,
                now=current,
            )

        derived_cells = _derive_primary_cells(verdict, primary_receipts)
        ledger_path = _bound_path(repo_root, verdict.get("token_ledger_binding"), "global token ledger")
        token_ledger = validate_global_token_ledger(load_json(ledger_path), trust_root=root, now=current)
        if token_ledger.get("status") != "final":
            raise VerdictError("promotion requires a signed final global token ledger")
        expected_ledger_entries = {
            ("primary", str(verdict["run_id"])): [
                str(binding.get("sha256") or "")
                for binding in receipt_bindings
                if isinstance(binding, Mapping)
            ],
            **{
                ("reproduction", run_id): hashes
                for run_id, hashes in reproduction_receipt_hashes_by_run.items()
            },
            **{
                key: list(value["receipt_sha256s"])
                for key, value in auxiliary_usage.items()
            },
        }
        observed_ledger_entries: dict[tuple[str, str], list[str]] = {}
        for entry in token_ledger.get("entries", []):
            key = (str(entry.get("phase") or ""), str(entry.get("run_id") or ""))
            if key in observed_ledger_entries:
                raise VerdictError("global token ledger has duplicate phase/run entries")
            observed_ledger_entries[key] = list(entry.get("receipt_sha256s") or [])
        if {
            key: Counter(values) for key, values in observed_ledger_entries.items()
        } != {
            key: Counter(values) for key, values in expected_ledger_entries.items()
        }:
            raise VerdictError("global token ledger does not cover the exact bound receipt set")
        ledger_totals = dict(token_ledger.get("totals") or {})
        derived_usage = {
            field: int(ledger_totals.get(field, -1)) for field in ("raw", "cached", "billed")
        }
        independently_summed_usage = _sum_usage(
            [item[0] for item in primary_receipts.values()] + all_reproduction_receipts
        )
        independently_summed_usage = {
            field: independently_summed_usage[field] + auxiliary_totals[field]
            for field in independently_summed_usage
        }
        if derived_usage != independently_summed_usage:
            raise VerdictError("global token ledger totals do not match signed execution receipts")
        run_gates = _derive_run_gates(
            run_manifest,
            score_report=score_report,
            run_manifest_path=run_path,
            repo_root=repo_root,
            token_usage=derived_usage,
            token_cap=int(verdict["token_cap"]),
            receipts=[item[0] for item in primary_receipts.values()],
        )
        derived_gates = {
            **contract_gates,
            **run_gates,
            "qualified_judges_only": judge_qualified,
            "sealed_bundle_valid": True,
            "independent_reproduction": reproduction_complete,
        }
        if derived_gates != dict(verdict["hard_gates"]):
            raise VerdictError("verdict hard gates do not match independently derived evidence")
        if derived_cells != list(verdict["required_cells"]):
            raise VerdictError("verdict required cells do not match signed receipts")
        if derived_usage != dict(verdict["token_usage"]):
            raise VerdictError("verdict token usage does not match signed receipts")
        return {
            "schema_version": "PromotionEvidenceValidation.v1",
            "promotion_allowed": verdict["status"] == "promote",
            "derived_hard_gates": derived_gates,
            "derived_required_cells": derived_cells,
            "derived_token_usage": derived_usage,
            "evidence_grades": {key: grade for key, (_receipt, grade) in primary_receipts.items()},
            "verdict_payload_sha256": artifact_hash(verdict),
        }
    except (AttestationError, QualificationError, ProvenanceError) as exc:
        raise VerdictError(str(exc)) from exc


def build_promotion_verdict(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an unsigned verdict body before protected infrastructure signs it."""

    if "signature" in payload:
        raise VerdictError("build_promotion_verdict accepts unsigned payloads only")
    placeholder = {
        "algorithm": "Ed25519",
        "key_id": "pending",
        "purpose": "promotion_verdict",
        "signed_at": "1970-01-01T00:00:00Z",
        "payload_sha256": "0" * 64,
        "value_base64": "pending",
    }
    _validate_verdict_body({**payload, "signature": placeholder})
    return dict(payload)
