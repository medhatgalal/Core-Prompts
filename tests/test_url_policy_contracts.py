from __future__ import annotations

import pytest

from intent_pipeline.ingestion.source_resolver import resolve_source
from intent_pipeline.ingestion.url_policy import (
    UrlPolicyContractError,
    UrlPolicyErrorCode,
    UrlRejectionCode,
    evaluate_url_policy,
    parse_url_policy_contract,
)


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


def test_url_policy_requires_explicit_rule_dimensions() -> None:
    invalid_payload = _url_policy_payload()
    invalid_payload["rules"] = [
        {
            "rule_id": "v1.url.docs.allow",
            "allowed_schemes": ["https"],
            "allowed_hosts": [],
            "allowed_domains": [],
            "allowed_path_prefixes": ["/docs"],
            "allowed_content_types": ["text/plain"],
            "max_bytes": 4096,
            "redirect_limit": 1,
            "timeout_seconds": 5,
        }
    ]

    with pytest.raises(UrlPolicyContractError) as exc_info:
        parse_url_policy_contract(invalid_payload)

    assert exc_info.value.code is UrlPolicyErrorCode.INVALID_RULE_FIELD


def test_url_policy_evaluates_canonical_url_against_allowlist() -> None:
    contract = parse_url_policy_contract(_url_policy_payload())
    source = resolve_source("HTTPS://EXAMPLE.COM:443/docs/start.txt")

    evaluation = evaluate_url_policy(source, contract)

    assert evaluation.accepted is True
    assert evaluation.require_rule().rule_id == "v1.url.docs.allow"


def test_url_policy_missing_contract_fails_closed() -> None:
    source = resolve_source("https://example.com/docs/start.txt")

    evaluation = evaluate_url_policy(source, None)

    assert evaluation.accepted is False
    assert evaluation.rejection is not None
    assert evaluation.rejection.code is UrlRejectionCode.POLICY_REQUIRED
    assert evaluation.rejection.terminal_status == "NEEDS_REVIEW"
