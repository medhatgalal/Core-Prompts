from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Protocol


EVIDENCE_STATUSES = (
    "structural_ready",
    "behavioral_pending",
    "promote",
    "hold",
    "blocked_contract",
    "inconclusive",
    "rollback",
    "stale_evidence",
)

PROFILE_TOKEN_CAPS = {
    "static": 0,
    "native": 0,
    "routing-canary": 300_000,
    "canary": 1_250_000,
    "promotion": 5_000_000,
    "cross-host": 12_000_000,
    "sweep": 30_000_000,
}

GOAL_REQUIRED = (
    "schema_version",
    "slug",
    "target",
    "intended_outcome",
    "change_class",
    "non_goals",
    "protected_behaviors",
    "editable_behavior",
    "primary_outcome",
    "secondary_outcomes",
    "regression_limits",
    "cost_latency_limits",
    "runtime_envelope",
    "promotion_rule",
    "rollback_trigger",
    "source_clause_hashes",
    "review_status",
)

TOPOLOGY_REQUIRED = (
    "schema_version",
    "slug",
    "ssot_sha256",
    "nodes",
    "composition",
    "state_machine",
    "outputs",
    "authority_boundaries",
    "resources",
    "handoffs",
    "protected_invariants",
    "risk_tiers",
    "source_references",
    "known_ambiguities",
    "coverage_policy",
    "normative_clause_coverage",
    "review_status",
)

PROMOTION_REQUIRED = (
    "schema_version",
    "run_id",
    "slug",
    "status",
    "baseline_revision",
    "candidate_revision",
    "baseline_sha256",
    "candidate_sha256",
    "goal_contract_sha256",
    "topology_sha256",
    "dataset_sha256",
    "scorer_sha256",
    "run_manifest_path",
    "run_manifest_sha256",
    "sealed_bundle_attestation_binding",
    "score_report_binding",
    "token_ledger_binding",
    "approved_trust_policy_binding",
    "primary_runner_identity_sha256",
    "receipt_bindings",
    "auxiliary_receipt_bindings",
    "adapter_bindings",
    "judge_qualification_bindings",
    "reproduction_manifest_bindings",
    "evaluation_policy_path",
    "evaluation_policy_sha256",
    "impact_plan_path",
    "impact_plan_sha256",
    "evaluator_path",
    "evaluator_sha256",
    "trust_root_sha256",
    "evaluator_version",
    "profile",
    "token_cap",
    "required_cells",
    "hard_gates",
    "token_usage",
    "issued_at",
    "expires_at",
    "issuer",
    "signature",
)

PROMOTION_ALLOWED = frozenset(PROMOTION_REQUIRED)

REQUIRED_PROMOTION_GATES = (
    "goal_contract_complete",
    "topology_complete",
    "no_unresolved_contradiction",
    "critical_invariant_coverage_100_percent",
    "critical_mutant_kill_100_percent",
    "overall_mutant_kill_at_least_95_percent",
    "no_protected_regression",
    "no_required_not_run_cells",
    "qualified_judges_only",
    "sealed_bundle_valid",
    "preregistered_stopping_rule",
    "token_budget_observed",
    "independent_reproduction",
)


class ContractError(ValueError):
    """Raised when evaluation evidence does not satisfy its public contract."""


class PromotionEvidenceVerifier(Protocol):
    def __call__(
        self,
        payload: Mapping[str, Any],
        *,
        trust_root: Path,
        repo_root: Path,
        approved_trust_policy_sha256: str,
        approved_trust_policy_revision: str,
        now: str | datetime | None = None,
    ) -> Mapping[str, Any]: ...


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def artifact_hash(value: str | bytes | Path | Mapping[str, Any]) -> str:
    if isinstance(value, Path):
        data = value.read_bytes()
    elif isinstance(value, Mapping):
        data = canonical_json(value).encode("utf-8")
    elif isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = value
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"expected JSON object: {path}")
    return payload


