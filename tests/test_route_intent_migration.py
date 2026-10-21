"""Receipt-backed pre-release rename on disposable installation targets."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import install_bundle
from core_install import catalog, planner, transaction

OLD = 'engos-orchestration-route-intent'
NEW = 'engos-route-intent'


def put(root, rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o644)
    return path


def source(root, slug, clients):
    surfaces = sorted(set(clients) | ({'codex'} if 'gemini' in clients else set()))
    resources = {}
    for provider in surfaces:
        prefix = f'.{provider}/skills/{slug}'
        put(root, prefix + '/SKILL.md', f'---\nname: {slug}\n---\nRoute intent.\n')
        rel = prefix + '/resources/reference.md'
        put(root, rel, 'Complete resource.\n')
        resources[provider + '_skill'] = [rel]
    put(root, '.meta/manifest.json', json.dumps({'ssot_sources': [
        {'slug': slug, 'expected_surface_names': [p + '_skill' for p in surfaces]}],
        'resources': resources}))
    put(root, '.meta/install-profiles/legacy-installations.json', json.dumps({
        'schema': 1, 'releases': {}, 'identities': {}, 'packages': [],
        'runtime': {}, 'launchers': {}}))
    for rel in ('VERSION', 'scripts/deploy-profile.py', 'scripts/update-core-prompts.py'):
        put(root, rel, 'fixture\n')
    install_bundle.build(root)


def apply(repo, target, request):
    proposal = planner.plan(repo, target, request)
    return transaction.apply(repo, target, proposal, lambda: planner.plan(repo, target, request))


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in root.rglob('*') if p.is_file()}


def prepared(tmp_path, schema=3, clients=('kiro',)):
    repo, target = tmp_path / 'source', tmp_path / 'target'
    repo.mkdir(); target.mkdir()
    source(repo, OLD, clients)
    request = {'mode': 'install', 'providers': list(clients), 'kinds': ['skill'], 'slugs': [OLD]}
    if schema == 3:
        request = {'mode': 'install', 'profile': {'schema': 1, 'scope': 'skills',
            'targets': list(clients), 'slugs': [OLD]}, 'selection_policy': 'curated'}
    # Initial ownership comes from the pre-rename installer, without its future mapping.
    with patch.dict(catalog.SUCCESSORS, {OLD: OLD}):
        apply(repo, target, request)
    source(repo, NEW, clients)
    return repo, target


@pytest.mark.parametrize('schema', [2, 3])
def test_owned_rename_preview_apply_and_exact_rollback(tmp_path, schema):
    repo, target = prepared(tmp_path, schema)
    before = snapshot(target)
    request = {'mode': 'sync', 'providers': ['kiro'], 'runtime': False}
    proposal = planner.plan(repo, target, request)
    assert snapshot(target) == before
    assert not proposal['preserved'] and not proposal['blockers']
    assert proposal['selection'] == [f'kiro:skill:{NEW}']
    result = apply(repo, target, request)
    assert not (target / f'.kiro/skills/{OLD}/SKILL.md').exists()
    assert (target / f'.kiro/skills/{NEW}/resources/reference.md').read_text() == 'Complete resource.\n'
    state = planner.read_state(target)
    assert state['schema'] == schema
    assert set(state['packages']) == {f'kiro:skill:{NEW}'}
    assert not planner.plan(repo, target, request)['actions']
    transaction.rollback(target, result['transaction'])
    after = snapshot(target)
    assert all(after.get(path) == data for path, data in before.items())
    assert not any(path.startswith(f'.kiro/skills/{NEW}/') for path in after)


@pytest.mark.parametrize('change', ['entry', 'extra'])
def test_changed_owned_old_package_is_preserved(tmp_path, change):
    repo, target = prepared(tmp_path)
    rel = f'.kiro/skills/{OLD}/' + ('SKILL.md' if change == 'entry' else 'resources/custom.md')
    put(target, rel, 'Keep my customization.\n')
    before = snapshot(target)
    request = {'mode': 'sync', 'providers': ['kiro'], 'runtime': False}
    proposal = planner.plan(repo, target, request)
    assert proposal['preserved']
    assert not any(a['path'].startswith(f'.kiro/skills/{OLD}/') for a in proposal['actions'])
    apply(repo, target, request)
    after = snapshot(target)
    assert all(after[path] == data for path, data in before.items() if path.startswith(f'.kiro/skills/{OLD}/'))
    assert f'kiro:skill:{OLD}' in planner.read_state(target)['packages']


def test_conflicting_new_package_preserves_old_and_new(tmp_path):
    repo, target = prepared(tmp_path)
    put(target, f'.kiro/skills/{NEW}/SKILL.md', 'My independent skill.\n')
    before = snapshot(target)
    request = {'mode': 'sync', 'providers': ['kiro'], 'runtime': False}
    proposal = planner.plan(repo, target, request)
    assert proposal['preserved']
    assert not any(a['path'].startswith('.kiro/skills/') for a in proposal['actions'])
    apply(repo, target, request)
    after = snapshot(target)
    assert all(after[path] == data for path, data in before.items() if path.startswith('.kiro/skills/'))
    assert f'kiro:skill:{OLD}' in planner.read_state(target)['selection']


def test_unowned_old_is_not_adopted_or_deleted(tmp_path):
    repo, target = tmp_path / 'source', tmp_path / 'target'
    repo.mkdir(); target.mkdir()
    source(repo, NEW, ('kiro',))
    old = put(target, f'.kiro/skills/{OLD}/SKILL.md', 'Unowned old skill.\n')
    apply(repo, target, {'mode': 'install', 'providers': ['kiro'], 'slugs': [NEW], 'runtime': False})
    assert old.read_text() == 'Unowned old skill.\n'
    assert set(planner.read_state(target)['packages']) == {f'kiro:skill:{NEW}'}


def test_missing_selected_old_retains_ownership_and_reports_repair(tmp_path):
    repo, target = prepared(tmp_path)
    for p in (target / f'.kiro/skills/{OLD}').rglob('*'):
        if p.is_file():
            p.unlink()
    request = {'mode': 'sync', 'providers': ['kiro'], 'runtime': False}
    proposal = planner.plan(repo, target, request)
    assert any('missing' in p['reason'] and 'repair' in p['reason'] for p in proposal['preserved'])
    assert proposal['selection'] == [f'kiro:skill:{OLD}']
    assert not any(a['path'].startswith('.kiro/skills/') for a in proposal['actions'])


def test_unrelated_removed_scope_still_fails(tmp_path):
    repo, target = prepared(tmp_path)
    state = planner.read_state(target)
    state['selection'].append('kiro:skill:unmapped-removed-skill')
    put(target, planner.STATE, json.dumps(state))
    with pytest.raises(ValueError, match='SOURCE_SCOPE_REMOVED.*unmapped-removed-skill'):
        planner.plan(repo, target, {'mode': 'sync', 'runtime': False})


@pytest.mark.parametrize('policy', ['curated', 'full_catalog'])
def test_shared_reader_joint_migration_and_scoped_hold(tmp_path, policy):
    repo, target = prepared(tmp_path, clients=('codex', 'gemini'))
    if policy == 'full_catalog':
        state = planner.read_state(target)
        state['selection_policy'] = {p: policy for p in ('codex', 'gemini')}
        put(target, planner.STATE, json.dumps(state))
    before = snapshot(target)
    scoped = planner.plan(repo, target, {'mode': 'sync', 'providers': ['codex'], 'runtime': False})
    assert any('SHARED_SURFACE_POLICY_CONFLICT' in b for b in scoped['blockers'])
    assert snapshot(target) == before
    with pytest.raises(transaction.InstallError, match='unresolved blockers'):
        apply(repo, target, {'mode': 'sync', 'providers': ['codex'], 'runtime': False})
    assert snapshot(target) == before
    request = {'mode': 'sync', 'providers': ['codex', 'gemini'], 'runtime': False}
    proposal = planner.plan(repo, target, request)
    assert not proposal['blockers']
    result = apply(repo, target, request)
    state = planner.read_state(target)
    assert set(state['selection']) == {f'{p}:skill:{NEW}' for p in ('codex', 'gemini')}
    assert set(state['packages']) == set(state['selection'])
    assert not (target / f'.agents/skills/{OLD}/SKILL.md').exists()
    transaction.rollback(target, result['transaction'])
    assert (target / planner.STATE).read_bytes() == before[planner.STATE][0]


def test_out_of_scope_provider_retains_old_selection(tmp_path):
    repo, target = prepared(tmp_path)
    before = snapshot(target)
    proposal = planner.plan(repo, target, {'mode': 'sync', 'providers': ['claude'], 'runtime': False})
    assert proposal['selection'] == [f'kiro:skill:{OLD}']
    assert not proposal['actions']
    assert snapshot(target) == before
