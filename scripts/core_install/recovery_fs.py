"""Recovery-only POSIX descriptor operations; ordinary installation never enters here."""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import uuid

from . import transaction as tx

# Capture advertised primitives, not signatures (some supported builtins have no
# inspectable signature). Calls remain dynamic so actual syscall faults are testable.
_PRIMITIVES = {name: getattr(os, name) for name in
               ('open', 'stat', 'mkdir', 'unlink', 'rmdir', 'rename', 'link', 'listdir')}


def capabilities():
    if not getattr(os, 'O_DIRECTORY', 0) or not getattr(os, 'O_NOFOLLOW', 0):
        raise tx.InstallError('recovery requires O_DIRECTORY and O_NOFOLLOW', 'unsupported-recovery')
    if not getattr(os, 'O_NONBLOCK', 0):
        raise tx.InstallError('recovery requires O_NONBLOCK for safe file acquisition', 'unsupported-recovery')
    needed = ('open', 'stat', 'mkdir', 'unlink', 'rmdir', 'rename', 'link')
    if (any(_PRIMITIVES[n] not in os.supports_dir_fd for n in needed)
            or any(_PRIMITIVES[n] not in os.supports_follow_symlinks for n in ('stat', 'link'))
            or _PRIMITIVES['listdir'] not in os.supports_fd):
        raise tx.InstallError('recovery requires POSIX descriptor-relative operations', 'unsupported-recovery')


def parts(rel):
    if (not isinstance(rel, str) or not rel or rel.startswith('/') or '\\' in rel or '\x00' in rel
            or any(p in ('', '.', '..') for p in rel.split('/'))):
        raise tx.InstallError('noncanonical recovery path', 'unsafe-path')
    return rel.split('/')


def directory(info):
    if not stat.S_ISDIR(info.st_mode):
        raise tx.InstallError('recovery directory changed', 'recovery-conflict')
    return dict(device=info.st_dev, inode=info.st_ino, mode=stat.S_IMODE(info.st_mode))


def file_bytes(fd):
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode):
        raise tx.InstallError('recovery file is not regular', 'recovery-conflict')
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    while data := os.read(fd, 65536):
        chunks.append(data)
    data = b''.join(chunks)
    after = os.fstat(fd)
    if (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns):
        raise tx.InstallError('recovery file changed while reading', 'recovery-conflict')
    return data, dict(device=after.st_dev, inode=after.st_ino, mode=stat.S_IMODE(after.st_mode),
                      sha256=hashlib.sha256(data).hexdigest())


def content_identity(identity):
    return None if identity is None else {k: identity[k] for k in ('sha256', 'mode')}


def close_once(fd):
    try:
        os.close(fd)
    except OSError as exc:
        raise tx.InstallError('descriptor close outcome uncertain; not retried', 'cleanup-uncertain') from exc


def own(stack, fd):
    stack.callback(close_once, fd)
    return fd


