#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 11):
    print('Python 3.11+ required for tomllib')
    raise SystemExit(1)

import tomllib

ROOT = Path(__file__).resolve().parent.parent
SSOT_DIR = ROOT / 'ssot'
META = ROOT / '.meta' / 'manifest.json'
RULES_PATH = ROOT / '.meta' / 'surface-rules.json'
SCHEMA_CACHE_MANIFEST = ROOT / '.meta' / 'schema-cache' / 'manifest.json'


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


def parse_args():
    parser = argparse.ArgumentParser(description='Validate generated CLI surfaces from SSOT.')
    parser.add_argument('--strict', action='store_true', help='fail on optional checks and missing optional CLI tooling')
    parser.add_argument('--with-cli', action='store_true', help='execute CLI-provided validators where available')
    parser.add_argument('--fail-on-cli-miss', action='store_true', help='treat all declared CLI tooling as required')
    parser.add_argument('--skip-schema', action='store_true', help='skip schema cache checks')
    return parser.parse_args()


def parse_bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def run_command(command: list[str], path: Path | None = None):
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=path.parent if path else None,
        timeout=20,
    )
    return proc.returncode, proc.stdout.strip()


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
    errors = [f"{path}: missing keys: {', '.join(missing)}"] if missing else []

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


def validate_schema_artifact(rule: dict, slug: str, strict: bool, warnings: list[str]):
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
        errors.extend(run_artifact_validator(path, rule, strict, warnings))
    else:
        errors.append(f'unknown format in rules for {rule["name"]}: {fmt}')

    return errors


def run_artifact_validator(path: Path, rule: dict, strict: bool, warnings: list[str]):
    validator = rule.get('validator', {})
    command = validator.get('command')
    if not command:
        return []

    if shutil.which(command[0]) is None:
        msg = f'missing validator command: {command[0]} ({path.name})'
        if strict:
            return [msg]
        warnings.append(msg)
        return []

    try:
        code, out = run_command([*command, str(path)])
    except Exception as exc:
        msg = f'{path}: validator execution error ({exc})'
        return [msg] if strict else warnings.append(msg) or []

    if code != 0:
        return [f'{path}: validator failed with code {code}: {out}']
    return []


def artifact_expected_path(rule: dict, slug: str) -> Path:
    return ROOT / rule['path'].format(slug=slug)


def collect_actual(rule: dict):
    fmt = rule['match']
    if fmt == 'skill_dir':
        skill_root = ROOT / '.codex' / 'skills'
        return {
            str((p / 'SKILL.md').relative_to(ROOT))
            for p in sorted(skill_root.glob('*'))
            if p.is_dir() and (p / 'SKILL.md').exists()
        }

    target = ROOT / rule['path']
    pattern = rule['path'].split('/')[-1].replace('{slug}', '*')
    base = target.parent
    if not base.exists():
        return set()
    return {
        str((base / p.name).relative_to(ROOT))
        for p in sorted(base.glob(pattern))
    }


def load_cache() -> dict:
    if not SCHEMA_CACHE_MANIFEST.exists():
        return {'generated_at': None, 'entries': []}
    try:
        return json.loads(SCHEMA_CACHE_MANIFEST.read_text(encoding='utf-8'))
    except Exception:
        return {'generated_at': None, 'entries': []}


def check_schema_cache(rules: list[dict], strict: bool, ttl_days: int, warnings: list[str]):
    cache = load_cache()
    index = {}
    for entry in cache.get('entries', []):
        if isinstance(entry, dict) and 'url' in entry:
            index[entry['url']] = entry

    now = datetime.now(timezone.utc)
    errors = []
    checked = []

    for rule in rules:
        if rule.get('schema_mode') != 'remote':
            continue
        for url in rule.get('source_urls', []):
            checked.append(url)
            cached = index.get(url)
            if not cached:
                message = f'missing schema cache entry for {url}'
                if strict:
                    errors.append(message)
                else:
                    warnings.append(message)
                continue

            if not cached.get('ok', False):
                message = f'schema cache marks source as unhealthy for {url}'
                if strict:
                    errors.append(message)
                else:
                    warnings.append(message)
                continue

            fetched_at = cached.get('fetched_at')
            if fetched_at:
                try:
                    age = now - datetime.fromisoformat(fetched_at)
                    if age.days >= ttl_days:
                        msg = f'schema cache entry stale ({age.days}d) for {url}'
                        if strict:
                            errors.append(msg)
                        else:
                            warnings.append(msg)
                except Exception:
                    if strict:
                        errors.append(f'cannot parse schema cache timestamp for {url}')
                    else:
                        warnings.append(f'cannot parse schema cache timestamp for {url}')

    return errors, sorted(set(checked))


