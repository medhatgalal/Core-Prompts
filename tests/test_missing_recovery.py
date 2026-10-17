"""Exact missing-package recovery and opaque shared-root discovery controls."""
import copy
import json
import os
from pathlib import Path

import pytest

from test_installation import installation, put
from core_install import planner, transaction as tx
import install_bundle


@pytest.fixture
def recovery(installation):
    repo, target = installation
    manifest = json.loads((repo / '.meta/manifest.json').read_text())
    for slug in ('engos-design-architecture', 'engos-quality-code-review'):
        entry = next((e for e in manifest['ssot_sources'] if e['slug'] == slug), None)
        if entry is None:
            entry = {'slug': slug, 'expected_surface_names': []}
            manifest['ssot_sources'].append(entry)
        entry['expected_surface_names'].append('grok_skill')
        root = f'.grok/skills/{slug}'
        put(repo, root + '/SKILL.md', 'current ' + slug)
        put(repo, root + '/resources/helper.py', 'resource')
        manifest['resources'].setdefault('grok_skill', []).append(root + '/resources/helper.py')
    put(repo, '.meta/manifest.json', json.dumps(manifest))
    install_bundle.build(repo)
    packages = planner.providers.current_packages(repo, manifest, tx.identity, tx.safe)
    owned = {k: {f: p[f] for f in ('provider', 'kind', 'slug', 'roots', 'files')}
             for k, p in packages.items() if p['provider'] == 'grok'}
    state = dict(schema=3, owner='Core-Prompts', selection=sorted(owned), packages=owned,
                 runtime={}, registrations={}, selection_policy={'grok': 'full_catalog'},
                 source_version='previous', preserved=[])
    put(target, planner.STATE, json.dumps(state))
    (target / '.grok/skills').mkdir(parents=True)
    request = dict(mode='recover_missing', providers=['grok'], kinds=['skill'],
                   slugs=['engos-design-architecture', 'engos-quality-code-review'], runtime=False)
    return repo, target, request


def test_unrelated_shared_links_do_not_block_and_are_visible(installation):
    repo, target = installation
    root = target / '.agents/skills'
    root.mkdir(parents=True)
    (root / 'addy').symlink_to('/missing/third-party')
    result = planner.plan(repo, target, {'mode': 'install', 'providers': ['codex', 'gemini'], 'runtime': False})
    assert not result['blockers']
    assert 'addy' in result['shared_exposure']['before_slugs']
    assert result['shared_exposure']['supported_readers'] == ['codex', 'gemini']
    tx.apply(repo, target, result, lambda: planner.plan(repo, target, result['request']))
    assert os.readlink(root / 'addy') == '/missing/third-party'


def test_recover_exact_missing_packages_and_restore_absence(recovery):
    repo, target, request = recovery
    before = (target / planner.STATE).read_bytes()
    plan = planner.plan(repo, target, request)
    assert not plan['blockers']
    assert plan['selection'] == json.loads(before)['selection']
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    for slug in request['slugs']:
        assert (target / f'.grok/skills/{slug}/resources/helper.py').read_text() == 'resource'
    tx.rollback(target, result['transaction'])
    assert (target / planner.STATE).read_bytes() == before
    assert all(not (target / f'.grok/skills/{s}').exists() for s in request['slugs'])
    assert (target / '.grok/skills').is_dir()


@pytest.mark.parametrize('kind', ['empty', 'partial', 'file', 'link', 'broken_link'])
def test_recovery_rejects_every_existing_root(recovery, kind):
    repo, target, request = recovery
    root = target / ('.grok/skills/' + request['slugs'][0])
    if kind == 'empty':
        root.mkdir()
    elif kind == 'partial':
        put(target, str(root.relative_to(target)) + '/custom', 'keep')
    elif kind == 'file':
        root.write_text('keep')
    else:
        root.symlink_to(target / ('missing' if kind == 'broken_link' else '.grok/skills'))
    before = (target / planner.STATE).read_bytes()
    with pytest.raises(ValueError):
        planner.plan(repo, target, request)
    assert (target / planner.STATE).read_bytes() == before
    assert not (target / ('.grok/skills/' + request['slugs'][1])).exists()


