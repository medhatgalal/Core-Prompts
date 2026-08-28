from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from core_prompts_eval.run_plan import RunPlanError, _validate_credential_binding


ROOT = Path(__file__).resolve().parents[1]
DIGEST = "a" * 64


def test_kiro_api_key_hash_only_metadata_is_structurally_accepted() -> None:
    binding = {
        "kind": "protected_env",
        "name": "KIRO_API_KEY",
        "descriptor_sha256": DIGEST,
    }

    _validate_credential_binding(
        binding,
        "model_cells[0].credential_binding",
        provider="kiro",
        host="kiro",
    )


def test_obsolete_kiro_service_file_contract_is_rejected() -> None:
    binding = {
        "kind": "protected_service_file",
        "name": "KIRO_SERVICE_CREDENTIAL_FILE",
        "format": "kiro-service-credential-v1",
        "source_path": "/protected/credential.json",
        "source_sha256": DIGEST,
        "descriptor_sha256": DIGEST,
    }

    with pytest.raises(RunPlanError, match="unsupported closed credential shape"):
        _validate_credential_binding(
            binding,
            "model_cells[0].credential_binding",
            provider="kiro",
            host="kiro",
        )


@pytest.mark.parametrize("forbidden", ["value", "path", "descriptor_path", "source_path", "source_sha256"])
def test_public_credential_metadata_rejects_values_paths_and_source_hashes(forbidden: str) -> None:
    binding = {
        "kind": "protected_env",
        "name": "KIRO_API_KEY",
        "descriptor_sha256": DIGEST,
        forbidden: "forbidden",
    }
    with pytest.raises(RunPlanError, match="unsupported closed credential shape"):
        _validate_credential_binding(
            binding,
            "model_cells[0].credential_binding",
            provider="kiro",
            host="kiro",
        )


def test_provider_cannot_claim_another_providers_official_variable() -> None:
    with pytest.raises(RunPlanError, match="official protected environment variable"):
        _validate_credential_binding(
            {"kind": "protected_env", "name": "OPENAI_API_KEY", "descriptor_sha256": DIGEST},
            "model_cells[0].credential_binding",
            provider="kiro",
            host="kiro",
        )


def test_run_plan_schema_contains_only_hash_only_env_credential_variants() -> None:
    schema = json.loads((ROOT / "evals/schemas/eval-run-plan.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    credential = schema["properties"]["model_cells"]["items"]["properties"]["credential_binding"]
    encoded = json.dumps(credential, sort_keys=True)

    assert "protected_service_file" not in encoded
    assert "KIRO_SERVICE_CREDENTIAL_FILE" not in encoded
    assert "KIRO_API_KEY" in encoded
    assert "source_path" not in encoded
    assert "source_sha256" not in encoded
    assert "descriptor_path" not in encoded

