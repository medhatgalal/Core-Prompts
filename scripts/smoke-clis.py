#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path
import json
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / '.meta' / 'surface-rules.json'
MANIFEST_PATH = ROOT / '.meta' / 'manifest.json'
SMOKE_REPORT_DIR = ROOT / 'reports' / 'smoke-clis'


def load_rules() -> dict:
    if not RULES_PATH.exists():
        raise SystemExit(f'Missing rules file: {RULES_PATH}')
    return json.loads(RULES_PATH.read_text(encoding='utf-8'))


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f'Missing manifest file: {MANIFEST_PATH}')
    return json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))


def run_probe(
    command: list[str],
    timeout: int = 15,
    max_chars: int | None = 4000,
    capture_mode: str = 'pipe',
) -> tuple[int, str]:
    if capture_mode == 'file':
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as handle:
            proc = subprocess.run(
                command,
                stdout=handle,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
            handle.seek(0)
            out = handle.read().strip()
    else:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        out = proc.stdout.strip()
    if max_chars is not None and len(out) > max_chars:
        out = out[:max_chars] + '...'
    return proc.returncode, out


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def is_approval_gated_output(text: str) -> bool:
    normalized = text.casefold()
    return (
        'need your permission to run this script' in normalized
        or 'need your permission to run the `claude agents` command' in normalized
        or 'requires approval because' in normalized
        or ('permission' in normalized and 'approval' in normalized and 'claude agents' in normalized)
        or 'would you like me to proceed?' in normalized
    )


def artifact_rules_by_name(rules: dict) -> dict[str, dict]:
    return {item['name']: item for item in rules.get('artifacts', []) if item.get('name')}


def expected_artifact_paths(manifest: dict, artifact_rules: dict[str, dict], tool_surface: str) -> list[str]:
    paths: list[str] = []
    for entry in manifest.get('ssot_sources', []):
        slug = entry.get('slug')
        if not slug:
            continue
        for surface_name in entry.get('expected_surface_names', []):
            rule = artifact_rules.get(surface_name)
            if not rule or rule.get('surface') != tool_surface:
                continue
            template = str(rule.get('path') or '')
            if template:
                paths.append(template.format(slug=slug))
    return sorted(dict.fromkeys(paths))


def expected_discovery_slugs(manifest: dict, surface_names: list[str]) -> list[str]:
    slugs: list[str] = []
    expected = set(surface_names)
    for entry in manifest.get('ssot_sources', []):
        surfaces = set(entry.get('expected_surface_names') or [])
        if surfaces & expected and entry.get('slug'):
            slugs.append(str(entry['slug']))
    return sorted(dict.fromkeys(slugs))


def discovery_pattern_builder(tool_name: str):
    if tool_name == 'gemini':
        return lambda slug: rf'^\s*{re.escape(slug)}\s+\[.+\]'
    if tool_name == 'claude':
        return lambda slug: rf'^\s+{re.escape(slug)}\s+·'
    if tool_name == 'kiro':
        return lambda slug: rf'^\s+{re.escape(slug)}\s+(Workspace|Global)\b'
    return None


def assert_discovery(
    name: str,
    command: list[str],
    expected_slugs: list[str],
    output: str,
    pattern_builder,
):
    missing = []
    for slug in expected_slugs:
        pattern = pattern_builder(slug)
        if not re.search(pattern, output, flags=re.MULTILINE):
            missing.append(slug)
    return {
        'tool': name,
        'command': 'discovery',
        'run': ' '.join(command),
        'status': 'ok' if not missing else 'error',
        'missing': missing,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Smoke CLI startup checks for known vendors.')
    parser.add_argument('--strict', action='store_true', help='treat missing/failed probes as hard failure')
    parser.add_argument('--smoke-timeout', type=int, default=15)
    args = parser.parse_args(argv)

    rules = load_rules()
    manifest = load_manifest()
    tools = rules.get('tooling', [])
    artifact_rules = artifact_rules_by_name(rules)

    failures: list[str] = []
    warnings: list[str] = []
    report = {
        'smoked_at': datetime.now(timezone.utc).isoformat(),
        'results': [],
        'warnings': warnings,
        'failures': failures,
    }

    for tool in tools:
        name = tool.get('name')
        binary = tool.get('command')
        required = bool(tool.get('required', False))
        smoke_args = tool.get('smoke_args') or ['--help']
        version_args = tool.get('version_args') or ['--version']
        tool_surface = str(tool.get('surface') or name)

        if shutil.which(binary) is None:
            msg = f'{name}: missing executable ({binary})'
            if required or args.strict:
                failures.append(msg)
            else:
                warnings.append(msg)
            report['results'].append({'tool': name, 'status': 'missing'})
            continue

        try:
            code, out = run_probe([binary] + version_args, timeout=args.smoke_timeout)
            report['results'].append({'tool': name, 'command': 'version', 'status': 'ok' if code == 0 else 'error', 'code': code, 'output': out})
        except Exception as exc:
            report['results'].append({'tool': name, 'command': 'version', 'status': 'error', 'error': str(exc)})
            warnings.append(f'{name}: version probe failed ({exc})')

        try:
            code, out = run_probe([binary] + smoke_args, timeout=args.smoke_timeout)
            report['results'].append({'tool': name, 'command': 'smoke', 'status': 'ok' if code == 0 else 'error', 'code': code, 'output': out})
            if code != 0 and (required or args.strict):
                failures.append(f'{name}: smoke command returned {code}')
        except Exception as exc:
            report['results'].append({'tool': name, 'command': 'smoke', 'status': 'error', 'error': str(exc)})
            if required or args.strict:
                failures.append(f'{name}: smoke probe failed ({exc})')

        expected_files = expected_artifact_paths(manifest, artifact_rules, tool_surface)
        missing_files = [path for path in expected_files if not (ROOT / path).exists()]
        report['results'].append(
            {
                'tool': name,
                'command': 'filesystem',
                'status': 'ok' if not missing_files else 'error',
                'missing': missing_files,
                'checked_count': len(expected_files),
            }
        )
        if missing_files:
            msg = f'{name}: missing generated surface files ({", ".join(missing_files[:8])})'
            if required or args.strict:
                failures.append(msg)
            else:
                warnings.append(msg)

        discovery_enabled = bool(tool.get('discovery_enabled', True))
        discovery_args = tool.get('discovery_args') or []
        discovery_surface_names = list(tool.get('discovery_surface_names') or [])
        discovery_timeout = int(tool.get('discovery_timeout_seconds') or args.smoke_timeout)
        normalize = strip_ansi if tool.get('discovery_strip_ansi') else (lambda s: s)
        expected_slugs = expected_discovery_slugs(manifest, discovery_surface_names)
        pattern_builder = discovery_pattern_builder(name)

        if discovery_enabled and discovery_args and pattern_builder and expected_slugs:
            discovery_cmd = [binary, *discovery_args]
            try:
                capture_mode = 'file' if name == 'gemini' else 'pipe'
                code, out = run_probe(
                    discovery_cmd,
                    timeout=discovery_timeout,
                    max_chars=100000,
                    capture_mode=capture_mode,
                )
                clean_out = normalize(out)
                if code != 0:
                    msg = f'{name}: discovery command returned {code}'
                    if required or args.strict:
                        failures.append(msg)
                    else:
                        warnings.append(msg)
                elif is_approval_gated_output(clean_out):
                    report['results'].append(
                        {
                            'tool': name,
                            'command': 'discovery',
                            'status': 'skipped',
                            'reason': 'approval_gated',
                            'expected_surface_names': discovery_surface_names,
                        }
                    )
                    continue
                discovery_result = assert_discovery(name, discovery_cmd, expected_slugs, clean_out, pattern_builder)
                discovery_result['expected_surface_names'] = discovery_surface_names
                report['results'].append(discovery_result)
                if discovery_result['status'] != 'ok':
                    msg = f'{name}: missing generated slugs in discovery output ({", ".join(discovery_result["missing"])})'
                    if required or args.strict:
                        failures.append(msg)
                    else:
                        warnings.append(msg)
            except Exception as exc:
                report['results'].append({'tool': name, 'command': 'discovery', 'status': 'error', 'error': str(exc)})
                if required or args.strict:
                    failures.append(f'{name}: discovery probe failed ({exc})')
                else:
                    warnings.append(f'{name}: discovery probe failed ({exc})')
        else:
            report['results'].append(
                {
                    'tool': name,
                    'command': 'discovery',
                    'status': 'skipped',
                    'reason': 'discovery disabled'
                    if not discovery_enabled
                    else ('no configured discovery surfaces' if not discovery_surface_names else 'no matching manifest surfaces'),
                    'expected_surface_names': discovery_surface_names,
                }
            )

    if warnings:
        for warning in warnings:
            print(f'warning: {warning}')

    report['warnings'] = list(warnings)
    report['failures'] = list(failures)
    write_smoke_report(report)

    if failures:
        print('smoke check failed:')
        for fail in failures:
            print(f'- {fail}')
        return 2

    print('Smoke checks complete.')
    return 0


def report_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')


def write_smoke_report(payload: dict) -> None:
    now = datetime.now(timezone.utc)
    SMOKE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2) + '\n'
    (SMOKE_REPORT_DIR / f'{report_timestamp(now)}.json').write_text(rendered, encoding='utf-8')
    (SMOKE_REPORT_DIR / 'latest.json').write_text(rendered, encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
