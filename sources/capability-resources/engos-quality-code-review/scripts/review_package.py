#!/usr/bin/env python3
r"""Collect committed-range bytes; completion is collection, never review judgment.

## Explicit committed-range collection

Only when an immutable committed-range package is requested, use the additive
`collect` route: `resources/scripts/review_package.py` with its adjacent
`resources/schemas/review-package.schema.json` and `resources/resource-map.json`.
Ordinary review keeps the `review` route, `HEAD` default, six narrative sections
and `Findings.v1`; staged, dirty, root-with-null-base and supplied patches are
outside this collector. Read `--help` before invocation.

```text
python3 <owner-skill>/resources/scripts/review_package.py \
  --repo <repository> --base <full-recorded-baseline-commit> \
  --head <full-exact-candidate-commit> --out <new-task-owned-leaf> \
  --task-id <task-id> --owner <task-owner> --generation <positive-integer> \
  --repository-id <controller-repository-id> \
  [--spec-sha256 <64-lowercase-hex>] [--plan-sha256 <64-lowercase-hex>]
```

Supply exact lowercase full commit IDs and an ancestor base. The new output leaf
must be absent, its parent must already exist, and all ancestors must be real
directories without symlinks or dot/dotdot components. Prefer a task-owned reports
parent outside the repository. The helper never overwrites/resumes/removes output;
preserve partial leaves for separately authorized cleanup and retry with a new
leaf. Python 3.11+, Git supporting `--no-lazy-fetch` and `--attr-source`, and POSIX
nofollow directory descriptors and no-replace hard links are required; unsupported
runtime/preflight fails without a weaker fallback. No model, network or pip package
is needed by the helper.

Exit 0 means complete collection, 2 means incomplete collection or freeze failure,
and 3 means invalid invocation, unsupported preflight or unsafe destination.
A safely frozen package emits exactly one `ReviewPackageResult.v1` JSON stdout
object containing relative `manifest.json`, its SHA-256 and collection status.
Before freeze or on freeze failure stdout is empty; a marker left after a failed
publication/cleanup/stdout operation is unconfirmed. Retain the receipt digest
independently; do not accept partial files or multiply linked manifests.

`ReviewPackage.v1` retains the complete parent-first base..head commit list and raw
commit messages, endpoint net patch, NUL-framed raw/numstat records, and both-side
raw blobs of net changed paths. Raw filenames are base64 data with escaped display
strings; no repository filename or committed symlink target is materialized.
Binary bytes are collected without claiming review. Changed gitlinks retain
endpoint metadata and short-form patch IDs but make collection incomplete; no
nested submodule history/content is read. Intermediate per-commit patches and
unchanged consumers are not collected, even when a range's commits cancel.

Caller task/owner/generation/repository and optional spec/plan hashes are assertions,
not authenticated ownership or proof of a reviewed specification. Producer script,
schema and map hashes bind bytes but need independent expected identities. Local
repository identity binds the resolved common Git directory and object format;
it is not a remote URL or portability claim. D6.S3 consumer verification is a
separate step: reject untrusted, stale, mismatched, incomplete or tampered packages
against independently recorded expectations. Collection completeness grants no
correctness/security verdict, model-read proof, consumer coverage, merge, release
or repair authority. Freeze observes the collector-created manifest inode and
exact bytes at pre-link, post-link and post-cleanup boundaries. It does not exclude
arbitrary same-UID writers racing later syscalls or modifying output after the
last observation or receipt; independently retained digest verification remains
required. Review still reads the material and relevant unchanged consumers at the
exact target before producing findings.

"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

OWNER = 'engos-quality-code-review'
HEX = r'(?:[0-9a-f]{40}|[0-9a-f]{64})'
MODES = {'100644', '100755', '120000', '160000'}


class Invalid(Exception):
    """Invalid invocation or unsupported preflight (exit 3)."""


class CollectionError(Exception):
    def __init__(self, operation, code='malformed_protocol'):
        self.operation, self.code = operation, code
        super().__init__(operation)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def read_json(data):
    return json.loads(data.decode('utf-8'), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def shape(value, rule):
    """Validate the frozen schema's small JSON-Schema subset without dependencies."""
    if 'anyOf' in rule:
        for branch in rule['anyOf']:
            try:
                shape(value, branch)
                break
            except ValueError:
                pass
        else:
            raise ValueError('anyOf')
    if 'const' in rule and value != rule['const']:
        raise ValueError('const')
    if 'enum' in rule and value not in rule['enum']:
        raise ValueError('enum')
    expected = rule.get('type')
    classes = {'object': dict, 'array': list, 'string': str, 'integer': int,
               'boolean': bool, 'null': type(None)}
    if expected and (not isinstance(value, classes[expected]) or
                     (expected == 'integer' and isinstance(value, bool))):
        raise ValueError('type')
    if isinstance(value, dict):
        if any(key not in value for key in rule.get('required', [])):
            raise ValueError('required')
        props = rule.get('properties', {})
        if rule.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError('unknown field')
        for key in value.keys() & props.keys():
            shape(value[key], props[key])
    if isinstance(value, list):
        if len(value) < rule.get('minItems', 0) or len(value) > rule.get('maxItems', len(value)):
            raise ValueError('items')
        for item in value:
            shape(item, rule.get('items', {}))
    if isinstance(value, str):
        if len(value) < rule.get('minLength', 0) or len(value) > rule.get('maxLength', len(value)):
            raise ValueError('length')
        if 'pattern' in rule and not re.search(rule['pattern'], value):
            raise ValueError('pattern')
    if isinstance(value, int) and not isinstance(value, bool):
        if value < rule.get('minimum', value) or value > rule.get('maximum', value):
            raise ValueError('bounds')
    for condition in rule.get('allOf', []):
        if 'if' in condition:
            try:
                shape(value, condition['if'])
            except ValueError:
                shape(value, condition.get('else', {}))
            else:
                shape(value, condition.get('then', {}))
        else:
            shape(value, condition)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Invalid(message)


