"""Explicit, manifest-bound adoption of unowned current Claude skill roots.

The ordinary installer never infers this authority. Empty directories are kept,
as in the existing file transaction engine; their modes and membership are bound.
"""
from __future__ import annotations

import base64
import copy
import os
import stat
import unicodedata
from pathlib import Path

from . import providers, transaction as tx


def snapshot(base, root):
    path = tx.safe(base, root)
    if not path.is_dir():
        raise ValueError('REPLACEMENT_CONFLICT: package root must be an existing directory: ' + root)
    directories = {root: stat.S_IMODE(path.stat().st_mode)}
    aliases = set()
    for directory, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            rel = (Path(directory) / name).relative_to(base).as_posix()
            checked = tx.safe(base, rel)
            alias = unicodedata.normalize('NFC', rel).casefold()
            if alias in aliases:
                raise ValueError('REPLACEMENT_CONFLICT: ambiguous member: ' + rel)
            aliases.add(alias)
            if checked.is_dir():
                mode = stat.S_IMODE(checked.stat().st_mode)
                if mode > 0o777:
                    raise ValueError('REPLACEMENT_CONFLICT: special directory mode: ' + rel)
                directories[rel] = mode
            else:
                tx._valid_identity(tx.identity(checked))
    if directories[root] > 0o777:
        raise ValueError('REPLACEMENT_CONFLICT: special root mode')
    return dict(files=tx.inventory(base, [root]), directories=dict(sorted(directories.items())))


def plan(repo, target, request, current, state, bundle):
    if set(request) != {'mode', 'manifest'}:
        raise ValueError('INVALID_REQUEST: replacement accepts only its exact manifest')
    manifest = request['manifest']
    if (not isinstance(manifest, dict) or set(manifest) != {'schema', 'target', 'packages'}
            or manifest['schema'] != 1 or manifest['target'] != str(target)
            or not isinstance(manifest['packages'], dict) or not manifest['packages']):
        raise ValueError('INVALID_REPLACEMENT: expected schema1 target and exact packages')
    # Do not silently convert older ownership/profile formats in this operation.
    from . import planner
    if state is None and (tx.safe(target, planner.V1_PROFILE).exists() or tx.safe(target, planner.V1_RECEIPT).exists()):
        raise ValueError('INVALID_REPLACEMENT: reconcile the legacy profile first')
    previous = state or dict(schema=2, owner='Core-Prompts', selection=[], packages={}, runtime={}, registrations={}, preserved=[])
    prospective = copy.deepcopy(previous)
    packages, actions = {}, []
    for key, approved in sorted(manifest['packages'].items()):
        desired = current.get(key)
        if (desired is None or desired['provider'] != 'claude' or desired['kind'] != 'skill'
                or not isinstance(approved, dict) or set(approved) != {'root', 'before', 'after'}
                or desired['roots'] != [approved['root']]):
            raise ValueError('INVALID_REPLACEMENT: exact current Claude skill required: ' + key)
        root = approved['root']
        for owned in previous['packages'].values():
            if key in previous['packages'] or any(r == root or r.startswith(root + '/') or root.startswith(r + '/') for r in owned['roots']):
                raise ValueError('INVALID_REPLACEMENT: package is already owned: ' + key)
        before, after = snapshot(target, root), snapshot(repo, root)
        if before != approved['before'] or not before['files'] or root + '/SKILL.md' not in before['files']:
            raise ValueError('REPLACEMENT_CONFLICT: before-image changed or incomplete: ' + root)
        if after != approved['after'] or after['files'] != desired['files']:
            raise ValueError('REPLACEMENT_CONFLICT: after-image differs from current package: ' + root)
        # File/directory type transitions need a separate reviewed migration.
        if set(before['files']) & set(after['directories']) or set(after['files']) & set(before['directories']):
            raise ValueError('REPLACEMENT_CONFLICT: file/directory transition: ' + root)
        packages[key] = dict(root=root, before=before, after=after)
        # Include identical files so the journal holds the FULL before-image.
        for rel, identity in after['files'].items():
            actions.append(dict(op='write', path=rel, before=before['files'].get(rel), after=identity, source=desired['sources'][rel]))
        for rel, identity in before['files'].items():
            if rel not in after['files']:
                actions.append(dict(op='remove', path=rel, before=identity, after=None))
        prospective['packages'][key] = {field: desired[field] for field in ('provider', 'kind', 'slug', 'roots', 'files')}
    # A preserved agent must not lose a referenced old package resource.
    agent_observations = {}
    roots = [(f'.{p}/agents', False) for p in providers.AGENT_EXTENSIONS]
    roots.append(('.gemini/config/agents', True))
    plugin_root = tx.safe(target, '.gemini/config/plugins')
    if plugin_root.is_dir():
        for plugin in sorted(plugin_root.iterdir()):
            plugin = tx.safe(target, plugin.relative_to(target).as_posix())
            if plugin.is_dir():
                roots.append(((plugin / 'agents').relative_to(target).as_posix(), True))
    for relative, recursive in roots:
        directory = tx.safe(target, relative)
        if not directory.is_dir():
            continue
        definitions = []
        for entry in (directory.rglob('*') if recursive else directory.iterdir()):
            # Inspect every encountered entry before type/suffix filtering. A
            # directory link can hide a preserved agent dependency; never follow it.
            entry = tx.safe(target, entry.relative_to(target).as_posix())
            if entry.suffix in ('.json', '.toml', '.md', '.yaml', '.yml') and not entry.is_dir():
                definitions.append(entry)
        definitions.sort()
        if len(definitions) > 1000:
            raise ValueError('REPLACEMENT_CONFLICT: more than 1000 agent definitions')
        for definition in definitions:
            rel = definition.relative_to(target).as_posix()
            definition = tx.safe(target, rel)
            agent_observations[rel] = tx.identity(definition)
            content = definition.read_text()
            for package in packages.values():
                removed = set(package['before']['files']) - set(package['after']['files'])
                if removed and providers.references_removed_files(content, rel, target, removed):
                    raise ValueError('REPLACEMENT_CONFLICT: preserved agent depends on removed files: ' + rel)
    prospective['selection'] = sorted(set(previous['selection']) | set(packages))
    prospective['preserved'] = [p for p in previous.get('preserved', []) if p.get('package') not in packages]
    content = tx.encoded(prospective)
    state_before = tx.identity(tx.safe(target, tx.INSTALLATION))
    actions.append(dict(op='write', path=tx.INSTALLATION, before=state_before,
                        after=tx._data_identity(content, state_before['mode'] if state_before else 0o644), content=base64.b64encode(content).decode()))
    return dict(schema=2, repo=str(repo), target=str(target), request=request, actions=actions,
                replacement_packages=packages, source_files=bundle, agent_observations=agent_observations, blockers=[], preserved=[],
                selection=prospective['selection'], outcomes=[dict(package=k, status='explicit-unowned-replacement') for k in packages])


