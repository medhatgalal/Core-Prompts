"""Executable coverage/quote regressions; no live credentials or CLI dependencies."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / 'sources/capability-resources/engos-design-freshness-sweep'
SCRIPT = RESOURCES / 'scripts/freshness_check.py'
spec = importlib.util.spec_from_file_location('freshness_check', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.fixture
def packet():
    return json.loads((RESOURCES / 'evals/lifted-blocker.json').read_text())


def test_lifted_blocker_page_two_and_platform_api(packet):
    result = checker.check(packet)
    assert result['status'] == 'ready'
    assert result['coverage'] == {'tickets': 2, 'mrs': 2, 'notes': 3, 'repos': 2}
    rendered = checker.markdown(result)
    assert checker.TITLE in rendered
    assert 'retire the workaround' in rendered
    assert 'T-1#c2' in rendered and 'platform-api@8' in rendered


@pytest.mark.parametrize('fault', ['last_page', 'total', 'cursor', 'linked_ticket', 'linked_mr', 'repo', 'owner', 'window', 'api', 'body', 'gap', 'unknown_citation', 'note_link', 'mr_link', 'duplicate_note', 'empty_roots'])
def test_incomplete_is_never_ready_or_blocked(packet, fault):
    discussion = packet['tickets']['T-1']['discussion']['comments']
    if fault == 'last_page':
        discussion['pages'].pop()
    elif fault == 'total':
        discussion['pages'][1]['total'] = 3
    elif fault == 'cursor':
        discussion['pages'][1]['cursor'] = 'wrong'
    elif fault == 'linked_ticket':
        del packet['tickets']['T-2']
    elif fault == 'linked_mr':
        del packet['mrs']['app!9']
    elif fault == 'repo':
        del packet['merges']['platform']
    elif fault == 'owner':
        packet['merges']['app']['owners'] = ['app-owner']
    elif fault == 'window':
        packet['merges']['app']['since'] = '2026-11-01T15:00:00Z'
    elif fault == 'api':
        packet['mrs']['platform!8']['inspected_ref'] = ''
    elif fault == 'body':
        discussion['pages'][1]['items'][0]['body'] = None
    elif fault == 'gap':
        packet['gaps'] = ['Denied T-3 discussion']
    elif fault == 'unknown_citation':
        packet['changes'][0]['evidence_refs'] = ['unread-api']
    elif fault == 'note_link':
        discussion['pages'][1]['items'][0]['ticket_links'] = ['T-3']
    elif fault == 'mr_link':
        packet['mrs']['platform!8']['mr_links'] = ['platform!99']
    elif fault == 'duplicate_note':
        discussion['pages'][1]['items'][0] = copy.deepcopy(discussion['pages'][0]['items'][0])
    elif fault == 'empty_roots':
        packet['roots'] = []
    assert checker.check(packet)['status'] == 'incomplete'


def blocked(packet):
    note = packet['mrs']['platform!8']['discussion']['notes']['pages'][0]['items'][0]
    note['body'] = 'Export remains blocked on tenant authorization.'
    packet['verdict'] = 'blocked'
    packet['blockers'] = [{'scope': 'tenant export authorization', 'owner': 'platform-owner',
                           'note_ref': note['ref'], 'quote': note['body'], 'current_evidence_refs': ['platform-api@8'],
                           'currency_assessment': 'Owner confirms this exact tenant scope against current API evidence.'}]


def test_owner_exact_quote_required(packet):
    blocked(packet)
    assert checker.check(packet)['status'] == 'blocked'
    packet['blockers'][0]['quote'] = 'Export is impossible.'
    assert checker.check(packet)['status'] == 'incomplete'


@pytest.mark.parametrize('fault', ['none', 'reporter', 'missing_currency', 'unknown_note', 'unknown_owner'])
def test_unsupported_blocked_verdict_refused(packet, fault):
    blocked(packet)
    b = packet['blockers'][0]
    if fault == 'none':
        packet['blockers'] = []
    elif fault == 'reporter':
        packet['mrs']['platform!8']['discussion']['notes']['pages'][0]['items'][0]['author'] = 'reporter'
    elif fault == 'missing_currency':
        b['current_evidence_refs'] = []
    elif fault == 'unknown_note':
        b['note_ref'] = 'missing'
    elif fault == 'unknown_owner':
        b['owner'] = 'reporter'
    assert checker.check(packet)['status'] == 'incomplete'


def test_zero_merges_requires_terminal_query_and_all_owners(packet):
    assert checker.check(packet)['status'] == 'ready'
    packet['merges']['app']['pages'][0]['next'] = 'unfetched'
    assert checker.check(packet)['status'] == 'incomplete'


def test_cli_and_invalid_input(packet, tmp_path):
    path = tmp_path / 'evidence.json'
    path.write_text(json.dumps(packet))
    command = [sys.executable, str(SCRIPT), '--evidence', str(path)]
    good = subprocess.run(command, capture_output=True, text=True)
    assert good.returncode == 0
    assert json.loads(good.stdout)['status'] == 'ready'
    packet['gaps'] = ['rate limited']
    path.write_text(json.dumps(packet))
    incomplete = subprocess.run(command, capture_output=True, text=True)
    assert incomplete.returncode == 1
    assert json.loads(incomplete.stdout)['status'] == 'incomplete'
    for malformed in ['{"schema_version":"FreshnessEvidence.v1","schema_version":"x"}', 'null', '{', '{"bad": NaN}']:
        path.write_text(malformed)
        bad = subprocess.run(command, capture_output=True, text=True)
        assert bad.returncode == 2 and not bad.stderr
        assert json.loads(bad.stdout)['status'] == 'incomplete'


def test_unsupported_owner_merge_cannot_disappear(packet):
    packet['mrs'].pop('platform!8')
    packet['tickets']['T-1']['discussion']['comments']['pages'][1]['items'][0]['mr_links'] = []
    assert checker.check(packet)['status'] == 'incomplete'


def test_old_but_current_owner_confirmation_allowed(packet):
    blocked(packet)
    packet['mrs']['platform!8']['discussion']['notes']['pages'][0]['items'][0]['at'] = '2026-09-20T00:00:00Z'
    result = checker.check(packet)
    assert result['status'] == 'blocked'
    rendered = checker.markdown(result)
    assert '2026-09-20' in rendered and 'CODEOWNERS@a1' in rendered
    packet['blockers'][0]['quote'] = 'Invented owner confirmation'
    rejected = checker.check(packet)
    assert rejected['status'] == 'incomplete' and not rejected['blockers']
    assert 'Invented owner confirmation' not in checker.markdown(rejected)


def test_distinct_endpoints_and_nested_reply_pagination(packet):
    mr = packet['mrs']['platform!8']
    del mr['discussion']['discussions']
    assert checker.check(packet)['status'] == 'incomplete'
    empty = {'query_ref': 'ledger/github-endpoint', 'pages': [{'cursor': None, 'next': None, 'total': 0, 'items': []}]}
    mr['platform'] = 'github'
    mr['discussion'] = {k: copy.deepcopy(empty) for k in ('issue_comments', 'reviews', 'review_comments', 'review_threads')}
    thread = {'ref': 'thread-1', 'notes': copy.deepcopy(empty)}
    mr['discussion']['review_threads']['pages'][0].update(total=1, items=[thread])
    assert checker.check(packet)['status'] == 'ready'
    thread['notes']['pages'][0]['next'] = 'page-2'
    assert checker.check(packet)['status'] == 'incomplete'
    thread['notes']['pages'][0]['next'] = None
    del mr['discussion']['reviews']
    assert checker.check(packet)['status'] == 'incomplete'


def test_duplicate_notes_across_endpoints_are_deduplicated(packet):
    mr = packet['mrs']['platform!8']
    note = copy.deepcopy(mr['discussion']['notes']['pages'][0]['items'][0])
    mr['discussion']['discussions']['pages'][0].update(total=1, items=[{
        'ref': 'thread', 'notes': {'query_ref': 'ledger/thread-notes', 'pages': [
            {'cursor': None, 'next': None, 'total': 1, 'items': [note]}]}}])
    assert checker.check(packet)['status'] == 'ready'
    note['body'] = 'Conflicting newer copy'
    assert checker.check(packet)['status'] == 'incomplete'


def test_ticket_description_read_binding_required(packet):
    packet['tickets']['T-2']['inspected_ref'] = ''
    assert checker.check(packet)['status'] == 'incomplete'


def test_only_review_submissions_may_have_legitimately_empty_body(packet):
    note = packet['tickets']['T-1']['discussion']['comments']['pages'][1]['items'][0]
    note['body'] = ''
    assert checker.check(packet)['status'] == 'incomplete'
    note['body'] = 'Lifted; use platform API.'
    mr = packet['mrs']['platform!8']
    blank = copy.deepcopy(note)
    blank.update(ref='review-1', body='', mr_links=[])
    empty = {'query_ref': 'ledger/github-endpoint', 'pages': [{'cursor': None, 'next': None, 'total': 0, 'items': []}]}
    mr['platform'] = 'github'
    mr['discussion'] = {k: copy.deepcopy(empty) for k in ('issue_comments', 'reviews', 'review_comments', 'review_threads')}
    mr['discussion']['reviews']['pages'][0].update(total=1, items=[blank])
    assert checker.check(packet)['status'] == 'ready'
    mr['discussion']['review_comments']['pages'][0].update(total=1, items=[dict(blank, ref='comment-1')])
    assert checker.check(packet)['status'] == 'incomplete'


@pytest.mark.parametrize('surface', ['codex', 'gemini', 'claude', 'kiro', 'grok'])
@pytest.mark.parametrize('slug', ['engos-design-specify-change', 'engos-design-plan-implementation', 'engos-design-shaping'])
def test_caller_has_detached_executable_freshness_bundle(surface, slug, packet, tmp_path):
    # A caller package works with no sibling skill or source checkout present.
    import shutil
    from intent_pipeline.capability_resources import load_resource_bundle
    source = ROOT / f'.{surface}/skills/{slug}/resources'
    target = tmp_path / 'isolated-caller' / 'resources'
    shutil.copytree(source, target)
    loaded = load_resource_bundle(target, 'freshness')
    paths = {row['path']: row['sha256'] for row in loaded['resources']}
    assert 'references/freshness-sweep.md' in paths
    assert 'scripts/freshness_check.py' in paths
    for name in ('references/freshness-sweep.md', 'scripts/freshness_check.py'):
        assert (target / name).read_bytes() == (RESOURCES / name).read_bytes()
    evidence = tmp_path / 'packet.json'
    evidence.write_text(json.dumps(packet))
    result = subprocess.run([sys.executable, str(target / 'scripts/freshness_check.py'),
                             '--evidence', str(evidence)], capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == 'ready'
