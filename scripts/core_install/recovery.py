"""Explicit absent-owned Grok recovery; never entered by routine sync or repair."""
from __future__ import annotations

import base64
import copy
import os
from pathlib import Path
import stat
import tempfile

from . import discovery, selection_policy, transaction as tx


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


def claim(target, journal, save):
    directories = contract(journal['plan'], target)
    # Check every root before claiming the first. mkdir remains exclusive.
    for root in journal['plan']['recovery_roots']:
        if tx.safe(target, root).exists():
            raise tx.InstallError('recovery root appeared: ' + root, 'recovery-conflict')
    journal['recovery_dirs'] = {}
    journal['recovery_files'] = {}
    journal['recovery_temps'] = {}
    save(target, journal)
    for rel in directories:
        path = tx.safe(target, rel)
        path.mkdir()  # Never accept a root/directory created by someone else.
        tx._sync_dir(path.parent)
        journal['recovery_dirs'][rel] = directory_identity(path)
        save(target, journal)


def check(target, journal, rollback=False):
    """Verify actual created nodes, not only expected content from the plan."""
    directories = contract(journal['plan'], target)
    recorded = journal.get('recovery_dirs', {})
    files = journal.get('recovery_files', {})
    temps = journal.get('recovery_temps', {})
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
    for rel in directories:
        path = tx.safe(target, rel)
        if not path.exists():
            if rel in recorded and not (rollback and restoring):
                raise tx.InstallError('recovery directory disappeared: ' + rel, 'recovery-conflict')
            continue
        if rel not in recorded or directory_identity(path) != recorded[rel]:
            raise tx.InstallError('unowned or changed recovery directory: ' + rel, 'recovery-conflict')
        for child in path.iterdir():
            name = child.relative_to(target).as_posix()
            tx.safe(target, name)
            if name not in recorded and name not in files and name not in temps:
                raise tx.InstallError('unexpected recovery member: ' + name, 'recovery-conflict')
    for rel, ident in {**files, **temps}.items():
        path = tx.safe(target, rel)
        if not path.exists() and rollback and (restoring or rel in temps):
            continue
        if not path.exists() or file_identity(path) != ident:
            raise tx.InstallError('changed recovery file: ' + rel, 'recovery-conflict')
        if rel in files and tx.identity(path) != expected_files[rel]:
            raise tx.InstallError('invalid recovery file identity', 'invalid-journal')
    if not rollback and set(recorded) != set(directories):
        raise tx.InstallError('incomplete recovery directory claims', 'recovery-conflict')


def publish(target, journal, action, data, save):
    """Publish complete bytes with an atomic no-clobber link, never replace."""
    path = tx.safe(target, action['path'])
    fd, temporary = tempfile.mkstemp(prefix='.core-recovery-', dir=path.parent)
    temp = Path(temporary)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(data)
        handle.flush()
        os.fchmod(handle.fileno(), action['after']['mode'])
        os.fsync(handle.fileno())
    rel = temp.relative_to(target).as_posix()
    journal['recovery_temps'][rel] = file_identity(temp)
    save(target, journal)
    check(target, journal)
    os.link(temp, path, follow_symlinks=False)  # EEXIST preserves any new destination.
    journal['recovery_files'][action['path']] = file_identity(path)
    save(target, journal)
    if file_identity(temp) != journal['recovery_temps'][rel]:
        raise tx.InstallError('recovery temporary changed', 'recovery-conflict')
    temp.unlink()
    del journal['recovery_temps'][rel]
    tx._sync_dir(path.parent)
    save(target, journal)


def remove_directories(target, journal):
    for rel, ident in journal.get('recovery_temps', {}).items():
        path = tx.safe(target, rel)
        if path.exists():
            if file_identity(path) != ident:
                raise tx.InstallError('recovery temporary changed', 'recovery-conflict')
            tx._remove(path)
    for rel in sorted(journal.get('recovery_dirs', {}), key=lambda r: (r.count('/'), r), reverse=True):
        path = tx.safe(target, rel)
        if path.exists():
            if directory_identity(path) != journal['recovery_dirs'][rel]:
                raise tx.InstallError('recovery directory changed', 'recovery-conflict')
            path.rmdir()  # Empty, exact, previously journaled directories only.
            tx._sync_dir(path.parent)
