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
    fired = []
    def claim(*args):
        fired.append(True)
        if kind == 'directory': root.mkdir()
        elif kind == 'file': root.write_text('external')
        else: root.symlink_to('/external')
        return original(*args)
    monkeypatch.setattr(rec, 'claim', claim)
    with pytest.raises(tx.InstallError, match='installation failed'):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired, 'root-appearance fault did not fire'
    assert root.is_symlink() if kind == 'link' else root.exists()
    assert not (target / plan['recovery_roots'][1]).exists()


def test_new_file_after_preflight_is_not_overwritten(recovery, monkeypatch):
    from core_install import recovery as rec
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    original = rec.os.link
    introduced = []
    def link(source, destination, **kwargs):
        if Path(destination).name == 'SKILL.md' and not introduced:
            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644, dir_fd=kwargs['dst_dir_fd'])
            try:
                os.write(fd, b'external writer')
            finally:
                os.close(fd)
            introduced.append(target / plan['recovery_roots'][0] / 'SKILL.md')
        return original(source, destination, **kwargs)
    monkeypatch.setattr(rec.os, 'link', link)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert introduced, 'publication fault did not fire'
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
    fired = []
    def interrupted(*args):
        original(*args)
        fired.append(True)
        raise OSError('injected after durable publish')
    monkeypatch.setattr(rec, 'publish', interrupted)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired, 'durable-publication interruption did not fire'
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
    from core_install.recovery_fs import Session
    original = Session.save
    fired = []
    def fail_directory_record(fs, journal):
        if journal.get('recovery_dirs'):
            fired.append(True)
            raise OSError('injected before recording mkdir identity')
        return original(fs, journal)
    monkeypatch.setattr(Session, 'save', fail_directory_record)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired, 'directory-record fault did not fire'
    monkeypatch.setattr(Session, 'save', original)
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
    fired = []
    def extra_member(fs, journal, action, data, save):
        original(fs, journal, action, data, save)
        put(fs.target, plan['recovery_roots'][0] + '/external', 'preserve')
        fired.append(True)
    monkeypatch.setattr(rec, 'publish', extra_member)
    with pytest.raises(tx.InstallError):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert (target / planner.STATE).read_bytes() == before
    assert fired, 'extra-member fault did not fire'
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
        if Path(destination).name == 'SKILL.md':
            published.append(target / plan['recovery_roots'][0] / 'SKILL.md')
            raise OSError('injected after publication before durable file record')
    monkeypatch.setattr(rec.os, 'link', interrupted_link)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert published, 'post-publication fault did not fire'
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


def test_empty_shared_slot_cannot_bypass_other_readers_curated_selection(installation):
    repo, target = installation
    slug = 'engos-design-architecture'
    state = dict(schema=3, owner='Core-Prompts', selection=[], packages={}, runtime={},
                 registrations={}, selection_policy={'gemini': 'curated'})
    state_path = put(target, planner.STATE, tx.encoded(state))
    shared = target / '.agents/skills' / slug
    shared.mkdir(parents=True)
    before = state_path.read_bytes()
    request = dict(mode='install', providers=['codex'], slugs=[slug], kinds=['skill'], runtime=False)
    plan = planner.plan(repo, target, request)
    assert plan['shared_exposure']['known_readers'] == ['codex', 'gemini']
    assert state_path.read_bytes() == before and not list(shared.iterdir())
    print(json.dumps({'known_readers': plan['shared_exposure']['known_readers'],
                      'before_slugs': plan['shared_exposure']['before_slugs'],
                      'blockers': plan['blockers'],
                      'shared_writes': [a['path'] for a in plan['actions']
                                        if a['path'].startswith('.agents/skills/')]}))
    assert any('SHARED_SURFACE_POLICY_CONFLICT' in blocker and 'gemini' in blocker
               for blocker in plan['blockers'])
    with pytest.raises(tx.InstallError, match='unresolved blockers'):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert state_path.read_bytes() == before and not list(shared.iterdir())


@pytest.mark.parametrize('other_policy', ['curated', 'full_catalog'])
def test_empty_shared_slot_can_be_populated_with_compatible_other_reader_policy(installation, other_policy):
    repo, target = installation
    slug = 'engos-design-architecture'
    selection = ['gemini:skill:' + slug] if other_policy == 'curated' else []
    state = dict(schema=3, owner='Core-Prompts', selection=selection, packages={}, runtime={},
                 registrations={}, selection_policy={'gemini': other_policy})
    put(target, planner.STATE, tx.encoded(state))
    shared = target / '.agents/skills' / slug
    shared.mkdir(parents=True)
    request = dict(mode='install', providers=['codex'], slugs=[slug], kinds=['skill'], runtime=False)
    plan = planner.plan(repo, target, request)
    assert not plan['blockers']
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert (shared / 'SKILL.md').read_text() == 'current skill\n'
    assert planner.read_state(target)['selection_policy']['gemini'] == other_policy


def test_empty_shared_slot_accepts_exact_joint_curated_profile(installation):
    repo, target = installation
    slug = 'engos-design-architecture'
    put(target, planner.STATE, tx.encoded(dict(schema=3, owner='Core-Prompts', selection=[], packages={},
        runtime={}, registrations={}, selection_policy={'gemini': 'curated'})))
    shared = target / '.agents/skills' / slug
    shared.mkdir(parents=True)
    profile = dict(schema=1, scope='skills', targets=['codex', 'gemini'], slugs=[slug])
    request = dict(mode='repair', providers=profile['targets'], profile=profile,
                   selection_policy='curated', kinds=['skill'])
    plan = planner.plan(repo, target, request)
    assert not plan['blockers']
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert (shared / 'SKILL.md').read_text() == 'current skill\n'
    state = planner.read_state(target)
    assert state['selection'] == ['codex:skill:' + slug, 'gemini:skill:' + slug]
    assert state['selection_policy'] == {'codex': 'curated', 'gemini': 'curated'}


