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


def comments(packet):
    return packet['tickets']['T-1']['discussion']['streams']['comments']


def complete(packet):
    result = checker.check(packet)
    assert result['validation_status'] == 'complete', result['errors']
    assert result['semantic_review_pending'] is True
    assert 'status' not in result
    return result


def test_structural_transport_not_semantic_discovery(packet):
    result = complete(packet)
    assert result['coverage'] == {'tickets': 2, 'mrs': 2, 'notes': 3, 'events': 0, 'repos': 2}
    assert checker.TITLE in checker.markdown(result)
    # Deliberately opposite prose still passes structure: agent adjudication is required.
    packet['proposed_assessment'] = 'Build workaround'
    complete(packet)
    source = json.loads((RESOURCES / 'evals/lifted-blocker-sources.json').read_text())
    assert not {'changes', 'proposed_assessment', 'blockers'} & source.keys()


@pytest.mark.parametrize('fault', ['last_page', 'total', 'cursor', 'linked_ticket', 'linked_mr', 'repo', 'window', 'api', 'body', 'gap', 'unknown_citation', 'note_link', 'mr_link', 'duplicate_note', 'empty_roots', 'inventory', 'required_stream'])
def test_missing_evidence_is_incomplete(packet, fault):
    stream = comments(packet)
    if fault == 'last_page': stream['pages'].pop()
    elif fault == 'total': stream['pages'][1]['total'] = 3
    elif fault == 'cursor': stream['pages'][1]['cursor'] = 'wrong'
    elif fault == 'linked_ticket': del packet['tickets']['T-2']
    elif fault == 'linked_mr': del packet['mrs']['app!9']
    elif fault == 'repo': packet['merge_queries'].pop()
    elif fault == 'window': packet['merge_queries'][0]['since'] = '2026-11-01T15:00:00Z'
    elif fault == 'api': packet['interface_inspections'] = []
    elif fault == 'body': stream['pages'][1]['items'][0]['full_body'] = False
    elif fault == 'gap': packet['gaps'] = ['Denied T-3 discussion']
    elif fault == 'unknown_citation': packet['changes'][0]['evidence_refs'] = ['unread-api']
    elif fault == 'note_link': stream['pages'][1]['items'][0]['ticket_links'] = ['T-3']
    elif fault == 'mr_link': packet['mrs']['platform!8']['mr_links'] = ['platform!99']
    elif fault == 'duplicate_note': stream['pages'][1]['items'][0] = copy.deepcopy(stream['pages'][0]['items'][0])
    elif fault == 'empty_roots': packet['roots'] = []
    elif fault == 'inventory': packet['tickets']['T-1']['discussion']['inventory_ref'] = ''
    elif fault == 'required_stream': packet['tickets']['T-1']['discussion']['required_streams'].append('timeline')
    assert checker.check(packet)['validation_status'] == 'incomplete'


def excerpt(packet, note=None):
    note = note or comments(packet)['pages'][1]['items'][0]
    packet['blockers'] = [{'scope_id': 'tenant-export', 'owner': 'platform-owner',
        'note_ref': note['ref'], 'quote': note['body'], 'current_evidence_refs': ['platform-api@8'],
        'currency_assessment': 'Compare full later context and current interface.'}]


def test_lifted_quote_is_only_matched_source_excerpt(packet):
    excerpt(packet)
    result = complete(packet)
    assert result['matched_source_excerpts'][0]['quote'] == 'Blocker lifted; use P!8 API.'
    rendered = checker.markdown(result)
    assert 'Matched source excerpt' in rendered
    assert 'Owner confirmation' not in rendered and 'Status: blocked' not in rendered
    packet['blockers'][0]['owner'] = 'app-owner'
    comments(packet)['pages'][1]['items'][0]['author'] = 'app-owner'
    assert checker.check(packet)['validation_status'] == 'incomplete'


@pytest.mark.parametrize('fault', ['quote', 'currency', 'note', 'responsibility'])
def test_excerpt_bindings(packet, fault):
    excerpt(packet)
    if fault == 'quote': packet['blockers'][0]['quote'] = 'Invented'
    elif fault == 'currency': packet['blockers'][0]['current_evidence_refs'] = []
    elif fault == 'note': packet['blockers'][0]['note_ref'] = 'unread'
    else: packet['responsibilities'] = {}
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete' and not result['matched_source_excerpts']


