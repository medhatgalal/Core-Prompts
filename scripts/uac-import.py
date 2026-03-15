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
from intent_pipeline.uac_capabilities import deployment_matrix_payload, emitted_surfaces_by_cli, recommended_target_systems
from intent_pipeline.uac_extract import extract_uac_analysis_text
from intent_pipeline.uac_manifest import analyze_manifest_fit, build_capability_manifest, orchestrator_handoff_payload
from intent_pipeline.uac_sources import (
    aggregate_collection_recommendation,
    enumerate_github_tree,
    enumerate_local_directory,
)
from intent_pipeline.uac_ssot import audit_ssot_entries, build_ssot_manifest_entry, build_ssot_handoff_contract, load_ssot_entries, render_audit_table
from intent_pipeline.uplift.engine import run_uplift_engine


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Capability Fabric UAC shell. Import one or more external sources, audit existing SSOT, explain the capability rubric, '
            'or plan how a source would land in SSOT without writing files.'
        ),
        epilog=(
            'Examples:\n'
            '  python3.11 scripts/uac-import.py --mode import --source /abs/path/to/prompt.md\n'
            '  python3.11 scripts/uac-import.py --mode import --source /abs/path/to/folder --target-system codex\n'
            '  python3.11 scripts/uac-import.py --mode import --source https://raw.githubusercontent.com/org/repo/main/file.md\n'
            '  python3.11 scripts/uac-import.py --mode import --source https://github.com/org/repo/tree/main/prompts --show-rubric\n'
            '  python3.11 scripts/uac-import.py --mode import --source a.md --source b.md --mode plan\n'
            '  python3.11 scripts/uac-import.py --mode audit --output table\n'
            '  python3.11 scripts/uac-import.py --mode explain --output table\n'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument('--mode', choices=('import', 'audit', 'explain', 'plan', 'apply'), default='import')
    parser.add_argument('--source', action='append', help='File path, directory path, raw https URL, GitHub tree/repo URL, or ssot for audit mode')
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
    return [build_ssot_manifest_entry(entry) for entry in load_ssot_entries(ROOT / 'ssot')]


def _build_analysis_bundle(
    *,
    slug: str,
    raw_text: str,
    source_metadata: dict[str, str],
    extraction: dict[str, str | None],
    summary: str,
    uplift: dict[str, Any],
    routing: dict[str, Any],
    assessment: dict[str, Any],
    target_system: str,
    install_target: str,
) -> dict[str, Any]:
    manifest = build_capability_manifest(
        slug=slug,
        source_metadata=source_metadata,
        raw_text=raw_text,
        summary=summary,
        assessment_payload=assessment,
        uplift_payload=uplift,
        routing_payload=routing,
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
    return {
        'status': 'accepted',
        'source': {
            'type': source_metadata['source_type'],
            'normalized_source': source_metadata['normalized_source'],
            'policy_rule_id': source_metadata['policy_rule_id'],
            'content_type': source_metadata['content_type'],
            'content_sha256': source_metadata['content_sha256'],
        },
        'extraction': extraction,
        'summary': summary,
        'uplift': {
            'primary_objective': uplift['intent'].get('primary_objective'),
            'in_scope': uplift['intent'].get('in_scope'),
            'out_of_scope': uplift['intent'].get('out_of_scope'),
            'quality_constraints': uplift['intent'].get('quality_constraints'),
        },
        'routing': {
            'decision': routing['route_selection']['decision'],
            'route_profile': routing['route_selection']['route_profile'],
            'dominant_rule_id': routing['route_selection']['dominant_rule_id'],
            'missing_evidence': routing['route_selection']['missing_evidence'],
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
        'handoff_contract': orchestrator_handoff_payload([manifest]),
        'recommendation': {
            'primary_target_systems': recommended_target_systems(target_system, assessment['capability_type']),
            'install_target': manifest['layers']['minimal']['install_target'],
            'next_actions': _next_actions(assessment['capability_type'], routing['route_selection']['route_profile'], cross_analysis['fit_assessment']),
        },
    }


def _import_local_file(path: Path, *, target_system: str, mode: str, install_target: str) -> dict[str, Any]:
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
    ).as_payload()
    payload = _build_analysis_bundle(
        slug=_slugify(path.stem),
        raw_text=ingestion.raw_text,
        source_metadata=ingestion.source_metadata,
        extraction=extraction.as_payload(),
        summary=summary,
        uplift=uplift.as_payload(),
        routing=routing.as_payload(),
        assessment=assessment,
        target_system=target_system,
        install_target=install_target,
    )
    if mode in {'plan', 'apply'}:
        payload['plan'] = _single_source_plan(path.name, payload)
    if mode == 'apply':
        payload['status'] = 'planned_only'
        payload['detail'] = 'apply mode requires an explicit target confirmation flow and is intentionally non-mutating in this release.'
    return payload


def _import_raw_url(source: str, *, max_bytes: int, timeout_seconds: int, target_system: str, mode: str, install_target: str) -> dict[str, Any]:
    if _looks_like_wrapper_source(source):
        return _import_remote_artifact(source, normalized_source=source, target_system=target_system, timeout_seconds=timeout_seconds, mode=mode, install_target=install_target)
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
        extraction = extract_uac_analysis_text(ingestion.raw_text, source)
        summary = run_phase1_pipeline(source, **shared_kwargs)
        uplift = run_uplift_engine(extraction.analysis_text, source_metadata=ingestion.source_metadata)
        routing = run_semantic_routing(uplift)
        assessment = assess_uac_source(
            ingestion.raw_text,
            analysis_text=extraction.analysis_text,
            source_metadata=ingestion.source_metadata,
            source_hint=source,
        ).as_payload()
    payload = _build_analysis_bundle(
        slug=_slugify(Path(urlsplit(source).path).stem or 'remote-source'),
        raw_text=ingestion.raw_text,
        source_metadata=ingestion.source_metadata,
        extraction=extraction.as_payload(),
        summary=summary,
        uplift=uplift.as_payload(),
        routing=routing.as_payload(),
        assessment=assessment,
        target_system=target_system,
        install_target=install_target,
    )
    if mode in {'plan', 'apply'}:
        payload['plan'] = _single_source_plan(source, payload)
    if mode == 'apply':
        payload['status'] = 'planned_only'
        payload['detail'] = 'apply mode requires an explicit target confirmation flow and is intentionally non-mutating in this release.'
    return payload


def _import_remote_artifact(
    raw_url: str,
    *,
    normalized_source: str,
    target_system: str,
    timeout_seconds: int,
    mode: str,
    install_target: str,
) -> dict[str, Any]:
    raw_text = _fetch_remote_text(raw_url, timeout_seconds=timeout_seconds)
    source_metadata = {
        'source_type': 'URL',
        'normalized_source': normalized_source,
        'policy_rule_id': _policy_rule_id(raw_url),
        'content_type': mimetypes.guess_type(urlsplit(raw_url).path)[0] or 'text/plain',
        'content_sha256': sha256(raw_text.encode('utf-8')).hexdigest(),
    }
    extraction = extract_uac_analysis_text(raw_text, raw_url)
    uplift = run_uplift_engine(extraction.analysis_text, source_metadata=source_metadata)
    routing = run_semantic_routing(uplift)
    assessment = assess_uac_source(
        raw_text,
        analysis_text=extraction.analysis_text,
        source_metadata=source_metadata,
        source_hint=normalized_source,
    ).as_payload()
    summary = run_phase1_pipeline_from_text(extraction.analysis_text)
    payload = _build_analysis_bundle(
        slug=_slugify(Path(urlsplit(normalized_source).path).stem or 'remote-artifact'),
        raw_text=raw_text,
        source_metadata=source_metadata,
        extraction=extraction.as_payload(),
        summary=summary,
        uplift=uplift.as_payload(),
        routing=routing.as_payload(),
        assessment=assessment,
        target_system=target_system,
        install_target=install_target,
    )
    if mode in {'plan', 'apply'}:
        payload['plan'] = _single_source_plan(normalized_source, payload)
    if mode == 'apply':
        payload['status'] = 'planned_only'
        payload['detail'] = 'apply mode requires an explicit target confirmation flow and is intentionally non-mutating in this release.'
    return payload


def _collection_manifest(source_label: str, source_type: str, normalized_source: str, collection: dict[str, Any], item_payloads: list[dict[str, Any]], install_target: str) -> dict[str, object]:
    capability_type = str(collection['capability_type'])
    combined_text = '\n\n'.join(str(item.get('summary', '')) for item in item_payloads if item.get('status') in {'accepted', 'planned_only'})
    assessment = {
        'capability_type': capability_type,
        'recommended_surface': capability_type,
        'confidence': 0.84 if capability_type != 'manual_review' else 0.55,
        'signals': ['collection-level recommendation'],
        'rationale': collection['rationale'],
        'rubric': classification_rubric_payload(),
        'deployment_matrix': deployment_matrix_payload(),
        'scorecard': {'accepted_item_count': len([item for item in item_payloads if item.get('status') in {'accepted', 'planned_only'}])},
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
    install = manifest['layers']['minimal']['install_target']
    if install_target != 'auto':
        install['recommended'] = install_target
        install['rationale'] = f'user override requested {install_target}'
        install['confidence'] = 1.0
    return manifest


def _import_local_directory(directory: Path, *, recurse: bool, max_items: int, target_system: str, mode: str, install_target: str) -> dict[str, Any]:
    candidates = enumerate_local_directory(directory, recurse=recurse, max_items=max_items)
    item_payloads = [_import_local_file(Path(candidate.locator), target_system=target_system, mode='import', install_target=install_target) for candidate in candidates]
    recommendation = aggregate_collection_recommendation(directory.name, item_payloads)
    manifest = _collection_manifest(directory.name, 'LOCAL_DIRECTORY', str(directory), recommendation.as_payload(), item_payloads, install_target)
    cross_analysis = analyze_manifest_fit(manifest, _existing_manifests()).as_payload()
    manifest['layers']['expanded']['overlap_candidates'] = [item['slug'] for item in cross_analysis['overlap_report'] if isinstance(item, dict) and item.get('slug')]
    payload = {
        'status': 'accepted',
        'source': {
            'type': 'LOCAL_DIRECTORY',
            'normalized_source': str(directory),
            'item_count': len(item_payloads),
        },
        'collection': recommendation.as_payload(),
        'manifest': manifest,
        'cross_analysis': cross_analysis,
        'handoff_contract': orchestrator_handoff_payload([manifest]),
        'items': [_compact_item_payload(candidate.display_name, item) for candidate, item in zip(candidates, item_payloads)],
    }
    if mode in {'plan', 'apply'}:
        payload['plan'] = _collection_plan(directory.name, payload['collection'], item_payloads, manifest)
    if mode == 'apply':
        payload['status'] = 'planned_only'
        payload['detail'] = 'apply mode requires explicit target confirmation and remains non-mutating.'
    return payload


def _import_github_tree(source: str, *, recurse: bool, max_items: int, timeout_seconds: int, target_system: str, mode: str, install_target: str) -> dict[str, Any]:
    tree_ref, candidates = enumerate_github_tree(source, recurse=recurse, max_items=max_items, timeout_seconds=timeout_seconds)
    item_payloads = [
        _import_remote_artifact(candidate.locator, normalized_source=candidate.normalized_source, target_system=target_system, timeout_seconds=timeout_seconds, mode='import', install_target=install_target)
        for candidate in candidates
    ]
    source_label = Path(tree_ref.path).name or tree_ref.repo
    recommendation = aggregate_collection_recommendation(source_label, item_payloads)
    manifest = _collection_manifest(source_label, 'GITHUB_TREE', tree_ref.normalized_source, recommendation.as_payload(), item_payloads, install_target)
    cross_analysis = analyze_manifest_fit(manifest, _existing_manifests()).as_payload()
    manifest['layers']['expanded']['overlap_candidates'] = [item['slug'] for item in cross_analysis['overlap_report'] if isinstance(item, dict) and item.get('slug')]
    payload = {
        'status': 'accepted',
        'source': {
            'type': 'GITHUB_TREE',
            'normalized_source': tree_ref.normalized_source,
            'owner': tree_ref.owner,
            'repo': tree_ref.repo,
            'ref': tree_ref.ref,
            'path': tree_ref.path,
            'item_count': len(item_payloads),
        },
        'collection': recommendation.as_payload(),
        'manifest': manifest,
        'cross_analysis': cross_analysis,
        'handoff_contract': orchestrator_handoff_payload([manifest]),
        'items': [_compact_item_payload(candidate.display_name, item) for candidate, item in zip(candidates, item_payloads)],
    }
    if mode in {'plan', 'apply'}:
        payload['plan'] = _collection_plan(source_label, payload['collection'], item_payloads, manifest)
    if mode == 'apply':
        payload['status'] = 'planned_only'
        payload['detail'] = 'apply mode requires explicit target confirmation and remains non-mutating.'
    return payload


def _compact_item_payload(display_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    compact = {'display_name': display_name, 'status': payload.get('status')}
    if payload.get('status') in {'accepted', 'planned_only'}:
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
                'recommendation': payload['recommendation'],
            }
        )
    else:
        compact['rejection'] = payload.get('rejection')
    return compact


def _single_source_plan(source_label: str, payload: dict[str, Any]) -> dict[str, Any]:
    slug = _slugify(source_label)
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
            'manifest_layers': list(manifest['layers'].keys()),
            'advisory_handoff_contract': True,
        },
    }


