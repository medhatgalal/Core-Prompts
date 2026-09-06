"""Regressions captured from the 2026-09-06 OpEx UAC plan; no skill-name policy."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util

import pytest

from intent_pipeline.uac_ssot import parse_ssot_frontmatter_and_body
from intent_pipeline.uac_quality import load_quality_profile, run_quality_loop

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/uac-source-integrity'
SOURCE = (FIXTURES / 'original-skill.md').read_text()
LOSSY = (FIXTURES / 'lossy-candidate.md').read_text()
SPEC = importlib.util.spec_from_file_location('uac_integrity_script', ROOT / 'scripts/uac-import.py')
UAC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UAC)


def payload(source_path):
    return {'status': 'accepted', 'source': {'normalized_source': str(source_path)},
            'cross_analysis': {'fit_assessment': 'fits_cleanly'},
            'manifest': {'slug': 'unregistered-rich-skill', 'layers': {
                'minimal': {'capability_type': 'skill', 'summary': 'Executive incident briefing',
                            'required_inputs': ['tickets'], 'expected_outputs': ['briefing']},
                'expanded': {'adjustment_recommendations': []}}},
            'benchmark_sources': [],
            'quality_result': {'status': 'structural_ready', 'final_candidate_text': LOSSY}}


def test_nested_metadata_does_not_override_root_fields(tmp_path):
    text = '---\ninputs:\n  x:\n    name: nested-name\n    description: nested-description\nname: root-name\ndescription: >\n  Root folded\n  description.\n---\nBody\n'
    fields, body = parse_ssot_frontmatter_and_body(text)
    assert fields['name'] == 'root-name'
    assert fields['description'] == 'Root folded description.'
    assert body == 'Body'
    path = tmp_path / 'SKILL.md'
    path.write_text(text)
    assert UAC._source_frontmatter_fields(payload(path)) == fields


@pytest.mark.parametrize('marker, expected', [('|-', 'First\nSecond'), ('>-', 'First Second')])
def test_root_block_scalars_and_legacy_adjacent_headers(marker, expected):
    fields, body = parse_ssot_frontmatter_and_body(f'---\nname: root\ndescription: {marker}\n  First\n  Second\n---\n---\nname: ignored\ncapability_type: both\n---\nBody')
    assert fields == {'name': 'root', 'description': expected, 'capability_type': 'both'}
    assert body == 'Body'


def test_nested_only_description_is_not_root_metadata():
    fields, _ = parse_ssot_frontmatter_and_body('---\ninputs:\n  x:\n    description: nested\n---\nBody')
    assert 'description' not in fields


def test_saved_loss_is_blocked_by_source_fidelity():
    result = run_quality_loop(slug='unregistered-rich-skill',
        profile=load_quality_profile(ROOT, 'unregistered-rich-skill', 'default'),
        candidate_text=LOSSY, source_text=SOURCE,
        descriptor=payload('unused')['manifest'], source_refs=['fixture'], benchmark_sources=[], max_passes=1)
    assert result['status'] == 'manual_review'
    assert any('imported source' in x for x in result['judge_reports'][0]['blockers'])


def test_normalization_retains_operational_body_and_schema(tmp_path):
    path = tmp_path / 'SKILL.md'; path.write_text(SOURCE)
    candidate = UAC._preferred_ssot_text('unregistered-rich-skill', payload(path))
    assert SOURCE.strip() in candidate
    fields = UAC._source_frontmatter_fields(payload(path))
    assert fields['description'].startswith('Generates an executive-ready HTML briefing')


def test_actual_apply_refuses_forged_ready_loss_before_writes(tmp_path, monkeypatch):
    source = tmp_path / 'SKILL.md'; source.write_text(SOURCE)
    workspace = tmp_path / 'repo'; workspace.mkdir()
    monkeypatch.setattr(UAC, 'ROOT', workspace)
    monkeypatch.setattr(UAC, '_preferred_ssot_text', lambda *a, **kw: LOSSY)
    result = UAC._apply_payload(payload(source), SimpleNamespace(yes=True, quality_loop='off'), [str(source)])
    assert result['status'] == 'manual_review'
    assert 'imported source' in result['detail']
    assert not list(workspace.rglob('*'))


def test_non_lossy_apply_selection_positive_control(tmp_path, monkeypatch):
    path = tmp_path / 'SKILL.md'; path.write_text(SOURCE)
    monkeypatch.setattr(UAC, 'ROOT', tmp_path)
    monkeypatch.setattr(UAC, '_preferred_ssot_text', lambda *a, **kw: SOURCE)
    selected, _ = UAC._safe_apply_ssot_text('unregistered-rich-skill', payload(path))
    assert selected.strip() == SOURCE.strip()


@pytest.mark.parametrize('removed', ['BRIEFING.md', 'customfield_10663', '#a93226', 'grid-template-columns: 200px 1fr'])
def test_partial_loss_is_blocked_even_when_shape_and_length_survive(removed):
    from intent_pipeline.uac_quality import evaluate_imported_source_fidelity
    assert removed in SOURCE
    assert evaluate_imported_source_fidelity(SOURCE.replace(removed, 'removed'), SOURCE)
    assert not evaluate_imported_source_fidelity('# Added contract\n\n' + SOURCE, SOURCE)


def test_declared_resource_preservation_and_escape_boundary(tmp_path, monkeypatch):
    from intent_pipeline.uac_quality import evaluate_imported_source_fidelity, _load_declared_capability_resource_texts
    slug = 'unregistered-rich-skill'
    resource = tmp_path / 'sources/capability-resources' / slug / 'original.md'
    resource.parent.mkdir(parents=True); resource.write_text(SOURCE)
    candidate = LOSSY + '\nRead `resources/original.md` for the full operating instructions.\n'
    resources = _load_declared_capability_resource_texts(slug, candidate, repo_root=tmp_path)
    assert not evaluate_imported_source_fidelity(candidate, SOURCE, preserved_resource_texts=resources)
    assert not _load_declared_capability_resource_texts(slug, 'resources/../unregistered-rich-skill/../../outside.md', repo_root=tmp_path)
    path = tmp_path / 'SKILL.md'; path.write_text(SOURCE)
    monkeypatch.setattr(UAC, 'ROOT', tmp_path)
    monkeypatch.setattr(UAC, '_preferred_ssot_text', lambda *a, **kw: candidate)
    selected, _ = UAC._safe_apply_ssot_text(slug, payload(path))
    assert selected.strip() == candidate.strip()


def test_captured_source_is_used_for_remote_or_changed_input(tmp_path):
    path = tmp_path / 'SKILL.md'; path.write_text('changed input')
    captured = {**payload(path), 'source_text': SOURCE}
    assert UAC._source_body_text(captured) == SOURCE
    captured['source']['normalized_source'] = 'https://example.test/SKILL.md'
    assert UAC._source_frontmatter_fields(captured)['name'] == 'opex-briefing'
    assert SOURCE.strip() in UAC._preferred_ssot_text('unregistered-rich-skill', captured)


@pytest.mark.parametrize('header, retained', [
    ('inputs: {approval: {required: true}}', ''),
    ('inputs: # schema\n  approval:\n    required: true', ''),
    ('inputs:\n  first: retained\n\n  approval:\n    required: true', 'inputs:\n  first: retained'),
])
def test_complete_structured_frontmatter_is_required(header, retained):
    from intent_pipeline.uac_quality import evaluate_imported_source_fidelity
    source = f'---\nname: sample\n{header}\n---\nRun the task.'
    candidate = f'---\nname: sample\n{retained}\n---\nRun the task.'
    assert evaluate_imported_source_fidelity(candidate, source)
    assert not evaluate_imported_source_fidelity(source, source)


def test_collection_snapshots_survive_compaction_and_gate_each_member(tmp_path, monkeypatch):
    from intent_pipeline.uac_quality import evaluate_imported_source_fidelity
    member = {**payload('https://example.test/SKILL.md'), 'source_text': SOURCE,
              'summary': 'briefing', 'uplift': {}, 'routing': {}, 'uac': {}, 'recommendation': {}}
    compact = UAC._compact_item_payload('skill', member)
    assert compact['source_text'] == SOURCE
    collection = {**payload(tmp_path), 'items': [compact]}
    assert SOURCE.strip() in UAC._preferred_ssot_text('unregistered-rich-skill', collection)
    assert evaluate_imported_source_fidelity(LOSSY, UAC._source_fidelity_input(collection))
    monkeypatch.setattr(UAC, 'ROOT', tmp_path)
    monkeypatch.setattr(UAC, '_preferred_ssot_text', lambda *a, **kw: LOSSY)
    result = UAC._apply_payload(collection, SimpleNamespace(yes=True, quality_loop='off'), [str(tmp_path)])
    assert result['status'] == 'manual_review'
    assert not list(tmp_path.rglob('*'))


@pytest.mark.parametrize('header', ['"inputs":\n  approval:\n    required: true', 'inputs: &schema\n  approval:\n    required: true', "'inputs': {approval: true}"])
def test_unrecognized_header_schemas_fail_closed(header):
    from intent_pipeline.uac_quality import evaluate_imported_source_fidelity
    source = f'---\nname: sample\n{header}\n---\nRun the task.'
    assert evaluate_imported_source_fidelity('---\nname: sample\n---\nRun the task.', source)


@pytest.mark.parametrize('marker, expected', [('|-', 'First line\nSecond line'), ('> # summary', 'First line Second line'), ('>2', 'First line Second line')])
def test_multiline_description_round_trip(marker, expected):
    source = f'---\nname: sample\ndescription: {marker}\n  First line\n  Second line\n---\nRun the task.'
    candidate = UAC._preferred_ssot_text('unregistered-rich-skill', {**payload('remote'), 'source_text': source})
    assert parse_ssot_frontmatter_and_body(source)[0]['description'] == expected
    assert parse_ssot_frontmatter_and_body(candidate)[0]['description'] == expected


def test_historical_and_imported_resource_checks_share_apply_evidence(tmp_path, monkeypatch):
    slug = 'unregistered-rich-skill'
    long_source = SOURCE + '\nAdditional retained instructions.\n' * 150
    (tmp_path / 'ssot').mkdir()
    (tmp_path / 'ssot' / f'{slug}.md').write_text(long_source)
    resource = tmp_path / 'sources/capability-resources' / slug / 'original.md'
    resource.parent.mkdir(parents=True); resource.write_text(long_source)
    path = tmp_path / 'SKILL.md'; path.write_text(long_source)
    candidate = LOSSY + '\nRead `resources/original.md` for the complete instructions.\n'
    monkeypatch.setattr(UAC, 'ROOT', tmp_path)
    monkeypatch.setattr(UAC, '_preferred_ssot_text', lambda *a, **kw: candidate)
    selected, _ = UAC._safe_apply_ssot_text(slug, payload(path))
    assert 'resources/original.md' in selected


def test_missing_legacy_source_blocks_actual_apply(tmp_path, monkeypatch):
    monkeypatch.setattr(UAC, 'ROOT', tmp_path)
    monkeypatch.setattr(UAC, '_preferred_ssot_text', lambda *a, **kw: LOSSY)
    result = UAC._apply_payload(payload('https://example.test/unavailable.md'), SimpleNamespace(yes=True, quality_loop='off'), [])
    assert result['status'] == 'manual_review'
    assert 're-ingest' in result['detail']
    assert not list(tmp_path.rglob('*'))


def test_folded_paragraphs_and_quoted_root_keys():
    fields, _ = parse_ssot_frontmatter_and_body('---\n"name": sample\n"description": >-\n  First line\n  continued.\n\n  Next paragraph.\n---\nBody')
    assert fields['name'] == 'sample'
    assert fields['description'] == 'First line continued.\nNext paragraph.'


def test_rich_collection_gets_canonical_root_frontmatter():
    rich = (ROOT / 'ssot/code-review.md').read_text()
    collection = {**payload('collection'), 'items': [
        {'status': 'accepted', 'display_name': 'review', 'source_text': rich, 'source': {'normalized_source': 'remote'}}]}
    candidate = UAC._preferred_ssot_text('unregistered-rich-skill', collection)
    fields, _ = parse_ssot_frontmatter_and_body(candidate)
    assert fields['name'] == 'unregistered-rich-skill'
    assert fields['capability_type'] == 'skill'
    assert rich.strip() in candidate


def test_redacted_snapshot_never_requires_restoring_original_header(tmp_path, monkeypatch):
    # Synthetic secret: the retained contract is the approved/redacted snapshot.
    original = SOURCE.replace('inputs:', 'credentials:\n  api_key: synthetic-private-value\ninputs:', 1)
    redacted = original.replace('synthetic-private-value', '[REDACTED]')
    path = tmp_path / 'SKILL.md'; path.write_text(original)
    imported = {**payload(path), 'source_text': redacted,
                'source_redactions': [{'field': 'credentials.api_key', 'reason': 'credential'}]}
    candidate = UAC._preferred_ssot_text('unregistered-rich-skill', imported)
    assert '[REDACTED]' in candidate
    assert 'synthetic-private-value' not in candidate
    monkeypatch.setattr(UAC, 'ROOT', tmp_path)
    monkeypatch.setattr(UAC, '_preferred_ssot_text', lambda *a, **kw: candidate)
    selected, _ = UAC._safe_apply_ssot_text('unregistered-rich-skill', imported)
    assert 'synthetic-private-value' not in selected
    assert imported['source_redactions'] == [{'field': 'credentials.api_key', 'reason': 'credential'}]


@pytest.mark.parametrize('fixture', ['original-skill.md', 'loop-package/SKILL.md'])
def test_retention_wrapper_does_not_replace_source_outcomes(fixture):
    source = (FIXTURES / fixture).read_text()
    imported = {**payload('remote'), 'source_text': source}
    # Deliberately wrong inferred outputs must not become task instructions.
    imported['manifest']['layers']['minimal']['expected_outputs'] = ['uplift payload', 'deployment guidance']
    candidate = UAC._preferred_ssot_text('unregistered-rich-skill', imported)
    wrapper = candidate.split('## Imported operating instructions', 1)[0]
    assert source.strip() in candidate
    assert 'uplift payload' not in wrapper
    assert 'deployment guidance' not in wrapper
    assert 'timestamp>-summary.md' not in wrapper
    assert 'current state summary' not in wrapper
    assert 'source contract' in wrapper


def test_seven_file_loop_collection_preserves_each_contract():
    from intent_pipeline.uac_quality import evaluate_imported_source_fidelity
    package = FIXTURES / 'loop-package'
    files = sorted(path for path in package.rglob('*') if path.is_file())
    assert len(files) == 7
    items = [{'status': 'accepted', 'display_name': str(path.relative_to(package)),
              'source_text': path.read_text(), 'source': {'normalized_source': str(path)}} for path in files]
    collection = {**payload(package), 'items': items}
    candidate = UAC._preferred_ssot_text('unregistered-rich-skill', collection)
    contracts = UAC._source_fidelity_input(collection)
    assert not evaluate_imported_source_fidelity(candidate, contracts)
    for item in items:
        assert item['source_text'].strip() in candidate
        assert evaluate_imported_source_fidelity(candidate.replace(item['source_text'].strip(), ''), contracts)