def test_empty_shared_slot_does_not_bypass_full_catalog_joint_consent(installation):
    repo, target = installation
    slug = 'engos-design-architecture'
    put(target, planner.STATE, tx.encoded(dict(schema=3, owner='Core-Prompts', selection=[], packages={},
        runtime={}, registrations={}, selection_policy={'gemini': 'curated'})))
    shared = target / '.agents/skills' / slug
    shared.mkdir(parents=True)
    request = dict(mode='sync', providers=['codex'], selection_policy='full_catalog')
    plan = planner.plan(repo, target, request)
    assert any('full catalog requires exact joint shared-reader profile' in b for b in plan['blockers'])
    assert any('expansion exceeds gemini' in b for b in plan['blockers'])
    with pytest.raises(tx.InstallError, match='unresolved blockers'):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert not list(shared.iterdir())


def test_existing_shared_entrypoint_update_is_not_new_policy_exposure(installation):
    repo, target = installation
    slug = 'engos-design-architecture'
    request = dict(mode='install', providers=['codex'], slugs=[slug], kinds=['skill'], runtime=False)
    initial = planner.plan(repo, target, request)
    tx.apply(repo, target, initial, lambda: planner.plan(repo, target, request))
    state = planner.read_state(target)
    state.update(schema=3, selection_policy={'codex': 'curated', 'gemini': 'curated'})
    put(target, planner.STATE, tx.encoded(state))
    for provider in ('codex', 'gemini'):
        put(repo, f'.{provider}/skills/{slug}/SKILL.md', 'updated existing skill\n')
    install_bundle.build(repo)
    request = dict(mode='sync', providers=['codex'], runtime=False)
    plan = planner.plan(repo, target, request)
    assert not plan['blockers']
    writes = [a for a in plan['actions'] if a['path'] == f'.agents/skills/{slug}/SKILL.md']
    assert len(writes) == 1 and writes[0]['before'] is not None
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert (target / writes[0]['path']).read_text() == 'updated existing skill\n'
    assert planner.read_state(target)['selection_policy']['gemini'] == 'curated'
    assert 'gemini:skill:' + slug not in planner.read_state(target)['selection']


def _trace_recovery_publication(monkeypatch, target, relative):
    """Observe actual syscalls; a refactor must still fire the asserted boundary."""
    import stat
    from core_install import recovery as rec
    path = target / relative
    trace = dict(link_fired=False, parent_synced=False, ownership_save_fired=False, events=[])
    real_link, real_fsync = rec.os.link, rec.os.fsync

    def link(source, destination, **kwargs):
        result = real_link(source, destination, **kwargs)
        if not trace['link_fired'] and Path(destination).name == path.name:
            assert path.is_file(), 'publication hook must observe the expected first package file'
            info = path.parent.stat()
            trace.update(link_fired=True, directory=(info.st_dev, info.st_ino))
            trace['events'].append('destination_link_created')
        return result

    def fsync(fd):
        info = os.fstat(fd)
        result = real_fsync(fd)
        if (trace['link_fired'] and stat.S_ISDIR(info.st_mode)
                and (info.st_dev, info.st_ino) == trace['directory']):
            trace['parent_synced'] = True
            trace['events'].append('destination_directory_fsynced')
        return result

    monkeypatch.setattr(rec.os, 'link', link)
    monkeypatch.setattr(rec.os, 'fsync', fsync)
    return trace


def test_recovery_safety_directory_sync_precedes_durable_file_record(recovery, monkeypatch):
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    first = next(a['path'] for a in plan['actions'] if a['path'].endswith('/SKILL.md'))
    trace = _trace_recovery_publication(monkeypatch, target, first)
    from core_install.recovery_fs import Session
    real_save = Session.save

    def save(fs, journal):
        real_save(fs, journal)
        if first in journal.get('recovery_files', {}) and not trace['ownership_save_fired']:
            trace['ownership_save_fired'] = True
            trace['synced_at_first_durable_record'] = trace['parent_synced']
            trace['events'].append('file_ownership_journal_saved')

    monkeypatch.setattr(Session, 'save', save)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    print(json.dumps({'control': 'CORE006-order', **trace}))
    assert trace['link_fired'] and trace['ownership_save_fired'], 'required observation hooks did not fire'
    assert trace['synced_at_first_durable_record'], 'file ownership persisted before destination directory fsync'


def test_recovery_safety_simulated_unsynced_namespace_loss_remains_rollbackable(recovery, monkeypatch):
    repo, target, request = recovery
    before = (target / planner.STATE).read_bytes()
    plan = planner.plan(repo, target, request)
    first = next(a['path'] for a in plan['actions'] if a['path'].endswith('/SKILL.md'))
    trace = _trace_recovery_publication(monkeypatch, target, first)
    from core_install.recovery_fs import Session
    real_save = Session.save

    def interrupted_save(fs, journal):
        real_save(fs, journal)
        if first in journal.get('recovery_files', {}) and not trace['ownership_save_fired']:
            trace.update(ownership_save_fired=True, fault_fired=True)
            # Deterministic namespace-loss model, not a real reboot/power-loss test.
            trace['simulated_namespace_loss'] = not trace['parent_synced']
            if trace['simulated_namespace_loss']:
                (target / first).unlink()
            raise OSError('injected interruption after durable file record')

    monkeypatch.setattr(Session, 'save', interrupted_save)
    with pytest.raises(tx.InstallError) as interrupted:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    monkeypatch.setattr(Session, 'save', real_save)
    print(json.dumps({'control': 'CORE006-simulated-namespace-loss', **trace}))
    assert trace['link_fired'] and trace['ownership_save_fired'] and trace['fault_fired']
    result = tx.rollback(target, interrupted.value.transaction)
    assert result['status'] == 'rolled-back'
    assert (target / planner.STATE).read_bytes() == before
    assert all(not (target / root).exists() for root in plan['recovery_roots'])


