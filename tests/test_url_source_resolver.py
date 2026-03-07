from __future__ import annotations

from pathlib import Path

import pytest

from intent_pipeline.ingestion.source_resolver import (
    ResolvedSourceKind,
    SourceResolverCode,
    SourceResolverError,
    resolve_source,
)


def test_url_resolver_canonicalizes_http_variants_to_one_form() -> None:
    variants = [
        "HTTPS://Example.COM:443/docs/index.txt",
        "https://example.com/docs/index.txt",
        " https://EXAMPLE.com:443/docs/guide/../index.txt ",
    ]

    outputs = [resolve_source(variant).normalized_source for variant in variants]

    assert outputs == [
        "https://example.com/docs/index.txt",
        "https://example.com/docs/index.txt",
        "https://example.com/docs/index.txt",
    ]


def test_url_resolver_preserves_local_file_resolution(tmp_path: Path) -> None:
    source_file = tmp_path / "note.txt"
    source_file.write_text("hello\n", encoding="utf-8")

    resolved = resolve_source(source_file)

    assert resolved.kind is ResolvedSourceKind.LOCAL_FILE
    assert resolved.absolute_path == source_file.resolve()
    assert resolved.normalized_source == str(source_file.resolve())


def test_url_resolver_rejects_unsupported_url_scheme() -> None:
    with pytest.raises(SourceResolverError) as exc_info:
        resolve_source("ftp://example.com/archive.txt")

    assert exc_info.value.code is SourceResolverCode.URL_SCHEME_NOT_ALLOWED
