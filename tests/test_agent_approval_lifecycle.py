"""Creation approval survives independently reviewed improvements, not scope drift."""
import copy
import json

import pytest

from intent_pipeline import consumer_shell
from intent_pipeline.uac_agent_review import agent_surface_review, preflight_agent_emission, _persisted_attestation
from test_agent_execution_need import BOTH, SKILL, PROVIDERS, review


def descriptor(root, attestation):
    path = root / '.meta/capabilities/fixture.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'judge_reports': [{'agent_surface_review': {
        'review_attestations': [attestation]}}]}))


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    (tmp_path / 'ssot').mkdir()
    (tmp_path / 'ssot/fixture.md').write_text(BOTH)
    descriptor(tmp_path, _persisted_attestation(review()))
    monkeypatch.setattr(consumer_shell, 'resolve_release_baseline',
                        lambda root: ({'ssot_sources': []}, 'skills-only-release'))
    return tmp_path


def improve(root, fresh=None, candidate=None):
    candidate = candidate or BOTH + '\nClarify the existing output.\n'
    return agent_surface_review(root, slug='fixture', candidate_text=candidate,
        effective_text=candidate, reviews=[] if fresh is None else [fresh], original_texts=[SKILL])


def test_improvement_reuses_approval_and_builds_before_next_release(admitted):
    candidate = BOTH + '\nClarify the existing output.\n'
    fresh = review(original=BOTH, candidate=candidate)
    fresh.pop('user_approval')
    result = improve(admitted, fresh, candidate)
    assert not result['blockers']
    carried = result['review_attestations'][0]
    assert carried['user_approval']['reference'] == review()['user_approval']['reference']
    (admitted / 'ssot/fixture.md').write_text(candidate)
    descriptor(admitted, carried)
    assert preflight_agent_emission(admitted) == []
    # A second improvement also reuses the scoped approval, with fresh review.
    newer = candidate + '\nClarify again.\n'
    second = review(original=candidate, candidate=newer)
    second.pop('user_approval')
    assert not improve(admitted, second, newer)['blockers']


def test_missing_fresh_review_requests_review_not_new_user_approval(admitted):
    result = improve(admitted)
    assert result['status'] == 'manual_review'
    assert any('fresh execution review' in b for b in result['blockers'])
    assert not any('explicit user approval' in b for b in result['blockers'])


def test_different_original_cannot_carry_existing_approval(admitted):
    fresh = review(candidate=BOTH + '\nClarify the existing output.\n')
    fresh.pop('user_approval')
    assert any('existing canonical source' in b for b in improve(admitted, fresh)['blockers'])


@pytest.mark.parametrize('change', ['candidate', 'effective', 'slug', 'reviewer', 'source', 'need'])
def test_stale_or_invalid_prior_admission_cannot_supply_user_approval(admitted, change):
    prior = _persisted_attestation(review())
    if change in ('candidate', 'effective'):
        prior[change + '_sha256'] = '0' * 64
    elif change == 'slug': prior['slug'] = 'other'
    elif change == 'reviewer': prior['reviewer']['independent'] = False
    elif change == 'source': prior['user_approval']['source'] = 'reviewer'
    else: prior['agent_execution_needs'] = []
    descriptor(admitted, prior)
    candidate = BOTH + '\nClarify the existing output.\n'
    fresh = review(original=BOTH, candidate=candidate)
    fresh.pop('user_approval')
    result = improve(admitted, fresh, candidate)
    assert not result['review_attestations']


def test_reduced_current_scope_cannot_restore_other_providers(admitted, monkeypatch):
    # Model a future per-provider declaration without introducing that API here.
    import intent_pipeline.uac_agent_review as gate
    original = gate.agent_providers
    current = BOTH + '\nCodex-only identity.\n'
    candidate = BOTH + '\nExpanded identity.\n'
    (admitted / 'ssot/fixture.md').write_text(current)
    old = review(candidate=current)
    descriptor(admitted, _persisted_attestation(old))
    monkeypatch.setattr(gate, 'agent_providers',
                        lambda text: {'codex'} if text == current else original(text))
    fresh = review(original=current, candidate=candidate)
    fresh.pop('user_approval')
    result = improve(admitted, fresh, candidate)
    assert set(result['added_providers']) == set(PROVIDERS) - {'codex'}
    assert sum('explicit user approval' in b for b in result['blockers']) == 3


