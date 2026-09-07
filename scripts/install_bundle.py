"""Portable runtime inventory for the existing standalone updater bundle.

Rendered dist/consumer-shell views are optional distribution extras, not runtime
inputs. They are absent from tagged Git mirrors and remain untouched by updates."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import stat

MANIFEST = '.meta/install-bundle.json'
ROOTS = ('.codex', '.gemini', '.claude', '.kiro', '.grok',
         '.meta/manifest.json', '.meta/capability-handoff.json', '.meta/capabilities',
         '.meta/install-profiles', 'sources/ssot-baselines',
         'scripts/deploy-copy-plan.py', 'scripts/deploy-profile.py', 'scripts/install_bundle.py',
         'scripts/register-codex-agents.py', 'scripts/deploy-surfaces.sh',
         'scripts/install-local.sh', 'scripts/update-core-prompts.py', 'VERSION', 'RELEASE_SOURCE.env')


def identity(path):
    return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'mode': stat.S_IMODE(path.stat().st_mode)}


def permitted(rel):
    if PurePosixPath(rel).as_posix() != rel or rel == '.codex/config.toml':
        return False
    return rel == MANIFEST or any(rel == root or rel.startswith(root + '/') for root in ROOTS)


def build(root):
    files = {}
    for relative in ROOTS:
        source = root / relative
        paths = sorted(source.rglob('*')) if source.is_dir() else [source]
        for path in paths:
            if not permitted(path.relative_to(root).as_posix()):
                continue
            if path.is_symlink():
                raise ValueError(f'bundle contains symlink: {path}')
            if path.is_file() and path.name != '.DS_Store' and '__pycache__' not in path.parts and path.suffix != '.pyc':
                files[path.relative_to(root).as_posix()] = identity(path)
    (root / MANIFEST).write_text(json.dumps({'schema': 1, 'owner': 'Core-Prompts', 'scope': 'standalone_runtime', 'files': files}, indent=2, sort_keys=True) + '\n')


def verified(root):
    manifest = root / MANIFEST
    payload = json.loads(manifest.read_text())
    if payload.get('schema') != 1 or payload.get('owner') != 'Core-Prompts' or payload.get('scope') != 'standalone_runtime':
        raise ValueError('invalid standalone bundle inventory')
    files = payload['files']
    if not files or not {'VERSION', 'scripts/deploy-profile.py', 'scripts/update-core-prompts.py'} <= files.keys():
        raise ValueError('incomplete standalone bundle inventory')
    for rel, expected in files.items():
        path = root / rel
        if (Path(rel).is_absolute() or '..' in Path(rel).parts or not permitted(rel)
                or any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(root))
                or not path.is_file() or identity(path) != expected):
            raise ValueError(f'standalone bundle identity mismatch: {rel}')
    return {**files, MANIFEST: identity(manifest)}