def test_recovery_safety_ancestor_swap_at_temp_creation_never_writes_foreign_tree(recovery, monkeypatch):
    from core_install import recovery as rec
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    first = next(a['path'] for a in plan['actions'] if a['path'].endswith('/SKILL.md'))
    claimed = (target / first).parent
    parked = claimed.with_name(claimed.name + '-race-parked')
    foreign = target.parent / 'foreign-sentinel'
    assert not foreign.exists() and not parked.exists()
    foreign.mkdir()
    (foreign / 'sentinel.txt').write_text('foreign content must remain byte-exact')
    before = {p.name: p.read_bytes() for p in foreign.iterdir()}
    real_open = rec.os.open
    fault = dict(fired=False)

    def raced_open(path, flags, mode=0o777, *, dir_fd=None):
        # tempfile.mkstemp reaches this real O_CREAT boundary. Descriptor-based
        # creation must remain anchored even when the pathname is replaced here.
        if not fault['fired'] and flags & os.O_CREAT and Path(path).name.startswith('.core-recovery-'):
            if dir_fd is None:
                expected_parent = Path(path).parent == claimed
            else:
                anchor, current = os.fstat(dir_fd), claimed.stat()
                expected_parent = (anchor.st_dev, anchor.st_ino) == (current.st_dev, current.st_ino)
            if expected_parent:
                claimed.rename(parked)
                claimed.symlink_to(foreign, target_is_directory=True)
                fault.update(fired=True, dir_fd_used=dir_fd is not None)
        if dir_fd is None:
            return real_open(path, flags, mode)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(rec.os, 'open', raced_open)
    error = None
    try:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    except tx.InstallError as exc:
        error = exc
    after = {p.name: p.read_bytes() for p in foreign.iterdir()}
    print(json.dumps({'control': 'CORE007-temp-creation-swap', **fault,
                      'foreign_before': sorted(before), 'foreign_after': sorted(after),
                      'installer_error': str(error)}))
    assert fault['fired'], 'ancestor replacement did not reach the real creation boundary'
    assert after == before, 'installer wrote into the foreign sentinel tree before rejecting the changed ancestor'
    assert error is not None, 'changed claimed-directory identity was not rejected'


def _safety_snapshot(root):
    import hashlib
    import stat
    result = {}
    for path in sorted(root.rglob('*')):
        info = path.lstat()
        result[str(path.relative_to(root))] = (stat.S_IFMT(info.st_mode), info.st_mode & 0o777,
            os.readlink(path) if path.is_symlink() else hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None)
    return result


@pytest.mark.parametrize('kind', ['regular', 'symlink'])
def test_recovery_adv001_never_adopts_substituted_temp_inode(recovery, monkeypatch, kind):
    from core_install import recovery as rec
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    first = target / plan['recovery_roots'][0] / 'SKILL.md'
    external = target.parent / 'adv001-external'
    external.write_text('external sentinel')
    before = external.read_bytes()
    real_link = rec.os.link
    fired = []
    def link(source, destination, **kwargs):
        if str(source).startswith('.core-recovery-') and not fired:
            parent = kwargs['src_dir_fd']
            fd = os.open(source, os.O_RDONLY, dir_fd=parent)
            try:
                original = os.fstat(fd)
                data = os.read(fd, 65536)
            finally:
                os.close(fd)
            os.rename(source, source + '-original', src_dir_fd=parent, dst_dir_fd=parent)
            if kind == 'regular':
                replacement = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, original.st_mode & 0o777, dir_fd=parent)
                try: os.write(replacement, data)
                finally: os.close(replacement)
            else:
                os.symlink(str(external), source, dir_fd=parent)
            fired.append((original.st_ino, os.stat(source, dir_fd=parent, follow_symlinks=False).st_ino))
        return real_link(source, destination, **kwargs)
    monkeypatch.setattr(rec.os, 'link', link)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired and fired[0][0] != fired[0][1], 'temp substitution did not fire with a distinct inode'
    journal = json.loads((target / tx.TRANSACTIONS / error.value.transaction / 'journal.json').read_text())
    assert not journal.get('recovery_files')
    assert external.read_bytes() == before
    assert first.exists() or first.is_symlink()
    with pytest.raises((ValueError, OSError)):
        tx.rollback(target, error.value.transaction)
    assert external.read_bytes() == before


@pytest.mark.parametrize('phase,boundary,area', [
    ('apply', 'mkdir', 'skills'), ('apply', 'open', 'package'), ('apply', 'open', 'resource'),
    ('apply', 'link', 'package'), ('apply', 'unlink', 'package'), ('apply', 'fsync', 'package'),
    ('rollback', 'unlink', 'package'), ('rollback', 'rmdir', 'skills'),
    ('apply', 'open', 'lock'), ('apply', 'link', 'journal'),
    ('apply', 'link', 'stage'), ('apply', 'rename', 'receipt')])
