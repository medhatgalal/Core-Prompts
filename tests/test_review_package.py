"""Real Git producer fixtures; Git is a required test prerequisite, never skipped."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import types
import errno

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'sources/capability-resources/engos-quality-code-review'
SCRIPT = SOURCE / 'scripts/review_package.py'

@pytest.fixture
def git_repo(tmp_path):
    assert shutil.which('git'), 'Git is required by ReviewPackage producer fixtures'
    repo = tmp_path / 'repo'; repo.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)
    git('init', '-q'); git('config', 'user.name', 'Fixture'); git('config', 'user.email', 'fixture@example.invalid')
    (repo / 'a').write_text('base\n'); git('add', '.'); git('commit', '-qm', 'base')
    base = git('rev-parse', 'HEAD').decode().strip()
    return repo, git, base


def invoke(repo, base, head, out, *extra):
    return subprocess.run([sys.executable, '-I', str(SCRIPT), '--repo', str(repo), '--base', base,
        '--head', head, '--out', str(out), '--task-id', 'D6.S2', '--owner', 'fixture',
        '--generation', '1', '--repository-id', 'fixture-repo', *extra], capture_output=True)


def package(result, out, status='complete'):
    assert result.returncode == (0 if status == 'complete' else 2), result.stderr
    receipt = json.loads(result.stdout)
    data = (out / 'manifest.json').read_bytes()
    assert receipt == {'schema_version': 'ReviewPackageResult.v1', 'status': status,
        'manifest': 'manifest.json', 'manifest_sha256': hashlib.sha256(data).hexdigest()}
    manifest = json.loads(data)
    assert manifest['status'] == status
    assert (out / 'manifest.json').stat().st_nlink == 1
    assert not (out / 'manifest.partial').exists()
    return manifest


def test_rp01_exact_endpoints(git_repo, tmp_path):
    repo, git, base = git_repo
    (repo / 'a').write_text('C1\n'); git('commit', '-qam', 'one'); c1 = git('rev-parse', 'HEAD').decode().strip()
    (repo / 'b').write_text('C2\n'); git('add', '.'); git('commit', '-qm', 'two'); head = git('rev-parse', 'HEAD').decode().strip()
    (repo / 'a').write_text('C3\n'); git('commit', '-qam', 'later')
    out = tmp_path / 'package'; m = package(invoke(repo, base, head, out), out)
    assert [c['oid'] for c in m['commits']] == [c1, head]
    assert b'C3' not in (out / 'diff.patch').read_bytes()
    assert m['base'] == base and m['head'] == head


def load_collector():
    spec = importlib.util.spec_from_file_location('review_package_fixture', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def call_module(module, repo, base, head, out, *extra):
    return module.main(['--repo', str(repo), '--base', base, '--head', head, '--out', str(out),
        '--task-id', 'D6.S2', '--owner', 'fixture', '--generation', '1', '--repository-id', 'fixture-repo', *extra])


def commit(git, repo, text='change\n', name='a'):
    (repo / name).write_text(text); git('add', '.'); git('commit', '-qm', 'change\tmessage\nsecond line')
    return git('rev-parse', 'HEAD').decode().strip()


def test_rp02_merge_dag(git_repo, tmp_path):
    repo, git, base = git_repo
    git('checkout', '-qb', 'left'); left = commit(git, repo, 'left\n', 'left')
    git('checkout', '-qb', 'right', base); right = commit(git, repo, 'right\n', 'right')
    git('merge', '--no-ff', '-qm', 'merge\tmessage\nsecond line', 'left'); head = git('rev-parse', 'HEAD').decode().strip()
    out = tmp_path / 'package'; m = package(invoke(repo, base, head, out), out)
    ids = [c['oid'] for c in m['commits']]
    assert set(ids) == {left, right, head} and ids[-1] == head
    assert m['commits'][-1]['parents'] == [right, left]
    assert b'merge\tmessage\nsecond line' in (out / ('objects/' + head + '.commit')).read_bytes()


@pytest.mark.parametrize('extra', [('--base', 'abc'), ('--head', 'HEAD'), ('--head', '-option'),
    ('--spec-sha256', 'ABC'), ('--generation', '0'), ('--generation', 'true'), ('--generation', '1.0'),
    ('--staged',), ('--working-tree',), ('--res', 'x')])
def test_rp03_invalid_args(git_repo, tmp_path, extra):
    repo, git, base = git_repo; out = tmp_path / 'package'
    result = invoke(repo, base, base, out, *extra)
    assert result.returncode == 3 and result.stdout == b'' and result.stderr and not out.exists()


def test_rp03_invalid_object_and_reverse(git_repo, tmp_path):
    repo, git, base = git_repo; head = commit(git, repo)
    blob = git('rev-parse', head + ':a').decode().strip()
    for i, (a, b) in enumerate([(head, base), (base, blob)]):
        out = tmp_path / str(i); result = invoke(repo, a, b, out)
        assert result.returncode == 3 and not out.exists()


def test_rp04_empty_and_canceling(git_repo, tmp_path):
    repo, git, base = git_repo
    out = tmp_path / 'empty'; m = package(invoke(repo, base, base, out), out)
    assert m['no_change'] is True and m['commits'] == [] and m['files'] == []
    first = commit(git, repo, 'temporary\n', 'temporary'); (repo / 'temporary').unlink(); git('add', '-u'); git('commit', '-qm', 'remove')
    head = git('rev-parse', 'HEAD').decode().strip(); out = tmp_path / 'cancel'
    m = package(invoke(repo, base, head, out), out)
    assert m['no_change'] is True and [c['oid'] for c in m['commits']] == [first, head]
    assert not any(k in m for k in ('verdict', 'review_status', 'findings'))


def test_rp05_binary_attributes(git_repo, tmp_path):
    repo, git, base = git_repo; sentinel = tmp_path / 'external-fired'
    (repo / 'binary').write_bytes(b'\0\xff\x01'); (repo / '.gitattributes').write_text('binary diff=hostile\n')
    git('config', 'diff.hostile.textconv', 'touch ' + str(sentinel)); git('config', 'diff.external', 'touch ' + str(sentinel))
    git('add', '.'); git('commit', '-qm', 'binary'); head = git('rev-parse', 'HEAD').decode().strip()
    out = tmp_path / 'first'; first = package(invoke(repo, base, head, out), out)
    (repo / '.gitattributes').write_text('* -diff\n')
    second_out = tmp_path / 'second'; second = package(invoke(repo, base, head, second_out), second_out)
    assert first == second and not sentinel.exists()
    f = next(f for f in first['files'] if f['path'] == 'binary')
    assert f['binary'] and f['added_lines'] is None and f['deleted_lines'] is None
    assert (out / f['new']['object']['path']).read_bytes() == b'\0\xff\x01'
    assert b'GIT binary patch' in (out / 'diff.patch').read_bytes()


def test_rp06_paths_modes_rename_delete(git_repo, tmp_path):
    repo, git, _ = git_repo
    (repo / 'rename').write_text('line\n' * 40); (repo / 'edited').write_text('old\n' * 40)
    for name in ['space name', 'tab\tname', 'newline\nname', '-dash', '$(sentinel)', 'delete']:
        (repo / name).write_text('old\n')
    git('add', '.'); git('commit', '-qm', 'paths'); base = git('rev-parse', 'HEAD').decode().strip()
    (repo / 'rename').rename(repo / 'renamed'); (repo / 'edited').rename(repo / 'edited-new'); (repo / 'edited-new').write_text('new\n' + 'old\n' * 39)
    (repo / 'delete').unlink(); (repo / 'a').chmod(0o755); os.symlink('outside-target', repo / 'symlink')
    for name in ['space name', 'tab\tname', 'newline\nname', '-dash', '$(sentinel)']:
        (repo / name).write_text('new\n')
    git('add', '.'); git('commit', '-qm', 'modify'); head = git('rev-parse', 'HEAD').decode().strip()
    out = tmp_path / 'package'; m = package(invoke(repo, base, head, out), out)
    assert len([f for f in m['files'] if f['change'] == 'R']) == 2
    assert any(f['change'] == 'D' and f['new'] is None for f in m['files'])
    assert any(f['new'] and f['new']['mode'] == '100755' for f in m['files'])
    symlink = next(f for f in m['files'] if f['path'] == 'symlink')
    assert (out / symlink['new']['object']['path']).read_bytes() == b'outside-target'
    assert not (out / 'symlink').exists()
    paths = [base64.b64decode((f['new'] or f['old'])['path']['bytes_base64']) for f in m['files']]
    assert b'tab\tname' in paths and b'newline\nname' in paths


@pytest.mark.parametrize('fault', ['missing_endpoint', 'missing_tree', 'missing_commit', 'missing_blob', 'corrupt_blob', 'corrupt_commit', 'duplicate_commit', 'reordered_commit', 'raw_mode', 'raw_length', 'raw_nul', 'raw_score', 'raw_duplicate', 'empty_patch', 'decorated_oid', 'extra_numstat'])
def test_rp07_protocol_faults(git_repo, tmp_path, monkeypatch, capfd, fault):
    repo, git, base = git_repo; commit(git, repo, 'first\n'); head = commit(git, repo, 'second\n')
    module = load_collector(); original = module.Git.read; fired = []
    def read(self, args, operation):
        data = original(self, args, operation)
        target = {'missing_endpoint': 'endpoint_type', 'missing_tree': 'read_tree', 'missing_commit': 'read_commit', 'missing_blob': 'read_blob',
            'corrupt_blob': 'read_blob', 'corrupt_commit': 'read_commit', 'duplicate_commit': 'commit_list', 'reordered_commit': 'commit_list',
            'empty_patch': 'patch_diff', 'raw_duplicate': 'raw_diff', 'raw_mode': 'raw_diff', 'raw_length': 'raw_diff', 'raw_nul': 'raw_diff', 'raw_score': 'raw_diff',
            'decorated_oid': 'resolve_endpoint', 'extra_numstat': 'numstat_diff'}[fault]
        # Endpoint preflight reads are allowed; inject disappearance at collection resolution.
        if fault == 'missing_endpoint': target = 'resolve_endpoint'
        if operation != target: return data
        fired.append(operation)
        if fault.startswith('missing'): raise module.CollectionError(operation, 'git_process_failure')
        if fault in ('corrupt_blob', 'corrupt_commit'): return data + b'corruption'
        if fault == 'empty_patch': return b''
        if fault == 'raw_duplicate': return data + data
        if fault == 'duplicate_commit': return data + data.splitlines(keepends=True)[0]
        if fault == 'reordered_commit': return b''.join(reversed(data.splitlines(keepends=True)))
        if fault == 'raw_mode': return data.replace(b':100644', b':999999', 1)
        if fault == 'raw_length':
            oid = data.split(b' ')[2]
            return data.replace(oid, oid[1:], 1)
        if fault == 'raw_nul': return data[:-1]
        if fault == 'raw_score': return data.replace(b' M\0', b' R101\0', 1)
        if fault == 'decorated_oid': return data + b'decoration\n'
        return data + b'1\t1\textra\0'
    monkeypatch.setattr(module.Git, 'read', read)
    out = tmp_path / 'package'; code = call_module(module, repo, base, head, out); captured = capfd.readouterr()
    assert fired and code == 2
    if captured.out:
        m = json.loads((out / 'manifest.json').read_bytes()); assert m['status'] == 'incomplete' and m['collection_errors']
    else:
        assert not (out / 'manifest.json').exists()


@pytest.mark.parametrize('kind', ['directory', 'nonempty', 'file', 'symlink', 'broken', 'ancestor_symlink', 'dotdot', 'root', 'gitdir', 'gitdescendant', 'missing_parent', 'file_parent'])
def test_rp08_unsafe_outputs(git_repo, tmp_path, kind):
    repo, git, base = git_repo; out = tmp_path / 'output'; sentinel = tmp_path / 'sentinel'; sentinel.write_bytes(b'preserve')
    if kind == 'directory': out.mkdir()
    if kind == 'nonempty': out.mkdir(); (out / 'keep').write_bytes(b'keep')
    if kind == 'file': out.write_bytes(b'keep')
    if kind in ('symlink', 'broken'): out.symlink_to(sentinel if kind == 'symlink' else tmp_path / 'absent')
    if kind == 'ancestor_symlink': out.symlink_to(repo, target_is_directory=True); out = out / 'leaf'
    if kind == 'dotdot': out = str(tmp_path) + '/repo/../leaf'
    if kind == 'root': out = repo
    if kind == 'gitdir': out = repo / '.git'
    if kind == 'gitdescendant': out = repo / '.git' / 'new'
    if kind == 'missing_parent': out = tmp_path / 'absent' / 'leaf'
    if kind == 'file_parent': out = sentinel / 'leaf'
    result = invoke(repo, base, base, out)
    assert result.returncode == 3 and result.stdout == b'' and sentinel.read_bytes() == b'preserve'


@pytest.mark.parametrize('fault', ['leaf_race', 'ancestor_swap', 'identity', 'artifact_write', 'manifest_fsync', 'interrupt', 'marker_race', 'link', 'unlink', 'directory_fsync', 'partial_hardlink', 'stdout'])
def test_rp09_output_faults(git_repo, tmp_path, monkeypatch, capfd, fault):
    repo, git, base = git_repo; head = commit(git, repo); module = load_collector(); fired = []
    module.os = types.SimpleNamespace(**vars(os))
    module.sys = types.SimpleNamespace(**vars(sys))
    parent = tmp_path / 'parent'; parent.mkdir(); out = parent / 'package'
    if fault == 'leaf_race':
        original = module.os.mkdir
        def mkdir(name, *args, **kwargs):
            if name == 'package':
                fired.append(fault); original(name, *args, **kwargs)
                (out / 'competitor').write_bytes(b'keep')
            return original(name, *args, **kwargs)
        monkeypatch.setattr(module.os, 'mkdir', mkdir)
        module.os.supports_dir_fd = os.supports_dir_fd | {mkdir}
    elif fault in ('ancestor_swap', 'identity'):
        original = module.Output.identity
        def identity(self):
            fired.append(fault)
            if fault == 'ancestor_swap' and len(fired) == 1:
                parent.rename(tmp_path / 'moved'); parent.symlink_to(repo, target_is_directory=True)
            if fault == 'identity': raise module.CollectionError('output_identity', 'output_identity_mismatch')
            return original(self)
        monkeypatch.setattr(module.Output, 'identity', identity)
    elif fault in ('artifact_write', 'interrupt'):
        original = module.Output.write
        def write(self, name, data):
            if name == 'diff.patch':
                fired.append(fault)
                if fault == 'interrupt': raise KeyboardInterrupt()
                raise OSError('fixture write failure')
            return original(self, name, data)
        monkeypatch.setattr(module.Output, 'write', write)
    elif fault == 'manifest_fsync':
        original = module.os.fsync
        def fsync(fd):
            if os.fstat(fd).st_size > 0 and (out / 'manifest.partial').exists():
                fired.append(fault); raise OSError('fixture fsync failure')
            return original(fd)
        monkeypatch.setattr(module.os, 'fsync', fsync)
    elif fault in ('marker_race', 'link'):
        original = module.os.link
        def link(*args, **kwargs):
            fired.append(fault)
            if fault == 'link': raise OSError('fixture unsupported hard link')
            (out / 'manifest.json').write_bytes(b'competitor')
            return original(*args, **kwargs)
        # supports_dir_fd refers to function identity: keep the capability check
        # real and inject publication only through freeze seam.
        original_freeze = module.Output.freeze
        def freeze(self, *args):
            monkeypatch.setattr(module.os, 'link', link)
            return original_freeze(self, *args)
        monkeypatch.setattr(module.Output, 'freeze', freeze)
    elif fault in ('directory_fsync', 'partial_hardlink'):
        original_freeze = module.Output.freeze
        def freeze(self, *args):
            if fault == 'directory_fsync':
                original_fsync = module.os.fsync
                def fsync(fd):
                    if fd == self.fd and (out / 'manifest.json').exists():
                        fired.append(fault); raise OSError('fixture directory fsync failure')
                    return original_fsync(fd)
                monkeypatch.setattr(module.os, 'fsync', fsync)
            else:
                original_link = module.os.link
                def link(*a, **kw):
                    fired.append(fault)
                    os.link(out / 'manifest.partial', parent / 'extra-link')
                    return original_link(*a, **kw)
                monkeypatch.setattr(module.os, 'link', link)
            return original_freeze(self, *args)
        monkeypatch.setattr(module.Output, 'freeze', freeze)
    elif fault == 'unlink':
        original_freeze = module.Output.freeze
        def freeze(self, *args):
            def unlink(*a, **kw): fired.append(fault); raise OSError('fixture unlink failure')
            monkeypatch.setattr(module.os, 'unlink', unlink)
            return original_freeze(self, *args)
        monkeypatch.setattr(module.Output, 'freeze', freeze)
    else:
        original_freeze = module.Output.freeze
        def freeze(self, *args):
            receipt = original_freeze(self, *args); fired.append(fault)
            class Broken:
                def write(self, data): raise OSError('fixture stdout failure')
                def flush(self): pass
            class Stdout: buffer = Broken()
            monkeypatch.setattr(module.sys, 'stdout', Stdout()); return receipt
        monkeypatch.setattr(module.Output, 'freeze', freeze)
    code = call_module(module, repo, base, head, out); captured = capfd.readouterr()
    assert fired and code == (3 if fault == 'leaf_race' else 2) and captured.out == ''
    if fault == 'leaf_race': assert (out / 'competitor').read_bytes() == b'keep'
    if fault == 'marker_race': assert (out / 'manifest.json').read_bytes() == b'competitor'
    if fault == 'ancestor_swap': assert not (repo / 'package').exists()
    if fault == 'unlink': assert (out / 'manifest.json').stat().st_nlink == 2


def test_rp10_bindings_and_source_drift(git_repo, tmp_path, monkeypatch, capfd):
    repo, git, base = git_repo; head = commit(git, repo)
    out = tmp_path / 'optional'; m = package(invoke(repo, base, head, out, '--spec-sha256', 'a' * 64), out)
    assert m['spec_sha256'] == 'a' * 64 and m['plan_sha256'] is None
    module = load_collector(); original = module.source_snapshot; fired = []
    def snapshot():
        paths, data, schema = original(); data[0] += b'pretend entry drift'; fired.append(True)
        return paths, data, schema
    monkeypatch.setattr(module, 'source_snapshot', snapshot)
    out = tmp_path / 'drift'; assert call_module(module, repo, base, head, out) == 2 and fired
    assert capfd.readouterr().out == '' and not (out / 'manifest.json').exists()


def inventory(repo):
    return {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in repo.rglob('*') if p.is_file() and not p.is_symlink()}


def test_rp11_environment_no_mutation(git_repo, tmp_path, monkeypatch):
    repo, git, base = git_repo; head = commit(git, repo); (repo / 'dirty').write_bytes(b'untracked')
    before = inventory(repo)
    monkeypatch.setenv('GIT_DIR', '/absent'); monkeypatch.setenv('GIT_WORK_TREE', '/absent')
    monkeypatch.setenv('GIT_INDEX_FILE', str(tmp_path / 'wrong-index')); monkeypatch.setenv('GIT_CONFIG_COUNT', '1')
    monkeypatch.setenv('GIT_CONFIG_KEY_0', 'diff.submodule'); monkeypatch.setenv('GIT_CONFIG_VALUE_0', 'diff')
    out = tmp_path / 'package'; package(invoke(repo, base, head, out), out)
    assert inventory(repo) == before and not (tmp_path / 'wrong-index').exists()


@pytest.mark.parametrize('context', ['grafts', 'attributes', 'shallow', 'git_missing', 'global_switch', 'platform'])
def test_rp12_unsupported_preflight(git_repo, tmp_path, monkeypatch, capfd, context):
    repo, git, base = git_repo; module = load_collector(); fired = []
    if context in ('grafts', 'attributes'): (repo / '.git/info' / context).write_text('unsupported\n')
    if context == 'shallow': (repo / '.git/shallow').write_text(base + '\n')
    if context in ('git_missing', 'global_switch'):
        original = module.Git.execute
        def execute(self, args):
            fired.append(context)
            if context == 'git_missing': raise FileNotFoundError('fixture')
            return subprocess.CompletedProcess(args, 129, b'', b'unsupported')
        monkeypatch.setattr(module.Git, 'execute', execute)
    if context == 'platform':
        def preflight(): fired.append(context); raise module.Invalid('unsupported platform')
        monkeypatch.setattr(module, 'platform_preflight', preflight)
    out = tmp_path / 'package'; assert call_module(module, repo, base, base, out) == 3
    assert capfd.readouterr().out == '' and not out.exists()
    if context in ('git_missing', 'global_switch', 'platform'): assert fired


def test_rp13_determinism_closed_schema(git_repo, tmp_path):
    import jsonschema
    repo, git, base = git_repo; head = commit(git, repo)
    one, two = tmp_path / 'one', tmp_path / 'two'
    m = package(invoke(repo, base, head, one), one); package(invoke(repo, base, head, two), two)
    assert inventory(one) == inventory(two)
    schema = json.loads((SOURCE / 'schemas/review-package.schema.json').read_bytes())
    jsonschema.Draft202012Validator.check_schema(schema); jsonschema.validate(m, schema)
    for key in ('verdict', 'review_status', 'extra'):
        with pytest.raises(jsonschema.ValidationError): jsonschema.validate(dict(m, **{key: 'ready'}), schema)
    bad = dict(m, collection_errors=[{'code': 'failure', 'operation': 'test', 'path': None, 'message': 'failure'}])
    with pytest.raises(jsonschema.ValidationError): jsonschema.validate(bad, schema)
    module = load_collector()
    with pytest.raises(ValueError): module.read_json(b'{"x":1,"x":2}')


def test_rp06_nonutf8_posix(git_repo, tmp_path):
    repo, git, base = git_repo; path = os.fsencode(repo) + b'/nonutf8-\xff'
    try:
        fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    except OSError as error:
        if error.errno in (errno.EILSEQ, 92):
            pytest.skip('host filesystem rejects non-UTF8 pathname bytes (EILSEQ)')
        raise
    os.write(fd, b'bytes\n'); os.close(fd); git('add', '.'); git('commit', '-qm', 'raw path')
    head = git('rev-parse', 'HEAD').decode().strip(); out = tmp_path / 'package'
    m = package(invoke(repo, base, head, out), out)
    assert base64.b64decode(m['files'][0]['new']['path']['bytes_base64']) == b'nonutf8-\xff'


@pytest.mark.parametrize('formatting', ['diff', 'log'])
def test_rp16_hostile_initialized_submodule(git_repo, tmp_path, monkeypatch, capfd, formatting):
    repo, git, base = git_repo
    nested = tmp_path / 'nested'; nested.mkdir()
    def sub(*args): return subprocess.check_output(['git', '-C', str(nested), *args], stderr=subprocess.PIPE)
    sub('init', '-q'); sub('config', 'user.name', 'Fixture'); sub('config', 'user.email', 'fixture@example.invalid')
    content_sentinel = b'NESTED_CONTENT_SENTINEL_D6_RP16'
    message_sentinel = 'NESTED_MESSAGE_SENTINEL_D6_RP16'
    (nested / 'secret').write_bytes(b'first\n'); sub('add', '.'); sub('commit', '-qm', 'nested initial')
    first = sub('rev-parse', 'HEAD').decode().strip()
    (nested / 'secret').write_bytes(content_sentinel); sub('commit', '-qam', message_sentinel)
    second = sub('rev-parse', 'HEAD').decode().strip()
    # Local file transport is permitted only in fixture SETUP, before observation.
    git('-c', 'protocol.file.allow=always', 'submodule', 'add', '-q', str(nested), 'module')
    child = repo / 'module'
    subprocess.check_call(['git', '-C', str(child), 'checkout', '-q', first])
    git('add', '.'); git('commit', '-qm', 'base gitlink'); base = git('rev-parse', 'HEAD').decode().strip()
    subprocess.check_call(['git', '-C', str(child), 'checkout', '-q', second])
    subprocess.check_call(['git', '-C', str(child), 'config', 'diff.submodule', formatting])
    git('add', '.'); git('commit', '-qm', 'head gitlink'); head = git('rev-parse', 'HEAD').decode().strip()
    git('config', 'diff.submodule', formatting)
    module = load_collector(); original = module.Git.execute; observations = []; trace = tmp_path / 'trace.jsonl'
    def execute(self, args):
        # Actual Git subprocess with normal argv/environment; only add test-owned trace.
        self.environment['GIT_TRACE2_EVENT'] = str(trace)
        observations.append((self.command(args), str(self.repo)))
        return original(self, args)
    monkeypatch.setattr(module.Git, 'execute', execute)
    out = tmp_path / 'package'; assert call_module(module, repo, base, head, out) == 2
    captured = capfd.readouterr(); assert captured.out
    m = json.loads((out / 'manifest.json').read_bytes())
    assert m['status'] == 'incomplete' and any(e['code'] == 'unsupported_gitlink' for e in m['collection_errors'])
    assert m['files'][0]['old']['mode'] == m['files'][0]['new']['mode'] == '160000'
    assert m['files'][0]['old']['oid'] == first and m['files'][0]['new']['oid'] == second
    diffs = [argv for argv, _ in observations if 'diff' in argv]
    assert len(diffs) == 3
    for argv in diffs:
        assert '--submodule=short' in argv and '--ignore-submodules=none' in argv and 'diff.submodule=short' in argv
    assert all(cwd == str(repo) for _, cwd in observations)
    assert not any('cat-file' in argv and (first in argv or second in argv) for argv, _ in observations)
    artifacts = b''.join(p.read_bytes() for p in out.rglob('*') if p.is_file())
    assert content_sentinel not in artifacts and message_sentinel.encode() not in artifacts
    assert first.encode() in (out / 'diff.patch').read_bytes() and second.encode() in (out / 'diff.patch').read_bytes()
    events = [json.loads(line) for line in trace.read_bytes().splitlines()]
    starts = [e for e in events if e.get('event') == 'start']
    assert starts and len(starts) == len(observations)  # instrumentation positively fired
    assert not any(e.get('event') == 'child_start' for e in events)
    traced_argv = [e.get('argv', []) for e in starts]
    assert not any(any(token in {'fetch', 'submodule--helper'} or token.startswith('git-remote-') for token in argv) for argv in traced_argv)


@pytest.mark.parametrize('which', ['script', 'schema', 'map'])
def test_rp10_actual_producer_drift(git_repo, tmp_path, monkeypatch, capfd, which):
    repo, git, base = git_repo; copied = tmp_path / 'owner'; shutil.copytree(SOURCE, copied)
    spec = importlib.util.spec_from_file_location('copied_collector', copied / 'scripts/review_package.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    original = module.Output.freeze; fired = []
    target = {'script': copied / 'scripts/review_package.py', 'schema': copied / 'schemas/review-package.schema.json', 'map': copied / 'resource-map.json'}[which]
    def freeze(self, *args):
        target.write_bytes(target.read_bytes() + b'\n'); fired.append(which)
        return original(self, *args)
    monkeypatch.setattr(module.Output, 'freeze', freeze)
    out = tmp_path / 'package'; assert call_module(module, repo, base, base, out) == 2
    assert fired and capfd.readouterr().out == '' and not (out / 'manifest.json').exists()


@pytest.mark.parametrize('which', ['duplicate_map', 'malformed_schema', 'missing_map'])
def test_rp10_invalid_adjacent_sources(git_repo, tmp_path, which):
    repo, git, base = git_repo; copied = tmp_path / 'owner'; shutil.copytree(SOURCE, copied)
    if which == 'duplicate_map': (copied / 'resource-map.json').write_bytes(b'{"routes":{},"routes":{}}')
    if which == 'malformed_schema': (copied / 'schemas/review-package.schema.json').write_text('{}')
    if which == 'missing_map': (copied / 'resource-map.json').unlink()
    script = copied / 'scripts/review_package.py'; out = tmp_path / 'package'
    result = subprocess.run([sys.executable, '-I', str(script), '--repo', str(repo), '--base', base, '--head', base,
        '--out', str(out), '--task-id', 'id', '--owner', 'owner', '--generation', '1', '--repository-id', 'repo'], capture_output=True)
    assert result.returncode == 3 and result.stdout == b'' and not out.exists()


@pytest.mark.parametrize('side', ['base', 'head'])
def test_rp07_missing_actual_endpoint(git_repo, tmp_path, side):
    repo, git, base = git_repo; out = tmp_path / 'package'
    a, b = ('f' * 40, base) if side == 'base' else (base, 'f' * 40)
    m = package(invoke(repo, a, b, out), out, 'incomplete')
    assert not m['target_resolved'] and m['no_change'] is None and m['collection_errors']


def test_rp06_type_change(git_repo, tmp_path):
    repo, git, base = git_repo; (repo / 'a').unlink(); (repo / 'a').symlink_to('outside-target')
    git('add', '.'); git('commit', '-qm', 'type'); head = git('rev-parse', 'HEAD').decode().strip()
    out = tmp_path / 'package'; m = package(invoke(repo, base, head, out), out)
    assert m['files'][0]['change'] == 'T' and m['files'][0]['new']['mode'] == '120000'


def test_rp14_canonical_standalone_runtime(git_repo, tmp_path):
    """Source-only closure check. Generated-provider evidence belongs to integration."""
    repo, git, base = git_repo; copied = tmp_path / 'owner'; shutil.copytree(SOURCE, copied)
    out = tmp_path / 'package'; env = dict(os.environ, PYTHONPATH='/absent-core-source')
    result = subprocess.run([sys.executable, '-I', str(copied / 'scripts/review_package.py'), '--repo', str(repo), '--base', base,
        '--head', base, '--out', str(out), '--task-id', 'id', '--owner', 'owner', '--generation', '1', '--repository-id', 'repo'],
        env=env, cwd=tmp_path, capture_output=True)
    package(result, out)


def test_rp03_divergent_range(git_repo, tmp_path):
    repo, git, base = git_repo; left = commit(git, repo, 'left\n')
    git('checkout', '-qb', 'right', base); right = commit(git, repo, 'right\n')
    out = tmp_path / 'package'; result = invoke(repo, left, right, out)
    assert result.returncode == 3 and result.stdout == b'' and not out.exists()


def test_rp11_replacements_and_hooks(git_repo, tmp_path):
    repo, git, base = git_repo; head = commit(git, repo, 'exact\n')
    replacement = commit(git, repo, 'replacement-not-selected\n'); git('replace', head, replacement)
    hooks = tmp_path / 'hooks'; hooks.mkdir(); sentinel = tmp_path / 'hook-fired'
    hook = hooks / 'post-checkout'; hook.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\nPath(' + repr(str(sentinel)) + ').touch()\n'); hook.chmod(0o755)
    git('config', 'core.hooksPath', str(hooks)); before = inventory(repo)
    out = tmp_path / 'package'; m = package(invoke(repo, base, head, out), out)
    assert b'replacement-not-selected' not in (out / 'diff.patch').read_bytes()
    assert (out / m['files'][0]['new']['object']['path']).read_bytes() == b'exact\n'
    assert inventory(repo) == before and not sentinel.exists()


def test_rp09_artifact_hardlink(git_repo, tmp_path, monkeypatch, capfd):
    repo, git, base = git_repo; head = commit(git, repo); module = load_collector(); fired = []
    original = module.Output.freeze; out = tmp_path / 'package'
    def freeze(self, *args):
        os.link(out / 'diff.patch', tmp_path / 'extra-link'); fired.append(True)
        return original(self, *args)
    monkeypatch.setattr(module.Output, 'freeze', freeze)
    assert call_module(module, repo, base, head, out) == 2 and fired
    assert capfd.readouterr().out == '' and not (out / 'manifest.json').exists()


def test_rp07_rename_score_framing():
    module = load_collector()
    raw = b':100644 100644 ' + b'a' * 40 + b' ' + b'b' * 40 + b' R1\0old\0new\0'
    with pytest.raises(module.CollectionError): module.parse_raw(raw, 40)


def test_rp10_drift_during_partial_write(git_repo, tmp_path, monkeypatch, capfd):
    repo, git, base = git_repo; copied = tmp_path / 'owner'; shutil.copytree(SOURCE, copied)
    script = copied / 'scripts/review_package.py'
    spec = importlib.util.spec_from_file_location('copied_drift_collector', script)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    original = module.Output.write; fired = []
    def write(self, name, data):
        ref = original(self, name, data)
        if name == 'manifest.partial': script.write_bytes(script.read_bytes() + b'\n'); fired.append(True)
        return ref
    monkeypatch.setattr(module.Output, 'write', write)
    out = tmp_path / 'package'; assert call_module(module, repo, base, base, out) == 2 and fired
    assert capfd.readouterr().out == '' and not (out / 'manifest.json').exists()


def test_d6src001_progressive_route_closure():
    from intent_pipeline.capability_resources import load_resource_bundle
    review = load_resource_bundle(SOURCE, 'review')
    collect = load_resource_bundle(SOURCE, 'collect')
    assert [r['path'] for r in review['resources']] == ['schemas/findings.schema.json', 'references/review-targets.md']
    assert {r['path'] for r in collect['resources']} == {'scripts/review_package.py', 'schemas/review-package.schema.json'}
    assert 'review_package.py' not in ''.join(r['content'] for r in review['resources'])


@pytest.mark.parametrize('window', ['prelink_bytes', 'prelink_replacement', 'link_swap', 'postlink_bytes', 'postlink_partial_replacement', 'postcleanup_bytes'])
def test_d6src002_actual_main_manifest_windows(git_repo, tmp_path, monkeypatch, capfd, window):
    repo, git, base = git_repo; module = load_collector()
    module.os = types.SimpleNamespace(**vars(os)); fired = []; out = tmp_path / 'package'
    def tamper_bytes(path):
        before = path.read_bytes(); altered = b'X' + before[1:]
        assert len(altered) == len(before) and altered != before
        path.write_bytes(altered)  # size/identity alone cannot detect this fault
    def replace_partial():
        partial = out / 'manifest.partial'; saved = partial.read_bytes()
        partial.rename(out / 'collector-owned-original')
        partial.write_bytes(saved)  # identical bytes still have a foreign inode
    if window.startswith('prelink'):
        original = module.Output.write
        def write(self, name, data):
            result = original(self, name, data)
            if name == 'manifest.partial':
                fired.append(window)
                if window == 'prelink_bytes': tamper_bytes(out / name)
                else: replace_partial()
            return result
        monkeypatch.setattr(module.Output, 'write', write)
    elif window == 'postcleanup_bytes':
        original_freeze = module.Output.freeze
        def freeze(self, *args):
            original = module.os.unlink
            def unlink(name, *a, **kw):
                result = original(name, *a, **kw)
                if name == 'manifest.partial': fired.append(window); tamper_bytes(out / 'manifest.json')
                return result
            monkeypatch.setattr(module.os, 'unlink', unlink)
            return original_freeze(self, *args)
        monkeypatch.setattr(module.Output, 'freeze', freeze)
    else:
        original_freeze = module.Output.freeze
        def freeze(self, *args):
            original = module.os.link
            def link(*a, **kw):
                if window == 'link_swap': fired.append(window); replace_partial()
                result = original(*a, **kw)
                if window == 'postlink_bytes': fired.append(window); tamper_bytes(out / 'manifest.partial')
                if window == 'postlink_partial_replacement': fired.append(window); replace_partial()
                return result
            monkeypatch.setattr(module.os, 'link', link)
            return original_freeze(self, *args)
        monkeypatch.setattr(module.Output, 'freeze', freeze)
    code = call_module(module, repo, base, base, out); captured = capfd.readouterr()
    assert fired == [window]  # actual fault window positively observed
    assert code == 2 and captured.out == '', 'tampered/replaced manifest must never yield complete receipt'
    assert captured.err
    if window.endswith('replacement') or window == 'link_swap':
        assert (out / 'manifest.partial').exists(), 'foreign replacement must not be unlinked'


def test_d6src002_manifest_descriptor_failure_closes_original(git_repo, tmp_path, monkeypatch, capfd):
    repo, git, base = git_repo; module = load_collector(); module.os = types.SimpleNamespace(**vars(os))
    original = module.os.dup; observed = []
    def dup(fd):
        observed.append(fd); raise OSError('fixture descriptor duplication failure')
    monkeypatch.setattr(module.os, 'dup', dup)
    out = tmp_path / 'package'; assert call_module(module, repo, base, base, out) == 2
    assert observed and capfd.readouterr().out == '' and not (out / 'manifest.json').exists()
    with pytest.raises(OSError): os.fstat(observed[0])
