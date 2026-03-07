from __future__ import annotations

import pytest

from intent_pipeline.ingestion.url_policy import UrlRejectionCode, UrlSourceRejectedError
from intent_pipeline.pipeline import ExtensionGateBlockedError, run_phase1_pipeline


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
            }
        ],
    }


def test_rejected_url_never_reaches_sanitizer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "intent_pipeline.pipeline.sanitize_two_pass",
        lambda _raw: (_ for _ in ()).throw(AssertionError("sanitize must not run for rejected URLs")),
    )

    with pytest.raises(UrlSourceRejectedError) as exc_info:
        run_phase1_pipeline(
            "https://blocked.example.net/docs/input.txt",
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
            url_policy=_url_policy_payload(),
        )

    assert exc_info.value.rejection.code is UrlRejectionCode.DISALLOWED_HOST


def test_url_requires_extension_gate_allowance() -> None:
    with pytest.raises(ExtensionGateBlockedError) as exc_info:
        run_phase1_pipeline("https://example.com/docs/input.txt")

    assert exc_info.value.decision.reason_code.value == "EXT-GATE-001-EXTENSIONS-DISABLED"
