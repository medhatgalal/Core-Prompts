from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping


SHA256_RE = re.compile(r"[0-9a-f]{64}")
REDACTED_KEYS = {
    "case",
    "case_id",
    "case_ids",
    "body",
    "bodies",
    "label",
    "labels",
    "seed",
    "seeds",
    "raw_trace",
    "raw_traces",
    "prompt",
    "prompts",
    "expected_output",
    "expected_outputs",
}


class ProvenanceError(ValueError):
    """Raised when evaluation provenance is absent, weak, or candidate-visible."""


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    for component in (absolute, *absolute.parents):
        if component.is_symlink():
            return True
    return False


def validate_candidate_blind_paths(
    *,
    sealed_paths: Iterable[Path],
    repo_root: Path,
    candidate_readable_roots: Iterable[Path],
) -> None:
    """Reject sealed material that a candidate could read directly or through a symlink."""

    resolved_repo = repo_root.resolve(strict=True)
    readable = [root.resolve(strict=True) for root in candidate_readable_roots]
    for path in sealed_paths:
        if _has_symlink_component(path):
            raise ProvenanceError(f"sealed material must not use a symlink path: {path}")
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ProvenanceError(f"sealed material is missing: {path}") from exc
        if _is_within(resolved, resolved_repo):
            raise ProvenanceError(f"sealed material must remain outside the repository: {path}")
        if any(_is_within(resolved, root) for root in readable):
            raise ProvenanceError(f"sealed material is inside a candidate-readable root: {path}")


def redact_public_record(payload: Any, *, secrets: Iterable[str] = ()) -> Any:
    """Remove all case-level material and replace incidental secret strings."""

    secret_values = tuple(value for value in secrets if value)

    def sensitive_key(key: object) -> bool:
        normalized = str(key).lower()
        return (
            normalized in REDACTED_KEYS
            or "case_id" in normalized
            or "raw_trace" in normalized
            or "label" in normalized
            or "seed" in normalized
            or normalized.endswith("_body")
            or normalized.endswith("_prompt")
        )

    def redact(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): redact(item)
                for key, item in value.items()
                if not sensitive_key(key)
            }
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, tuple):
            return [redact(item) for item in value]
        if isinstance(value, str):
            replaced = value
            for secret in secret_values:
                replaced = replaced.replace(secret, "[REDACTED]")
            return replaced
        if str(value) in secret_values:
            return "[REDACTED]"
        return value

    return redact(payload)


def derive_evidence_grade(receipt: Mapping[str, Any], *, signature_verified: bool) -> str:
    """Derive evidence grade from receipt facts; never trust a claimed grade."""

    result = str(receipt.get("result") or "").upper()
    if result == "NOT_RUN" or not result:
        return "NOT_RUN"
    commitment = receipt.get("trace_commitment_sha256")
    complete_trace = receipt.get("trace_complete") is True and isinstance(commitment, str) and bool(SHA256_RE.fullmatch(commitment))
    if signature_verified and complete_trace:
        return "A"
    if signature_verified:
        return "B"
    return "C"


def validate_cell_provenance(
    receipt: Mapping[str, Any],
    *,
    signature_verified: bool,
    critical: bool,
) -> str:
    grade = derive_evidence_grade(receipt, signature_verified=signature_verified)
    claimed = receipt.get("derived_evidence_grade")
    if claimed is not None and claimed != grade:
        raise ProvenanceError("receipt evidence grade claim does not match verified provenance")
    if critical and grade != "A":
        raise ProvenanceError("critical evaluation cells require Grade A signed, complete trace evidence")
    return grade
