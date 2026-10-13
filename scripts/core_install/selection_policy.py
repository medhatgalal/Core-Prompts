"""Explicit future skill membership. Receipt proof never constitutes consent."""
from __future__ import annotations

import hashlib
import json

POLICIES = {'full_catalog', 'curated', 'legacy_unspecified'}
SHARED_READERS = {'codex', 'gemini'}


def state_policies(state):
    readers = {k.split(':')[0] for k in state['selection']}
    if state['schema'] == 2:
        return {p: 'legacy_unspecified' for p in readers}
    policies = state.get('selection_policy')
    if (not isinstance(policies, dict) or not readers <= set(policies) or set(policies) - {'codex','gemini','claude','kiro','grok','agy'}
            or any(not isinstance(value, str) or value not in POLICIES for value in policies.values())):
        raise ValueError('INVALID_STATE: schema3 requires exact valid provider selection_policy')
    return dict(policies)


def validate_request(request, clients):
    value = request.get('selection_policy')
    if value is None:
        return None
    if value not in ('full_catalog', 'curated'):
        raise ValueError('INVALID_REQUEST: unknown selection policy')
    if request.get('runtime') is False or request.get('legacy_slugs') or request.get('kinds', ['skill']) != ['skill']:
        raise ValueError('INVALID_REQUEST: selection policy requires skills and runtime')
    if 'profile' not in request and ('providers' not in request or len(clients) != 1):
        raise ValueError('INVALID_REQUEST: selection policy requires one explicit provider or an exact profile')
    if 'profile' in request and (request.get('slugs') or set(clients) != set(request['profile']['targets'])):
        raise ValueError('INVALID_REQUEST: policy profile must name exact participants')
    if value == 'full_catalog' and (request.get('slugs') or request.get('profile', {}).get('slugs')):
        raise ValueError('INVALID_REQUEST: full-catalog cannot limit slugs')
    return value


def saved_membership(profile, receipt, historical, current, encoded, key, layouts):
    """Map a saved profile's historical receipt file scope, without incoming enumeration.

    Entire historic package identity and source mapping must match the immutable
    catalog. Current target customization is assessed separately by the planner.
    """
    fail = 'LEGACY_MEMBERSHIP_UNPROVEN: review an exact profile or restore the original ownership receipt; '
    if (not isinstance(receipt, dict) or receipt.get('schema') != 1
            or receipt.get('owner') != 'Core-Prompts'
            or receipt.get('approved_profile_sha256') != hashlib.sha256(encoded(profile)).hexdigest()):
        raise ValueError(fail + 'profile-bound receipt required')
    scope, files = receipt.get('skill_scope'), receipt.get('files')
    if (not isinstance(scope, list) or not scope or scope != sorted(set(scope))
            or not all(isinstance(r, str) and r for r in scope) or not isinstance(files, dict)):
        raise ValueError(fail + 'canonical nonempty historical skill_scope required')
    matched, covered = set(), set()
    for raw in historical:
        if raw['kind'] != 'skill':
            continue
        candidates = []
        if raw['provider'] in profile['targets']:
            candidates.extend((raw['provider'], package, raw['provider']) for package in layouts(raw))
        # The pinned v1.16.3 profile engine installs Gemini's shared tree from
        # the canonical Codex source after checking provider byte equivalence.
        # Preserve that exact source identity and derive logical Gemini only
        # when the original saved profile explicitly named Gemini.
        if ('gemini' in profile['targets'] and raw['provider'] == 'codex'
                and 'v1.16.3' in raw.get('releases', [])):
            candidates.extend(('gemini', package, 'codex') for package in layouts(raw)
                              if package['roots'][0].startswith('.agents/skills/'))
        for logical_provider, package, source_provider in candidates:
            members = package['files']
            if not members or not set(members) <= set(scope):
                continue
            if not all(isinstance(files.get(r), dict) and files[r].get('identity') == ident
                       and files[r].get('source') == r.replace('.agents/skills/', '.' + source_provider + '/skills/', 1)
                       for r, ident in members.items()):
                continue
            successor = package.get('successor', package['slug'])
            next_key = key(logical_provider, 'skill', successor) if successor else None
            if next_key not in current:
                continue
            if profile.get('slugs') and package['slug'] not in profile['slugs'] and successor not in profile['slugs']:
                continue
            matched.add(next_key)
            covered.update(members)
    if covered != set(scope) or not matched or {k.split(':')[0] for k in matched} != set(profile['targets']):
        raise ValueError(fail + 'unmappable or contradictory historical membership')
    return matched


def digest(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