def test_recovery_descriptor_ancestors_never_redirect_mutations(recovery, monkeypatch, phase, boundary, area):
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    result = None
    if phase == 'rollback':
        result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    foreign = target.parent / 'descriptor-foreign'
    foreign.mkdir()
    (foreign / 'sentinel').write_bytes(b'untouched')
    state = dict(fired=False, baseline=_safety_snapshot(foreign))
    selected = dict(rel=None)
    original_atomic = Session.atomic
    def atomic(fs, rel, data, mode, expected=None):
        if ((area == 'journal' and rel.endswith('/journal.json')) or
                (area == 'stage' and '/after/' in rel) or (area == 'receipt' and rel == tx.INSTALLATION)):
            selected['rel'] = rel
        return original_atomic(fs, rel, data, mode, expected)
    monkeypatch.setattr(Session, 'atomic', atomic)
    original = getattr(os, boundary)
    def mutation(*args, **kwargs):
        if state['fired']:
            return original(*args, **kwargs)
        leaf = str(args[1] if boundary in ('link', 'rename') else args[0]) if boundary != 'fsync' else ''
        fd = args[0] if boundary == 'fsync' else kwargs.get('dir_fd', kwargs.get('dst_dir_fd'))
        anchor_rel = '.grok/skills' if area == 'skills' else plan['recovery_roots'][0]
        expected_parent = target / anchor_rel
        allowed = True
        if area == 'resource': anchor_rel += '/resources'; expected_parent = target / anchor_rel
        if area == 'lock':
            anchor_rel = tx.STATE; expected_parent = target / tx.STATE
            allowed = leaf == 'installation.lock' and bool(args[1] & os.O_CREAT)
        elif area in ('journal', 'stage', 'receipt'):
            allowed = selected['rel'] is not None and leaf == Path(selected['rel']).name
            if allowed:
                expected_parent = target / Path(selected['rel']).parent
                anchor_rel = tx.STATE if area == 'receipt' else str(Path(selected['rel']).parent)
        elif boundary == 'open': allowed = leaf.startswith('.core-recovery-') and bool(args[1] & os.O_CREAT)
        elif boundary == 'link': allowed = leaf == 'SKILL.md'
        elif boundary == 'unlink': allowed = leaf == 'SKILL.md' if phase == 'rollback' else leaf.startswith('.core-recovery-')
        if allowed and fd is not None and expected_parent.exists() and not expected_parent.is_symlink():
            opened, expected = os.fstat(fd), expected_parent.stat()
            if (opened.st_dev, opened.st_ino) == (expected.st_dev, expected.st_ino):
                anchor = target / anchor_rel
                parked = anchor.with_name(anchor.name + '-parked')
                # Seed names that a path-following mutation would otherwise touch.
                if boundary == 'link': (foreign / Path(args[0]).name).write_text('foreign source')
                if boundary in ('unlink', 'rename'): (foreign / leaf).write_text('foreign leaf')
                if boundary == 'rmdir': (foreign / leaf).mkdir()
                state['baseline'] = _safety_snapshot(foreign)
                anchor.rename(parked)
                anchor.symlink_to(foreign, target_is_directory=True)
                state.update(fired=True, anchor=str(anchor), fd_used=True)
        return original(*args, **kwargs)
    monkeypatch.setattr(os, boundary, mutation)
    failed = False
    try:
        if phase == 'apply': tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
        else: tx.rollback(target, result['transaction'])
    except (ValueError, OSError): failed = True
    assert state['fired'], f'{phase}/{boundary}/{area} hook did not fire'
    assert _safety_snapshot(foreign) == state['baseline'], 'foreign tree changed'
    assert failed, 'namespace rebinding was not reported'


@pytest.mark.parametrize('where', ['transaction', 'before', 'after', 'journal', 'stage'])
def test_recovery_adv002_exclusive_metadata_preserves_arriving_nodes(recovery, monkeypatch, where):
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    real_mkdir, real_link = os.mkdir, os.link
    fired = []
    def mkdir(name, *args, **kwargs):
        matching = ((where == 'transaction' and len(str(name)) == 32) or str(name) == where)
        if matching and not fired:
            real_mkdir(name, *args, **kwargs)
            parent = kwargs['dir_fd']
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=parent)
            try:
                leaf = os.open('foreign', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640, dir_fd=child)
                os.write(leaf, b'preserve'); os.close(leaf)
                fired.append(('directory', os.fstat(child).st_ino))
            finally: os.close(child)
        return real_mkdir(name, *args, **kwargs)
    def link(source, destination, **kwargs):
        if not fired and ((where == 'journal' and destination == 'journal.json') or
                          (where == 'stage' and str(destination).isdigit())):
            leaf = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640, dir_fd=kwargs['dst_dir_fd'])
            try:
                os.write(leaf, b'preserve')
                fired.append(('file', os.fstat(leaf).st_ino))
            finally: os.close(leaf)
        return real_link(source, destination, **kwargs)
    monkeypatch.setattr(os, 'mkdir', mkdir); monkeypatch.setattr(os, 'link', link)
    with pytest.raises((ValueError, OSError)):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired, 'metadata collision did not fire'
    retained = [p for p in target.rglob('*') if p.is_file() and p.read_bytes() == b'preserve']
    assert len(retained) == 1 and retained[0].stat().st_mode & 0o777 == 0o640
    if fired[0][0] == 'file': assert retained[0].stat().st_ino == fired[0][1]
    else: assert retained[0].parent.stat().st_ino == fired[0][1]


@pytest.mark.parametrize('where', ['journal', 'receipt'])
def test_recovery_guarded_metadata_replacement_preserves_changed_preimage(recovery, monkeypatch, where):
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    original = Session.atomic
    changed = []
    def atomic(fs, rel, data, mode, expected=None):
        if not changed and expected is not None and (rel.endswith('/journal.json') if where == 'journal' else rel == tx.INSTALLATION):
            path = target / rel
            path.rename(path.with_name(path.name + '-old'))
            path.write_bytes(b'foreign metadata')
            changed.append((path, path.stat().st_ino))
        return original(fs, rel, data, mode, expected)
    monkeypatch.setattr(Session, 'atomic', atomic)
    with pytest.raises(tx.InstallError): tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert changed, 'owned-preimage fault did not fire'
    assert changed[0][0].read_bytes() == b'foreign metadata' and changed[0][0].stat().st_ino == changed[0][1]


