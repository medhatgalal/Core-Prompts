"""Bounded URL retrieval and immutable content-addressed snapshot materialization."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import ipaddress
from pathlib import Path
import socket
import tempfile
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .source_resolver import ResolvedSource, ResolvedSourceKind, SourceResolverError, resolve_source
from .url_policy import (
    UrlPolicyContract,
    UrlPolicyRule,
    UrlSourceRejectedError,
    evaluate_url_policy,
    reject_content_type,
    reject_fetch_failed,
    reject_private_address,
    reject_redirect_limit,
    reject_response_too_large,
    reject_timeout_limit,
)


_REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True, slots=True)
class UrlTransportResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    redirect_url: str | None = None


@dataclass(frozen=True, slots=True)
class UrlSnapshotDescriptor:
    original_source: str
    normalized_source: str
    snapshot_path: Path
    content_sha256: str
    content_type: str
    content_length: int
    policy_rule_id: str
    evidence_paths: tuple[str, ...]

    def as_source_metadata(self) -> dict[str, str]:
        return {
            "source_type": ResolvedSourceKind.URL.value,
            "normalized_source": self.normalized_source,
            "policy_rule_id": self.policy_rule_id,
            "content_sha256": self.content_sha256,
            "content_type": self.content_type,
        }


class StdlibUrlTransport:
    """One-hop transport using stdlib urllib with redirects disabled."""

    def open(self, url: str, *, timeout_seconds: int, max_bytes: int) -> UrlTransportResponse:
        request = Request(
            url,
            headers={
                "Accept": "text/plain, text/markdown;q=0.9, text/*;q=0.8, */*;q=0.1",
                "User-Agent": "intent-pipeline/1.0",
            },
        )
        opener = build_opener(_NoRedirectHandler)
        try:
            with opener.open(request, timeout=timeout_seconds) as response:
                headers = {str(key).lower(): str(value) for key, value in response.headers.items()}
                body = response.read(max_bytes + 1)
                return UrlTransportResponse(
                    status_code=int(response.getcode()),
                    headers=headers,
                    body=body,
                )
        except HTTPError as exc:
            headers = {str(key).lower(): str(value) for key, value in exc.headers.items()}
            location = headers.get("location") if exc.code in _REDIRECT_STATUS_CODES else None
            body = exc.read(max_bytes + 1) if location is None else b""
            return UrlTransportResponse(
                status_code=int(exc.code),
                headers=headers,
                body=body,
                redirect_url=location,
            )


class UrlSnapshotStore:
    """Materialize approved URL payloads into immutable local snapshots."""

    def __init__(
        self,
        snapshot_root: Path | None = None,
        *,
        transport: object | None = None,
    ) -> None:
        self.snapshot_root = snapshot_root or (Path(tempfile.gettempdir()) / "intent-pipeline-url-snapshots")
        self.transport = transport or StdlibUrlTransport()

    def materialize(
        self,
        source: ResolvedSource,
        policy_contract: UrlPolicyContract | Mapping[str, object] | None,
    ) -> UrlSnapshotDescriptor:
        if source.kind is not ResolvedSourceKind.URL:
            raise TypeError("UrlSnapshotStore.materialize expects a URL ResolvedSource")

        redirect_count = 0
        current_source = source
        while True:
            evaluation = evaluate_url_policy(current_source, policy_contract)
            rule = evaluation.require_rule()
            self._validate_public_addresses(current_source, matched_rule=rule)

            response = self._open_url(
                current_source.normalized_source,
                timeout_seconds=rule.timeout_seconds,
                max_bytes=rule.max_bytes,
            )
            if response.redirect_url:
                if redirect_count >= rule.redirect_limit:
                    raise UrlSourceRejectedError(
                        reject_redirect_limit(current_source, matched_rule_id=rule.rule_id)
                    )
                current_source = _resolve_redirect_source(current_source.normalized_source, response.redirect_url)
                redirect_count += 1
                continue

            content_type = str(response.headers.get("content-type", "")).split(";", 1)[0].lower()
            if not rule.allows_content_type(content_type):
                raise UrlSourceRejectedError(
                    reject_content_type(
                        current_source,
                        content_type or "<missing>",
                        matched_rule_id=rule.rule_id,
                    )
                )
            if len(response.body) > rule.max_bytes:
                raise UrlSourceRejectedError(
                    reject_response_too_large(
                        current_source,
                        len(response.body),
                        matched_rule_id=rule.rule_id,
                    )
                )
            snapshot_path, content_hash = self._write_snapshot(response.body)
            return UrlSnapshotDescriptor(
                original_source=source.original_source,
                normalized_source=current_source.normalized_source,
                snapshot_path=snapshot_path,
                content_sha256=content_hash,
                content_type=content_type,
                content_length=len(response.body),
                policy_rule_id=rule.rule_id,
                evidence_paths=tuple(sorted(set(rule.evidence_paths) | {"snapshot.content_sha256", "url_fetch"})),
            )

    def _open_url(self, url: str, *, timeout_seconds: int, max_bytes: int) -> UrlTransportResponse:
        try:
            response = self.transport.open(url, timeout_seconds=timeout_seconds, max_bytes=max_bytes)
        except TimeoutError as exc:
            source = resolve_source(url)
            raise UrlSourceRejectedError(reject_timeout_limit(source)) from exc
        except URLError as exc:
            source = resolve_source(url)
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, TimeoutError):
                raise UrlSourceRejectedError(reject_timeout_limit(source)) from exc
            raise UrlSourceRejectedError(
                reject_fetch_failed(source, f"Unable to fetch URL: {reason}")
            ) from exc
        except OSError as exc:
            source = resolve_source(url)
            raise UrlSourceRejectedError(
                reject_fetch_failed(source, f"Unable to fetch URL: {exc}")
            ) from exc
        if not isinstance(response, UrlTransportResponse):
            raise TypeError("URL transport must return UrlTransportResponse")
        return response

    def _validate_public_addresses(self, source: ResolvedSource, *, matched_rule: UrlPolicyRule) -> None:
        assert source.host is not None
        port = source.port or (443 if source.scheme == "https" else 80)
        for address in _resolve_host_addresses(source.host, port):
            if not _is_public_address(address):
                raise UrlSourceRejectedError(
                    reject_private_address(
                        source,
                        address,
                        matched_rule_id=matched_rule.rule_id,
                    )
                )

    def _write_snapshot(self, body: bytes) -> tuple[Path, str]:
        content_hash = sha256(body).hexdigest()
        self.snapshot_root.mkdir(parents=True, exist_ok=True)
        snapshot_path = self.snapshot_root / content_hash
        if not snapshot_path.exists():
            snapshot_path.write_bytes(body)
        return snapshot_path, content_hash


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _resolve_redirect_source(base_url: str, redirect_url: str) -> ResolvedSource:
    candidate = urljoin(base_url, redirect_url)
    try:
        resolved = resolve_source(candidate)
    except SourceResolverError as exc:
        raise UrlSourceRejectedError(
            reject_fetch_failed(
                resolve_source(base_url),
                f"Invalid redirect target: {exc.detail}",
            )
        ) from exc
    if resolved.kind is not ResolvedSourceKind.URL:
        raise UrlSourceRejectedError(
            reject_fetch_failed(resolve_source(base_url), "Redirect target must remain a URL.")
        )
    return resolved


def _resolve_host_addresses(host: str, port: int) -> tuple[str, ...]:
    addresses: set[str] = set()
    for family, _, _, _, sockaddr in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        if family == socket.AF_INET:
            addresses.add(str(sockaddr[0]))
        elif family == socket.AF_INET6:
            addresses.add(str(sockaddr[0]))
    return tuple(sorted(addresses))


def _is_public_address(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    # Phase 9 treats every non-global destination as out of bounds, including
    # CGNAT/shared space and other special-use ranges that are not always
    # covered by the narrower private/reserved attribute set.
    return ip.is_global


__all__ = [
    "StdlibUrlTransport",
    "UrlSnapshotDescriptor",
    "UrlSnapshotStore",
    "UrlTransportResponse",
]
