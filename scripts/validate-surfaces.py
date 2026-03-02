#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
import sys

if sys.version_info < (3, 11):
    print('Python 3.11+ required for tomllib')
    raise SystemExit(1)

import tomllib

ROOT = Path(__file__).resolve().parent.parent
SSOT_DIR = ROOT / 'ssot'
META = ROOT / '.meta' / 'manifest.json'

REQUIRED = {
    '.gemini/commands': 1,
    '.claude/commands': 1,
    '.kiro/prompts': 1,
    '.kiro/agents': 1,
    '.codex/skills': 1,
}


def parse_frontmatter(path: Path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        return {}
    end = text.find('\n---', 3)
    if end == -1:
        return {}
    block = text[4:end].strip()
    out = {}
    for line in block.splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def validate_gemini(path: Path, slug: str):
    with path.open('rb') as f:
        data = tomllib.load(f)
    errors = []
    for key in ('name', 'description', 'prompt'):
        if key not in data:
            errors.append(f'{path}: missing key {key}')
    if data.get('name') != slug:
        errors.append(f'{path}: expected name {slug}, found {data.get("name")}')
    return errors


def validate_frontmatter(path: Path):
    errors = []
    fm = parse_frontmatter(path)
    if not fm.get('description'):
        errors.append(f'{path}: missing description in frontmatter')
    return errors


def validate_json(path: Path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return [f'{path}: invalid json: {exc}']
    missing = {'name', 'description', 'prompt', 'resources', 'hooks', 'tools'} - set(data)
    return [f'{path}: missing keys: {', '.join(sorted(missing))}'] if missing else []


def check_paths(root: Path, pattern: str):
    return sorted(p.name for p in root.glob(pattern))


def main():
    if not META.exists():
        print('Missing manifest:', META)
        return 2

    manifest = json.loads(META.read_text(encoding='utf-8'))
    ssot_files = sorted(p.stem for p in SSOT_DIR.glob('*.md'))

    errors = []

    # Ensure every SSOT has generated output in each surface
    for slug in ssot_files:
        if not (ROOT / '.gemini' / 'commands' / f'{slug}.toml').exists():
            errors.append(f'missing gemini command: .gemini/commands/{slug}.toml')
        if not (ROOT / '.claude' / 'commands' / f'{slug}.md').exists():
            errors.append(f'missing claude command: .claude/commands/{slug}.md')
        if not (ROOT / '.kiro' / 'prompts' / f'{slug}.md').exists():
            errors.append(f'missing kiro prompt: .kiro/prompts/{slug}.md')
        if not (ROOT / '.kiro' / 'agents' / f'{slug}.json').exists():
            errors.append(f'missing kiro agent: .kiro/agents/{slug}.json')
        if not (ROOT / '.codex' / 'skills' / slug / 'SKILL.md').exists():
            errors.append(f'missing codex skill: .codex/skills/{slug}/SKILL.md')

        errors.extend(validate_gemini(ROOT / '.gemini' / 'commands' / f'{slug}.toml', slug))
        errors.extend(validate_frontmatter(ROOT / '.claude' / 'commands' / f'{slug}.md'))
        errors.extend(validate_frontmatter(ROOT / '.kiro' / 'prompts' / f'{slug}.md'))
        errors.extend(validate_frontmatter(ROOT / '.codex' / 'skills' / slug / 'SKILL.md'))
        errors.extend(validate_json(ROOT / '.kiro' / 'agents' / f'{slug}.json'))

    # Ensure no extras
    allowed_gemini = {f'{s}.toml' for s in ssot_files}
    allowed_claude = {f'{s}.md' for s in ssot_files}
    allowed_kiro_prompt = {f'{s}.md' for s in ssot_files}
    allowed_kiro_agent = {f'{s}.json' for s in ssot_files}
    allowed_codex = {s for s in ssot_files}

    actual_gemini = {p.name for p in (ROOT / '.gemini' / 'commands').glob('*.toml')}
    actual_claude = {p.name for p in (ROOT / '.claude' / 'commands').glob('*.md')}
    actual_kiro_prompt = {p.name for p in (ROOT / '.kiro' / 'prompts').glob('*.md')}
    actual_kiro_agent = {p.name for p in (ROOT / '.kiro' / 'agents').glob('*.json')}
    actual_codex = {p.name for p in (ROOT / '.codex' / 'skills').glob('*') if p.is_dir()}

    for extra in sorted(actual_gemini - allowed_gemini):
        errors.append(f'unexpected gemini artifact: .gemini/commands/{extra}')
    for extra in sorted(actual_claude - allowed_claude):
        errors.append(f'unexpected claude artifact: .claude/commands/{extra}')
    for extra in sorted(actual_kiro_prompt - allowed_kiro_prompt):
        errors.append(f'unexpected kiro prompt: .kiro/prompts/{extra}')
    for extra in sorted(actual_kiro_agent - allowed_kiro_agent):
        errors.append(f'unexpected kiro agent: .kiro/agents/{extra}')
    for extra in sorted(actual_codex - allowed_codex):
        errors.append(f'unexpected codex skill dir: .codex/skills/{extra}')

    # manifest sanity
    manifest_ssot = {entry['slug'] for entry in manifest.get('ssot_sources', [])}
    if manifest_ssot != set(ssot_files):
        errors.append('manifest slugs do not match ssot directory')

    if errors:
        print('Validation failed:')
        for e in errors:
            print('-', e)
        return 2

    print('Validation passed.')
    print(f'SSOT files: {len(ssot_files)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
