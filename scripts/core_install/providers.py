"""Provider-specific package layouts and conservative registration patches.

This module is pure: it describes packages and returns proposed bytes; only the
transaction module writes to an installation.
"""
from __future__ import annotations

import json
import fnmatch
from functools import lru_cache
import posixpath
import re
import shlex
import tomllib
from pathlib import Path
from urllib.parse import unquote

PROVIDERS = ('codex', 'kiro', 'claude', 'gemini', 'grok')
AGENT_EXTENSIONS = {'codex': 'toml', 'kiro': 'json', 'claude': 'md', 'gemini': 'md'}
SKILL_ROOTS = {p: ('.agents/skills' if p == 'codex' else f'.{p}/skills') for p in PROVIDERS}


def reporting_launchers(target):
    """Current safe launcher and exact target-bound launcher emitted in v1.13+."""
    script=str(target / '.core-prompts-updater/scripts/eng-report.py')
    legacy=f'''#!/usr/bin/env bash
set -euo pipefail
SCRIPT="{script}"
if [[ ! -f "$SCRIPT" ]]; then echo "error: eng-report.py not found at $SCRIPT" >&2; exit 1; fi
exec python3 "$SCRIPT" "$@"
'''.encode()
    current=f'''#!/usr/bin/env bash
set -euo pipefail
SCRIPT={shlex.quote(script)}
if [[ -n "${{PYTHON_BIN:-}}" ]]; then runner="$PYTHON_BIN";
elif command -v python3.14 >/dev/null 2>&1; then runner=python3.14;
else runner=python3; fi
exec "$runner" "$SCRIPT" "$@"
'''.encode()
    return current,legacy


def key(provider, kind, slug):
    return f'{provider}:{kind}:{slug}'


def current_packages(repo, manifest, snapshot, safe):
    """Expand declared source membership, preserving provider and surface identity."""
    result = {}
    for entry in manifest['ssot_sources']:
        slug = entry['slug']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError(f'invalid source slug: {slug}')
        for surface in entry['expected_surface_names']:
            provider, kind = surface.rsplit('_', 1)
            if provider not in PROVIDERS or kind not in ('skill', 'agent'):
                raise ValueError(f'unsupported source surface: {surface}')
            if kind == 'skill':
                source_root = f'.{provider}/skills/{slug}'
                root = f'{SKILL_ROOTS[provider]}/{slug}'
                entrypoint = f'{source_root}/SKILL.md'
                roots = [root]
                convert = lambda rel: root + rel[len(source_root):]
                members = [entrypoint, *[r for r in manifest.get('resources', {}).get(surface, []) if r.startswith(source_root + '/')]]
            else:
                if provider not in AGENT_EXTENSIONS:
                    raise ValueError(f'provider has no agent surface: {provider}')
                entrypoint = f'.{provider}/agents/{slug}.{AGENT_EXTENSIONS[provider]}'
                resource_root = f'.{provider}/agents/resources/{slug}'
                roots = [entrypoint, resource_root]
                convert = lambda rel: rel
                members = [entrypoint, *[r for r in manifest.get('resources', {}).get(surface, []) if r.startswith(resource_root + '/')]]
            files, sources = {}, {}
            for rel in members:
                identity = snapshot(safe(repo, rel))
                if identity is None:
                    raise ValueError(f'missing source member: {rel}')
                files[convert(rel)] = identity
                sources[convert(rel)] = rel
            result[key(provider, kind, slug)] = dict(provider=provider, kind=kind, slug=slug,
                roots=roots, files=files, sources=sources, entrypoint=convert(entrypoint))
    return result


def codex_layouts(package):
    """Historical Codex skills can have been copied into either documented root."""
    yield package
    if package['provider'] == 'codex' and package['kind'] == 'skill':
        clone = dict(package)
        transform = lambda rel: rel.replace('.codex/skills/', '.agents/skills/', 1)
        clone['roots'] = [transform(r) for r in package['roots']]
        clone['files'] = {transform(r): value for r, value in package['files'].items()}
        if clone['roots'] != package['roots']:
            yield clone


def agent_skill_dependencies(package, repo):
    if package['kind'] != 'agent' or package['provider'] != 'kiro':
        return []
    payload = json.loads((repo / package['sources'][package['entrypoint']]).read_text())
    return [r.removeprefix('skill://') for r in payload.get('resources', [])
            if isinstance(r, str) and r.startswith('skill://') and '*' not in r]


