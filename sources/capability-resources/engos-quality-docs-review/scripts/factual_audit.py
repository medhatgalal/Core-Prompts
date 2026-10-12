#!/usr/bin/env python3
"""Read-only validation and identity roundtrip of two legacy factual audit forms."""
import argparse
import json
import math
import sys
from pathlib import Path

FORMATS = ('master-array', 'prompt-e-object')
STATUSES = ('verified', 'needs_revision', 'unclear')


def validate(payload, source_format):
    issues = []

    def issue(path, code, message):
        issues.append(dict(path=path, code=code, message=message))

    def fields(value, required, path):
        if not isinstance(value, dict):
            issue(path, 'type', 'Expected object')
            return
        for key, expected in required.items():
            at = path + '/' + key
            if key not in value:
                issue(at, 'required', 'Missing field')
                continue
            v = value[key]
            if expected == 'string':
                valid = isinstance(v, str)
            elif expected == 'paths':
                valid = isinstance(v, list) and all(isinstance(x, str) for x in v)
            elif expected == 'status':
                valid = isinstance(v, str) and v in STATUSES
            else:
                valid = type(v) is int and v >= 0
            if not valid:
                issue(at, 'type_or_value', 'Invalid known field type or value')

    if source_format not in FORMATS:
        issue('/', 'format', 'Unsupported explicit source format')
        return issues
    if source_format == 'master-array':
        items, at = payload, ''
        required = dict(claim='string', source_paths='paths', status='status', rewrite_if_needed='string')
    else:
        if not isinstance(payload, dict):
            issue('/', 'type', 'Expected object')
            return issues
        for key in ('summary', 'items'):
            if key not in payload:
                issue('/' + key, 'required', 'Missing field')
        summary = payload.get('summary')
        fields(summary, dict.fromkeys(('total_claims',) + STATUSES, 'count'), '/summary')
        items, at = payload.get('items'), '/items'
        required = dict(claim='string', file='string', status='status', source_paths='paths', issue='string', safe_rewrite='string')
    if not isinstance(items, list):
        issue(at or '/', 'type', 'Expected array')
        return issues
    for i, item in enumerate(items):
        fields(item, required, at + '/' + str(i))
    if source_format == 'prompt-e-object' and isinstance(summary, dict):
        counts = {'total_claims': len(items)}
        counts.update({s: sum(isinstance(i, dict) and i.get('status') == s for i in items) for s in STATUSES})
        for key, expected in counts.items():
            if type(summary.get(key)) is int and summary[key] >= 0 and summary[key] != expected:
                issue('/summary/' + key, 'count_mismatch', 'Count does not match items')
    return issues


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate object key')
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('Nonfinite JSON number')


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite JSON number")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('validate', 'roundtrip'))
    parser.add_argument('--format', required=True, choices=FORMATS)
    parser.add_argument('--input', required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        data = Path(args.input).read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        report = dict(format=args.format, valid=False, issues=[dict(path='/', code='io', message='Cannot read UTF-8 input')])
        print(json.dumps(report), file=sys.stderr if args.command == 'roundtrip' else sys.stdout)
        return 3
    try:
        payload = json.loads(data, object_pairs_hook=_pairs, parse_constant=_nonfinite, parse_float=_finite_float)
        issues = validate(payload, args.format)
    except (ValueError, RecursionError):
        issues = [dict(path='/', code='json', message='Malformed, duplicate-key or nonfinite JSON')]
    report = dict(format=args.format, valid=not issues, issues=issues)
    if args.command == 'validate':
        print(json.dumps(report))
    elif issues:
        print(json.dumps(report), file=sys.stderr)
    else:
        print(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    return 2 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
