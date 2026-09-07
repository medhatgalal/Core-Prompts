#!/usr/bin/env python3
"""Receipt-protected selected installation, invoked by deploy-surfaces.sh.

No discovery-root scans, recursive retirement, or installation-owner inference.
Only the generated manifest and an explicit profile define writable files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import install_bundle

STATE = '.core-prompts-state/profile-install'
RECEIPT = f'{STATE}/ownership.json'
PROFILE = f'{STATE}/profile.json'
ROOTS = {'codex': '.agents/skills', 'kiro': '.kiro/skills', 'grok': '.grok/skills',
         'claude': '.claude/skills', 'gemini': '.gemini/skills'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def safe(root, rel):
    p = Path(rel)
    if p.is_absolute() or not p.parts or any(x in ('..', '.') for x in p.parts):
        raise ValueError(f'unsafe relative path: {rel}')
    path = root / p
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError(f'symlink is preserved; cannot manage {rel}')
        if candidate == root:
            break
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'path escapes root: {rel}')
    return path


def snapshot(path):
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f'expected regular file: {path}')
    return {'sha256': digest(path.read_bytes()), 'mode': stat.S_IMODE(path.stat().st_mode)}


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.core-prompts-stage-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def bundle_inventory(root, rel):
    path = safe(root, rel)
    if not path.exists():
        return {}
    if not path.is_dir():
        raise ValueError(f'expected skill directory: {rel}')
    return {str(p.relative_to(root)): snapshot(safe(root, str(p.relative_to(root))))
            for p in sorted(path.rglob('*')) if p.is_file() or p.is_symlink()}


def read_receipt(home):
    p = safe(home, RECEIPT)
    if not p.exists():
        return {'schema': 1, 'owner': 'Core-Prompts', 'files': {}}
    result = json.loads(p.read_text())
    if result.get('schema') != 1 or result.get('owner') != 'Core-Prompts':
        raise ValueError('unrecognized ownership receipt')
    return result


def desired_files(repo, profile):
    targets = profile.get('targets', [])
    if not targets or len(set(targets)) != len(targets) or set(targets) - ROOTS.keys():
        raise ValueError('profile requires unique supported targets')
    if profile.get('schema') != 1 or profile.get('scope') != 'skills':
        raise ValueError('profile schema 1 requires explicit skills scope')
    manifest = json.loads((repo / '.meta/manifest.json').read_text())
    slugs = profile.get('slugs', [])
    entries = {e['slug']: e for e in manifest['ssot_sources']}
    if set(slugs) - entries.keys():
        raise ValueError('profile contains unknown slugs')
    result = {}
    for slug, entry in entries.items():
        if slugs and slug not in slugs:
            continue
        for cli in targets:
            surface = cli + '_skill'
            if surface not in entry['expected_surface_names']:
                continue
            skill = f'.{cli}/skills/{slug}/SKILL.md'
            # Full package membership comes from the generated manifest, not home scans.
            members = [skill, *manifest.get('resources', {}).get(surface, [])]
            for rel in members:
                prefix = f'.{cli}/skills/{slug}/'
                if not rel.startswith(prefix):
                    continue
                source = safe(repo, rel)
                value = snapshot(source)
                if value is None:
                    raise ValueError(f'missing generated source: {rel}')
                target = ROOTS[cli] + '/' + slug + '/' + rel[len(prefix):]
                result[target] = {'source': rel, 'identity': value, 'bundle': ROOTS[cli] + '/' + slug}
    if not result:
        raise ValueError('profile selects no generated skill packages')
    return result


def plan(repo, home, profile, routine=False, release_state=None):
    desired = desired_files(repo, profile)
    receipt = read_receipt(home)
    known = receipt['files']
    preserved, observations, blocked = [], {}, set()
    for rel, item in desired.items():
        try:
            current = snapshot(safe(home, rel))
            observations[rel] = current
            if current is not None and current != known.get(rel, {}).get('identity'):
                blocked.add(item['bundle'])
                preserved.append({'path': rel, 'reason': 'unknown provenance or customization'})
        except ValueError as exc:
            blocked.add(item['bundle'])
            observations[rel] = {'blocked': str(exc)}
            preserved.append({'path': rel, 'reason': str(exc)})
    inventories = {}
    for bundle in sorted({i['bundle'] for i in desired.values()}):
        try:
            inventories[bundle] = bundle_inventory(home, bundle)
            if any(rel not in known or value != known[rel].get('identity')
                   for rel, value in inventories[bundle].items()):
                blocked.add(bundle)
                preserved.append({'path': bundle, 'reason': 'package has unknown or customized members'})
        except ValueError as exc:
            blocked.add(bundle)
            inventories[bundle] = {'blocked': str(exc)}
    actions = []
    for rel, item in sorted(desired.items()):
        if item['bundle'] in blocked:
            continue
        if observations[rel] != item['identity']:
            actions.append({'action': 'copy', 'path': rel, 'before': observations[rel], **item})
    # Retirement is an explicit file list. A previous ownership receipt, an identical
    # retained destination, and a reviewed reader evidence reference are all required.
    retiring = set(profile.get('retire', []))
    legacy_ok = set()
    for bundle in sorted({'/'.join(Path(rel).parts[:3]) for rel in retiring}):
        if not bundle.startswith('.codex/skills/') or len(Path(bundle).parts) != 3:
            raise ValueError('retirement is limited to exact legacy Codex skill packages')
        try:
            inventory = bundle_inventory(home, bundle)
            inventories[bundle] = inventory
            complete = set(inventory) <= retiring
            for rel, current in inventory.items():
                retained = '.agents/skills/' + rel.removeprefix('.codex/skills/')
                item = desired.get(retained)
                complete = complete and (current == known.get(rel, {}).get('identity')
                    and item is not None and item['bundle'] not in blocked and current == item['identity'])
            if complete:
                legacy_ok.add(bundle)
        except ValueError as exc:
            inventories[bundle] = {'blocked': str(exc)}
    for rel in sorted(retiring):
        if rel in desired or not rel.startswith('.codex/skills/'):
            raise ValueError('retirement is limited to redundant legacy Codex skill files')
        if '/'.join(Path(rel).parts[:3]) not in legacy_ok:
            preserved.append({'path': rel, 'reason': 'legacy package has unknown, customized, or unlisted members'})
            continue
        current = snapshot(safe(home, rel))
        observations[rel] = current
        if current is None:
            continue
        retained = '.agents/skills/' + rel.removeprefix('.codex/skills/')
        item = desired.get(retained)
        if (not profile.get('reader_evidence') or current != known.get(rel, {}).get('identity')
                or not item or item['bundle'] in blocked or current != item['identity']):
            preserved.append({'path': rel, 'reason': 'retirement ownership, retained identity, or reader evidence missing'})
            continue
        actions.append({'action': 'retire', 'path': rel, 'before': current, 'retained': retained})
    evidence = profile.get('reader_evidence')
    evidence_hash = snapshot(safe(repo, evidence)) if evidence else None
    if evidence and evidence_hash is None:
        raise ValueError('reader evidence file missing')
    updater_observations, blockers = {}, []
    support = safe(home, '.core-prompts-updater')
    bundle = {}
    if routine and not support.exists():
        blockers.append('routine updates require an installed standalone bundle')
    if support.exists():
        try:
            bundle = install_bundle.verified(repo)
        except (ValueError, OSError) as exc:
            blockers.append(str(exc))
        prior_bundle = receipt.get('bundle_files', {})
        for rel, expected in bundle.items():
            target = '.core-prompts-updater/' + rel
            current = snapshot(safe(home, target))
            updater_observations[target] = current
            if routine:
                if current != prior_bundle.get(rel):
                    blockers.append('customized or unknown standalone file: ' + target)
                elif current != expected:
                    actions.append({'action': 'copy', 'path': target, 'before': current,
                                    'source': rel, 'identity': expected, 'bundle': '.core-prompts-updater'})
            elif current != expected:
                blockers.append('installed updater requires separate reviewed refresh: ' + target)
        if routine and set(prior_bundle) - set(bundle):
            blockers.append('standalone bundle file scope was removed; reviewed migration required')
    if routine:
        if digest(encoded(profile)) != receipt.get('approved_profile_sha256'):
            blockers.append('saved target profile differs from approved ownership scope')
        if set(desired) != set(receipt.get('skill_scope', [])):
            blockers.append('selected skill file scope changed; reviewed migration required')
        if preserved or any(observations.get(rel) != known.get(rel, {}).get('identity') for rel in desired):
            blockers.append('selected skills have customized, unknown, or missing files')
    result = {'schema': 1, 'owner': 'Core-Prompts', 'repo': str(repo), 'target': str(home),
            'profile': profile, 'routine': routine, 'release_state': release_state, 'reader_evidence': evidence_hash,
            'manifest_sha256': digest((repo / '.meta/manifest.json').read_bytes()),
            'source_files': desired, 'observed_files': observations, 'inventories': inventories,
            'receipt': snapshot(safe(home, RECEIPT)), 'saved_profile': snapshot(safe(home, PROFILE)),
            'actions': actions, 'preserved': preserved, 'updater_observations': updater_observations, 'blockers': blockers}
    next_receipt = json.loads(json.dumps(receipt))
    for item in actions:
        if item['path'].startswith('.core-prompts-updater/'):
            continue
        if item['action'] == 'copy':
            next_receipt['files'][item['path']] = {'source': item['source'], 'identity': item['identity']}
        else:
            next_receipt['files'].pop(item['path'], None)
    saved_profile = dict(profile)
    if not any(a['path'].startswith('.codex/skills/') for a in preserved):
        saved_profile['retire'] = []
        saved_profile.pop('reader_evidence', None)
    next_receipt['approved_profile_sha256'] = digest(encoded(saved_profile))
    next_receipt['skill_scope'] = sorted(desired)
    next_receipt['bundle_files'] = bundle
    state_actions = []
    state_payloads = [(RECEIPT, next_receipt), (PROFILE, saved_profile)]
    if release_state is not None:
        state_payloads.append(('.core-prompts-state/release-watch.json', release_state))
    for rel, payload in state_payloads:

        after = {'sha256': digest(encoded(payload)), 'mode': 0o644}
        before = snapshot(safe(home, rel))
        if before != after:
            state_actions.append({'path': rel, 'before': before, 'after': after, 'payload': payload})
    result['state_actions'] = state_actions
    transaction = digest(encoded(result))[:32]
    attempt = 0
    while safe(home, f'{STATE}/transactions/{transaction}').exists():
        attempt += 1
        transaction = digest(encoded(result) + str(attempt).encode())[:32]
    txrel = f'{STATE}/transactions/{transaction}'
    result['transaction'] = transaction
    result['transaction_artifacts'] = ([f'{txrel}/journal.json'] + [f'{txrel}/before/{a["path"]}'
        for a in [*actions, *state_actions] if a['before'] is not None]) if actions or state_actions else []
    result['atomic_staging'] = 'temporary .core-prompts-stage-* files beside each written file, removed after replace'
    return result


def apply(repo, home, profile, approved):
    fresh = plan(repo, home, profile, routine=approved.get('routine', False), release_state=approved.get('release_state'))
    if fresh != approved:
        raise ValueError('approved plan differs from current source, profile, ownership, or target; regenerate and review')
    if fresh['blockers']:
        raise ValueError('profile install blocked: ' + '; '.join(fresh['blockers']))
    if not fresh['actions'] and not fresh['state_actions']:
        return {'status': 'no-op', 'preserved': fresh['preserved']}
    transaction = fresh['transaction']
    txrel = f'{STATE}/transactions/{transaction}'
    tx = safe(home, txrel)
    tx.mkdir(parents=True, exist_ok=False)
    changes = [{'path': item['path'], 'before': item['before'],
                'after': item.get('identity') if item['action'] == 'copy' else None}
               for item in fresh['actions']]
    changes.extend({k: item[k] for k in ('path', 'before', 'after')} for item in fresh['state_actions'])
    for change in changes:
        if change['before'] is not None:
            source = safe(home, change['path'])
            if snapshot(source) != change['before']:
                raise ValueError('target changed while saving preimages; regenerate plan')
            atomic_write(tx / 'before' / change['path'], source.read_bytes(), change['before']['mode'])
    atomic_write(tx / 'journal.json', encoded({'schema': 1, 'changes': changes, 'plan': fresh}))
    for item in fresh['actions']:
        dst = safe(home, item['path'])
        if snapshot(dst) != item['before']:
            raise ValueError(f'target changed during apply; recover transaction {transaction}')
        if item['action'] == 'retire':
            dst.unlink()
        else:
            source = safe(repo, item['source'])
            data = source.read_bytes()
            if digest(data) != item['identity']['sha256'] or snapshot(source) != item['identity']:
                raise ValueError(f'source changed during apply; recover transaction {transaction}')
            atomic_write(dst, data, item['identity']['mode'])
    for item in fresh['state_actions']:
        dst = safe(home, item['path'])
        if snapshot(dst) != item['before']:
            raise ValueError(f'state changed during apply; recover transaction {transaction}')
        atomic_write(dst, encoded(item['payload']), item['after']['mode'])
    for change in changes:
        if snapshot(safe(home, change['path'])) != change['after']:
            raise ValueError(f'post-install readback differs; recover transaction {transaction}')
    return {'status': 'applied', 'transaction': transaction, 'actions': len(fresh['actions']),
            'preserved': fresh['preserved']}


def rollback(home, transaction, dry_run=False):
    if len(transaction) != 32 or any(c not in '0123456789abcdef' for c in transaction):
        raise ValueError('invalid transaction id')
    tx = safe(home, f'{STATE}/transactions/{transaction}')
    journal = json.loads((tx / 'journal.json').read_text())
    operational = '.core-prompts-state/release-watch.json'
    release_state = journal['plan'].get('release_state')
    for item in journal['changes']:
        current = snapshot(safe(home, item['path']))
        if item['path'] == operational and release_state is not None and current is not None:
            live = json.loads(safe(home, operational).read_text())
            previous = json.loads(safe(tx, 'before/' + operational).read_text()) if item['before'] else {}
            # Release polling may update timestamps, latest/pending version and notes.
            # Only another installed-version transition invalidates this recovery.
            if live.get('installed_version') not in {previous.get('installed_version'), release_state.get('installed_version')}:
                raise ValueError('rollback preserves newer installed release state')
            current = item['after']

        if current not in (item['before'], item['after']):
            raise ValueError(f'rollback preserves changed file: {item["path"]}')
        if item['before'] is not None:
            if snapshot(safe(tx, 'before/' + item['path'])) != item['before']:
                raise ValueError('rollback backup differs from recorded preimage')
    if dry_run:
        return {'status': 'rollback-planned', 'transaction': transaction, 'changes': journal['changes']}
    for item in reversed(journal['changes']):
        dst = safe(home, item['path'])
        if item['path'] == operational and release_state is not None and item['before']:
            live = json.loads(dst.read_text())
            previous = json.loads(safe(tx, 'before/' + operational).read_text())
            live['installed_version'] = previous.get('installed_version', '')
            latest = live.get('latest_version', '')
            pending = latest if latest.removeprefix('v') != live['installed_version'].removeprefix('v') else ''
            live.update(status='pending-install' if pending else 'current', pending_version=pending,
                        note='Restored previous managed installation; retained latest release observation')
            atomic_write(dst, encoded(live), item['before']['mode'])
            continue
        if snapshot(dst) == item['before']:
            continue
        if item['before'] is None:
            dst.unlink()
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(dst, safe(tx, 'before/' + item['path']).read_bytes(), item['before']['mode'])
    return {'status': 'rolled-back', 'transaction': transaction}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--apply-plan', type=Path)
    parser.add_argument('--rollback')
    parser.add_argument('--sync', action='store_true', help='Use the persisted approved scope for receipt-protected routine updates')
    args = parser.parse_args()
    try:
        if args.apply_plan and (args.dry_run or args.rollback):
            raise ValueError('--apply-plan cannot be combined with --dry-run or --rollback')
        repo, home = args.repo.absolute(), args.target.absolute()
        if repo.resolve() == home.resolve():
            raise ValueError('profile installs require a distinct target; build repository surfaces instead')
        if args.rollback:
            result = rollback(home, args.rollback, args.dry_run)
        else:
            if not args.profile:
                raise ValueError('--profile is required')
            profile = json.loads(args.profile.read_text())
            if args.sync:
                approved = plan(repo, home, profile, routine=True)
                result = approved if args.dry_run else apply(repo, home, profile, approved)
            elif args.dry_run:
                result = plan(repo, home, profile)
            elif args.apply_plan:
                result = apply(repo, home, profile, json.loads(args.apply_plan.read_text()))
            else:
                raise ValueError('use --dry-run or an exact reviewed --apply-plan')
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
