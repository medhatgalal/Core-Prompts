"""Policy-guarded local file reader for ingestion."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from .policy import LocalSourceRejectedError, SourceValidationResult, validate_local_source
from .url_snapshot_store import UrlSnapshotDescriptor


class IngestionReadErrorCode(str, Enum):
    """Deterministic error reasons for local file reads."""

    FILE_READ_FAILED = "FILE_READ_FAILED"
    TEXT_DECODE_FAILED = "TEXT_DECODE_FAILED"


class IngestionReadError(RuntimeError):
    """Raised when an approved local file cannot be read deterministically."""

    def __init__(self, code: IngestionReadErrorCode, path: Path, detail: str) -> None:
        super().__init__(f"{code.value}: {detail}")
        self.code = code
        self.path = path
        self.detail = detail


def _require_local_file(source: str | Path) -> Path:
    validation: SourceValidationResult = validate_local_source(source)
    descriptor = validation.require_source()
    return descriptor.absolute_path


def read_local_file_bytes(source: str | Path) -> bytes:
    """Read bytes from a local file source approved by ingestion policy."""
    approved_path = _require_local_file(source)
    try:
        return approved_path.read_bytes()
    except OSError as exc:
        raise IngestionReadError(
            IngestionReadErrorCode.FILE_READ_FAILED,
            approved_path,
            f"Unable to read bytes from approved source: {approved_path}",
        ) from exc


def read_local_file_text(source: str | Path, encoding: str = "utf-8") -> str:
    """Read text from a local file source approved by ingestion policy."""
    approved_path = _require_local_file(source)
    try:
        return approved_path.read_text(encoding=encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise IngestionReadError(
            IngestionReadErrorCode.TEXT_DECODE_FAILED,
            approved_path,
            f"Unable to decode approved source using {encoding}: {approved_path}",
        ) from exc
    except OSError as exc:
        raise IngestionReadError(
            IngestionReadErrorCode.FILE_READ_FAILED,
            approved_path,
            f"Unable to read text from approved source: {approved_path}",
        ) from exc


def read_snapshot_text(snapshot: UrlSnapshotDescriptor, encoding: str = "utf-8") -> str:
    """Read text from an immutable URL snapshot."""
    return read_local_file_text(snapshot.snapshot_path, encoding=encoding)


__all__ = [
    "IngestionReadError",
    "IngestionReadErrorCode",
    "LocalSourceRejectedError",
    "read_local_file_bytes",
    "read_local_file_text",
    "read_snapshot_text",
]