@pytest.mark.parametrize('boundary', ['after_link', 'directory_sync', 'before_file_save', 'after_file_save', 'after_save_replace', 'after_temp_unlink'])
def test_recovery_durability_faults_reconcile_actual_journal(recovery, monkeypatch, boundary):
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    first = next(a['path'] for a in plan['actions'] if a['path'].endswith('/SKILL.md'))
    trace = _trace_recovery_publication(monkeypatch, target, first)
    actual_link, actual_sync, actual_save, actual_atomic = os.link, os.fsync, Session.save, Session.atomic
    fault = dict(fired=False, saving_file=False)
    def link(*args, **kwargs):
        result = actual_link(*args, **kwargs)
        if boundary == 'after_link' and trace['link_fired'] and not fault['fired']:
            fault['fired'] = True; raise OSError('injected after package link')
        return result
    def sync(fd):
        info = os.fstat(fd)
        if (boundary == 'directory_sync' and trace['link_fired'] and not fault['fired']
                and (info.st_dev, info.st_ino) == trace['directory']):
            fault['fired'] = True; raise OSError('injected destination directory fsync failure')
        return actual_sync(fd)
    def save(fs, journal):
        first_record = first in journal.get('recovery_files', {})
        if first_record and not fault['fired']:
            if boundary == 'before_file_save':
                fault['fired'] = True; raise OSError('injected before ownership save')
            if boundary == 'after_temp_unlink' and not journal.get('recovery_temps'):
                fault['fired'] = True; raise OSError('injected after durable temp unlink')
        fault['saving_file'] = first_record
        actual_save(fs, journal)
        fault['saving_file'] = False
        if first_record and boundary == 'after_file_save' and not fault['fired']:
            fault['fired'] = True; raise OSError('injected after durable ownership save')
    def atomic(fs, rel, data, mode, expected=None):
        result = actual_atomic(fs, rel, data, mode, expected)
        if (boundary == 'after_save_replace' and fault['saving_file'] and not fault['fired']
                and rel.endswith('/journal.json') and expected is not None):
            fault['fired'] = True; raise OSError('injected after visible journal replacement')
        return result
    monkeypatch.setattr(os, 'link', link); monkeypatch.setattr(os, 'fsync', sync)
    monkeypatch.setattr(Session, 'save', save); monkeypatch.setattr(Session, 'atomic', atomic)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fault['fired'], boundary + ' fault did not fire'
    journal = json.loads((target / tx.TRANSACTIONS / error.value.transaction / 'journal.json').read_text())
    recorded = first in journal.get('recovery_files', {})
    assert not recorded or trace['parent_synced'], 'visible ownership fact preceded namespace durability'
    monkeypatch.setattr(Session, 'save', actual_save); monkeypatch.setattr(Session, 'atomic', actual_atomic)
    monkeypatch.setattr(os, 'link', actual_link); monkeypatch.setattr(os, 'fsync', actual_sync)
    if recorded:
        assert tx.rollback(target, error.value.transaction)['status'] == 'rolled-back'
        assert all(not (target / root).exists() for root in plan['recovery_roots'])
    else:
        with pytest.raises(tx.InstallError): tx.rollback(target, error.value.transaction)
        assert (target / first).exists(), 'unrecorded publication was deleted'
    if boundary == 'after_save_replace': assert 'content_sha256' in str(error.value)


def test_recovery_old_schema2_missing_temp_field_and_repeat_rollback(recovery):
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    path = target / tx.TRANSACTIONS / result['transaction'] / 'journal.json'
    value = json.loads(path.read_text()); del value['recovery_temps']; path.write_bytes(tx.encoded(value))
    assert tx.rollback(target, result['transaction'])['status'] == 'rolled-back'
    assert tx.rollback(target, result['transaction'])['status'] == 'rolled-back'


def test_recovery_foreign_recorded_temp_is_not_deleted(recovery, monkeypatch):
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    actual = Session.save; fired = []
    def save(fs, journal):
        actual(fs, journal)
        if journal.get('recovery_files') and not fired:
            fired.append(True); raise OSError('injected before temp cleanup')
    monkeypatch.setattr(Session, 'save', save)
    with pytest.raises(tx.InstallError) as error: tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired
    monkeypatch.setattr(Session, 'save', actual)
    journal = json.loads((target / tx.TRANSACTIONS / error.value.transaction / 'journal.json').read_text())
    temp = target / next(iter(journal['recovery_temps']))
    data, mode = temp.read_bytes(), temp.stat().st_mode & 0o777
    temp.rename(target.parent / 'held-original-temp')
    temp.write_bytes(data); temp.chmod(mode); inode = temp.stat().st_ino
    with pytest.raises(tx.InstallError): tx.rollback(target, error.value.transaction)
    assert temp.read_bytes() == data and temp.stat().st_ino == inode


@pytest.mark.parametrize('unsupported', ['flag', 'nonblock', 'dir_fd', 'preflight_sync'])
def test_recovery_admission_failure_precedes_mutation_but_ordinary_route_works(recovery, monkeypatch, unsupported):
    from core_install import recovery_fs as fsmod
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    before = _safety_snapshot(target)
    fired = []
    with monkeypatch.context() as patch:
        if unsupported == 'flag': patch.delattr(os, 'O_NOFOLLOW')
        elif unsupported == 'nonblock': patch.delattr(os, 'O_NONBLOCK')
        elif unsupported == 'dir_fd': patch.setattr(os, 'supports_dir_fd', os.supports_dir_fd - {fsmod._PRIMITIVES['rename']})
        else:
            def fail(fd):
                fired.append(True)
                raise OSError('injected existing-directory preflight fsync failure')
            patch.setattr(os, 'fsync', fail)
        with pytest.raises((ValueError, OSError)):
            tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
        assert _safety_snapshot(target) == before
        if unsupported == 'preflight_sync': assert fired, 'preflight sync fault did not fire'
        if unsupported != 'preflight_sync':
            ordinary = dict(mode='install', providers=['kiro'], kinds=['skill'], runtime=False)
            proposed = planner.plan(repo, target, ordinary)
            tx.apply(repo, target, proposed, lambda: planner.plan(repo, target, ordinary))
            assert (target / '.kiro/skills/engos-design-architecture/SKILL.md').exists()