def collect_cli_versions(rules: dict[str, Any]):
    tooling = rules.get('tooling', [])
    cli_info = {}
    for tool in tooling:
        name = tool['name']
        binary = tool.get('command')
        entry = {
            'command': binary,
            'required': bool(tool.get('required', False)),
            'available': shutil.which(binary) is not None,
        }
        if entry['available']:
            version_cmd = [binary] + list(tool.get('version_args') or ['--version'])
            try:
                code, output = run_command(version_cmd)
            except Exception as exc:
                entry['version_error'] = str(exc)
            else:
                entry['version_exit_code'] = code
                entry['version_output'] = output.splitlines()[:4]
        cli_info[name] = entry
    return cli_info


def cli_probe_warnings(rules: dict, args):
    errors: list[str] = []
    warnings: list[str] = []

    for tool in rules.get('tooling', []):
        name = tool.get('name', 'unknown')
        binary = tool.get('command')
        required = bool(tool.get('required', False))
        if shutil.which(binary) is None:
            if args.fail_on_cli_miss or (args.strict and required):
                errors.append(f'missing required CLI binary: {name} ({binary})')
            else:
                warnings.append(f'missing CLI binary (non-fatal): {name} ({binary})')
    return errors, warnings

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def update_manifest_provenance(manifest: dict, args, validation_errors: list[str], validation_warnings: list[str], checked_sources: list[str], cli_info: dict):
    manifest['validation'] = {
        'validated_at': now_iso(),
        'strict': args.strict,
        'with_cli': args.with_cli,
        'fail_on_cli_miss': args.fail_on_cli_miss,
        'rules_file': str(RULES_PATH.relative_to(ROOT)),
        'rules_sha256': sha256_file(RULES_PATH),
        'schema_cache_ttl_days': int((json.loads(RULES_PATH.read_text(encoding='utf-8')).get('schema_cache_ttl_days') or 0)),
        'schema_cache_sources_checked': checked_sources,
        'validation_errors': len(validation_errors),
        'validation_warnings': len(validation_warnings),
        'cli_versions': cli_info,
    }
    META.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


def main():
    args = parse_args()
    args.strict = args.strict or parse_bool_env('SURFACE_VALIDATE_STRICT', False)
    args.with_cli = args.with_cli or parse_bool_env('SURFACE_VALIDATE_WITH_CLI', False)
    if args.fail_on_cli_miss:
        args.strict = True

    if not META.exists():
        print(f'Missing manifest: {META}')
        return 2
    if not RULES_PATH.exists():
        print(f'Missing rules file: {RULES_PATH}')
        return 2

    rules_obj = json.loads(RULES_PATH.read_text(encoding='utf-8'))
    rules = rules_obj.get('artifacts', [])
    ssot_files = sorted(p.stem for p in SSOT_DIR.glob('*.md'))
    ssot_slugs = set(ssot_files)

    if not rules:
        print('No artifact definitions in .meta/surface-rules.json')
        return 2

    manifest = json.loads(META.read_text(encoding='utf-8'))

    errors: list[str] = []
    warnings: list[str] = []

    for slug in sorted(ssot_slugs):
        for rule in rules:
            errors.extend(validate_schema_artifact(rule, slug, args.with_cli or args.strict, warnings))

    # Extra / missing file checks
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

    # Schema cache checks
    ttl_days = int(rules_obj.get('schema_cache_ttl_days', 14))
    cache_errors, checked_sources = ([], [])
    if not args.skip_schema:
        cache_errors, checked_sources = check_schema_cache(rules, args.strict or args.with_cli, ttl_days, warnings)
        errors.extend(cache_errors)

    # manifest consistency check
    manifest_ssot = {entry.get('slug') for entry in manifest.get('ssot_sources', [])}
    if manifest_ssot != ssot_slugs:
        errors.append('manifest slugs do not match ssot directory')

    # CLI existence checks for optional/strict behavior
    cli_errors, cli_warnings = cli_probe_warnings(rules_obj, args)
    errors.extend(cli_errors)
    warnings.extend(cli_warnings)

    cli_info = collect_cli_versions(rules_obj)

    # Always write provenance so callers can see what was used
    update_manifest_provenance(manifest, args, errors, warnings, checked_sources, cli_info)

    if warnings:
        print('Warnings:')
        for warning in warnings:
            print('-', warning)

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
