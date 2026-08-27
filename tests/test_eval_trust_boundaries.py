from __future__ import annotations

import base64
import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from core_prompts_eval.attestations import (
    AttestationError,
    signature_message,
    validate_adapter_conformance,
    validate_candidate_submission,
    validate_global_token_ledger,
    validate_signed_attestation,
    validate_trust_store,
)
from core_prompts_eval.contracts import ContractError, artifact_hash
from core_prompts_eval.provenance import (
    ProvenanceError,
    derive_evidence_grade,
    redact_public_record,
    validate_candidate_blind_paths,
    validate_cell_provenance,
)
from core_prompts_eval.qualification import QualificationError, qualify_judge
from core_prompts_eval.verdict import (
    VerdictError,
    validate_adapter_conformance_bindings,
    validate_signed_promotion_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
NOW = dt.datetime(2026, 8, 27, 16, 0, tzinfo=dt.timezone.utc)
JUDGE_BINDINGS = {
    "judge_model_sha256": "6" * 64,
    "judge_prompt_sha256": "7" * 64,
    "judge_rubric_sha256": "8" * 64,
    "judge_tool_policy_sha256": "9" * 64,
    "judge_preregistration_sha256": "a" * 64,
    "gold_set_commitment_sha256": "b" * 64,
}


@pytest.fixture()
def signing_material() -> tuple[Ed25519PrivateKey, dict[str, object]]:
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    purposes = (
            "adapter_conformance",
            "sealed_bundle",
            "judge_qualification",
            "execution_receipt",
            "global_token_ledger",
            "promotion_verdict",
    )
    trust_store = {
        "schema_version": "ProtectedTrustStore.v1",
        "keys": [
            {
                "schema_version": "ProtectedTrustRoot.v1",
                "key_id": f"test-{purpose}",
                "algorithm": "Ed25519",
                "public_key_base64": base64.b64encode(public).decode("ascii"),
                "purposes": [purpose],
                "not_before": "2026-08-01T00:00:00Z",
                "expires_at": "2026-09-30T00:00:00Z",
                "revoked_at": None,
            }
            for purpose in purposes
        ],
    }
    return private, trust_store


def _signed(
    private: Ed25519PrivateKey,
    payload: dict[str, object],
    *,
    purpose: str,
    key_id: str | None = None,
) -> dict[str, object]:
    unsigned = dict(payload)
    payload_sha256 = artifact_hash(unsigned)
    signature = private.sign(signature_message(unsigned))
    return {
        **unsigned,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": key_id or f"test-{purpose}",
            "purpose": purpose,
            "signed_at": "2026-08-27T15:59:00Z",
            "payload_sha256": payload_sha256,
            "value_base64": base64.b64encode(signature).decode("ascii"),
        },
    }


def _receipt_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "ExecutionReceipt.v1",
        "receipt_id": "receipt-1",
        "issuer": "protected-evaluator",
        "run_id": "run-1",
        "runner_identity": "protected-runner-primary",
        "randomization_seed": 314159,
        "cell_id": "critical-codex",
        "trial_id": "trial-opaque-1",
        "repetition": 1,
        "planned_repetitions": 3,
        "order_index": 0,
        "host": "codex",
        "adapter_id": "codex-cli",
        "adapter_version": "1.0.0",
        "adapter_sha256": "b" * 64,
        "resolved_model_identifier": "gpt-5.6-sol-2026-08-01",
        "model_version": "2026-08-01",
        "effort": "high",
        "cli_version": "1.2.3",
        "cli_sha256": "c" * 64,
        "tool_policy_sha256": "a" * 64,
        "approval_policy_sha256": "1" * 64,
        "credential_descriptor_sha256": "9" * 64,
        "candidate_sha256": "d" * 64,
        "dataset_sha256": "e" * 64,
        "input_sha256": "2" * 64,
        "output_sha256": "3" * 64,
        "raw_trace_sha256": "4" * 64,
        "result": "PASS",
        "trace_commitment_sha256": "f" * 64,
        "trace_complete": True,
        "token_usage": {"raw": 100, "cached": 20, "billed": 80, "reserved": 120},
        "attempts": 1,
        "latency_ms": 15_000,
        "started_at": "2026-08-27T15:00:00Z",
        "completed_at": "2026-08-27T15:10:00Z",
        "expires_at": "2026-09-27T15:10:00Z",
        "derived_evidence_grade": "A",
    }
    payload.update(updates)
    return payload


def test_new_attestation_schemas_are_closed() -> None:
    fixtures = {
        "candidate-submission.schema.json": {
            "schema_version": "CandidateSubmission.v1",
            "submission_id": "submission-1",
            "slug": "batman",
            "baseline_sha256": "a" * 64,
            "candidate_sha256": "b" * 64,
            "goal_contract_sha256": "c" * 64,
            "topology_sha256": "d" * 64,
            "evaluation_policy_sha256": "e" * 64,
            "submitted_at": "2026-08-27T15:00:00Z",
            "expires_at": "2026-08-28T15:00:00Z",
        },
        "sealed-bundle-attestation.schema.json": {
            "schema_version": "SealedBundleAttestation.v1",
            "bundle_id": "sealed-1",
            "bundle_sha256": "a" * 64,
            "dataset_sha256": "b" * 64,
            "scorer_sha256": "c" * 64,
            "case_count": 40,
            "critical_case_count": 10,
            "candidate_visible": False,
            "storage_class": "protected",
            "created_at": "2026-08-27T15:00:00Z",
            "expires_at": "2026-09-27T15:00:00Z",
        },
        "judge-qualification.schema.json": {
            "schema_version": "JudgeQualification.v1",
            "qualification_id": "judge-q-1",
            "judge_id": "judge-1",
            **JUDGE_BINDINGS,
            "metrics": {
                "binary_agreement": 0.9,
                "krippendorff_alpha": 0.8,
                "critical_exact": True,
                "mirrored_bias_delta": 0.0,
                "label_bias_delta": 0.01,
                "verbosity_bias_delta": 0.02,
                "expected_samples": 20,
                "observed_samples": 20,
            },
            "qualified": True,
            "created_at": "2026-08-27T15:00:00Z",
            "expires_at": "2026-09-27T15:00:00Z",
        },
        "execution-receipt.schema.json": _receipt_payload(),
    }
    signature = {
        "algorithm": "Ed25519",
        "key_id": "test-evaluator-2026",
        "purpose": "execution_receipt",
        "signed_at": "2026-08-27T15:59:00Z",
        "payload_sha256": "0" * 64,
        "value_base64": base64.b64encode(b"x" * 64).decode("ascii"),
    }

    for filename, payload in fixtures.items():
        schema = json.loads((ROOT / "evals" / "schemas" / filename).read_text(encoding="utf-8"))
        purpose = {
            "candidate-submission.schema.json": "candidate_submission",
            "sealed-bundle-attestation.schema.json": "sealed_bundle",
            "judge-qualification.schema.json": "judge_qualification",
            "execution-receipt.schema.json": "execution_receipt",
        }[filename]
        valid = {**payload, "signature": {**signature, "purpose": purpose}}
        jsonschema.validate(valid, schema)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate({**valid, "unexpected": True}, schema)