def test_firstparty_confirmation_old_quote_and_anchor(packet):
    note = copy.deepcopy(comments(packet)['pages'][1]['items'][0])
    note.update(ref='internal-decision@1',source_ref='internal-decision',body='Export remains blocked for this scope.',at='2026-09-20T00:00:00Z',updated_at='2026-09-20T00:00:00Z',mr_links=[])
    packet['confirmation_records'] = [note]
    excerpt(packet, note)
    complete(packet)
    note['updated_at'] = '2026-11-12T00:00:00Z'
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_baselines_preserve_partial_report(packet):
    packet.update(baseline_mode='first_design',source_ref='T-1@revision',design_ref=None,design_at=None)
    assert 'No prior design exists' in checker.markdown(complete(packet))
    packet['baseline_mode'] = 'revision_comparison'
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete' and result['coverage']['notes'] == 3
    assert any('design_at unknown' in e for e in result['errors'])


def test_per_owner_receipts_and_zero_results(packet):
    full = packet['merge_queries'].pop(0)
    for owner in packet['owners']:
        for role in ('author', 'coauthor', 'merger'):
            q = copy.deepcopy(full)
            q.update(mode='per_owner',owner=owner,role=role,query_ref=f'app/{owner}/{role}')
            packet['merge_queries'].append(q)
    complete(packet)
    missing = packet['merge_queries'].pop()
    assert checker.check(packet)['validation_status'] == 'incomplete'
    packet['merge_queries'].append(missing)
    missing['pages'][0]['next'] = 'unread'
    assert checker.check(packet)['validation_status'] == 'incomplete'


def empty_stream(role='events'):
    return {'role':role,'query_ref':'synthetic/events','pages':[{'cursor':None,'next':None,'total':0,'items':[]}]}


@pytest.mark.parametrize('system,name,role', [('generic-tracker','comments','threads'), ('github','timeline','events'), ('gitlab','resource_state_events','events')])
def test_arbitrary_streams_nested_replies_and_event_links(packet, system, name, role):
    r = packet['tickets']['T-2'];r['system'] = system
    discussion = r['discussion'];discussion['required_streams'].append(name) if name not in discussion['required_streams'] else None
    stream = empty_stream(role);discussion['streams'][name] = stream
    note = copy.deepcopy(comments(packet)['pages'][1]['items'][0]);note.update(ref='event-or-reply',ticket_links=['T-1'],mr_links=[])
    if role == 'threads':
        nested = empty_stream('notes');nested['pages'][0].update(total=1,items=[note])
        record = {'ref':'thread','ticket_links':[],'mr_links':[],'notes':nested}
    else: record = note
    stream['pages'][0].update(total=1,items=[record])
    complete(packet)
    note['ticket_links'] = ['deep-ticket']
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert result['coverage']['tickets'] == 2 and result['attempted']['tickets'] == 3
    assert result['frontier']['tickets'] == ['deep-ticket']
    if role == 'threads':
        note['ticket_links'] = [];nested['pages'][0]['next'] = 'missing-reply'
        assert checker.check(packet)['validation_status'] == 'incomplete'


def test_transitive_codehost_ticket_adds_repo_without_mr(packet):
    ticket = copy.deepcopy(packet['tickets']['T-2'])
    ticket.update(system='github',source_kind='codehost_issue',repo_mapping={'kind':'native_repository','source_ref':'third/code#12@r1'},repo_refs=['third/code'],ticket_links=['T-1'],mr_links=[])
    packet['tickets']['third/code#12'] = ticket
    packet['mrs']['platform!8']['ticket_links'] = ['third/code#12']
    assert checker.check(packet)['validation_status'] == 'incomplete'
    packet['repos'].append('third/code')
    q = copy.deepcopy(packet['merge_queries'][0]);q.update(repo_ref='third/code',query_ref='third/all')
    packet['merge_queries'].append(q)
    complete(packet)


def test_listing_cannot_support_interface_claim(packet):
    merge = {'ref':'app!77','merged_at':'2026-11-09T10:00:00Z','participation':{'author':['other'],'coauthor':[],'merger':[]}}
    packet['merge_queries'][0]['pages'][0].update(total=1,items=[merge])
    packet['changes'][0]['evidence_refs'] = ['app!77']
    assert checker.check(packet)['validation_status'] == 'incomplete'
    packet['changes'][0].update(kind='status',evidence_refs=['T-1#c2'])
    complete(packet)


