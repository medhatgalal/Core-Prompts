#!/usr/bin/env python3
"""Read-only, externally pinned current committed-candidate binding. Not a review."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def strict(data):
    return json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


class ReadSet:
    """Hold nofollow path chains and file descriptors; recheck identity and bytes."""
    def __init__(self):
        self.fds, self.chain, self.files = [], [], []

    def directory(self, path):
        path = Path(os.path.abspath(path))
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.fds.append(fd)
        for name in path.parts[1:]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            self.fds.append(child); self.chain.append((fd, name, child)); fd = child
        return fd

    def file(self, path):
        path = Path(os.path.abspath(path))
        return self.read(self.directory(path.parent), path.name)

    def read(self, parent, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        self.fds.append(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('regular single-link file required')
        data = self.bytes(fd)
        self.files.append((parent, name, fd, info.st_dev, info.st_ino, data))
        return data

    @staticmethod
    def bytes(fd):
        os.lseek(fd, 0, os.SEEK_SET)
        with os.fdopen(os.dup(fd), 'rb') as stream:
            return stream.read()

    def recheck(self):
        for parent, name, fd in self.chain:
            a, b = os.stat(name, dir_fd=parent, follow_symlinks=False), os.fstat(fd)
            if not stat.S_ISDIR(a.st_mode) or (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
                raise ValueError('directory identity changed')
        for parent, name, fd, dev, ino, data in self.files:
            a, b = os.stat(name, dir_fd=parent, follow_symlinks=False), os.fstat(fd)
            if any(not stat.S_ISREG(v.st_mode) or v.st_nlink != 1 or
                   (v.st_dev, v.st_ino) != (dev, ino) or v.st_size != len(data) for v in (a, b)):
                raise ValueError('file identity changed')
            if self.bytes(fd) != data:
                raise ValueError('file bytes changed')

    def close(self):
        for fd in reversed(self.fds):
            os.close(fd)


class DigestSink:
    def __init__(self, producer):
        self.producer, self.refs = producer, {}

    def write(self, path, data):
        if not (path in {'diff.patch', 'stat.numstat', 'changes.raw'} or
                re.fullmatch(r'objects/(?:[0-9a-f]{40}|[0-9a-f]{64})\.(?:blob|commit)', path)):
            raise ValueError('replay artifact path')
        ref = {'path': path, 'sha256': digest(data), 'bytes': len(data)}
        if path in self.refs and self.refs[path] != ref:
            raise ValueError('artifact collision')
        self.refs[path] = ref
        return ref


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(3, 'verify-review-package: invalid invocation: ' + message + '\n')


def current(git, expected, length):
    # Git status can run a clean/process driver and trust its transformed bytes.
    # Reject effective configured drivers before any worktree comparison; merely
    # clearing the driver would silently change repository comparison semantics.
    # Git.command already disables fsmonitor, hooks, external diffs and global/
    # system config, and excludes inherited GIT_* config overrides.
    filters = git.execute(['config', '--null', '--get-regexp', r'^filter\..*\.(clean|process)$'])
    if filters.returncode not in (0, 1) or (filters.returncode == 1 and filters.stdout):
        raise ValueError('filter configuration unavailable')
    if filters.returncode == 0:
        if not filters.stdout or not filters.stdout.endswith(b'\0'):
            raise ValueError('filter configuration malformed')
        for record in filters.stdout[:-1].split(b'\0'):
            name, separator, value = record.partition(b'\n')
            if not separator or not re.fullmatch(rb'filter\..*\.(clean|process)', name):
                raise ValueError('filter configuration malformed')
            if value:
                raise ValueError('configured clean/process filters unsupported for read-only current candidate')
    ref = expected['candidate_ref']
    if ref != 'HEAD':
        git.read(['check-ref-format', ref], 'candidate_ref')
    actual = git.oid(git.read(['rev-parse', '--verify', ref + '^{commit}'], 'candidate_ref'), 'candidate_ref', length)
    if actual != expected['head']:
        raise ValueError('candidate ref moved')
    sparse = git.execute(['config', '--bool', '--get', 'core.sparseCheckout'])
    if sparse.returncode not in (0, 1) or (sparse.returncode == 0 and sparse.stdout != b'false\n'):
        raise ValueError('sparse checkout unsupported')
    flags = git.read(['ls-files', '-v', '-z'], 'index_flags').split(b'\0')
    if any(row and (row[:1] == b'S' or row[:1].islower() or len(row) < 3 or row[1:2] != b' ') for row in flags):
        raise ValueError('hidden or malformed index flags')
    staged = git.read(['diff', '--cached', '--raw', '-z', '--no-abbrev', '--ignore-submodules=none',
                       '--submodule=short', expected['head'], '--'], 'staged_candidate')
    status = git.read(['status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=all'], 'candidate_status')
    if staged or status:
        raise ValueError('current candidate has staged, unstaged or untracked changes')


def main(argv=None):
    parser = Parser(allow_abbrev=False)
    for name in ('repo', 'package', 'result', 'expect', 'expect-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    reads = ReadSet(); manifest_hash = None; code = 'invalid_expectation'; exit_code = 3
    try:
        if not re.fullmatch('[0-9a-f]{64}', args.expect_sha256):
            raise ValueError('external expectation digest required')
        package_path = Path(os.path.abspath(args.package))
        for external in (args.expect, args.result):
            if Path(os.path.abspath(external)).is_relative_to(package_path):
                raise ValueError('expectation/result must be outside package')
        expectation_bytes = reads.file(args.expect)
        if digest(expectation_bytes) != args.expect_sha256:
            raise ValueError('expectation digest mismatch')
        expected = strict(expectation_bytes)
        root = Path(__file__).resolve().parent.parent
        paths = [root/'scripts/review_package.py', root/'schemas/review-package.schema.json', root/'resource-map.json',
                 Path(__file__).resolve(), root/'schemas/review-package-expectation.schema.json']
        source_bytes = [reads.file(p) for p in paths]
        pinned = [expected['producer'][k] for k in ('script_sha256', 'schema_sha256', 'resource_map_sha256')]
        pinned += [expected['verifier'][k] for k in ('script_sha256', 'expectation_schema_sha256')]
        if [digest(b) for b in source_bytes] != pinned:
            raise ValueError('trusted source binding mismatch')
        # Load exact already checked bytes, never caller cwd, package code or sibling lookup.
        producer = types.ModuleType('trusted_review_package'); producer.__file__ = str(paths[0])
        exec(compile(source_bytes[0], str(paths[0]), 'exec'), producer.__dict__)
        producer.platform_preflight()
        producer.shape(expected, strict(source_bytes[4]))
        if type(expected['collector_exit_code']) is not int or expected['collector_exit_code'] != 0:
            raise ValueError('collector exit must be actual integer zero')
        _, selected_bytes, schema = producer.source_snapshot()
        if selected_bytes != source_bytes[:3]:
            raise ValueError('source drift')
        exit_code = 2; code = 'binding_rejected'
        result_bytes = reads.file(args.result)
        if digest(result_bytes) != expected['collection_result_sha256']:
            raise ValueError('collector stdout digest mismatch')
        result = strict(result_bytes)
        wanted_result = {'schema_version':'ReviewPackageResult.v1','status':'complete',
                         'manifest':'manifest.json','manifest_sha256':expected['manifest_sha256']}
        if result != wanted_result or type(result) is not dict:
            raise ValueError('invalid collector result')
        package_fd = reads.directory(args.package)
        objects_fd = reads.directory(package_path/'objects')
        manifest_bytes = reads.read(package_fd, 'manifest.json'); manifest_hash = digest(manifest_bytes)
        if manifest_hash != expected['manifest_sha256']:
            raise ValueError('manifest digest mismatch')
        manifest = strict(manifest_bytes); producer.shape(manifest, schema)
        for key in ('task', 'repository', 'base', 'head', 'spec_sha256', 'plan_sha256', 'producer'):
            if producer.canonical(manifest[key]) != producer.canonical(expected[key]):
                raise ValueError('expected '+key+' mismatch')
        if (manifest['status'] != 'complete' or not manifest['target_resolved'] or manifest['collection_errors'] or
            manifest['target_kind'] != 'committed_range' or manifest['comparison'] != 'range' or
            manifest['included_change_classes'] != ['committed']):
            raise ValueError('incomplete or noncommitted package')
        invocation = types.SimpleNamespace(repo=args.repo, base=expected['base'], head=expected['head'],
            task_id=expected['task']['id'], owner=expected['task']['owner'], generation=expected['task']['generation'],
            repository_id=expected['repository']['id'], spec_sha256=expected['spec_sha256'], plan_sha256=expected['plan_sha256'])
        git, top, admin, algorithm = producer.repository_preflight(invocation)
        current(git, expected, 40 if algorithm == 'sha1' else 64)
        replay = producer.manifest_factory(invocation, admin, algorithm, source_bytes[:3], schema)
        sink = DigestSink(producer); producer.collect(invocation, git, sink, replay, algorithm)
        replay['status'] = 'incomplete' if replay['collection_errors'] else 'complete'
        if replay != manifest or replay['status'] != 'complete':
            raise ValueError('source replay mismatch')
        expected_names = {'objects', 'manifest.json'} | {p for p in sink.refs if '/' not in p}
        object_names = {p.split('/')[1] for p in sink.refs if '/' in p}
        def membership():
            if set(os.listdir(package_fd)) != expected_names or set(os.listdir(objects_fd)) != object_names:
                raise ValueError('unexpected or missing package member')
        membership()
        for path, ref in sink.refs.items():
            data = reads.read(objects_fd if '/' in path else package_fd, path.split('/')[-1])
            if len(data) != ref['bytes'] or digest(data) != ref['sha256']:
                raise ValueError('artifact integrity mismatch')
        current(git, expected, 40 if algorithm == 'sha1' else 64)
        membership(); reads.recheck()
        payload = {'schema_version':'ReviewPackageBinding.v1','binding_status':'matched',
            'expectation_sha256':args.expect_sha256,'manifest_sha256':manifest_hash,'review_status':'not_assessed','errors':[]}
        print(json.dumps(payload, separators=(',', ':'), sort_keys=True)); return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as error:
        payload = {'schema_version':'ReviewPackageBinding.v1','binding_status':'unverified' if exit_code == 3 else 'rejected',
            'expectation_sha256':args.expect_sha256,'manifest_sha256':manifest_hash,'review_status':'not_assessed',
            'errors':[{'code':code,'message':('Required evidence could not be safely read.' if isinstance(error, OSError) else str(error))}]}
        print(json.dumps(payload, separators=(',', ':'), sort_keys=True)); return exit_code
    except Exception:
        print(json.dumps({'schema_version':'ReviewPackageBinding.v1','binding_status':'unverified',
            'expectation_sha256':args.expect_sha256,'manifest_sha256':manifest_hash,'review_status':'not_assessed',
            'errors':[{'code':'context_unavailable','message':'Required trusted runtime or repository context unavailable.'}]}))
        return 3
    finally:
        reads.close()


if __name__ == '__main__':
    sys.exit(main())