def contract(plan):
    packages = plan.get('replacement_packages')
    mode = plan.get('request', {}).get('mode')
    if packages is None and mode != 'replace_unowned':
        return
    if mode != 'replace_unowned' or packages != plan['request'].get('manifest', {}).get('packages') or not packages:
        raise tx.InstallError('invalid replacement contract', 'invalid-plan')
    expected = {tx.INSTALLATION}
    actions = {a['path']: a for a in plan['actions']}
    for key, package in packages.items():
        root = package['root']
        if key != 'claude:skill:' + root.removeprefix('.claude/skills/') or root.split('/')[:2] != ['.claude', 'skills'] or len(root.split('/')) != 3:
            raise tx.InstallError('invalid replacement root', 'invalid-plan')
        for side in ('before', 'after'):
            image = package[side]
            if set(image) != {'files', 'directories'} or root not in image['directories']:
                raise tx.InstallError('invalid replacement snapshot', 'invalid-plan')
            for rel, mode in image['directories'].items():
                if (rel != root and not rel.startswith(root + '/')) or type(mode) is not int or not 0 <= mode <= 0o777:
                    raise tx.InstallError('invalid replacement directory', 'invalid-plan')
            for rel in package[side]['files']:
                if not rel.startswith(root + '/'):
                    raise tx.InstallError('unlisted replacement path', 'invalid-plan')
            expected.update(package[side]['files'])
        for rel in set(package['before']['files']) | set(package['after']['files']):
            action = actions.get(rel, {})
            after = package['after']['files'].get(rel)
            if (action.get('before') != package['before']['files'].get(rel) or action.get('after') != after
                    or action.get('op') != ('write' if after else 'remove')
                    or after and action.get('source') != rel):
                raise tx.InstallError('replacement action differs from manifest', 'invalid-plan')
    if {a['path'] for a in plan['actions']} != expected:
        raise tx.InstallError('replacement actions differ from complete manifest', 'invalid-plan')


def check(target, plan, phase='before', partial=False):
    """Guard whole membership, including empty directories and later extras."""
    for package in plan.get('replacement_packages', {}).values():
        live = snapshot(target, package['root'])
        before, after = package['before'], package['after']
        directories = {**after['directories'], **before['directories']}
        expected_dirs = before['directories'] if phase == 'before' and not partial else directories
        if partial:
            if (not set(before['directories']) <= set(live['directories']) <= set(directories)
                    or any(directories.get(r) != m for r, m in live['directories'].items())):
                raise tx.InstallError('replacement directory drift', 'replacement-conflict')
            allowed = set(before['files']) | set(after['files'])
            if set(live['files']) - allowed:
                raise tx.InstallError('replacement has unlisted files', 'replacement-conflict')
            for rel in allowed:
                if live['files'].get(rel) not in (before['files'].get(rel), after['files'].get(rel)):
                    raise tx.InstallError('replacement member drift: ' + rel, 'replacement-conflict')
        elif live != dict(files=(before if phase == 'before' else after)['files'], directories=expected_dirs):
            raise tx.InstallError('replacement package drift: ' + package['root'], 'replacement-conflict')


def prepare_directories(target, plan):
    # Called after preimages are durable; old directory modes remain untouched.
    for package in plan.get('replacement_packages', {}).values():
        for rel, mode in sorted(package['after']['directories'].items(), key=lambda item: (item[0].count('/'), item[0])):
            path = tx.safe(target, rel)
            if rel not in package['before']['directories']:
                path.mkdir(mode=mode)
                path.chmod(mode)