def arguments(argv):
    parser = Parser(description=__doc__, allow_abbrev=False, formatter_class=argparse.RawDescriptionHelpFormatter)
    for key in ('repo', 'base', 'head', 'out', 'task-id', 'owner', 'generation', 'repository-id'):
        parser.add_argument('--' + key, required=True)
    for key in ('spec-sha256', 'plan-sha256'):
        parser.add_argument('--' + key)
    args = parser.parse_args(argv)
    for key in ('base', 'head'):
        if not re.fullmatch(HEX, getattr(args, key)):
            raise Invalid('base/head must be exact lowercase full commit IDs')
    for key in ('spec_sha256', 'plan_sha256'):
        value = getattr(args, key)
        if value is not None and not re.fullmatch('[0-9a-f]{64}', value):
            raise Invalid('spec/plan digest must be lowercase SHA-256')
    if not re.fullmatch('[1-9][0-9]*', args.generation):
        raise Invalid('generation must be a positive decimal integer')
    try:
        args.generation = int(args.generation)
    except ValueError:
        raise Invalid('generation cannot be represented as a positive integer') from None
    for key in ('task_id', 'owner', 'repository_id'):
        value = getattr(args, key)
        if not value or len(value) > 256 or re.search(r'[\x00-\x1f\x7f]', value):
            raise Invalid('task and repository bindings must be nonempty opaque text without controls')
    return args


