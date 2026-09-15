from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from intent_pipeline.uac_agent_review import agent_surface_review
from intent_pipeline.uac_baselines import text_sha256

ROOT = Path(__file__).resolve().parents[1]
SKILL = '---\nname: fixture\ncapability_type: skill\n---\n# Workflow\nUse a dedicated read-only execution profile.\n'
BOTH = SKILL.replace('capability_type: skill', 'capability_type: both')
PROVIDERS = ('codex', 'gemini', 'claude', 'kiro')


def review(original=SKILL, candidate=BOTH):
    return {
        'schema_version': 'UACRequirementReview.v1', 'slug': 'fixture',
        'original_sha256': text_sha256(original), 'candidate_sha256': text_sha256(candidate),
        'effective_sha256': text_sha256(candidate), 'verdict': 'approved',
        'user_approval': {'source': 'user', 'decision': 'approved', 'slug': 'fixture',
                          'providers': list(PROVIDERS), 'reference': 'test-user-message:explicit-agent-addition'},
        'reviewer': {'agent_id': 'reviewer', 'author_agent_id': 'author', 'independent': True},
        'requirements': [{'id': 'all', 'source_start_line': 1, 'source_end_line': len(original.splitlines()),
                          'rationale': 'The workflow remains intact.', 'disposition': 'preserved',
                          'candidate_excerpt': '# Workflow'}],
        'agent_execution_needs': [
            {'provider': provider, 'execution_need': 'A saved read-only profile is required.',
             'why_generic_worker_insufficient': 'The generic profile permits writes.',
             'candidate_excerpt': 'dedicated read-only execution profile'}
            for provider in PROVIDERS
        ],
    }


def check(tmp_path, reviews=(), current=SKILL, candidate=BOTH):
    if current is not None:
        (tmp_path / 'ssot').mkdir(exist_ok=True)
        (tmp_path / 'ssot' / 'fixture.md').write_text(current)
    return agent_surface_review(tmp_path, slug='fixture', candidate_text=candidate,
                                effective_text=candidate, reviews=reviews, original_texts=[SKILL])


@pytest.mark.parametrize('current', [None, SKILL])
def test_new_or_expanded_agent_requires_review_for_every_provider(tmp_path, current):
    result = check(tmp_path, current=current)
    assert result['status'] == 'manual_review'
    assert set(result['added_providers']) == set(PROVIDERS)
    assert len(result['blockers']) == 8


def test_existing_explicit_agents_are_preserved_without_new_attestation(tmp_path):
    assert check(tmp_path, current=BOTH)['status'] == 'unchanged'


def test_bound_independent_provider_review_admits_expansion(tmp_path):
    result = check(tmp_path, reviews=[review()])
    assert result['status'] == 'reviewed'
    assert result['blockers'] == []
    assert result['identity_authenticated'] is False
    assert result['behavioral_status'] == 'behavioral_pending'


@pytest.mark.parametrize('mutation', ['missing_provider', 'stale', 'self_review', 'excerpt', 'empty_need', 'duplicate_provider', 'malformed'])
def test_inadequate_provider_review_cannot_admit_expansion(tmp_path, mutation):
    candidate_review = copy.deepcopy(review())
    if mutation == 'missing_provider':
        candidate_review['agent_execution_needs'].pop()
    elif mutation == 'stale':
        candidate_review['candidate_sha256'] = '0' * 64
    elif mutation == 'self_review':
        candidate_review['reviewer']['agent_id'] = 'author'
    elif mutation == 'excerpt':
        candidate_review['agent_execution_needs'][0]['candidate_excerpt'] = 'missing excerpt'
    elif mutation == 'empty_need':
        candidate_review['agent_execution_needs'][0]['why_generic_worker_insufficient'] = ''
    elif mutation == 'duplicate_provider':
        candidate_review['agent_execution_needs'].append(candidate_review['agent_execution_needs'][0])
    else:
        candidate_review['agent_execution_needs'] = 'invalid'
    assert check(tmp_path, reviews=[candidate_review])['status'] == 'manual_review'


def test_final_candidate_change_invalidates_review(tmp_path):
    assert check(tmp_path, reviews=[review()], candidate=BOTH + '\nChanged behavior.\n')['status'] == 'manual_review'


