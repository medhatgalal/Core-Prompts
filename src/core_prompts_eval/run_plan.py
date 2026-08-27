from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .contracts import PROFILE_TOKEN_CAPS, artifact_hash


RUN_PLAN_REQUIRED = (
    "schema_version",
    "preregistration_status",
    "run_id",
    "slug",
    "profile",
    "baseline_revision",
    "candidate_revision",
    "baseline_sha256",
    "candidate_sha256",
    "goal_contract_sha256",
    "topology_sha256",
    "evaluation_policy_sha256",
    "evaluation_policy_path",
    "impact_plan_sha256",
    "impact_plan_path",
    "judge_qualification_sha256",
    "judge_qualifications",
    "sealed_bundle_attestation_sha256",
    "sealed_bundle_attestation_path",
    "evaluator_package_sha256",
    "dataset",
    "scorer_sha256",
    "scorer_path",
    "cli_versions",
    "cli_sha256",
    "trust_root_path",
    "trust_root_sha256",
    "model_cells",
    "approval_policy",
    "seed",
    "runner_identity",
    "order",
    "repetitions",
    "max_tokens_per_call",
    "token_budget",
    "timeout_seconds",
    "max_output_bytes",
    "stopping_rule",
    "independent_reproduction_required",
    "created_at",
)

RUN_PLAN_OPTIONAL = {"adapter", "tool_policy"}

HASH_FIELDS = (
    "baseline_sha256",
    "candidate_sha256",
    "goal_contract_sha256",
    "topology_sha256",
    "evaluation_policy_sha256",
    "impact_plan_sha256",
    "judge_qualification_sha256",
    "sealed_bundle_attestation_sha256",
    "evaluator_package_sha256",
    "scorer_sha256",
    "cli_sha256",
    "trust_root_sha256",
)


class RunPlanError(ValueError):
    """Raised when a model-mediated evaluation plan is not safely preregistered."""


@dataclass(frozen=True)
class RunPlan:
    path: Path
    payload: Mapping[str, Any]

    @property
    def run_id(self) -> str:
        return str(self.payload["run_id"])

    @property
    def profile(self) -> str:
        return str(self.payload["profile"])

    @property
    def adapter_id(self) -> str:
        return str(self._single_adapter()["id"])

    @property
    def adapter_version(self) -> str:
        return str(self._single_adapter()["version"])

    def _single_adapter(self) -> Mapping[str, Any]:
        binding = self.payload.get("adapter")
        if isinstance(binding, Mapping):
            return binding
        cells = self.payload.get("model_cells")
        if isinstance(cells, list) and len(cells) == 1 and isinstance(cells[0], Mapping):
            cell_binding = cells[0].get("adapter")
            if isinstance(cell_binding, Mapping):
                return cell_binding
        raise RunPlanError("multi-cell run plans do not have one global adapter")

    @property
    def sha256(self) -> str:
        return artifact_hash(dict(self.payload))