class Git:
    def __init__(self, repo):
        self.repo = repo
        self.head = None
        self.environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        self.environment.update(LC_ALL='C', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                                GIT_ATTR_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')

    def command(self, args):
        argv = ['git', '--no-pager', '--no-replace-objects', '--no-lazy-fetch']
        if self.head:
            argv.append('--attr-source=' + self.head)
        for setting in ('core.attributesFile=' + os.devnull, 'core.fsmonitor=false',
                        'core.hooksPath=' + os.devnull, 'protocol.allow=never', 'diff.external=',
                        'diff.algorithm=myers', 'diff.indentHeuristic=false', 'diff.submodule=short',
                        'core.quotePath=true'):
            argv.extend(['-c', setting])
        return argv + ['-C', str(self.repo), *args]

    def execute(self, args):
        # Bounded test observation seam: patch execute/run, never a production flag.
        return subprocess.run(self.command(args), env=self.environment, capture_output=True, shell=False)

    def read(self, args, operation):
        try:
            result = self.execute(args)
        except OSError:
            raise CollectionError(operation, 'git_process_failure') from None
        if result.returncode:
            raise CollectionError(operation, 'git_process_failure')
        return result.stdout

    def oid(self, data, operation, length):
        if not re.fullmatch(('[0-9a-f]{%d}\n' % length).encode(), data):
            raise CollectionError(operation)
        return data[:-1].decode('ascii')

    def object(self, kind, oid, algorithm):
        data = self.read(['cat-file', kind, oid], 'read_' + kind)
        actual = hashlib.new(algorithm, kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != oid:
            raise CollectionError('read_' + kind, 'object_hash_mismatch')
        return data


def check_schema(rule):
    if not isinstance(rule, dict):
        raise ValueError('schema node')
    if 'type' in rule and rule['type'] not in {'object', 'array', 'string', 'integer', 'boolean', 'null'}:
        raise ValueError('schema type')
    if 'pattern' in rule:
        re.compile(rule['pattern'])
    if 'properties' in rule:
        if not isinstance(rule['properties'], dict):
            raise ValueError('schema properties')
        for value in rule['properties'].values():
            check_schema(value)
    if 'required' in rule and (not isinstance(rule['required'], list) or
            any(not isinstance(v, str) for v in rule['required'])):
        raise ValueError('schema required')
    for key in ('anyOf', 'allOf'):
        if key in rule:
            if not isinstance(rule[key], list) or not rule[key]:
                raise ValueError('schema branches')
            for value in rule[key]:
                check_schema(value)
    for key in ('items', 'if', 'then', 'else'):
        if key in rule:
            check_schema(rule[key])


def source_snapshot():
    script = Path(__file__).resolve()
    resource = script.parent.parent
    paths = [script, resource / 'schemas/review-package.schema.json', resource / 'resource-map.json']
    try:
        data = [p.read_bytes() for p in paths]
        schema, mapping = read_json(data[1]), read_json(data[2])
        if (set(mapping) != {'schema_version', 'shared', 'routes', 'dependencies'} or
                mapping['schema_version'] != 'CapabilityResourceMap.v1' or mapping['shared'] != [] or
                set(mapping['routes']) != {'review', 'collect', 'verify-package'} or
                mapping['routes']['review'] != ['references/review-targets.md'] or
                mapping['dependencies'].get('references/review-targets.md') != ['schemas/findings.schema.json']):
            raise ValueError('owner resource map shape')
        expected_dependencies = {
            'references/review-targets.md': ['schemas/findings.schema.json'],
            'scripts/review_package.py': ['schemas/review-package.schema.json'],
            'references/review-package-consumption.md': ['scripts/verify_review_package.py'],
            'scripts/verify_review_package.py': ['scripts/review_package.py', 'schemas/review-package-expectation.schema.json']}
        if (mapping['dependencies'] != expected_dependencies or
                mapping['routes']['verify-package'] != ['references/review-package-consumption.md']):
            raise ValueError('owner verifier resource map shape')
        if schema.get('title') != 'ReviewPackage.v1 committed-range collection manifest':
            raise ValueError('schema identity')
        if mapping.get('routes', {}).get('collect') != ['scripts/review_package.py']:
            raise ValueError('collect route missing')
        if mapping.get('dependencies', {}).get('scripts/review_package.py') != ['schemas/review-package.schema.json']:
            raise ValueError('collect dependency missing')
        if schema.get('properties', {}).get('schema_version') != {'const': 'ReviewPackage.v1'}:
            raise ValueError('schema version')
        required = {'schema_version', 'status', 'target_kind', 'comparison', 'included_change_classes',
                    'base', 'head', 'target_resolved', 'base_tree', 'head_tree', 'task', 'repository',
                    'producer', 'spec_sha256', 'plan_sha256', 'commits', 'diff', 'stat', 'raw_changes',
                    'files', 'no_change', 'coverage', 'collection_errors'}
        if set(schema.get('required', [])) != required or set(schema.get('properties', {})) != required:
            raise ValueError('schema field set')
        if schema.get('additionalProperties') is not False or not schema.get('allOf'):
            raise ValueError('schema closure')
        coverage = schema['properties']['coverage']
        if set(coverage.get('properties', {})) != {'diff_scope', 'commit_scope', 'source_scope', 'unchanged_consumers',
                'checkout_changes', 'binary_policy', 'submodule_policy', 'trust'}:
            raise ValueError('coverage schema')
        if any(not isinstance(v.get('const'), str) for v in coverage['properties'].values()):
            raise ValueError('coverage constants')
        check_schema(schema)
    except (OSError, ValueError, TypeError, AttributeError, KeyError, re.error):
        raise Invalid('missing or malformed adjacent schema/resource map') from None
    return paths, data, schema


def platform_preflight():
    required = (os.open, os.mkdir, os.stat, os.link, os.unlink)
    if (os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY') or
            any(f not in os.supports_dir_fd for f in required) or
            os.link not in os.supports_follow_symlinks):
        raise Invalid('POSIX nofollow/dir_fd/hard-link primitives required')


def repository_preflight(args):
    try:
        repo = Path(args.repo).resolve(strict=True)
    except OSError:
        raise Invalid('repository must be an existing non-bare Git worktree') from None
    git = Git(repo)
    try:
        if git.read(['rev-parse', '--is-bare-repository'], 'repository') != b'false\n':
            raise Invalid('non-bare repository required')
        top = Path(os.fsdecode(git.read(['rev-parse', '--show-toplevel'], 'repository').removesuffix(b'\n'))).resolve(strict=True)
        admin = []
        for option in ('--git-common-dir', '--absolute-git-dir'):
            value = Path(os.fsdecode(git.read(['rev-parse', option], 'repository').removesuffix(b'\n')))
            admin.append((value if value.is_absolute() else repo / value).resolve(strict=True))
        fmt = git.read(['rev-parse', '--show-object-format'], 'object_format')
        if fmt not in (b'sha1\n', b'sha256\n'):
            raise Invalid('unsupported object format')
        fmt = fmt[:-1].decode()
        length = 40 if fmt == 'sha1' else 64
        if len(args.base) != length or len(args.head) != length:
            raise Invalid('commit IDs do not match repository object format')
        if git.read(['rev-parse', '--is-shallow-repository'], 'shallow') != b'false\n':
            raise Invalid('shallow repository unsupported')
        for name in ('grafts', 'attributes'):
            for root in set(admin):
                path = root / 'info' / name
                if path.exists() and path.stat().st_size:
                    raise Invalid('nonempty info/' + name + ' unsupported')
        # Harmless option probes; nonexistent endpoints are not confused with tool support.
        git.head = args.head
        git.read(['rev-parse', '--show-object-format'], 'feature_probe')
        git.head = None
    except CollectionError:
        raise Invalid('Git/repository preflight failed; required global switches must be supported') from None
    return git, top, admin, fmt


class Output:
    """Own a newly reserved leaf; every write stays relative to held descriptors."""
    def __init__(self, raw, top, admin):
        if any(p in ('.', '..') for p in raw.split('/')):
            raise Invalid('output dot/dotdot components forbidden')
        absolute = os.path.abspath(raw)
        path = Path(absolute)
        if path == top or any(path == a or a in path.parents for a in admin):
            raise Invalid('repository root and Git administrative output forbidden')
        self.fds = []
        self.chain = []
        self.refs = {}
        self.manifest_fd = None
        self.manifest_identity = None
        self.leaf = path.name
        if not self.leaf:
            raise Invalid('new output leaf required')
        try:
            fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            self.fds.append(fd)
            for component in path.parent.parts[1:]:
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                self.fds.append(child)
                self.chain.append((fd, component, child))
                fd = child
            self.parent = fd
            os.mkdir(self.leaf, 0o700, dir_fd=fd)
        except OSError:
            self.close()
            raise Invalid('output requires existing nonsymlink parents and absent leaf') from None
        try:
            self.fd = os.open(self.leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            self.fds.append(self.fd)
            self.chain.append((fd, self.leaf, self.fd))
            os.mkdir('objects', 0o700, dir_fd=self.fd)
            self.objects = os.open('objects', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd)
            self.fds.append(self.objects)
            self.chain.append((self.fd, 'objects', self.objects))
        except OSError:
            self.close()
            raise CollectionError('reserve_output', 'output_failure') from None

    def identity(self):
        for parent, name, fd in self.chain:
            actual, expected = os.stat(name, dir_fd=parent, follow_symlinks=False), os.fstat(fd)
            if not stat.S_ISDIR(actual.st_mode) or (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
                raise CollectionError('output_identity', 'output_identity_mismatch')

    def locate(self, path):
        if '/' in path:
            if not re.fullmatch('objects/' + HEX + r'\.(blob|commit)', path):
                raise CollectionError('artifact_path')
            return self.objects, path.split('/')[1]
        if path not in {'diff.patch', 'stat.numstat', 'changes.raw', 'manifest.partial', 'manifest.json'}:
            raise CollectionError('artifact_path')
        return self.fd, path

    def write(self, path, data):
        parent, name = self.locate(path)
        ref = {'path': path, 'sha256': digest(data), 'bytes': len(data)}
        if path in self.refs:
            if self.refs[path] != ref:
                raise CollectionError('artifact_write', 'artifact_collision')
            return ref
        access = os.O_RDWR if path == 'manifest.partial' else os.O_WRONLY
        fd = os.open(name, access | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                if path == 'manifest.partial':
                    self.manifest_fd = os.dup(stream.fileno())
                    self.fds.append(self.manifest_fd)
                    info = os.fstat(stream.fileno())
                    self.manifest_identity = (info.st_dev, info.st_ino)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            # Preserve owned partial file; never rewrite it to disguise failure.
            raise
        self.refs[path] = ref
        return ref

    def validate_artifacts(self, manifest, algorithm):
        refs = []
        for key in ('diff', 'stat', 'raw_changes'):
            if manifest[key] is not None:
                refs.append(manifest[key])
        refs.extend(c['object'] for c in manifest['commits'])
        for record in manifest['files']:
            refs.extend(s['object'] for s in (record['old'], record['new']) if s and s['object'])
        expected = {r['path'] for r in refs}
        if expected != set(self.refs):
            raise CollectionError('artifact_validation', 'artifact_set_mismatch')
        names = set(os.listdir(self.fd))
        if names != {'objects'} | {p for p in expected if '/' not in p}:
            raise CollectionError('artifact_validation', 'unexpected_artifact')
        if set(os.listdir(self.objects)) != {p.split('/')[1] for p in expected if '/' in p}:
            raise CollectionError('artifact_validation', 'unexpected_artifact')
        for ref in refs:
            parent, name = self.locate(ref['path'])
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                data = stream.read()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size != ref['bytes'] or digest(data) != ref['sha256']:
                raise CollectionError('artifact_validation', 'artifact_integrity_failure')
            if '/' in ref['path']:
                oid, kind = name.split('.')
                if hashlib.new(algorithm, kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest() != oid:
                    raise CollectionError('artifact_validation', 'object_hash_mismatch')
        os.fsync(self.objects)

    def verify_manifest(self, data, names, links):
        """Check retained created inode, path links and actual bytes at freeze boundaries.

        These observed boundaries detect accidental/fault-window changes. They do
        not lock out an arbitrary same-UID writer racing syscalls or changing bytes
        after the last observation; callers must retain and verify the receipt.
        """
        if self.manifest_fd is None or self.manifest_identity is None:
            raise CollectionError('manifest_publication', 'manifest_identity_mismatch')
        info = os.fstat(self.manifest_fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != links or
                (info.st_dev, info.st_ino) != self.manifest_identity or info.st_size != len(data)):
            raise CollectionError('manifest_publication', 'manifest_identity_mismatch')
        for name in names:
            path_info = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            if (not stat.S_ISREG(path_info.st_mode) or path_info.st_nlink != links or
                    (path_info.st_dev, path_info.st_ino) != self.manifest_identity):
                raise CollectionError('manifest_publication', 'manifest_identity_mismatch')
        os.lseek(self.manifest_fd, 0, os.SEEK_SET)
        with os.fdopen(os.dup(self.manifest_fd), 'rb') as stream:
            actual = stream.read()
        if actual != data or digest(actual) != digest(data):
            raise CollectionError('manifest_publication', 'manifest_bytes_mismatch')
        after = os.fstat(self.manifest_fd)
        if (after.st_size != len(data) or after.st_nlink != links or
                (after.st_dev, after.st_ino) != self.manifest_identity):
            raise CollectionError('manifest_publication', 'manifest_identity_mismatch')

    def freeze(self, manifest, schema, paths, source_bytes, algorithm):
        self.identity()
        if [p.read_bytes() for p in paths] != source_bytes:
            raise CollectionError('producer_binding', 'producer_drift')
        shape(manifest, schema)
        self.validate_artifacts(manifest, algorithm)
        data = canonical(manifest)
        self.write('manifest.partial', data)
        self.identity()
        if [p.read_bytes() for p in paths] != source_bytes:
            raise CollectionError('producer_binding', 'producer_drift')
        self.verify_manifest(data, ['manifest.partial'], 1)
        os.link('manifest.partial', 'manifest.json', src_dir_fd=self.fd, dst_dir_fd=self.fd, follow_symlinks=False)
        # Both path names must still denote the retained collector-created inode.
        # A foreign partial replacement is preserved rather than unlinked.
        self.verify_manifest(data, ['manifest.partial', 'manifest.json'], 2)
        os.unlink('manifest.partial', dir_fd=self.fd)
        os.fsync(self.fd)
        self.verify_manifest(data, ['manifest.json'], 1)
        self.identity()
        return {'schema_version': 'ReviewPackageResult.v1', 'status': manifest['status'],
                'manifest': 'manifest.json', 'manifest_sha256': digest(data)}

    def close(self):
        for fd in reversed(self.fds):
            os.close(fd)
        self.fds = []


def path_record(path):
    if not path or path.startswith(b'/') or b'\0' in path or any(p in (b'', b'.', b'..') for p in path.split(b'/')):
        raise CollectionError('parse_paths', 'invalid_git_path')
    return {'display': ascii(path.decode('utf-8', 'surrogateescape'))[1:-1],
            'bytes_base64': base64.b64encode(path).decode('ascii')}


def parse_raw(data, length):
    if not data:
        return []
    if not data.endswith(b'\0'):
        raise CollectionError('parse_raw')
    tokens = data[:-1].split(b'\0')
    result = []
    seen_paths = set()
    index = 0
    while index < len(tokens):
        header = tokens[index]; index += 1
        match = re.fullmatch(rb':([0-9]{6}) ([0-9]{6}) ([0-9a-f]{' + str(length).encode() + rb'}) ([0-9a-f]{' + str(length).encode() + rb'}) ([ADMT]|R[0-9]{3})', header)
        if not match or index >= len(tokens):
            raise CollectionError('parse_raw')
        oldmode, newmode, oldoid, newoid, status = [x.decode('ascii') for x in match.groups()]
        change = status[0]; similarity = int(status[1:]) if change == 'R' else None
        if similarity is not None and similarity > 100:
            raise CollectionError('parse_raw')
        oldpath = newpath = tokens[index]; index += 1
        if change == 'R':
            if index >= len(tokens):
                raise CollectionError('parse_raw')
            newpath = tokens[index]; index += 1
            if oldpath == newpath:
                raise CollectionError('parse_raw')
        old = None if oldmode == '000000' else (oldmode, oldoid, oldpath)
        new = None if newmode == '000000' else (newmode, newoid, newpath)
        for mode, oid in ((oldmode, oldoid), (newmode, newoid)):
            if (mode == '000000') != (oid == '0' * length) or mode not in MODES | {'000000'}:
                raise CollectionError('parse_raw')
        if ((change == 'A' and (old or not new)) or (change == 'D' and (not old or new)) or
                (change in 'MRT' and (not old or not new))):
            raise CollectionError('parse_raw')
        for side in (old, new):
            if side:
                path_record(side[2])
        if old and new:
            if (change == 'T') != (oldmode[:2] != newmode[:2]) and change != 'R':
                raise CollectionError('parse_raw')
        effective = newpath if new else oldpath
        if effective in seen_paths:
            raise CollectionError('parse_raw', 'duplicate_path')
        seen_paths.add(effective)
        result.append((change, similarity, old, new))
    return result


def parse_numstat(data):
    if not data:
        return []
    if not data.endswith(b'\0'):
        raise CollectionError('parse_numstat')
    tokens = data[:-1].split(b'\0'); index = 0; result = []
    while index < len(tokens):
        fields = tokens[index].split(b'\t', 2); index += 1
        if len(fields) != 3:
            raise CollectionError('parse_numstat')
        added, deleted, path = fields
        if added == deleted == b'-':
            counts = (True, None, None)
        elif re.fullmatch(rb'[0-9]+', added) and re.fullmatch(rb'[0-9]+', deleted):
            counts = (False, int(added), int(deleted))
        else:
            raise CollectionError('parse_numstat')
        if path:
            oldpath = newpath = path
        else:
            if index + 1 >= len(tokens):
                raise CollectionError('parse_numstat')
            oldpath, newpath = tokens[index:index + 2]; index += 2
        path_record(oldpath); path_record(newpath)
        result.append((oldpath, newpath, *counts))
    return result


def commit_fields(data, length):
    header, separator, _ = data.partition(b'\n\n')
    if not separator:
        raise CollectionError('parse_commit')
    lines = header.split(b'\n')
    if sum(line.startswith(b'tree ') for line in lines) != 1:
        raise CollectionError('parse_commit')
    if not lines or not re.fullmatch(rb'tree [0-9a-f]{' + str(length).encode() + rb'}', lines[0]):
        raise CollectionError('parse_commit')
    parents = []
    for line in lines[1:]:
        if line.startswith(b'parent '):
            if not re.fullmatch(rb'parent [0-9a-f]{' + str(length).encode() + rb'}', line):
                raise CollectionError('parse_commit')
            parents.append(line[7:].decode())
    if len(set(parents)) != len(parents):
        raise CollectionError('parse_commit')
    return lines[0][5:].decode(), parents


def collect(args, git, output, manifest, algorithm):
    length = 40 if algorithm == 'sha1' else 64
    for oid in (args.base, args.head):
        kind = git.read(['cat-file', '-t', oid], 'endpoint_type')
        if kind in (b'blob\n', b'tree\n', b'tag\n'):
            raise Invalid('endpoint is not a commit object')
        if kind != b'commit\n':
            raise CollectionError('endpoint_type')
        resolved = git.oid(git.read(['rev-parse', '--verify', oid + '^{commit}'], 'resolve_endpoint'), 'resolve_endpoint', length)
        if resolved != oid:
            raise CollectionError('resolve_endpoint')
        kind = git.read(['cat-file', '-t', oid], 'endpoint_type')
        if kind in (b'blob\n', b'tree\n', b'tag\n'):
            raise Invalid('endpoint is not a commit object')
        if kind != b'commit\n':
            raise CollectionError('endpoint_type')
    result = git.execute(['merge-base', '--is-ancestor', args.base, args.head])
    if result.returncode == 1:
        raise Invalid('base must be an ancestor of head')
    if result.returncode:
        raise CollectionError('range_ancestry', 'git_process_failure')
    git.head = args.head
    trees = []
    for oid in (args.base, args.head):
        tree, _ = commit_fields(git.object('commit', oid, algorithm), length)
        git.object('tree', tree, algorithm)
        trees.append(tree)
    manifest.update(target_resolved=True, base_tree=trees[0], head_tree=trees[1], no_change=trees[0] == trees[1])
    listing = git.read(['rev-list', '--reverse', '--topo-order', args.base + '..' + args.head], 'commit_list')
    if listing and not re.fullmatch((r'(?:[0-9a-f]{%d}\n)+' % length).encode(), listing):
        raise CollectionError('commit_list')
    ids = [x.decode() for x in listing.splitlines()]
    if len(ids) != len(set(ids)) or args.base in ids or (args.base == args.head) != (not ids) or (ids and ids[-1] != args.head):
        raise CollectionError('commit_list')
    records = manifest['commits']; seen = set(); boundaries = set()
    for oid in ids:
        raw = git.object('commit', oid, algorithm); tree, parents = commit_fields(raw, length)
        git.object('tree', tree, algorithm)
        for parent in parents:
            if parent in ids and parent not in seen:
                raise CollectionError('commit_order')
            if parent not in ids:
                if parent not in boundaries:
                    check = git.execute(['merge-base', '--is-ancestor', parent, args.base])
                    if check.returncode:
                        raise CollectionError('commit_membership')
                    boundaries.add(parent)
        ref = output.write('objects/' + oid + '.commit', raw)
        records.append({'oid': oid, 'tree': tree, 'parents': parents, 'object': ref}); seen.add(oid)
    reachable = set(); stack = [args.head] if ids else []
    by_id = {r['oid']: r for r in records}
    while stack:
        oid = stack.pop()
        if oid in reachable:
            continue
        reachable.add(oid)
        stack.extend(p for p in by_id[oid]['parents'] if p in by_id)
    if reachable != set(ids):
        raise CollectionError('commit_membership')
    manifest['commits'] = records
    options = ['--no-ext-diff', '--no-textconv', '--find-renames=50%', '-l0',
               '--ignore-submodules=none', '--submodule=short', '--no-relative']
    endpoint = [args.base, args.head, '--']
    raw = git.read(['diff', '--raw', '-z', '--no-abbrev', *options, *endpoint], 'raw_diff')
    numstat = git.read(['diff', '--numstat', '-z', *options, *endpoint], 'numstat_diff')
    patch = git.read(['diff', '--patch', '--binary', '--full-index', '--no-color', '--src-prefix=a/',
                      '--dst-prefix=b/', '--unified=3', *options, *endpoint], 'patch_diff')
    changes = parse_raw(raw, length); counts = parse_numstat(numstat)
    if len(changes) != len(counts):
        raise CollectionError('diff_crosscheck')
    # Parse/crosscheck before declaring any artifact complete.
    for (change, _, old, new), (oldpath, newpath, *_counts) in zip(changes, counts):
        if change == 'R':
            expected = (old[2], new[2])
        else:
            path = new[2] if new else old[2]; expected = (path, path)
        if expected != (oldpath, newpath):
            raise CollectionError('diff_crosscheck')
    if manifest['no_change'] != (not changes) or (not changes and (raw or numstat or patch)) or (changes and not patch):
        raise CollectionError('diff_crosscheck')
    manifest['raw_changes'] = output.write('changes.raw', raw)
    manifest['stat'] = output.write('stat.numstat', numstat)
    manifest['diff'] = output.write('diff.patch', patch)
    files = []
    def side_record(side):
        if side is None:
            return None
        mode, oid, path = side
        record = {'path': path_record(path), 'mode': mode, 'oid': oid, 'object': None}
        if mode == '160000':
            add_error(manifest, CollectionError('source_blob', 'unsupported_gitlink'), record['path']['display'])
        else:
            try:
                data = git.object('blob', oid, algorithm)
            except CollectionError as error:
                add_error(manifest, error, record['path']['display'])
            else:
                record['object'] = output.write('objects/' + oid + '.blob', data)
        return record
    for (change, similarity, old, new), (_, _, binary, added, deleted) in zip(changes, counts):
        old_record, new_record = side_record(old), side_record(new)
        effective = new_record or old_record
        files.append({'path': effective['path']['display'], 'change': change, 'similarity': similarity,
                      'old': old_record, 'new': new_record,
                      'head_blob': new[1] if new and new[0] != '160000' else None,
                      'binary': binary, 'added_lines': added, 'deleted_lines': deleted})
    files.sort(key=lambda f: (base64.b64decode((f['new'] or f['old'])['path']['bytes_base64']),
                             base64.b64decode(f['old']['path']['bytes_base64']) if f['old'] else b''))
    manifest['files'] = files


def add_error(manifest, error, path=None):
    manifest['collection_errors'].append({'code': error.code, 'operation': error.operation,
                                         'path': path, 'message': 'Collection could not verify ' + error.operation + '.'})


def manifest_factory(args, admin, algorithm, source_bytes, schema):
    manifest = {key: None for key in ('base_tree', 'head_tree', 'diff', 'stat', 'raw_changes', 'no_change')}
    manifest.update(schema_version='ReviewPackage.v1', status='incomplete', target_kind='committed_range',
                    comparison='range', included_change_classes=['committed'], base=args.base, head=args.head,
                    target_resolved=False, task={'id': args.task_id, 'owner': args.owner, 'generation': args.generation},
                    repository={'id': args.repository_id, 'object_format': algorithm,
                                'local_identity_sha256': digest(canonical({'common_git_dir': admin[0].as_posix(), 'object_format': algorithm}))},
                    producer={'owner': OWNER, 'script_sha256': digest(source_bytes[0]),
                              'schema_sha256': digest(source_bytes[1]), 'resource_map_sha256': digest(source_bytes[2])},
                    spec_sha256=args.spec_sha256, plan_sha256=args.plan_sha256, commits=[], files=[], collection_errors=[],
                    coverage={key: value['const'] for key, value in schema['properties']['coverage']['properties'].items()})
    return manifest


def main(argv=None):
    output = None
    try:
        args = arguments(argv)
        platform_preflight()
        paths, source_bytes, schema = source_snapshot()
        git, top, admin, algorithm = repository_preflight(args)
        # Reject existing/unsafe output before target collection. Invalid ranges remain
        # no-manifest errors; their reserved leaf is preserved without unsafe cleanup.
        try:
            for oid in (args.base, args.head):
                kind = git.read(['cat-file', '-t', oid], 'endpoint_type')
                if kind in (b'blob\n', b'tree\n', b'tag\n'):
                    raise Invalid('endpoint is not a commit object')
                if kind != b'commit\n':
                    raise CollectionError('endpoint_type')
            ancestry = git.execute(['merge-base', '--is-ancestor', args.base, args.head])
            if ancestry.returncode == 1:
                raise Invalid('base must be an ancestor of head')
        except CollectionError:
            pass
        output = Output(args.out, top, admin)
        manifest = manifest_factory(args, admin, algorithm, source_bytes, schema)
        try:
            collect(args, git, output, manifest, algorithm)
        except CollectionError as error:
            add_error(manifest, error)
        manifest['status'] = 'incomplete' if manifest['collection_errors'] else 'complete'
        receipt = output.freeze(manifest, schema, paths, source_bytes, algorithm)
        sys.stdout.buffer.write(canonical(receipt)); sys.stdout.buffer.flush()
        return 0 if manifest['status'] == 'complete' else 2
    except Invalid as error:
        print('review-package: ' + str(error), file=sys.stderr)
        return 3
    except (CollectionError, OSError, ValueError, KeyboardInterrupt) as error:
        if isinstance(error, CollectionError):
            print('review-package: ' + error.operation + ': ' + error.code, file=sys.stderr)
        retained = ascii(args.out)[1:-1] if 'args' in locals() else '<unreserved>'
        print('review-package: collection/freeze failed; preserve partial output ' + retained + ' and use a new leaf.', file=sys.stderr)
        return 2
    finally:
        if output is not None:
            output.close()


if __name__ == '__main__':
    sys.exit(main())