def test_quality_loop_off_apply_refuses_before_any_writes(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('agent_gate_uac', ROOT / 'scripts' / 'uac-import.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, '_preferred_ssot_text', lambda *a, **kw: BOTH)
    monkeypatch.setattr(module, '_snapshot_apply_artifacts', lambda: {})
    payload = {'status': 'accepted', 'manifest': {'slug': 'fixture'}, 'source_text': SKILL}
    args = SimpleNamespace(yes=True, quality_loop='off', requirement_review=[])
    result = module._apply_payload(payload, args, [])
    assert result['status'] == 'manual_review'
    assert 'Agent emission refused' in result['detail']
    assert list(tmp_path.iterdir()) == []


def test_quality_loop_off_plan_exposes_missing_admission(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('agent_gate_plan_uac', ROOT / 'scripts' / 'uac-import.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, '_preferred_ssot_text', lambda *a, **kw: BOTH)
    payload = {'status': 'accepted', 'manifest': {'slug': 'fixture'}, 'source_text': SKILL}
    result = module._run_quality_for_payload(payload, SimpleNamespace(quality_loop='off', requirement_review=[]))
    assert result['agent_surface_review']['status'] == 'manual_review'


def test_builder_rejects_direct_expansion_before_any_output_write(tmp_path, monkeypatch):
    from intent_pipeline import consumer_shell
    (tmp_path / 'ssot').mkdir()
    (tmp_path / 'ssot' / 'fixture.md').write_text(BOTH)
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root: ({'ssot_sources': []}, 'pinned-test'))
    spec = importlib.util.spec_from_file_location('agent_gate_builder', ROOT / 'scripts' / 'build-surfaces.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'SSOT_DIR', tmp_path / 'ssot')
    monkeypatch.setattr(module, 'write_json_if_changed', lambda *a: pytest.fail('write before admission'))
    monkeypatch.setattr(module, 'cleanup_slug_outputs', lambda *a: pytest.fail('cleanup before admission'))
    with pytest.raises(SystemExit, match='Agent emission preflight failed'):
        module.main()
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob('*')) == ['ssot', 'ssot/fixture.md']


def test_archive_uses_latest_pinned_catalog_without_self_blessing_manifest(tmp_path, monkeypatch):
    import json
    import shutil
    from intent_pipeline import consumer_shell
    from intent_pipeline.uac_agent_review import preflight_agent_emission
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root: (None, 'unavailable'))
    catalog = tmp_path / '.meta' / 'install-profiles' / 'legacy-installations.json'
    catalog.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / '.meta/install-profiles/legacy-installations.json', catalog)
    (tmp_path / 'ssot').mkdir()
    (tmp_path / 'ssot' / 'engos-meta-supercharge.md').write_text(BOTH)
    assert any('explicit user approval' in error for error in preflight_agent_emission(tmp_path))
    (tmp_path / 'ssot' / 'fixture.md').write_text(BOTH)
    (tmp_path / '.meta' / 'manifest.json').write_text(json.dumps({'ssot_sources': [
        {'slug': 'fixture', 'expected_surface_names': [f'{p}_agent' for p in PROVIDERS]}]}))
    assert any('fixture:' in error for error in preflight_agent_emission(tmp_path))


def test_build_expansion_accepts_only_bound_persisted_review(tmp_path, monkeypatch):
    import json
    from intent_pipeline import consumer_shell
    from intent_pipeline.uac_agent_review import preflight_agent_emission
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root: ({'ssot_sources': []}, 'pinned-test'))
    (tmp_path / 'ssot').mkdir()
    (tmp_path / 'ssot' / 'fixture.md').write_text(BOTH)
    directory = tmp_path / '.meta' / 'capabilities'
    directory.mkdir(parents=True)
    from intent_pipeline.uac_agent_review import _persisted_attestation
    descriptor = {'judge_reports': [{'agent_surface_review': {
        'review_attestations': [_persisted_attestation(review())]}}]}
    (directory / 'fixture.json').write_text(json.dumps(descriptor))
    assert preflight_agent_emission(tmp_path) == []
    (tmp_path / 'ssot' / 'fixture.md').write_text(BOTH + '\nChanged after approval.\n')
    assert preflight_agent_emission(tmp_path)


def test_missing_or_invalid_catalog_blocks_unknown_archive_agents(tmp_path, monkeypatch):
    from intent_pipeline import consumer_shell
    from intent_pipeline.uac_agent_review import preflight_agent_emission
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root: (None, 'unavailable'))
    (tmp_path / 'ssot').mkdir()
    (tmp_path / 'ssot' / 'fixture.md').write_text(BOTH)
    assert 'baseline unavailable' in preflight_agent_emission(tmp_path)[0]


def test_catalog_baseline_does_not_revive_agents_absent_from_latest_release(tmp_path):
    import json
    from intent_pipeline.uac_agent_review import _catalog_agent_baseline
    data = json.loads((ROOT / '.meta/install-profiles/legacy-installations.json').read_text())
    latest = max(data['releases'], key=lambda tag: tuple(map(int, tag[1:].split('.'))))
    data['packages'] = [package for package in data['packages']
                        if not (package['kind'] == 'agent' and latest in package['releases']
                                and package['successor'] == 'engos-meta-supercharge')]
    path = tmp_path / '.meta' / 'install-profiles' / 'legacy-installations.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data))
    baseline, basis = _catalog_agent_baseline(tmp_path)
    assert latest in basis
    assert 'engos-meta-supercharge' not in {entry['slug'] for entry in baseline['ssot_sources']}