def load_run_plan(path: Path) -> RunPlan:
    path = path.resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunPlanError(f"cannot load run plan: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunPlanError("run plan must be a JSON object")
    validate_run_plan(payload)
    return RunPlan(path=path, payload=payload)


def validate_run_plan(payload: Mapping[str, Any]) -> None:
    missing = [field for field in RUN_PLAN_REQUIRED if field not in payload]
    if missing:
        raise RunPlanError(f"run plan missing required fields: {', '.join(missing)}")
    unexpected = sorted(set(payload) - set(RUN_PLAN_REQUIRED) - RUN_PLAN_OPTIONAL)
    if unexpected:
        raise RunPlanError(f"run plan contains unsupported fields: {', '.join(unexpected)}")
    if payload["schema_version"] != "EvalRunPlan.v1":
        raise RunPlanError("unsupported run plan schema")
    if payload["preregistration_status"] != "locked":
        raise RunPlanError("run plan must be locked before model calls")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,127}", str(payload["run_id"])):
        raise RunPlanError("run_id is not filesystem safe")
    if payload["profile"] not in PROFILE_TOKEN_CAPS or payload["profile"] in {"static", "native"}:
        raise RunPlanError("run plan profile must be model mediated")
    for field in HASH_FIELDS:
        if not re.fullmatch(r"[0-9a-f]{64}", str(payload[field])):
            raise RunPlanError(f"{field} must be a lowercase SHA-256 digest")
    for field in ("baseline_revision", "candidate_revision", "slug", "created_at"):
        if not str(payload[field]).strip():
            raise RunPlanError(f"{field} must not be empty")
    for field in (
        "evaluation_policy_path",
        "impact_plan_path",
        "sealed_bundle_attestation_path",
        "scorer_path",
        "trust_root_path",
    ):
        if not str(payload[field]).strip():
            raise RunPlanError(f"{field} must not be empty")
    qualifications = payload["judge_qualifications"]
    if not isinstance(qualifications, list) or not qualifications:
        raise RunPlanError("judge_qualifications must contain at least one path and hash binding")
    qualification_hashes: list[str] = []
    for index, binding in enumerate(qualifications):
        if not isinstance(binding, Mapping) or not str(binding.get("path") or ""):
            raise RunPlanError(f"judge_qualifications[{index}] must bind a path and SHA-256 digest")
        digest = str(binding.get("sha256") or "")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise RunPlanError(f"judge_qualifications[{index}].sha256 must be a lowercase SHA-256 digest")
        qualification_hashes.append(digest)
    aggregate = qualification_hashes[0] if len(qualification_hashes) == 1 else artifact_hash({"sha256": qualification_hashes})
    if aggregate != payload["judge_qualification_sha256"]:
        raise RunPlanError("judge qualification aggregate hash does not match its bindings")
    dataset = payload["dataset"]
    if not isinstance(dataset, Mapping) or not str(dataset.get("path") or ""):
        raise RunPlanError("dataset must bind a path and SHA-256 digest")
    if not Path(str(dataset["path"])).expanduser().is_absolute():
        raise RunPlanError("sealed dataset path must be absolute")
    if not re.fullmatch(r"[0-9a-f]{64}", str(dataset.get("sha256") or "")):
        raise RunPlanError("dataset.sha256 must be a lowercase SHA-256 digest")
    if not isinstance(payload["cli_versions"], Mapping) or not str(payload["cli_versions"].get("capability-eval") or ""):
        raise RunPlanError("cli_versions must bind capability-eval")
    cells = payload["model_cells"]
    if not isinstance(cells, list) or not cells:
        raise RunPlanError("model_cells must contain at least one resolved cell")
    for index, cell in enumerate(cells):
        if not isinstance(cell, Mapping):
            raise RunPlanError(f"model_cells[{index}] must be an object")
        model = str(cell.get("resolved_model_identifier") or "")
        if not model or model.lower() in {"default", "latest", "auto"}:
            raise RunPlanError(f"model_cells[{index}] has an unresolved model identifier")
        allowed_cell_fields = {
            "id",
            "host",
            "provider",
            "resolved_model_identifier",
            "model_version",
            "effort",
            "cli_version",
            "cli_sha256",
            "required",
            "adapter_conformance_binding",
            "adapter",
            "tool_policy",
            "credential_binding",
        }
        unexpected_cell_fields = sorted(set(cell) - allowed_cell_fields)
        if unexpected_cell_fields:
            raise RunPlanError(
                f"model_cells[{index}] contains unsupported fields: {', '.join(unexpected_cell_fields)}"
            )
        for field in ("id", "host", "provider", "model_version", "effort", "cli_version"):
            if not str(cell.get(field) or ""):
                raise RunPlanError(f"model_cells[{index}].{field} must not be empty")
        if not re.fullmatch(r"[0-9a-f]{64}", str(cell.get("cli_sha256") or "")):
            raise RunPlanError(f"model_cells[{index}].cli_sha256 must be a lowercase SHA-256 digest")
        if not isinstance(cell.get("required"), bool):
            raise RunPlanError(f"model_cells[{index}].required must be boolean")
        _validate_credential_binding(
            cell.get("credential_binding"), f"model_cells[{index}].credential_binding"
        )
        binding = cell.get("adapter_conformance_binding")
        if cell["required"] is True:
            if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256"}:
                raise RunPlanError(
                    f"model_cells[{index}] requires an adapter_conformance_binding with path and sha256"
                )
            if not str(binding.get("path") or "") or not re.fullmatch(
                r"[0-9a-f]{64}", str(binding.get("sha256") or "")
            ):
                raise RunPlanError(f"model_cells[{index}] adapter conformance binding is invalid")
        elif binding is not None:
            raise RunPlanError(f"model_cells[{index}] non-required cells cannot bind promotion conformance")
    if len(cells) > 1:
        if "adapter" in payload or "tool_policy" in payload:
            raise RunPlanError("multi-cell plans require per-cell adapter and tool_policy bindings")
        for index, cell in enumerate(cells):
            _validate_adapter_binding(cell.get("adapter"), f"model_cells[{index}].adapter")
            _validate_tool_policy(cell.get("tool_policy"), f"model_cells[{index}].tool_policy")
    else:
        cell = cells[0]
        if "adapter" in cell and "adapter" in payload:
            raise RunPlanError("single-cell plans cannot bind both global and per-cell adapter")
        if "tool_policy" in cell and "tool_policy" in payload:
            raise RunPlanError("single-cell plans cannot bind both global and per-cell tool_policy")
        _validate_adapter_binding(cell.get("adapter", payload.get("adapter")), "single-cell adapter")
        _validate_tool_policy(cell.get("tool_policy", payload.get("tool_policy")), "single-cell tool_policy")
    if not isinstance(payload["approval_policy"], Mapping):
        raise RunPlanError("approval_policy must be an object")
    if payload["approval_policy"].get("model_calls") != "explicit_cli_flag":
        raise RunPlanError("approval_policy must require the explicit CLI model-call flag")
    if payload["approval_policy"].get("human_reviewed") is not True:
        raise RunPlanError("approval_policy must record human review before execution")
    if payload["order"] not in {"baseline_first", "candidate_first", "seeded_balanced"}:
        raise RunPlanError("unsupported paired execution order")
    if not str(payload["runner_identity"] or "").strip():
        raise RunPlanError("runner_identity must be a non-empty opaque identity")
    repetitions = _positive_int(payload, "repetitions")
    _positive_int(payload, "max_tokens_per_call")
    token_budget = _positive_int(payload, "token_budget")
    _positive_int(payload, "timeout_seconds")
    _positive_int(payload, "max_output_bytes")
    if token_budget > PROFILE_TOKEN_CAPS[str(payload["profile"])]:
        raise RunPlanError("run plan token budget exceeds the profile hard cap")
    stopping_rule = payload["stopping_rule"]
    if not isinstance(stopping_rule, Mapping) or stopping_rule.get("kind") != "fixed_repetitions":
        raise RunPlanError("only a fixed preregistered stopping rule is supported")
    if int(stopping_rule.get("repetitions", -1)) != repetitions:
        raise RunPlanError("stopping rule repetitions must equal planned repetitions")
    if not isinstance(payload["independent_reproduction_required"], bool):
        raise RunPlanError("independent_reproduction_required must be boolean")
    if payload["profile"] == "promotion" and payload["independent_reproduction_required"] is not True:
        raise RunPlanError("promotion plans must require independent reproduction")
    if payload["profile"] == "promotion" and any(cell["required"] is not True for cell in cells):
        raise RunPlanError("promotion plans must mark every model cell required")