@pytest.mark.parametrize('change', ['no_state', 'not_selected', 'unowned', 'wrong_roots', 'bad_member', 'schema1'])
def test_recovery_requires_prior_selection_and_exact_ownership(recovery, change):
    repo, target, request = recovery
    path = target / planner.STATE
    state = json.loads(path.read_text())
    key = state['selection'][0]
    if change == 'no_state':
        path.unlink()
    else:
        if change == 'not_selected': state['selection'].remove(key)
        if change == 'unowned': del state['packages'][key]
        if change == 'wrong_roots': state['packages'][key]['roots'] = ['.grok/skills/other']
        if change == 'bad_member': state['packages'][key]['files'] = {'outside': next(iter(state['packages'][key]['files'].values()))}
        if change == 'schema1': state['schema'] = 1
        path.write_text(json.dumps(state))
    with pytest.raises(ValueError):
        planner.plan(repo, target, request)
    assert not (target / '.core-prompts-state/install-transactions').exists()


@pytest.mark.parametrize('patch', [dict(providers=['codex']), dict(kinds=['agent']), dict(runtime=True),
    dict(slugs=[]), dict(slugs=['architecture']), dict(slugs=['unknown']),
    dict(slugs=['engos-design-architecture'] * 2), dict(selection_policy='full_catalog'),
    dict(profile={}), dict(release_state={}), dict(legacy_slugs=['architecture'])])
def test_recovery_direct_request_rejects_expansion(recovery, patch):
    repo, target, request = recovery
    with pytest.raises(ValueError):
        planner.plan(repo, target, {**request, **patch})


def test_recovery_preserves_other_packages_policies_and_runtime(recovery):
    repo, target, request = recovery
    state_path = target / planner.STATE
    before = json.loads(state_path.read_text())
    before['runtime'] = {'runtime-sentinel': {'sha256': 'a' * 64, 'mode': 0o644}}
    before['registrations'] = {'custom': 'keep'}
    state_path.write_text(json.dumps(before))
    custom = put(target, '.grok/skills/crucible/SKILL.md', 'custom')
    request['slugs'] = request['slugs'][:1]
    plan = planner.plan(repo, target, request)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    after = json.loads(state_path.read_text())
    for field in ('selection', 'selection_policy', 'runtime', 'registrations', 'source_version'):
        assert after[field] == before[field]
    assert custom.read_text() == 'custom'
    assert not (target / '.grok/skills/engos-quality-code-review').exists()


@pytest.mark.parametrize('mode', ['repair', 'sync'])
def test_routine_modes_do_not_recover_absent_owned_roots(recovery, mode):
    repo, target, request = recovery
    plan = planner.plan(repo, target, {'mode': mode, 'providers': ['grok'], 'runtime': False})
    assert not any(a['path'].startswith('.grok/skills/') for a in plan['actions'])
    assert {p['package'] for p in plan['preserved']} >= set(json.loads((target / planner.STATE).read_text())['selection'])


@pytest.mark.parametrize('change', ['add', 'remove', 'retarget', 'replace_same_target'])
def test_shared_membership_and_link_identity_stale_the_plan(installation, change):
    repo, target = installation
    root = target / '.agents/skills'
    root.mkdir(parents=True)
    link = root / 'addy'
    link.symlink_to('/unrelated')
    request = dict(mode='install', providers=['codex', 'gemini'], runtime=False)
    approved = planner.plan(repo, target, request)
    if change == 'add':
        (root / 'personal').mkdir()
    elif change == 'remove':
        link.unlink()
    else:
        # Retain original inode to ensure replacement cannot reuse it.
        link.rename(root / 'old-link')
        link.symlink_to('/changed' if change == 'retarget' else '/unrelated')
        (root / 'old-link').unlink()
    with pytest.raises(tx.InstallError, match='stale approved plan'):
        tx.apply(repo, target, approved, lambda: planner.plan(repo, target, request))


def test_shared_error_is_unknown_and_selected_link_remains_protected(installation):
    repo, target = installation
    root = target / '.agents/skills'
    root.parent.mkdir()
    root.symlink_to('/absent')
    result = planner.plan(repo, target, {'mode': 'install', 'providers': ['grok'], 'runtime': False})
    assert result['blockers']
    assert result['shared_exposure']['before_slugs'] is None
    assert result['shared_exposure']['after_slugs'] is None
    root.unlink()
    root.mkdir()
    (root / 'engos-design-architecture').symlink_to('/absent')
    result = planner.plan(repo, target, {'mode': 'install', 'providers': ['codex'], 'runtime': False})
    assert any('symlink' in p['reason'] for p in result['preserved'])
    assert not any(a['path'].startswith('.agents/skills/') for a in result['actions'])