def test_duplicate_notes_conflicting_versions_and_owner_merge_full_read(packet):
    mr=packet['mrs']['platform!8'];note=copy.deepcopy(mr['discussion']['streams']['notes']['pages'][0]['items'][0])
    nested=empty_stream('notes');nested['pages'][0].update(total=1,items=[note])
    mr['discussion']['streams']['discussions']['pages'][0].update(total=1,items=[{'ref':'thread','ticket_links':[],'mr_links':[],'notes':nested}])
    assert complete(packet)['coverage']['notes'] == 3
    note['body']='different revision'
    assert checker.check(packet)['validation_status'] == 'incomplete'
    del packet['mrs']['platform!8']
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_cli_errors_and_v1_recollection(packet, tmp_path):
    path=tmp_path/'packet.json';command=[sys.executable,str(SCRIPT),'--evidence',str(path)]
    for value,code in [(packet,0),(dict(packet,gaps=['denied']),1),(dict(packet,schema_version='FreshnessEvidence.v1'),2)]:
        path.write_text(json.dumps(value));r=subprocess.run(command,capture_output=True,text=True)
        assert r.returncode == code and not r.stderr
        assert 'status' not in json.loads(r.stdout)
    for raw in ['null','{','{"bad":NaN}','{"x":1,"x":2}']:
        path.write_text(raw);r=subprocess.run(command,capture_output=True,text=True)
        assert r.returncode == 2 and not r.stderr
        assert 'Traceback' not in r.stdout


@pytest.mark.parametrize('role', ['author', 'coauthor', 'merger'])
def test_owner_selection_covers_each_participation_role(packet, role):
    merge = packet['merge_queries'][1]['pages'][0]['items'][0]
    merge['participation'] = {key: ['platform-owner'] if key == role else []
                              for key in ('author', 'coauthor', 'merger')}
    complete(packet)
    # Removing the only note-link cannot hide an owner merge selected by its role.
    comments(packet)['pages'][1]['items'][0]['mr_links'] = []
    del packet['mrs']['platform!8']
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_owner_implementation_read_and_query_receipts_survive_output(packet):
    result = complete(packet)
    scope = result['queries'][0]['scope']
    assert scope['repo_ref'] == 'app' and scope['mode'] == 'repo_wide'
    assert result['queries'][0]['cursors'] == [{'cursor': None, 'next': None}]
    packet['interface_inspections'] = []
    packet['changes'][0].update(kind='status',evidence_refs=['T-1#c2'])
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_channel_empty_body_waiver_cannot_erase_ordinary_comment(packet):
    note = comments(packet)['pages'][1]['items'][0]
    note['body'] = ''
    assert checker.check(packet)['validation_status'] == 'incomplete'
    comments(packet)['allow_empty_body'] = True
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete' and result['coverage']['notes'] == 2
    note['full_body'] = False
    assert checker.check(packet)['validation_status'] == 'incomplete'


@pytest.mark.parametrize('collection,ref', [('tickets', 'T-2'), ('mrs', 'app!9')])
@pytest.mark.parametrize('fault', ['full_body', 'revision', 'inspected_ref', 'body', 'absent_revision'])
def test_incomplete_record_is_attempted_frontier_not_read(packet, collection, ref, fault):
    record = packet[collection][ref]
    if fault == 'absent_revision':
        del record['revision']
    else:
        record[fault] = False if fault == 'full_body' else None if fault == 'body' else ''
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert result['attempted'][collection] == 2
    assert result['coverage'][collection] == 1
    assert result['frontier'][collection] == [ref]
    assert result['queries'] and result['errors']


@pytest.mark.parametrize('fault', ['full_body', 'revision', 'body'])
def test_incomplete_note_is_not_counted_read(packet, fault):
    note = comments(packet)['pages'][1]['items'][0]
    note[fault] = False if fault == 'full_body' else None if fault == 'body' else ''
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert result['coverage']['notes'] == 2
    assert result['coverage']['mrs'] == 2  # Links still expand despite incomplete source.


def test_every_linked_mr_needs_actual_content_inspection(packet):
    packet['interface_inspections'] = [entry for entry in packet['interface_inspections']
                                       if entry['subject_ref'] != 'app!9']
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert 'linked/selected MR diff/content inspection missing' in result['errors']