def test_protected_trust_store_schema_and_semantics_are_closed(
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    _private, store = signing_material
    schema = json.loads(
        (ROOT / "evals" / "schemas" / "protected-trust-store.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(store, schema)
    validated = validate_trust_store(store)
    assert len(validated["keys"]) == 6
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**store, "unexpected": True}, schema)

    duplicate = {**store, "keys": [*store["keys"], dict(store["keys"][0])]}
    with pytest.raises(AttestationError, match="duplicate"):
        validate_trust_store(duplicate)

    multi = {
        **store,
        "keys": [
            {**store["keys"][0], "purposes": ["execution_receipt", "promotion_verdict"]},
            *store["keys"][1:],
        ],
    }
    with pytest.raises(AttestationError, match="exactly one purpose"):
        validate_trust_store(multi)

def test_candidate_submission_uses_a_separate_single_purpose_root(
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, store = signing_material
    public_key = store["keys"][0]["public_key_base64"]
    candidate_root = {
        "schema_version": "ProtectedTrustRoot.v1",
        "key_id": "test-candidate-submission",
        "algorithm": "Ed25519",
        "public_key_base64": public_key,
        "purposes": ["candidate_submission"],
        "not_before": "2026-08-01T00:00:00Z",
        "expires_at": "2026-09-30T00:00:00Z",
        "revoked_at": None,
    }
    submission = _signed(
        private,
        {
            "schema_version": "CandidateSubmission.v1",
            "submission_id": "submission-1",
            "slug": "batman",
            "baseline_sha256": "a" * 64,
            "candidate_sha256": "b" * 64,
            "goal_contract_sha256": "c" * 64,
            "topology_sha256": "d" * 64,
            "evaluation_policy_sha256": "e" * 64,
            "submitted_at": "2026-08-27T15:00:00Z",
            "expires_at": "2026-08-28T15:00:00Z",
        },
        purpose="candidate_submission",
        key_id="test-candidate-submission",
    )
    assert validate_candidate_submission(submission, trust_root=candidate_root, now=NOW)["submission_id"] == "submission-1"
    with pytest.raises(AttestationError, match="unknown purpose"):
        validate_trust_store({"schema_version": "ProtectedTrustStore.v1", "keys": [candidate_root]})


def _adapter_conformance_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "AdapterConformance.v1",
        "conformance_id": "adapter-codex-1",
        "issuer": "protected-evaluator",
        "adapter_id": "codex-cli",
        "adapter_version": "1.0.0",
        "adapter_sha256": "a" * 64,
        "cli_version": "1.2.3",
        "cli_sha256": "b" * 64,
        "cell_id": "codex-anchor",
        "host": "codex",
        "resolved_model_identifier": "gpt-5.6-sol-2026-08-01",
        "model_version": "2026-08-01",
        "effort": "high",
        "tool_policy_sha256": "c" * 64,
        "approval_policy_sha256": "d" * 64,
        "credential_descriptor_sha256": "9" * 64,
        "authentication_verified": True,
        "response_model_resolved": True,
        "usage_complete": True,
        "retry_semantics_verified": True,
        "tool_semantics_verified": True,
        "session_isolation_verified": True,
        "authorship_boundary_verified": True,
        "fixture_receipt_sha256s": ["e" * 64],
        "probe_receipt_sha256s": ["f" * 64],
        "qualified": True,
        "created_at": "2026-08-27T15:00:00Z",
        "expires_at": "2026-09-27T15:00:00Z",
    }
    payload.update(updates)
    return payload


def test_adapter_conformance_schema_is_closed_and_requires_all_checks() -> None:
    schema = json.loads(
        (ROOT / "evals" / "schemas" / "adapter-conformance.schema.json").read_text(encoding="utf-8")
    )
    signature = {
        "algorithm": "Ed25519",
        "key_id": "test-evaluator-2026",
        "purpose": "adapter_conformance",
        "signed_at": "2026-08-27T15:59:00Z",
        "payload_sha256": "0" * 64,
        "value_base64": base64.b64encode(b"x" * 64).decode("ascii"),
    }
    payload = {**_adapter_conformance_payload(), "signature": signature}
    jsonschema.validate(payload, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**payload, "unexpected": True}, schema)


