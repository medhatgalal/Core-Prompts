"""Recognize only byte-for-byte reproducible caches of receipt-owned Python files.

Recognition authorizes an explicit journaled retirement, never silent exclusion
from package inventory. Unknown extras continue to preserve the whole package.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import PurePosixPath

from .transaction import identity, safe
from .recovery_fs import file_bytes, content_identity

# Compilation consumes trusted, hash-checked source bytes over stdin. It never
# imports/executes package code, follows a cache-selected source path or writes pyc.
_COMPILER = '''import base64, importlib.util, json, marshal, struct, sys
v = json.load(sys.stdin)
s = base64.b64decode(v['source'])
assert sys.implementation.cache_tag == v['tag']
code = compile(s, v['filename'], 'exec', dont_inherit=True, optimize=v['optimize'])
flags = v['flags']
header = importlib.util.MAGIC_NUMBER + struct.pack('<I', flags)
if flags & 1:
    header += importlib.util.source_hash(s)
else:
    header += struct.pack('<II', v['mtime'] & 0xffffffff, len(s) & 0xffffffff)
sys.stdout.buffer.write(header + marshal.dumps(code))
'''


def _read(path, expected):
    # Acquire even a substituted FIFO without blocking; reject links and special
    # nodes before reading, and verify the held file against the planned identity.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        data, observed = file_bytes(fd)
        return data if content_identity(observed) == expected else None
    finally:
        os.close(fd)


def recognized(target, owned, observed):
    """Return exact cache/source records, or None if any package member conflicts."""
    if not owned or owned.get('kind') != 'skill':
        return None
    files = owned['files']
    if not files or any(observed.get(r) != value for r, value in files.items()):
        return None
    extras = set(observed) - set(files)
    if not extras:
        return []
    records = []
    for rel in sorted(extras):
        path = PurePosixPath(rel)
        match = re.fullmatch(r'(.+)\.(cpython-(3[0-9]{2}))(?:(\.opt-([12])))?\.pyc', path.name)
        if path.parent.name != '__pycache__' or not match:
            return None
        source = str(path.parent.parent / (match[1] + '.py'))
        if source not in files:
            return None
        source_path, cache_path = safe(target, source), safe(target, rel)
        try:
            data, cache = _read(source_path, files[source]), _read(cache_path, observed[rel])
        except (OSError, ValueError):
            return None
        if data is None or cache is None or len(cache) < 16:
            return None
        flags = int.from_bytes(cache[4:8], 'little')
        if flags not in (0, 1, 3):
            return None
        tag = match[2]
        binary = sys.executable if tag == sys.implementation.cache_tag else shutil.which('python3.' + match[3][1:])
        if binary is None:
            return None
        payload = dict(source=base64.b64encode(data).decode(), filename=str(source_path),
                       tag=tag, optimize=int(match[5] or 0), flags=flags, mtime=int(source_path.stat().st_mtime))
        try:
            result = subprocess.run([binary, '-I', '-B', '-c', _COMPILER], input=json.dumps(payload).encode(),
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode or result.stdout != cache or identity(source_path) != files[source] or identity(cache_path) != observed[rel]:
            return None
        records.append(dict(path=rel, before=observed[rel], source=source, source_identity=files[source],
                            reason='byte-for-byte reproducible Python cache; journaled retirement'))
    return records



def check(target, plan, applied=()):
    """Recheck full observed packages against only completed planned mutations.

    In particular, a cache-only transaction must guard its unchanged source even
    when that source is absent from the write actions. Call at retirement and
    ownership boundaries, not just in the earlier replan snapshot.
    """
    from .transaction import InstallError, inventory
    observations = plan.get('cache_observations', {})
    if plan.get('cache_retirements') and not observations:
        raise InstallError('missing cache package guards', 'invalid-plan')
    for observed in observations.values():
        expected = dict(observed['files'])
        roots = observed['roots']
        for action in applied:
            if any(action['path'].startswith(root + '/') for root in roots):
                if action['after'] is None:
                    expected.pop(action['path'], None)
                else:
                    expected[action['path']] = action['after']
        if inventory(target, roots) != expected:
            raise InstallError('cache source or package drift before commit', 'cache-conflict')
