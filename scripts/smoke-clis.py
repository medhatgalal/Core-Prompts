#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any
import json
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / '.meta' / 'surface-rules.json'


def load_rules() -> dict:
    if not RULES_PATH.exists():
        raise SystemExit(f'Missing rules file: {RULES_PATH}')
    return json.loads(RULES_PATH.read_text(encoding='utf-8'))


def run_probe(command: list[str], timeout: int = 15) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    out = proc.stdout.strip()
    if len(out) > 4000:
        out = out[:4000] + '...'
    return proc.returncode, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Smoke CLI startup checks for known vendors.')
    parser.add_argument('--strict', action='store_true', help='treat missing/failed probes as hard failure')
    parser.add_argument('--smoke-timeout', type=int, default=15)
    args = parser.parse_args(argv)

    rules = load_rules()
    tools = rules.get('tooling', [])

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