def test_signed_adapter_conformance_fails_closed_on_any_unqualified_check(
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    signed = _signed(private, _adapter_conformance_payload(), purpose="adapter_conformance")
    verified = validate_adapter_conformance(signed, trust_root=trust_root, now=NOW)
    assert verified["qualified"] is True

    for field in (
        "response_model_resolved",
        "usage_complete",
        "retry_semantics_verified",
        "tool_semantics_verified",
        "session_isolation_verified",
        "authorship_boundary_verified",
        "authentication_verified",
        "qualified",
    ):
        failing = _signed(
            private,
            _adapter_conformance_payload(**{field: False}),
            purpose="adapter_conformance",
        )
        with pytest.raises(AttestationError, match="adapter conformance"):
            validate_adapter_conformance(failing, trust_root=trust_root, now=NOW)

    unresolved = _signed(
        private,
        _adapter_conformance_payload(resolved_model_identifier="default"),
        purpose="adapter_conformance",
    )
    with pytest.raises(AttestationError, match="resolved model"):
        validate_adapter_conformance(unresolved, trust_root=trust_root, now=NOW)


def test_adapter_conformance_binding_rejects_stale_execution_receipt(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    certificate = _signed(
        private, _adapter_conformance_payload(), purpose="adapter_conformance"
    )
    path = _write_json(tmp_path, "adapter.json", certificate)
    binding = {
        "adapter_id": "codex-cli",
        "version": "1.0.0",
        "path": "adapter.json",
        "sha256": artifact_hash(path),
    }
    receipt = _receipt_payload(
        cell_id="codex-anchor",
        resolved_model_identifier="different-model",
    )
    with pytest.raises(VerdictError, match="stale receipt bindings"):
        validate_adapter_conformance_bindings(
            [binding],
            trust_root=trust_root,
            repo_root=tmp_path,
            receipts=[receipt],
            now=NOW,
        )


def _token_ledger_payload(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "GlobalTokenLedger.v1",
        "ledger_id": "batman-promotion-ledger",
        "issuer": "protected-evaluator",
        "experiment_id": "batman-subagent-controller-promotion",
        "profile": "promotion",
        "token_cap": 5_000_000,
        "sequence": 2,
        "previous_ledger_sha256": "a" * 64,
        "entries": [
            {
                "entry_id": "primary-1",
                "phase": "primary",
                "run_id": "run-primary",
                "receipt_sha256s": ["b" * 64],
                "reserved": 1_000,
                "raw": 800,
                "cached": 100,
                "billed": 700,
                "recorded_at": "2026-08-27T15:10:00Z",
            },
            {
                "entry_id": "reproduction-1",
                "phase": "reproduction",
                "run_id": "run-reproduction",
                "receipt_sha256s": ["c" * 64],
                "reserved": 500,
                "raw": 400,
                "cached": 50,
                "billed": 350,
                "recorded_at": "2026-08-27T15:30:00Z",
            },
        ],
        "totals": {"reserved": 1_500, "raw": 1_200, "cached": 150, "billed": 1_050},
        "remaining_raw_tokens": 4_998_800,
        "status": "open",
        "created_at": "2026-08-27T15:00:00Z",
        "updated_at": "2026-08-27T15:30:00Z",
        "expires_at": "2026-08-28T15:30:00Z",
    }
    payload.update(updates)
    return payload


def test_global_token_ledger_is_closed_signed_cumulative_and_chained(
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_store = signing_material
    schema = json.loads(
        (ROOT / "evals" / "schemas" / "global-token-ledger.schema.json").read_text(encoding="utf-8")
    )
    signed = _signed(private, _token_ledger_payload(), purpose="global_token_ledger")
    jsonschema.validate(signed, schema)
    verified = validate_global_token_ledger(
        signed,
        trust_root=trust_store,
        expected_previous_sha256="a" * 64,
        now=NOW,
    )
    assert verified["remaining_raw_tokens"] == 4_998_800

    bad_totals = _signed(
        private,
        _token_ledger_payload(totals={"reserved": 1_500, "raw": 1_199, "cached": 150, "billed": 1_050}),
        purpose="global_token_ledger",
    )
    with pytest.raises(AttestationError, match="totals"):
        validate_global_token_ledger(bad_totals, trust_root=trust_store, now=NOW)

    with pytest.raises(AttestationError, match="previous ledger"):
        validate_global_token_ledger(
            signed,
            trust_root=trust_store,
            expected_previous_sha256="f" * 64,
            now=NOW,
        )

    entries = _token_ledger_payload()["entries"]
    duplicate_receipt = _signed(
        private,
        _token_ledger_payload(
            entries=[entries[0], {**entries[1], "receipt_sha256s": entries[0]["receipt_sha256s"]}]
        ),
        purpose="global_token_ledger",
    )
    with pytest.raises(AttestationError, match="more than one entry"):
        validate_global_token_ledger(duplicate_receipt, trust_root=trust_store, now=NOW)


def test_signature_verification_is_exact_and_bound_to_purpose(
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    signed = _signed(private, _receipt_payload(), purpose="execution_receipt")

    verified = validate_signed_attestation(signed, trust_root=trust_root, now=NOW)
    assert verified["receipt_id"] == "receipt-1"

    tampered = {**signed, "result": "FAIL"}
    with pytest.raises(AttestationError, match="payload hash"):
        validate_signed_attestation(tampered, trust_root=trust_root, now=NOW)

    wrong_purpose = {**signed, "signature": {**signed["signature"], "purpose": "promotion_verdict"}}
    with pytest.raises(AttestationError, match="purpose"):
        validate_signed_attestation(
            wrong_purpose,
            trust_root=trust_root,
            expected_purpose="execution_receipt",
            now=NOW,
        )

    unknown_key = {**signed, "signature": {**signed["signature"], "key_id": "unknown-key"}}
    with pytest.raises(AttestationError, match="key_id and purpose"):
        validate_signed_attestation(unknown_key, trust_root=trust_root, now=NOW)


@pytest.mark.parametrize(
    ("root_update", "now", "message"),
    [
        ({"revoked_at": "2026-08-20T00:00:00Z"}, NOW, "revoked"),
        ({"expires_at": "2026-08-26T00:00:00Z"}, NOW, "expired"),
        ({"not_before": "2026-08-28T00:00:00Z"}, NOW, "not yet valid"),
    ],
)
def test_trust_root_time_and_revocation_checks_fail_closed(
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
    root_update: dict[str, object],
    now: dt.datetime,
    message: str,
) -> None:
    private, trust_root = signing_material
    signed = _signed(private, _receipt_payload(), purpose="execution_receipt")
    updated_store = {
        **trust_root,
        "keys": [
            {**root, **root_update} if root["purposes"] == ["execution_receipt"] else root
            for root in trust_root["keys"]
        ],
    }
    with pytest.raises(AttestationError, match=message):
        validate_signed_attestation(signed, trust_root=updated_store, now=now)


def test_signature_from_the_future_is_rejected(
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    signed = _signed(private, _receipt_payload(), purpose="execution_receipt")
    signed["signature"] = {**signed["signature"], "signed_at": "2026-08-27T16:06:00Z"}
    with pytest.raises(AttestationError, match="future"):
        validate_signed_attestation(signed, trust_root=trust_root, now=NOW)


def test_candidate_blind_path_validation_rejects_repo_roots_and_symlinks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = tmp_path / "candidate-readable"
    candidate.mkdir()
    protected = tmp_path / "protected"
    protected.mkdir()
    bundle = protected / "bundle.jsonl"
    bundle.write_text("sealed\n", encoding="utf-8")

    validate_candidate_blind_paths(
        sealed_paths=[bundle],
        repo_root=repo,
        candidate_readable_roots=[candidate],
    )

    inside = repo / "sealed.jsonl"
    inside.write_text("bad\n", encoding="utf-8")
    with pytest.raises(ProvenanceError, match="repository"):
        validate_candidate_blind_paths(
            sealed_paths=[inside], repo_root=repo, candidate_readable_roots=[candidate]
        )

    link = tmp_path / "sealed-link.jsonl"
    link.symlink_to(bundle)
    with pytest.raises(ProvenanceError, match="symlink"):
        validate_candidate_blind_paths(
            sealed_paths=[link], repo_root=repo, candidate_readable_roots=[candidate]
        )


def test_public_redaction_removes_case_material_and_secret_values() -> None:
    record = {
        "run_id": "run-1",
        "case_id": "secret-case-17",
        "nested": {
            "body": "hidden prompt",
            "label": "FAIL",
            "seed": 8871,
            "raw_trace": ["secret-case-17", "hidden prompt"],
            "aggregate": 0.9,
        },
    }
    redacted = redact_public_record(record, secrets=["secret-case-17", "hidden prompt", "FAIL", "8871"])
    encoded = json.dumps(redacted, sort_keys=True)

    assert redacted == {"run_id": "run-1", "nested": {"aggregate": 0.9}}
    assert all(secret not in encoded for secret in ("secret-case-17", "hidden prompt", "FAIL", "8871"))


def test_judge_qualification_enforces_all_thresholds_and_binding() -> None:
    metrics = {
        "binary_agreement": 0.80,
        "krippendorff_alpha": 0.70,
        "critical_exact": True,
        "mirrored_bias_delta": 0.05,
        "label_bias_delta": 0.05,
        "verbosity_bias_delta": 0.05,
        "expected_samples": 20,
        "observed_samples": 20,
    }
    result = qualify_judge(
        metrics,
        **JUDGE_BINDINGS,
    )
    assert result["qualified"] is True

    for field, bad in (
        ("binary_agreement", 0.79),
        ("krippendorff_alpha", 0.69),
        ("critical_exact", False),
        ("mirrored_bias_delta", 0.051),
        ("label_bias_delta", 0.051),
        ("verbosity_bias_delta", 0.051),
        ("observed_samples", 19),
    ):
        with pytest.raises(QualificationError):
            qualify_judge(
                {**metrics, field: bad},
                **JUDGE_BINDINGS,
            )

    with pytest.raises(QualificationError, match="binding"):
        qualify_judge(metrics, **{**JUDGE_BINDINGS, "judge_model_sha256": "not-a-hash"})


def test_receipt_derived_provenance_and_critical_grade_requirement() -> None:
    receipt = _receipt_payload()
    assert derive_evidence_grade(receipt, signature_verified=True) == "A"
    assert derive_evidence_grade(
        {**receipt, "trace_complete": False, "derived_evidence_grade": "B"},
        signature_verified=True,
    ) == "B"
    assert derive_evidence_grade(receipt, signature_verified=False) == "C"
    assert derive_evidence_grade({**receipt, "result": "NOT_RUN"}, signature_verified=True) == "NOT_RUN"

    validate_cell_provenance(receipt, signature_verified=True, critical=True)
    with pytest.raises(ProvenanceError, match="Grade A"):
        validate_cell_provenance(
            {**receipt, "trace_complete": False, "derived_evidence_grade": "B"},
            signature_verified=True,
            critical=True,
        )


def _write_json(root: Path, relative: str, payload: object) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _promotion_evidence(
    repo: Path,
    private: Ed25519PrivateKey,
    trust_root: dict[str, object],
) -> dict[str, object]:
    baseline_revision = "1" * 40
    candidate_revision = "2" * 40
    baseline_sha256 = "a" * 64
    candidate_sha256 = "b" * 64
    dataset_sha256 = "c" * 64
    scorer_sha256 = "d" * 64
    primary_runner_name = "protected-runner-primary"
    reproduction_runner_name = "protected-reproduction-b"
    primary_runner_identity = artifact_hash(primary_runner_name)
    reproduction_runner_identity = artifact_hash(reproduction_runner_name)
    trust_root_path = _write_json(repo, "trust-root.json", trust_root)
    approved_policy = _write_json(
        repo,
        "evals/approved-trust-policy.json",
        {
            "schema_version": "ApprovedTrustPolicy.v1",
            "policy_id": "batman-protected-evaluator-2026",
            "status": "approved",
            "trust_store_sha256": artifact_hash(trust_root_path),
            "authorized_keys": [
                {"purpose": root["purposes"][0], "key_id": root["key_id"]}
                for root in trust_root["keys"]
            ],
            "approved_at": "2026-08-20T00:00:00Z",
            "expires_at": "2026-09-30T00:00:00Z",
        },
    )
    if not (repo / ".git").exists():
        subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "evals/approved-trust-policy.json"], cwd=repo, check=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo, check=False)
    if staged.returncode != 0:
        subprocess.run(["git", "commit", "-m", "approve evaluator trust policy"], cwd=repo, check=True, capture_output=True)
    approved_policy_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    baseline_revision = approved_policy_revision
    goal = _write_json(
        repo,
        "evals/contracts/batman.json",
        {
            "schema_version": "GoalContract.v1",
            "slug": "batman",
            "target": "deliver",
            "intended_outcome": "verified delivery",
            "change_class": "authority",
            "non_goals": [],
            "protected_behaviors": [],
            "editable_behavior": [],
            "primary_outcome": {},
            "secondary_outcomes": [],
            "regression_limits": {},
            "cost_latency_limits": {},
            "runtime_envelope": {},
            "promotion_rule": "all gates",
            "rollback_trigger": "regression",
            "source_clause_hashes": [],
            "review_status": "human_reviewed",
        },
    )
    topology = _write_json(
        repo,
        "evals/topologies/batman.json",
        {
            "schema_version": "CapabilityTopology.v1",
            "slug": "batman",
            "ssot_sha256": candidate_sha256,
            "nodes": {},
            "composition": {},
            "state_machine": {},
            "outputs": [],
            "authority_boundaries": [],
            "resources": [],
            "handoffs": [],
            "review_status": "human_reviewed",
            "known_ambiguities": [],
            "normative_clause_coverage": {"total": 1, "mapped": 1, "waived": 0},
            "protected_invariants": [{"mapped_to": ["BAT-1"]}],
            "risk_tiers": {},
            "source_references": [],
            "coverage_policy": {},
        },
    )
    policy = _write_json(repo, "evaluation-policy.json", {"schema_version": "EvaluationPolicy.v1"})
    impact = _write_json(repo, "impact-plan.json", {"schema_version": "EvalImpactPlan.v1"})
    evaluator = repo / "evaluator.py"
    evaluator.write_text("# evaluator v1\n", encoding="utf-8")
    preregistration = _write_json(
        repo,
        "evidence/preregistered-plan.json",
        {
            "schema_version": "CapabilityPreregistration.v1",
            "status": "preregistered_not_run",
            "stopping_rule": {"complete_all_preregistered_trials_for_promotion": True},
        },
    )
    score_report = _write_json(
        repo,
        "evidence/score-report.json",
        {
            "schema_version": "ProtectedScoreReport.v1",
            "run_id": "run-1",
            "candidate_sha256": candidate_sha256,
            "dataset_sha256": dataset_sha256,
            "scorer_sha256": scorer_sha256,
            "scoring_status": "completed",
            "mutation_summary": {
                "critical_total": 10,
                "critical_killed": 10,
                "overall_total": 20,
                "overall_killed": 19,
            },
            "protected_regression_count": 0,
        },
    )

    sealed = _signed(
        private,
        {
            "schema_version": "SealedBundleAttestation.v1",
            "bundle_id": "sealed-1",
            "bundle_sha256": "e" * 64,
            "dataset_sha256": dataset_sha256,
            "scorer_sha256": scorer_sha256,
            "case_count": 40,
            "critical_case_count": 10,
            "candidate_visible": False,
            "storage_class": "protected",
            "created_at": "2026-08-27T15:00:00Z",
            "expires_at": "2026-09-27T15:00:00Z",
        },
        purpose="sealed_bundle",
    )
    sealed_path = _write_json(repo, "evidence/sealed-attestation.json", sealed)

    metrics = {
        "binary_agreement": 0.9,
        "krippendorff_alpha": 0.8,
        "critical_exact": True,
        "mirrored_bias_delta": 0.01,
        "label_bias_delta": 0.01,
        "verbosity_bias_delta": 0.01,
        "expected_samples": 20,
        "observed_samples": 20,
    }
    qualification = _signed(
        private,
        {
            "schema_version": "JudgeQualification.v1",
            "qualification_id": "judge-q-1",
            "judge_id": "judge-1",
            **JUDGE_BINDINGS,
            "metrics": metrics,
            "qualified": True,
            "created_at": "2026-08-27T15:00:00Z",
            "expires_at": "2026-09-27T15:00:00Z",
        },
        purpose="judge_qualification",
    )
    qualification_path = _write_json(repo, "evidence/judge-q.json", qualification)

    receipt_payload = _receipt_payload(
        candidate_sha256=candidate_sha256,
        dataset_sha256=dataset_sha256,
    )
    adapter_certificate = _signed(
        private,
        _adapter_conformance_payload(
            cell_id=receipt_payload["cell_id"],
            host=receipt_payload["host"],
            adapter_id=receipt_payload["adapter_id"],
            adapter_version=receipt_payload["adapter_version"],
            adapter_sha256=receipt_payload["adapter_sha256"],
            cli_version=receipt_payload["cli_version"],
            cli_sha256=receipt_payload["cli_sha256"],
            resolved_model_identifier=receipt_payload["resolved_model_identifier"],
            model_version=receipt_payload["model_version"],
            effort=receipt_payload["effort"],
            tool_policy_sha256=receipt_payload["tool_policy_sha256"],
            approval_policy_sha256=receipt_payload["approval_policy_sha256"],
        ),
        purpose="adapter_conformance",
    )
    adapter_certificate_path = _write_json(
        repo, "evidence/adapter-conformance.json", adapter_certificate
    )
    reproduction_adapter_certificate = _signed(
        private,
        _adapter_conformance_payload(
            conformance_id="adapter-codex-reproduction",
            cell_id=receipt_payload["cell_id"],
            host=receipt_payload["host"],
            adapter_id=receipt_payload["adapter_id"],
            adapter_version=receipt_payload["adapter_version"],
            adapter_sha256=receipt_payload["adapter_sha256"],
            cli_version=receipt_payload["cli_version"],
            cli_sha256=receipt_payload["cli_sha256"],
            resolved_model_identifier=receipt_payload["resolved_model_identifier"],
            model_version=receipt_payload["model_version"],
            effort=receipt_payload["effort"],
            tool_policy_sha256=receipt_payload["tool_policy_sha256"],
            approval_policy_sha256=receipt_payload["approval_policy_sha256"],
            credential_descriptor_sha256=reproduction_runner_identity,
        ),
        purpose="adapter_conformance",
    )
    reproduction_adapter_certificate_path = _write_json(
        repo, "evidence/reproduction-adapter-conformance.json", reproduction_adapter_certificate
    )
    receipt = _signed(private, receipt_payload, purpose="execution_receipt")
    receipt_path = _write_json(repo, "evidence/receipt.json", receipt)
    reproduction_receipt = _signed(
        private,
        {
            **receipt_payload,
            "receipt_id": "receipt-reproduction",
            "run_id": "run-reproduction",
            "runner_identity": reproduction_runner_name,
            "randomization_seed": 9913,
            "credential_descriptor_sha256": reproduction_runner_identity,
            "output_sha256": "5" * 64,
            "raw_trace_sha256": "6" * 64,
            "trace_commitment_sha256": "7" * 64,
        },
        purpose="execution_receipt",
    )
    reproduction_receipt_path = _write_json(repo, "evidence/reproduction-receipt.json", reproduction_receipt)

    run_manifest = {
        "schema_version": "EvalRunManifest.v1",
        "run_id": "run-1",
        "baseline_revision": baseline_revision,
        "candidate_revision": candidate_revision,
        "baseline_sha256": baseline_sha256,
        "candidate_sha256": candidate_sha256,
        "dataset_sha256": dataset_sha256,
        "scorer_sha256": scorer_sha256,
        "goal_contract_sha256": artifact_hash(goal),
        "topology_sha256": artifact_hash(topology),
        "evaluation_policy_sha256": artifact_hash(policy),
        "impact_plan_sha256": artifact_hash(impact),
        "evaluator_package_sha256": artifact_hash(evaluator),
        "trust_root_sha256": artifact_hash(trust_root_path),
        "raw_trace_hashes": [receipt_payload["raw_trace_sha256"]],
        "run_plan_sha256": artifact_hash(preregistration),
        "stopping_rule": {"complete_all_preregistered_trials_for_promotion": True},
        "planned_repetitions": 1,
        "completed_repetitions": 1,
        "seed": 314159,
    }
    run_manifest_path = _write_json(repo, "evidence/run-manifest.json", run_manifest)
    reproduction_manifest = {
        **run_manifest,
        "run_id": "run-reproduction",
        "seed": 9913,
        "raw_trace_hashes": ["6" * 64],
    }
    reproduction_manifest_path = _write_json(
        repo, "evidence/reproduction-manifest.json", reproduction_manifest
    )
    conformance_usage = _write_json(
        repo,
        "evidence/conformance-token-usage.json",
        {
            "schema_version": "ProtectedTokenUsage.v1",
            "raw": 10,
            "cached": 2,
            "billed": 8,
            "receipt_sha256s": ["0" * 64],
        },
    )
    adjudication_usage = _write_json(
        repo,
        "evidence/adjudication-token-usage.json",
        {
            "schema_version": "ProtectedTokenUsage.v1",
            "raw": 10,
            "cached": 2,
            "billed": 8,
            "receipt_sha256s": ["1" * 64],
        },
    )
    token_ledger = _signed(
        private,
        {
            "schema_version": "GlobalTokenLedger.v1",
            "ledger_id": "batman-promotion-final",
            "issuer": "protected-evaluator",
            "experiment_id": "batman-subagent-controller-promotion",
            "profile": "promotion",
            "token_cap": 5_000_000,
            "sequence": 0,
            "previous_ledger_sha256": None,
            "entries": [
                {
                    "entry_id": "conformance",
                    "phase": "adapter_conformance",
                    "run_id": "adapter-probes",
                    "receipt_sha256s": ["0" * 64],
                    "reserved": 10,
                    "raw": 10,
                    "cached": 2,
                    "billed": 8,
                    "recorded_at": "2026-08-27T15:05:00Z",
                },
                {
                    "entry_id": "primary",
                    "phase": "primary",
                    "run_id": "run-1",
                    "receipt_sha256s": [artifact_hash(receipt_path)],
                    "reserved": 120,
                    "raw": 100,
                    "cached": 20,
                    "billed": 80,
                    "recorded_at": "2026-08-27T15:10:00Z",
                },
                {
                    "entry_id": "reproduction",
                    "phase": "reproduction",
                    "run_id": "run-reproduction",
                    "receipt_sha256s": [artifact_hash(reproduction_receipt_path)],
                    "reserved": 120,
                    "raw": 100,
                    "cached": 20,
                    "billed": 80,
                    "recorded_at": "2026-08-27T15:40:00Z",
                },
                {
                    "entry_id": "judge",
                    "phase": "adjudication",
                    "run_id": "judge-run-1",
                    "receipt_sha256s": ["1" * 64],
                    "reserved": 10,
                    "raw": 10,
                    "cached": 2,
                    "billed": 8,
                    "recorded_at": "2026-08-27T15:50:00Z",
                },
            ],
            "totals": {"reserved": 260, "raw": 220, "cached": 44, "billed": 176},
            "remaining_raw_tokens": 4_999_780,
            "status": "final",
            "created_at": "2026-08-27T15:00:00Z",
            "updated_at": "2026-08-27T15:40:00Z",
            "expires_at": "2026-08-28T15:40:00Z",
        },
        purpose="global_token_ledger",
    )
    token_ledger_path = _write_json(repo, "evidence/token-ledger.json", token_ledger)

    verdict = {
        "schema_version": "PromotionVerdict.v2",
        "run_id": "run-1",
        "slug": "batman",
        "status": "promote",
        "baseline_sha256": baseline_sha256,
        "candidate_sha256": candidate_sha256,
        "goal_contract_sha256": artifact_hash(goal),
        "topology_sha256": artifact_hash(topology),
        "dataset_sha256": dataset_sha256,
        "scorer_sha256": scorer_sha256,
        "baseline_revision": baseline_revision,
        "candidate_revision": candidate_revision,
        "run_manifest_path": "evidence/run-manifest.json",
        "run_manifest_sha256": artifact_hash(run_manifest_path),
        "sealed_bundle_attestation_binding": {
            "path": "evidence/sealed-attestation.json",
            "sha256": artifact_hash(sealed_path),
        },
        "score_report_binding": {
            "path": "evidence/score-report.json",
            "sha256": artifact_hash(score_report),
        },
        "token_ledger_binding": {
            "path": "evidence/token-ledger.json",
            "sha256": artifact_hash(token_ledger_path),
        },
        "approved_trust_policy_binding": {
            "path": "evals/approved-trust-policy.json",
            "sha256": artifact_hash(approved_policy),
            "revision": approved_policy_revision,
        },
        "primary_runner_identity_sha256": primary_runner_identity,
        "receipt_bindings": [
            {"receipt_id": "receipt-1", "path": "evidence/receipt.json", "sha256": artifact_hash(receipt_path)}
        ],
        "auxiliary_receipt_bindings": [
            {
                "binding_id": "conformance",
                "phase": "adapter_conformance",
                "run_id": "adapter-probes",
                "path": "evidence/conformance-token-usage.json",
                "sha256": artifact_hash(conformance_usage),
            },
            {
                "binding_id": "judge",
                "phase": "adjudication",
                "run_id": "judge-run-1",
                "path": "evidence/adjudication-token-usage.json",
                "sha256": artifact_hash(adjudication_usage),
            },
        ],
        "adapter_bindings": [
            {
                "adapter_id": "codex-cli",
                "version": "1.0.0",
                "phase": "primary",
                "runner_identity_sha256": primary_runner_identity,
                "path": "evidence/adapter-conformance.json",
                "sha256": artifact_hash(adapter_certificate_path),
            },
            {
                "adapter_id": "codex-cli",
                "version": "1.0.0",
                "phase": "reproduction",
                "runner_identity_sha256": reproduction_runner_identity,
                "path": "evidence/reproduction-adapter-conformance.json",
                "sha256": artifact_hash(reproduction_adapter_certificate_path),
            },
        ],
        "judge_qualification_bindings": [
            {"judge_id": "judge-1", "path": "evidence/judge-q.json", "sha256": artifact_hash(qualification_path), **JUDGE_BINDINGS}
        ],
        "reproduction_manifest_bindings": [
            {
                "run_id": "run-reproduction",
                "path": "evidence/reproduction-manifest.json",
                "sha256": artifact_hash(reproduction_manifest_path),
                "seed": 9913,
                "runner_identity_sha256": reproduction_runner_identity,
                "receipt_bindings": [
                    {
                        "receipt_id": "receipt-reproduction",
                        "path": "evidence/reproduction-receipt.json",
                        "sha256": artifact_hash(reproduction_receipt_path),
                    }
                ],
            }
        ],
        "evaluation_policy_path": "evaluation-policy.json",
        "evaluation_policy_sha256": artifact_hash(policy),
        "impact_plan_path": "impact-plan.json",
        "impact_plan_sha256": artifact_hash(impact),
        "evaluator_path": "evaluator.py",
        "evaluator_sha256": artifact_hash(evaluator),
        "trust_root_sha256": artifact_hash(trust_root_path),
        "evaluator_version": "1",
        "profile": "promotion",
        "token_cap": 5_000_000,
        "required_cells": [
            {
                "host": "codex",
                "resolved_model_identifier": "gpt-5.6-sol-2026-08-01",
                "result": "PASS",
                "evidence_grade": "A",
                "critical": True,
                "receipt_ids": ["receipt-1"],
            }
        ],
        "hard_gates": {
            "goal_contract_complete": True,
            "topology_complete": True,
            "no_unresolved_contradiction": True,
            "critical_invariant_coverage_100_percent": True,
            "critical_mutant_kill_100_percent": True,
            "overall_mutant_kill_at_least_95_percent": True,
            "no_protected_regression": True,
            "no_required_not_run_cells": True,
            "qualified_judges_only": True,
            "sealed_bundle_valid": True,
            "preregistered_stopping_rule": True,
            "token_budget_observed": True,
            "independent_reproduction": True,
        },
        "token_usage": {"raw": 220, "cached": 44, "billed": 176},
        "issued_at": "2026-08-27T15:58:00Z",
        "expires_at": "2026-08-28T15:58:00Z",
        "issuer": "protected-evaluator",
    }
    return _signed(private, verdict, purpose="promotion_verdict")


def _approved_policy_args(verdict: dict[str, object]) -> dict[str, str]:
    binding = verdict["approved_trust_policy_binding"]
    assert isinstance(binding, dict)
    return {
        "approved_trust_policy_sha256": str(binding["sha256"]),
        "approved_trust_policy_revision": str(binding["revision"]),
    }


def test_signed_promotion_evidence_closes_the_full_hash_chain(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)

    result = validate_signed_promotion_evidence(
        verdict,
        trust_root=tmp_path / "trust-root.json",
        repo_root=tmp_path,
        now=NOW,
        **_approved_policy_args(verdict),
    )
    assert result["promotion_allowed"] is True
    assert result["evidence_grades"] == {"receipt-1": "A"}


def test_uac_accepts_signed_sealed_attestation_with_distinct_bundle_and_dataset(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)
    sealed = json.loads((tmp_path / "evidence/sealed-attestation.json").read_text(encoding="utf-8"))
    assert sealed["bundle_sha256"] != sealed["dataset_sha256"]
    assert not (tmp_path / "evals/sealed-manifest.json").exists()
    verdict_path = _write_json(tmp_path, "evidence/promotion-verdict.json", verdict)
    spec = importlib.util.spec_from_file_location("uac_import_sealed_e2e", ROOT / "scripts/uac-import.py")
    assert spec and spec.loader
    uac = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(uac)
    original_root = uac.ROOT
    try:
        uac.ROOT = tmp_path
        monkeypatch.setattr(uac, "_safe_apply_ssot_text", lambda *args, **kwargs: ("candidate\n", {}))

        def stop_after_signed_evidence(*args, **kwargs):
            raise ContractError("revision-binding-sentinel")

        monkeypatch.setattr(uac, "_validate_promotion_revision_bindings", stop_after_signed_evidence)
        result = uac._apply_payload(
            {
                "status": "accepted",
                "source": {"normalized_source": str(tmp_path / "candidate.md")},
                "cross_analysis": {"fit_assessment": "fits_cleanly"},
                "manifest": {"slug": "batman"},
            },
            SimpleNamespace(
                promotion_verdict=verdict_path,
                promotion_trust_root=tmp_path / "trust-root.json",
                finalize_existing_candidate=True,
                approved_trust_policy_sha256=verdict["approved_trust_policy_binding"]["sha256"],
                approved_trust_policy_revision=verdict["approved_trust_policy_binding"]["revision"],
                yes=True,
                quality_loop="off",
            ),
            [str(tmp_path / "candidate.md")],
        )
    finally:
        uac.ROOT = original_root

    assert result["status"] == "stale_evidence"
    assert "revision-binding-sentinel" in result["detail"]


def test_reproduction_must_use_distinct_run_seed_and_runner_identity(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)
    reproduction_path = tmp_path / "evidence/reproduction-manifest.json"
    reproduction = json.loads(reproduction_path.read_text(encoding="utf-8"))
    reproduction["seed"] = 314159
    _write_json(tmp_path, "evidence/reproduction-manifest.json", reproduction)
    unsigned = {key: value for key, value in verdict.items() if key != "signature"}
    unsigned["reproduction_manifest_bindings"][0]["seed"] = 314159
    unsigned["reproduction_manifest_bindings"][0]["sha256"] = artifact_hash(reproduction_path)
    verdict = _signed(private, unsigned, purpose="promotion_verdict")

    with pytest.raises(VerdictError, match="runner identity and seed|distinct preregistered seed"):
        validate_signed_promotion_evidence(
            verdict,
            trust_root=tmp_path / "trust-root.json",
            repo_root=tmp_path,
            now=NOW,
            **_approved_policy_args(verdict),
        )


def test_reproduction_must_use_a_distinct_runner_identity(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)
    primary_identity = verdict["primary_runner_identity_sha256"]
    unsigned = {key: value for key, value in verdict.items() if key != "signature"}
    unsigned["reproduction_manifest_bindings"][0]["runner_identity_sha256"] = primary_identity
    verdict = _signed(private, unsigned, purpose="promotion_verdict")

    with pytest.raises(VerdictError, match="distinct runner identity"):
        validate_signed_promotion_evidence(
            verdict,
            trust_root=tmp_path / "trust-root.json",
            repo_root=tmp_path,
            now=NOW,
            **_approved_policy_args(verdict),
        )


def test_reproduction_must_use_a_distinct_full_run_id(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)
    unsigned = {key: value for key, value in verdict.items() if key != "signature"}
    unsigned["reproduction_manifest_bindings"][0]["run_id"] = verdict["run_id"]
    verdict = _signed(private, unsigned, purpose="promotion_verdict")

    with pytest.raises(VerdictError, match="distinct full run IDs"):
        validate_signed_promotion_evidence(
            verdict,
            trust_root=tmp_path / "trust-root.json",
            repo_root=tmp_path,
            now=NOW,
            **_approved_policy_args(verdict),
        )


def test_promotion_token_ledger_must_cover_every_primary_and_reproduction_receipt(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)
    ledger_path = tmp_path / "evidence/token-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    unsigned_ledger = {key: value for key, value in ledger.items() if key != "signature"}
    unsigned_ledger["entries"] = unsigned_ledger["entries"][:1]
    unsigned_ledger["totals"] = {"reserved": 10, "raw": 10, "cached": 2, "billed": 8}
    unsigned_ledger["remaining_raw_tokens"] = 4_999_990
    rebound_ledger = _signed(private, unsigned_ledger, purpose="global_token_ledger")
    _write_json(tmp_path, "evidence/token-ledger.json", rebound_ledger)
    unsigned_verdict = {key: value for key, value in verdict.items() if key != "signature"}
    unsigned_verdict["token_ledger_binding"]["sha256"] = artifact_hash(ledger_path)
    verdict = _signed(private, unsigned_verdict, purpose="promotion_verdict")

    with pytest.raises(VerdictError, match="exact bound receipt set"):
        validate_signed_promotion_evidence(
            verdict,
            trust_root=tmp_path / "trust-root.json",
            repo_root=tmp_path,
            now=NOW,
            **_approved_policy_args(verdict),
        )


def test_promotion_rejects_candidate_selected_trust_policy_without_operator_approval(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)

    with pytest.raises(VerdictError, match="explicit operator approval"):
        validate_signed_promotion_evidence(
            verdict,
            trust_root=tmp_path / "trust-root.json",
            repo_root=tmp_path,
            now=NOW,
            approved_trust_policy_sha256="0" * 64,
            approved_trust_policy_revision="1" * 40,
        )


def test_signed_promotion_evidence_rejects_stale_artifact_and_claimed_grade(
    tmp_path: Path,
    signing_material: tuple[Ed25519PrivateKey, dict[str, object]],
) -> None:
    private, trust_root = signing_material
    verdict = _promotion_evidence(tmp_path, private, trust_root)
    (tmp_path / "impact-plan.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(VerdictError, match="impact_plan_sha256"):
        validate_signed_promotion_evidence(
            verdict,
            trust_root=tmp_path / "trust-root.json",
            repo_root=tmp_path,
            now=NOW,
            **_approved_policy_args(verdict),
        )

    verdict = _promotion_evidence(tmp_path, private, trust_root)
    receipt_path = tmp_path / "evidence" / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    unsigned_receipt = {key: value for key, value in receipt.items() if key != "signature"}
    weakened = _signed(
        private,
        {**unsigned_receipt, "trace_complete": False},
        purpose="execution_receipt",
    )
    _write_json(tmp_path, "evidence/receipt.json", weakened)
    # Rebind the manifest and verdict, preserving the false Grade A claim.
    manifest_path = tmp_path / "evidence" / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["raw_trace_hashes"] = [unsigned_receipt["raw_trace_sha256"]]
    _write_json(tmp_path, "evidence/run-manifest.json", manifest)
    unsigned_verdict = {key: value for key, value in verdict.items() if key != "signature"}
    unsigned_verdict["run_manifest_sha256"] = artifact_hash(manifest_path)
    unsigned_verdict["receipt_bindings"] = [
        {"receipt_id": "receipt-1", "path": "evidence/receipt.json", "sha256": artifact_hash(receipt_path)}
    ]
    verdict = _signed(private, unsigned_verdict, purpose="promotion_verdict")
    with pytest.raises((VerdictError, ProvenanceError), match="Grade A|evidence grade"):
        validate_signed_promotion_evidence(
            verdict,
            trust_root=tmp_path / "trust-root.json",
            repo_root=tmp_path,
            now=NOW,
            **_approved_policy_args(verdict),
        )


def test_protected_evaluator_template_is_secret_free_and_scripts_compile() -> None:
    template = ROOT / "tooling" / "protected-evaluator"
    required = (
        "README.md",
        "gitlab-ci.template.yml",
        "config/protected-evaluator.example.json",
        "scripts/generate_signing_key.py",
        "scripts/sign_artifact.py",
        "scripts/validate_submission.py",
    )
    for relative in required:
        path = template / relative
        assert path.is_file(), relative
        if path.suffix == ".py":
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
    tracked_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in template.rglob("*")
        if path.is_file() and path.suffix in {".md", ".json", ".py", ".yml"}
    )
    assert "BEGIN PRIVATE KEY" not in tracked_text
    assert '"case_id"' not in tracked_text
    assert '"seed"' not in tracked_text


def test_protected_key_generation_writes_private_material_only_to_restricted_file(tmp_path: Path) -> None:
    script = ROOT / "tooling" / "protected-evaluator" / "scripts" / "generate_signing_key.py"
    private_path = tmp_path / "signing.key"
    trust_path = tmp_path / "trust-root.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--private-key-out",
            str(private_path),
            "--trust-root-out",
            str(trust_path),
            "--key-id",
            "test-protected-key",
            "--purpose",
            "promotion_verdict",
            "--not-before",
            "2026-08-27T00:00:00Z",
            "--expires-at",
            "2026-09-27T00:00:00Z",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert private_path.is_file() and trust_path.is_file()
    assert os.stat(private_path).st_mode & 0o077 == 0
    trust = json.loads(trust_path.read_text(encoding="utf-8"))
    assert trust["schema_version"] == "ProtectedTrustRoot.v1"
    assert "private" not in json.dumps(trust).lower()