def references_removed_files(content, config_rel, target, removed, replacement=()):
    """Conservatively resolve file/skill URIs, directories and glob resources.

    Historical generated root-relative URIs and documented agent-relative URIs
    are both considered. This is bounded string matching against the proposed
    file set, never a recursive discovery-root scan or environment expansion.
    """
    if any(rel in content for rel in removed):
        return True
    refs = re.findall(r'(?:file|skill)://([^\s\"\'<>`]+)', content)
    for raw in refs:
        raw=unquote(raw)
        if '${' in raw or '$' in raw or '\\' in raw:
            return True  # unresolved local references cannot authorize retirement
        if raw.startswith('~/'):
            patterns=[str(target / raw[2:])]
        elif raw.startswith('/'):
            patterns=[raw]
        else:
            patterns=[str(target / raw),str(target / Path(config_rel).parent / raw)]
        patterns=[posixpath.normpath(p) for p in patterns]
        def globmatch(path, pattern):
            names,parts=path.split('/'),pattern.split('/')
            @lru_cache(None)
            def match(i,j):
                if j==len(parts):
                    return i==len(names)
                if parts[j]=='**':
                    return match(i,j+1) or (i<len(names) and match(i+1,j))
                return i<len(names) and fnmatch.fnmatchcase(names[i],parts[j]) and match(i+1,j+1)
            return match(0,0)
        def matches(rel):
            absolute=str(target / rel)
            ancestors=[absolute,*[str(p) for p in Path(absolute).parents if str(p).startswith(str(target))]]
            return any(globmatch(path,pattern) for pattern in patterns for path in ancestors)
        if any(matches(rel) for rel in removed):
            # A root-wide discovery pattern still finds a complete successor.
            # Old-name-specific globs do not, so they preserve that predecessor.
            if replacement and all(matches(rel) for rel in replacement):
                continue
            return True
    return False


def registration_patch(original, target, additions, retirements, owned_stanzas):
    """Return exact-span changes only for generated, proven agent registrations.

    Never grant stanza ownership from a marker, matching name or conventional
    path alone. Callers supply independently proven installed agent paths. Only
    a config_file-only legacy stanza is eligible without a prior stanza receipt.
    Unknown extra settings, comments within a stanza and unrelated bytes survive.
    """
    text = original.decode('utf-8')
    # TOML parse failure is a blocker, not an excuse to rewrite the config.
    document = tomllib.loads(text)
    agents = document.get('agents', {})
    if not isinstance(agents, dict):
        raise ValueError('invalid Codex agents table')
    header = re.compile(r'^\[agents\.([a-z0-9-]+)\]\s*(?:\r?\n|$)', re.M)
    matches = list(header.finditer(text))
    spans = {}
    for match in matches:
        end_match = re.search(r'^\s*\[|^# (?:>>>|<<<) core-prompts codex agents', text[match.end():], re.M)
        end = match.end() + end_match.start() if end_match else len(text)
        if match[1] in spans:
            raise ValueError('duplicate Codex agent stanza')
        spans[match[1]] = (match.start(), end, text[match.start():end])
    edits, after_owned, conflicts = [], dict(owned_stanzas), []
    for slug, old_path in retirements.items():
        if slug not in agents:
            continue
        span = spans.get(slug)
        if span is None:
            conflicts.append(f'custom Codex registration syntax: {slug}')
            continue
        body = span[2]
        values = agents[slug]
        expected_path = str(target / old_path)
        generated = (values == {'config_file': expected_path}
                     and all('#' not in line for line in body.splitlines()))
        if owned_stanzas.get(slug) == body or generated:
            edits.append((span[0], span[1], ''))
            after_owned.pop(slug, None)
        else:
            conflicts.append(f'custom Codex registration: {slug}')
    for slug, new_path in additions.items():
        body = f'[agents.{slug}]\nconfig_file = {json.dumps(str(target / new_path))}\n\n'
        if slug in agents:
            span = spans.get(slug)
            if agents[slug] == {'config_file': str(target / new_path)} and span:
                # A matching path can be used without taking ownership of user
                # comments; otherwise a later retirement could delete them.
                if owned_stanzas.get(slug) == span[2] or all('#' not in line for line in span[2].splitlines()):
                    after_owned[slug] = span[2]
                continue
            if span and owned_stanzas.get(slug) == span[2]:
                edits.append((span[0], span[1], body))
                after_owned[slug] = body
            else:
                conflicts.append(f'custom successor Codex registration: {slug}')
        else:
            after_owned[slug] = body
            edits.append((len(text), len(text), ('\n' if text and not text.endswith('\n\n') else '') + body))
    if conflicts:
        return original, dict(owned_stanzas), conflicts
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    tomllib.loads(text)
    return text.encode(), after_owned, []