@pytest.mark.parametrize('kind', ['directory', 'file', 'link'])
def test_root_appearing_after_replan_is_preserved(recovery, monkeypatch, kind):
    from core_install import recovery as rec
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    root = target / plan['recovery_roots'][0]
    original = rec.claim
    def claim(*args):
        if kind == 'directory': root.mkdir()
        elif kind == 'file': root.write_text('external')
        else: root.symlink_to('/external')
        return original(*args)
    monkeypatch.setattr(rec, 'claim', claim)
    with pytest.raises(tx.InstallError, match='installation failed'):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert root.is_symlink() if kind == 'link' else root.exists()
    assert not (target / plan['recovery_roots'][1]).exists()


def test_new_file_after_preflight_is_not_overwritten(recovery, monkeypatch):
    from core_install import recovery as rec
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    original = rec.os.link
    introduced = []
    def link(source, destination, **kwargs):
        Path(destination).write_text('external writer')
        introduced.append(Path(destination))
        return original(source, destination, **kwargs)
    monkeypatch.setattr(rec.os, 'link', link)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert introduced[0].read_text() == 'external writer'
    with pytest.raises(tx.InstallError):
        tx.rollback(target, error.value.transaction)
    assert introduced[0].read_text() == 'external writer'


def test_interrupted_recovery_rolls_back_recorded_nodes(recovery, monkeypatch):
    from core_install import recovery as rec
    repo, target, request = recovery
    before = (target / planner.STATE).read_bytes()
    plan = planner.plan(repo, target, request)
    original = rec.publish
    def interrupted(*args):
        original(*args)
        raise OSError('injected after durable publish')
    monkeypatch.setattr(rec, 'publish', interrupted)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    tx.rollback(target, error.value.transaction)
    assert (target / planner.STATE).read_bytes() == before
    assert all(not (target / root).exists() for root in plan['recovery_roots'])


@pytest.mark.parametrize('change', ['extra', 'mode', 'edit', 'replace_dir'])
def test_rollback_preserves_external_changes(recovery, change):
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    root = target / plan['recovery_roots'][0]
    if change == 'extra': (root / 'external-link').symlink_to('/external')
    if change == 'mode': root.chmod(0o700)
    if change == 'edit': (root / 'SKILL.md').write_text('custom now')
    if change == 'replace_dir':
        root.rename(root.with_name(root.name + '-original'))
        root.mkdir()
    with pytest.raises(tx.InstallError):
        tx.rollback(target, result['transaction'])
    assert root.exists()


def test_unrecorded_directory_claim_fails_closed(recovery, monkeypatch):
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    original = tx._save
    def fail_directory_record(target, journal):
        if journal.get('recovery_dirs'):
            raise OSError('injected before recording mkdir identity')
        return original(target, journal)
    monkeypatch.setattr(tx, '_save', fail_directory_record)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    monkeypatch.setattr(tx, '_save', original)
    with pytest.raises(tx.InstallError, match='unowned or changed recovery directory'):
        tx.rollback(target, error.value.transaction)
    assert (target / plan['recovery_roots'][0]).is_dir()


@pytest.mark.parametrize('extra', [[], ['--repair'], ['--with-agents'], ['--surface-only'],
    ['--selection-policy', 'curated'], ['--rollback', 'abc'], ['--list-transactions'],
    ['--apply-plan', 'plan.json'], ['--profile', 'profile.json']])
def test_cli_recovery_requires_preview_and_rejects_mixed_operations(recovery, extra, capsys):
    from core_install import cli
    repo, target, request = recovery
    args = ['--repo', str(repo), '--target', str(target), '--recover-missing', '--cli', 'grok',
            '--slug', request['slugs'][0]]
    if extra: args.append('--dry-run')
    assert cli.main(args + extra) == 1
    assert 'INVALID_REQUEST' in capsys.readouterr().err


def test_cli_recovery_preview_then_apply_plan(recovery, tmp_path, capsys):
    from core_install import cli
    repo, target, request = recovery
    args = ['--repo', str(repo), '--target', str(target)]
    assert cli.main(args + ['--recover-missing', '--cli', 'grok', '--slug', request['slugs'][0], '--dry-run']) == 0
    plan = json.loads(capsys.readouterr().out)
    saved = tmp_path / 'reviewed-plan.json'
    saved.write_text(json.dumps(plan))
    assert cli.main(args + ['--apply-plan', str(saved)]) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'complete'


