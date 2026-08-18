from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


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
    "baseline_sha256",
    "candidate_sha256",
    "goal_contract_sha256",
    "topology_sha256",
    "dataset_sha256",
    "scorer_sha256",
    "evaluator_version",
    "profile",
    "token_cap",
    "required_cells",
    "hard_gates",
    "token_usage",
    "created_at",
)

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


def validate_promotion_verdict(payload: Mapping[str, Any], *, repo_root: Path | None = None) -> None:
    _require(payload, PROMOTION_REQUIRED, "PromotionVerdict.v1")
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
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(payload[field])):
            raise ContractError(f"{field} must be a lowercase SHA-256 digest")
    if payload["status"] == "promote":
        gates = dict(payload["hard_gates"])
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
            sealed = load_json(repo_root / "evals" / "sealed-manifest.json")
            if sealed.get("status") != "ready" or sealed.get("candidate_visible") is not False:
                raise ContractError("sealed promotion bundle is unavailable or compromised")
            if sealed.get("bundle_sha256") != payload["dataset_sha256"]:
                raise ContractError("sealed promotion bundle hash does not match the verdict")
