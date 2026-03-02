#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    print('Python 3.11+ required for tomllib')
    raise SystemExit(1)

import tomllib

ROOT = Path(__file__).resolve().parent.parent
SSOT_DIR = ROOT / 'ssot'
META = ROOT / '.meta' / 'manifest.json'
RULES_PATH = ROOT / '.meta' / 'surface-rules.json'


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


def validate_frontmatter(path: Path, required: list[str]):
    errors = []
    fm = parse_frontmatter(path)
    for key in required:
        if key not in fm or not fm[key]:
            errors.append(f'{path}: missing frontmatter {key}')
    return errors


def validate_gemini(path: Path, required: list[str], slug: str):
    errors = []
    try:
        with path.open('rb') as f:
            data = tomllib.load(f)
    except Exception as exc:
        return [f'{path}: invalid TOML ({exc})']

    for key in required:
        if key not in data:
            errors.append(f'{path}: missing key {key}')
    if data.get('name') != slug:
        errors.append(f'{path}: expected name {slug}, found {data.get("name")}')
    return errors


def validate_json(path: Path, required_fields: list[str], slug: str, resource_patterns: list[str] | None = None):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return [f'{path}: invalid json ({exc})']

    missing = sorted(set(required_fields) - set(data.keys()))
    errors = [f'{path}: missing keys: {", ".join(missing)}'] if missing else []

    if data.get('name') and data.get('name') != slug:
        errors.append(f'{path}: expected name {slug}, found {data.get("name")}')

    if resource_patterns:
        resources = data.get('resources')
        if not isinstance(resources, list) or not resources:
            errors.append(f'{path}: resources must be a non-empty list')
        else:
            for resource in resources:
                if not isinstance(resource, str):
                    errors.append(f'{path}: resources entries must be strings')
                    continue
                if not any(re.match(pattern, resource) for pattern in resource_patterns):
                    errors.append(f'{path}: unsupported resource uri {resource}')

    return errors


def run_kiro_validator(path: Path, rule: dict):
    cmd = rule.get('validator', {}).get('command')
    if not cmd:
        return []

    full = [*cmd, str(path)]
    proc = subprocess.run(full, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        out = proc.stdout.strip() or 'no output'
        return [f'{path}: kiro validation failed: {out}']
    return []


def artifact_expected_path(rule: dict, slug: str) -> Path:
    return ROOT / rule['path'].format(slug=slug)


def expected_dir(rule: dict) -> Path:
    return ROOT / rule['path'].split('{')[0]


def expected_basename(rule: dict, slug: str) -> str:
    return Path(rule['path'].format(slug=slug)).name


def validate_one(rule: dict, slug: str) -> list[str]:
    path = artifact_expected_path(rule, slug)
    fmt = rule['format']
    errors: list[str] = []

    if not path.exists():
        return [f'missing {rule["surface"]} {rule["name"]}: {path.relative_to(ROOT)}']

    if fmt == 'toml':
        errors.extend(validate_gemini(path, rule.get('required_fields', []), slug))
    elif fmt == 'frontmatter_markdown':
        errors.extend(validate_frontmatter(path, rule.get('required_frontmatter', [])))
    elif fmt == 'json':
        errors.extend(validate_json(path, rule.get('required_fields', []), slug, rule.get('resource_uri_patterns')))
        errors.extend(run_kiro_validator(path, rule))
    else:
        errors.append(f'unknown format in rules for {rule["name"]}: {fmt}')

    return errors


def collect_actual(rule: dict):
    fmt = rule['match']
    base_dir = ROOT / rule['path'].split('{')[0].rstrip('/')

    if not base_dir.exists():
        return set()

    if fmt == 'skill_dir':
        return {
            str((base_dir / p.name / 'SKILL.md').relative_to(ROOT))
            for p in sorted(base_dir.glob('*'))
            if p.is_dir() and (p / 'SKILL.md').exists()
        }

    pattern = rule['path'].split('/')[-1].replace('{slug}', '*')
    if '/' in rule['path'].split('/', 1)[1]:
        prefix = '/'.join(rule['path'].split('/')[:-1])
        return {
            str((p).relative_to(ROOT))
            for p in sorted((ROOT / prefix).glob(pattern))
        }

    return {
        str((base_dir / p.name).relative_to(ROOT))
        for p in sorted(base_dir.glob(pattern))
    }


def collect_expected(slugs: set[str], artifacts: list[dict]):
    expected = {}
    for art in artifacts:
        for slug in ssot_slugs:
            expected[art['name']].add(str(artifact_expected_path(art, slug).relative_to(ROOT)))
    return expected


def main():
    if not META.exists():
        print(f'Missing manifest: {META}')
        return 2
    if not RULES_PATH.exists():
        print(f'Missing rules file: {RULES_PATH}')
        return 2

    manifest = json.loads(META.read_text(encoding='utf-8'))
    rules = json.loads(RULES_PATH.read_text(encoding='utf-8')).get('artifacts', [])
    ssot_files = sorted(p.stem for p in SSOT_DIR.glob('*.md'))
    ssot_slugs = set(ssot_files)

    errors: list[str] = []

    if not rules:
        errors.append('No artifact definitions in .meta/surface-rules.json')

    for slug in sorted(ssot_slugs):
        for rule in rules:
            errors.extend(validate_one(rule, slug))

    # Extra/missing artifact checks
    expected = {}
    for rule in rules:
        expected_set = set()
        for slug in ssot_slugs:
            expected_set.add(str(artifact_expected_path(rule, slug).relative_to(ROOT)))
        expected[rule['name']] = expected_set

    for rule in rules:
        actual = set(collect_actual(rule))
        art_name = rule['name']
        for extra in sorted(actual - expected[art_name]):
            errors.append(f'unexpected {rule["surface"]} {art_name}: {extra}')
        for missing in sorted(expected[art_name] - actual):
            errors.append(f'missing {rule["surface"]} {art_name}: {missing}')

    manifest_ssot = {entry['slug'] for entry in manifest.get('ssot_sources', [])}
    if manifest_ssot != ssot_slugs:
        errors.append('manifest slugs do not match ssot directory')

    for artifact_name in [a['name'] for a in rules]:
        if artifact_name not in expected:
            errors.append(f'No expected set produced for artifact: {artifact_name}')

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
