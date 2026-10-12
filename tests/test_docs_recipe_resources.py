"""Finite contracts for optional documentation resources, not a ship executor."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'sources/capability-resources/engos-quality-docs-review'
GITOPS = ROOT / 'sources/capability-resources/engos-quality-gitops-review'
HELPER = DOCS / 'scripts/factual_audit.py'
spec = importlib.util.spec_from_file_location('factual_audit', HELPER)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
SCHEMA = json.loads((DOCS / 'schemas/factual-audit.schema.json').read_text())


def item(status='verified', e=False):
    result = dict(claim='é', source_paths=['README.md'], status=status)
    result.update(dict(file='README.md', issue='', safe_rewrite='') if e else dict(rewrite_if_needed=''))
    return result


def e_payload(statuses=()):
    return dict(summary=dict(total_claims=len(statuses), **{s: statuses.count(s) for s in audit.STATUSES}), items=[item(s, True) for s in statuses])


def shape_valid(payload, fmt):
    schema = dict(SCHEMA, **{'$ref': '#/$defs/' + fmt})
    schema.pop('oneOf')
    return jsonschema.Draft202012Validator(schema).is_valid(payload)


@pytest.mark.parametrize('fmt,payload', [('master-array', []), ('master-array', [item(s) for s in audit.STATUSES]), ('prompt-e-object', e_payload()), ('prompt-e-object', e_payload(list(audit.STATUSES)))])
def test_valid_schema_helper_roundtrip(tmp_path, fmt, payload):
    if payload:
        target = payload[0] if isinstance(payload, list) else payload
        target['extension'] = {'nested': ['界', {'unchanged': True}]}
    assert shape_valid(payload, fmt)
    assert audit.validate(payload, fmt) == []
    path = tmp_path / 'input.json'
    path.write_text(json.dumps(payload, ensure_ascii=False))
    before = path.read_bytes()
    result = subprocess.run([sys.executable, str(HELPER), 'roundtrip', '--format', fmt, '--input', str(path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(result.stdout) == payload
    assert path.read_bytes() == before
    assert list(json.loads(result.stdout)[0] if isinstance(payload, list) and payload else json.loads(result.stdout)) == list(payload[0] if isinstance(payload, list) and payload else payload)


@pytest.mark.parametrize('fmt,payload', [('master-array', {}), ('master-array', [None]), ('master-array', [dict(item(), status='verified|needs_revision|unclear')]), ('master-array', [dict(item(), claim=None)]), ('master-array', [dict(item(), source_paths=[1])]), ('master-array', [{'claim': 'a'}]), ('prompt-e-object', []), ('prompt-e-object', {'items': []}), ('prompt-e-object', dict(e_payload(), summary=None)), ('prompt-e-object', dict(e_payload(), items=None))])
def test_structural_failures(fmt, payload):
    assert not shape_valid(payload, fmt)
    assert audit.validate(payload, fmt)


@pytest.mark.parametrize('count', [True, -1, 0.5, None, '0'])
def test_bad_count_types(count):
    payload = e_payload()
    payload['summary']['total_claims'] = count
    assert not shape_valid(payload, 'prompt-e-object')
    assert audit.validate(payload, 'prompt-e-object')


def test_count_arithmetic_is_separate_and_never_repaired():
    payload = e_payload(['verified', 'unclear'])
    payload['summary']['verified'] = 2
    before = copy.deepcopy(payload)
    assert shape_valid(payload, 'prompt-e-object')
    assert any(i['code'] == 'count_mismatch' for i in audit.validate(payload, 'prompt-e-object'))
    assert payload == before


@pytest.mark.parametrize('raw', ['{', '{"items":[],"items":[]}', '[NaN]', '[Infinity]', '[1e999]', '[{"claim":"","source_paths":[],"status":"verified","rewrite_if_needed":"","extension":1e999}]'])
def test_invalid_json_emits_no_payload(tmp_path, raw):
    path = tmp_path / 'bad.json'; path.write_text(raw)
    result = subprocess.run([sys.executable, str(HELPER), 'roundtrip', '--format', 'master-array', '--input', str(path)], capture_output=True, text=True)
    assert result.returncode == 2
    assert result.stdout == ''
    assert json.loads(result.stderr)['valid'] is False
    assert path.read_text() == raw


def test_wrong_explicit_format_and_cli_io(tmp_path):
    path = tmp_path / 'master.json'; path.write_text('[]')
    for fmt, code in [('prompt-e-object', 2), ('auto', 3)]:
        result = subprocess.run([sys.executable, str(HELPER), 'roundtrip', '--format', fmt, '--input', str(path)], capture_output=True, text=True)
        assert result.returncode == code and result.stdout == ''
    assert audit.main(['validate', '--format', 'master-array', '--input', str(tmp_path / 'missing')]) == 3


def test_literal_clause_map_and_unchanged_donors():
    report = ROOT / 'reports/program-doc-recipes'
    mapping = json.loads((ROOT / 'reports/d8-docs-recipes/clause-destination-map.json').read_text())
    assert len(mapping) == 250 and len({x['source_clause_id'] for x in mapping}) == 250
    for row in mapping:
        lines = (ROOT / row['destination_path']).read_text().splitlines(keepends=True)
        start, end = row['destination_line_span']
        assert hashlib.sha256(''.join(lines[start - 1:end]).encode()).hexdigest() == row['destination_literal_sha256']
    for path, sha in json.loads((report / 'source-hashes.json').read_text()).items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha


def test_optional_routes_have_only_finite_dependencies():
    routes = []
    for root in [DOCS, GITOPS]:
        resource_map = json.loads((root / 'resource-map.json').read_text())
        assert resource_map['shared'] == []
        routes += list(resource_map['routes'])
        for route_paths in resource_map['routes'].values():
            for path in route_paths:
                assert (root / path).is_file()
                for dep in resource_map['dependencies'][path]:
                    # Integrator owns the one declared shared-schema import.
                    if root == GITOPS:
                        assert dep == 'schemas/docs-ship-handoff.schema.json'
                        assert (DOCS / dep).is_file()
                    else:
                        assert (root / dep).is_file()
    assert len(routes) == 8
    for slug in ('engos-quality-docs-review', 'engos-quality-gitops-review'):
        candidate = (ROOT / f'reports/program-doc-recipes/{slug}-candidate.md').read_text()
        original = (ROOT / f'ssot/{slug}.md').read_text()
        assert candidate.startswith(original)
        assert 'Generic review loads no recipe' in candidate
    assert 'Only explicitly requested execution of a substantial documentation rewrite' in (ROOT / 'reports/program-doc-recipes/engos-quality-docs-review-candidate.md').read_text()


# These are independently implemented contract fixtures, never distributed runtime.
def manifest(candidate):
    entries = candidate['files']
    seen = set()
    for entry in entries:
        path = entry['path']
        if not path or any(c in path for c in ('\\', '\x00', '\r', '\n')) or any(p in ('', '.', '..') for p in path.split('/')) or path in seen:
            raise ValueError('Unsafe or duplicate path')
        seen.add(path)
        assert set(entry) == {'path', 'state', 'mode', 'sha256'}
        if entry['state'] == 'present':
            if entry['mode'] not in ('100644', '100755'): raise ValueError('Unsupported mode')
        elif entry['state'] != 'deleted' or entry['mode'] is not None or entry['sha256'] is not None:
            raise ValueError('Invalid deletion')
    return dict(manifest_version='DocsCandidateManifest.v1', target_kind=candidate['target_kind'], files=sorted(entries, key=lambda e: e['path'].encode()))


def digest(candidate):
    return hashlib.sha256(json.dumps(manifest(candidate), ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def request(kind='committed', gate='release'):
    candidate = dict(target_kind=kind, base_sha='a'*40, head_sha='b'*40, manifest_version='DocsCandidateManifest.v1', files=[dict(path='README.md', state='present', mode='100644', sha256='c'*64)], scope_note='README documentation only')
    candidate['content_digest'] = digest(candidate)
    return dict(schema_version='DocsShipHandoff.v1', kind='request', gate=gate, candidate=candidate, content_result=dict(verdict='PASS', evidence=['docs-observation'], unknowns=[]), requested_checks=['gitlab', 'github'], authority=['review'])


def response(req):
    return dict(schema_version='DocsShipHandoff.v1', kind='response', gate=req['gate'], candidate=copy.deepcopy(req['candidate']), authority=['review'], status='ready', observed_at='2026-10-12T12:00:00Z', checks=[dict(name=n, status='pass', evidence_ref=n+'-run', observed_head=req['candidate']['head_sha'], reason='exact candidate') for n in req['requested_checks']], version_prerequisites=dict(version='1.0.0', top_changelog_version='1.0.0', unreleased_empty=True, release_base='v0.9.0', package_verified=True), proposed_steps=[dict(phase='package', argv=['scripts/package-surfaces.sh', '--version', '1.0.0'], preconditions=['merged'], evidence_refs=['help'])], unknowns=[], blockers=[], manifest_verification=dict(method='committed_tree_reproduced', verified_target_kind='committed', verified_head=req['candidate']['head_sha'], reproduced_content_digest=req['candidate']['content_digest'], evidence_ref='git-tree-extraction', limitation='declared documentation scope'))


def ready(req, reply, independently_extracted, upstream_fresh=True):
    identity = lambda c: (c['target_kind'], c['base_sha'], c['head_sha'], c['manifest_version'], manifest(c), c['content_digest'])
    v = reply['manifest_verification']
    return (req['content_result']['verdict'] == 'PASS' and not req['content_result']['unknowns'] and reply['status'] == 'ready' and not reply['unknowns'] and not reply['blockers'] and upstream_fresh and req['gate'] == reply['gate'] and identity(req['candidate']) == identity(reply['candidate']) and req['candidate']['content_digest'] == digest(req['candidate']) and req['candidate']['target_kind'] == 'committed' and v['method'] == 'committed_tree_reproduced' and v['verified_target_kind'] == 'committed' and v['verified_head'] == req['candidate']['head_sha'] and v['reproduced_content_digest'] == digest(independently_extracted) == digest(req['candidate']) and all(any(c['name'] == n and c['status'] == 'pass' and c['observed_head'] == req['candidate']['head_sha'] and c['evidence_ref'] for c in reply['checks']) for n in req['requested_checks']) and (req['gate'] != 'release' or (reply['version_prerequisites']['version'] == reply['version_prerequisites']['top_changelog_version'] and reply['version_prerequisites']['version'] is not None and reply['version_prerequisites']['unreleased_empty'] is True and reply['version_prerequisites']['release_base'] is not None and reply['version_prerequisites']['package_verified'] is True)) and all(not any(x in arg for x in ('<', '>', '...')) for step in reply['proposed_steps'] for arg in step['argv']))


def test_actual_handoff_schema_positive_negative():
    schema = json.loads((DOCS / 'schemas/docs-ship-handoff.schema.json').read_text())
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    req = request(); reply = response(req)
    assert validator.is_valid(req) and validator.is_valid(reply)
    for bad in (dict(req, kind='auto'), dict(req, gate='deploy'), dict(reply, status='green'), dict(reply, candidate=dict(reply['candidate'], head_sha='short')), dict(req, candidate=dict(req['candidate'], target_kind='auto'))):
        assert not validator.is_valid(bad)
    assert ready(req, reply, req['candidate'])


@pytest.mark.parametrize('failure', ['head', 'digest', 'gate', 'missing_ci', 'unknown', 'upstream', 'placeholder', 'dirty_bytes', 'snapshot', 'discriminator'])
def test_candidate_bound_failures(failure):
    req = request(); reply = response(req); extracted = copy.deepcopy(req['candidate']); fresh = True
    if failure == 'head': reply['candidate']['head_sha'] = 'd'*40
    if failure == 'digest': reply['candidate']['content_digest'] = 'd'*64
    if failure == 'gate': reply['gate'] = 'commit'
    if failure == 'missing_ci': reply['checks'].pop()
    if failure == 'unknown': reply['unknowns'] = ['missing identity']
    if failure == 'upstream': fresh = False
    if failure == 'placeholder': reply['proposed_steps'][0]['argv'] = ['git', 'tag', '<next-version>']
    if failure == 'dirty_bytes': extracted['files'][0]['sha256'] = 'd'*64
    if failure in ('snapshot', 'discriminator'):
        req = request('snapshot'); reply = response(req); extracted = copy.deepcopy(req['candidate'])
        if failure == 'discriminator': req['candidate']['target_kind'] = reply['candidate']['target_kind'] = 'committed'
    assert not ready(req, reply, extracted, fresh)


def test_manifest_canonical_order_and_changes():
    c = request()['candidate']; c['files'].append(dict(path='é.md', state='deleted', mode=None, sha256=None))
    altered = copy.deepcopy(c); altered['files'].reverse(); altered['files'] = [dict(reversed(list(e.items()))) for e in altered['files']]
    assert digest(c) == digest(altered)
    for key, value in [('mode', '100755'), ('sha256', hashlib.sha256(b'changed\n').hexdigest())]:
        altered = copy.deepcopy(c); altered['files'][0][key] = value
        assert digest(c) != digest(altered)
    assert hashlib.sha256(b'a').hexdigest() != hashlib.sha256(b'a\n').hexdigest()
    altered = copy.deepcopy(c); altered['target_kind'] = 'snapshot'
    assert digest(c) != digest(altered)


@pytest.mark.parametrize('path', ['/abs', '../escape', 'a/../b', './a', 'a//b', 'a\\b', 'a\nb', 'a\rb', 'a\x00b', 'a/'])
def test_unsafe_paths(path):
    c = request()['candidate']; c['files'][0]['path'] = path
    with pytest.raises(ValueError): digest(c)


def test_duplicate_and_unsupported_modes():
    c = request()['candidate']; c['files'].append(copy.deepcopy(c['files'][0]))
    with pytest.raises(ValueError): digest(c)
    for mode in ['120000', '160000']:
        c = request()['candidate']; c['files'][0]['mode'] = mode
        with pytest.raises(ValueError): digest(c)


def test_independent_committed_tree_extraction(tmp_path):
    repo = tmp_path / 'repo'; repo.mkdir()
    def git(*args):
        return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True).stdout
    git('init', '-q'); git('config', 'user.name', 'Contract Fixture'); git('config', 'user.email', 'fixture@example.invalid')
    (repo / 'old.md').write_bytes(b'old\n'); git('add', 'old.md'); git('commit', '-qm', 'base')
    base = git('rev-parse', 'HEAD').decode().strip()
    git('mv', 'old.md', 'new.md'); (repo / 'new.md').write_bytes(b'new\n'); git('add', 'new.md'); git('commit', '-qm', 'rename target')
    head = git('rev-parse', 'HEAD').decode().strip()
    req = request(gate='merge'); c = req['candidate']
    mode = git('ls-tree', head, '--', 'new.md').decode().split()[0]
    c.update(base_sha=base, head_sha=head, files=[dict(path='old.md', state='deleted', mode=None, sha256=None), dict(path='new.md', state='present', mode=mode, sha256=hashlib.sha256(git('show', head+':new.md')).hexdigest())])
    assert git('ls-tree', base, '--', 'old.md') and not git('ls-tree', head, '--', 'old.md')
    c['content_digest'] = digest(c); reply = response(req)
    independently_extracted = copy.deepcopy(c)
    assert ready(req, reply, independently_extracted)
    (repo / 'new.md').write_bytes(b'dirty bytes same head\n')
    dirty = copy.deepcopy(c); dirty['files'][1]['sha256'] = hashlib.sha256((repo / 'new.md').read_bytes()).hexdigest()
    assert not ready(req, reply, dirty)
    assert ready(req, reply, independently_extracted)
    snapshot = copy.deepcopy(req); snapshot['candidate'] = dirty; snapshot['candidate']['target_kind'] = 'snapshot'; snapshot['candidate']['content_digest'] = digest(snapshot['candidate'])
    assert not ready(snapshot, response(snapshot), dirty)
    git('add', 'new.md'); git('commit', '-qm', 'snapshot becomes a new committed identity')
    assert git('rev-parse', 'HEAD').decode().strip() != head


@pytest.mark.parametrize('key,value', [('version', None), ('top_changelog_version', '2.0.0'), ('unreleased_empty', False), ('release_base', None), ('package_verified', False)])
def test_release_prerequisite_failure(key, value):
    req = request(); reply = response(req)
    reply['version_prerequisites'][key] = value
    assert not ready(req, reply, req['candidate'])


def test_public_recipe_discovery_and_strict_boundary_text():
    for name in ['README.md', 'docs/GETTING-STARTED.md', 'docs/EXAMPLES.md', 'docs/CLI-REFERENCE.md']:
        text = (ROOT / name).read_text()
        assert 'Optional documentation recipes' in text
        assert 'E content PASS does not establish hosted readiness' in text
        assert 'dirty snapshot bytes with green HEAD CI cannot pass' in text
    examples = (ROOT / 'docs/EXAMPLES.md').read_text()
    for route in ['docs-bundle', 'readme-authoring', 'ai-onboarding', 'information-relocation', 'document-visuals', 'factual-audit', 'adversarial-doc-review', 'docs-release-readiness']:
        assert route in examples
    f = (DOCS / 'references/adversarial-doc-review.md').read_text()
    assert 'Historical source command sequence (D8-COMPAT-SHIP-ORDER; never active commands)' in f
    assert 'Never tag before package' in f and 'No numeric pass threshold invented.' in f
    for template, fmt in [('factual-audit-master.json', 'master-array'), ('factual-audit-prompt-e.json', 'prompt-e-object')]:
        payload = json.loads((DOCS / 'templates' / template).read_text())
        assert shape_valid(payload, fmt) and not audit.validate(payload, fmt)
