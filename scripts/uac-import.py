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
from intent_pipeline.uac_descriptors import build_descriptor, load_descriptor, save_descriptor, write_source_note
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
from intent_pipeline.uac_baselines import (
    evaluate_candidate_against_baseline,
    persist_source_baseline,
    resolve_historical_baseline,
    text_sha256,
)
from intent_pipeline.uac_templates import load_capability_template
from intent_pipeline.uac_repomix import collect_repomix_candidates, materialize_repomix_candidate, repomix_available
from intent_pipeline.uac_sources import (
    UacSourceCandidate,
    aggregate_collection_recommendation,
    cluster_source_candidates,
    enumerate_github_tree,
    enumerate_local_directory,
)
from intent_pipeline.uac_ssot import (
    build_ssot_manifest_entry,
    build_ssot_handoff_contract,
    extract_invocation_hints,
    extract_section_bullets,
    load_ssot_entries,
    parse_frontmatter_list,
    parse_ssot_frontmatter_and_body,
)
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
    frontmatter, body = parse_ssot_frontmatter_and_body(raw_text)
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
    minimal = dict((manifest.get('layers') or {}).get('minimal') or {})
    optional_metadata = {
        'version': frontmatter.get('version'),
        'author': frontmatter.get('author'),
        'compatibility': frontmatter.get('compatibility'),
    }
    supported_agents = parse_frontmatter_list(frontmatter.get('supported_agents') or frontmatter.get('agents'))
    for key, value in optional_metadata.items():
        if value:
            minimal[key] = value
    if supported_agents:
        minimal['supported_agents'] = supported_agents
    manifest.setdefault('layers', {})
    manifest['layers']['minimal'] = minimal
    invocation_hints = extract_invocation_hints(body)
    if invocation_hints:
        manifest['invocation_hints'] = invocation_hints
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
    if cross_analysis['fit_assessment'] == 'manual_review' and capability_type != 'manual_review' and not _same_slug_update_only(cross_analysis, slug):
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


def _existing_manifest_by_slug(slug: str) -> dict[str, Any] | None:
    for manifest in _existing_manifests():
        if str(manifest.get('slug')) == slug:
            return manifest
    return None


def _compact_descriptor_delta(existing: Mapping[str, Any] | None, candidate: Mapping[str, Any]) -> dict[str, Any]:
    if not existing:
        return {
            'change_type': 'new_descriptor',
            'changed_fields': ['descriptor'],
            'existing': None,
            'candidate': {
                'display_name': candidate.get('display_name'),
                'quality_profile': candidate.get('quality_profile'),
                'quality_status': candidate.get('quality_status'),
            },
        }

    changed_fields: list[str] = []
    for key in ('display_name', 'family_slug', 'quality_profile', 'quality_status', 'quality_pass_count', 'quality_stop_reason'):
        if existing.get(key) != candidate.get(key):
            changed_fields.append(key)

    existing_min = dict((existing.get('layers') or {}).get('minimal') or {})
    candidate_min = dict((candidate.get('layers') or {}).get('minimal') or {})
    for key in ('summary', 'display_name', 'capability_type', 'version', 'author', 'compatibility', 'supported_agents'):
        if existing_min.get(key) != candidate_min.get(key):
            changed_fields.append(f'layers.minimal.{key}')

    return {
        'change_type': 'descriptor_update' if changed_fields else 'descriptor_noop',
        'changed_fields': changed_fields,
        'existing': {
            'display_name': existing.get('display_name'),
            'quality_profile': existing.get('quality_profile'),
            'quality_status': existing.get('quality_status'),
        },
        'candidate': {
            'display_name': candidate.get('display_name'),
            'quality_profile': candidate.get('quality_profile'),
            'quality_status': candidate.get('quality_status'),
        },
    }


