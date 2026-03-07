from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import pytest

from intent_pipeline.ingestion.source_resolver import resolve_source
from intent_pipeline.ingestion.url_policy import UrlRejectionCode, UrlSourceRejectedError
from intent_pipeline.ingestion.url_snapshot_store import UrlSnapshotStore, UrlTransportResponse


def _url_policy_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "rules": [
            {
                "rule_id": "v1.url.docs.allow",
                "allowed_schemes": ["https"],
                "allowed_hosts": ["example.com"],
                "allowed_domains": [],
                "allowed_path_prefixes": ["/docs"],
                "allowed_content_types": ["text/plain"],
                "max_bytes": 4096,
                "redirect_limit": 1,
                "timeout_seconds": 5,
                "priority": 10,
                "evidence_paths": ["url_policy.rules[0]"],
            }
        ],
    }


@dataclass
class FakeTransport:
    responses: dict[str, UrlTransportResponse]
    calls: list[str]

    def open(self, url: str, *, timeout_seconds: int, max_bytes: int) -> UrlTransportResponse:
        self.calls.append(f"{url}|{timeout_seconds}|{max_bytes}")
        return self.responses[url]


def test_snapshot_store_materializes_content_addressed_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b"hello from snapshot\n"
    transport = FakeTransport(
        responses={
            "https://example.com/docs/input.txt": UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain; charset=utf-8"},
                body=body,
            )
        },
        calls=[],
    )
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda _host, _port: ("93.184.216.34",),
    )

    descriptor = UrlSnapshotStore(tmp_path, transport=transport).materialize(
        resolve_source("https://example.com/docs/input.txt"),
        _url_policy_payload(),
    )

    assert descriptor.snapshot_path.read_bytes() == body
    assert descriptor.snapshot_path.name == sha256(body).hexdigest()
    assert descriptor.content_sha256 == sha256(body).hexdigest()
    assert transport.calls == ["https://example.com/docs/input.txt|5|4096"]


def test_redirect_targets_are_revalidated_against_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeTransport(
        responses={
            "https://example.com/docs/input.txt": UrlTransportResponse(
                status_code=302,
                headers={"location": "https://blocked.example.net/docs/input.txt"},
                body=b"",
                redirect_url="https://blocked.example.net/docs/input.txt",
            )
        },
        calls=[],
    )
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda host, _port: ("93.184.216.34",) if host == "example.com" else ("203.0.113.20",),
    )

    with pytest.raises(UrlSourceRejectedError) as exc_info:
        UrlSnapshotStore(tmp_path, transport=transport).materialize(
            resolve_source("https://example.com/docs/input.txt"),
            _url_policy_payload(),
        )

    assert exc_info.value.rejection.code is UrlRejectionCode.DISALLOWED_HOST


def test_private_addresses_are_rejected_before_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeTransport(
        responses={
            "https://example.com/docs/input.txt": UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain"},
                body=b"body",
            )
        },
        calls=[],
    )
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda _host, _port: ("127.0.0.1",),
    )

    with pytest.raises(UrlSourceRejectedError) as exc_info:
        UrlSnapshotStore(tmp_path, transport=transport).materialize(
            resolve_source("https://example.com/docs/input.txt"),
            _url_policy_payload(),
        )

    assert exc_info.value.rejection.code is UrlRejectionCode.PRIVATE_ADDRESS_NOT_ALLOWED
    assert transport.calls == []


def test_non_global_addresses_are_rejected_before_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeTransport(
        responses={
            "https://example.com/docs/input.txt": UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain"},
                body=b"body",
            )
        },
        calls=[],
    )
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda _host, _port: ("100.64.0.1",),
    )

    with pytest.raises(UrlSourceRejectedError) as exc_info:
        UrlSnapshotStore(tmp_path, transport=transport).materialize(
            resolve_source("https://example.com/docs/input.txt"),
            _url_policy_payload(),
        )

    assert exc_info.value.rejection.code is UrlRejectionCode.PRIVATE_ADDRESS_NOT_ALLOWED
    assert transport.calls == []
