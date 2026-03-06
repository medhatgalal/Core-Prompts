"""Local-source admission policy for ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import urlparse

from intent_pipeline.extensions.contracts import (
    ExtensionGateDecision,
    ExtensionGateResult,
    ExtensionPolicyContract,
    ExtensionSourceKind,
    parse_extension_policy_contract_fail_closed,
)


_DISALLOWED_URI_SCHEMES = frozenset({"http", "https", "ftp", "file", "ssh", "data"})
_WINDOWS_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:[\\/]")


class SourceRejectionCode(str, Enum):
    """Deterministic reasons for policy rejections."""

    INVALID_SOURCE_TYPE = "INVALID_SOURCE_TYPE"
    EMPTY_SOURCE = "EMPTY_SOURCE"
    URI_SCHEME_NOT_ALLOWED = "URI_SCHEME_NOT_ALLOWED"
    NETWORK_PATH_NOT_ALLOWED = "NETWORK_PATH_NOT_ALLOWED"
    PATH_RESOLUTION_FAILED = "PATH_RESOLUTION_FAILED"
    NOT_A_FILE = "NOT_A_FILE"
    EXTENSION_GATE_BLOCK = "EXTENSION_GATE_BLOCK"
    EXTENSION_GATE_NEEDS_REVIEW = "EXTENSION_GATE_NEEDS_REVIEW"


@dataclass(frozen=True)
class SourceRejection:
    code: SourceRejectionCode
    detail: str


@dataclass(frozen=True)
class LocalSourceDescriptor:
    original_source: str
    absolute_path: Path


class LocalSourceRejectedError(ValueError):
    """Raised when a source is rejected by local ingestion policy."""

    def __init__(self, rejection: SourceRejection) -> None:
        super().__init__(f"{rejection.code.value}: {rejection.detail}")
        self.rejection = rejection


@dataclass(frozen=True)
class SourceValidationResult:
    accepted: bool
    source: LocalSourceDescriptor | None = None
    rejection: SourceRejection | None = None
    extension_gate: ExtensionGateResult | None = None

    def require_source(self) -> LocalSourceDescriptor:
        if self.source is not None:
            return self.source
        if self.rejection is None:
            raise RuntimeError("Rejected source must include rejection details.")
        raise LocalSourceRejectedError(self.rejection)


def _reject(code: SourceRejectionCode, detail: str) -> SourceValidationResult:
    return SourceValidationResult(
        accepted=False,
        rejection=SourceRejection(code=code, detail=detail),
    )


def _reject_extension_gate(gate_result: ExtensionGateResult) -> SourceValidationResult:
    code = (
        SourceRejectionCode.EXTENSION_GATE_NEEDS_REVIEW
        if gate_result.decision is ExtensionGateDecision.NEEDS_REVIEW
        else SourceRejectionCode.EXTENSION_GATE_BLOCK
    )
    return SourceValidationResult(
        accepted=False,
        rejection=SourceRejection(
            code=code,
            detail=f"fail.closed::{gate_result.reason_code.value}",
        ),
        extension_gate=gate_result,
    )


def _is_disallowed_uri(raw_source: str) -> bool:
    if _WINDOWS_DRIVE_PREFIX.match(raw_source):
        return False
    parsed = urlparse(raw_source)
    return parsed.scheme.lower() in _DISALLOWED_URI_SCHEMES


def _is_network_style_path(raw_source: str) -> bool:
    return raw_source.startswith("\\\\") or raw_source.startswith("//")


def validate_local_source(
    source: str | Path,
    extension_policy: ExtensionPolicyContract | Mapping[str, Any] | None = None,
    *,
    require_extension_policy: bool = False,
) -> SourceValidationResult:
    """Validate that the source is a local file path and resolve it absolutely."""
    extension_gate: ExtensionGateResult | None = None
    if require_extension_policy or extension_policy is not None:
        parsed_policy, policy_gate = parse_extension_policy_contract_fail_closed(
            extension_policy,
            evidence_path="ingestion.policy_contract",
        )
        if policy_gate.decision is not ExtensionGateDecision.ALLOW:
            return _reject_extension_gate(policy_gate)

        assert parsed_policy is not None
        extension_gate = parsed_policy.evaluate_source_kind(ExtensionSourceKind.LOCAL_FILE)
        if extension_gate.decision is not ExtensionGateDecision.ALLOW:
            return _reject_extension_gate(extension_gate)

    if isinstance(source, Path):
        raw_source = str(source)
    elif isinstance(source, str):
        raw_source = source
    else:
        return _reject(
            SourceRejectionCode.INVALID_SOURCE_TYPE,
            f"Expected str | Path, got {type(source).__name__}",
        )

    if raw_source == "":
        return _reject(SourceRejectionCode.EMPTY_SOURCE, "Source cannot be empty.")
    if _is_disallowed_uri(raw_source):
        return _reject(
            SourceRejectionCode.URI_SCHEME_NOT_ALLOWED,
            f"URI scheme is not allowed for ingestion: {raw_source}",
        )
    if _is_network_style_path(raw_source):
        return _reject(
            SourceRejectionCode.NETWORK_PATH_NOT_ALLOWED,
            f"Network-style paths are not allowed: {raw_source}",
        )

    try:
        absolute_path = Path(raw_source).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        return _reject(
            SourceRejectionCode.PATH_RESOLUTION_FAILED,
            f"Unable to resolve source path: {exc}",
        )

    if not absolute_path.is_file():
        return _reject(
            SourceRejectionCode.NOT_A_FILE,
            f"Source is not an existing file: {absolute_path}",
        )

    return SourceValidationResult(
        accepted=True,
        source=LocalSourceDescriptor(
            original_source=raw_source,
            absolute_path=absolute_path,
        ),
        extension_gate=extension_gate,
    )