def test_validator_imports_gate_without_pythonpath(tmp_path):
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate-surfaces.py'), '--help'],
                            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert 'usage:' in result.stdout


def test_legacy_undeclared_canonical_preserves_released_agents(tmp_path, monkeypatch):
    from intent_pipeline import consumer_shell
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root: (
        {'ssot_sources': [{'slug': 'fixture', 'expected_surface_names': [f'{p}_agent' for p in PROVIDERS]}]},
        'pinned-test'))
    undeclared = SKILL.replace('capability_type: skill\n', '')
    assert check(tmp_path, current=undeclared)['status'] == 'unchanged'
    # Explicit skill declarations and new slugs cannot inherit grandfathering.
    assert check(tmp_path, current=SKILL)['status'] == 'manual_review'
    fresh = tmp_path / 'fresh'
    fresh.mkdir()
    assert check(fresh, current=None)['status'] == 'manual_review'


def test_accepted_retired_private_source_is_not_distributed(tmp_path):
    import json
    from intent_pipeline.uac_agent_review import agent_surface_review
    private = 'SOURCE_ONLY_PRIVATE_SENTINEL_DO_NOT_DISTRIBUTE'
    original = SKILL + '\n' + private + '\n'
    attestation = review(original=original)
    attestation['requirements'][0].update(disposition='retired', authorization=private, rationale=private)
    attestation['requirements'][0]['candidate_excerpt'] = private
    attestation['source_text'] = original
    attestation['reviewer']['debug_source'] = private
    attestation['agent_execution_needs'][0]['debug_source'] = private
    result = agent_surface_review(tmp_path, slug='fixture', candidate_text=BOTH, effective_text=BOTH,
                                  reviews=[attestation], original_texts=[original])
    assert result['status'] == 'reviewed'
    assert private not in json.dumps(result)
    assert 'review_original_texts' not in result
    rebuilt = agent_surface_review(tmp_path, slug='fixture', candidate_text=BOTH, effective_text=BOTH,
                                   reviews=result['review_attestations'], baseline_providers=set(),
                                   require_original_text=False)
    assert rebuilt['status'] == 'reviewed'
    assert rebuilt['source_fidelity'] == 'intake_attestation_not_replayed'


@pytest.fixture
def released_undeclared(tmp_path, monkeypatch):
    import subprocess
    from intent_pipeline import consumer_shell
    current = SKILL.replace('capability_type: skill\n', '')
    directory = tmp_path / 'ssot'
    directory.mkdir()
    (directory / 'fixture.md').write_text(current)
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', 'add', 'ssot/fixture.md'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                    'commit', '-qm', 'Released source'], cwd=tmp_path, check=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tmp_path, text=True).strip()
    surfaces = [f'{p}_{kind}' for p in PROVIDERS for kind in ('agent', 'skill')] + ['grok_skill']
    baseline = {'ssot_sources': [{'slug': 'fixture', 'expected_surface_names': surfaces}]}
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root: (baseline, f'git:release@{revision} .meta/manifest.json'))
    candidate = current.replace('\n---\n', '\ncapability_type: both\n---\n', 1)
    return tmp_path, current, candidate, baseline


def test_exact_declaration_normalization_preserves_existing_contract(released_undeclared):
    from intent_pipeline.uac_agent_review import declaration_normalization
    root, current, candidate, _ = released_undeclared
    result = declaration_normalization(root, slug='fixture', candidate_text=candidate)
    assert result['status'] == 'preserved_existing_contract'
    assert result['quality_evidence'] == 'retained_not_rejudged'
    assert result['behavioral_status'] == 'not_retested'


@pytest.mark.parametrize('mutation', ['whitespace', 'body', 'frontmatter', 'newslug', 'expansion', 'unverified', 'edited_current'])
def test_normalization_rejects_every_non_declaration_change(released_undeclared, monkeypatch, mutation):
    from intent_pipeline.uac_agent_review import declaration_normalization
    from intent_pipeline import consumer_shell
    root, current, candidate, baseline = released_undeclared
    slug = 'fixture'
    if mutation == 'whitespace':
        candidate += '\n'
    elif mutation == 'body':
        candidate = candidate.replace('read-only', 'writable')
    elif mutation == 'frontmatter':
        candidate = candidate.replace('name: fixture', 'name: fixture\ndescription: changed')
    elif mutation == 'newslug':
        slug = 'new-fixture'
        candidate = candidate.replace('name: fixture', 'name: new-fixture')
    elif mutation == 'expansion':
        baseline['ssot_sources'][0]['expected_surface_names'].remove('codex_agent')
    elif mutation == 'unverified':
        monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root: (baseline, 'pinned-catalog'))
    else:
        (root / 'ssot/fixture.md').write_text(current + '\nUnreviewed edit.\n')
        candidate += '\nUnreviewed edit.\n'
    assert declaration_normalization(root, slug=slug, candidate_text=candidate) is None