@pytest.mark.parametrize('schema,policy', [(2, None), (3, 'curated'), (3, 'full_catalog')])
def test_recovery_never_expands_saved_membership(recovery, schema, policy):
    repo, target, request = recovery
    path = target / planner.STATE
    state = json.loads(path.read_text())
    removed_key = 'grok:skill:' + request['slugs'][1]
    state['selection'].remove(removed_key)
    del state['packages'][removed_key]
    state['schema'] = schema
    if policy is None: del state['selection_policy']
    else: state['selection_policy']['grok'] = policy
    path.write_text(json.dumps(state))
    request['slugs'] = request['slugs'][:1]
    plan = planner.plan(repo, target, request)
    assert plan['selection'] == state['selection']
    assert not any(removed_key.split(':')[-1] in a['path'] for a in plan['actions'])
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert json.loads(path.read_text())['selection'] == state['selection']


def test_source_symlink_and_source_drift_still_block(recovery):
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    source = repo / ('.grok/skills/' + request['slugs'][0] + '/SKILL.md')
    source.write_text('changed after preview')
    with pytest.raises(ValueError):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    source.unlink()
    source.symlink_to(repo / 'VERSION')
    with pytest.raises(ValueError, match='bundle identity mismatch'):
        planner.plan(repo, target, request)