@pytest.mark.parametrize('fault', ['blank_api', 'only_diff', 'empty_diff_without_receipt'])
def test_positive_interface_evidence_cannot_be_blank_or_diff(packet, fault):
    inspected = packet['interface_inspections'][0]
    if fault == 'blank_api': inspected['body'] = ''
    elif fault == 'only_diff': inspected['kind'] = 'diff'
    else: inspected.update(kind='diff', body='')
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_verified_empty_diff_covers_read_but_not_positive_api(packet):
    inspection = packet['interface_inspections'][1]
    inspection.update(body='',empty_diff_ref='app!9/diff@commit9#zero-files')
    complete(packet)
    packet['changes'][0]['evidence_refs'] = [inspection['ref']]
    assert checker.check(packet)['validation_status'] == 'incomplete'
    packet['changes'][0].update(kind='status',evidence_refs=[inspection['ref']])
    complete(packet)


def test_unresolved_merge_participation_is_gap(packet):
    packet['merge_queries'][0]['pages'][0].update(total=1,items=[{
        'ref':'app!77','merged_at':'2026-11-09T10:00:00Z',
        'participation':{'author':[],'coauthor':[],'merger':[]}}])
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert any('attribution gap' in error for error in result['errors'])


@pytest.mark.parametrize('field', ['design_ref', 'design_at'])
def test_first_design_rejects_prior_design_coordinates(packet, field):
    packet.update(baseline_mode='first_design',source_ref='T-1@revision',design_ref=None,design_at=None)
    packet[field] = 'design@r1' if field == 'design_ref' else '2026-10-01T12:00:00Z'
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert 'No prior design exists.' not in checker.markdown(result)


def test_external_no_repository_mapping_requires_provenance_and_native_repo(packet):
    ticket = packet['tickets']['T-2']
    ticket.update(source_kind='external_ticket',repo_refs=[],repo_mapping={
        'kind':'no_repository','source_ref':'T-2@revision#coordination-only'})
    complete(packet)
    ticket['repo_mapping']['source_ref'] = ''
    assert checker.check(packet)['validation_status'] == 'incomplete'
    ticket['repo_mapping'].update(kind='unresolved',source_ref='T-2@revision')
    assert checker.check(packet)['validation_status'] == 'incomplete'
    ticket['repo_mapping']['kind'] = 'no_repository'
    ticket['source_kind'] = 'codehost_issue'
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_gitlab_native_state_event_without_invented_body_or_edit_time(packet):
    # Provider-shaped event fields from the Resource State Events API, not a note.
    native = {'id':143,'user':{'id':1,'name':'Platform Owner','username':'platform-owner',
                             'state':'active','web_url':'https://gitlab.example.test/platform-owner'},
              'created_at':'2026-11-10T13:00:00Z','resource_type':'MergeRequest',
              'resource_id':8,'source_commit':None,'source_merge_request_id':None,'state':'closed'}
    event = {'ref':'platform!8#state143','source_ref':'ledger/resource-state-events/143',
             'revision':'state-event143@receipt1','author':native['user']['username'],
             'at':native['created_at'],'content':native,'full_body':True,
             'edit_metadata':{'semantics':'not_exposed',
                              'source_ref':'https://docs.gitlab.com/api/resource_state_events/#list-project-merge-request-state-events'},
             'ticket_links':[],'mr_links':[]}
    discussion = packet['mrs']['platform!8']['discussion']
    discussion['inventory_ref'] = 'ledger/provider-capabilities@1#notes-discussions-resource-events'
    discussion['required_streams'].append('resource_state_events')
    stream = empty_stream('events');stream['pages'][0].update(total=1,items=[event])
    discussion['streams']['resource_state_events'] = stream
    result = complete(packet)
    assert result['coverage']['notes'] == 3
    assert result['coverage']['events'] == 1
    assert 'body' not in event and 'updated_at' not in event
    del event['edit_metadata']['source_ref']
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_editable_note_missing_observed_edit_time_is_named_gap(packet):
    note = comments(packet)['pages'][1]['items'][0]
    del note['updated_at']
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete' and result['coverage']['notes'] == 2
    assert any('edit metadata missing' in error for error in result['errors'])