def test_retired_skill_cannot_reuse_stale_agent_approval(admitted):
    (admitted / 'ssot/fixture.md').write_text(SKILL)
    fresh = copy.deepcopy(review())
    fresh.pop('user_approval')
    result = improve(admitted, fresh, BOTH)
    assert sum('explicit user approval' in b for b in result['blockers']) == 4


def test_current_bound_admission_can_follow_historical_review(admitted):
    candidate = BOTH + '\nClarify the existing output.\n'
    fresh = review(original=BOTH, candidate=candidate)
    fresh.pop('user_approval')
    result = improve(admitted, fresh, candidate)
    path = admitted / '.meta/capabilities/fixture.json'
    value = json.loads(path.read_text())
    value['judge_reports'].append({'agent_surface_review': result})
    path.write_text(json.dumps(value))
    (admitted / 'ssot/fixture.md').write_text(candidate)
    assert preflight_agent_emission(admitted) == []


@pytest.mark.parametrize("retirement", [False, True])
def test_quality_loop_off_apply_persists_current_admission(admitted, monkeypatch, retirement):
    import importlib.util
    from pathlib import Path
    from types import SimpleNamespace
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('lifecycle_apply', root / 'scripts/uac-import.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    candidate = SKILL if retirement else BOTH + '\nClarify the existing output.\n'
    fresh = review(original=BOTH, candidate=candidate)
    fresh.pop('user_approval')
    monkeypatch.setattr(module, 'ROOT', admitted)
    monkeypatch.setattr(module, '_snapshot_apply_artifacts', lambda: {})
    monkeypatch.setattr(module, '_preferred_ssot_text', lambda *a, **kw: candidate)
    monkeypatch.setattr(module, '_safe_apply_ssot_text', lambda *a, **kw: (candidate, {}))
    monkeypatch.setattr(module, 'build_descriptor', lambda **kw: {})
    monkeypatch.setattr(module, '_descriptor_shared_constraints', lambda *a: ())
    monkeypatch.setattr(module, '_compile_applied_skill', lambda *a, **kw: {'status': 'structural_ready'})
    def native_check(*args, **kwargs):
        # Real admission validator executes after the actual source/descriptor
        # writes. Native build/compile are outside this focused lifecycle test.
        errors = preflight_agent_emission(admitted)
        return SimpleNamespace(returncode=bool(errors), stdout='', stderr='; '.join(errors))
    monkeypatch.setattr(module.subprocess, 'run', native_check)
    payload = {'status': 'accepted', 'manifest': {'slug': 'fixture', 'layers': {'minimal': {}}},
               'source': {'normalized_source': 'local-fixture'}, 'source_text': candidate,
               'requirement_reviews': [fresh]}
    args = SimpleNamespace(yes=True, quality_loop='off', requirement_review=[])
    result = module._apply_payload(payload, args, [])
    assert result['status'] == 'applied', result
    saved = json.loads((admitted / '.meta/capabilities/fixture.json').read_text())
    admissions = [r['agent_surface_review'] for r in saved['judge_reports'] if 'agent_surface_review' in r]
    assert sum(len(a.get('review_attestations', [])) for a in admissions) == (0 if retirement else 1)
    assert preflight_agent_emission(admitted) == []

    if retirement:
        (admitted / 'ssot/fixture.md').write_text(BOTH)
        assert any('explicit user approval required' in error for error in preflight_agent_emission(admitted))


def test_identical_existing_agent_retains_current_admission(admitted):
    result = improve(admitted, candidate=BOTH)
    assert not result['blockers']
    assert len(result['review_attestations']) == 1
    descriptor(admitted, result['review_attestations'][0])
    assert preflight_agent_emission(admitted) == []


def test_skill_only_build_revokes_prior_agent_admission(admitted, monkeypatch):
    import importlib.util
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('retired_grant_builder',root/'scripts/build-surfaces.py')
    builder = importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    monkeypatch.setattr(builder,'ROOT',admitted)
    monkeypatch.setattr(builder,'CAPABILITY_RESOURCE_SOURCE_DIR',admitted/'sources/capability-resources')
    (admitted/'ssot/fixture.md').write_text(SKILL)
    entry=builder.load_ssot_entries(admitted/'ssot')[0]
    manifest=builder.build_ssot_manifest_entry(entry,admitted)
    resolved=builder.resolve_descriptor(entry,manifest,{})
    assert not any(r.get('agent_surface_review',{}).get('review_attestations') for r in resolved['judge_reports'])
    (admitted/'ssot/fixture.md').write_text(BOTH)
    assert any('explicit user approval required' in error for error in preflight_agent_emission(admitted))