class Session:
    def __init__(self, target):
        self.target = Path(target).absolute()
        self.stack = ExitStack()
        self.bindings = []
        self.active_bindings = []
        self.expected_directories = {}
        self.anchors = {}
        self.journal_expected = {}
        self.last_save_outcome = None

    def __enter__(self):
        try:
            capabilities()
            fd = own(self.stack, os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW))
            for name in self.target.parts[1:]:
                child = own(self.stack, os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd))
                ident = directory(os.fstat(child))
                self.bindings.append((fd, name, ident))
                fd = child
            self.root = fd
            self.verify()
            # Fixed common anchors retain identity across separate operations.
            # Every preflight precedes even persistent lock creation.
            self.anchors[''] = self.root
            os.fsync(self.root)
            for rel in (tx.STATE, '.grok/skills'):
                os.fsync(self.anchor(rel))
            try:
                os.fsync(self.anchor(tx.TRANSACTIONS))
            except FileNotFoundError:
                pass
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *exc):
        return self.stack.__exit__(*exc)

    def expect_directory(self, rel, identity):
        previous = self.expected_directories.get(rel)
        if previous is not None and previous != identity:
            raise tx.InstallError('recovery directory binding changed: ' + rel, 'recovery-conflict')
        self.expected_directories[rel] = dict(identity)

    def anchor(self, rel):
        fd, prefix = self.root, ''
        for name in parts(rel):
            key = (prefix + '/' + name).lstrip('/')
            if key in self.anchors:
                fd = self.anchors[key]
            else:
                child = own(self.stack, os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd))
                ident = directory(os.fstat(child))
                self.expect_directory(key, ident)
                self.bindings.append((fd, name, ident))
                self.anchors[key] = child
                fd = child
            prefix = key
        self.verify()
        return fd

    def verify(self, extra=()):
        for fd, name, expected in [*self.bindings, *self.active_bindings, *extra]:
            actual = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if directory(actual) != expected:
                raise tx.InstallError('recovery directory namespace changed: ' + name, 'recovery-conflict')

    @contextmanager
    def parent(self, rel):
        components = parts(rel)
        with ExitStack() as stack:
            fd = self.root
            bindings = []
            prefix = []
            self.verify()
            for name in components[:-1]:
                child = own(stack, os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd))
                ident = directory(os.fstat(child))
                prefix.append(name)
                self.expect_directory("/".join(prefix), ident)
                bindings.append((fd, name, ident))
                fd = child
            self.verify(bindings)
            start = len(self.active_bindings)
            self.active_bindings.extend(bindings)
            try:
                yield fd, components[-1]
            finally:
                try:
                    self.verify()
                finally:
                    del self.active_bindings[start:]

    @contextmanager
    def open_directory(self, rel):
        with self.parent(rel) as (parent, name), ExitStack() as stack:
            fd = own(stack, os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent))
            expected = directory(os.fstat(fd))
            self.expect_directory(rel, expected)
            self.verify([(parent, name, expected)])
            try:
                yield fd
            finally:
                self.verify([(parent, name, expected)])

    def read_named(self, parent, name):
        self.verify()
        with ExitStack() as stack:
            fd = own(stack, os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent))
            data, ident = file_bytes(fd)
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode)) !=
                    (ident['device'], ident['inode'], ident['mode'])):
                raise tx.InstallError('recovery named file binding changed', 'recovery-conflict')
            self.verify()
            return data, ident

    def read(self, rel):
        with self.parent(rel) as (fd, name):
            return self.read_named(fd, name)

    def identity(self, rel):
        try:
            return self.read(rel)[1]
        except FileNotFoundError:
            return None

    def dir_identity(self, rel):
        try:
            with self.open_directory(rel) as fd:
                return directory(os.fstat(fd))
        except FileNotFoundError:
            return None

    def names(self, rel):
        with self.open_directory(rel) as fd:
            return sorted(os.listdir(fd))

    def mkdir(self, rel, common=False):
        with self.parent(rel) as (fd, name):
            try:
                os.mkdir(name, dir_fd=fd)
            except FileExistsError:
                if not common:
                    raise
            # mkdir has no returned inode handle: detect observed substitution,
            # without claiming atomic attribution against hostile leaf writers.
            expected = directory(os.stat(name, dir_fd=fd, follow_symlinks=False))
            with ExitStack() as stack:
                child = own(stack, os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd))
                if directory(os.fstat(child)) != expected:
                    raise tx.InstallError('created recovery directory changed', 'recovery-conflict')
                os.fsync(fd)
                self.verify([(fd, name, expected)])
                self.expect_directory(rel, expected)
            return expected

    def lock(self):
        with self.parent(tx.STATE + '/installation.lock') as (parent, name):
            fd = own(self.stack, os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=parent))
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise tx.InstallError('installation lock is not regular', 'unsafe-path')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise tx.InstallError('installation lock is held by another operation', 'locked') from exc
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (not stat.S_ISREG(named.st_mode) or (named.st_dev, named.st_ino) != (info.st_dev, info.st_ino)):
                raise tx.InstallError('installation lock binding changed', 'recovery-conflict')
            os.fsync(parent)

    @contextmanager
    def temporary(self, parent, data, mode, prefix):
        with ExitStack() as stack:
            for _ in range(32):
                name = prefix + uuid.uuid4().hex
                try:
                    fd = own(stack, os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                             0o600, dir_fd=parent))
                    break
                except FileExistsError:
                    continue
            else:
                raise tx.InstallError('recovery temporary name collisions', 'recovery-conflict')
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError('short recovery write')
                view = view[written:]
            os.fchmod(fd, mode)
            os.fsync(fd)
            actual, original = file_bytes(fd)
            if actual != data or content_identity(original) != tx._data_identity(data, mode):
                raise tx.InstallError('recovery staged identity differs', 'invalid-stage')
            self.match_named(parent, name, original)
            yield name, fd, original

    def match_named(self, parent, name, expected):
        actual = self.read_named(parent, name)[1]
        if actual != expected:
            raise tx.InstallError('recovery original inode binding changed: ' + name, 'recovery-conflict')

    def atomic(self, rel, data, mode, expected=None):
        """None means exclusive creation; replacement requires a full prior identity."""
        with self.parent(rel) as (parent, name):
            if expected is not None:
                self.match_named(parent, name, expected)
            with self.temporary(parent, data, mode, '.core-metadata-') as (temp, fd, original):
                os.fsync(parent)
                self.match_named(parent, temp, original)
                if expected is None:
                    os.link(temp, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
                    self.match_named(parent, temp, original)
                else:
                    self.match_named(parent, name, expected)
                    os.rename(temp, name, src_dir_fd=parent, dst_dir_fd=parent)
                self.match_named(parent, name, original)
                if file_bytes(fd)[1] != original:
                    raise tx.InstallError('held replacement inode changed', 'recovery-conflict')
                os.fsync(parent)
                self.match_named(parent, name, original)
                if expected is None:
                    self.match_named(parent, temp, original)
                    os.unlink(temp, dir_fd=parent)
                    os.fsync(parent)
                return original

    def save(self, journal):
        rel = f"{tx.TRANSACTIONS}/{journal['transaction']}/journal.json"
        expected = self.journal_expected.get(rel)
        try:
            actual = self.atomic(rel, tx.encoded(journal), 0o600, expected)
        except BaseException:
            # Saving can fail after rename. Inspect actual anchored state; never
            # retry using an assumed old identity or manufacture a durable fact.
            try:
                data, ident = self.read(rel)
                self.last_save_outcome = dict(identity=ident, content_sha256=hashlib.sha256(data).hexdigest())
            except BaseException:
                self.last_save_outcome = 'unreadable-or-ambiguous'
            raise
        self.journal_expected[rel] = actual

    def unlink(self, rel, expected):
        with self.parent(rel) as (parent, name):
            self.match_named(parent, name, expected)
            os.unlink(name, dir_fd=parent)
            os.fsync(parent)

    def rmdir(self, rel, expected):
        with self.parent(rel) as (parent, name):
            if directory(os.stat(name, dir_fd=parent, follow_symlinks=False)) != expected:
                raise tx.InstallError('recovery directory changed', 'recovery-conflict')
            with self.open_directory(rel) as fd:
                if os.listdir(fd):
                    raise tx.InstallError('recovery directory is not empty', 'recovery-conflict')
            os.rmdir(name, dir_fd=parent)
            os.fsync(parent)
