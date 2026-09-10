"""Read-only installation reconciliation. Every decision retains package identity."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import install_bundle
from . import catalog, providers
from .transaction import encoded, identity, inventory, safe

STATE = '.core-prompts-state/installation.json'
V1_PROFILE = '.core-prompts-state/profile-install/profile.json'
V1_RECEIPT = '.core-prompts-state/profile-install/ownership.json'
LAUNCHER = b'''#!/usr/bin/env bash
set -euo pipefail
SUPPORT_ROOT="${CORE_PROMPTS_SUPPORT_ROOT:-$HOME/.core-prompts-updater}"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  runner="$PYTHON_BIN"
elif command -v python3.14 >/dev/null 2>&1; then
  runner=python3.14
else
  runner=python3
fi
exec "$runner" "$SUPPORT_ROOT/scripts/update-core-prompts.py" "$@"
'''


def byte_identity(data, mode=0o644):
    return {'sha256': hashlib.sha256(data).hexdigest(), 'mode': mode}


def read_json(root, rel):
    path = safe(root, rel)
    return json.loads(path.read_text()) if path.exists() else None


def read_state(target):
    state = read_json(target, STATE)
    if safe(target, STATE).exists() and (not isinstance(state, dict) or state.get('schema') != 2
                              or state.get('owner') != 'Core-Prompts'
                              or not isinstance(state.get('selection'), list)
                              or not isinstance(state.get('packages'), dict)
                              or not isinstance(state.get('runtime'), dict)):
        raise ValueError('INVALID_STATE: unrecognized installation ownership')
    return state


def _profile_selection(profile, current):
    if not isinstance(profile,dict) or profile.get('schema') != 1 or profile.get('scope') != 'skills':
        raise ValueError('INVALID_PROFILE: expected schema1 skills profile')
    clients = profile.get('targets', [])
    if not isinstance(clients,list) or not clients or not all(isinstance(v,str) for v in clients) or len(clients) != len(set(clients)) or set(clients) - set(providers.PROVIDERS):
        raise ValueError('INVALID_PROFILE: unique supported targets required')
    slugs = profile.get('slugs', [])
    if not isinstance(slugs,list) or not all(isinstance(s,str) and s for s in slugs):
        raise ValueError('INVALID_PROFILE: slugs must be an array of names')
    names = {p['slug'] for p in current.values()}
    mapped = [catalog.SUCCESSORS.get(s, s) for s in slugs]
    if set(mapped) - names - {None}:
        raise ValueError('INVALID_PROFILE: unknown slug')
    return {k for k, p in current.items() if p['kind'] == 'skill' and p['provider'] in clients
            and (not slugs or p['slug'] in mapped)}


def _observe(target, roots, observations):
    signature = '|'.join(roots)
    try:
        files = inventory(target, roots)
        observations[signature] = {'roots': roots, 'files': files}
        return files, None
    except (ValueError, OSError) as exc:
        observations[signature] = {'roots': roots, 'error': str(exc)}
        return {}, str(exc)


def plan(repo: Path, target: Path, request: dict):
    """Create a deterministic, hash-bound proposal; never write to the target.

    mode=repair authorizes recognition/adoption within requested providers;
    mode=sync keeps saved scope; mode=install explicitly selects current source
    packages. A v1 profile's skill selection always survives conversion.
    """
    repo, target = repo.absolute(), target.absolute()
    if not isinstance(request,dict):
        raise ValueError('INVALID_REQUEST: object required')
    for field in ('providers','kinds','slugs','legacy_slugs'):
        if field in request and (not isinstance(request[field],list) or not all(isinstance(v,str) and v for v in request[field])):
            raise ValueError(f'INVALID_REQUEST: {field} must be an array of names')
    if 'runtime' in request and type(request['runtime']) is not bool:
        raise ValueError('INVALID_REQUEST: runtime must be boolean')
    safe(target, STATE)
    if repo.resolve() == target.resolve():
        raise ValueError('INVALID_TARGET: build repository surfaces instead')
    mode = request.get('mode', 'repair')
    if mode not in ('install', 'repair', 'sync'):
        raise ValueError('INVALID_REQUEST: unknown installation mode')
    bundle = install_bundle.verified(repo)
    trusted = catalog.load_catalog(repo)
    manifest = read_json(repo, '.meta/manifest.json')
    current = providers.current_packages(repo, manifest, identity, safe)
    state = read_state(target)
    previous = state or dict(schema=2, owner='Core-Prompts', selection=[], packages={}, runtime={}, registrations={})
    profile = request['profile'] if 'profile' in request else (read_json(target, V1_PROFILE) if state is None else None)
    profile_present = 'profile' in request or (state is None and safe(target,V1_PROFILE).exists())
    if profile_present:
        _profile_selection(profile,current)
    if mode == 'sync' and state is None and profile is None:
        # Legacy full installs never had a profile. Their first new-runtime sync
        # discovers independently recognized packages instead of doing nothing.
        mode = 'repair'
    old_receipt = read_json(target, V1_RECEIPT) if state is None else None
    if state is None and safe(target,V1_RECEIPT).exists() and not isinstance(old_receipt,dict):
        raise ValueError('INVALID_STATE: invalid prior profile receipt')
    if old_receipt is not None:
        if old_receipt.get('schema') != 1 or old_receipt.get('owner') != 'Core-Prompts':
            raise ValueError('INVALID_STATE: invalid prior profile receipt')
        # The actual saved profile (not a caller-supplied replacement) is bound.
        saved_profile = read_json(target, V1_PROFILE)
        if saved_profile is None or hashlib.sha256(encoded(saved_profile)).hexdigest() != old_receipt.get('approved_profile_sha256'):
            raise ValueError('INVALID_STATE: saved profile and ownership differ')
    clients = request['providers'] if 'providers' in request else (profile.get('targets') if profile else None)
    if clients is None:
        clients = sorted({k.split(':')[0] for k in previous['selection']}) if state else list(providers.PROVIDERS)
    if not isinstance(clients, list) or len(clients) != len(set(clients)) or set(clients) - set(providers.PROVIDERS):
        raise ValueError('INVALID_REQUEST: unknown or repeated provider')
    def in_scope(provider,kind,slug,old_slug=None):
        if provider not in clients:
            return False
        if request.get('legacy_slugs'):
            return old_slug in request['legacy_slugs']
        if request.get('slugs') and slug not in request['slugs']:
            return False
        return not request.get('kinds') or kind in request['kinds']
    selection = set(previous['selection'])
    profile_selection = _profile_selection(profile, current) if profile else None
    if profile:
        selection |= profile_selection
    missing_selected = selection - set(current)
    # Explicitly retired identities disappear only under a catalog retirement.
    if missing_selected:
        raise ValueError('SOURCE_SCOPE_REMOVED: ' + ', '.join(sorted(missing_selected)))
    observations, preserved, blockers, actions, outcomes = {}, [], [], [], []
    discovered, inventories = {}, {}
    specs = list(catalog.packages(trusted))
    # Current names matter for inspection, but current bytes alone do not prove
    # historical ownership. Initial adoption requires trusted history or receipt.
    candidates = {}
    for raw in specs:
        if raw['kind'] == 'agent':
            raw = dict(raw, roots=[raw['roots'][0], f'.{raw["provider"]}/agents/resources/{raw["slug"]}'])
        for spec in providers.codex_layouts(raw):
            if spec['provider'] not in clients:
                continue
            signature = (spec['provider'], spec['kind'], spec['slug'], tuple(spec['roots']))
            candidates.setdefault(signature, []).append(spec)
    for k, p in current.items():
        if p['provider'] in clients:
            signature = (p['provider'], p['kind'], p['slug'], tuple(p['roots']))
            candidates.setdefault(signature, [])
    present_keys = set()
    assessed_keys = set()
    for (provider, kind, slug, roots), variants in sorted(candidates.items()):
        files, error = _observe(target, list(roots), observations)
        if not files and not error:
            continue
        k = providers.key(provider, kind, slug)
        present_keys.add(k)
        known = next((v for v in variants if files == v['files']), None) if not error else None
        owned = previous['packages'].get(k)
        if owned and list(roots) == owned.get('roots') and files == owned.get('files') and not error:
            known = dict(owned, provider=provider, kind=kind, slug=slug,
                         successor=catalog.SUCCESSORS.get(slug, slug), releases=['ownership-receipt'])
        if old_receipt and not error and files and all(old_receipt.get('files', {}).get(r, {}).get('identity') == i for r, i in files.items()):
            # v1 only owned skills. It cannot assert agent ownership indirectly.
            if kind == 'skill':
                known = dict(provider=provider,kind=kind,slug=slug,roots=list(roots),files=files,
                             successor=catalog.SUCCESSORS.get(slug,slug),releases=['schema1-receipt'])
        successor = catalog.SUCCESSORS.get(slug, slug)
        newkey = providers.key(provider,kind,successor) if successor else None
        eligible = mode != 'sync' or newkey in selection
        eligible = eligible and in_scope(provider,kind,successor,slug)
        if profile_selection is not None and kind == 'skill' and newkey not in profile_selection:
            eligible = False
        if eligible:
            assessed_keys.add(newkey or k)
        if known and eligible:
            record = dict(known, roots=list(roots), files=files)
            discovered.setdefault(newkey or k, []).append(record)
            if newkey:
                selection.add(newkey)
        elif not known and eligible:
            preserved.append(dict(package=newkey or k,provider=provider,kind=kind,slug=slug,roots=list(roots),
                                  reason=error or 'unrecognized, partial, or customized package'))
        inventories[tuple(roots)] = files
    if mode == 'install':
        kinds = request.get('kinds', ['skill'])
        if not isinstance(kinds,list) or set(kinds) - {'skill','agent'}:
            raise ValueError('INVALID_REQUEST: unknown package kind')
        slugs = request.get('slugs', [])
        if set(slugs) - {p['slug'] for p in current.values()}:
            raise ValueError('INVALID_REQUEST: unknown requested slug')
        selection |= {k for k,p in current.items() if p['provider'] in clients and p['kind'] in kinds
                      and (not slugs or p['slug'] in slugs)}
    if not state and not profile and not present_keys and mode == 'repair':
        # Rerunning the installer is also the fresh-install entry point. Provider
        # availability is resolved by the CLI; callers must give fresh targets.
        if not request.get('providers'):
            raise ValueError('NO_INSTALLATION: select providers for a fresh installation')
        selection |= {k for k,p in current.items() if p['provider'] in clients and p['kind'] in request.get('kinds',['skill'])}
    next_packages = dict(previous['packages'])
    package_actions, blocked_keys, to_retire = {}, set(), {}
    for k in sorted(selection | set(discovered)):
        sources = discovered.get(k, [])
        desired = current.get(k)
        if desired is None:
            # Only explicit catalog retirement may have no successor.
            if sources and all(s['successor'] is None for s in sources):
                to_retire[k] = sources
                package_actions[k] = []
            continue
        if not in_scope(desired['provider'],desired['kind'],desired['slug']):
            continue
        assessed_keys.add(k)
        files, error = _observe(target, desired['roots'], observations)
        owned = previous['packages'].get(k)
        source_match = next((s for s in sources if s['roots'] == desired['roots'] and s['files'] == files), None)
        receipt_match = old_receipt and files and all(old_receipt.get('files',{}).get(r,{}).get('identity') == v for r,v in files.items())
        if error or (files and not source_match and not (owned and files == owned.get('files')) and not receipt_match):
            blocked_keys.add(k)
            preserved.append(dict(package=k,provider=desired['provider'],kind=desired['kind'],slug=desired['slug'],roots=desired['roots'],reason=error or 'successor is unowned or customized; predecessor retained'))
            continue
        if owned and not files:
            blocked_keys.add(k)
            preserved.append(dict(package=k,provider=desired['provider'],kind=desired['kind'],slug=desired['slug'],roots=desired['roots'],reason='owned package is missing; repair explicitly before updating'))
            continue
        proposed = []
        for rel, after in sorted(desired['files'].items()):
            before = files.get(rel)
            if before != after:
                proposed.append(dict(op='write',path=rel,before=before,after=after,source=desired['sources'][rel]))
        # Retiring obsolete owned resources is a package migration, not a
        # recursive directory deletion. Unexpected members above block it.
        for rel, before in sorted(files.items()):
            if rel not in desired['files']:
                proposed.append(dict(op='remove',path=rel,before=before,after=None))
        package_actions[k] = proposed
        to_retire[k] = [s for s in sources if s['roots'] != desired['roots']]
        next_packages[k] = {n:desired[n] for n in ('provider','kind','slug','roots','files')}

    # Dependency closure is checked before the first action is accepted. Also
    # capture custom agent definitions: changing one after preview stales plan.
    agent_observations = {}
    dependent_retirements = []
    replacing_agents = {rel:k for k, sources in discovered.items()
                        if k in package_actions and k not in blocked_keys
                        for source in sources if source['kind']=='agent'
                        for rel in source['files'] if '/agents/resources/' not in rel}
    for provider in providers.AGENT_EXTENSIONS:
        root = safe(target, f'.{provider}/agents')
        if not root.is_dir():
            continue
        files = sorted(p for p in root.iterdir() if p.suffix in ('.json','.toml','.md'))
        if len(files) > 1000:
            blockers.append('DISCOVERY_LIMIT: more than 1000 agent definitions')
            continue
        for p in files:
            rel = p.relative_to(target).as_posix()
            try:
                p = safe(target,rel)
                agent_observations[rel] = identity(p)
                content = p.read_text()
            except (OSError,ValueError,UnicodeError) as exc:
                blockers.append(f'AGENT_DISCOVERY: {rel}: {exc}')
                continue
            retire_sets = {k:list(v) for k,v in to_retire.items()}
            for k, proposed in package_actions.items():
                removed={a['path']:a['before'] for a in proposed if a['op']=='remove'}
                if removed and k in current:
                    retire_sets.setdefault(k,[]).append(dict(current[k],files=removed))
            for k, old_specs in retire_sets.items():
                if k in blocked_keys:
                    continue
                for old in old_specs:
                    # Exact old resource/path dependency in any other agent is
                    # conservatively preserved, not rewritten by text replace.
                    replacement = current[k]['files'] if k in current and old['roots'] != current[k]['roots'] else ()
                    if providers.references_removed_files(content,rel,target,old['files'],replacement):
                        if rel in replacing_agents:
                            dependent_retirements.append((k,replacing_agents[rel],rel))
                            continue
                        own_agent = next((ak for ak,ap in current.items() if ap['kind']=='agent' and ap['entrypoint']==rel and ak in package_actions),None)
                        if own_agent and own_agent not in blocked_keys:
                            continue
                        blocked_keys.add(k)
                        preserved.append(dict(package=k,slug=old['slug'],provider=old['provider'],kind=old['kind'],roots=old['roots'],reason=f'preserved agent depends on legacy files: {rel}'))
    dependency_edges = []
    changed = True
    while changed:
        changed = False
        for dependent, owner, rel in dependent_retirements:
            if owner in blocked_keys and dependent not in blocked_keys:
                blocked_keys.add(dependent); changed = True
                preserved.append(dict(package=dependent,roots=[rel],reason='preserved agent requires legacy files'))
        for k in sorted(package_actions):
            if k in blocked_keys or k not in current:
                continue
            p = current[k]
            for dep in providers.agent_skill_dependencies(p,repo):
                dk = next((x for x,q in current.items() if dep in q['files']), None)
                if dk is not None:
                    dependency_edges.append((k,dk,dep))
                available = dk in package_actions and dk not in blocked_keys
                if not available and dk is not None and dk not in blocked_keys:
                    observed,error = _observe(target,current[dk]['roots'],observations)
                    available = error is None and observed == current[dk]['files']
                if not available:
                    blocked_keys.add(k); changed = True
                    preserved.append(dict(package=k,provider=p['provider'],kind=p['kind'],slug=p['slug'],roots=p['roots'],reason=f'missing or preserved skill dependency: {dep}'))

    # Registrations are proposed as bytes and are guarded with their agent.
    codex_add, codex_remove = {}, {}
    codex_keys = set()
    for k in package_actions:
        if k in blocked_keys:
            continue
        p = current.get(k)
        if p and p['provider']=='codex' and p['kind']=='agent':
            codex_add[p['slug']] = p['entrypoint']; codex_keys.add(k)
        for old in to_retire.get(k,[]):
            if old['provider']=='codex' and old['kind']=='agent':
                codex_remove[old['slug']] = f'.codex/agents/{old["slug"]}.toml'; codex_keys.add(k)
    registrations = dict(previous.get('registrations',{}))
    if codex_add or codex_remove:
        rel='.codex/config.toml'
        try:
            path=safe(target,rel); before=identity(path)
            content=path.read_bytes() if before else b''
            updated, registrations, conflicts = providers.registration_patch(content,target,codex_add,codex_remove,registrations)
            observations['registration']={'roots':[rel],'files':{rel:before} if before else {}}
            if conflicts:
                blocked_keys |= codex_keys
                preserved.extend(dict(package=k,roots=[rel],reason=c) for c in conflicts for k in sorted(codex_keys))
            elif content != updated:
                actions.append(dict(op='write',path=rel,before=before,after=byte_identity(updated,before['mode'] if before else 0o644),content=base64.b64encode(updated).decode()))
        except (ValueError,OSError) as exc:
            blocked_keys |= codex_keys
            preserved.extend(dict(package=k,roots=[rel],reason=str(exc)) for k in sorted(codex_keys))
    # Registration can veto an agent late. Propagate that veto back to every
    # legacy dependency, then forward to replacement dependents before emit.
    changed=True
    while changed:
        changed=False
        for dependent,owner,rel in [*dependent_retirements,*dependency_edges]:
            if owner in blocked_keys and dependent not in blocked_keys:
                blocked_keys.add(dependent);changed=True
                preserved.append(dict(package=dependent,roots=[rel],reason='connected package preserved by dependency/registration conflict'))
        if codex_keys & blocked_keys:
            if codex_keys - blocked_keys:
                blocked_keys |= codex_keys;changed=True
            actions=[a for a in actions if a['path']!='.codex/config.toml']
            registrations=dict(previous.get('registrations',{}))
    for k in sorted(package_actions):
        if k in blocked_keys:
            if k in previous['packages']:
                next_packages[k]=previous['packages'][k]
            else:
                next_packages.pop(k,None)
            continue
        actions.extend(package_actions[k])
        for old in to_retire.get(k,[]):
            for rel,before in sorted(old['files'].items()):
                actions.append(dict(op='remove',path=rel,before=before,after=None))
        outcomes.append(dict(package=k,status='retired' if k not in current else 'managed',historical=[s.get('releases',[]) for s in discovered.get(k,[])]))

    runtime, runtime_observations = {}, {}
    manage_runtime = request.get('runtime', True)
    prior_runtime = previous['runtime']
    if old_receipt:
        prior_runtime = {'.core-prompts-updater/'+r:i for r,i in old_receipt.get('bundle_files',{}).items()}
    if not manage_runtime:
        runtime = dict(prior_runtime)
    for rel,after in (sorted(bundle.items()) if manage_runtime else []):
        dst='.core-prompts-updater/'+rel
        try:
            before=identity(safe(target,dst)); runtime_observations[dst]=before
        except (ValueError,OSError) as exc:
            blockers.append(f'RUNTIME_CONFLICT: {dst}: {exc}'); continue
        recognized = before is None or before == prior_runtime.get(dst) or before in catalog.runtime_identities(trusted,rel)
        # Self-update from a verified installed runtime may keep identical source
        # files; it still never adopts differing target bytes as trusted source.
        if before == after and (repo.resolve() == (target/'.core-prompts-updater').resolve() or old_receipt or state):
            recognized = recognized or before == prior_runtime.get(dst)
        if not recognized:
            blockers.append(f'RUNTIME_CONFLICT: customized or unknown updater member: {dst}'); continue
        runtime[dst]=after
        if before != after:
            actions.append(dict(op='write',path=dst,before=before,after=after,source=rel))
    for rel,before in (prior_runtime.items() if manage_runtime else []):
        if rel not in runtime and rel.startswith('.core-prompts-updater/'):
            observed=identity(safe(target,rel));runtime_observations[rel]=observed
            if observed != before:
                blockers.append(f'RUNTIME_CONFLICT: obsolete updater member changed: {rel}')
            elif observed is not None:
                actions.append(dict(op='remove',path=rel,before=before,after=None))
    if manage_runtime:
        launcher='update_core_prompts.sh'
        before=identity(safe(target,launcher)); after=byte_identity(LAUNCHER,0o755)
        runtime_observations[launcher]=before
        if before is not None and before != prior_runtime.get(launcher) and before not in catalog.runtime_identities(trusted,launcher):
            blockers.append('LAUNCHER_CONFLICT: existing updater launcher is unrecognized or customized')
        else:
            runtime[launcher]=after
            if before != after:
                actions.append(dict(op='write',path=launcher,before=before,after=after,content=base64.b64encode(LAUNCHER).decode()))
        if any(k.endswith(':engos-audit-engineering-progress') for k in selection):
            rel='.local/bin/eng-report'; package='runtime:eng-report-launcher'
            assessed_keys.add(package)
            content,legacy = providers.reporting_launchers(target)
            after=byte_identity(content,0o755)
            try:
                before=identity(safe(target,rel));runtime_observations[rel]=before
                if before is not None and before not in [prior_runtime.get(rel),after,byte_identity(legacy,0o755)]:
                    raise ValueError('custom reporting launcher')
                runtime[rel]=after
                if before!=after:
                    actions.append(dict(op='write',path=rel,before=before,after=after,content=base64.b64encode(content).decode()))
            except (OSError,ValueError) as exc:
                preserved.append(dict(package=package,roots=[rel],reason=str(exc)))
    installation_preserved = [p for p in previous.get('preserved',[]) if p.get('package') not in assessed_keys] + preserved
    prospective=dict(schema=2,owner='Core-Prompts',selection=sorted(selection),packages=next_packages,
                     runtime=runtime,registrations=registrations,source_version=(repo/'VERSION').read_text().strip(),
                     catalog_sha256=identity(repo/catalog.CATALOG_PATH)['sha256'],preserved=installation_preserved)
    if old_receipt or previous.get('schema1_origin'):
        prospective['schema1_origin'] = previous.get('schema1_origin') or {'profile_sha256':identity(target/V1_PROFILE)['sha256'],'receipt_sha256':identity(target/V1_RECEIPT)['sha256']}
    content=encoded(prospective); after=byte_identity(content)
    before=identity(safe(target,STATE))
    if before != after:
        actions.append(dict(op='write',path=STATE,before=before,after=after,content=base64.b64encode(content).decode()))
    if request.get('release_state'):
        value=dict(request['release_state'])
        if installation_preserved:
            value.update(status='attention-required',note='Runtime updated; some packages preserved. Review installation report.')
        content=encoded(value); rel='.core-prompts-state/release-watch.json'
        before=identity(safe(target,rel));after=byte_identity(content)
        if before != after:
            actions.append(dict(op='write',path=rel,before=before,after=after,content=base64.b64encode(content).decode()))
    # A package must not enqueue the same path through multiple historical
    # matches. Identical duplicate actions collapse; conflicting actions block.
    unique={}
    for action in actions:
        prior=unique.get(action['path'])
        if prior is not None and prior != action:
            blockers.append('ACTION_CONFLICT: '+action['path'])
        unique[action['path']]=action
    return dict(schema=2,repo=str(repo),target=str(target),request=request,selection=sorted(selection),
                source_files=bundle,observations=observations,agent_observations=agent_observations,
                runtime_observations=runtime_observations,state_identity=identity(safe(target,STATE)),
                schema1_profile_identity=identity(safe(target,V1_PROFILE)),schema1_receipt_identity=identity(safe(target,V1_RECEIPT)),
                actions=list(unique.values()),preserved=preserved,installation_preserved=installation_preserved,blockers=blockers,outcomes=outcomes)
