#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.ingestion.url_policy import UrlSourceRejectedError
from intent_pipeline.pipeline import ingest_phase1_source, run_phase1_pipeline
from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uac_assessment import assess_uac_source, classification_rubric_payload
from intent_pipeline.uac_extract import extract_uac_analysis_text
from intent_pipeline.uac_sources import (
    aggregate_collection_recommendation,
    enumerate_github_tree,
    enumerate_local_directory,
)
from intent_pipeline.uplift.engine import run_uplift_engine


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import a local file, local directory, raw https URL, or GitHub folder/repo URL into the deterministic "
            "UAC intake flow."
        ),
        epilog=(
            "Examples:\n"
            "  python3.11 scripts/uac-import.py --source /abs/path/to/prompt.md\n"
            "  python3.11 scripts/uac-import.py --source /abs/path/to/folder --target-system codex\n"
            "  python3.11 scripts/uac-import.py --source https://raw.githubusercontent.com/org/repo/main/file.md\n"
            "  python3.11 scripts/uac-import.py --source https://github.com/org/repo/tree/main/prompts --show-rubric\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--source", required=True, help="File path, directory path, raw https URL, or GitHub tree/repo URL")
    parser.add_argument(
        "--target-system",
        default="all",
        choices=("auto", "all", "codex", "gemini", "claude", "kiro"),
        help="Preferred output target for packaging guidance",
    )
    parser.add_argument("--max-bytes", type=int, default=262144, help="URL fetch limit when source is remote")
    parser.add_argument("--timeout-seconds", type=int, default=15, help="URL fetch timeout when source is remote")
    parser.add_argument("--max-items", type=int, default=25, help="Maximum files to inspect for folder/repo imports")
    parser.add_argument("--no-recurse", action="store_true", help="Only inspect the immediate directory level for folder imports")
    parser.add_argument("--show-rubric", action="store_true", help="Include the classification rubric in the output")
    return parser.parse_args()


def _looks_like_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_raw_text_url(value: str) -> bool:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        return False
    return parsed.netloc != "github.com"


def _looks_like_wrapper_source(value: str) -> bool:
    suffix = Path(urlsplit(value).path).suffix.casefold()
    return suffix in {".toml", ".json"}


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


def _import_local_file(path: Path, *, target_system: str) -> dict[str, Any]:
    ingestion = ingest_phase1_source(path)
    extraction = extract_uac_analysis_text(ingestion.raw_text, str(path))
    summary = run_phase1_pipeline(path)
    uplift = run_uplift_engine(extraction.analysis_text, source_metadata=ingestion.source_metadata)
    routing = run_semantic_routing(uplift)
    assessment = assess_uac_source(
        ingestion.raw_text,
        analysis_text=extraction.analysis_text,
        source_metadata=ingestion.source_metadata,
        source_hint=path,
    )
    return _success_payload(
        source_metadata=ingestion.source_metadata,
        extraction=extraction.as_payload(),
        summary=summary,
        uplift=uplift.as_payload(),
        routing=routing.as_payload(),
        assessment=assessment.as_payload(),
        target_system=target_system,
    )


def _import_raw_url(source: str, *, max_bytes: int, timeout_seconds: int, target_system: str) -> dict[str, Any]:
    if _looks_like_wrapper_source(source):
        return _import_remote_artifact(source, normalized_source=source, target_system=target_system, timeout_seconds=timeout_seconds)
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
        extraction = extract_uac_analysis_text(ingestion.raw_text, source)
        summary = run_phase1_pipeline(source, **shared_kwargs)
        uplift = run_uplift_engine(extraction.analysis_text, source_metadata=ingestion.source_metadata)
        routing = run_semantic_routing(uplift)
        assessment = assess_uac_source(
            ingestion.raw_text,
            analysis_text=extraction.analysis_text,
            source_metadata=ingestion.source_metadata,
            source_hint=source,
        )
    return _success_payload(
        source_metadata=ingestion.source_metadata,
        extraction=extraction.as_payload(),
        summary=summary,
        uplift=uplift.as_payload(),
        routing=routing.as_payload(),
        assessment=assessment.as_payload(),
        target_system=target_system,
    )