def test_recovery_uses_advertised_rename_without_signature_introspection(recovery, monkeypatch):
    import inspect
    repo, target, request = recovery
    monkeypatch.setattr(os, 'supports_dir_fd', os.supports_dir_fd - {os.replace})
    actual = inspect.signature
    def signature(value, *args, **kwargs):
        if value is os.link: raise ValueError('supported builtin has no signature')
        return actual(value, *args, **kwargs)
    monkeypatch.setattr(inspect, 'signature', signature)
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert tx.rollback(target, result['transaction'])['status'] == 'rolled-back'


def test_recovery_and_ordinary_share_persistent_flock(recovery):
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    with tx._lock(target):
        inode = (target / tx.STATE / 'installation.lock').stat().st_ino
        with pytest.raises(tx.InstallError, match='lock is held'):
            tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    ordinary = dict(mode='sync', providers=['grok'], runtime=False)
    proposed = planner.plan(repo, target, ordinary)
    with Session(target) as fs:
        fs.lock()
        with pytest.raises(tx.InstallError, match='lock is held'):
            tx.apply(repo, target, proposed, lambda: planner.plan(repo, target, ordinary))
    assert (target / tx.STATE / 'installation.lock').stat().st_ino == inode
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    tx.rollback(target, result['transaction'])
    assert (target / tx.STATE / 'installation.lock').stat().st_ino == inode


def test_recovery_preserves_lock_replaced_after_open(recovery, monkeypatch):
    import fcntl
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    path = target / tx.STATE / 'installation.lock'
    actual = fcntl.flock; fired = []
    def flock(fd, operation):
        actual(fd, operation)
        if not fired:
            path.rename(path.with_name('original-lock'))
            path.write_bytes(b'foreign lock'); path.chmod(0o640)
            fired.append(path.stat().st_ino)
    monkeypatch.setattr(fcntl, 'flock', flock)
    with pytest.raises(tx.InstallError, match='lock binding changed'):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired and path.stat().st_ino == fired[0] and path.read_bytes() == b'foreign lock'
    assert not (target / tx.TRANSACTIONS).exists()


@pytest.mark.parametrize('site', ['__enter__', 'anchor', 'parent', 'open_directory', 'read_named', 'mkdir', 'lock', 'temporary'])
@pytest.mark.parametrize('exception', [OSError, KeyboardInterrupt, SystemExit])
def test_recovery_each_descriptor_owner_unwinds_baseexceptions(recovery, monkeypatch, site, exception):
    import inspect
    from core_install import recovery_fs as fsmod
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    real_open, real_close, actual_own = os.open, os.close, fsmod.own
    live, fired = set(), []
    def opening(*args, **kwargs):
        fd = real_open(*args, **kwargs); assert fd not in live; live.add(fd); return fd
    def closing(fd):
        assert fd in live, 'unowned or double-close descriptor'
        live.remove(fd); return real_close(fd)
    def owner(stack, fd):
        result = actual_own(stack, fd)
        if not fired and inspect.currentframe().f_back.f_code.co_name == site:
            fired.append((site, fd)); raise exception('injected after immediate FD ownership registration')
        return result
    monkeypatch.setattr(os, 'open', opening); monkeypatch.setattr(os, 'close', closing); monkeypatch.setattr(fsmod, 'own', owner)
    with pytest.raises((ValueError, OSError, KeyboardInterrupt, SystemExit)):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired, site + ' acquisition fault did not fire'
    assert not live, 'registered descriptors leaked after BaseException'


@pytest.mark.parametrize('underlying_close_happened', [False, True])
def test_recovery_ambiguous_close_is_reported_not_retried(recovery, monkeypatch, underlying_close_happened):
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    actual_open, actual_close = os.open, os.close
    live, attempts, fired = set(), {}, []
    def opening(*args, **kwargs):
        fd = actual_open(*args, **kwargs); live.add(fd); return fd
    def closing(fd):
        attempts[fd] = attempts.get(fd, 0) + 1
        if not fired:
            fired.append(fd)
            if underlying_close_happened:
                actual_close(fd); live.remove(fd)
            raise OSError('injected ambiguous close outcome')
        actual_close(fd); live.remove(fd)
    monkeypatch.setattr(os, 'open', opening); monkeypatch.setattr(os, 'close', closing)
    try:
        with pytest.raises(tx.InstallError, match='close outcome uncertain'):
            tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
        assert fired
        assert attempts[fired[0]] == 1, 'ambiguous descriptor close retried'
        assert live == (set() if underlying_close_happened else {fired[0]}), 'other owners failed to unwind'
    finally:
        # Test-only cleanup: the injected model knows whether its real close ran.
        for fd in tuple(live): actual_close(fd); live.remove(fd)


def test_recovery_publication_fds_do_not_accumulate(recovery, monkeypatch):
    from core_install import recovery as rec
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    actual_open, actual_close, actual_publish = os.open, os.close, rec.publish
    live, publication_counts = set(), []
    def opening(*args, **kwargs):
        fd = actual_open(*args, **kwargs); assert fd not in live; live.add(fd); return fd
    def closing(fd):
        assert fd in live, 'descriptor closed twice'; live.remove(fd); return actual_close(fd)
    def publish(*args):
        before = len(live); actual_publish(*args); publication_counts.append((before, len(live)))
    monkeypatch.setattr(os, 'open', opening); monkeypatch.setattr(os, 'close', closing); monkeypatch.setattr(rec, 'publish', publish)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert len(publication_counts) == 4 and all(a == b for a, b in publication_counts)
    assert not live
    tx.rollback(target, result['transaction'])
    assert not live