def test_github_rest_review_body_read_separate_from_edit_currency(packet):
    # Full REST review submission response: submitted_at/commit_id, no updated_at.
    native = {'id':80,'node_id':'review80','user':{'login':'platform-owner','id':1},
              'body':'Use the tenant API for the reviewed scope.','state':'APPROVED',
              'html_url':'https://github.example.test/platform/repo/pull/8#pullrequestreview-80',
              'submitted_at':'2026-11-10T13:00:00Z','commit_id':'commit8',
              'author_association':'COLLABORATOR'}
    review = {'ref':native['html_url'],'source_ref':'ledger/rest-review80@receipt1',
              'revision':native['commit_id']+'#review80@receipt1',
              'record_kind':'review_submission','author':native['user']['login'],
              'at':native['submitted_at'],'observed_at':'2026-11-11T15:00:03Z',
              'body':native['body'],'native_content':native,'full_body':True,
              'edit_metadata':{'semantics':'not_exposed',
                               'source_ref':'https://docs.github.com/en/rest/pulls/reviews#list-reviews-for-a-pull-request'},
              'ticket_links':[],'mr_links':[]}
    discussion = packet['mrs']['platform!8']['discussion']
    discussion['required_streams'].append('reviews')
    stream = empty_stream('notes');stream['pages'][0].update(total=1,items=[review])
    discussion['streams']['reviews'] = stream
    result = checker.check(packet)
    assert result['coverage']['notes'] == 4 and result['coverage']['events'] == 0
    assert result['validation_status'] == 'complete' and result['semantic_review_pending']
    assert 'status' not in result and not result['errors']
    assert result['currency_limits'][0]['ref'] == review['ref']
    assert 'Full review body read' in result['currency_limits'][0]['limitation']
    assert 'updated_at' not in review
    # Collection is anchored at start; acquisition naturally occurs afterward.
    assert result['currency_limits'][0]['observed_at'] == '2026-11-11T15:00:03Z'
    assert result['until'] == '2026-11-11T15:00:00+00:00'
    review['observed_at'] = '2026-11-10T12:59:59Z'
    impossible = checker.check(packet)
    assert impossible['validation_status'] == 'incomplete'
    assert impossible['coverage']['notes'] == 3
    assert any('observation precedes submission' in e for e in impossible['errors'])
    review['observed_at'] = '2026-11-11T15:00:03Z'
    # A read-body citation is preserved despite the separate currency limitation.
    packet['changes'][0].update(kind='status',evidence_refs=[review['ref']])
    assert not any('change cites unread' in e for e in checker.check(packet)['errors'])
    del review['edit_metadata']['source_ref']
    unknown = checker.check(packet)
    assert unknown['coverage']['notes'] == 3
    assert any('edit metadata missing' in e for e in unknown['errors'])
    review['edit_metadata']['source_ref'] = 'ledger/rest-review-schema@1'
    review['updated_at'] = '2026-11-12T00:00:00Z'
    assert checker.check(packet)['validation_status'] == 'incomplete'
    del review['updated_at']
    review['full_body'] = False
    assert checker.check(packet)['validation_status'] == 'incomplete'


def test_github_mixed_timeline_counts_notes_events_and_follows_crossref(packet):
    discussion = packet['tickets']['T-1']['discussion']
    discussion['inventory_ref'] = 'ledger/graphql-schema@1#IssueTimelineItems'
    original = comments(packet)['pages'][1]['items'][0]
    duplicate = copy.deepcopy(original)
    duplicate.update(source_ref='ledger/timeline-page1#IssueComment',
                     observed_at='2026-11-11T15:00:03Z',item_kind='note',
                     kind_source_ref='ledger/graphql-schema@1#IssueComment')
    timeline_only = copy.deepcopy(original)
    timeline_only.update(ref='T-1#timeline-only',source_ref='ledger/timeline-page1#IssueComment2',
                         body='Additional complete timeline-only comment.',mr_links=[],
                         item_kind='note',kind_source_ref='ledger/graphql-schema@1#IssueComment')
    native = {'__typename':'CrossReferencedEvent','id':'crossref1',
              'createdAt':'2026-11-10T14:00:00Z','actor':{'login':'platform-owner'},
              'source':{'__typename':'Issue','url':'https://github.example.test/app/repo/issues/12'}}
    event = {'ref':'T-1#crossref1','source_ref':'ledger/timeline-page1#CrossReferencedEvent',
             'revision':'crossref1@receipt1','author':native['actor']['login'],
             'at':native['createdAt'],'content':native,'full_body':True,
             'item_kind':'event','kind_source_ref':'ledger/graphql-schema@1#CrossReferencedEvent',
             'edit_metadata':{'semantics':'not_exposed','source_ref':'ledger/graphql-schema@1#CrossReferencedEvent'},
             'ticket_links':['timeline-linked'],'mr_links':[]}
    stream = empty_stream('mixed');stream['query_ref']='ledger/timeline-page1'
    stream['pages'][0].update(total=3,items=[duplicate,timeline_only,event])
    discussion['required_streams'].append('timeline');discussion['streams']['timeline']=stream
    linked = copy.deepcopy(packet['tickets']['T-2'])
    linked.update(ticket_links=[],mr_links=[],inspected_ref='timeline-linked@r1')
    packet['tickets']['timeline-linked']=linked
    result = complete(packet)
    assert result['coverage']['notes'] == 4 and result['coverage']['events'] == 1
    assert result['coverage']['tickets'] == 3
    receipt = next(q for q in result['queries'] if q['query_ref']=='ledger/timeline-page1')
    assert receipt['items'] == 3 and receipt['cursors'] == [{'cursor':None,'next':None}]
    assert receipt['item_provenance'][0]['source_ref'] == duplicate['source_ref']
    del packet['tickets']['timeline-linked']
    missing = checker.check(packet)
    assert missing['validation_status'] == 'incomplete'
    assert missing['frontier']['tickets'] == ['timeline-linked']