def _collection_plan(source_label: str, collection: dict[str, Any], item_payloads: list[dict[str, Any]], manifest: dict[str, object]) -> dict[str, Any]:
    accepted_items = [item for item in item_payloads if item.get('status') in {'accepted', 'planned_only'}]
    slug = _slugify(collection.get('recommended_slug') or source_label)
    return {
        'proposed_ssot_slug': slug,
        'collection_type': collection['collection_type'],
        'capability_type': collection['capability_type'],
        'shared_roof': collection['shared_roof'],
        'accepted_item_count': len(accepted_items),
        'install_target': manifest['layers']['minimal']['install_target'],
        'manifest_layers': list(manifest['layers'].keys()),
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


def _rejection_payload(source: str, error: UrlSourceRejectedError, *, mode: str) -> dict[str, Any]:
    rejection = error.rejection
    payload = {
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
    if mode in {'plan', 'apply'}:
        payload['plan'] = {'proposed_ssot_slug': _slugify(source), 'deployment_intent': 'hold_for_review'}
    return payload


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
        'notes': [
            'command, plugin, power, and extension are wrapper surfaces rather than capability types',
            'Capability Fabric/UAC publishes advisory manifests and handoff contracts only',
            'existing SSOT can be audited with --mode audit',
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


def _process_source(source: str, *, args: argparse.Namespace) -> dict[str, Any]:
    if _looks_like_url(source) and not _is_raw_text_url(source):
        return _import_github_tree(
            source,
            recurse=not args.no_recurse,
            max_items=args.max_items,
            timeout_seconds=args.timeout_seconds,
            target_system=args.target_system,
            mode=args.mode,
            install_target=args.install_target,
        )
    if _looks_like_url(source):
        return _import_raw_url(
            source,
            max_bytes=args.max_bytes,
            timeout_seconds=args.timeout_seconds,
            target_system=args.target_system,
            mode=args.mode,
            install_target=args.install_target,
        )
    path = Path(source).expanduser().resolve()
    if path.is_dir():
        return _import_local_directory(
            path,
            recurse=not args.no_recurse,
            max_items=args.max_items,
            target_system=args.target_system,
            mode=args.mode,
            install_target=args.install_target,
        )
    if path.is_file():
        return _import_local_file(path, target_system=args.target_system, mode=args.mode, install_target=args.install_target)
    raise SystemExit(
        'uac-import.py requires a file path, directory path, raw https URL, or GitHub folder URL. '
        f'Got: {path}'
    )


def _multi_source_payload(sources: list[str], args: argparse.Namespace) -> dict[str, Any]:
    item_payloads = []
    for source in sources:
        item_payloads.append(_process_source(source, args=args))
    recommendation = aggregate_collection_recommendation('multi-source-import', item_payloads)
    manifest = _collection_manifest('multi-source-import', 'MULTI_SOURCE', '::'.join(sources), recommendation.as_payload(), item_payloads, args.install_target)
    cross_analysis = analyze_manifest_fit(manifest, _existing_manifests()).as_payload()
    manifest['layers']['expanded']['overlap_candidates'] = [item['slug'] for item in cross_analysis['overlap_report'] if isinstance(item, dict) and item.get('slug')]
    payload = {
        'status': 'accepted',
        'mode': args.mode,
        'source': {'type': 'MULTI_SOURCE', 'normalized_source': sources, 'item_count': len(item_payloads)},
        'collection': recommendation.as_payload(),
        'manifest': manifest,
        'cross_analysis': cross_analysis,
        'handoff_contract': orchestrator_handoff_payload([manifest]),
        'items': [_compact_item_payload(source, item) for source, item in zip(sources, item_payloads)],
        'plan': _collection_plan('multi-source-import', recommendation.as_payload(), item_payloads, manifest),
    }
    if args.mode == 'apply':
        payload['status'] = 'planned_only'
        payload['detail'] = 'apply mode requires explicit target confirmation and remains non-mutating.'
    return payload


def main() -> int:
    args = _parse_args()
    mode = args.mode

    if mode == 'explain':
        payload = _explain_payload()
        return _render_output(payload, args.output)

    if mode == 'audit':
        payload = _audit_payload()
        if args.show_rubric:
            payload['classification_rubric'] = classification_rubric_payload()
        return _render_output(payload, args.output)

    sources = [value.strip() for value in args.source or [] if value and value.strip()]
    if not sources:
        raise SystemExit('--source is required for import, plan, and apply modes')

    try:
        if len(sources) > 1:
            payload = _multi_source_payload(sources, args)
        else:
            payload = _process_source(sources[0], args=args)
    except UrlSourceRejectedError as error:
        payload = _rejection_payload(sources[0], error, mode=mode)

    payload['mode'] = mode
    if args.show_rubric:
        payload['classification_rubric'] = classification_rubric_payload()
        payload['deployment_matrix'] = deployment_matrix_payload()

    return _render_output(payload, args.output)


if __name__ == '__main__':
    raise SystemExit(main())