@pytest.mark.parametrize('ordinary_hint', [True, False])
def test_rollback_backend_classification_drift_blocks_before_mutations(recovery, monkeypatch, ordinary_hint):
    from contextlib import contextmanager
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    path = target / tx.TRANSACTIONS / result['transaction'] / 'journal.json'
    recovery_bytes = path.read_bytes()
    ordinary = json.loads(recovery_bytes)
    ordinary['schema'] = 1; ordinary['plan'].pop('recovery_roots'); ordinary['plan']['request']['mode'] = 'install'
    ordinary_bytes = tx.encoded(ordinary)
    fired = []
    if ordinary_hint:
        path.write_bytes(ordinary_bytes)
        actual = tx._lock
        @contextmanager
        def lock(target):
            with actual(target):
                path.write_bytes(recovery_bytes); fired.append(True); yield
        monkeypatch.setattr(tx, '_lock', lock)
    else:
        actual = Session.lock
        def lock(fs):
            actual(fs); path.write_bytes(ordinary_bytes); fired.append(True)
        monkeypatch.setattr(Session, 'lock', lock)
    with pytest.raises(tx.InstallError) as drift:
        tx.rollback(target, result['transaction'])
    assert drift.value.code == 'stale-journal'
    assert fired, 'rollback classification drift did not fire'
    assert path.read_bytes() == (recovery_bytes if ordinary_hint else ordinary_bytes)
    assert all((target / root / 'SKILL.md').is_file() for root in plan['recovery_roots'])


@pytest.mark.parametrize('boundary', ['open', 'fsync', 'link'])
def test_recovery_syscall_failure_closes_all_owned_descriptors(recovery, monkeypatch, boundary):
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    actual_open, actual_close, actual_sync, actual_link = os.open, os.close, os.fsync, os.link
    live, names, fired = set(), {}, []
    def opening(path, *args, **kwargs):
        if boundary == 'open' and str(path).startswith('.core-recovery-') and not fired:
            fired.append(True); raise OSError('injected real creation failure')
        fd = actual_open(path, *args, **kwargs); assert fd not in live
        live.add(fd); names[fd] = str(path); return fd
    def closing(fd):
        assert fd in live; live.remove(fd); names.pop(fd); return actual_close(fd)
    def sync(fd):
        if boundary == 'fsync' and names.get(fd, '').startswith('.core-recovery-') and not fired:
            fired.append(True); raise OSError('injected actual file fsync failure')
        return actual_sync(fd)
    def link(source, destination, **kwargs):
        if boundary == 'link' and str(source).startswith('.core-recovery-') and not fired:
            fired.append(True); raise OSError('injected real publication failure')
        return actual_link(source, destination, **kwargs)
    monkeypatch.setattr(os, 'open', opening); monkeypatch.setattr(os, 'close', closing)
    monkeypatch.setattr(os, 'fsync', sync); monkeypatch.setattr(os, 'link', link)
    with pytest.raises(tx.InstallError): tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert fired and not live


def test_recovery_reconciles_visible_journal_when_parent_fsync_fails(recovery, monkeypatch):
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    first = next(a['path'] for a in plan['actions'] if a['path'].endswith('/SKILL.md'))
    trace = _trace_recovery_publication(monkeypatch, target, first)
    save, rename, sync = Session.save, os.rename, os.fsync
    state = dict(saving_file=False, renamed=False, fired=False)
    def saving(fs, journal):
        state['saving_file'] = first in journal.get('recovery_files', {})
        save(fs, journal)
        state['saving_file'] = False
    def renaming(source, destination, **kwargs):
        result = rename(source, destination, **kwargs)
        if destination == 'journal.json' and state['saving_file']:
            info = os.fstat(kwargs['dst_dir_fd'])
            state.update(renamed=True, parent=(info.st_dev, info.st_ino))
        return result
    def syncing(fd):
        info = os.fstat(fd)
        if state['renamed'] and not state['fired'] and (info.st_dev, info.st_ino) == state['parent']:
            state['fired'] = True; raise OSError('injected after visible journal rename before directory sync')
        return sync(fd)
    monkeypatch.setattr(Session, 'save', saving); monkeypatch.setattr(os, 'rename', renaming); monkeypatch.setattr(os, 'fsync', syncing)
    with pytest.raises(tx.InstallError) as error: tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert state['fired'] and trace['parent_synced']
    journal = json.loads((target / tx.TRANSACTIONS / error.value.transaction / 'journal.json').read_text())
    assert first in journal['recovery_files'] and 'content_sha256' in str(error.value)
    monkeypatch.setattr(Session, 'save', save); monkeypatch.setattr(os, 'rename', rename); monkeypatch.setattr(os, 'fsync', sync)
    assert tx.rollback(target, error.value.transaction)['status'] == 'rolled-back'


def test_extracted_capsule_ordinary_route_survives_missing_recovery_capability(recovery, monkeypatch):
    from test_install_capsule import load
    repo, target, request = recovery
    capsule = load(Path(__file__).resolve().parents[1] / 'scripts/deploy-profile.py', 'missing_recovery_capability')
    ordinary = dict(mode='install', providers=['kiro'], kinds=['skill'], runtime=False)
    approved = capsule.installation_plan(repo, target, ordinary)
    monkeypatch.delattr(os, 'O_NOFOLLOW')
    capsule.installation_apply(repo, target, approved, lambda: capsule.installation_plan(repo, target, ordinary))
    assert (target / '.kiro/skills/engos-design-architecture/SKILL.md').exists()
    recovery_plan = capsule.installation_plan(repo, target, request)
    before = _safety_snapshot(target)
    with pytest.raises(ValueError, match='requires O_DIRECTORY and O_NOFOLLOW'):
        capsule.installation_apply(repo, target, recovery_plan, lambda: capsule.installation_plan(repo, target, request))
    assert _safety_snapshot(target) == before


