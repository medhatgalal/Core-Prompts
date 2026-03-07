from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.ingestion.url_snapshot_store import UrlTransportResponse
from intent_pipeline.pipeline import run_phase1_pipeline


def _extension_policy_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "extension_mode": "CONTROLLED",
        "rules": [
            {
                "rule_id": "v1.url.allow",
                "source_kind": "URL",
                "decision": "ALLOW",
                "priority": 10,
                "evidence_paths": ["policy_contract.rules[0]"],
            }
        ],
    }


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


def test_approved_url_pipeline_reads_snapshot_not_live_stream(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeTransport(
        responses={
            "https://example.com/docs/input.txt": UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain"},
                body=(
                    b"Objective: Produce deterministic URL summaries.\n"
                    b"In Scope: Snapshot approved URL content.\n"
                    b"Constraint: Keep snapshot reads immutable.\n"
                ),
            )
        },
        calls=[],
    )
    captured: dict[str, Path] = {}
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda _host, _port: ("93.184.216.34",),
    )
    monkeypatch.setattr(
        "intent_pipeline.pipeline.read_snapshot_text",
        lambda snapshot, encoding="utf-8": captured.setdefault("snapshot_path", snapshot.snapshot_path).read_text(encoding=encoding),
    )

    result = run_phase1_pipeline(
        "https://example.com/docs/input.txt",
        extension_mode="CONTROLLED",
        route_profile="IMPLEMENTATION",
        requested_capabilities=("cap.read",),
        extension_policy=_extension_policy_payload(),
        url_policy=_url_policy_payload(),
        snapshot_root=tmp_path,
        url_transport=transport,
    )

    assert "Objective: Produce deterministic URL summaries." in result
    assert captured["snapshot_path"].exists()
    assert transport.calls == ["https://example.com/docs/input.txt|5|4096"]


def test_rejected_url_pipeline_returns_typed_needs_review_evidence() -> None:
    with pytest.raises(UrlSourceRejectedError) as exc_info:
        run_phase1_pipeline(
            "https://example.com/private/input.txt",
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
            url_policy=_url_policy_payload(),
        )

    assert exc_info.value.rejection.terminal_status == "NEEDS_REVIEW"
    assert exc_info.value.rejection.evidence_paths == ("url_policy.rules.allowed_path_prefixes",)


def test_url_pipeline_rejects_non_intent_bearing_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeTransport(
        responses={
            "https://example.com/docs/python.gitignore": UrlTransportResponse(
                status_code=200,
                headers={"content-type": "text/plain"},
                body=(
                    b"# Byte-compiled / optimized / DLL files\n"
                    b"__pycache__/\n"
                    b"*.py[cod]\n"
                    b"*$py.class\n"
                ),
            )
        },
        calls=[],
    )
    monkeypatch.setattr(
        "intent_pipeline.ingestion.url_snapshot_store._resolve_host_addresses",
        lambda _host, _port: ("93.184.216.34",),
    )

    with pytest.raises(UrlSourceRejectedError) as exc_info:
        run_phase1_pipeline(
            "https://example.com/docs/python.gitignore",
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
            url_policy=_url_policy_payload(),
            snapshot_root=tmp_path,
            url_transport=transport,
        )

    assert exc_info.value.rejection.code.value == "URL-INGEST-013-UNSUITABLE-CONTENT"
    assert exc_info.value.rejection.terminal_status == "REJECTED"
    assert exc_info.value.rejection.evidence_paths == (
        "source_suitability.objective",
        "source_suitability.in_scope",
        "source_suitability.out_of_scope",
        "source_suitability.constraints",
        "source_suitability.acceptance",
    )
