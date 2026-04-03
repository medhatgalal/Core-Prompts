#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
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
VALIDATION_REPORT_DIR = ROOT / 'reports' / 'validation'
CONTRACT_REQUIRED_SLUGS = {path.stem for path in SSOT_DIR.glob('*.md')}
BENCHMARK_SECTION_ALIASES = {
    'Purpose': ('Purpose',),
    'Primary Objective': ('Primary Objective',),
    'Workflow Contract': (
        'Workflow',
        'Review Process',
        'Standard Workflow',
        'Invocation Contract',
        'Agent Operating Contract',
        'Workflow Contract',
        'Resolution Process',
        'Execution Plan',
    ),
    'Boundaries': ('Tool Boundaries', 'Capability Boundary', 'Constraints', 'Hard Constraints'),
    'Invocation Hints': ('Invocation Hints', 'Usage Examples', 'Examples'),
    'Required Inputs': ('Required Inputs',),
    'Required Output': ('Required Output', 'Expected Outputs', 'Output Contract', 'Output Format'),
    'Examples': ('Examples', 'Usage Examples', 'Example Invocation Patterns'),
    'Evaluation Rubric': ('Evaluation Rubric',),
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


def count_frontmatter_blocks(path: Path):
    text = path.read_text(encoding='utf-8')
    remainder = text
    count = 0
    while remainder.startswith('---\n'):
        end = remainder.find('\n---', 3)
        if end == -1:
            break
        count += 1
        remainder = remainder[end + 4 :]
        if remainder.startswith('\n'):
            remainder = remainder[1:]
    return count


def strip_frontmatter_blocks(text: str) -> str:
    remainder = text
    while remainder.startswith('---\n'):
        end = remainder.find('\n---', 3)
        if end == -1:
            break
        remainder = remainder[end + 4 :]
        if remainder.startswith('\n'):
            remainder = remainder[1:]
    return remainder


def extract_first_heading(text: str, fallback_slug: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('# '):
            return stripped[2:].strip()
    return ' '.join(part.capitalize() for part in fallback_slug.replace('_', '-').split('-'))


def collect_h2_titles(text: str) -> set[str]:
    return {line[3:].strip() for line in text.splitlines() if line.startswith('## ')}


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
    block_count = count_frontmatter_blocks(path)
    if block_count > 1:
        errors.append(f'{path}: multiple frontmatter blocks found ({block_count})')
    for key in required:
        if key not in fm or not fm[key]:
            errors.append(f'{path}: missing frontmatter {key}')
    return errors


def validate_descriptor_display_name(path: Path, slug: str):
    descriptor_path = ROOT / '.meta' / 'capabilities' / f'{slug}.json'
    if not descriptor_path.exists():
        return []
    try:
        descriptor = json.loads(descriptor_path.read_text(encoding='utf-8'))
    except Exception as exc:
        return [f'{descriptor_path}: invalid json ({exc})']

    text = path.read_text(encoding='utf-8')
    canonical_display_name = (
        parse_frontmatter(path).get('display_name')
        or extract_first_heading(strip_frontmatter_blocks(text), slug)
    )
    descriptor_display_name = (
        descriptor.get('display_name')
        or ((descriptor.get('layers') or {}).get('minimal') or {}).get('display_name')
        or ''
    )
    if descriptor_display_name and descriptor_display_name != canonical_display_name:
        return [
            f'{path}: descriptor display_name drift (ssot "{canonical_display_name}" != descriptor "{descriptor_display_name}")'
        ]
    return []


def validate_benchmark_contract(path: Path, slug: str):
    if slug not in CONTRACT_REQUIRED_SLUGS:
        return []
    titles = collect_h2_titles(path.read_text(encoding='utf-8'))
    errors = []
    for label, aliases in BENCHMARK_SECTION_ALIASES.items():
        if not any(alias in titles for alias in aliases):
            errors.append(f'{path}: benchmark contract missing section for {label}')
    return errors


def validate_ssot_source(path: Path):
    errors = validate_frontmatter(path, ['name', 'description'])
    slug = path.stem
    errors.extend(validate_descriptor_display_name(path, slug))
    errors.extend(validate_benchmark_contract(path, slug))
    return errors


def validate_toml(path: Path, required: list[str], slug: str, forbidden: list[str] | None = None):
    errors = []
    try:
        with path.open('rb') as f:
            data = tomllib.load(f)
    except Exception as exc:
        return [f'{path}: invalid TOML ({exc})']

    for key in required:
        if key not in data:
            errors.append(f'{path}: missing key {key}')
    for key in forbidden or []:
        if key in data:
            errors.append(f'{path}: forbidden key {key}')
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


LOCAL_ABSOLUTE_SOURCE_PATTERN = re.compile(r"^(/|[A-Za-z]:[\\/]).+")
SECRET_LITERAL_PATTERN = re.compile(
    r'(?i)\b(api[_-]?key|access[_-]?token|secret|password)\b\s*[:=]\s*["\']?([A-Za-z0-9_\-\/+=]{16,})'
)
SECRET_PLACEHOLDER_PATTERN = re.compile(r'(?i)(example|sample|dummy|placeholder|changeme|your_|<|env\b|\$\{)')


def _find_absolute_local_source_refs(value, *, path_parts: tuple[str, ...] = ()):
    findings: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            findings.extend(_find_absolute_local_source_refs(nested, path_parts=(*path_parts, str(key))))
        return findings
    if isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(_find_absolute_local_source_refs(nested, path_parts=(*path_parts, str(index))))
        return findings
    if not isinstance(value, str):
        return findings
    if not LOCAL_ABSOLUTE_SOURCE_PATTERN.match(value):
        return findings
    joined = ".".join(path_parts)
    if joined.endswith("layers.minimal.resources.0") or joined.endswith("layers.minimal.source_provenance.normalized_source"):
        findings.append((joined, value))
    return findings


def validate_portable_capability_metadata(path: Path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return [f'{path}: invalid json ({exc})']

    findings = _find_absolute_local_source_refs(data)
    return [f'{path}: absolute local source reference is not portable at {joined}: {value}' for joined, value in findings]


def _walk_key_values(value, *, path_parts: tuple[str, ...] = ()):
    findings: list[tuple[tuple[str, ...], object]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            findings.extend(_walk_key_values(nested, path_parts=(*path_parts, str(key))))
        return findings
    if isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(_walk_key_values(nested, path_parts=(*path_parts, str(index))))
        return findings
    findings.append((path_parts, value))
    return findings


def validate_advisory_policy_metadata(path: Path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return [f'{path}: invalid json ({exc})']

    errors: list[str] = []
    for joined, value in _walk_key_values(data):
        joined_path = '.'.join(joined)
        if joined_path.endswith('authority_tier') and value not in {'advisory', 'workflow_provider', 'advisor', 'analyst'}:
            errors.append(f'{path}: unexpected authority_tier {value!r} at {joined_path}')
    if path.name == 'capability-handoff.json':
        if data.get('advisory_only') is not True:
            errors.append(f'{path}: handoff contract must set advisory_only=true')
    minimal = ((data.get('layers') or {}).get('minimal') or {}) if isinstance(data, dict) else {}
    tool_policy = minimal.get('tool_policy') or {}
    forbidden = {str(item).casefold() for item in tool_policy.get('forbidden') or []}
    required_forbidden = {'orchestration', 'delegation decisions', 'runtime execution control'}
    missing = sorted(required_forbidden - forbidden)
    if minimal and missing:
        errors.append(f'{path}: tool_policy.forbidden missing {", ".join(missing)}')
    return errors


def validate_secret_like_literals(path: Path):
    try:
        text = path.read_text(encoding='utf-8')
    except Exception as exc:
        return [f'{path}: cannot read text for secret scan ({exc})']

    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = SECRET_LITERAL_PATTERN.search(line)
        if not match:
            continue
        candidate = match.group(2)
        if SECRET_PLACEHOLDER_PATTERN.search(candidate):
            continue
        errors.append(f'{path}:{line_number}: secret-like literal detected for {match.group(1)}')
    return errors


def validate_schema_artifact(
    rule: dict,
    slug: str,
    with_cli: bool,
    strict: bool,
    warnings: list[str],
):
    path = artifact_expected_path(rule, slug)
    fmt = rule['format']
    errors: list[str] = []

    if not path.exists():
        return [f'missing {rule["surface"]} {rule["name"]}: {path.relative_to(ROOT)}']

    if fmt == 'toml':
        errors.extend(validate_toml(path, rule.get('required_fields', []), slug, rule.get('forbidden_fields')))
    elif fmt == 'frontmatter_markdown':
        errors.extend(validate_frontmatter(path, rule.get('required_frontmatter', [])))
    elif fmt == 'json':
        errors.extend(validate_json(path, rule.get('required_fields', []), slug, rule.get('resource_uri_patterns')))
        if with_cli:
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


def eligible_slugs_for_rule(rule: dict, manifest_entries: list[dict[str, object]]) -> set[str]:
    matched = set()
    artifact_name = rule['name']
    for entry in manifest_entries:
        emitted = set(entry.get('expected_surface_names') or [])
        if artifact_name in emitted:
            matched.add(str(entry.get('slug')))
    return matched


def collect_actual(rule: dict):
    fmt = rule['match']
    if fmt == 'skill_dir':
        skill_root_value = rule.get('skill_root')
        if skill_root_value:
            skill_root = ROOT / skill_root_value
        else:
            path_template = rule.get('path', '')
            if '{slug}' not in path_template:
                return set()
            prefix = path_template.split('{slug}', 1)[0].rstrip('/')
            skill_root = ROOT / prefix
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


def safe_rglob(base: Path, pattern: str) -> list[Path]:
    if not base.exists():
        return []
    try:
        return sorted(base.rglob(pattern))
    except FileNotFoundError:
        matched: list[Path] = []
        for dirpath, _, filenames in os.walk(base):
            for filename in filenames:
                if fnmatch.fnmatch(filename, pattern):
                    matched.append(Path(dirpath) / filename)
        return sorted(matched)


def collect_capability_metadata_paths() -> list[Path]:
    descriptor_paths = sorted((ROOT / '.meta' / 'capabilities').glob('*.json'))
    bundled_paths = safe_rglob(ROOT / '.codex', 'capability.json')
    bundled_paths += safe_rglob(ROOT / '.gemini', 'capability.json')
    bundled_paths += safe_rglob(ROOT / '.claude', 'capability.json')
    bundled_paths += safe_rglob(ROOT / '.kiro', 'capability.json')
    return [ROOT / '.meta' / 'manifest.json', ROOT / '.meta' / 'capability-handoff.json', *descriptor_paths, *bundled_paths]


def collect_surface_text_paths() -> list[Path]:
    paths: list[Path] = []
    for base in (ROOT / '.codex', ROOT / '.gemini', ROOT / '.claude', ROOT / '.kiro'):
        if not base.exists():
            continue
        paths.extend(safe_rglob(base, 'SKILL.md'))
        paths.extend(safe_rglob(base, '*.md'))
        paths.extend(safe_rglob(base, '*.toml'))
        paths.extend(safe_rglob(base, '*.json'))
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen or path.name == 'capability.json':
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


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
                cache_path = cached.get('cache_path')
                cache_file = ROOT / str(cache_path) if cache_path else None
                if cache_file and cache_file.exists():
                    warnings.append(f'{message} (using cached artifact)')
                elif strict:
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


def serialize_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2) + '\n'


def report_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')


def write_validation_report(args, validation_errors: list[str], validation_warnings: list[str], checked_sources: list[str], cli_info: dict):
    now = datetime.now(timezone.utc)
    payload = {
        'validated_at': now_iso(),
        'manifest_file': str(META.relative_to(ROOT)),
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
    VALIDATION_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = VALIDATION_REPORT_DIR / f'{report_timestamp(now)}.json'
    archive_path.write_text(serialize_json(payload), encoding='utf-8')
    (VALIDATION_REPORT_DIR / 'latest.json').write_text(serialize_json(payload), encoding='utf-8')
    return payload


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
    ssot_file_paths = sorted(SSOT_DIR.glob('*.md'))
    ssot_files = [p.stem for p in ssot_file_paths]
    ssot_slugs = {p.stem for p in ssot_file_paths}

    if not rules:
        print('No artifact definitions in .meta/surface-rules.json')
        return 2

    manifest = json.loads(META.read_text(encoding='utf-8'))
    manifest_entries = manifest.get('ssot_sources', [])

    errors: list[str] = []
    warnings: list[str] = []

    for rule in rules:
        eligible_slugs = eligible_slugs_for_rule(rule, manifest_entries)
        for slug in sorted(eligible_slugs):
            errors.extend(validate_schema_artifact(rule, slug, args.with_cli, args.strict, warnings))

    # Extra / missing file checks
    expected = {}
    for rule in rules:
        expected_set = set()
        for slug in eligible_slugs_for_rule(rule, manifest_entries):
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
    manifest_ssot = {entry.get('slug') for entry in manifest_entries}
    if manifest_ssot != ssot_slugs:
        errors.append('manifest slugs do not match ssot directory')

    for path in ssot_file_paths:
        errors.extend(validate_ssot_source(path))
        errors.extend(validate_secret_like_literals(path))

    for metadata_path in collect_capability_metadata_paths():
        errors.extend(validate_portable_capability_metadata(metadata_path))
        errors.extend(validate_advisory_policy_metadata(metadata_path))
        errors.extend(validate_secret_like_literals(metadata_path))

    for surface_path in collect_surface_text_paths():
        errors.extend(validate_secret_like_literals(surface_path))

    # CLI existence checks for optional/strict behavior
    cli_errors, cli_warnings = cli_probe_warnings(rules_obj, args)
    errors.extend(cli_errors)
    warnings.extend(cli_warnings)

    cli_info = collect_cli_versions(rules_obj)

    # Always write provenance so callers can see what was used
    write_validation_report(args, errors, warnings, checked_sources, cli_info)

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
