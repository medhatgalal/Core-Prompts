"""Observe the shared namespace without following unrelated package links."""
from __future__ import annotations

import os
import stat

from .transaction import safe


def node_identity(info):
    return dict(device=info.st_dev, inode=info.st_ino, mode=stat.S_IMODE(info.st_mode),
                mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)


def shared_root(target):
    root = '.agents/skills'
    try:
        path = safe(target, root)
        if not path.exists():
            return dict(root=root, status='absent', identity=None, entries={})
        if not path.is_dir():
            raise ValueError('shared skill root is not a directory')
        entries = {}
        for child in sorted(path.iterdir()):
            info = child.lstat()
            kind = ('link' if stat.S_ISLNK(info.st_mode) else
                    'directory' if stat.S_ISDIR(info.st_mode) else
                    'file' if stat.S_ISREG(info.st_mode) else 'other')
            entry = dict(type=kind, identity=node_identity(info))
            if kind == 'link':
                entry['target'] = os.readlink(child)
                after = child.lstat()
                if not stat.S_ISLNK(after.st_mode) or node_identity(after) != node_identity(info):
                    raise ValueError('shared link changed during observation: ' + child.name)
            entries[child.name] = entry
        return dict(root=root, status='observed', identity=node_identity(path.lstat()), entries=entries)
    except (OSError, ValueError) as exc:
        return dict(root=root, status='error', identity=None, entries=None, error=str(exc))


def slots(observation):
    if observation['status'] == 'error':
        return None
    return sorted(name for name, entry in observation['entries'].items()
                  if entry['type'] in ('directory', 'link'))
