"""Explicit absent-owned Grok recovery; never entered by routine sync or repair."""
from __future__ import annotations

import base64
import copy
import json
import os
import re
import time
from pathlib import Path
import stat
import uuid

from . import discovery, selection_policy, transaction as tx
from .recovery_fs import Session, content_identity, file_bytes


def plan(repo, target, request, current, state, bundle):
    if (set(request) != {'mode', 'providers', 'kinds', 'slugs', 'runtime'}
            or request['providers'] != ['grok'] or request['kinds'] != ['skill']
            or request['runtime'] is not False or not request['slugs']
            or len(set(request['slugs'])) != len(request['slugs'])):
        raise ValueError('INVALID_REQUEST: recovery requires exact Grok skill slugs and no other operation')
    if state is None:
        raise ValueError('RECOVERY_INELIGIBLE: schema2/3 ownership receipt required')
    parent = tx.safe(target, '.grok/skills')
    if not parent.is_dir():
        raise ValueError('RECOVERY_INELIGIBLE: existing safe .grok/skills parent required')
    roots, actions, recovered = [], [], []
    prospective = copy.deepcopy(state)
    for slug in sorted(request['slugs']):
        key = 'grok:skill:' + slug
        package, owned = current.get(key), state['packages'].get(key)
        root = '.grok/skills/' + slug
        if (package is None or key not in state['selection'] or not isinstance(owned, dict)
                or any(owned.get(f) != package[f] for f in ('provider', 'kind', 'slug', 'roots'))
                or package['roots'] != [root] or not isinstance(owned.get('files'), dict)
                or package['entrypoint'] not in owned['files']):
            raise ValueError('RECOVERY_INELIGIBLE: current selected owned package required: ' + slug)
        for rel, ident in owned['files'].items():
            tx.safe(target, rel)
            tx._valid_identity(ident)
            if not rel.startswith(root + '/') or ident is None:
                raise ValueError('RECOVERY_INELIGIBLE: invalid owned package members: ' + slug)
        path = tx.safe(target, root)
        if path.exists():
            raise ValueError('RECOVERY_INELIGIBLE: package root must be wholly absent: ' + root)
        roots.append(root)
        recovered.append(key)
        actions.extend(dict(op='write', path=rel, before=None, after=ident, source=package['sources'][rel])
                       for rel, ident in sorted(package['files'].items()))
        prospective['packages'][key] = {f: package[f] for f in ('provider', 'kind', 'slug', 'roots', 'files')}
    # Clear only the exact recovered packages' previous preservation notices.
    if 'preserved' in prospective:
        prospective['preserved'] = [p for p in prospective['preserved'] if p.get('package') not in recovered]
    content = tx.encoded(prospective)
    before = tx.identity(tx.safe(target, tx.INSTALLATION))
    after = tx._data_identity(content, before['mode'])
    if before != after:
        actions.append(dict(op='write', path=tx.INSTALLATION, before=before, after=after,
                            content=base64.b64encode(content).decode()))
    shared = discovery.shared_root(target)
    blockers = ['SHARED_SURFACE_POLICY_CONFLICT: ' + shared['error']] if shared['status'] == 'error' else []
    return dict(schema=2, repo=str(repo), target=str(target), request=request, selection=state['selection'],
                selection_before=state['selection'], source_files=bundle, state_identity=before,
                recovery_roots=roots, recovered_packages=recovered,
                observations={'.agents/skills': shared, '.grok/skills': directory_identity(parent)},
                policy_before=selection_policy.state_policies(state), policy_after=selection_policy.state_policies(state),
                shared_exposure=dict(root='.agents/skills', supported_readers=['codex', 'gemini'],
                                     known_readers=sorted(set(selection_policy.state_policies(state)) & {'codex', 'gemini'}),
                                     observation_status=shared['status'], entries=shared['entries'],
                                     discovery_verified=False, before_slugs=discovery.slots(shared),
                                     after_slugs=discovery.slots(shared)),
                actions=actions, preserved=[], installation_preserved=prospective.get('preserved', []),
                blockers=blockers, outcomes=[])