def _require(payload: Mapping[str, Any], required: tuple[str, ...], kind: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ContractError(f"{kind} missing required fields: {', '.join(missing)}")


def validate_goal_contract(payload: Mapping[str, Any]) -> None:
    _require(payload, GOAL_REQUIRED, "GoalContract.v1")
    if payload["schema_version"] != "GoalContract.v1":
        raise ContractError("unsupported Goal Contract schema")
    if payload["review_status"] not in {"draft", "human_reviewed", "blocked"}:
        raise ContractError("invalid Goal Contract review_status")
    if not isinstance(payload["source_clause_hashes"], list):
        raise ContractError("source_clause_hashes must be a list")


def validate_topology(payload: Mapping[str, Any]) -> None:
    _require(payload, TOPOLOGY_REQUIRED, "CapabilityTopology.v1")
    if payload["schema_version"] != "CapabilityTopology.v1":
        raise ContractError("unsupported topology schema")
    coverage = payload["normative_clause_coverage"]
    if not isinstance(coverage, Mapping) or "total" not in coverage or "mapped" not in coverage:
        raise ContractError("normative_clause_coverage must contain total and mapped")
    if payload["review_status"] == "human_reviewed" and payload["known_ambiguities"]:
        raise ContractError("human-reviewed topology cannot contain unresolved ambiguities")


def _parse_timestamp(value: object, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{field} must include a timezone")
    return parsed


def _bound_artifact(repo_root: Path, path_value: object, expected_sha256: object, label: str) -> Path:
    relative = Path(str(path_value))
    if relative.is_absolute() or ".." in relative.parts:
        raise ContractError(f"{label} path must be repository-relative")
    root = repo_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ContractError(f"{label} path escapes the repository") from exc
    if not path.is_file() or artifact_hash(path) != expected_sha256:
        raise ContractError(f"{label} artifact is missing or stale")
    return path


def _validate_artifact_bindings(payload: Mapping[str, Any], repo_root: Path) -> None:
    _bound_artifact(repo_root, payload["run_manifest_path"], payload["run_manifest_sha256"], "run manifest")
    sealed_binding = payload["sealed_bundle_attestation_binding"]
    if not isinstance(sealed_binding, Mapping):
        raise ContractError("sealed_bundle_attestation_binding must be an object")
    _bound_artifact(
        repo_root,
        sealed_binding.get("path"),
        sealed_binding.get("sha256"),
        "sealed bundle attestation",
    )
    score_binding = payload["score_report_binding"]
    if not isinstance(score_binding, Mapping):
        raise ContractError("score_report_binding must be an object")
    _bound_artifact(repo_root, score_binding.get("path"), score_binding.get("sha256"), "protected score report")
    ledger_binding = payload["token_ledger_binding"]
    if not isinstance(ledger_binding, Mapping):
        raise ContractError("token_ledger_binding must be an object")
    _bound_artifact(repo_root, ledger_binding.get("path"), ledger_binding.get("sha256"), "global token ledger")
    approved_policy = payload["approved_trust_policy_binding"]
    if not isinstance(approved_policy, Mapping):
        raise ContractError("approved_trust_policy_binding must be an object")
    _bound_artifact(
        repo_root,
        approved_policy.get("path"),
        approved_policy.get("sha256"),
        "approved trust policy",
    )
    if not re.fullmatch(r"[0-9a-f]{40}", str(approved_policy.get("revision") or "")):
        raise ContractError("approved trust policy revision must be a full Git commit ID")
    _bound_artifact(
        repo_root,
        payload["evaluation_policy_path"],
        payload["evaluation_policy_sha256"],
        "evaluation policy",
    )
    _bound_artifact(repo_root, payload["impact_plan_path"], payload["impact_plan_sha256"], "impact plan")
    _bound_artifact(repo_root, payload["evaluator_path"], payload["evaluator_sha256"], "evaluator")
    binding_specs = (
        ("receipt_bindings", "receipt_id", "execution receipt"),
        ("auxiliary_receipt_bindings", "binding_id", "auxiliary receipt record"),
        ("adapter_bindings", "adapter_id", "adapter"),
        ("judge_qualification_bindings", "judge_id", "judge qualification"),
        ("reproduction_manifest_bindings", "run_id", "reproduction manifest"),
    )
    for collection_name, identity_field, label in binding_specs:
        collection = payload[collection_name]
        if not isinstance(collection, list) or not collection:
            raise ContractError(f"{collection_name} must be a non-empty list")
        identities: set[str] = set()
        for index, binding in enumerate(collection):
            if not isinstance(binding, Mapping):
                raise ContractError(f"{collection_name}[{index}] must be an object")
            identity = str(binding.get(identity_field) or "")
            if collection_name == "adapter_bindings":
                phase = str(binding.get("phase") or "")
                runner_identity = str(binding.get("runner_identity_sha256") or "")
                if phase not in {"primary", "reproduction"} or not re.fullmatch(
                    r"[0-9a-f]{64}", runner_identity
                ):
                    raise ContractError("adapter binding must include a valid phase and runner identity")
                identity = f"{phase}:{identity}"
            if collection_name == "auxiliary_receipt_bindings":
                phase = str(binding.get("phase") or "")
                run_id = str(binding.get("run_id") or "")
                if phase not in {"adapter_conformance", "adjudication"} or not run_id:
                    raise ContractError("auxiliary receipt binding must include a valid phase and run ID")
                identity = f"{phase}:{run_id}:{identity}"
            if not identity or identity in identities:
                raise ContractError(f"{collection_name} contains a missing or duplicate {identity_field}")
            identities.add(identity)
            _bound_artifact(repo_root, binding.get("path"), binding.get("sha256"), f"{label} {identity}")
            if collection_name == "reproduction_manifest_bindings":
                receipts = binding.get("receipt_bindings")
                if not isinstance(receipts, list) or not receipts:
                    raise ContractError("reproduction manifest binding must include signed receipt bindings")
                receipt_ids: set[str] = set()
                for receipt in receipts:
                    if not isinstance(receipt, Mapping):
                        raise ContractError("reproduction receipt binding must be an object")
                    receipt_id = str(receipt.get("receipt_id") or "")
                    if not receipt_id or receipt_id in receipt_ids:
                        raise ContractError("reproduction receipt bindings must have unique receipt IDs")
                    receipt_ids.add(receipt_id)
                    _bound_artifact(
                        repo_root,
                        receipt.get("path"),
                        receipt.get("sha256"),
                        f"reproduction receipt {receipt_id}",
                    )


def _default_promotion_evidence_verifier(
    payload: Mapping[str, Any],
    *,
    trust_root: Path,
    repo_root: Path,
    approved_trust_policy_sha256: str,
    approved_trust_policy_revision: str,
    now: str | datetime | None = None,
) -> Mapping[str, Any]:
    try:
        from .verdict import validate_signed_promotion_evidence
    except ImportError as exc:
        raise ContractError("signed promotion evidence verifier is unavailable") from exc
    try:
        verified = validate_signed_promotion_evidence(
            payload,
            trust_root=trust_root,
            repo_root=repo_root,
            approved_trust_policy_sha256=approved_trust_policy_sha256,
            approved_trust_policy_revision=approved_trust_policy_revision,
            now=now,
        )
    except ValueError as exc:
        raise ContractError(f"signed promotion evidence refused: {exc}") from exc
    if not isinstance(verified, Mapping):
        raise ContractError("signed promotion evidence verifier returned no derived evidence")
    return verified


def _derived_field(verified: Mapping[str, Any], name: str) -> Any:
    if name in verified:
        return verified[name]
    derived_name = f"derived_{name}"
    if derived_name in verified:
        return verified[derived_name]
    raise ContractError(f"signed promotion evidence omitted derived {name}")


def validate_promotion_verdict(
    payload: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
    trust_root: Path | None = None,
    approved_trust_policy_sha256: str | None = None,
    approved_trust_policy_revision: str | None = None,
    now: str | datetime | None = None,
    evidence_verifier: PromotionEvidenceVerifier | None = None,
) -> None:
    _require(payload, PROMOTION_REQUIRED, "PromotionVerdict.v1")
    unknown = sorted(set(payload) - PROMOTION_ALLOWED)
    if unknown:
        raise ContractError(f"PromotionVerdict.v1 contains unknown fields: {', '.join(unknown)}")
    if payload["schema_version"] != "PromotionVerdict.v1":
        raise ContractError("unsupported promotion verdict schema")
    if payload["status"] not in EVIDENCE_STATUSES:
        raise ContractError(f"invalid promotion status: {payload['status']}")
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
        "primary_runner_identity_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(payload[field])):
            raise ContractError(f"{field} must be a lowercase SHA-256 digest")
    for field in ("baseline_revision", "candidate_revision"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(payload[field])):
            raise ContractError(f"{field} must be a full lowercase Git commit ID")
    issued_at = _parse_timestamp(payload["issued_at"], "issued_at")
    expires_at = _parse_timestamp(payload["expires_at"], "expires_at")
    if expires_at <= issued_at:
        raise ContractError("expires_at must be later than issued_at")
    signature = payload["signature"]
    signature_fields = ("algorithm", "key_id", "purpose", "signed_at", "payload_sha256", "value_base64")
    if not isinstance(signature, Mapping) or not all(signature.get(key) for key in signature_fields):
        raise ContractError(f"signature must contain {', '.join(signature_fields)}")
    if signature["algorithm"] != "Ed25519" or signature["purpose"] != "promotion_verdict":
        raise ContractError("signature must use Ed25519 for promotion_verdict")
    _parse_timestamp(signature["signed_at"], "signature.signed_at")
    if not re.fullmatch(r"[0-9a-f]{64}", str(signature["payload_sha256"])):
        raise ContractError("signature.payload_sha256 must be a lowercase SHA-256 digest")
    if payload["status"] == "promote":
        if repo_root is None:
            raise ContractError("promote verdict validation requires a repository root")
        if trust_root is None:
            trust_root = repo_root / "evals" / "trust-root.json"
        if not trust_root.is_file():
            raise ContractError("promote verdict validation requires a trust root")
        if artifact_hash(trust_root) != payload["trust_root_sha256"]:
            raise ContractError("promotion trust root is missing or stale")
        if not re.fullmatch(r"[0-9a-f]{64}", str(approved_trust_policy_sha256 or "")):
            raise ContractError("promote verdict requires an operator-approved trust policy hash")
        if not re.fullmatch(r"[0-9a-f]{40}", str(approved_trust_policy_revision or "")):
            raise ContractError("promote verdict requires an operator-approved trust policy revision")
        policy_binding = payload["approved_trust_policy_binding"]
        if (
            policy_binding.get("sha256") != approved_trust_policy_sha256
            or policy_binding.get("revision") != approved_trust_policy_revision
        ):
            raise ContractError("verdict trust policy does not match explicit operator approval")
        _validate_artifact_bindings(payload, repo_root)
        verifier = evidence_verifier or _default_promotion_evidence_verifier
        verified = verifier(
            payload,
            trust_root=trust_root,
            repo_root=repo_root,
            approved_trust_policy_sha256=approved_trust_policy_sha256,
            approved_trust_policy_revision=approved_trust_policy_revision,
            now=now,
        )
        if not isinstance(verified, Mapping):
            raise ContractError("signed promotion evidence verifier returned no derived evidence")
        derived_gates = dict(_derived_field(verified, "hard_gates"))
        derived_cells = list(_derived_field(verified, "required_cells"))
        derived_usage = dict(_derived_field(verified, "token_usage"))
        gates = dict(payload["hard_gates"])
        if canonical_json(gates) != canonical_json(derived_gates):
            raise ContractError("verdict hard gates do not match signed evidence")
        if canonical_json({"cells": payload["required_cells"]}) != canonical_json({"cells": derived_cells}):
            raise ContractError("verdict required cells do not match signed receipts")
        if canonical_json(dict(payload["token_usage"])) != canonical_json(derived_usage):
            raise ContractError("verdict token usage does not match signed receipts")
        missing_gates = [name for name in REQUIRED_PROMOTION_GATES if name not in gates]
        if missing_gates:
            raise ContractError(f"promote verdict omits required hard gates: {', '.join(missing_gates)}")
        failed = [name for name in REQUIRED_PROMOTION_GATES if gates[name] is not True]
        if failed:
            raise ContractError(f"promote verdict has failed hard gates: {', '.join(failed)}")
        if not payload["required_cells"]:
            raise ContractError("promote verdict has no required runtime cells")
        for cell in payload["required_cells"]:
            if cell.get("result") not in {"pass", "PASS"}:
                raise ContractError("promote verdict contains a non-passing required cell")
            if cell.get("evidence_grade") not in {"A", "B"}:
                raise ContractError("promote verdict contains unsupported or self-reported provenance")
            if cell.get("critical") is True and cell.get("evidence_grade") != "A":
                raise ContractError("promote verdict contains a critical cell below evidence grade A")
            receipt_ids = cell.get("receipt_ids")
            if not isinstance(receipt_ids, list) or not receipt_ids or len(receipt_ids) != len(set(receipt_ids)):
                raise ContractError("promote verdict contains a cell without unique receipt bindings")
            model = str(cell.get("resolved_model_identifier") or "")
            if not model or model.lower() in {"default", "latest", "auto"}:
                raise ContractError("promote verdict contains an unresolved model identifier")
        if payload["profile"] not in PROFILE_TOKEN_CAPS:
            raise ContractError("promote verdict uses an unknown profile")
        if int(payload["token_cap"]) != PROFILE_TOKEN_CAPS[payload["profile"]]:
            raise ContractError("promote verdict token cap does not match policy")
        if int(dict(payload["token_usage"]).get("raw", 0)) > int(payload["token_cap"]):
            raise ContractError("promote verdict exceeds its raw-token cap")
    if repo_root is not None:
        goal_path = repo_root / "evals" / "contracts" / f"{payload['slug']}.json"
        topology_path = repo_root / "evals" / "topologies" / f"{payload['slug']}.json"
        for label, path, expected in (
            ("goal contract", goal_path, payload["goal_contract_sha256"]),
            ("topology", topology_path, payload["topology_sha256"]),
        ):
            if not path.exists() or artifact_hash(path) != expected:
                raise ContractError(f"{label} evidence is missing or stale")
        if payload["status"] == "promote":
            goal = load_json(goal_path)
            topology = load_json(topology_path)
            validate_goal_contract(goal)
            validate_topology(topology)
            if goal["review_status"] != "human_reviewed":
                raise ContractError("Goal Contract is not human reviewed")
            if topology["review_status"] != "human_reviewed" or topology["known_ambiguities"]:
                raise ContractError("Capability Topology is not closed and human reviewed")
            coverage = topology["normative_clause_coverage"]
            if int(coverage["mapped"]) + int(coverage.get("waived", 0)) != int(coverage["total"]):
                raise ContractError("normative clause coverage is incomplete")
