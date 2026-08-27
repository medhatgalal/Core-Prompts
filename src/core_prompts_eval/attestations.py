from __future__ import annotations

import base64
import binascii
import datetime as dt
import hashlib
import re
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .contracts import artifact_hash, canonical_json


SHA256_RE = re.compile(r"[0-9a-f]{64}")
SIGNATURE_DOMAIN = b"Core-Prompts-Attestation-v1\x00"
SCHEMA_PURPOSES = {
    "CandidateSubmission.v1": "candidate_submission",
    "SealedBundleAttestation.v1": "sealed_bundle",
    "JudgeQualification.v1": "judge_qualification",
    "ExecutionReceipt.v1": "execution_receipt",
    "PromotionVerdict.v1": "promotion_verdict",
    "PromotionVerdict.v2": "promotion_verdict",
    "AdapterConformance.v1": "adapter_conformance",
    "GlobalTokenLedger.v1": "global_token_ledger",
}
TRUST_ROOT_FIELDS = {
    "schema_version",
    "key_id",
    "algorithm",
    "public_key_base64",
    "purposes",
    "not_before",
    "expires_at",
    "revoked_at",
}
SIGNATURE_FIELDS = {
    "algorithm",
    "key_id",
    "purpose",
    "signed_at",
    "payload_sha256",
    "value_base64",
}
EVALUATOR_PURPOSES = frozenset(SCHEMA_PURPOSES.values()) - {"candidate_submission"}


