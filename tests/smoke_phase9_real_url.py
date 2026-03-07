from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.pipeline import ingest_phase1_source, run_phase1_pipeline
from intent_pipeline.uplift.engine import run_uplift_engine


NEGATIVE_URL = "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"
POSITIVE_URL = (
    "https://raw.githubusercontent.com/kubernetes/enhancements/master/keps/"
    "sig-api-machinery/2885-server-side-unknown-field-validation/README.md"
)


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
                "rule_id": "v1.url.raw-github-python-gitignore",
                "allowed_schemes": ["https"],
                "allowed_hosts": ["raw.githubusercontent.com"],
                "allowed_domains": [],
                "allowed_path_prefixes": ["/github/gitignore/main/"],
                "allowed_content_types": ["text/plain"],
                "max_bytes": 262144,
                "redirect_limit": 2,
                "timeout_seconds": 15,
                "priority": 10,
                "evidence_paths": ["url_policy.rules[0]"],
            },
            {
                "rule_id": "v1.url.raw-kubernetes-kep-2885",
                "allowed_schemes": ["https"],
                "allowed_hosts": ["raw.githubusercontent.com"],
                "allowed_domains": [],
                "allowed_path_prefixes": [
                    "/kubernetes/enhancements/master/keps/sig-api-machinery/2885-server-side-unknown-field-validation/"
                ],
                "allowed_content_types": ["text/plain"],
                "max_bytes": 524288,
                "redirect_limit": 2,
                "timeout_seconds": 15,
                "priority": 20,
                "evidence_paths": ["url_policy.rules[1]"],
            },
        ],
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_root = Path(temp_dir)

        try:
            ingest_phase1_source(
                NEGATIVE_URL,
                extension_mode="CONTROLLED",
                route_profile="IMPLEMENTATION",
                requested_capabilities=("cap.read",),
                extension_policy=_extension_policy_payload(),
                url_policy=_url_policy_payload(),
                snapshot_root=snapshot_root,
            )
        except UrlSourceRejectedError as exc:
            negative_payload = {
                "normalized_source": exc.rejection.normalized_source,
                "policy_rule_id": exc.rejection.matched_rule_id,
                "rejection_code": exc.rejection.code.value,
                "terminal_status": exc.rejection.terminal_status,
                "detail": exc.rejection.detail,
                "evidence_paths": list(exc.rejection.evidence_paths),
            }
        else:
            raise AssertionError("Negative real source must be rejected")

        ingestion = ingest_phase1_source(
            POSITIVE_URL,
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
            url_policy=_url_policy_payload(),
            snapshot_root=snapshot_root,
        )
        summary = run_phase1_pipeline(
            POSITIVE_URL,
            extension_mode="CONTROLLED",
            route_profile="IMPLEMENTATION",
            requested_capabilities=("cap.read",),
            extension_policy=_extension_policy_payload(),
            url_policy=_url_policy_payload(),
            snapshot_root=snapshot_root,
        )
        uplift = run_uplift_engine(
            ingestion.raw_text,
            source_metadata=ingestion.source_metadata,
        ).as_payload()

    first_ten_lines = ingestion.raw_text.splitlines()[:10]
    context_source = uplift["context"]["source"]
    intent = uplift["intent"]
    positive_payload = {
        "normalized_source": ingestion.source_metadata["normalized_source"],
        "policy_rule_id": ingestion.source_metadata["policy_rule_id"],
        "content_sha256": ingestion.source_metadata["content_sha256"],
        "first_10_lines": first_ten_lines,
        "rendered_summary": summary,
        "uplift_context_source": context_source,
        "uplift_intent": {
            "primary_objective": intent.get("primary_objective"),
            "in_scope": intent.get("in_scope"),
            "out_of_scope": intent.get("out_of_scope"),
        },
    }

    assert negative_payload["rejection_code"] == "URL-INGEST-013-UNSUITABLE-CONTENT"
    assert negative_payload["terminal_status"] == "REJECTED"
    assert positive_payload["normalized_source"] == POSITIVE_URL
    assert positive_payload["policy_rule_id"] == "v1.url.raw-kubernetes-kep-2885"
    assert positive_payload["content_sha256"]
    assert first_ten_lines
    assert "Intent\n- " in summary
    assert len([line for line in summary.splitlines() if line.startswith("- ")]) <= 8
    assert context_source["normalized_source"] == POSITIVE_URL
    assert intent["primary_objective"]
    assert intent["in_scope"]
    assert intent["out_of_scope"]

    print(
        json.dumps(
            {
                "negative_case": negative_payload,
                "positive_case": positive_payload,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
