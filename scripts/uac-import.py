#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.pipeline import ingest_phase1_source, run_phase1_pipeline
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uac_assessment import assess_uac_source
from intent_pipeline.uplift.engine import run_uplift_engine


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import one local prompt/spec file or one raw https URL into the deterministic UAC "
            "ingestion, uplift, routing, and packaging assessment flow."
        )
    )
    parser.add_argument("--source", required=True, help="Absolute/relative file path or raw https URL")
    parser.add_argument(
        "--target-system",
        default="all",
        choices=("auto", "all", "codex", "gemini", "claude", "kiro"),
        help="Preferred output target for packaging guidance",
    )
    parser.add_argument("--max-bytes", type=int, default=262144, help="URL fetch limit when source is remote")
    parser.add_argument("--timeout-seconds", type=int, default=15, help="URL fetch timeout when source is remote")
    return parser.parse_args()


def _looks_like_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


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


def _url_policy_payload(url: str, *, max_bytes: int, timeout_seconds: int) -> dict[str, object]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SystemExit("uac-import.py requires raw https URLs for remote imports")
    return {
        "schema_version": "1.0.0",
        "rules": [
            {
                "rule_id": _policy_rule_id(url),
                "allowed_schemes": ["https"],
                "allowed_hosts": [parsed.hostname],
                "allowed_domains": [],
                "allowed_path_prefixes": [parsed.path or "/"],
                "allowed_content_types": ["text/plain", "text/markdown"],
                "max_bytes": max_bytes,
                "redirect_limit": 2,
                "timeout_seconds": timeout_seconds,
                "priority": 10,
                "evidence_paths": ["url_policy.rules[0]"],
            }
        ],
    }


def _policy_rule_id(url: str) -> str:
    from hashlib import sha256

    digest = sha256(url.encode("utf-8")).hexdigest()[:12]
    host = (urlsplit(url).hostname or "unknown").replace(".", "-")
    return f"v1.url.{host}.{digest}"


def _target_systems(target_system: str, *, recommended_surface: str) -> list[str]:
    if target_system == "all":
        return ["codex", "gemini", "claude", "kiro"]
    if target_system == "auto":
        if recommended_surface == "agent":
            return ["codex", "gemini", "claude", "kiro"]
        return ["codex", "gemini", "claude", "kiro"]
    return [target_system]


def _import_local(path: Path) -> dict[str, Any]:
    ingestion = ingest_phase1_source(path)
    summary = run_phase1_pipeline(path)
    uplift = run_uplift_engine(ingestion.raw_text, source_metadata=ingestion.source_metadata)
    routing = run_semantic_routing(uplift)
    assessment = assess_uac_source(
        ingestion.raw_text,
        source_metadata=ingestion.source_metadata,
        source_hint=path,
    )
    return _success_payload(
        ingestion,
        summary,
        uplift.as_payload(),
        routing.as_payload(),
        assessment.as_payload(),
        target_system="all",
    )