def _build_descriptor_preview(
    payload: Mapping[str, Any],
    *,
    quality_plan: Mapping[str, Any] | None = None,
    quality_result: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    slug = str(payload['manifest']['slug'])
    descriptor = build_descriptor(
        manifest=payload['manifest'],
        family_slug=slug,
        shared_summary=str(payload['manifest']['layers']['minimal'].get('summary') or ''),
        shared_constraints=_source_constraints(payload)
        or tuple(payload.get('manifest', {}).get('layers', {}).get('expanded', {}).get('adjustment_recommendations') or ()),
        modes=tuple(_mode_entries_from_items(payload.get('items', []))),
        benchmark_sources=tuple(payload.get('benchmark_sources') or ()),
        quality_profile=(quality_plan or {}).get('quality_profile'),
        quality_status=(quality_result or {}).get('status'),
        judge_reports=tuple((quality_result or {}).get('judge_reports') or ()),
        consumption_hints=dict((quality_result or {}).get('consumption_hints') or {}),
        quality_pass_count=(quality_result or {}).get('pass_count'),
        quality_stop_reason=(quality_result or {}).get('stop_reason'),
        historical_baseline=dict((quality_result or {}).get('historical_baseline') or {}),
        quality_validation_matrix=tuple((quality_plan or {}).get('validation_matrix') or ()),
    )
    existing_descriptor = load_descriptor(ROOT, slug)
    return descriptor, _compact_descriptor_delta(existing_descriptor, descriptor)


def _user_visible_impact(payload: Mapping[str, Any]) -> dict[str, Any]:
    manifest = payload['manifest']
    minimal = dict((manifest.get('layers') or {}).get('minimal') or {})
    slug = str(manifest.get('slug') or '')
    existing_manifest = _existing_manifest_by_slug(slug)
    surfaces = sorted(name for values in (minimal.get('emitted_surfaces') or {}).values() for name in values)
    impact = {
        'change_kind': 'new_capability' if not existing_manifest else 'update_existing_capability',
        'display_name': manifest.get('display_name'),
        'capability_type': minimal.get('capability_type'),
        'install_target': (minimal.get('install_target') or {}).get('recommended'),
        'expected_surfaces': surfaces,
        'invocation_hints': list(manifest.get('invocation_hints') or []),
        'expected_outputs': list(minimal.get('expected_outputs') or []),
        'compatibility': minimal.get('compatibility'),
        'supported_agents': list(minimal.get('supported_agents') or []),
    }
    if existing_manifest:
        existing_minimal = dict((existing_manifest.get('layers') or {}).get('minimal') or {})
        changed_fields: list[str] = []
        for key in ('summary', 'capability_type', 'compatibility', 'supported_agents'):
            if existing_minimal.get(key) != minimal.get(key):
                changed_fields.append(key)
        if sorted(existing_manifest.get('expected_surface_names') or []) != sorted(manifest.get('expected_surface_names') or []):
            changed_fields.append('expected_surface_names')
        if list(existing_manifest.get('invocation_hints') or []) != list(manifest.get('invocation_hints') or []):
            changed_fields.append('invocation_hints')
        impact['changed_fields'] = changed_fields
    else:
        impact['changed_fields'] = ['new_capability']
    return impact


def _overlap_preview(payload: Mapping[str, Any]) -> dict[str, Any]:
    cross = dict(payload.get('cross_analysis') or {})
    return {
        'fit_assessment': cross.get('fit_assessment'),
        'duplicate_risk': cross.get('duplicate_risk'),
        'overlap_candidates': list(cross.get('overlap_report') or []),
        'conflict_report': list(cross.get('conflict_report') or []),
        'required_existing_adjustments': list(cross.get('required_existing_adjustments') or []),
        'required_new_entry_adjustments': list(cross.get('required_new_entry_adjustments') or []),
        'work_graph_change_summary': cross.get('work_graph_change_summary'),
    }


def _contributor_guidance(payload: Mapping[str, Any], quality_result: Mapping[str, Any] | None = None) -> list[str]:
    guidance: list[str] = []
    overlap = _overlap_preview(payload)
    if overlap['fit_assessment'] == 'manual_review':
        guidance.append('Resolve overlap or graph-role conflicts before apply.')
    elif overlap['fit_assessment'] == 'requires_adjustment':
        guidance.append('Tighten scope or normalize metadata against the listed overlap candidates before apply.')
    if quality_result:
        blockers = list((quality_result.get('judge_reports') or [])[-1].get('blockers') or []) if quality_result.get('judge_reports') else []
        if blockers:
            guidance.append('Address the current quality blockers before apply.')
        if quality_result.get('status') == 'ship':
            guidance.append('Quality gate is ready for apply once repo mutation is intentional.')
        elif quality_result.get('status') == 'revise':
            guidance.append('Use the final candidate text and scorecard to revise before apply.')
        elif quality_result.get('status') == 'manual_review':
            guidance.append('The quality loop exhausted automatic refinement; manual tightening is required.')
    if not guidance:
        guidance.append('No canonical blockers found; review the rendered preview and expected user-visible impact before apply.')
    return guidance


def _preview_payload(
    payload: Mapping[str, Any],
    *,
    quality_plan: Mapping[str, Any] | None = None,
    quality_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rendered_ssot = str((quality_result or {}).get('final_candidate_text') or _render_ssot_markdown(str(payload['manifest']['slug']), dict(payload)))
    descriptor_preview, descriptor_delta = _build_descriptor_preview(
        payload,
        quality_plan=quality_plan,
        quality_result=quality_result,
    )
    ship_readiness = {
        'quality_status': (quality_result or {}).get('status'),
        'quality_pass_count': (quality_result or {}).get('pass_count'),
        'quality_stop_reason': (quality_result or {}).get('stop_reason'),
        'blockers': list((quality_result.get('judge_reports') or [])[-1].get('blockers') or []) if quality_result and quality_result.get('judge_reports') else [],
    }
    return {
        'rendered_ssot_markdown': rendered_ssot,
        'descriptor_preview': descriptor_preview,
        'descriptor_delta': descriptor_delta,
        'overlap_preview': _overlap_preview(payload),
        'user_visible_impact': _user_visible_impact(payload),
        'ship_readiness': ship_readiness,
        'contributor_guidance': _contributor_guidance(payload, quality_result=quality_result),
    }


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
    candidate_text = _preferred_ssot_text(slug, payload)
    quality_result = run_quality_loop(
        slug=slug,
        profile=profile,
        candidate_text=candidate_text,
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


def _source_frontmatter_fields(payload: Mapping[str, Any]) -> dict[str, str]:
    normalized_source = str(((payload.get('source') or {}).get('normalized_source')) or '').strip()
    if not normalized_source:
        return {}
    source_path = Path(normalized_source).expanduser()
    if not source_path.is_file():
        return {}
    try:
        text = source_path.read_text(encoding='utf-8')
    except OSError:
        return {}
    if not text.startswith('---\n'):
        return {}
    end_idx = text.find('\n---', 4)
    if end_idx == -1:
        return {}
    fields: dict[str, str] = {}
    for raw_line in text[4:end_idx].splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            fields[key] = value
    return fields


def _escape_double_quoted_yaml(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


def _extract_label_bullets(raw_text: str, labels: tuple[str, ...]) -> tuple[str, ...]:
    lines = raw_text.splitlines()
    normalized_labels = {f'{label}:' for label in labels}
    for index, line in enumerate(lines):
        if line.strip() not in normalized_labels:
            continue
        bullets: list[str] = []
        for follow in lines[index + 1:]:
            stripped = follow.strip()
            if stripped.startswith('- '):
                bullets.append(stripped[2:].strip())
                continue
            if not stripped:
                if bullets:
                    break
                continue
            if stripped.endswith(':') or stripped.startswith('## '):
                break
            if bullets:
                break
        if bullets:
            return tuple(dict.fromkeys(item for item in bullets if item))
    return ()


def _source_section_bullets(payload: Mapping[str, Any], headings: tuple[str, ...]) -> tuple[str, ...]:
    source_text = _source_body_text(payload)
    if not source_text:
        return ()
    for heading in headings:
        bullets = tuple(extract_section_bullets(source_text, f'## {heading}'))
        if bullets:
            return bullets
    return _extract_label_bullets(source_text, headings)


def _source_body_text(payload: Mapping[str, Any]) -> str | None:
    normalized_source = str(((payload.get('source') or {}).get('normalized_source')) or '').strip()
    if not normalized_source:
        return None
    source_path = Path(normalized_source).expanduser()
    if not source_path.is_file():
        return None
    try:
        return source_path.read_text(encoding='utf-8')
    except OSError:
        return None


def _source_constraints(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return _source_section_bullets(payload, ('Constraints',))


def _source_required_inputs(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return _source_section_bullets(payload, ('Required Inputs', 'Required Input'))


def _source_expected_outputs(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return _source_section_bullets(
        payload,
        ('Required Output', 'Expected Outputs', 'Output Contract', 'Output Format'),
    )


def _repo_head_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    head = result.stdout.strip()
    return head[:8] if head else None


def _repo_relative_source_path(path: str) -> str | None:
    try:
        resolved = Path(path).expanduser().resolve()
    except OSError:
        return None
    try:
        return str(resolved.relative_to(ROOT).as_posix())
    except ValueError:
        return None


def _baseline_materialization_payload(
    slug: str,
    payload: Mapping[str, Any],
    *,
    ssot_text: str,
    ssot_path: Path,
) -> dict[str, str | None]:
    source_text = _source_body_text(payload)
    if source_text:
        capability_type = str(
            ((payload.get('manifest') or {}).get('layers', {}).get('minimal', {}).get('capability_type') or 'skill')
        )
        template_name = capability_type if capability_type in {'skill', 'agent', 'both'} else 'skill'
        template = load_capability_template(ROOT, template_name)
        if all(marker in source_text for marker in template.required_headings):
            return {
                'text': source_text.rstrip() + '\n',
                'source_kind': 'canonical_source',
                'source_path': _repo_relative_source_path(str(((payload.get('source') or {}).get('normalized_source')) or '')),
                'source_sha256': text_sha256(source_text.rstrip() + '\n'),
                'source_commit': _repo_head_commit(ROOT),
            }
    persisted_text = ssot_path.read_text(encoding='utf-8')
    return {
        'text': persisted_text,
        'source_kind': 'current_ssot',
        'source_path': str(ssot_path.relative_to(ROOT)),
        'source_sha256': text_sha256(persisted_text),
        'source_commit': _repo_head_commit(ROOT),
    }


def _same_slug_update_only(cross_analysis: Mapping[str, Any], slug: str) -> bool:
    if str(cross_analysis.get('fit_assessment') or '') != 'manual_review':
        return False
    expected_conflict = f'slug {slug} already exists'
    conflicts = [str(item) for item in cross_analysis.get('conflict_report') or []]
    if not conflicts or any(item != expected_conflict for item in conflicts):
        return False
    return True


def _normalize_payload_for_same_slug_update(payload: Mapping[str, Any]) -> dict[str, Any]:
    slug = str(((payload.get('manifest') or {}).get('slug')) or '')
    cross_analysis = payload.get('cross_analysis') or {}
    if not slug or not _same_slug_update_only(cross_analysis, slug):
        return dict(payload)
    normalized = json.loads(json.dumps(payload))
    normalized_cross = dict(normalized.get('cross_analysis') or {})
    normalized_cross['duplicate_risk'] = 'low'
    normalized_cross['conflict_report'] = []
    normalized_cross['overlap_report'] = [
        item
        for item in normalized_cross.get('overlap_report') or []
        if not (isinstance(item, dict) and item.get('slug') == slug and item.get('reason') == 'same slug')
    ]
    normalized_cross['fit_assessment'] = 'fits_cleanly' if not normalized_cross['overlap_report'] else 'requires_adjustment'
    normalized_cross['work_graph_change_summary'] = (
        f'{slug} matches an existing canonical slug and will be treated as an update target for judge/apply.'
    )
    normalized['cross_analysis'] = normalized_cross
    manifest = normalized.get('manifest') or {}
    expanded = ((manifest.get('layers') or {}).get('expanded') or {})
    expanded['overlap_candidates'] = [
        candidate for candidate in expanded.get('overlap_candidates') or [] if str(candidate) != slug
    ]
    if normalized.get('recommendation'):
        route_profile = str(((normalized.get('routing') or {}).get('route_selection') or {}).get('route_profile') or '')
        if not route_profile:
            route_profile = str(((normalized.get('routing') or {}).get('route_profile')) or '')
        capability_type = str(((normalized.get('uac') or {}).get('capability_type')) or '')
        normalized['recommendation']['next_actions'] = _next_actions(capability_type, route_profile, 'fits_cleanly')
    return normalized


def _preferred_ssot_text(slug: str, payload: Mapping[str, Any], *, quality_result: Mapping[str, Any] | None = None) -> str:
    source_text = _source_body_text(payload)
    if source_text:
        capability_type = str(
            ((payload.get('manifest') or {}).get('layers', {}).get('minimal', {}).get('capability_type') or 'skill')
        )
        template_name = capability_type if capability_type in {'skill', 'agent', 'both'} else 'skill'
        template = load_capability_template(ROOT, template_name)
        if all(marker in source_text for marker in template.required_headings):
            return source_text
    final_candidate = str((quality_result or {}).get('final_candidate_text') or '').strip()
    if final_candidate:
        return final_candidate
    return _render_ssot_markdown(slug, dict(payload))


def _evaluate_ssot_fidelity(slug: str, candidate_text: str) -> dict[str, Any]:
    baseline = resolve_historical_baseline(ROOT, slug, candidate_text=candidate_text)
    return evaluate_candidate_against_baseline(candidate_text, baseline)


def _safe_apply_ssot_text(
    slug: str,
    payload: Mapping[str, Any],
    *,
    quality_result: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    ssot_text = _preferred_ssot_text(slug, payload, quality_result=quality_result)
    fidelity = _evaluate_ssot_fidelity(slug, ssot_text)
    if not fidelity['hard_failures']:
        return ssot_text, None

    source_text = _source_body_text(payload)
    if source_text and source_text.strip() and source_text.strip() != ssot_text.strip():
        source_fidelity = _evaluate_ssot_fidelity(slug, source_text)
        if not source_fidelity['hard_failures']:
            return source_text, {
                'selected_text': 'source_text',
                'blocked_candidate_failures': list(fidelity['hard_failures']),
            }

    raise ValueError(
        'Apply refused to land a regressed SSOT body: '
        + '; '.join(str(item) for item in fidelity['hard_failures'])
    )


def _render_ssot_markdown(slug: str, payload: dict[str, Any], *, quality_profile: Mapping[str, Any] | None = None) -> str:
    manifest = payload['manifest']
    minimal = manifest['layers']['minimal']
    quality_profile = quality_profile or {}
    source_fields = _source_frontmatter_fields(payload)
    title = str(
        quality_profile.get('title')
        or source_fields.get('display_name')
        or ' '.join(part.capitalize() for part in slug.replace('_', '-').split('-'))
    )
    summary = str(minimal.get('summary') or f'Capability import for {slug}.').strip()
    capability_type = str(minimal.get('capability_type') or 'manual_review')
    install_target = str(source_fields.get('install_target') or minimal.get('install_target', {}).get('recommended') or 'auto')
    version = str(minimal.get('version') or '').strip()
    author = str(minimal.get('author') or '').strip()
    compatibility = str(minimal.get('compatibility') or '').strip()
    supported_agents = [str(item) for item in minimal.get('supported_agents') or [] if str(item).strip()]
    description = str(quality_profile.get('description') or source_fields.get('description') or summary.splitlines()[0][:160])
    escaped_description = description.replace('"', '\\"')
    template = load_capability_template(ROOT, capability_type if capability_type in {'skill', 'agent', 'both'} else 'skill')
    constraints = payload.get('uplift', {}).get('quality_constraints') or manifest['layers']['expanded'].get('adjustment_recommendations') or []
    required_inputs = list(
        _source_required_inputs(payload)
        or minimal.get('required_inputs')
        or ['user intent/context', 'relevant source material']
    )
    expected_outputs = list(
        _source_expected_outputs(payload)
        or minimal.get('expected_outputs')
        or ['deterministic recommendation']
    )
    review_timing = [
        '- commit: when commands, behavior, or metadata contracts change',
        '- pull request: when repo structure, CI, release flow, or docs drift materially',
        '- merge: when adjacent capability or doc surfaces changed and drift is likely',
        '- release: verify shipped behavior, install flow, and references against the final state',
    ]
    lines = [
        '---',
        f'name: "{slug}"',
    ]
    if source_fields.get('display_name'):
        lines.append(f'display_name: "{_escape_double_quoted_yaml(source_fields["display_name"])}"')
    if source_fields.get('kind'):
        lines.append(f'kind: "{_escape_double_quoted_yaml(source_fields["kind"])}"')
    lines.extend([
        f'description: "{escaped_description}"',
        f'capability_type: "{capability_type}"',
    ])
    if source_fields.get('agent_tools'):
        lines.append(f'agent_tools: "{_escape_double_quoted_yaml(source_fields["agent_tools"])}"')
    if source_fields.get('version'):
        lines.append(f'version: "{_escape_double_quoted_yaml(source_fields["version"])}"')
    lines.extend([
        f'install_target: "{install_target}"',
    ])
    if version:
        lines.append(f'version: "{version}"')
    if author:
        lines.append(f'author: "{_escape_double_quoted_yaml(author)}"')
    if compatibility:
        lines.append(f'compatibility: "{_escape_double_quoted_yaml(compatibility)}"')
    if supported_agents:
        joined_agents = ', '.join(supported_agents)
        lines.append(f'supported_agents: "{_escape_double_quoted_yaml(joined_agents)}"')
    lines.extend([
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
    ])
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
        lines.extend(['', '## Invocation Hints'])
        invocation_hints = list(manifest.get('invocation_hints') or [])
        if invocation_hints:
            for hint in invocation_hints:
                lines.append(f'- {hint}')
        else:
            lines.append(f'- {payload.get("summary", summary)}')
        lines.append('')
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
    source_fields = _source_frontmatter_fields(result)
    descriptor = build_descriptor(
        manifest=result['manifest'],
        family_slug=slug,
        shared_summary=str(source_fields.get('description') or result['manifest']['layers']['minimal'].get('summary') or ''),
        shared_constraints=_source_constraints(result)
        or tuple(result.get('uplift', {}).get('quality_constraints') or ())
        or tuple(result.get('manifest', {}).get('layers', {}).get('expanded', {}).get('adjustment_recommendations') or ()),
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
    if quality_plan and quality_result:
        descriptor.update(
            quality_descriptor_fields(
                profile=load_quality_profile(ROOT, slug, (quality_plan or {}).get('quality_profile') or 'auto'),
                quality_result=quality_result,
                benchmark_sources=tuple(result.get('benchmark_sources') or ()),
            )
        )
        descriptor['quality_validation_matrix'] = list((quality_plan or {}).get('validation_matrix') or ())
    try:
        ssot_text, apply_guard = _safe_apply_ssot_text(slug, result, quality_result=quality_result)
    except ValueError as exc:
        result['mode'] = 'apply'
        result['status'] = 'manual_review'
        result['detail'] = str(exc)
        result['apply_result'] = {
            'changed_paths': [str(path.relative_to(ROOT)) for path in quality_paths],
            'quality': {
                'profile': (quality_plan or {}).get('quality_profile'),
                'status': (quality_result or {}).get('status'),
                'pass_count': (quality_result or {}).get('pass_count'),
                'stop_reason': (quality_result or {}).get('stop_reason'),
            },
            'deploy_next_step': 'Revise the candidate or preserve the operational source body before apply.',
        }
        return result
    ssot_path.write_text(ssot_text + ('\n' if not ssot_text.endswith('\n') else ''), encoding='utf-8')
    if quality_result and quality_result.get('status') == 'ship':
        baseline_source = _baseline_materialization_payload(slug, result, ssot_text=ssot_text, ssot_path=ssot_path)
        baseline_materialization = persist_source_baseline(
            ROOT,
            slug=slug,
            baseline_text=str(baseline_source['text'] or ''),
            overwrite=False,
            source_kind=str(baseline_source['source_kind'] or ''),
            source_path=baseline_source['source_path'],
            source_sha256=baseline_source['source_sha256'],
            source_commit=baseline_source['source_commit'],
        )
    if baseline_materialization:
        descriptor['historical_baseline'] = dict(descriptor.get('historical_baseline') or {})
        descriptor['historical_baseline']['baseline_path'] = baseline_materialization['baseline_path']
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
    if apply_guard:
        result['apply_guard'] = apply_guard
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
    if payload.get('status') == 'accepted' and args.mode in {'judge', 'apply'}:
        payload = _normalize_payload_for_same_slug_update(payload)
    if payload.get('status') == 'accepted' and args.mode in {'plan', 'judge', 'apply'}:
        payload = _run_quality_for_payload(payload, args)
        payload['preview'] = _preview_payload(
            payload,
            quality_plan=payload.get('quality_plan'),
            quality_result=payload.get('quality_result'),
        )
    if args.mode == 'judge':
        payload['mode'] = 'judge'
    if args.mode == 'apply':
        payload = _apply_payload(payload, args, args.source or [])
    if args.show_rubric and 'classification_rubric' not in payload:
        payload['classification_rubric'] = classification_rubric_payload()
    return _render_output(payload, args.output)


if __name__ == '__main__':
    raise SystemExit(main())