def _import_remote_artifact(
    raw_url: str,
    *,
    normalized_source: str,
    target_system: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    raw_text = _fetch_remote_text(raw_url, timeout_seconds=timeout_seconds)
    source_metadata = {
        "source_type": "URL",
        "normalized_source": normalized_source,
        "policy_rule_id": _policy_rule_id(raw_url),
        "content_type": mimetypes.guess_type(urlsplit(raw_url).path)[0] or "text/plain",
        "content_sha256": sha256(raw_text.encode("utf-8")).hexdigest(),
    }
    extraction = extract_uac_analysis_text(raw_text, raw_url)
    uplift = run_uplift_engine(extraction.analysis_text, source_metadata=source_metadata)
    routing = run_semantic_routing(uplift)
    assessment = assess_uac_source(
        raw_text,
        analysis_text=extraction.analysis_text,
        source_metadata=source_metadata,
        source_hint=normalized_source,
    )
    summary = run_phase1_pipeline_from_text(extraction.analysis_text)
    return _success_payload(
        source_metadata=source_metadata,
        extraction=extraction.as_payload(),
        summary=summary,
        uplift=uplift.as_payload(),
        routing=routing.as_payload(),
        assessment=assessment.as_payload(),
        target_system=target_system,
    )


def _import_local_directory(
    directory: Path,
    *,
    recurse: bool,
    max_items: int,
    target_system: str,
) -> dict[str, Any]:
    candidates = enumerate_local_directory(directory, recurse=recurse, max_items=max_items)
    item_payloads = [_import_local_file(Path(candidate.locator), target_system=target_system) for candidate in candidates]
    recommendation = aggregate_collection_recommendation(directory.name, item_payloads)
    return {
        "status": "accepted",
        "source": {
            "type": "LOCAL_DIRECTORY",
            "normalized_source": str(directory),
            "item_count": len(item_payloads),
        },
        "collection": recommendation.as_payload(),
        "items": [_compact_item_payload(candidate.display_name, item) for candidate, item in zip(candidates, item_payloads)],
    }


def _import_github_tree(
    source: str,
    *,
    recurse: bool,
    max_items: int,
    timeout_seconds: int,
    target_system: str,
) -> dict[str, Any]:
    tree_ref, candidates = enumerate_github_tree(source, recurse=recurse, max_items=max_items, timeout_seconds=timeout_seconds)
    item_payloads = [
        _import_remote_artifact(
            candidate.locator,
            normalized_source=candidate.normalized_source,
            target_system=target_system,
            timeout_seconds=timeout_seconds,
        )
        for candidate in candidates
    ]
    source_label = Path(tree_ref.path).name or tree_ref.repo
    recommendation = aggregate_collection_recommendation(source_label, item_payloads)
    return {
        "status": "accepted",
        "source": {
            "type": "GITHUB_TREE",
            "normalized_source": tree_ref.normalized_source,
            "owner": tree_ref.owner,
            "repo": tree_ref.repo,
            "ref": tree_ref.ref,
            "path": tree_ref.path,
            "item_count": len(item_payloads),
        },
        "collection": recommendation.as_payload(),
        "items": [_compact_item_payload(candidate.display_name, item) for candidate, item in zip(candidates, item_payloads)],
    }


def _compact_item_payload(display_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "display_name": display_name,
        "status": payload.get("status"),
    }
    if payload.get("status") == "accepted":
        compact.update(
            {
                "source": payload["source"],
                "extraction": payload.get("extraction"),
                "summary": payload["summary"],
                "uplift": payload["uplift"],
                "routing": payload["routing"],
                "uac": payload["uac"],
                "recommendation": payload["recommendation"],
            }
        )
    else:
        compact["rejection"] = payload.get("rejection")
    return compact


def _success_payload(
    *,
    source_metadata: dict[str, str],
    extraction: dict[str, str | None],
    summary: str,
    uplift: dict[str, Any],
    routing: dict[str, Any],
    assessment: dict[str, Any],
    target_system: str,
) -> dict[str, Any]:
    return {
        "status": "accepted",
        "source": {
            "type": source_metadata["source_type"],
            "normalized_source": source_metadata["normalized_source"],
            "policy_rule_id": source_metadata["policy_rule_id"],
            "content_type": source_metadata["content_type"],
            "content_sha256": source_metadata["content_sha256"],
        },
        "extraction": extraction,
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
            "rubric": assessment["rubric"],
            "scorecard": assessment["scorecard"],
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


def _fetch_remote_text(url: str, *, timeout_seconds: int) -> str:
    request = Request(url, headers={"User-Agent": "core-prompts-uac-import"})
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8")


def run_phase1_pipeline_from_text(text: str) -> str:
    from intent_pipeline.sanitization.pipeline import sanitize_two_pass
    from intent_pipeline.summary.renderer import render_intent_summary

    sanitized = sanitize_two_pass(text)
    return render_intent_summary(sanitized)


def main() -> int:
    args = _parse_args()
    source = args.source.strip()
    try:
        if _looks_like_url(source) and not _is_raw_text_url(source):
            payload = _import_github_tree(
                source,
                recurse=not args.no_recurse,
                max_items=args.max_items,
                timeout_seconds=args.timeout_seconds,
                target_system=args.target_system,
            )
        elif _looks_like_url(source):
            payload = _import_raw_url(
                source,
                max_bytes=args.max_bytes,
                timeout_seconds=args.timeout_seconds,
                target_system=args.target_system,
            )
        else:
            path = Path(source).expanduser().resolve()
            if path.is_dir():
                payload = _import_local_directory(
                    path,
                    recurse=not args.no_recurse,
                    max_items=args.max_items,
                    target_system=args.target_system,
                )
            elif path.is_file():
                payload = _import_local_file(path, target_system=args.target_system)
            else:
                raise SystemExit(f"uac-import.py requires a file path, directory path, raw https URL, or GitHub folder URL. Got: {path}")
    except UrlSourceRejectedError as error:
        payload = _rejection_payload(source, error)

    if args.show_rubric:
        payload["classification_rubric"] = classification_rubric_payload()

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
