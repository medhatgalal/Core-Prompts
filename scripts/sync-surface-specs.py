#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / '.meta' / 'surface-rules.json'
CACHE_DIR = ROOT / '.meta' / 'schema-cache'
CACHE_MANIFEST = CACHE_DIR / 'manifest.json'


def safe_cache_name(url: str) -> str:
    hashed = hashlib.sha256(url.encode('utf-8')).hexdigest()[:24]
    slug = re.sub(r'[^A-Za-z0-9._-]+', '_', url)
    slug = slug[:48].strip('_.') or 'url'
    return f'{slug}_{hashed}.json'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def fetch_url(url: str, timeout: int = 20) -> Dict[str, Any]:
    req = Request(url, headers={
        'User-Agent': 'Core-Prompts Schema Sync (Python urllib)'
    })
    with urlopen(req, timeout=timeout, context=ssl._create_unverified_context()) as resp:
        status = getattr(resp, 'status', 200)
        payload = resp.read()
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return {
            'status': status,
            'ok': 200 <= status < 300,
            'status_text': getattr(resp, 'reason', ''),
            'url': str(resp.url),
            'headers': {
                'content_type': headers.get('content-type'),
                'etag': headers.get('etag'),
                'last_modified': headers.get('last-modified'),
                'cache_control': headers.get('cache-control'),
            },
            'content': payload,
            'content_length': len(payload),
        }


def load_rules() -> dict:
    if not RULES_PATH.exists():
        raise SystemExit(f'Missing rules file: {RULES_PATH}')
    return json.loads(RULES_PATH.read_text(encoding='utf-8'))


def collect_sources(rule_obj: dict):
    urls = list(rule_obj.get('source_urls') or [])
    if not urls:
        return []
    # Normalize duplicates for deterministic output
    seen = set()
    out = []
    for u in urls:
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Sync LLM CLI surface schema references from docs.')
    parser.add_argument('--refresh', action='store_true', help='re-fetch URLs even when cache exists')
    parser.add_argument('--strict', action='store_true', help='fail fast on fetch failures')
    parser.add_argument('--timeout', type=int, default=20)
    args = parser.parse_args(argv)

    rules = load_rules()
    cache_dir = CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    source_urls = set()
    for rule in rules.get('artifacts', []):
        for u in collect_sources(rule):
            source_urls.add(u)

    manifest = load_json(CACHE_MANIFEST, {'generated_at': None, 'entries': []})
    existing = {e.get('url'): e for e in manifest.get('entries', []) if isinstance(e, dict)}

    entries = []
    failed = []

    for url in sorted(source_urls):
        entry = existing.get(url, {}).copy()
        cache_file_name = safe_cache_name(url)
        cache_file = cache_dir / cache_file_name
        should_fetch = args.refresh or not cache_file.exists() or 'fetched_at' not in entry

        if should_fetch:
            try:
                data = fetch_url(url, timeout=args.timeout)
                checksum = sha256_bytes(data['content'])
                snippet = data['content'][:2000].decode('utf-8', errors='replace')
                title_match = re.search(r'<title>(.*?)</title>', snippet, flags=re.I | re.S)
                payload = {
                    'url': data['url'],
                    'status': data['status'],
                    'status_text': data['status_text'],
                    'ok': bool(data['ok']),
                    'checksum': checksum,
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'content_length': data['content_length'],
                    'headers': data['headers'],
                    'cache_path': str(cache_file.relative_to(ROOT)),
                    'title': title_match.group(1).strip() if title_match else None,
                    'snippet': snippet[:300].replace('\n', ' ').strip()
                }
                cache_file.write_text(payload['checksum'] + '\n', encoding='utf-8')
                entries.append(payload)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                payload = {
                    'url': url,
                    'ok': False,
                    'error': str(exc),
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'cache_path': str(cache_file.relative_to(ROOT)),
                }
                if cache_file.exists():
                    payload['cache_path'] = str(cache_file.relative_to(ROOT))
                    payload['reused_cache'] = True
                failed.append(url)
                entries.append(payload)
            except Exception as exc:  # defensive
                entries.append({
                    'url': url,
                    'ok': False,
                    'error': f'{type(exc).__name__}: {exc}',
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'cache_path': str(cache_file.relative_to(ROOT)),
                })
                failed.append(url)
                entries.append(entries[-1])
        else:
            entries.append(entry)

    out = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'entries': entries,
        'source_count': len(entries),
    }
    CACHE_MANIFEST.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')

    if failed and args.strict:
        print('Schema sync failed for URLs:')
        for u in failed:
            print(f'- {u}')
        return 2

    print(f'synced {len(entries)} schema-source URLs into {CACHE_MANIFEST}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
