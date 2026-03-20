from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from intent_pipeline.uac_manifest import (
    analyze_manifest_fit,
    build_capability_manifest,
    infer_install_target,
    normalize_persisted_source_reference,
    orchestrator_handoff_payload,
)

ROOT = Path(__file__).resolve().parents[1]


def test_infer_install_target_prefers_repo_local_for_repo_file() -> None:
    target = infer_install_target(
        'ssot/uac-import.md',
        source_type='LOCAL_FILE',
        repo_root=ROOT,
    )

    assert target['recommended'] == 'repo_local'
    assert target['confirmation_required_for_apply'] is True


def test_infer_install_target_prefers_global_for_remote_source() -> None:
    target = infer_install_target(
        'https://github.com/example/repo/tree/main/prompts',
        source_type='GITHUB_TREE',
        repo_root=ROOT,
    )

    assert target['recommended'] == 'global'


def test_normalize_persisted_source_reference_uses_repo_relative_for_repo_file() -> None:
    normalized = normalize_persisted_source_reference(
        str((ROOT / 'ssot' / 'architecture.md').resolve()),
        source_type='LOCAL_FILE',
        repo_root=ROOT,
    )

    assert normalized == 'ssot/architecture.md'


def test_build_capability_manifest_creates_layered_schema() -> None:
    manifest = build_capability_manifest(
        slug='architecture-review',
        source_metadata={
            'source_type': 'URL',
            'normalized_source': 'https://example.com/architecture.md',
            'policy_rule_id': 'rule-1',
            'content_type': 'text/markdown',
            'content_sha256': 'abc123',
        },
        raw_text='Primary Objective: review architecture\nIn Scope:\n- boundaries\nConstraints:\n- deterministic',
        summary='Architecture review summary',
        assessment_payload={
            'capability_type': 'skill',
            'confidence': 0.91,
            'rationale': 'Structured workflow',
            'emitted_surfaces': {'codex': ['codex_skill'], 'claude': ['claude_skill']},
        },
        uplift_payload={'primary_objective': 'review architecture', 'in_scope': ['boundaries'], 'quality_constraints': ['deterministic']},
        routing_payload={'route_profile': 'VALIDATION'},
        repo_root=ROOT,
    )

    assert manifest['manifest_version'] == 'capability-fabric.v0'
    assert set(manifest['layers']) == {'minimal', 'expanded', 'org_graph'}
    assert manifest['layers']['minimal']['tool_policy']['forbidden']
    assert manifest['layers']['org_graph']['authority_tier'] == 'advisory'


def test_build_capability_manifest_persists_repo_relative_local_sources() -> None:
    manifest = build_capability_manifest(
        slug='architecture',
        source_metadata={
            'source_type': 'LOCAL_FILE',
            'normalized_source': str((ROOT / 'ssot' / 'architecture.md').resolve()),
            'policy_rule_id': 'ssot.architecture',
            'content_type': 'text/markdown',
            'content_sha256': 'ssot',
        },
        raw_text='architecture review',
        summary='Architecture review summary',
        assessment_payload={
            'capability_type': 'skill',
            'confidence': 0.91,
            'rationale': 'Structured workflow',
            'emitted_surfaces': {'codex': ['codex_skill'], 'claude': ['claude_skill']},
        },
        uplift_payload={'primary_objective': 'review architecture', 'in_scope': ['boundaries'], 'quality_constraints': ['deterministic']},
        routing_payload={'route_profile': 'VALIDATION'},
        repo_root=ROOT,
    )

    minimal = manifest['layers']['minimal']
    assert minimal['resources'] == ['ssot/architecture.md']
    assert minimal['source_provenance']['normalized_source'] == 'ssot/architecture.md'
    assert minimal['install_target']['recommended'] == 'repo_local'


def test_analyze_manifest_fit_detects_duplicate_slug() -> None:
    candidate = {
        'slug': 'architecture',
        'layers': {'minimal': {'capability_type': 'skill', 'role': 'architect', 'domain_tags': ['architecture']}}
    }
    existing = [
        {
            'slug': 'architecture',
            'layers': {'minimal': {'capability_type': 'skill', 'role': 'architect', 'domain_tags': ['architecture']}}
        }
    ]

    analysis = analyze_manifest_fit(candidate, existing)

    assert analysis.duplicate_risk == 'high'
    assert analysis.fit_assessment == 'manual_review'


def test_orchestrator_handoff_payload_exposes_advisory_quality_fields() -> None:
    manifest = {
        'slug': 'architecture',
        'display_name': 'Architecture Studio',
        'quality_profile': 'architecture',
        'quality_status': 'ship',
        'consumption_hints': {
            'preferred_use_cases': ['API design'],
            'artifact_conventions': ['architecture/spec.md'],
            'invocation_style': 'interactive_or_artifact_oriented',
            'requires_human_confirmation': True,
        },
        'layers': {
            'minimal': {
                'capability_type': 'skill',
                'summary': 'Architecture Studio',
                'role': 'architect',
                'domain_tags': ['architecture'],
                'required_inputs': ['requirements'],
                'expected_outputs': ['architecture recommendation'],
                'tool_policy': {
                    'allowed': ['metadata publication'],
                    'forbidden': ['orchestration'],
                },
                'install_target': {'recommended': 'global'},
                'emitted_surfaces': {'codex': ['codex_skill']},
                'confidence': 0.95,
                'review_status': 'ready_for_orchestrator_review',
            },
            'expanded': {
                'overlap_candidates': [],
                'relationship_suggestions': [],
            },
            'org_graph': {
                'org_role': 'architect',
                'reports_to_suggestions': [],
                'delegates_to_suggestions': [],
                'collaborates_with_suggestions': [],
                'authority_tier': 'advisory',
                'work_graph_impact': 'Adds an advisory architecture capability.',
            },
        },
    }

    payload = orchestrator_handoff_payload([manifest])
    capability = payload['capabilities'][0]

    assert capability['advisory_only'] is True
    assert capability['display_name'] == 'Architecture Studio'
    assert capability['quality_status'] == 'ship'
    assert capability['benchmark_profile'] == 'architecture'
    assert capability['preferred_use_cases'] == ['API design']
    assert capability['artifact_conventions'] == ['architecture/spec.md']
    assert capability['invocation_style'] == 'interactive_or_artifact_oriented'
    assert capability['requires_human_confirmation'] is True


def test_uac_import_multi_source_returns_collection_manifest(tmp_path: Path) -> None:
    a = tmp_path / 'a.md'
    b = tmp_path / 'b.md'
    a.write_text('Primary Objective: classify architecture prompts\n\nIn Scope:\n- design\n\nConstraints:\n- deterministic', encoding='utf-8')
    b.write_text('Primary Objective: converge prompt family\n\nIn Scope:\n- architecture\n\nConstraints:\n- preserve boundaries', encoding='utf-8')

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts' / 'uac-import.py'),
            '--mode',
            'plan',
            '--source',
            str(a),
            '--source',
            str(b),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload['source']['type'] == 'MULTI_SOURCE'
    assert payload['collection']['collection_type'] in {'skill_family', 'mixed_review'}
    assert 'manifest' in payload
    assert 'cross_analysis' in payload
    assert payload['plan']['accepted_item_count'] == 2