def _positive_int(payload: Mapping[str, Any], field: str) -> int:
    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RunPlanError(f"{field} must be a positive integer")
    return value


def _validate_adapter_binding(value: object, label: str) -> None:
    if (
        not isinstance(value, Mapping)
        or set(value) != {"id", "version", "sha256"}
        or not str(value.get("id") or "")
        or not str(value.get("version") or "")
        or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sha256") or ""))
    ):
        raise RunPlanError(f"{label} must bind exactly id, version, and SHA-256 digest")


def _validate_tool_policy(value: object, label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != {"mode", "allowed"} or not str(value.get("mode") or ""):
        raise RunPlanError(f"{label} must bind exactly mode and allowed")
    allowed = value.get("allowed")
    if (
        not isinstance(allowed, list)
        or len(set(allowed)) != len(allowed)
        or any(
            not isinstance(item, str)
            or re.fullmatch(r"[A-Za-z0-9_.:@/-]+", item) is None
            for item in allowed
        )
    ):
        raise RunPlanError(f"{label}.allowed must be a unique safe argv list")
    if value["mode"] == "none" and allowed:
        raise RunPlanError(f"{label} mode none cannot allow tools")
    if value["mode"] != "none" and not allowed:
        raise RunPlanError(f"{label} non-none mode requires an explicit allowlist")


def _validate_credential_binding(value: object, label: str) -> None:
    if not isinstance(value, Mapping):
        raise RunPlanError(f"{label} must be an object")
    kind = value.get("kind")
    common = {"kind", "descriptor_path", "descriptor_sha256"}
    expected = {
        "none": common,
        "protected_env": common | {"name"},
        "protected_service_file": common
        | {"name", "format", "source_path", "source_sha256"},
    }.get(str(kind))
    if expected is None or set(value) != expected:
        raise RunPlanError(f"{label} has an unsupported closed credential shape")
    if not str(value.get("descriptor_path") or "") or not re.fullmatch(
        r"[0-9a-f]{64}", str(value.get("descriptor_sha256") or "")
    ):
        raise RunPlanError(f"{label} descriptor binding is invalid")
    if kind == "protected_env" and value.get("name") != "OPENAI_API_KEY":
        raise RunPlanError(f"{label} supports only protected OPENAI_API_KEY")
    if kind == "protected_service_file":
        if (
            value.get("name") != "KIRO_SERVICE_CREDENTIAL_FILE"
            or value.get("format") != "kiro-service-credential-v1"
            or not Path(str(value.get("source_path") or "")).expanduser().is_absolute()
            or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("source_sha256") or ""))
        ):
            raise RunPlanError(f"{label} Kiro service credential binding is invalid")


__all__ = ["RunPlan", "RunPlanError", "load_run_plan", "validate_run_plan"]