def _import_url(source: str, *, max_bytes: int, timeout_seconds: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_root = Path(temp_dir) / "snapshots"
        shared_kwargs = {
            "extension_mode": "CONTROLLED",
            "route_profile": "IMPLEMENTATION",
            "requested_capabilities": ("cap.read",),
            "extension_policy": _extension_policy_payload(),
            "url_policy": _url_policy_payload(source, max_bytes=max_bytes, timeout_seconds=timeout_seconds),
            "snapshot_root": snapshot_root,
        }
        ingestion = ingest_phase1_source(source, **shared_kwargs)
        summary = run_phase1_pipeline(source, **shared_kwargs)
        uplift = run_uplift_engine(ingestion.raw_text, source_metadata=ingestion.source_metadata)
        routing = run_semantic_routing(uplift)
        assessment = assess_uac_source(
            ingestion.raw_text,
            source_metadata=ingestion.source_metadata,
            source_hint=source,
        )
    return _success_payload(
        ingestion,
        summary,
        uplift.as_payload(),
        routing.as_payload(),
        assessment.as_payload(),
        target_system="all",
    )


def _success_payload(
    ingestion,
    summary: str,
    uplift: dict[str, Any],
    routing: dict[str, Any],
    assessment: dict[str, Any],
    *,
    target_system: str,
) -> dict[str, Any]:
    return {
        "status": "accepted",
        "source": {
            "type": ingestion.source_metadata["source_type"],
            "normalized_source": ingestion.source_metadata["normalized_source"],
            "policy_rule_id": ingestion.source_metadata["policy_rule_id"],
            "content_type": ingestion.source_metadata["content_type"],
            "content_sha256": ingestion.source_metadata["content_sha256"],
        },
        "summary": summary,
        "uplift": {
            "primary_objective": uplift["intent"].get("primary_objective"),
            "in_scope": uplift["intent"].get("in_scope"),
            "out_of_scope": uplift["intent"].get("out_of_scope"),
            "quality_constraints": uplift["intent"].get("quality_constraints"),
        },
        "routing": {
            "decision": routing["route_selection"]["decision"],
            "route_profile": routing["route_selection"]["route_profile"],
            "dominant_rule_id": routing["route_selection"]["dominant_rule_id"],
            "missing_evidence": routing["route_selection"]["missing_evidence"],
        },
        "uac": {
            "content_kind": assessment["content_kind"],
            "recommended_surface": assessment["recommended_surface"],
            "confidence": assessment["confidence"],
            "signals": assessment["signals"],
            "rationale": assessment["rationale"],
            "modernization_focus": assessment["modernization_focus"],
            "target_systems": assessment["target_systems"],
        },
        "recommendation": {
            "primary_target_systems": _target_systems(
                target_system,
                recommended_surface=str(assessment["recommended_surface"]),
            ),
            "next_actions": _next_actions(
                assessment["recommended_surface"],
                routing["route_selection"]["route_profile"],
            ),
        },
    }


def _next_actions(recommended_surface: str, route_profile: str) -> list[str]:
    if recommended_surface == "agent":
        return [
            "Preserve control-plane instructions and explicit tool boundaries.",
            "Emit target agent registrations only where the platform supports agents.",
            f"Carry forward route profile {route_profile} as the default execution bias.",
        ]
    if recommended_surface == "skill":
        return [
            "Normalize into one canonical skill/command source file.",
            "Preserve explicit examples, constraints, and expected output sections.",
            f"Use route profile {route_profile} to guide target-system packaging defaults.",
        ]
    return [
        "Review manually before packaging.",
        "Add explicit objective/scope markers if you want deterministic uplift.",
        "Separate executable prompt text from surrounding config or prose.",
    ]


def _rejection_payload(source: str, error: UrlSourceRejectedError) -> dict[str, Any]:
    rejection = error.rejection
    return {
        "status": "rejected",
        "source": {
            "type": "URL",
            "normalized_source": rejection.normalized_source,
            "policy_rule_id": rejection.matched_rule_id,
        },
        "rejection": {
            "code": rejection.code,
            "terminal_status": rejection.terminal_status,
            "detail": rejection.detail,
            "evidence_paths": list(rejection.evidence_paths),
        },
        "recommendation": {
            "next_actions": [
                "Use a prompt/spec-like source with explicit objectives, scope, or constraints.",
                "Do not attempt packaging until the suitability gate accepts the source.",
            ]
        },
        "requested_source": source,
    }


def main() -> int:
    args = _parse_args()
    source = args.source.strip()
    try:
        if _looks_like_url(source):
            payload = _import_url(
                source,
                max_bytes=args.max_bytes,
                timeout_seconds=args.timeout_seconds,
            )
        else:
            path = Path(source).expanduser().resolve()
            if not path.is_file():
                raise SystemExit(f"uac-import.py currently requires a file path, got: {path}")
            payload = _import_local(path)
    except UrlSourceRejectedError as error:
        payload = _rejection_payload(source, error)

    if payload.get("status") == "accepted":
        payload["recommendation"]["primary_target_systems"] = _target_systems(
            args.target_system,
            recommended_surface=str(payload["uac"]["recommended_surface"]),
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