@pytest.mark.parametrize('script', ['install-local.sh', 'deploy-surfaces.sh'])
def test_extracted_capsule_and_both_wrappers_recover(recovery, script, tmp_path):
    import shutil
    import subprocess
    import sys
    repo, target, request = recovery
    source_root = Path(__file__).resolve().parents[1]
    for name in ('install-local.sh', 'deploy-surfaces.sh', 'deploy-profile.py', 'install_bundle.py'):
        shutil.copy2(source_root / 'scripts' / name, repo / 'scripts' / name)
    install_bundle.build(repo)
    assert not (repo / 'scripts/core_install').exists()
    root = target / '.agents/skills'
    root.mkdir(parents=True)
    (root / 'addy').symlink_to('/not-followed')
    command = ['bash', str(repo / 'scripts' / script), '--target', str(target), '--allow-nonlocal-target']
    env = {**os.environ, 'PYTHON_BIN': sys.executable}
    preview = subprocess.run(command + ['--recover-missing', '--cli', 'grok', '--slug', request['slugs'][0], '--dry-run'],
                             capture_output=True, text=True, env=env)
    assert preview.returncode == 0, preview.stdout + preview.stderr
    value = json.loads(preview.stdout)
    assert value['shared_exposure']['before_slugs'] == ['addy']
    saved = tmp_path / 'capsule-plan.json'
    saved.write_text(preview.stdout)
    result = subprocess.run(command + ['--apply-plan', str(saved)], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    transaction = json.loads(result.stdout)['transaction']
    rollback = subprocess.run(command + ['--rollback', transaction], capture_output=True, text=True, env=env)
    assert rollback.returncode == 0, rollback.stdout + rollback.stderr
    assert not (target / '.grok/skills' / request['slugs'][0]).exists()
    assert os.readlink(root / 'addy') == '/not-followed'


def test_recovery_stage_source_drift_and_extra_member_before_receipt(recovery, monkeypatch):
    from core_install import recovery as rec
    repo, target, request = recovery
    before = (target / planner.STATE).read_bytes()
    plan = planner.plan(repo, target, request)
    original = rec.publish
    def extra_member(target, journal, action, data, save):
        original(target, journal, action, data, save)
        put(target, plan['recovery_roots'][0] + '/external', 'preserve')
    monkeypatch.setattr(rec, 'publish', extra_member)
    with pytest.raises(tx.InstallError):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert (target / planner.STATE).read_bytes() == before
    assert (target / plan['recovery_roots'][0] / 'external').read_text() == 'preserve'


def test_shared_absent_empty_and_blocked_missing_projection(recovery):
    repo, target, request = recovery
    first = planner.plan(repo, target, request)
    assert first['shared_exposure']['observation_status'] == 'absent'
    assert first['shared_exposure']['before_slugs'] == []
    (target / '.agents/skills').mkdir(parents=True)
    second = planner.plan(repo, target, request)
    assert second['shared_exposure']['observation_status'] == 'observed'
    assert second['shared_exposure']['before_slugs'] == []


def test_shared_link_atime_change_is_not_identity_drift(installation, monkeypatch):
    from core_install import discovery
    from types import SimpleNamespace
    repo, target = installation
    root = target / '.agents/skills'
    root.mkdir(parents=True)
    link = root / 'addy'
    link.symlink_to('/unrelated')
    original = Path.lstat
    calls = []
    def lstat(path):
        info = original(path)
        if path == link:
            calls.append(path)
            if len(calls) == 2:
                fields = {name: getattr(info, name) for name in dir(info) if name.startswith('st_')}
                fields['st_atime'] += 1
                fields['st_atime_ns'] += 1_000_000_000
                return SimpleNamespace(**fields)
        return info
    monkeypatch.setattr(Path, 'lstat', lstat)
    observation = discovery.shared_root(target)
    assert observation['status'] == 'observed'
    assert observation['entries']['addy']['target'] == '/unrelated'
    assert len(calls) == 2


def test_publication_before_durable_file_record_fails_closed(recovery, monkeypatch):
    from core_install import recovery as rec
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    original = rec.os.link
    published = []
    def interrupted_link(source, destination, **kwargs):
        original(source, destination, **kwargs)
        published.append(Path(destination))
        raise OSError('injected after publication before durable file record')
    monkeypatch.setattr(rec.os, 'link', interrupted_link)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert published[0].exists()
    with pytest.raises(tx.InstallError, match='unexpected recovery member'):
        tx.rollback(target, error.value.transaction)
    assert published[0].exists()


def test_schema1_reader_rejects_recovery_journal(recovery):
    # Fixed legacy reader contract: no moving HEAD, installed tool or Git history.
    # This fixture proves the format boundary, not full archived-engine behavior.
    def schema1_reader(path):
        journal = json.loads(path.read_text())
        if journal.get('schema') != 1:
            raise ValueError('invalid transaction journal')
        return journal

    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    journal_path = target / tx.TRANSACTIONS / result['transaction'] / 'journal.json'
    assert json.loads(journal_path.read_text())['schema'] == 2
    with pytest.raises(ValueError, match='invalid transaction journal'):
        schema1_reader(journal_path)
    assert (target / plan['recovery_roots'][0] / 'SKILL.md').exists()
    tx.rollback(target, result['transaction'])
    # Retained journals still require a capable installer after rollback.
    with pytest.raises(ValueError, match='invalid transaction journal'):
        schema1_reader(journal_path)


@pytest.mark.parametrize('extra', [['--repair'], ['--repair', '--cli', 'grok', '--slug', 'unknown']])
def test_ordinary_reviewed_repair_accepts_legacy_flags_without_overriding_plan(installation, tmp_path, capsys, extra):
    from core_install import cli
    repo, target = installation
    put(target, '.kiro/skills/architecture/SKILL.md', 'kiro-architecture-skill\n')
    request = dict(mode='repair', providers=['kiro'], runtime=False)
    plan = planner.plan(repo, target, request)
    assert not plan['blockers'] and not plan['preserved']
    saved = tmp_path / 'ordinary-repair.json'
    saved.write_text(json.dumps(plan))
    assert cli.main(['--repo', str(repo), '--target', str(target), '--apply-plan', str(saved), *extra]) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'complete'
    assert (target / '.kiro/skills/engos-design-architecture/SKILL.md').exists()
    assert not (target / '.grok').exists()


@pytest.mark.parametrize('extra', [['--repair'], ['--cli', 'grok'], ['--slug', 'engos-design-architecture'],
    ['--with-agents'], ['--surface-only', '--slug', 'engos-design-architecture'],
    ['--profile', 'unused.json'], ['--selection-policy', 'curated'],
    ['--list-transactions'], ['--strict-cli']])
def test_reviewed_recovery_rejects_fresh_flags_before_dispatch(recovery, tmp_path, capsys, extra):
    from core_install import cli
    repo, target, request = recovery
    before = (target / planner.STATE).read_bytes()
    saved = tmp_path / 'recovery.json'
    saved.write_text(json.dumps(planner.plan(repo, target, request)))
    assert cli.main(['--repo', str(repo), '--target', str(target), '--apply-plan', str(saved), *extra]) == 1
    assert 'INVALID_REQUEST' in capsys.readouterr().err
    assert (target / planner.STATE).read_bytes() == before
    assert not (target / tx.TRANSACTIONS).exists()
