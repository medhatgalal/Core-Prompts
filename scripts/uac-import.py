#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import json
import mimetypes
import subprocess
import sys
import tempfile
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
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
from intent_pipeline.uac_benchmarks import benchmark_search, should_search_benchmarks
from intent_pipeline.uac_capabilities import deployment_matrix_payload, emitted_surfaces_by_cli, recommended_target_systems
from intent_pipeline.uac_descriptors import build_descriptor, save_descriptor, write_source_note
from intent_pipeline.uac_extract import extract_uac_analysis_text
from intent_pipeline.uac_manifest import analyze_manifest_fit, build_capability_manifest, orchestrator_handoff_payload
from intent_pipeline.uac_quality import (
    build_quality_plan,
    latest_quality_review_path,
    load_quality_profile,
    quality_descriptor_fields,
    quality_profile_dir,
    quality_review_dir,
    quality_review_path,
    render_latest_review_markdown,
    run_quality_loop,
)
from intent_pipeline.uac_baselines import persist_source_baseline
from intent_pipeline.uac_templates import load_capability_template
from intent_pipeline.uac_repomix import collect_repomix_candidates, materialize_repomix_candidate, repomix_available
from intent_pipeline.uac_sources import (
    UacSourceCandidate,
    aggregate_collection_recommendation,
    cluster_source_candidates,
    enumerate_github_tree,
    enumerate_local_directory,
)
from intent_pipeline.uac_ssot import build_ssot_manifest_entry, build_ssot_handoff_contract, load_ssot_entries
from intent_pipeline.uplift.engine import run_uplift_engine


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Capability Fabric UAC shell. Best used through an AI assistant turn-by-turn, but fully scriptable from shell. '
            'import/plan analyze sources without mutation, apply writes canonical SSOT plus descriptor metadata, and deploy remains separate.'
        ),
        epilog=(
            'Examples:\n'
            '  python3 scripts/uac-import.py --mode import --source /abs/path/to/prompt.md\n'
            '  python3 scripts/uac-import.py --mode plan --source /abs/path/to/folder\n'
            '  python3 scripts/uac-import.py --mode judge --source /abs/path/to/folder --quality-profile architecture\n'
            '  python3 scripts/uac-import.py --mode apply --source /abs/path/to/folder --yes\n'
            '  python3 scripts/uac-import.py --mode import --source https://github.com/org/repo/tree/main/prompts\n'
            '  python3 scripts/uac-import.py --mode audit --output table\n'
            '  python3 scripts/uac-import.py --mode explain --output table\n'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('--mode', choices=('import', 'audit', 'explain', 'plan', 'judge', 'apply'), default='import')
    parser.add_argument('--source', action='append', help='File path, directory path, raw https URL, GitHub tree/repo URL, or repomix-reducible repo source')
    parser.add_argument(
        '--target-system',
        default='all',
        choices=('auto', 'all', 'codex', 'gemini', 'claude', 'kiro'),
        help='Preferred output target for packaging guidance',
    )
    parser.add_argument(
        '--install-target',
        default='auto',
        choices=('auto', 'global', 'repo_local', 'both'),
        help='Installation scope. auto infers and apply always requires confirmation before mutation.',
    )
    parser.add_argument('--max-bytes', type=int, default=262144, help='URL fetch limit when source is remote')
    parser.add_argument('--timeout-seconds', type=int, default=15, help='URL fetch timeout when source is remote')
    parser.add_argument('--max-items', type=int, default=25, help='Maximum files to inspect for folder/repo imports')
    parser.add_argument('--no-recurse', action='store_true', help='Only inspect the immediate directory level for folder imports')
    parser.add_argument('--show-rubric', action='store_true', help='Include the classification rubric in the output')
    parser.add_argument('--output', choices=('json', 'table'), default='json', help='Render output as JSON or a human-readable table where supported')
    parser.add_argument('--yes', action='store_true', help='Confirm repo-mutating apply without interactive prompt')
    parser.add_argument(
        '--benchmark-search',
        choices=('auto', 'always', 'off'),
        default='auto',
        help='Search GitHub/Google/X for comparable sources when uplifting generic or low-fit families',
    )
    parser.add_argument(
        '--use-repomix',
        choices=('auto', 'always', 'off'),
        default='auto',
        help='Use repomix to reduce broad repos/folders before UAC analysis when available',
    )
    parser.add_argument(
        '--quality-loop',
        choices=('on', 'off'),
        default='on',
        help='Run the built-in quality iteration loop for plan, judge, and apply',
    )
    parser.add_argument(
        '--quality-profile',
        default='auto',
        help='Quality profile to use for judging and apply. auto selects by slug/family.',
    )
    parser.add_argument(
        '--max-quality-passes',
        type=int,
        default=10,
        help='Maximum quality passes for the built-in judge loop',
    )
    return parser.parse_args()


def _looks_like_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def _is_raw_text_url(value: str) -> bool:
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.netloc:
        return False
    return parsed.netloc != 'github.com'


def _looks_like_wrapper_source(value: str) -> bool:
    suffix = Path(urlsplit(value).path).suffix.casefold()
    return suffix in {'.toml', '.json'}


def _extension_policy_payload() -> dict[str, object]:
    return {
        'schema_version': '1.0.0',
        'extension_mode': 'CONTROLLED',
        'rules': [
            {
                'rule_id': 'v1.url.allow',
                'source_kind': 'URL',
                'decision': 'ALLOW',
                'priority': 10,
                'evidence_paths': ['policy_contract.rules[0]'],
            }
        ],
    }


def _url_policy_payload(url: str, *, max_bytes: int, timeout_seconds: int) -> dict[str, object]:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname:
        raise SystemExit('uac-import.py requires raw https URLs for remote imports')
    return {
        'schema_version': '1.0.0',
        'rules': [
            {
                'rule_id': _policy_rule_id(url),
                'allowed_schemes': ['https'],
                'allowed_hosts': [parsed.hostname],
                'allowed_domains': [],
                'allowed_path_prefixes': [parsed.path or '/'],
                'allowed_content_types': ['text/plain', 'text/markdown'],
                'max_bytes': max_bytes,
                'redirect_limit': 2,
                'timeout_seconds': timeout_seconds,
                'priority': 10,
                'evidence_paths': ['url_policy.rules[0]'],
            }
        ],
    }


def _policy_rule_id(url: str) -> str:
    digest = sha256(url.encode('utf-8')).hexdigest()[:12]
    host = (urlsplit(url).hostname or 'unknown').replace('.', '-')
    return f'v1.url.{host}.{digest}'


def _existing_manifests() -> list[dict[str, object]]:
    return [build_ssot_manifest_entry(entry, ROOT) for entry in load_ssot_entries(ROOT / 'ssot')]


def _analyze_text_source(
    *,
    slug: str,
    raw_text: str,
    source_metadata: dict[str, str],
    source_hint: str | Path,
    summary: str,
    target_system: str,
    install_target: str,
    benchmark_policy: str,
    collection_type: str | None = None,
) -> dict[str, Any]:
    extraction = extract_uac_analysis_text(raw_text, str(source_hint))
    uplift = run_uplift_engine(extraction.analysis_text, source_metadata=source_metadata)
    uplift_payload = uplift.as_payload()
    routing = run_semantic_routing(uplift)
    routing_payload = routing.as_payload()
    assessment = assess_uac_source(
        raw_text,
        analysis_text=extraction.analysis_text,
        source_metadata=source_metadata,
        source_hint=source_hint,
    ).as_payload()
    manifest = build_capability_manifest(
        slug=slug,
        source_metadata=source_metadata,
        raw_text=raw_text,
        summary=summary,
        assessment_payload=assessment,
        uplift_payload=uplift_payload,
        routing_payload=routing_payload,
        repo_root=ROOT,
    )
    cross_analysis = analyze_manifest_fit(manifest, _existing_manifests()).as_payload()
    manifest['layers']['expanded']['overlap_candidates'] = [
        item['slug'] for item in cross_analysis['overlap_report'] if isinstance(item, dict) and item.get('slug')
    ]
    install = manifest['layers']['minimal']['install_target']
    if install_target != 'auto':
        install['recommended'] = install_target
        install['rationale'] = f'user override requested {install_target}'
        install['confidence'] = 1.0
    capability_type = str(assessment['capability_type'])
    if cross_analysis['fit_assessment'] == 'manual_review' and capability_type != 'manual_review':
        assessment = dict(assessment)
        assessment['capability_type'] = 'manual_review'
        assessment['recommended_surface'] = 'manual_review'
        assessment['deployment_intent'] = 'hold_for_review'
        manifest['layers']['minimal']['capability_type'] = 'manual_review'
        manifest['layers']['minimal']['review_status'] = 'manual_review'
    benchmark_sources = _benchmark_payloads(
        slug=slug,
        fit_assessment=str(cross_analysis['fit_assessment']),
        collection_type=collection_type,
        query=f'{slug} prompt library',
        policy=benchmark_policy,
    )
    return {
        'status': 'accepted',
        'source': {
            'type': source_metadata['source_type'],
            'normalized_source': source_metadata['normalized_source'],
            'policy_rule_id': source_metadata['policy_rule_id'],
            'content_type': source_metadata['content_type'],
            'content_sha256': source_metadata['content_sha256'],
        },
        'extraction': extraction.as_payload(),
        'summary': summary,
        'uplift': {
            'primary_objective': uplift_payload['intent'].get('primary_objective'),
            'in_scope': uplift_payload['intent'].get('in_scope'),
            'out_of_scope': uplift_payload['intent'].get('out_of_scope'),
            'quality_constraints': uplift_payload['intent'].get('quality_constraints'),
        },
        'routing': {
            'decision': routing_payload['route_selection']['decision'],
            'route_profile': routing_payload['route_selection']['route_profile'],
            'dominant_rule_id': routing_payload['route_selection']['dominant_rule_id'],
            'missing_evidence': routing_payload['route_selection']['missing_evidence'],
        },
        'uac': {
            'content_kind': assessment['content_kind'],
            'capability_type': assessment['capability_type'],
            'recommended_surface': assessment['recommended_surface'],
            'confidence': assessment['confidence'],
            'signals': assessment['signals'],
            'rationale': assessment['rationale'],
            'rubric': assessment['rubric'],
            'deployment_matrix': assessment['deployment_matrix'],
            'scorecard': assessment['scorecard'],
            'emitted_surfaces': assessment['emitted_surfaces'],
            'deployment_intent': assessment['deployment_intent'],
            'modernization_focus': assessment['modernization_focus'],
            'target_systems': assessment['target_systems'],
        },
        'manifest': manifest,
        'cross_analysis': cross_analysis,
        'benchmark_sources': benchmark_sources,
        'handoff_contract': orchestrator_handoff_payload([manifest]),
        'recommendation': {
            'primary_target_systems': recommended_target_systems(target_system, assessment['capability_type']),
            'install_target': manifest['layers']['minimal']['install_target'],
            'next_actions': _next_actions(assessment['capability_type'], routing_payload['route_selection']['route_profile'], cross_analysis['fit_assessment']),
        },
    }


def _import_local_file(path: Path, *, target_system: str, install_target: str, benchmark_policy: str) -> dict[str, Any]:
    ingestion = ingest_phase1_source(path)
    summary = run_phase1_pipeline(path)
    return _analyze_text_source(
        slug=_slugify(path.stem),
        raw_text=ingestion.raw_text,
        source_metadata=ingestion.source_metadata,
        source_hint=path,
        summary=summary,
        target_system=target_system,
        install_target=install_target,
        benchmark_policy=benchmark_policy,
    )


def _import_raw_url(source: str, *, max_bytes: int, timeout_seconds: int, target_system: str, install_target: str, benchmark_policy: str) -> dict[str, Any]:
    if _looks_like_wrapper_source(source):
        return _import_remote_artifact(
            source,
            normalized_source=source,
            target_system=target_system,
            timeout_seconds=timeout_seconds,
            install_target=install_target,
            benchmark_policy=benchmark_policy,
        )
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_root = Path(temp_dir) / 'snapshots'
        shared_kwargs = {
            'extension_mode': 'CONTROLLED',
            'route_profile': 'IMPLEMENTATION',
            'requested_capabilities': ('cap.read',),
            'extension_policy': _extension_policy_payload(),
            'url_policy': _url_policy_payload(source, max_bytes=max_bytes, timeout_seconds=timeout_seconds),
            'snapshot_root': snapshot_root,
        }
        ingestion = ingest_phase1_source(source, **shared_kwargs)
        summary = run_phase1_pipeline(source, **shared_kwargs)
    return _analyze_text_source(
        slug=_slugify(Path(urlsplit(source).path).stem or 'remote-source'),
        raw_text=ingestion.raw_text,
        source_metadata=ingestion.source_metadata,
        source_hint=source,
        summary=summary,
        target_system=target_system,
        install_target=install_target,
        benchmark_policy=benchmark_policy,
    )


def _import_remote_artifact(
    raw_url: str,
    *,
    normalized_source: str,
    target_system: str,
    timeout_seconds: int,
    install_target: str,
    benchmark_policy: str,
) -> dict[str, Any]:
    raw_text = _fetch_remote_text(raw_url, timeout_seconds=timeout_seconds)
    source_metadata = {
        'source_type': 'URL',
        'normalized_source': normalized_source,
        'policy_rule_id': _policy_rule_id(raw_url),
        'content_type': mimetypes.guess_type(urlsplit(raw_url).path)[0] or 'text/plain',
        'content_sha256': sha256(raw_text.encode('utf-8')).hexdigest(),
    }
    return _analyze_text_source(
        slug=_slugify(Path(urlsplit(normalized_source).path).stem or 'remote-artifact'),
        raw_text=raw_text,
        source_metadata=source_metadata,
        source_hint=normalized_source,
        summary=run_phase1_pipeline_from_text(raw_text),
        target_system=target_system,
        install_target=install_target,
        benchmark_policy=benchmark_policy,
    )


def _repomix_candidates_for_source(source: str, args: argparse.Namespace) -> tuple[list[UacSourceCandidate], dict[str, Path]]:
    if args.use_repomix == 'off' or not repomix_available():
        return [], {}
    should_use = args.use_repomix == 'always'
    if args.use_repomix == 'auto':
        if _looks_like_url(source) and not _is_raw_text_url(source):
            should_use = True
        else:
            path = Path(source).expanduser()
            should_use = path.is_dir() and any((path / name).exists() for name in ('commands', 'prompts', 'skills', 'agents', '.git'))
    if not should_use:
        return [], {}
    repomix_candidates = collect_repomix_candidates(source, max_items=max(args.max_items * 2, 50))
    if not repomix_candidates:
        return [], {}
    temp_paths: dict[str, Path] = {}
    candidates: list[UacSourceCandidate] = []
    for candidate in repomix_candidates[: args.max_items * 2]:
        materialized = materialize_repomix_candidate(candidate)
        temp_paths[candidate.path] = materialized
        candidates.append(
            UacSourceCandidate(
                source_type='REPOMIX_FILE',
                display_name=candidate.path,
                normalized_source=f'repomix://{source}/{candidate.path}',
                locator=str(materialized),
            )
        )
    return candidates[: args.max_items], temp_paths


def _collection_manifest(
    source_label: str,
    source_type: str,
    normalized_source: str,
    collection: dict[str, Any],
    item_payloads: list[dict[str, Any]],
    install_target: str,
    benchmark_policy: str,
) -> dict[str, object]:
    capability_type = str(collection['capability_type'])
    combined_text = '\n\n'.join(str(item.get('summary', '')) for item in item_payloads if item.get('status') == 'accepted')
    assessment = {
        'capability_type': capability_type,
        'recommended_surface': capability_type,
        'confidence': 0.84 if capability_type != 'manual_review' else 0.55,
        'signals': ['collection-level recommendation'],
        'rationale': collection['rationale'],
        'rubric': classification_rubric_payload(),
        'deployment_matrix': deployment_matrix_payload(),
        'scorecard': {'accepted_item_count': len([item for item in item_payloads if item.get('status') == 'accepted'])},
        'emitted_surfaces': {cli: list(values) for cli, values in emitted_surfaces_by_cli(capability_type).items() if values},
        'deployment_intent': 'generate' if capability_type != 'manual_review' else 'hold_for_review',
        'modernization_focus': [
            'normalize family-level objectives and constraints',
            'deduplicate overlapping modes',
            'preserve per-item specialization under one canonical family',
        ],
        'target_systems': ['codex', 'gemini', 'claude', 'kiro'],
        'content_kind': collection['collection_type'],
    }
    manifest = build_capability_manifest(
        slug=_slugify(collection.get('recommended_slug') or source_label),
        source_metadata={
            'source_type': source_type,
            'normalized_source': normalized_source,
            'policy_rule_id': f'collection.{_slugify(source_label)}',
            'content_type': 'text/plain',
            'content_sha256': sha256(combined_text.encode('utf-8')).hexdigest(),
        },
        raw_text=combined_text,
        summary=collection['rationale'],
        assessment_payload=assessment,
        uplift_payload={'primary_objective': None, 'in_scope': [], 'out_of_scope': [], 'quality_constraints': []},
        routing_payload={'route_profile': 'COLLECTION_REVIEW'},
        repo_root=ROOT,
    )
    cross_analysis = analyze_manifest_fit(manifest, _existing_manifests()).as_payload()
    manifest['layers']['expanded']['overlap_candidates'] = [
        item['slug'] for item in cross_analysis['overlap_report'] if isinstance(item, dict) and item.get('slug')
    ]
    install = manifest['layers']['minimal']['install_target']
    if install_target != 'auto':
        install['recommended'] = install_target
        install['rationale'] = f'user override requested {install_target}'
        install['confidence'] = 1.0
    benchmark_sources = _benchmark_payloads(
        slug=_slugify(collection.get('recommended_slug') or source_label),
        fit_assessment=str(cross_analysis['fit_assessment']),
        collection_type=str(collection['collection_type']),
        query=f"{source_label} prompt library",
        policy=benchmark_policy,
    )
    return {
        'manifest': manifest,
        'cross_analysis': cross_analysis,
        'benchmark_sources': benchmark_sources,
    }


def _import_local_directory(directory: Path, *, recurse: bool, max_items: int, target_system: str, install_target: str, benchmark_policy: str, args: argparse.Namespace) -> dict[str, Any]:
    repomix_candidates, _ = _repomix_candidates_for_source(str(directory), args)
    candidates = repomix_candidates or enumerate_local_directory(directory, recurse=recurse, max_items=max_items)
    item_payloads = [_process_candidate(candidate, target_system=target_system, install_target=install_target, benchmark_policy=benchmark_policy) for candidate in candidates]
    return _collection_or_cluster_payload(directory.name, 'LOCAL_DIRECTORY', str(directory), candidates, item_payloads, install_target, benchmark_policy)


def _import_github_tree(source: str, *, recurse: bool, max_items: int, timeout_seconds: int, target_system: str, install_target: str, benchmark_policy: str, args: argparse.Namespace) -> dict[str, Any]:
    repomix_candidates, _ = _repomix_candidates_for_source(source, args)
    if repomix_candidates:
        candidates = repomix_candidates[:max_items]
        normalized_source = source
        source_label = Path(urlsplit(source).path).name or 'github-source'
    else:
        tree_ref, candidates = enumerate_github_tree(source, recurse=recurse, max_items=max_items, timeout_seconds=timeout_seconds)
        normalized_source = tree_ref.normalized_source
        source_label = Path(tree_ref.path).name or tree_ref.repo
    item_payloads = [
        _process_candidate(candidate, target_system=target_system, install_target=install_target, benchmark_policy=benchmark_policy, timeout_seconds=timeout_seconds)
        for candidate in candidates
    ]
    return _collection_or_cluster_payload(source_label, 'GITHUB_TREE', normalized_source, candidates, item_payloads, install_target, benchmark_policy)


def _process_candidate(
    candidate: UacSourceCandidate,
    *,
    target_system: str,
    install_target: str,
    benchmark_policy: str,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    if candidate.source_type == 'LOCAL_FILE':
        return _import_local_file(Path(candidate.locator), target_system=target_system, install_target=install_target, benchmark_policy=benchmark_policy)
    if candidate.source_type == 'REPOMIX_FILE':
        raw_text = Path(candidate.locator).read_text(encoding='utf-8')
        source_metadata = {
            'source_type': 'REPOMIX_FILE',
            'normalized_source': candidate.normalized_source,
            'policy_rule_id': f"repomix.{_slugify(candidate.display_name)}",
            'content_type': mimetypes.guess_type(candidate.display_name)[0] or 'text/plain',
            'content_sha256': sha256(raw_text.encode('utf-8')).hexdigest(),
        }
        return _analyze_text_source(
            slug=_slugify(Path(candidate.display_name).stem),
            raw_text=raw_text,
            source_metadata=source_metadata,
            source_hint=candidate.display_name,
            summary=run_phase1_pipeline_from_text(raw_text),
            target_system=target_system,
            install_target=install_target,
            benchmark_policy=benchmark_policy,
        )
    return _import_remote_artifact(
        candidate.locator,
        normalized_source=candidate.normalized_source,
        target_system=target_system,
        timeout_seconds=timeout_seconds,
        install_target=install_target,
        benchmark_policy=benchmark_policy,
    )


def _collection_or_cluster_payload(
    source_label: str,
    source_type: str,
    normalized_source: str,
    candidates: list[UacSourceCandidate],
    item_payloads: list[dict[str, Any]],
    install_target: str,
    benchmark_policy: str,
) -> dict[str, Any]:
    clusters = cluster_source_candidates(candidates)
    payload_items = [_compact_item_payload(candidate.display_name, item) for candidate, item in zip(candidates, item_payloads)]
    if len(clusters) > 1:
        grouped_items: dict[str, list[tuple[UacSourceCandidate, dict[str, Any]]]] = defaultdict(list)
        by_display = {candidate.display_name: item for candidate, item in zip(candidates, item_payloads)}
        for cluster in clusters:
            for candidate in cluster.candidates:
                grouped_items[cluster.slug].append((candidate, by_display[candidate.display_name]))
        cluster_payloads = []
        for cluster in clusters:
            entries = grouped_items[cluster.slug]
            cluster_items = [item for _, item in entries]
            recommendation = aggregate_collection_recommendation(cluster.label, cluster_items)
            collection_bits = _collection_manifest(cluster.label, source_type, normalized_source, recommendation.as_payload(), cluster_items, install_target, benchmark_policy)
            cluster_payloads.append(
                {
                    'slug': cluster.slug,
                    'label': cluster.label,
                    'collection': recommendation.as_payload(),
                    'manifest': collection_bits['manifest'],
                    'cross_analysis': collection_bits['cross_analysis'],
                    'benchmark_sources': collection_bits['benchmark_sources'],
                    'items': [_compact_item_payload(candidate.display_name, item) for candidate, item in entries],
                }
            )
        top_collection = aggregate_collection_recommendation(source_label, item_payloads)
        top_bits = _collection_manifest(source_label, source_type, normalized_source, top_collection.as_payload(), item_payloads, install_target, benchmark_policy)
        return {
            'status': 'accepted',
            'source': {
                'type': source_type,
                'normalized_source': normalized_source,
                'item_count': len(item_payloads),
                'cluster_count': len(cluster_payloads),
            },
            'collection': top_collection.as_payload(),
            'manifest': top_bits['manifest'],
            'cross_analysis': top_bits['cross_analysis'],
            'benchmark_sources': top_bits['benchmark_sources'],
            'handoff_contract': orchestrator_handoff_payload([item['manifest'] for item in cluster_payloads]),
            'clusters': cluster_payloads,
            'items': payload_items,
            'plan': {
                'proposed_ssot_slug': _slugify(source_label),
                'collection_type': 'mixed_review',
                'family_recommendations': [
                    {
                        'slug': cluster['slug'],
                        'label': cluster['label'],
                        'capability_type': cluster['collection']['capability_type'],
                        'recommended_slug': cluster['collection']['recommended_slug'],
                    }
                    for cluster in cluster_payloads
                ],
                'install_target': top_bits['manifest']['layers']['minimal']['install_target'],
                'action': 'narrow to one family before apply',
            },
        }
    recommendation = aggregate_collection_recommendation(source_label, item_payloads)
    collection_bits = _collection_manifest(source_label, source_type, normalized_source, recommendation.as_payload(), item_payloads, install_target, benchmark_policy)
    return {
        'status': 'accepted',
        'source': {
            'type': source_type,
            'normalized_source': normalized_source,
            'item_count': len(item_payloads),
        },
        'collection': recommendation.as_payload(),
        'manifest': collection_bits['manifest'],
        'cross_analysis': collection_bits['cross_analysis'],
        'benchmark_sources': collection_bits['benchmark_sources'],
        'handoff_contract': orchestrator_handoff_payload([collection_bits['manifest']]),
        'items': payload_items,
        'plan': _collection_plan(source_label, recommendation.as_payload(), item_payloads, collection_bits['manifest']),
    }


def _compact_item_payload(display_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    compact = {'display_name': display_name, 'status': payload.get('status')}
    if payload.get('status') == 'accepted':
        compact.update(
            {
                'source': payload['source'],
                'extraction': payload.get('extraction'),
                'summary': payload['summary'],
                'uplift': payload['uplift'],
                'routing': payload['routing'],
                'uac': payload['uac'],
                'manifest': payload['manifest'],
                'cross_analysis': payload['cross_analysis'],
                'benchmark_sources': payload.get('benchmark_sources', []),
                'recommendation': payload['recommendation'],
            }
        )
    else:
        compact['rejection'] = payload.get('rejection')
    return compact


def _payload_source_refs(payload: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    if 'items' in payload:
        refs.extend(
            str(item['source']['normalized_source'])
            for item in payload['items']
            if item.get('status') == 'accepted' and item.get('source')
        )
    elif payload.get('source', {}).get('normalized_source'):
        normalized = payload['source']['normalized_source']
        if isinstance(normalized, list):
            refs.extend(str(item) for item in normalized)
        else:
            refs.append(str(normalized))
    return refs


def _quality_descriptor_seed(payload: Mapping[str, Any]) -> dict[str, Any]:
    manifest = json.loads(json.dumps(payload['manifest']))
    if payload.get('source', {}).get('cluster_count'):
        manifest['family_slug'] = manifest.get('slug')
    if payload.get('handoff_contract'):
        manifest['handoff_contract'] = json.loads(json.dumps(payload['handoff_contract']))
    if payload.get('recommendation'):
        manifest['recommendation'] = json.loads(json.dumps(payload['recommendation']))
    if payload.get('cross_analysis'):
        manifest['cross_analysis'] = json.loads(json.dumps(payload['cross_analysis']))
    return manifest


def _run_quality_for_payload(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if payload.get('status') != 'accepted' or args.quality_loop == 'off':
        return payload
    slug = str(payload['manifest']['slug'])
    descriptor_seed = _quality_descriptor_seed(payload)
    profile = load_quality_profile(ROOT, slug, args.quality_profile)
    source_refs = _payload_source_refs(payload)
    plan = build_quality_plan(
        slug=slug,
        profile=profile,
        capability_type=str(((descriptor_seed.get('layers') or {}).get('minimal') or {}).get('capability_type') or 'skill'),
        descriptor_path=f'.meta/capabilities/{slug}.json',
        source_refs=source_refs,
        benchmark_sources=payload.get('benchmark_sources') or (),
        max_passes_override=args.max_quality_passes,
    )
    rendered_text = _render_ssot_markdown(slug, payload, quality_profile=profile.payload)
    quality_result = run_quality_loop(
        slug=slug,
        profile=profile,
        candidate_text=rendered_text,
        descriptor=descriptor_seed,
        source_refs=source_refs,
        benchmark_sources=payload.get('benchmark_sources') or (),
        max_passes=max(1, min(args.max_quality_passes, profile.max_passes)),
    )
    result = dict(payload)
    result['quality_plan'] = plan
    result['quality_result'] = quality_result
    result['quality_result']['final_candidate_text'] = quality_result['final_candidate_text']
    return result


def _single_source_plan(source_label: str, payload: dict[str, Any]) -> dict[str, Any]:
    slug = payload['manifest']['slug']
    manifest = payload['manifest']
    return {
        'proposed_ssot_slug': slug,
        'capability_type': payload['uac']['capability_type'],
        'deployment_intent': payload['uac']['deployment_intent'],
        'emitted_surfaces': payload['uac']['emitted_surfaces'],
        'install_target': payload['recommendation']['install_target'],
        'cross_analysis': payload['cross_analysis'],
        'landing': {
            'ssot_file': f'ssot/{slug}.md',
            'descriptor_file': f'.meta/capabilities/{slug}.json',
            'manifest_layers': list(manifest['layers'].keys()),
            'advisory_handoff_contract': True,
        },
    }


def _collection_plan(source_label: str, collection: dict[str, Any], item_payloads: list[dict[str, Any]], manifest: dict[str, object]) -> dict[str, Any]:
    accepted_items = [item for item in item_payloads if item.get('status') == 'accepted']
    slug = _slugify(collection.get('recommended_slug') or source_label)
    return {
        'proposed_ssot_slug': slug,
        'collection_type': collection['collection_type'],
        'capability_type': collection['capability_type'],
        'shared_roof': collection['shared_roof'],
        'accepted_item_count': len(accepted_items),
        'install_target': manifest['layers']['minimal']['install_target'],
        'manifest_layers': list(manifest['layers'].keys()),
        'landing': {
            'ssot_file': f'ssot/{slug}.md',
            'descriptor_file': f'.meta/capabilities/{slug}.json',
        },
        'family_members': [item['source']['normalized_source'] for item in accepted_items],
    }


def _next_actions(capability_type: str, route_profile: str, fit_assessment: str) -> list[str]:
    actions = []
    if capability_type == 'agent':
        actions.extend([
            'Preserve control-plane instructions and explicit tool boundaries.',
            'Emit target agent registrations only where the platform supports agents.',
        ])
    elif capability_type == 'both':
        actions.extend([
            'Keep one SSOT source and emit both skill/workflow and agent surfaces.',
            'Separate reusable workflow content from agent-only control metadata.',
        ])
    elif capability_type == 'skill':
        actions.extend([
            'Normalize into one canonical skill/command source file.',
            'Preserve explicit examples, constraints, and expected output sections.',
        ])
    else:
        actions.extend([
            'Review manually before packaging.',
            'Add explicit objective/scope markers if you want deterministic uplift.',
        ])
    actions.append(f'Carry forward route profile {route_profile} as advisory packaging context only.')
    if fit_assessment == 'requires_adjustment':
        actions.append('Adjust both the new manifest and overlapping existing manifests before apply.')
    if fit_assessment == 'manual_review':
        actions.append('Do not auto-apply while overlap or conflict issues remain unresolved.')
    return actions


def _rejection_payload(source: str, error: UrlSourceRejectedError) -> dict[str, Any]:
    rejection = error.rejection
    return {
        'status': 'rejected',
        'source': {
            'type': 'URL',
            'normalized_source': rejection.normalized_source,
            'policy_rule_id': rejection.matched_rule_id,
        },
        'rejection': {
            'code': rejection.code,
            'terminal_status': rejection.terminal_status,
            'detail': rejection.detail,
            'evidence_paths': list(rejection.evidence_paths),
        },
        'recommendation': {
            'next_actions': [
                'Use a prompt/spec-like source with explicit objectives, scope, or constraints.',
                'Do not attempt packaging until the suitability gate accepts the source.',
            ]
        },
        'requested_source': source,
    }


def _fetch_remote_text(url: str, *, timeout_seconds: int) -> str:
    request = Request(url, headers={'User-Agent': 'capability-fabric-uac'})
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode('utf-8')


def run_phase1_pipeline_from_text(text: str) -> str:
    from intent_pipeline.sanitization.pipeline import sanitize_two_pass
    from intent_pipeline.summary.renderer import render_intent_summary

    sanitized = sanitize_two_pass(text)
    return render_intent_summary(sanitized)


def _audit_payload() -> dict[str, Any]:
    from intent_pipeline.uac_ssot import audit_ssot_entries, render_audit_table

    audits = audit_ssot_entries(ROOT)
    status_counts: dict[str, int] = {}
    for audit in audits:
        status_counts[audit.audit_status] = status_counts.get(audit.audit_status, 0) + 1
    return {
        'status': 'accepted',
        'mode': 'audit',
        'source': {'type': 'SSOT_DIRECTORY', 'normalized_source': str((ROOT / 'ssot').resolve())},
        'summary': {
            'entry_count': len(audits),
            'status_counts': status_counts,
        },
        'audit_table': render_audit_table(audits),
        'items': [audit.as_payload() for audit in audits],
        'handoff_contract': build_ssot_handoff_contract(ROOT),
        'deployment_matrix': deployment_matrix_payload(),
        'classification_rubric': classification_rubric_payload(),
    }


def _explain_payload() -> dict[str, Any]:
    return {
        'status': 'accepted',
        'mode': 'explain',
        'classification_rubric': classification_rubric_payload(),
        'deployment_matrix': deployment_matrix_payload(),
        'quality_profiles': [path.stem for path in sorted(quality_profile_dir(ROOT).glob('*.json'))],
        'notes': [
            'command, plugin, power, and extension are wrapper surfaces rather than capability types',
            'Capability Fabric/UAC publishes advisory manifests and handoff contracts only',
            'judge runs the built-in quality loop without writing repo-tracked state',
            'apply mutates this repo only after explicit confirmation',
        ],
    }


def _render_output(payload: dict[str, Any], output_mode: str) -> int:
    if output_mode == 'table':
        if 'audit_table' in payload:
            print(payload['audit_table'])
            print()
            print(json.dumps({k: v for k, v in payload.items() if k != 'audit_table'}, indent=2, sort_keys=True))
            return 0
        if payload.get('mode') == 'explain':
            print('Capability Type | Codex | Gemini | Claude | Kiro')
            print('---------------+-------+--------+--------+-----')
            matrix = payload['deployment_matrix']['capability_types']
            for capability in ('skill', 'agent', 'both', 'manual_review'):
                row = matrix[capability]['surfaces']
                print(
                    f"{capability.ljust(14)} | "
                    f"{', '.join(row['codex']) or '-'} | "
                    f"{', '.join(row['gemini']) or '-'} | "
                    f"{', '.join(row['claude']) or '-'} | "
                    f"{', '.join(row['kiro']) or '-'}"
                )
            return 0
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _slugify(value: str) -> str:
    import re

    normalized = re.sub(r'[^a-z0-9]+', '-', value.casefold()).strip('-')
    return normalized or 'uac-import'


def _benchmark_payloads(*, slug: str, fit_assessment: str, collection_type: str | None, query: str, policy: str) -> list[dict[str, str]]:
    if policy == 'off':
        return []
    if policy == 'always' or should_search_benchmarks(slug=slug, fit_assessment=fit_assessment, collection_type=collection_type):
        return benchmark_search(query)
    return []


def _process_source(source: str, *, args: argparse.Namespace) -> dict[str, Any]:
    if _looks_like_url(source) and not _is_raw_text_url(source):
        return _import_github_tree(
            source,
            recurse=not args.no_recurse,
            max_items=args.max_items,
            timeout_seconds=args.timeout_seconds,
            target_system=args.target_system,
            install_target=args.install_target,
            benchmark_policy=args.benchmark_search,
            args=args,
        )
    if _looks_like_url(source):
        return _import_raw_url(
            source,
            max_bytes=args.max_bytes,
            timeout_seconds=args.timeout_seconds,
            target_system=args.target_system,
            install_target=args.install_target,
            benchmark_policy=args.benchmark_search,
        )
    path = Path(source).expanduser().resolve()
    if path.is_dir():
        return _import_local_directory(
            path,
            recurse=not args.no_recurse,
            max_items=args.max_items,
            target_system=args.target_system,
            install_target=args.install_target,
            benchmark_policy=args.benchmark_search,
            args=args,
        )
    if path.is_file():
        return _import_local_file(path, target_system=args.target_system, install_target=args.install_target, benchmark_policy=args.benchmark_search)
    raise SystemExit(
        'uac-import.py requires a file path, directory path, raw https URL, or GitHub folder URL. '
        f'Got: {path}'
    )


def _multi_source_payload(sources: list[str], args: argparse.Namespace) -> dict[str, Any]:
    item_payloads = [_process_source(source, args=args) for source in sources]
    recommendation = aggregate_collection_recommendation('multi-source-import', item_payloads)
    collection_bits = _collection_manifest('multi-source-import', 'MULTI_SOURCE', '::'.join(sources), recommendation.as_payload(), item_payloads, args.install_target, args.benchmark_search)
    return {
        'status': 'accepted',
        'mode': args.mode,
        'source': {'type': 'MULTI_SOURCE', 'normalized_source': sources, 'item_count': len(item_payloads)},
        'collection': recommendation.as_payload(),
        'manifest': collection_bits['manifest'],
        'cross_analysis': collection_bits['cross_analysis'],
        'benchmark_sources': collection_bits['benchmark_sources'],
        'handoff_contract': orchestrator_handoff_payload([collection_bits['manifest']]),
        'items': [_compact_item_payload(source, item) for source, item in zip(sources, item_payloads)],
        'plan': _collection_plan('multi-source-import', recommendation.as_payload(), item_payloads, collection_bits['manifest']),
    }


def _mode_entries_from_items(items: list[dict[str, Any]]) -> list[dict[str, object]]:
    modes: list[dict[str, object]] = []
    for item in items:
        if item.get('status') != 'accepted':
            continue
        display_name = str(item.get('display_name') or item['source']['normalized_source'])
        mode_slug = _slugify(Path(display_name).stem)
        modes.append(
            {
                'mode_slug': mode_slug,
                'display_name': Path(display_name).stem.replace('-', ' ').replace('_', ' ').title(),
                'source_refs': [item['source']['normalized_source']],
                'mode_summary': item.get('summary'),
                'required_inputs': item['manifest']['layers']['minimal']['required_inputs'],
                'expected_outputs': item['manifest']['layers']['minimal']['expected_outputs'],
                'examples': item.get('uplift', {}).get('in_scope') or [],
                'uplift_notes': item.get('uplift', {}).get('quality_constraints') or [],
            }
        )
    return modes


def _render_ssot_markdown(slug: str, payload: dict[str, Any], *, quality_profile: Mapping[str, Any] | None = None) -> str:
    manifest = payload['manifest']
    minimal = manifest['layers']['minimal']
    quality_profile = quality_profile or {}
    title = str(quality_profile.get('title') or ' '.join(part.capitalize() for part in slug.replace('_', '-').split('-')))
    summary = str(minimal.get('summary') or f'Capability import for {slug}.').strip()
    capability_type = str(minimal.get('capability_type') or 'manual_review')
    install_target = str(minimal.get('install_target', {}).get('recommended') or 'auto')
    description = str(quality_profile.get('description') or summary.splitlines()[0][:160])
    escaped_description = description.replace('"', '\\"')
    template = load_capability_template(ROOT, capability_type if capability_type in {'skill', 'agent', 'both'} else 'skill')
    constraints = payload.get('uplift', {}).get('quality_constraints') or manifest['layers']['expanded'].get('adjustment_recommendations') or []
    required_inputs = list(minimal.get('required_inputs') or ['user intent/context', 'relevant source material'])
    expected_outputs = list(minimal.get('expected_outputs') or ['deterministic recommendation'])
    review_timing = [
        '- commit: when commands, behavior, or metadata contracts change',
        '- pull request: when repo structure, CI, release flow, or docs drift materially',
        '- merge: when adjacent capability or doc surfaces changed and drift is likely',
        '- release: verify shipped behavior, install flow, and references against the final state',
    ]
    lines = [
        '---',
        f'name: "{slug}"',
        f'description: "{escaped_description}"',
        f'capability_type: "{capability_type}"',
        f'install_target: "{install_target}"',
        '---',
        '',
        f'# {title}',
        '',
        '## Purpose',
        f'Use this capability when the user needs {summary[0].lower() + summary[1:] if summary else "a deterministic capability response"}',
        '',
        '## Primary Objective',
        str(payload.get('uplift', {}).get('primary_objective') or summary),
        '',
    ]
    if capability_type in {'agent', 'both'}:
        lines.extend([
            '## Agent Operating Contract',
            'When emitted as an agent, this capability remains advisory by default and must not claim hidden orchestration authority.',
            '',
            'Mission:',
            '- inspect the relevant source or repo context first',
            '- produce deterministic outputs or artifacts for the requested task',
            '- preserve the provider boundary by publishing advice, not runtime-control policy',
            '',
            '## Tool Boundaries',
            '- allowed: read relevant inputs, inspect current state, and write the intended artifacts when explicitly requested',
            '- forbidden: runtime routing, delegation decisions, workflow-control loops, or unrelated code execution',
            '- escalation: if implementation or orchestration is requested, hand that off as a separate capability decision',
            '',
        ])
    if '## Output Directory' in template.required_headings or '## Output Directory' in template.preferred_headings:
        lines.extend([
            '## Output Directory',
            '- `reports/<slug>/<timestamp>-summary.md` style report paths are the default when file output is requested',
            '- repo-ready artifacts should be named explicitly when the user asks for direct changes',
            '',
        ])
    lines.extend([
        '## Workflow',
        '1. Clarify the task, success criteria, and hard constraints.',
        '2. Inspect the relevant repo or source context before making recommendations.',
        '3. Produce deterministic outputs with explicit evidence, boundaries, and target paths or artifacts.',
        '4. Record risks, review timing, and anything that requires manual confirmation.',
        '',
        '## Rules',
        '- Keep the capability reusable and deterministic.',
        '- Publish advisory guidance only unless the caller explicitly requests execution.',
        '- Do not claim orchestration, delegation, or runtime-control ownership.',
        '',
        '## Required Inputs',
    ])
    for item in required_inputs:
        lines.append(f'- {item}')
    lines.extend(['', '## Required Output'])
    for item in expected_outputs:
        lines.append(f'- {item}')
    lines.extend([
        '- explicit risks and open questions',
        '- target paths, commands, or artifact names when applicable',
        '',
        '## Constraints',
    ])
    for item in constraints:
        lines.append(f'- {item}')
    if 'items' in payload:
        lines.extend(['', '## Modes'])
        for item in payload['items']:
            if item.get('status') != 'accepted':
                continue
            lines.extend([
                f"### {Path(item['display_name']).stem.replace('-', ' ').replace('_', ' ').title()}",
                '',
                f"Source: `{item['source']['normalized_source']}`",
                '',
                'Objective',
                str(item.get('uplift', {}).get('primary_objective') or item.get('summary') or '').strip(),
                '',
            ])
            in_scope = item.get('uplift', {}).get('in_scope') or []
            if in_scope:
                lines.append('In Scope')
                for bullet in in_scope:
                    lines.append(f'- {bullet}')
                lines.append('')
    else:
        lines.extend(['', '## Invocation Hints', payload.get('summary', summary), ''])
        in_scope = payload.get('uplift', {}).get('in_scope') or []
        if in_scope:
            lines.append('In Scope')
            for bullet in in_scope:
                lines.append(f'- {bullet}')
            lines.append('')
        out_of_scope = payload.get('uplift', {}).get('out_of_scope') or []
        if out_of_scope:
            lines.append('Out of Scope')
            for bullet in out_of_scope:
                lines.append(f'- {bullet}')
            lines.append('')
    lines.extend([
        '## Examples',
        '### Example Request',
        f'> Use `{slug}` to inspect a repo change, produce a deterministic recommendation, and make the review timing explicit.',
        '',
        '### Example Output Shape',
        '- current state summary',
        '- findings or recommendation',
        '- target paths or commands',
        '- risks and review timing',
        '',
        '## Evaluation Rubric',
        '| Check | What Passing Looks Like |',
        '| --- | --- |',
        '| Intent coverage | The capability states when to use it and what success looks like |',
        '| Output contract | Deliverables are deterministic and reviewable |',
        '| Boundary clarity | The capability says what it will not do |',
        '| Surface usability | The body is strong enough to support every emitted surface |',
        '',
        '## Review Timing',
        *review_timing,
        '',
        '## Advisory Notes',
        '- Relationship and org-graph metadata remain advisory for future orchestrators.',
        '- Use the sidecar descriptor as the canonical machine-readable contract.',
        f"- Emit surfaces for: `{', '.join(sorted(name for values in minimal.get('emitted_surfaces', {}).values() for name in values))}`",
        '',
    ])
    return '\n'.join(lines)


def _persist_quality_reviews(slug: str, quality_plan: Mapping[str, Any], quality_result: Mapping[str, Any]) -> list[Path]:
    profile_path = quality_profile_dir(ROOT) / f"{quality_plan['quality_profile']}.json"
    review_dir = quality_review_dir(ROOT, slug)
    review_dir.mkdir(parents=True, exist_ok=True)
    changed: list[Path] = []
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')
    for report in quality_result.get('judge_reports') or []:
        path = quality_review_path(ROOT, slug, int(report['pass_number']), stamp)
        path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        changed.append(path)
    latest_path = latest_quality_review_path(ROOT, slug)
    latest_path.write_text(
        render_latest_review_markdown(slug=slug, quality_result=quality_result),
        encoding='utf-8',
    )
    changed.append(latest_path)
    if profile_path.exists():
        changed.append(profile_path)
    return changed


def _apply_payload(payload: dict[str, Any], args: argparse.Namespace, sources: list[str]) -> dict[str, Any]:
    if payload.get('status') != 'accepted':
        return payload
    if payload.get('source', {}).get('cluster_count', 0) > 1:
        payload = dict(payload)
        payload['status'] = 'manual_review'
        payload['detail'] = 'The source spans several families. Narrow to one family before apply.'
        return payload
    cross = payload.get('cross_analysis', {})
    if cross.get('fit_assessment') == 'manual_review':
        payload = dict(payload)
        payload['status'] = 'manual_review'
        payload['detail'] = 'Cross-analysis flagged duplicate or conflicting graph roles. Resolve those before apply.'
        return payload
    if not args.yes:
        confirmation = input('Apply will write SSOT + descriptor into this repo, rebuild surfaces, and validate. Type yes to continue: ').strip().lower()
        if confirmation not in {'y', 'yes'}:
            payload = dict(payload)
            payload['status'] = 'cancelled'
            payload['detail'] = 'apply cancelled by user'
            return payload
    result = dict(payload)
    if args.quality_loop == 'on' and 'quality_result' not in result:
        result = _run_quality_for_payload(result, args)
    slug = str(result['manifest']['slug'])
    quality_plan = result.get('quality_plan')
    quality_result = result.get('quality_result')
    quality_paths: list[Path] = []
    if quality_plan and quality_result:
        quality_paths = _persist_quality_reviews(slug, quality_plan, quality_result)
        if quality_result.get('status') != 'ship':
            result['mode'] = 'apply'
            result['status'] = 'manual_review'
            result['detail'] = 'Quality gate refused landing. Review the persisted quality reports and revise before apply.'
            result['apply_result'] = {
                'changed_paths': [str(path.relative_to(ROOT)) for path in quality_paths],
                'quality': {
                    'profile': quality_plan['quality_profile'],
                    'status': quality_result.get('status'),
                    'pass_count': quality_result.get('pass_count'),
                    'stop_reason': quality_result.get('stop_reason'),
                },
                'deploy_next_step': 'Run bin/uac judge or revise the candidate prompt before apply.',
            }
            return result
    ssot_path = ROOT / 'ssot' / f'{slug}.md'
    descriptor = build_descriptor(
        manifest=result['manifest'],
        family_slug=slug,
        shared_summary=str(result['manifest']['layers']['minimal'].get('summary') or ''),
        shared_constraints=tuple(result.get('manifest', {}).get('layers', {}).get('expanded', {}).get('adjustment_recommendations') or ()),
        modes=tuple(_mode_entries_from_items(result.get('items', []))),
        benchmark_sources=tuple(result.get('benchmark_sources') or ()),
        quality_profile=(quality_plan or {}).get('quality_profile'),
        quality_status=(quality_result or {}).get('status'),
        judge_reports=tuple((quality_result or {}).get('judge_reports') or ()),
        consumption_hints=dict((quality_result or {}).get('consumption_hints') or {}),
        quality_pass_count=(quality_result or {}).get('pass_count'),
        quality_stop_reason=(quality_result or {}).get('stop_reason'),
        historical_baseline=dict((quality_result or {}).get('historical_baseline') or {}),
        quality_validation_matrix=tuple((quality_plan or {}).get('validation_matrix') or ()),
    )
    baseline_materialization = None
    if quality_result and quality_result.get('status') == 'ship':
        baseline_materialization = persist_source_baseline(
            ROOT,
            slug=slug,
            baseline_text=str((quality_result or {}).get('final_candidate_text') or _render_ssot_markdown(slug, result)),
            overwrite=False,
        )
    if quality_plan and quality_result:
        descriptor.update(
            quality_descriptor_fields(
                profile=load_quality_profile(ROOT, slug, (quality_plan or {}).get('quality_profile') or 'auto'),
                quality_result=quality_result,
                benchmark_sources=tuple(result.get('benchmark_sources') or ()),
            )
        )
        descriptor['quality_validation_matrix'] = list((quality_plan or {}).get('validation_matrix') or ())
    if baseline_materialization:
        descriptor['historical_baseline'] = dict(descriptor.get('historical_baseline') or {})
        descriptor['historical_baseline']['baseline_path'] = baseline_materialization['baseline_path']
    ssot_text = str((quality_result or {}).get('final_candidate_text') or _render_ssot_markdown(slug, result))
    ssot_path.write_text(ssot_text + ('\n' if not ssot_text.endswith('\n') else ''), encoding='utf-8')
    descriptor_path = save_descriptor(ROOT, slug, descriptor)
    source_note = None
    source_refs = []
    if 'items' in result:
        source_refs.extend(item['source']['normalized_source'] for item in result['items'] if item.get('status') == 'accepted')
    else:
        source_refs.append(result['source']['normalized_source'])
    if any(ref.startswith('http') or ref.startswith('repomix://') for ref in source_refs) or result.get('benchmark_sources'):
        source_note = write_source_note(
            ROOT,
            slug,
            title=f'{slug} source assessment',
            source_refs=source_refs,
            benchmark_sources=result.get('benchmark_sources') or (),
            rationale=str(result['manifest']['layers']['minimal'].get('rationale') or result['manifest']['layers']['minimal'].get('summary') or ''),
        )
    build_proc = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build-surfaces.py')], capture_output=True, text=True)
    validate_proc = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'validate-surfaces.py'), '--strict'], capture_output=True, text=True)
    result['mode'] = 'apply'
    result['apply_result'] = {
        'changed_paths': [str(ssot_path.relative_to(ROOT)), str(descriptor_path.relative_to(ROOT))]
        + ([baseline_materialization['baseline_path']] if baseline_materialization else [])
        + ([str(source_note.relative_to(ROOT))] if source_note else [])
        + [str(path.relative_to(ROOT)) for path in quality_paths],
        'build': {'returncode': build_proc.returncode, 'stdout': build_proc.stdout.strip(), 'stderr': build_proc.stderr.strip()},
        'validate': {'returncode': validate_proc.returncode, 'stdout': validate_proc.stdout.strip(), 'stderr': validate_proc.stderr.strip()},
        'quality': {
            'profile': (quality_plan or {}).get('quality_profile'),
            'status': (quality_result or {}).get('status'),
            'pass_count': (quality_result or {}).get('pass_count'),
            'stop_reason': (quality_result or {}).get('stop_reason'),
        },
        'deploy_next_step': 'Run bin/capability-fabric deploy or scripts/deploy-surfaces.sh after reviewing repo changes.',
    }
    if build_proc.returncode == 0 and validate_proc.returncode == 0:
        result['status'] = 'applied'
        result['detail'] = 'SSOT and descriptor landed in repo, surfaces rebuilt, validation passed.'
    else:
        result['status'] = 'apply_failed_validation'
        result['detail'] = 'Repo changes were written, but build or validation failed. Review the recorded outputs before deploy.'
    return result


def main() -> int:
    args = _parse_args()
    if args.mode in {'import', 'plan', 'judge', 'apply'} and not args.source:
        raise SystemExit('--source is required for import, plan, judge, and apply modes')
    if args.mode == 'audit':
        payload = _audit_payload()
    elif args.mode == 'explain':
        payload = _explain_payload()
    elif len(args.source or []) > 1:
        payload = _multi_source_payload(args.source or [], args)
    else:
        source = (args.source or [None])[0]
        try:
            payload = _process_source(source, args=args)
        except UrlSourceRejectedError as error:
            payload = _rejection_payload(source, error)
        if payload.get('status') == 'accepted' and args.mode in {'plan', 'judge', 'apply'} and 'plan' not in payload:
            payload['plan'] = _single_source_plan(source, payload)
    if payload.get('status') == 'accepted' and args.mode in {'plan', 'judge', 'apply'}:
        payload = _run_quality_for_payload(payload, args)
    if args.mode == 'judge':
        payload['mode'] = 'judge'
    if args.mode == 'apply':
        payload = _apply_payload(payload, args, args.source or [])
    if args.show_rubric and 'classification_rubric' not in payload:
        payload['classification_rubric'] = classification_rubric_payload()
    return _render_output(payload, args.output)


if __name__ == '__main__':
    raise SystemExit(main())