def test_normalization_plan_judge_and_final_apply_revalidate(released_undeclared, monkeypatch):
    root, current, candidate, _ = released_undeclared
    spec = importlib.util.spec_from_file_location('normalization_uac', ROOT / 'scripts/uac-import.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', root)
    payload = {'status': 'accepted', 'manifest': {'slug': 'fixture'}, 'source_text': candidate}
    normalized = module._run_quality_for_payload(payload, SimpleNamespace(quality_loop='on', requirement_review=[]))
    assert normalized['declaration_normalization']['status'] == 'preserved_existing_contract'
    assert 'quality_result' not in normalized
    assert module._preferred_ssot_text('fixture', normalized) == candidate
    selected, guard = module._safe_apply_ssot_text('fixture', normalized)
    assert selected == candidate
    assert guard['declaration_normalization']['quality_evidence'] == 'retained_not_rejudged'
    (root / 'ssot/fixture.md').write_text(current + '\nChanged after judgment.\n')
    with pytest.raises(ValueError, match='no longer matches'):
        module._safe_apply_ssot_text('fixture', normalized)


def test_independent_review_is_not_user_approval(tmp_path):
    value = review()
    value.pop('user_approval')
    result = check(tmp_path, reviews=[value])
    assert result['status'] == 'manual_review'
    assert all('explicit user approval' in item for item in result['blockers'])


@pytest.mark.parametrize('change', ['wrong_slug', 'reviewer_source', 'missing_reference', 'one_provider', 'not_approved'])
def test_user_approval_is_scoped_and_explicit(tmp_path, change):
    value = review()
    approval = value['user_approval']
    if change == 'wrong_slug': approval['slug'] = 'another-skill'
    elif change == 'reviewer_source': approval['source'] = 'reviewer'
    elif change == 'missing_reference': approval['reference'] = ''
    elif change == 'one_provider': approval['providers'] = ['codex']
    else: approval['decision'] = 'recommended'
    result = check(tmp_path, reviews=[value])
    assert result['status'] == 'manual_review'
    assert any('explicit user approval' in item for item in result['blockers'])


def test_existing_agent_improvement_does_not_require_new_creation_approval(tmp_path):
    result = check(tmp_path, current=BOTH, candidate=BOTH+'\nClarify the existing review output.\n')
    assert result['status'] == 'unchanged'
    assert not result['added_providers']


def test_retired_git_baseline_cannot_authorize_reintroduction(tmp_path, monkeypatch):
    from intent_pipeline import consumer_shell
    from intent_pipeline.uac_agent_review import preflight_agent_emission
    slug = 'engos-meta-supercharge'
    candidate = BOTH.replace('name: fixture', 'name: '+slug)
    (tmp_path/'ssot').mkdir()
    (tmp_path/'ssot'/f'{slug}.md').write_text(candidate)
    baseline = {'ssot_sources':[{'slug':slug,'expected_surface_names':[f'{p}_agent' for p in PROVIDERS]}]}
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline', lambda root:(baseline,'test-pinned-release'))
    errors = preflight_agent_emission(tmp_path)
    assert sum('explicit user approval required' in error for error in errors)==4


def test_retired_agent_can_be_reintroduced_with_actual_scoped_approval_record(tmp_path, monkeypatch):
    import json
    from intent_pipeline import consumer_shell
    from intent_pipeline.uac_agent_review import preflight_agent_emission, _persisted_attestation
    slug = 'engos-meta-supercharge'
    original = SKILL.replace('name: fixture','name: '+slug)
    candidate = BOTH.replace('name: fixture','name: '+slug)
    (tmp_path/'ssot').mkdir(); (tmp_path/'ssot'/f'{slug}.md').write_text(candidate)
    approved = review(original,candidate)
    approved['slug']=slug; approved['user_approval']['slug']=slug
    directory=tmp_path/'.meta'/'capabilities'; directory.mkdir(parents=True)
    (directory/f'{slug}.json').write_text(json.dumps({'judge_reports':[{'agent_surface_review':{'review_attestations':[_persisted_attestation(approved)]}}]}))
    monkeypatch.setattr(consumer_shell,'resolve_release_baseline',lambda root:({'ssot_sources':[]},'test-pinned-release'))
    assert preflight_agent_emission(tmp_path)==[]