@pytest.mark.parametrize('divergence', ['body', 'revision', 'author', 'ticket_links'])
def test_gitlab_overlap_deduplicates_content_not_acquisition_receipts(packet, divergence):
    mr = packet['mrs']['platform!8']
    original = mr['discussion']['streams']['notes']['pages'][0]['items'][0]
    duplicate = copy.deepcopy(original)
    duplicate.update(source_ref='ledger/thread-acquisition#note1',observed_at='2026-11-11T15:00:03Z')
    original['observed_at']='2026-11-11T15:00:01Z'
    nested=empty_stream('notes');nested['query_ref']='ledger/thread-acquisition'
    nested['pages'][0].update(total=1,items=[duplicate])
    mr['discussion']['streams']['discussions']['pages'][0].update(total=1,items=[{
        'ref':'thread-overlap','ticket_links':[],'mr_links':[],'notes':nested}])
    result = complete(packet)
    assert result['coverage']['notes'] == 3
    receipts = [row for query in result['queries'] for row in query['item_provenance']
                if row['ref']==original['ref']]
    assert {row['source_ref'] for row in receipts} == {original['source_ref'],duplicate['source_ref']}
    assert len({row['observed_at'] for row in receipts}) == 2
    duplicate[divergence] = ['T-1'] if divergence=='ticket_links' else 'different'
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert any('conflicting duplicate' in error for error in result['errors'])


def test_mixed_stream_empty_exceptions_are_bound_to_item_kind_and_source(packet):
    ordinary = copy.deepcopy(comments(packet)['pages'][1]['items'][0])
    ordinary.update(ref='ordinary-blank',body='',mr_links=[],item_kind='note',
                    kind_source_ref='ledger/schema#IssueComment')
    review = {'ref':'review-empty','source_ref':'ledger/reviews/80','revision':'commit8#review80',
              'record_kind':'review_submission','item_kind':'note',
              'kind_source_ref':'ledger/rest-schema#PullRequestReview',
              'author':'platform-owner','at':'2026-11-10T13:00:00Z',
              'observed_at':'2026-11-11T15:00:03Z','body':'','full_body':True,
              'edit_metadata':{'semantics':'not_exposed','source_ref':'ledger/rest-schema#PullRequestReview'},
              'ticket_links':[],'mr_links':[]}
    event = {'ref':'event-empty','source_ref':'ledger/events/1','revision':'event1',
             'item_kind':'event','kind_source_ref':'ledger/schema#EmptyEvent',
             'author':'platform-owner','at':'2026-11-10T13:00:00Z','body':'','full_body':True,
             'edit_metadata':{'semantics':'immutable','source_ref':'ledger/schema#EmptyEvent'},
             'ticket_links':[],'mr_links':[]}
    discussion = packet['mrs']['platform!8']['discussion']
    discussion['required_streams'].append('mixed')
    stream = empty_stream('mixed');stream['allow_empty_body']=True
    stream['pages'][0].update(total=3,items=[ordinary,review,event])
    discussion['streams']['mixed']=stream
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete'
    assert result['coverage']['notes'] == 4 and result['coverage']['events'] == 1
    # The legitimate empty records pass; only the erased ordinary comment holds.
    ordinary['body']='Complete ordinary comment.'
    result = complete(packet)
    assert result['coverage']['notes'] == 5 and result['coverage']['events'] == 1
    assert result['currency_limits'][0]['ref'] == 'review-empty'
    del review['kind_source_ref']
    result = checker.check(packet)
    assert result['validation_status'] == 'incomplete' and result['coverage']['notes'] == 4


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
    assert json.loads(result.stdout)['validation_status'] == 'complete'