@pytest.mark.parametrize('anchor_kind', ['state', 'skills', 'transactions', 'package'])
def test_recovery_retains_directory_binding_between_operations(recovery, monkeypatch, anchor_kind):
    from core_install import recovery as rec
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    fired = []
    original_mkdir, original_claim, original_publish = Session.mkdir, rec.claim, rec.publish
    def swap(rel):
        path = target / rel
        prior_receipt = (path / 'installation.json').read_bytes() if anchor_kind == 'state' else None
        path.rename(path.with_name(path.name + '-prior'))
        path.mkdir()
        (path / 'foreign-marker').write_text('foreign directory')
        if prior_receipt is not None: (path / 'installation.json').write_bytes(prior_receipt)
        fired.append((path, _safety_snapshot(path)))
    def mkdir(fs, rel, common=False):
        if not fired and ((anchor_kind == 'state' and rel == tx.TRANSACTIONS) or
                          (anchor_kind == 'transactions' and rel.startswith(tx.TRANSACTIONS + '/') and rel.count('/') == 2)):
            swap(tx.STATE if anchor_kind == 'state' else tx.TRANSACTIONS)
        return original_mkdir(fs, rel, common)
    def claim(fs, journal, save):
        if anchor_kind == 'skills' and not fired: swap('.grok/skills')
        return original_claim(fs, journal, save)
    def publish(fs, journal, action, data, save):
        if anchor_kind == 'package' and not fired: swap(plan['recovery_roots'][0])
        return original_publish(fs, journal, action, data, save)
    monkeypatch.setattr(Session, 'mkdir', mkdir); monkeypatch.setattr(rec, 'claim', claim); monkeypatch.setattr(rec, 'publish', publish)
    try: tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    except (ValueError, OSError): pass
    assert fired, 'between-operation directory replacement did not fire'
    assert _safety_snapshot(fired[0][0]) == fired[0][1], 'foreign replacement directory was adopted and mutated'


@pytest.mark.parametrize('when', ['after_lock', 'journal_rescan'])
def test_recovery_never_adopts_same_json_new_journal_inode(recovery, monkeypatch, when):
    from core_install import recovery as rec
    from core_install.recovery_fs import Session
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    path = target / tx.TRANSACTIONS / result['transaction'] / 'journal.json'
    data, mode = path.read_bytes(), path.stat().st_mode & 0o777
    fired = []
    def swap():
        path.rename(path.with_name('journal-original.json'))
        path.write_bytes(data); path.chmod(mode); fired.append(path.stat().st_ino)
    original_lock, original_journals = Session.lock, rec.journals
    def lock(fs):
        original_lock(fs)
        if when == 'after_lock' and not fired: swap()
    def journals(fs):
        if when == 'journal_rescan' and not fired: swap()
        return original_journals(fs)
    monkeypatch.setattr(Session, 'lock', lock); monkeypatch.setattr(rec, 'journals', journals)
    error = None
    try: tx.rollback(target, result['transaction'])
    except (ValueError, OSError) as exc: error = exc
    assert fired, 'same-JSON journal replacement did not fire'
    assert error is not None, 'foreign journal inode became replacement authority'
    assert path.read_bytes() == data and path.stat().st_ino == fired[0]


@pytest.mark.parametrize('engine', ['source', 'capsule'])
def test_recovery_rollback_fifo_substitution_is_bounded_and_releases_lock(recovery, engine):
    import subprocess
    import sys
    repo, target, request = recovery
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    first = target / plan['recovery_roots'][0] / 'SKILL.md'
    first.rename(target.parent / 'original-before-fifo')
    os.mkfifo(first, 0o640)
    fifo = first.lstat()
    state_before = (target / planner.STATE).read_bytes()
    journal_path = target / tx.TRANSACTIONS / result['transaction'] / 'journal.json'
    journal_before = journal_path.read_bytes()
    lock = target / tx.STATE / 'installation.lock'
    lock_inode = lock.stat().st_ino
    driver = r'''
import json, os, stat, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
if sys.argv[4] == 'capsule':
    import importlib.util
    spec = importlib.util.spec_from_file_location('fifo_capsule', Path(sys.argv[1]) / 'deploy-profile.py')
    capsule = importlib.util.module_from_spec(spec); spec.loader.exec_module(capsule)
    tx, recovery_fs = capsule._capsule_module('transaction'), capsule._capsule_module('recovery_fs')
else:
    from core_install import transaction as tx, recovery_fs
root = Path(sys.argv[2])
actual_open = os.open
fired = []
def opening(path, flags, *args, **kwargs):
    if str(path) == 'SKILL.md' and kwargs.get('dir_fd') is not None:
        info = os.stat(path, dir_fd=kwargs['dir_fd'], follow_symlinks=False)
        if stat.S_ISFIFO(info.st_mode):
            fired.append(True)
            print(json.dumps({'fifo_open_fired': True, 'nonblocking': bool(flags & os.O_NONBLOCK)}), flush=True)
    return actual_open(path, flags, *args, **kwargs)
os.open = opening
try:
    tx.rollback(root, sys.argv[3])
except (ValueError, OSError) as exc:
    assert fired, 'actual rollback FIFO boundary did not fire'
    assert 'not regular' in str(exc), repr(exc)
    with tx._lock(root):
        print(json.dumps({'status': 'blocked', 'lock_reacquired_before_process_exit': True}), flush=True)
else:
    raise AssertionError('FIFO substitution was not rejected')
'''
    command = [sys.executable, '-I', '-B', '-c', driver,
               str(Path(__file__).resolve().parents[1] / 'scripts'), str(target), result['transaction'], engine]
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=3)
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f'actual rollback hung at FIFO open; bounded child killed/waited; stdout={exc.stdout!r}')
    assert process.returncode == 0, process.stdout + process.stderr
    events = [json.loads(line) for line in process.stdout.splitlines()]
    assert events[0] == {'fifo_open_fired': True, 'nonblocking': True}
    assert events[-1] == {'status': 'blocked', 'lock_reacquired_before_process_exit': True}
    after = first.lstat()
    assert (after.st_ino, after.st_mode) == (fifo.st_ino, fifo.st_mode)
    assert (target / planner.STATE).read_bytes() == state_before
    assert journal_path.read_bytes() == journal_before
    assert lock.stat().st_ino == lock_inode