def directory_identity(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise tx.InstallError('recovery directory changed: ' + str(path), 'recovery-conflict')
    return dict(device=info.st_dev, inode=info.st_ino, mode=stat.S_IMODE(info.st_mode))


def file_identity(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise tx.InstallError('recovery file changed: ' + str(path), 'recovery-conflict')
    return dict(device=info.st_dev, inode=info.st_ino, **tx.identity(path))


def contract(plan, target):
    roots = plan.get('recovery_roots')
    if roots is None:
        if plan.get('request', {}).get('mode') == 'recover_missing':
            raise tx.InstallError('missing recovery root contract', 'invalid-plan')
        return []
    request = plan.get('request', {})
    if (request.get('mode') != 'recover_missing' or request.get('providers') != ['grok']
            or request.get('kinds') != ['skill'] or request.get('runtime') is not False
            or not isinstance(roots, list) or not roots or roots != sorted(set(roots))
            or roots != sorted('.grok/skills/' + s for s in request.get('slugs', []))):
        raise tx.InstallError('invalid recovery root contract', 'invalid-plan')
    directories = set(roots)
    for root in roots:
        tx.safe(target, root)
        if len(root.split('/')) != 3:
            raise tx.InstallError('invalid recovery root', 'invalid-plan')
    for action in plan['actions']:
        rel = action['path']
        if rel == tx.INSTALLATION and action['op'] == 'write' and action['before'] is not None:
            continue
        if (action['op'] != 'write' or action['before'] is not None
                or not any(rel.startswith(root + '/') for root in roots)):
            raise tx.InstallError('recovery contains unrelated action', 'invalid-plan')
        parent = Path(rel).parent
        while parent.as_posix() not in roots:
            directories.add(parent.as_posix())
            parent = parent.parent
    return sorted(directories, key=lambda r: (r.count('/'), r))



def claim(fs, journal, save):
    directories = contract(journal['plan'], fs.target)
    for root in journal['plan']['recovery_roots']:
        if fs.dir_identity(root) is not None:
            raise tx.InstallError('recovery root appeared: ' + root, 'recovery-conflict')
    journal.update(recovery_dirs={}, recovery_files={}, recovery_temps={})
    save(journal)
    for rel in directories:
        journal['recovery_dirs'][rel] = fs.mkdir(rel)
        save(journal)


def check(fs, journal, rollback=False):
    directories = contract(journal['plan'], fs.target)
    recorded, files, temps = (journal.get(name, {}) for name in ('recovery_dirs', 'recovery_files', 'recovery_temps'))
    if (not isinstance(recorded, dict) or not isinstance(files, dict) or not isinstance(temps, dict)
            or set(recorded) - set(directories)):
        raise tx.InstallError('invalid recovery journal', 'invalid-journal')
    expected_files = {a['path']: a['after'] for a in journal['plan']['actions'] if a['path'] != tx.INSTALLATION}
    if set(files) - set(expected_files):
        raise tx.InstallError('invalid recovery file record', 'invalid-journal')
    for rel in temps:
        if (not any(rel.startswith(r + '/') for r in journal['plan']['recovery_roots'])
                or not Path(rel).name.startswith('.core-recovery-')):
            raise tx.InstallError('invalid recovery temporary record', 'invalid-journal')
    restoring = journal.get('restoring', False) or journal['status'] == 'rolled-back'
    for rel, ident in recorded.items():
        fs.expect_directory(rel, ident)
    for rel in directories:
        current = fs.dir_identity(rel)
        if current is None:
            if rel in recorded and not (rollback and restoring):
                raise tx.InstallError('recovery directory disappeared: ' + rel, 'recovery-conflict')
            continue
        if rel not in recorded or current != recorded[rel]:
            raise tx.InstallError('unowned or changed recovery directory: ' + rel, 'recovery-conflict')
        for name in fs.names(rel):
            child = rel + '/' + name
            if child not in recorded and child not in files and child not in temps:
                raise tx.InstallError('unexpected recovery member: ' + child, 'recovery-conflict')
    for rel, ident in {**files, **temps}.items():
        current = fs.identity(rel)
        if current is None and rollback and (restoring or rel in temps):
            continue
        if current is None or current != ident:
            raise tx.InstallError('changed recovery file: ' + rel, 'recovery-conflict')
        if rel in files and content_identity(current) != expected_files[rel]:
            raise tx.InstallError('invalid recovery file identity', 'invalid-journal')
    if not rollback and set(recorded) != set(directories):
        raise tx.InstallError('incomplete recovery directory claims', 'recovery-conflict')


def publish(fs, journal, action, data, save):
    with fs.parent(action['path']) as (parent, name):
        with fs.temporary(parent, data, action['after']['mode'], '.core-recovery-') as (temp, fd, original):
            rel = str(Path(action['path']).parent / temp)
            os.fsync(parent)
            fs.match_named(parent, temp, original)
            journal['recovery_temps'][rel] = original
            save(journal)
            check(fs, journal)
            fs.match_named(parent, temp, original)
            os.link(temp, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            fs.match_named(parent, temp, original)
            fs.match_named(parent, name, original)
            if file_bytes(fd)[1] != original:
                raise tx.InstallError('original publication descriptor changed', 'recovery-conflict')
            os.fsync(parent)
            fs.match_named(parent, temp, original)
            fs.match_named(parent, name, original)
            if file_bytes(fd)[1] != original:
                raise tx.InstallError('original publication descriptor changed', 'recovery-conflict')
            journal['recovery_files'][action['path']] = original
            save(journal)
            fs.match_named(parent, temp, original)
            os.unlink(temp, dir_fd=parent)
            os.fsync(parent)
            del journal['recovery_temps'][rel]
            save(journal)


def remove_directories(fs, journal):
    for rel, ident in journal.get('recovery_temps', {}).items():
        if fs.identity(rel) is not None:
            fs.unlink(rel, ident)
    for rel in sorted(journal.get('recovery_dirs', {}), key=lambda r: (r.count('/'), r), reverse=True):
        if fs.dir_identity(rel) is not None:
            fs.rmdir(rel, journal['recovery_dirs'][rel])


def load_journal(fs, transaction):
    # Validate the transaction basename without using it as an unchecked path.
    if not isinstance(transaction, str) or re.fullmatch(r'[0-9a-f]{32}', transaction) is None:
        raise tx.InstallError('invalid transaction id', 'invalid-transaction')
    rel = f'{tx.TRANSACTIONS}/{transaction}/journal.json'
    data, ident = fs.read(rel)
    journal = json.loads(data)
    if (not isinstance(journal, dict) or journal.get('schema') not in (1, 2, 3)
            or journal.get('transaction') != transaction or type(journal.get('created_ns')) is not int
            or type(journal.get('restoring', False)) is not bool
            or journal.get('status') not in ('prepared', 'applying', 'complete', 'rolled-back')):
        raise tx.InstallError('invalid transaction journal', 'invalid-journal')
    tx._actions(journal.get('plan'), fs.target)
    if (journal['schema'] == 2) != bool(journal['plan'].get('recovery_roots')):
        raise tx.InstallError('journal schema does not match recovery contract', 'invalid-journal')
    if (journal['schema'] == 3) != bool(journal['plan'].get('replacement_packages')):
        raise tx.InstallError('journal schema does not match replacement contract', 'invalid-journal')
    prior_identity = fs.journal_expected.get(rel)
    if prior_identity is not None and prior_identity != ident:
        raise tx.InstallError("journal identity changed during recovery", "stale-journal")
    fs.journal_expected[rel] = ident
    return journal


def journals(fs):
    if fs.dir_identity(tx.TRANSACTIONS) is None:
        return []
    return [load_journal(fs, name) for name in fs.names(tx.TRANSACTIONS)]


def apply(repo, target, approved, replan):
    approved = json.loads(tx.encoded(approved))
    transaction = None
    with Session(target) as fs:
        fs.lock()
        if any(j['status'] in ('prepared', 'applying') for j in journals(fs)):
            raise tx.InstallError('unfinished transaction requires rollback', 'unfinished-transaction')
        actions = tx._actions(approved, target, repo)
        if approved.get('blockers'):
            raise tx.InstallError('approved plan contains unresolved blockers', 'blocked-plan')
        if tx.encoded(replan()) != tx.encoded(approved):
            raise tx.InstallError('stale approved plan: replan differs', 'stale-plan')
        preimages, postimages, preidentities = {}, {}, {}
        for index, action in enumerate(actions):
            current = fs.identity(action['path'])
            if content_identity(current) != action['before']:
                raise tx.InstallError('target drift: ' + action['path'], 'stale-target')
            preidentities[action['path']] = current
            if current is not None:
                data, actual = fs.read(action['path'])
                if actual != current:
                    raise tx.InstallError('target changed while reading preimage', 'stale-target')
                preimages[index] = data
            postimages[index] = tx._source(repo, action)
        transaction = uuid.uuid4().hex
        directory = f'{tx.TRANSACTIONS}/{transaction}'
        journal = dict(schema=2, transaction=transaction, status='prepared', created_ns=time.time_ns(), plan=approved)
        try:
            fs.mkdir(tx.TRANSACTIONS, common=True)
            if any(j["status"] in ("prepared", "applying") for j in journals(fs)):
                raise tx.InstallError("unfinished transaction requires rollback", "unfinished-transaction")
            fs.mkdir(directory)
            fs.save(journal)
            for kind, images in (('before', preimages), ('after', postimages)):
                fs.mkdir(directory + '/' + kind)
                for index, data in images.items():
                    fs.atomic(f'{directory}/{kind}/{index}', data, actions[index][kind]['mode'])
            journal['status'] = 'applying'
            fs.save(journal)
            claim(fs, journal, fs.save)
            for index, action in tx._order(actions):
                check(fs, journal)
                if fs.identity(action['path']) != preidentities[action['path']]:
                    raise tx.InstallError('target drift during recovery: ' + action['path'], 'stale-target')
                data, staged = fs.read(f'{directory}/after/{index}')
                if content_identity(staged) != action['after']:
                    raise tx.InstallError('staged postimage changed', 'invalid-stage')
                if action['path'] == tx.INSTALLATION:
                    fs.atomic(action['path'], data, action['after']['mode'], preidentities[action['path']])
                else:
                    publish(fs, journal, action, data, fs.save)
                if content_identity(fs.identity(action['path'])) != action['after']:
                    raise tx.InstallError('recovery write verification failed', 'verification-failed')
            check(fs, journal)
            journal['status'] = 'complete'
            fs.save(journal)
            return {**tx._receipt(journal), 'preserved': [], 'retention_candidates': []}
        except Exception as exc:
            raise tx.InstallError(f'installation failed; recoverable transaction {transaction}; '
                                  f'journal save outcome={fs.last_save_outcome}: {exc}', 'apply-failed', transaction) from exc


def rollback(target, transaction, dry_run, hint):
    with Session(target) as fs:
        before_lock = load_journal(fs, transaction)
        if before_lock != hint or before_lock['schema'] != 2:
            raise tx.InstallError('rollback classification changed', 'stale-journal')
        fs.lock()
        journal = load_journal(fs, transaction)
        if journal != before_lock or journal['schema'] != 2:
            raise tx.InstallError('rollback classification changed', 'stale-journal')
        if any(j['transaction'] != transaction and j['status'] in ('prepared', 'applying') for j in journals(fs)):
            raise tx.InstallError('another unfinished transaction requires rollback first', 'unfinished-transaction')
        check(fs, journal, rollback=True)
        directory = f'{tx.TRANSACTIONS}/{transaction}'
        restore = []
        for index, action in tx._order(journal['plan']['actions']):
            current = fs.identity(action['path'])
            expected = [action['after']] if journal['status'] == 'complete' and not journal.get('restoring') else [action['before'], action['after']]
            if journal['status'] == 'rolled-back':
                expected = [action['before']]
            if content_identity(current) not in expected:
                raise tx.InstallError('rollback conflict: ' + action['path'], 'rollback-conflict', transaction)
            data = None
            if content_identity(current) != action['before'] and action['before'] is not None:
                data, backup = fs.read(f'{directory}/before/{index}')
                if content_identity(backup) != action['before']:
                    raise tx.InstallError('missing or corrupt backup', 'invalid-backup', transaction)
            restore.append((action, current, data))
        if dry_run:
            return {**tx._receipt(journal), 'status': 'rollback-ready'}
        if journal['status'] == 'rolled-back':
            return tx._receipt(journal)
        try:
            journal.update(status='applying', restoring=True)
            fs.save(journal)
            # Preserve package action ordering; restore the receipt only after
            # namespace removals are durable, before the final journal fact.
            for action, current, data in restore:
                if action['path'] == tx.INSTALLATION:
                    continue
                check(fs, journal, rollback=True)
                if fs.identity(action['path']) != current:
                    raise tx.InstallError('rollback conflict during restore', 'rollback-conflict')
                if current is not None:
                    fs.unlink(action['path'], current)
            remove_directories(fs, journal)
            for action, current, data in restore:
                if action['path'] == tx.INSTALLATION and data is not None:
                    fs.atomic(action['path'], data, action['before']['mode'], current)
            journal['status'] = 'rolled-back'
            fs.save(journal)
            return tx._receipt(journal)
        except Exception as exc:
            raise tx.InstallError(f'rollback failed; recoverable transaction {transaction}; '
                                  f'journal save outcome={fs.last_save_outcome}: {exc}', 'rollback-failed', transaction) from exc