class AttestationError(ValueError):
    """Raised when signed evaluation evidence is invalid or untrusted."""


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_time(value: object, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value:
        raise AttestationError(f"{field} must be an RFC 3339 timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AttestationError(f"{field} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise AttestationError(f"{field} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _decode_base64(value: object, *, field: str, expected_length: int) -> bytes:
    if not isinstance(value, str):
        raise AttestationError(f"{field} must be base64 text")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AttestationError(f"{field} is not valid base64") from exc
    if len(decoded) != expected_length:
        raise AttestationError(f"{field} must decode to {expected_length} bytes")
    return decoded


def unsigned_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact signed object, excluding only its signature envelope."""

    return {key: value for key, value in payload.items() if key != "signature"}


def signature_message(payload: Mapping[str, Any]) -> bytes:
    """Build the cross-purpose, canonical message signed by Ed25519."""

    canonical = canonical_json(unsigned_payload(payload)).encode("utf-8")
    return SIGNATURE_DOMAIN + hashlib.sha256(canonical).digest()


def _validate_root_shape(root: Mapping[str, Any], *, allow_candidate_submission: bool) -> None:
    if set(root) != TRUST_ROOT_FIELDS:
        raise AttestationError("protected trust root has an invalid closed shape")
    if root.get("schema_version") != "ProtectedTrustRoot.v1":
        raise AttestationError("unsupported protected trust-root schema")
    if root.get("algorithm") != "Ed25519":
        raise AttestationError("protected trust root must use Ed25519")
    if not isinstance(root.get("key_id"), str) or not root["key_id"]:
        raise AttestationError("protected trust root key_id is required")
    purposes = root.get("purposes")
    if not isinstance(purposes, list) or len(purposes) != 1 or not isinstance(purposes[0], str):
        raise AttestationError("protected trust root must authorize exactly one purpose")
    allowed = set(EVALUATOR_PURPOSES)
    if allow_candidate_submission:
        allowed.add("candidate_submission")
    if purposes[0] not in allowed:
        raise AttestationError(f"protected trust root has an unknown purpose: {purposes[0]}")
    _decode_base64(root.get("public_key_base64"), field="public_key_base64", expected_length=32)
    not_before = _parse_time(root.get("not_before"), "not_before")
    expires_at = _parse_time(root.get("expires_at"), "expires_at")
    if expires_at <= not_before:
        raise AttestationError("protected trust root validity window is invalid")
    if root.get("revoked_at") is not None:
        _parse_time(root["revoked_at"], "revoked_at")


def validate_trust_store(trust_store: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a closed evaluator trust store of unique one-purpose roots."""

    if set(trust_store) != {"schema_version", "keys"}:
        raise AttestationError("protected trust store has an invalid closed shape")
    if trust_store.get("schema_version") != "ProtectedTrustStore.v1":
        raise AttestationError("unsupported protected trust-store schema")
    keys = trust_store.get("keys")
    if not isinstance(keys, list) or not keys:
        raise AttestationError("protected trust store keys must be a non-empty list")
    key_ids: set[str] = set()
    validated: list[dict[str, Any]] = []
    for item in keys:
        if not isinstance(item, Mapping):
            raise AttestationError("protected trust store keys must be objects")
        _validate_root_shape(item, allow_candidate_submission=False)
        key_id = str(item["key_id"])
        if key_id in key_ids:
            raise AttestationError(f"protected trust store has duplicate key_id: {key_id}")
        key_ids.add(key_id)
        validated.append(dict(item))
    return {"schema_version": "ProtectedTrustStore.v1", "keys": validated}


def _select_trust_root(trust_root: Mapping[str, Any], key_id: str, purpose: str) -> Mapping[str, Any]:
    if trust_root.get("schema_version") == "ProtectedTrustStore.v1":
        store = validate_trust_store(trust_root)
        matches = [
            item
            for item in store["keys"]
            if item.get("key_id") == key_id and item.get("purposes") == [purpose]
        ]
        if len(matches) != 1:
            raise AttestationError("signature key_id and purpose are not uniquely present in the protected trust store")
        return matches[0]
    _validate_root_shape(trust_root, allow_candidate_submission=True)
    return trust_root


def validate_trust_root(
    trust_root: Mapping[str, Any],
    *,
    purpose: str,
    key_id: str,
    now: dt.datetime | None = None,
) -> Mapping[str, Any]:
    root = _select_trust_root(trust_root, key_id, purpose)
    if root.get("key_id") != key_id:
        raise AttestationError("signature key_id does not match the protected trust root")
    purposes = root.get("purposes")
    if purposes != [purpose]:
        raise AttestationError(f"protected trust root does not authorize purpose: {purpose}")

    current_value = now or _utc_now()
    if current_value.tzinfo is None:
        raise AttestationError("current time must include a timezone")
    current = current_value.astimezone(dt.timezone.utc)
    not_before = _parse_time(root.get("not_before"), "not_before")
    expires_at = _parse_time(root.get("expires_at"), "expires_at")
    revoked = root.get("revoked_at")
    if revoked is not None:
        _parse_time(revoked, "revoked_at")
        raise AttestationError("protected trust root is revoked")
    if current < not_before:
        raise AttestationError("protected trust root is not yet valid")
    if current >= expires_at:
        raise AttestationError("protected trust root is expired")
    return root


def validate_signed_attestation(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any],
    expected_purpose: str | None = None,
    now: dt.datetime | None = None,
    max_future_skew_seconds: int = 300,
) -> dict[str, Any]:
    """Verify an attestation's exact payload binding, signer, and validity window."""

    signature = payload.get("signature")
    if not isinstance(signature, Mapping) or set(signature) != SIGNATURE_FIELDS:
        raise AttestationError("attestation signature has an invalid closed shape")
    if signature.get("algorithm") != "Ed25519":
        raise AttestationError("attestation signature must use Ed25519")

    schema_version = payload.get("schema_version")
    inferred_purpose = SCHEMA_PURPOSES.get(str(schema_version))
    purpose = expected_purpose or inferred_purpose
    if not purpose:
        raise AttestationError("attestation purpose cannot be inferred")
    if signature.get("purpose") != purpose:
        raise AttestationError("attestation signature purpose does not match its evidence type")

    current_value = now or _utc_now()
    if current_value.tzinfo is None:
        raise AttestationError("current time must include a timezone")
    current = current_value.astimezone(dt.timezone.utc)
    signed_at = _parse_time(signature.get("signed_at"), "signed_at")
    if signed_at > current + dt.timedelta(seconds=max_future_skew_seconds):
        raise AttestationError("attestation signed_at is in the future")

    key_id = str(signature.get("key_id") or "")
    root = validate_trust_root(trust_root, purpose=purpose, key_id=key_id, now=current)
    if signed_at < _parse_time(root["not_before"], "not_before"):
        raise AttestationError("attestation predates the signing key validity window")
    if signed_at >= _parse_time(root["expires_at"], "expires_at"):
        raise AttestationError("attestation was signed after the signing key expired")

    unsigned = unsigned_payload(payload)
    actual_hash = artifact_hash(unsigned)
    claimed_hash = signature.get("payload_sha256")
    if not isinstance(claimed_hash, str) or not SHA256_RE.fullmatch(claimed_hash) or claimed_hash != actual_hash:
        raise AttestationError("attestation payload hash does not match its canonical payload")

    if "expires_at" in unsigned and current >= _parse_time(unsigned["expires_at"], "expires_at"):
        raise AttestationError("attestation is expired")
    public_key = Ed25519PublicKey.from_public_bytes(
        _decode_base64(root["public_key_base64"], field="public_key_base64", expected_length=32)
    )
    signature_bytes = _decode_base64(signature.get("value_base64"), field="value_base64", expected_length=64)
    try:
        public_key.verify(signature_bytes, signature_message(unsigned))
    except InvalidSignature as exc:
        raise AttestationError("Ed25519 signature verification failed") from exc
    return dict(unsigned)


def validate_candidate_submission(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any],
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    return validate_signed_attestation(
        payload,
        trust_root=trust_root,
        expected_purpose="candidate_submission",
        now=now,
    )


def validate_sealed_bundle_attestation(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any],
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    verified = validate_signed_attestation(
        payload,
        trust_root=trust_root,
        expected_purpose="sealed_bundle",
        now=now,
    )
    if verified.get("candidate_visible") is not False or verified.get("storage_class") != "protected":
        raise AttestationError("sealed bundle attestation must assert candidate-blind protected storage")
    return verified


def validate_judge_qualification(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any],
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    return validate_signed_attestation(
        payload,
        trust_root=trust_root,
        expected_purpose="judge_qualification",
        now=now,
    )


def validate_execution_receipt(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any],
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    return validate_signed_attestation(
        payload,
        trust_root=trust_root,
        expected_purpose="execution_receipt",
        now=now,
    )


def validate_adapter_conformance(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any],
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    verified = validate_signed_attestation(
        payload,
        trust_root=trust_root,
        expected_purpose="adapter_conformance",
        now=now,
    )
    required_checks = (
        "response_model_resolved",
        "usage_complete",
        "retry_semantics_verified",
        "tool_semantics_verified",
        "session_isolation_verified",
        "authorship_boundary_verified",
        "authentication_verified",
        "qualified",
    )
    failed = [field for field in required_checks if verified.get(field) is not True]
    if failed:
        raise AttestationError(f"adapter conformance failed required checks: {', '.join(failed)}")
    model = str(verified.get("resolved_model_identifier") or "")
    if not model or model.lower() in {"default", "latest", "auto"}:
        raise AttestationError("adapter conformance lacks a resolved model from the response")
    for field in (
        "adapter_sha256",
        "cli_sha256",
        "tool_policy_sha256",
        "approval_policy_sha256",
        "credential_descriptor_sha256",
    ):
        if not SHA256_RE.fullmatch(str(verified.get(field) or "")):
            raise AttestationError(f"adapter conformance has an invalid {field}")
    for field in ("fixture_receipt_sha256s", "probe_receipt_sha256s"):
        hashes = verified.get(field)
        if (
            not isinstance(hashes, list)
            or not hashes
            or len(set(hashes)) != len(hashes)
            or any(not isinstance(value, str) or not SHA256_RE.fullmatch(value) for value in hashes)
        ):
            raise AttestationError(f"adapter conformance has invalid {field}")
    return verified


def validate_global_token_ledger(
    payload: Mapping[str, Any],
    *,
    trust_root: Mapping[str, Any],
    now: dt.datetime | None = None,
    expected_previous_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify one signed cumulative token ledger and its exact predecessor link."""

    verified = validate_signed_attestation(
        payload,
        trust_root=trust_root,
        expected_purpose="global_token_ledger",
        now=now,
    )
    if verified.get("profile") != "promotion" or verified.get("token_cap") != 5_000_000:
        raise AttestationError("global token ledger must enforce the promotion 5M raw-token cap")
    entries = verified.get("entries")
    if not isinstance(entries, list) or not entries:
        raise AttestationError("global token ledger entries must be non-empty")
    totals = {"reserved": 0, "raw": 0, "cached": 0, "billed": 0}
    entry_ids: set[str] = set()
    receipt_hashes: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise AttestationError("global token ledger entries must be objects")
        entry_id = str(entry.get("entry_id") or "")
        if not entry_id or entry_id in entry_ids:
            raise AttestationError("global token ledger entry IDs must be present and unique")
        entry_ids.add(entry_id)
        hashes = entry.get("receipt_sha256s")
        if (
            not isinstance(hashes, list)
            or not hashes
            or len(set(hashes)) != len(hashes)
            or any(not isinstance(value, str) or not SHA256_RE.fullmatch(value) for value in hashes)
        ):
            raise AttestationError("global token ledger receipt hashes are invalid")
        duplicates = receipt_hashes.intersection(hashes)
        if duplicates:
            raise AttestationError("global token ledger counts a receipt in more than one entry")
        receipt_hashes.update(hashes)
        for field in totals:
            value = entry.get(field)
            if not isinstance(value, int) or value < 0:
                raise AttestationError("global token ledger accounting values must be non-negative integers")
            totals[field] += value
        if int(entry["raw"]) > int(entry["reserved"]):
            raise AttestationError("global token ledger raw usage exceeds its reservation")
    if verified.get("totals") != totals:
        raise AttestationError("global token ledger totals do not match its entries")
    if totals["reserved"] > 5_000_000 or totals["raw"] > 5_000_000:
        raise AttestationError("global token ledger exceeds the 5M raw-token cap")
    if verified.get("remaining_raw_tokens") != 5_000_000 - totals["raw"]:
        raise AttestationError("global token ledger remaining_raw_tokens is inconsistent")
    sequence = verified.get("sequence")
    previous = verified.get("previous_ledger_sha256")
    if not isinstance(sequence, int) or sequence < 0:
        raise AttestationError("global token ledger sequence must be non-negative")
    if sequence == 0 and previous is not None:
        raise AttestationError("initial global token ledger must not claim a predecessor")
    if sequence > 0 and (not isinstance(previous, str) or not SHA256_RE.fullmatch(previous)):
        raise AttestationError("global token ledger has an invalid previous ledger hash")
    if expected_previous_sha256 is not None and previous != expected_previous_sha256:
        raise AttestationError("global token ledger previous ledger hash does not match")
    return verified
