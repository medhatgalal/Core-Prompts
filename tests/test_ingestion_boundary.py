from __future__ import annotations

from pathlib import Path

import pytest

from src.intent_pipeline.ingestion.policy import (
    LocalSourceRejectedError,
    SourceRejectionCode,
    validate_local_source,
)
from src.intent_pipeline.ingestion.reader import read_local_file_bytes, read_local_file_text


def test_ingest_01_local_only_accepts_absolute_path(tmp_path: Path) -> None:
    """INGEST-01: local absolute file paths are accepted."""
    source_file = tmp_path / "input.txt"
    source_file.write_text("hello", encoding="utf-8")

    result = validate_local_source(source_file)

    assert result.accepted is True
    approved = result.require_source()
    assert approved.absolute_path == source_file.resolve()


def test_ingest_01_local_only_accepts_relative_path(tmp_path: Path, monkeypatch) -> None:
    """INGEST-01: local relative file paths are accepted."""
    source_file = tmp_path / "nested" / "input.txt"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("hello", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = validate_local_source("nested/input.txt")

    assert result.accepted is True
    approved = result.require_source()
    assert approved.absolute_path == source_file.resolve()


def test_ingest_02_uri_reject_blocks_non_local_schemes() -> None:
    """INGEST-02: URI and network-style sources are rejected by policy."""
    rejected_sources = [
        "http://example.com/file.txt",
        "https://example.com/file.txt",
        "ftp://example.com/file.txt",
        "file:///tmp/file.txt",
        "ssh://example.com/file.txt",
        "data:text/plain;base64,SGVsbG8=",
        "\\\\server\\share\\file.txt",
        "//server/share/file.txt",
    ]

    for source in rejected_sources:
        result = validate_local_source(source)
        assert result.accepted is False
        assert result.rejection is not None
        assert result.rejection.code in {
            SourceRejectionCode.URI_SCHEME_NOT_ALLOWED,
            SourceRejectionCode.NETWORK_PATH_NOT_ALLOWED,
        }


def test_ingest_02_reject_before_read(monkeypatch) -> None:
    """INGEST-02: URI rejection happens before any file read operation."""

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("read_text should not be called for rejected sources")

    monkeypatch.setattr(Path, "read_text", fail_if_called)

    with pytest.raises(LocalSourceRejectedError) as exc_info:
        read_local_file_text("https://example.com/file.txt")

    assert exc_info.value.rejection.code == SourceRejectionCode.URI_SCHEME_NOT_ALLOWED


def test_ingest_01_read_local_file_text_and_bytes(tmp_path: Path) -> None:
    """INGEST-01: approved local files are read deterministically."""
    source_file = tmp_path / "payload.txt"
    source_file.write_text("hello world\n", encoding="utf-8")

    assert read_local_file_text(source_file) == "hello world\n"
    assert read_local_file_bytes(source_file) == b"hello world\n"
