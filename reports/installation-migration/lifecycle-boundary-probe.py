"""Characterize the installer boundary recorded in LIFECYCLE-FOLLOWUP.md.

Run explicitly with pytest. These tests include expected refusals for missing
future lifecycle support; passing is not proof of rename/merge implementation.
All installation mutations use pytest temporary directories, never a live home.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tests'))
import test_installation as fixture_support
from core_install import catalog, planner, providers, transaction
import install_bundle

installation = fixture_support.installation
put = fixture_support.put
execute = fixture_support.execute
ORIGINAL = 'engos-design-architecture'
NEW = 'engos-future-example'


def add_skill(repo, provider, slug, body):
    manifest = json.loads((repo / '.meta/manifest.json').read_text())
    entry = next((e for e in manifest['ssot_sources'] if e['slug'] == slug), None)
    if entry is None:
        entry = {'slug': slug, 'expected_surface_names': []}
        manifest['ssot_sources'].append(entry)
    surface = f'{provider}_skill'
    if surface not in entry['expected_surface_names']:
        entry['expected_surface_names'].append(surface)
    manifest['resources'].setdefault(surface, [])
    put(repo, '.meta/manifest.json', json.dumps(manifest))
    put(repo, f'.{provider}/skills/{slug}/SKILL.md', body)


def active_path(provider, slug):
    return f'{providers.SKILL_ROOTS[provider]}/{slug}/SKILL.md'


def install_initial(repo, target, provider, slugs=(ORIGINAL,)):
    for slug in slugs:
        add_skill(repo, provider, slug, 'version one\n')
    install_bundle.build(repo)
    execute(repo, target, mode='install', providers=[provider],
            kinds=['skill'], slugs=list(slugs))


@pytest.mark.parametrize('provider', providers.PROVIDERS)
def test_content_hash_changes_are_expected_and_scoped(installation, provider):
    repo, target = installation
    install_initial(repo, target, provider)
    rel = active_path(provider, ORIGINAL)
    before = transaction.identity(target / rel)
    add_skill(repo, provider, ORIGINAL, 'version two\n')
    with pytest.raises(ValueError, match='standalone bundle identity mismatch'):
        planner.plan(repo, target, {'mode': 'sync'})
    install_bundle.build(repo)
    plan = planner.plan(repo, target, {'mode': 'sync'})
    assert not plan['blockers'] and not plan['preserved']
    action = next(a for a in plan['actions'] if a['path'] == rel)
    assert action['before'] == before and action['after'] != before
    active_actions = [a['path'] for a in plan['actions']
                      if not a['path'].startswith(('.core-prompts-updater/', '.core-prompts-state/'))]
    assert active_actions == [rel]
    execute(repo, target, mode='sync')
    saved = planner.read_state(target)
    assert saved['packages'][providers.key(provider, 'skill', ORIGINAL)]['files'][rel] == action['after']
    assert (target / rel).read_text() == 'version two\n'
    assert not planner.plan(repo, target, {'mode': 'sync'})['actions']


@pytest.mark.parametrize('provider', providers.PROVIDERS)
def test_new_skill_is_available_but_requires_explicit_selection(installation, provider):
    repo, target = installation
    install_initial(repo, target, provider)
    add_skill(repo, provider, NEW, 'new capability\n')
    install_bundle.build(repo)
    execute(repo, target, mode='sync')
    assert not (target / active_path(provider, NEW)).exists()
    assert (target / f'.core-prompts-updater/.{provider}/skills/{NEW}/SKILL.md').exists()
    assert planner.read_state(target)['selection'] == [providers.key(provider, 'skill', ORIGINAL)]
    execute(repo, target, mode='install', providers=[provider], kinds=['skill'], slugs=[NEW])
    assert (target / active_path(provider, NEW)).read_text() == 'new capability\n'
    assert len(planner.read_state(target)['selection']) == 2
    assert not planner.plan(repo, target, {'mode': 'sync'})['actions']


@pytest.mark.parametrize('provider', providers.PROVIDERS)
def test_custom_package_does_not_stop_unrelated_package_update(installation, provider):
    repo, target = installation
    install_initial(repo, target, provider, (ORIGINAL, NEW))
    put(target, active_path(provider, ORIGINAL), 'my customization\n')
    add_skill(repo, provider, ORIGINAL, 'upstream revision\n')
    add_skill(repo, provider, NEW, 'upstream revision\n')
    install_bundle.build(repo)
    plan = planner.plan(repo, target, {'mode': 'sync'})
    assert not plan['blockers'] and plan['preserved']
    assert not any(a['path'] == active_path(provider, ORIGINAL) for a in plan['actions'])
    assert any(a['path'] == active_path(provider, NEW) for a in plan['actions'])
    execute(repo, target, mode='sync')
    assert (target / active_path(provider, ORIGINAL)).read_text() == 'my customization\n'
    assert (target / active_path(provider, NEW)).read_text() == 'upstream revision\n'


@pytest.mark.parametrize('provider', providers.PROVIDERS)
@pytest.mark.parametrize('change', ['rename', 'merge', 'retire'])
def test_future_identity_transitions_currently_fail_closed(installation, provider, change, monkeypatch):
    repo, target = installation
    selected = (ORIGINAL, NEW) if change == 'merge' else (ORIGINAL,)
    install_initial(repo, target, provider, selected)
    saved_before = (target / planner.STATE).read_bytes()
    manifest = json.loads((repo / '.meta/manifest.json').read_text())
    manifest['ssot_sources'] = [e for e in manifest['ssot_sources'] if e['slug'] not in selected]
    put(repo, '.meta/manifest.json', json.dumps(manifest))
    successor = 'engos-next-identity'
    if change != 'retire':
        add_skill(repo, provider, successor, 'renamed or merged capability\n')
    # Even a declared alias cannot reach migration processing: missing-selection
    # rejection runs first. These patches affect only this disposable test process.
    for slug in selected:
        monkeypatch.setitem(catalog.SUCCESSORS, slug, successor if change != 'retire' else None)
    install_bundle.build(repo)
    with pytest.raises(ValueError, match='SOURCE_SCOPE_REMOVED'):
        planner.plan(repo, target, {'mode': 'sync'})
    assert (target / planner.STATE).read_bytes() == saved_before
    assert all((target / active_path(provider, s)).exists() for s in selected)


@pytest.mark.parametrize('provider', providers.PROVIDERS)
def test_package_resource_additions_and_removals_update_inventory(installation, provider):
    repo, target = installation
    install_initial(repo, target, provider)
    resource = f'.{provider}/skills/{ORIGINAL}/resources/example.txt'
    target_resource = str(Path(active_path(provider, ORIGINAL)).parent / 'resources/example.txt')
    manifest = json.loads((repo / '.meta/manifest.json').read_text())
    manifest['resources'][f'{provider}_skill'].append(resource)
    put(repo, resource, 'new resource\n')
    put(repo, '.meta/manifest.json', json.dumps(manifest))
    install_bundle.build(repo)
    execute(repo, target, mode='sync')
    assert (target / target_resource).read_text() == 'new resource\n'
    manifest['resources'][f'{provider}_skill'].remove(resource)
    put(repo, '.meta/manifest.json', json.dumps(manifest))
    (repo / resource).unlink()
    install_bundle.build(repo)
    plan = planner.plan(repo, target, {'mode': 'sync'})
    assert any(a['path'] == target_resource and a['op'] == 'remove' for a in plan['actions'])
    execute(repo, target, mode='sync')
    assert not (target / target_resource).exists()
    assert not planner.plan(repo, target, {'mode': 'sync'})['actions']


def test_shared_runtime_integrity_can_block_an_unrelated_active_update(installation):
    repo, target = installation
    install_initial(repo, target, 'kiro')
    unrelated = f'.core-prompts-updater/.gemini/skills/{ORIGINAL}/SKILL.md'
    put(target, unrelated, 'custom runtime copy\n')
    add_skill(repo, 'kiro', ORIGINAL, 'version two\n')
    install_bundle.build(repo)
    plan = planner.plan(repo, target, {'mode': 'sync'})
    assert any('RUNTIME_CONFLICT' in b and unrelated in b for b in plan['blockers'])
    assert (target / active_path('kiro', ORIGINAL)).read_text() == 'version one\n'
