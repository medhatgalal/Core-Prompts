#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
import json
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / '.meta' / 'surface-rules.json'
SSOT_DIR = ROOT / 'ssot'


def load_rules() -> dict:
    if not RULES_PATH.exists():
        raise SystemExit(f'Missing rules file: {RULES_PATH}')
    return json.loads(RULES_PATH.read_text(encoding='utf-8'))


def run_probe(command: list[str], timeout: int = 15, max_chars: int | None = 4000) -> tuple[int, str]:
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


def load_expected_slugs() -> list[str]:
    slugs: list[str] = []
    for path in sorted(SSOT_DIR.glob('*.md')):
        text = path.read_text(encoding='utf-8')
        slug = path.stem
        if text.startswith('---\n'):
            end = text.find('\n---', 3)
            if end != -1:
                front = text[4:end]
                for line in front.splitlines():
                    line = line.strip()
                    if line.startswith('name:'):
                        value = line.split(':', 1)[1].strip().strip('"').strip("'")
                        if value:
                            slug = value
                        break
        slugs.append(slug)
    return sorted(set(slugs))


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


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
    tools = rules.get('tooling', [])
    expected_slugs = load_expected_slugs()

    failures: list[str] = []
    warnings: list[str] = []
    report = {
        'smoked_at': datetime.now(timezone.utc).isoformat(),
        'results': [],
    }

    for tool in tools:
        name = tool.get('name')
        binary = tool.get('command')
        required = bool(tool.get('required', False))
        smoke_args = tool.get('smoke_args') or ['--help']
        version_args = tool.get('version_args') or ['--version']

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

        # Check that generated skill/agent surfaces are discoverable in local CLIs.
        discovery_cmd: list[str] | None = None
        pattern_builder = None
        normalize = lambda s: s
        if name == 'gemini':
            discovery_cmd = [binary, 'skills', 'list']
            pattern_builder = lambda slug: rf'^\s*{re.escape(slug)}\s+\[.+\]'
        elif name == 'claude':
            discovery_cmd = [binary, 'agents']
            pattern_builder = lambda slug: rf'^\s+{re.escape(slug)}\s+·'
        elif name == 'kiro':
            discovery_cmd = [binary, 'agent', 'list']
            pattern_builder = lambda slug: rf'^\s+{re.escape(slug)}\s+(Workspace|Global)\b'
            normalize = strip_ansi

        if discovery_cmd and pattern_builder:
            try:
                code, out = run_probe(discovery_cmd, timeout=args.smoke_timeout, max_chars=100000)
                clean_out = normalize(out)
                if code != 0:
                    msg = f'{name}: discovery command returned {code}'
                    if required or args.strict:
                        failures.append(msg)
                    else:
                        warnings.append(msg)
                discovery_result = assert_discovery(name, discovery_cmd, expected_slugs, clean_out, pattern_builder)
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

    if warnings:
        for warning in warnings:
            print(f'warning: {warning}')

    if failures:
        print('smoke check failed:')
        for fail in failures:
            print(f'- {fail}')
        return 2

    print('Smoke checks complete.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
