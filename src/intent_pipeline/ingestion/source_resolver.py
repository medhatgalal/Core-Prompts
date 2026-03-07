"""Deterministic source classification and canonical URL normalization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import posixpath
import re
from urllib.parse import quote, unquote, urlsplit, urlunsplit


_WINDOWS_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:[\\/]")
_SUPPORTED_URL_SCHEMES = frozenset({"http", "https"})
_EXPLICIT_URI_SCHEMES = frozenset({"http", "https", "ftp", "file", "ssh", "data"})
_SAFE_PATH_CHARS = "/~!$&'()*+,;=:@-._"


class SourceResolverCode(str, Enum):
    INVALID_SOURCE_TYPE = "INVALID_SOURCE_TYPE"
    EMPTY_SOURCE = "EMPTY_SOURCE"
    URL_SCHEME_NOT_ALLOWED = "URL_SCHEME_NOT_ALLOWED"
    URL_HOST_REQUIRED = "URL_HOST_REQUIRED"
    URL_CREDENTIALS_NOT_ALLOWED = "URL_CREDENTIALS_NOT_ALLOWED"
    URL_FRAGMENT_NOT_ALLOWED = "URL_FRAGMENT_NOT_ALLOWED"


class ResolvedSourceKind(str, Enum):
    LOCAL_FILE = "LOCAL_FILE"
    URL = "URL"


@dataclass(frozen=True, slots=True)
class ResolvedSource:
    kind: ResolvedSourceKind
    original_source: str
    normalized_source: str
    absolute_path: Path | None = None
    scheme: str | None = None
    host: str | None = None
    port: int | None = None
    path: str | None = None
    query: str = ""


class SourceResolverError(ValueError):
    """Raised when a source cannot be classified deterministically."""

    def __init__(self, code: SourceResolverCode, detail: str) -> None:
        super().__init__(f"{code.value}: {detail}")
        self.code = code
        self.detail = detail


def resolve_source(source: str | Path) -> ResolvedSource:
    """Resolve a raw ingestion source into either local-file or canonical URL form."""
    if isinstance(source, Path):
        raw_source = str(source)
        return _resolve_local_source(raw_source)
    if not isinstance(source, str):
        raise SourceResolverError(
            SourceResolverCode.INVALID_SOURCE_TYPE,
            f"Expected str | Path, got {type(source).__name__}",
        )

    raw_source = source
    if raw_source == "":
        raise SourceResolverError(SourceResolverCode.EMPTY_SOURCE, "Source cannot be empty.")

    stripped_source = raw_source.strip()
    if _WINDOWS_DRIVE_PREFIX.match(raw_source):
        return _resolve_local_source(raw_source)

    parsed = urlsplit(stripped_source)
    scheme = parsed.scheme.lower()
    if scheme in _SUPPORTED_URL_SCHEMES or scheme in _EXPLICIT_URI_SCHEMES:
        return _resolve_url_source(raw_source, stripped_source, parsed)
    return _resolve_local_source(raw_source)


def _resolve_local_source(raw_source: str) -> ResolvedSource:
    absolute_path = Path(raw_source).expanduser().resolve(strict=False)
    return ResolvedSource(
        kind=ResolvedSourceKind.LOCAL_FILE,
        original_source=raw_source,
        normalized_source=str(absolute_path),
        absolute_path=absolute_path,
    )


def _resolve_url_source(raw_source: str, stripped_source: str, parsed: object) -> ResolvedSource:
    split_result = parsed if hasattr(parsed, "scheme") else urlsplit(stripped_source)
    scheme = split_result.scheme.lower()
    if scheme not in _SUPPORTED_URL_SCHEMES:
        raise SourceResolverError(
            SourceResolverCode.URL_SCHEME_NOT_ALLOWED,
            f"Unsupported URL scheme: {scheme or '<missing>'}",
        )
    if split_result.username or split_result.password:
        raise SourceResolverError(
            SourceResolverCode.URL_CREDENTIALS_NOT_ALLOWED,
            "URL credentials are not allowed.",
        )
    if split_result.fragment:
        raise SourceResolverError(
            SourceResolverCode.URL_FRAGMENT_NOT_ALLOWED,
            "URL fragments are not allowed.",
        )
    if split_result.hostname is None:
        raise SourceResolverError(
            SourceResolverCode.URL_HOST_REQUIRED,
            "URL host is required.",
        )

    host = split_result.hostname.encode("idna").decode("ascii").lower()
    port = split_result.port
    if port == _default_port_for_scheme(scheme):
        port = None
    netloc = host if port is None else f"{host}:{port}"
    normalized_path = _normalize_url_path(split_result.path)
    normalized_source = urlunsplit((scheme, netloc, normalized_path, split_result.query, ""))

    return ResolvedSource(
        kind=ResolvedSourceKind.URL,
        original_source=raw_source,
        normalized_source=normalized_source,
        scheme=scheme,
        host=host,
        port=port,
        path=normalized_path,
        query=split_result.query,
    )


def _normalize_url_path(raw_path: str) -> str:
    decoded = unquote(raw_path or "/")
    if not decoded.startswith("/"):
        decoded = f"/{decoded}"
    preserve_trailing = decoded.endswith("/") and decoded != "/"
    normalized = posixpath.normpath(decoded)
    if preserve_trailing and normalized != "/":
        normalized = f"{normalized}/"
    return quote(normalized, safe=_SAFE_PATH_CHARS)


def _default_port_for_scheme(scheme: str) -> int | None:
    if scheme == "http":
        return 80
    if scheme == "https":
        return 443
    return None


__all__ = [
    "ResolvedSource",
    "ResolvedSourceKind",
    "SourceResolverCode",
    "SourceResolverError",
    "resolve_source",
]
