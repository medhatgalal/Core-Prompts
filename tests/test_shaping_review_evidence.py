"""FAKE host/semantic observations: mechanical evidence only, no actual review."""
from test_shaping_runtime import runtime, workshop, prepare, advance, version, fake_receipt
import pytest


def test_review_policy_opt_in(workshop):
    from test_shaping_runtime import write_json
    policy = workshop.policy()
    policy.update(policy_id='FAKE-new-policy', review_evidence=True)
    path = write_json(workshop.root / 'sources/new-policy.json', policy)
    with pytest.raises(Exception, match='participation'):
        workshop.reopen('G0', 'Explicit fixture policy migration', version(workshop), path)
        advance(workshop, through=2)
        prepare(workshop, 'G3')


def test_png_decoding(runtime):
    with pytest.raises(runtime.Hold, match='PNG'):
        runtime.validate_review_png(b'not an image')


def test_legacy_receipt_unchanged(workshop):
    advance(workshop)
    assert workshop.status()['content_ready']

import base64
import hashlib
import json
import struct
import zlib
from copy import deepcopy
from test_shaping_runtime import write_json


def png(blank=False):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    pixels = bytes([0, 0, 0, 0, 255, 255, 255, 0, 255, 0, 0, 0, 0, 255])
    if blank: pixels = bytes(14)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b'')


def bound_quote(rt, path, locator='1:1', candidate=None):
    raw = (candidate / path).read_bytes() if candidate else (rt.root / path).read_bytes()
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'locator': locator,
            'quote': b''.join(raw.splitlines(keepends=True)[int(locator.split(':')[0])-1:int(locator.split(':')[1])]).decode()}


@pytest.fixture
def package(workshop, request):
    rt = workshop
    reported = getattr(request, "param", None)
    policy = rt.policy(); policy.update(policy_id='shaping-gates.v4+rubric.v4', review_evidence=True, shaping_loop=True)
    policy['gates']['G2']['required_outputs'].append('research-coverage.json')
    policy['gates']['G3']['required_outputs'].append('shape-set.json')
    rt.reopen('G0', 'Explicit fixture future profile', version(rt), write_json(rt.root / 'sources/new-policy.json', policy))
    advance(rt, through=1)
    code = rt.root / 'sources/receiver.py'; code.write_text('def receive(item):\n    return item.kind == "landed" and item.text == item.id\n' if reported else 'def receive(item):\n    return item.kind == "landed"\n')
    proof = ('before the slice is on main, a person can see a judgment of that slice and can see that the judge is not the author.' if reported else 'FAKE proof: a person sees an independent judgment before landing.')
    (rt.root / 'sources/proof.txt').write_text(proof + '\n')
    from test_shaping_runtime import accept_fixture
    research_order, research_candidate = prepare(rt, 'G2', extra_inputs=['sources/receiver.py', 'sources/proof.txt'])
    source_quote = bound_quote(rt, 'sources/receiver.py', '1:2')
    write_json(research_candidate / 'research-coverage.json', {'schema_version': 1, 'opened': [
        {'path': source_quote['path'], 'sha256': source_quote['sha256'], 'locators': ['1:2']}]})
    accept_fixture(rt, research_order, research_candidate)
    host = {'schema_version': 1, 'run_id': 'fixture-run', 'work_order_id': 'G3-evidence', 'host': 'FAKE-HOST', 'observed': True,
            'author': 'fixture-author', 'reviewer': 'fixture-reviewer', 'contributors': ['fixture-author'], 'repairs': []}
    write_json(rt.root / 'sources/participation.json', host)
    # prepare fixture helper intentionally lacks participation; construct exact ordinary spec.
    # Reuse common prepare fields, adding bound future-policy host participation.
    spec = deepcopy(rt._load()['orders']['G2-a'])
    allowed = ('schema_version', 'work_order_id', 'gate', 'author', 'reviewer', 'inputs', 'source_revision', 'resource_revision',
               'skill_allowlist', 'original_constraints', 'assigned_questions', 'source_access_scope', 'effort_bound', 'stop_conditions')
    spec = {k: spec[k] for k in allowed}; spec.update(gate='G3', work_order_id='G3-evidence', participation_evidence='sources/participation.json')
    spec['inputs'] += ['sources/participation.json']
    spec['seam_applicability'] = {'land': 'existing'}
    spec['accepted_proof'] = {'text': proof, 'source': bound_quote(rt, 'sources/proof.txt')}
    spec['shape_basis'] = [{'path': source_quote['path'], 'sha256': source_quote['sha256'], 'locators': ['1:2']}]
    order = rt.prepare(spec, version(rt)); candidate = rt.root / order['candidate_root']; candidate.mkdir(parents=True)
    for name in rt.policy()['gates']['G3']['required_outputs']:
        (candidate / name).write_text('FAKE candidate\n')
    (candidate / 'sequence.mmd').write_text('sequenceDiagram\n    Person->>Land: item.kind is landed\n')
    (candidate / 'evidence.txt').write_text('FAKE semantic evidence; no truth claim\n')
    for name in ('component', 'sequence', 'data-flow'): (candidate / f'{name}.png').write_bytes(png())
    source = bound_quote(rt, 'sources/receiver.py', '1:2')
    plan = {'schema_version': 1, 'proof': proof, 'proof_source': bound_quote(rt, 'sources/proof.txt'), 'seams': [
        {'id': 'land', 'applicability': 'existing', 'reason': 'FAKE existing receiving seam', 'receiver': 'receive',
         'field': 'item.kind', 'field_type': 'string', 'expression': 'item.kind == "landed"',
         'input': 'item.kind', 'message': 'item.kind is landed', 'proof': proof, 'read': source}]}
    write_json(candidate / 'shape-set.json', {'schema_version': 1, 'selected_parts': ['proposed-judgment'], 'walk_away_item': 'FAKE no supported predicate',
        'claims': [{'id': 'land', 'status': 'existing', 'load_bearing': True, 'evidence': spec['shape_basis'], 'basis_claims': []},
                   {'id': 'proposed-judgment', 'status': 'proposed_extension', 'load_bearing': True, 'evidence': [], 'basis_claims': ['land']}]})
    if reported:
        plan['seams'][0].update(reason='Supplied/unverified C1: the person is not a new caller', expression='the observation holds', input='the observation holds', message='judge is not author')
        (candidate / 'sequence.mmd').write_text('sequenceDiagram\n    Person->>Land: judge is not author\n')
        write_json(candidate / 'reported-context.json', {'label': 'SUPPLIED/UNVERIFIED historical facts; no protected reads', 'stored_receipt': 'G3-shape-a1', 'stored_verdict': 'pass', 'stored_findings': [], 'stored_overall_report': 'about 4.083', 'historical_dimensions': None, 'synthetic_scores_not_historical': [5]+[4]*11, 'table_accept': '1. accept', 'funded': 'visible judgment', 'outside_scope': ['Dashboard','B1','U2'], 'original_renders': ['component.mmd','sequence.mmd','data-flow.mmd'], 'question_report': 'unanswered in-scope blocking=false without independence quote'})
    write_json(candidate / 'review-plan.json', plan)
    write_json(candidate / 'questions.json', [{'id': 'Q1', 'blocking': False, 'in_scope': True, 'status': 'deferred', 'evidence': [],
             'decision_id': None, 'dependency_evidence': [], 'evidence_standard': 'FAKE scoped question',
             'details': {'text': 'Does the caller need another dashboard?', 'respondent': 'human-owner'}}])
    write_json(candidate / 'decisions.json', [])
    seal = rt.seal(order['work_order_id'], version(rt)); order = rt._load()['orders'][order['work_order_id']]
    receipt = fake_receipt(rt, order, seal); receipt['schema_version'] = 2
    packet = seal['review_packet']
    receipt['review_evidence'] = {'schema_version': 1, 'packet_hash': hashlib.sha256(rt.__class__.__module__.encode()).hexdigest(),
          'host': {'identity': 'FAKE-HOST', 'reviewer': order['reviewer']['identity'], 'observed': True, 'return_hash': seal['return_hash']},
          'openings': packet['entries'], 'renders': {},
          'seams': [{'id': 'land', 'predicate_status': 'grounded', 'read_support': True, 'applicability_supported': True, 'message_matches': True, 'explanation': 'FAKE semantic observation: proposed behavior absent is legal'}],
          'questions': [{'id': 'Q1', 'text': 'Does the caller need another dashboard?', 'proof': proof, 'depends': False,
                        'source': bound_quote(rt, 'sources/proof.txt'), 'independence_supported': True, 'respondent': 'human-owner', 'answer_observation': None}],
          'semantic_audit': {'performed': True, 'consistent': True, 'contradictions': [], 'explanation': 'FAKE independent contradiction audit'}}
    # Use runtime canonical JSON hash; no host authenticity claimed by these fake records.
    receipt['review_evidence']['packet_hash'] = hashlib.sha256((json.dumps(packet, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()
    for source in ('component.mmd', 'sequence.mmd', 'data-flow.mmd'):
        name = source.replace('.mmd', '.png')
        receipt['review_evidence']['renders'][source] = {'source_hash': seal['subject'][source], 'path': name, 'sha256': seal['subject'][name],
           'pixels_path': name, 'pixels_sha256': seal['subject'][name], 'opened': True, 'visible': True, 'labels': True, 'connectors': True,
           'source_agreement': True, 'explanation': 'FAKE pixel inspection; no actual independent visual review'}
    host_record = {'schema_version': 1, 'run_id': order['run_id'], 'work_order_id': order['work_order_id'],
        'packet_hash': receipt['review_evidence']['packet_hash'], 'host': receipt['review_evidence']['host'], 'openings': packet['entries'],
        'renders': {key: {field: render[field] for field in ('source_hash','path','sha256','pixels_path','pixels_sha256','opened')}
                    for key, render in receipt['review_evidence']['renders'].items()}, 'answers': {}, 'contributors': ['fixture-author']}
    sidecar = write_json(rt.root / 'sources/host-review.json', host_record)
    observation = rt.review_observation(order['work_order_id'], 'sources/host-review.json', version(rt))
    receipt['review_evidence']['host_record'] = observation['binding']
    order = rt._load()['orders'][order['work_order_id']]
    if reported:
        values = [5]+[4]*11
        for name, value in zip(receipt['scores']['dimensions'], values): receipt['scores']['dimensions'][name]['score'] = value
        receipt['scores'].update(team_mean=29/7, pitch_mean=4, overall=49/12)
    return rt, order, candidate, receipt


def assess(package, acceptance=True):
    rt, order, candidate, receipt = package
    rt._review(receipt, rt._load(), order, rt._candidate(rt._load(), order)[0], acceptance=acceptance)


def finding(package, route, check, item):
    rt, order, candidate, receipt = package
    receipt['assessments'][check]['outcome'] = 'unverifiable' if route == 'review_hold' else 'fail'
    receipt['verdict'] = 'fail'
    receipt['findings'].append({'id': f'F{len(receipt["findings"])+1}', 'check': check, 'item': item, 'route': route, 'status': 'unresolved',
      'source': (bound_quote(rt, item, candidate=candidate) if route == 'review_hold' and item.endswith('.mmd') else bound_quote(rt, 'sources/receiver.py', '1:2') if item in ('land', 'semantic-audit') else bound_quote(rt, 'sources/proof.txt')), 'repair': 'FAKE concrete repair: supply bound evidence',
      'respondent': 'human-owner' if route == 'respondent' else None, 'prerequisite': None})


def test_grounded_proposed_behavior_open_question_passes(package):
    assess(package)


@pytest.mark.parametrize('values,reason', [([3,5]+[4]*10,None), ([3]*12,'overall below'), ([2]+[5]*11,'dimension below'),
                                         ([True]+[4]*11,'invalid finite score'), ([float('nan')]+[4]*11,'invalid finite score'), ([float('inf')]+[4]*11,'invalid finite score')])
def test_score_floors(package, values, reason):
    receipt = package[3]; scores = receipt['scores']; names = list(scores['dimensions'])
    for name, value in zip(names, values): scores['dimensions'][name]['score'] = value
    scores.update(team_mean=sum(values[:7])/7, pitch_mean=sum(values[7:])/5, overall=sum(values)/12)
    # Actual rubric split is defined by runtime, not assumed fixture ordering.
    if reason:
        with pytest.raises(Exception, match=reason): assess(package)
    else: assess(package)

@pytest.mark.parametrize('route,change,check,item', [
    ('review_hold', 'pixels', 'diagrams_visual', 'component.mmd'),
    ('research', 'predicate', 'contracts_security', 'land'),
    ('shaping', 'message', 'contracts_security', 'land'),
    ('respondent', 'question', 'workstreams_proof', 'Q1')])
def test_typed_returns_and_unchanged_gate(package, route, change, check, item):
    receipt = package[3]; evidence = receipt['review_evidence']
    if change == 'pixels': evidence['renders'].pop('component.mmd')
    elif change == 'predicate': evidence['seams'][0]['predicate_status'] = 'missing'
    elif change == 'message': evidence['seams'][0]['message_matches'] = False
    else: evidence['questions'][0]['depends'] = True
    with pytest.raises(Exception, match='missing relevant typed finding'): assess(package, False)
    finding(package, route, check, item)
    assess(package, False)
    assert receipt['next_state'] == 'G3'
    with pytest.raises(Exception, match='review evidence unresolved'): assess(package)


def test_independent_failures_are_preserved(package):
    evidence = package[3]['review_evidence']
    evidence['renders'].pop('component.mmd'); evidence['seams'][0]['predicate_status'] = 'missing'
    evidence['questions'][0]['independence_supported'] = False
    finding(package, 'review_hold', 'diagrams_visual', 'component.mmd')
    with pytest.raises(Exception, match='missing relevant typed finding'): assess(package, False)
    finding(package, 'research', 'contracts_security', 'land')
    finding(package, 'respondent', 'workstreams_proof', 'Q1')
    assess(package, False)
    assert len(package[3]['findings']) == 3


@pytest.mark.parametrize('tamper,reason', [('packet','packet binding'), ('open','ordered host openings'), ('host','host observation'),
   ('quote','source quote/span'), ('span','line bounds'), ('crossrun','receipt binding'), ('sourcehash','render/source'),
   ('renderhash','render packet'), ('schema','receipt v2'), ('state','verdict/state'), ('aggregate','incorrect overall'), ('audit','contradiction audit')])
def test_bound_evidence_tamper(package, tamper, reason):
    receipt = package[3]; evidence = receipt['review_evidence']
    if tamper == 'packet': evidence['packet_hash'] = '0'*64
    elif tamper == 'open': evidence['openings'] = list(reversed(evidence['openings']))
    elif tamper == 'host': evidence['host']['observed'] = False
    elif tamper == 'quote': evidence['questions'][0]['source']['quote'] = 'Arbitrary nondependence quote'
    elif tamper == 'span': evidence['questions'][0]['source']['locator'] = '99:99'
    elif tamper == 'crossrun': receipt['run_id'] = 'other-run'
    elif tamper == 'sourcehash': evidence['renders']['component.mmd']['source_hash'] = '0'*64
    elif tamper == 'renderhash': evidence['renders']['component.mmd']['sha256'] = '0'*64
    elif tamper == 'schema': receipt['schema_version'] = 1
    elif tamper == 'state': receipt['next_state'] = 'G2'
    elif tamper == 'aggregate': receipt['scores']['overall'] = 5
    else: evidence['semantic_audit']['performed'] = False
    with pytest.raises(Exception, match=reason): assess(package)


def test_semantic_contradiction_observation_requires_relevant_finding(package):
    package[3]['review_evidence']['seams'][0]['predicate_status'] = 'missing'
    audit = package[3]['review_evidence']['semantic_audit']; audit['consistent'] = False
    audit['contradictions'] = [{'id': 'semantic-audit', 'check': 'contracts_security', 'item': 'land', 'route': 'research',
        'rationale_path': 'scores.dimensions.solution_sharpness.rationale', 'rationale_quote': package[3]['scores']['dimensions']['solution_sharpness']['rationale'],
        'source': bound_quote(package[0], 'sources/receiver.py', '1:2'), 'explanation': 'FAKE reviewer semantic interpretation of missing predicate'}]
    with pytest.raises(Exception, match='missing relevant typed finding'): assess(package, False)
    finding(package, 'research', 'contracts_security', 'land')
    finding(package, 'research', 'contracts_security', 'semantic-audit')
    assess(package, False)


@pytest.mark.parametrize('kind', ['comment', 'unrelated-field', 'unsupported-applicability'])
def test_grounding_is_independent_semantic_observation(package, kind):
    judgment = package[3]['review_evidence']['seams'][0]
    if kind == 'unsupported-applicability': judgment['applicability_supported'] = False
    else: judgment['read_support'] = False
    judgment['explanation'] = 'FAKE independent source finding: ' + kind
    finding(package, 'research', 'contracts_security', 'land')
    assess(package, False)


def test_irrelevant_finding_cannot_hide_missing_predicate(package):
    package[3]['review_evidence']['seams'][0]['predicate_status'] = 'missing'
    finding(package, 'research', 'contracts_security', 'unrelated')
    with pytest.raises(Exception, match='missing relevant typed finding'): assess(package, False)


def test_unresolved_predicate_cannot_pass_empty_findings(package):
    package[3]['review_evidence']['seams'][0]['predicate_status'] = 'missing'
    with pytest.raises(Exception, match='missing relevant typed finding'): assess(package, False)


def test_authorized_respondent_is_required(package):
    review = package[3]['review_evidence']['questions'][0]; review['depends'] = True
    review['answer_observation'] = {'identity': 'fixer', 'authority': 'FAKE', 'observed': True, 'source': review['source']}
    with pytest.raises(Exception, match='unauthorized respondent'): assess(package, False)


def test_changed_sealed_candidate_holds(package):
    rt, order, candidate, receipt = package
    (candidate / 'component.png').write_bytes(png(blank=True))
    with pytest.raises(Exception, match='candidate bytes changed after seal'):
        rt.accept(write_json(rt.root / 'review.json', receipt), version(rt))


@pytest.mark.parametrize('raw,reason', [(b'not png','invalid PNG'), (png(True),'blank PNG'), (png()[:-4],'truncated PNG')])
def test_actual_png_invalid_blank_truncated(runtime, raw, reason):
    with pytest.raises(runtime.Hold, match=reason): runtime.validate_review_png(raw)


def test_actual_png_decodes_self_contained(runtime):
    assert runtime.validate_review_png(png()) == (2,2)


@pytest.mark.parametrize('raw', [b'<svg/>', b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>',
 b'<!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg"/>',
 b'<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(https://external.example/x)"/></svg>'])
def test_svg_unsafe_or_blank(runtime, raw):
    with pytest.raises(runtime.Hold): runtime.validate_review_svg(raw)


def test_safe_svg_subset(runtime):
    runtime.validate_review_svg(b'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20"/><text x="1" y="10">FAKE</text></svg>')


@pytest.mark.parametrize('problem,reason', [('fixer','cannot grade'), ('renamed','cannot grade'), ('consent','consent required'),
 ('other','cannot grade'), ('unavailable','identity capability')])
def test_stable_participation_rejects_fixer_contributor_and_missing_host(package, problem, reason):
    rt, order, candidate, receipt = package
    host = json.loads(base64.b64decode(order['seal']['review_inputs']['sources/participation.json']))
    host['contributors'].append('fixture-reviewer')
    if problem in ('fixer','renamed','consent'):
        host['repairs'] = [{'identity': 'fixture-reviewer', 'original_author': 'old-author', 'original_reviewer': 'old-reviewer',
          'work_order_id': 'FAKE-failed-origin', 'return_hash': '0'*64, 'finding_id': 'F1', 'contributed': True, 'consent': {'accepted': problem != 'consent', 'user': 'FAKE-user', 'reference': 'FAKE-consent', 'before_contribution': True}}]
    if problem == 'unavailable': host['observed'] = False
    # Test host record validation independently; a real sealed input change separately holds.
    probe = deepcopy(order); probe['seal'] = None
    write_json(rt.root / 'sources/probe.json', host); probe['participation_evidence'] = 'sources/probe.json'
    state = rt._load()
    state['orders']['FAKE-failed-origin'] = {'author': 'old-author', 'reviewer': {'identity': 'old-reviewer'}, 'seal': {'return_hash': '0'*64}}
    state.setdefault('observations', []).append({'record': {'kind': 'review_returned', 'work_order_id': 'FAKE-failed-origin'}, 'review': {'verdict': 'fail', 'return_hash': '0'*64, 'findings': [{'id':'F1'}]}})
    with pytest.raises(Exception, match=reason): rt._participation(probe, state)


def test_synthetic_49_over_12_is_valid_numeric_only(package):
    # Supplied historical dimension values unavailable: synthetic vector, not a regrade.
    scores = package[3]['scores']; values = [5] + [4]*11
    for name, value in zip(scores['dimensions'], values): scores['dimensions'][name]['score'] = value
    scores.update(team_mean=29/7, pitch_mean=4, overall=49/12)
    assess(package)
    package[3]['review_evidence']['renders'].pop('component.mmd')
    finding(package, 'review_hold', 'diagrams_visual', 'component.mmd')
    assess(package, False)


def test_current_v2_failed_review_history_retains_bytes(package):
    rt, order, candidate, receipt = package
    finding(package, 'shaping', 'rubric_assessment', 'rubric_assessment')
    for score in receipt['scores']['dimensions'].values(): score['score'] = 3
    receipt['scores'].update(team_mean=3, pitch_mean=3, overall=3)
    path = write_json(rt.root / 'sources/failure-review.json', receipt)
    rt.observe({'event_id': 'FAKE-returned', 'kind': 'review_returned', 'run_id': order['run_id'], 'work_order_id': order['work_order_id'],
      'generation': order['generation'], 'actor': order['reviewer']['identity'], 'observed_at': '2026-10-05T12:00:00Z',
      'version': version(rt), 'evidence': 'sources/failure-review.json'}, version(rt))
    path.write_text('receipt no longer exists as mutable source')
    assert rt._floor_only_failure_facts(rt._load())


def test_receipt_copied_openings_without_controller_record_holds(package):
    rt, order, candidate, receipt = package
    order.pop('review_observation')
    with pytest.raises(Exception, match='controller post-seal host record required'): assess(package)


def test_controller_rejects_postseal_new_contributor(package):
    rt, order, candidate, receipt = package
    record = deepcopy(order['review_observation']['record'])
    record['contributors'].append('late-fixer')
    write_json(rt.root / 'sources/late-observation.json', record)
    with pytest.raises(Exception, match='sealed revision contributors changed'):
        rt.review_observation(order['work_order_id'], 'sources/late-observation.json', version(rt))


def test_v2_dispatch_schema_is_exact(package):
    assert package[1]['required_return_schema'] == 'shaping-review-evidence.v1#/definitions/reviewV2'


def test_invalid_second_return_and_unowned_item_hold(package):
    receipt = package[3]; receipt['review_evidence']['seams'][0]['predicate_status'] = 'missing'
    finding(package, 'research', 'contracts_security', 'land')
    finding(package, 'shaping', 'contracts_security', 'land')
    with pytest.raises(Exception, match='not owned'): assess(package, False)
    receipt['findings'][-1]['item'] = 'unowned-subject'
    with pytest.raises(Exception, match='not owned'): assess(package, False)


def test_cyclic_return_prerequisites_hold(package):
    receipt = package[3]; receipt['review_evidence']['seams'][0]['predicate_status'] = 'missing'
    receipt['review_evidence']['renders'].pop('component.mmd')
    finding(package, 'research', 'contracts_security', 'land'); finding(package, 'review_hold', 'diagrams_visual', 'component.mmd')
    receipt['findings'][0]['prerequisite'] = 'F2'; receipt['findings'][1]['prerequisite'] = 'F1'
    with pytest.raises(Exception, match='cyclic'): assess(package, False)


def test_v2_missing_render_receipt_can_record_hold(package):
    receipt = package[3]; receipt['review_evidence']['renders'].pop('component.mmd'); receipt['render_evidence'].pop('component.mmd')
    finding(package, 'review_hold', 'diagrams_visual', 'component.mmd'); assess(package, False)

@pytest.mark.parametrize('package', ['reported'], indirect=True)
def test_reported_historical_fixture_is_not_regraded_and_missing_pixels_hold(package):
    rt, order, candidate, receipt = package
    reported = json.loads((candidate / 'reported-context.json').read_text())
    assert reported['historical_dimensions'] is None and reported['stored_verdict'] == 'pass'
    assert receipt['scores']['overall'] == 49/12
    # Isolate pixels: supplied predicate/question defects repaired with separately FAKE observations.
    receipt['review_evidence']['renders'] = {}
    for source in ('component.mmd','sequence.mmd','data-flow.mmd'):
        finding(package, 'review_hold', 'diagrams_visual', source)
    assess(package, False)
    with pytest.raises(Exception, match='review evidence unresolved'): assess(package)
    assert json.loads((candidate / 'reported-context.json').read_text()) == reported


@pytest.mark.parametrize('package', ['reported'], indirect=True)
def test_reported_observation_sentence_is_not_named_predicate(package):
    rt, order, candidate, receipt = package
    # Isolate predicate/rationale: FAKE complete render inspections and valid nondependence quote retained.
    seam = receipt['review_evidence']['seams'][0]; seam.update(predicate_status='missing', read_support=False)
    receipt['scores']['dimensions']['solution_sharpness']['rationale'] = 'Supplied/unverified: land boolean remains the observation sentence rather than a named predicate.'
    with pytest.raises(Exception, match='missing relevant typed finding'): assess(package, False)
    finding(package, 'research', 'contracts_security', 'land')
    receipt['review_evidence']['semantic_audit'].update(consistent=False, contradictions=[{'id':'rationale-defect','check':'contracts_security','item':'land','route':'research',
      'rationale_path':'scores.dimensions.solution_sharpness.rationale', 'rationale_quote':receipt['scores']['dimensions']['solution_sharpness']['rationale'],
      'source':bound_quote(rt,'sources/receiver.py','1:2'), 'explanation':'FAKE independent semantic finding for supplied observation-sentence rationale'}])
    finding(package, 'research', 'contracts_security', 'rationale-defect')
    receipt['findings'][-1]['source'] = bound_quote(rt,'sources/receiver.py','1:2')
    assess(package, False)
    assert json.loads((candidate / 'reported-context.json').read_text())['stored_verdict'] == 'pass'


@pytest.mark.parametrize('route', ['research','shaping'])
def test_contradiction_cannot_relabel_missing_or_dependent_failure(package, route):
    receipt = package[3]; evidence = receipt['review_evidence']
    if route == 'research':
        evidence['questions'][0]['depends'] = True
        finding(package,'respondent','workstreams_proof','Q1')
        subject,check,source = 'Q1','workstreams_proof',bound_quote(package[0],'sources/proof.txt')
    else:
        evidence['seams'][0]['predicate_status'] = 'missing'
        finding(package,'research','contracts_security','land')
        subject,check,source = 'land','contracts_security',bound_quote(package[0],'sources/receiver.py','1:2')
    evidence['semantic_audit'].update(consistent=False, contradictions=[{'id':'wrong-route','check':check,'item':subject,'route':route,
      'rationale_path':f'assessments.{check}.explanation','rationale_quote':receipt['assessments'][check]['explanation'],'source':source,'explanation':'FAKE wrong route'}])
    with pytest.raises(Exception, match='route/check must match'): assess(package, False)


def test_progress_handles_v2_review_retained_bytes(package):
    rt, order, candidate, receipt = package
    assert rt._progress_review_failure(rt._load(), order, receipt) is None
    receipt['scores']['overall'] = 5
    assert 'incorrect overall' in rt._progress_review_failure(rt._load(), order, receipt)


def test_controller_pinned_applicability_allows_explicit_nontechnical(package):
    rt, order, candidate, receipt = package
    # Isolated consistency probe: final host owns applicability, not shapeClaim status.
    files = rt._candidate(rt._load(), order)[0]
    plan = json.loads(base64.b64decode(files['review-plan.json']['base64']))
    plan['seams'][0]['applicability'] = 'nontechnical'
    order = deepcopy(order); order['seam_applicability']['land'] = 'nontechnical'
    raw = (json.dumps(plan)+'\n').encode(); files['review-plan.json']={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
    # This is not a forged acceptance: regenerate an isolated packet and bound observation for method-level protocol testing.
    order['seal']['subject']['review-plan.json'] = files['review-plan.json']['sha256']; order['seal']['review_files'] = files
    packet = rt._review_packet(rt._load(),order,files,order['seal']); order['seal']['review_packet'] = packet
    receipt['subject'] = order['seal']['subject']; evidence = receipt['review_evidence']; evidence['packet_hash'] = hashlib.sha256((json.dumps(packet,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest(); evidence['openings'] = packet['entries']
    order['review_observation']['record'].update(packet_hash=evidence['packet_hash'], openings=packet['entries'])
    evidence['seams'][0]['predicate_status'] = 'not_applicable'
    rt._review(receipt,rt._load(),order,files)


def test_generic_score_rationale_contradiction_is_bound_to_owned_assessment(package):
    rt, order, candidate, receipt = package
    receipt['scores']['dimensions']['cost']['rationale'] = 'FAKE contradiction: unlimited scope exceeds funded cost.'
    receipt['assessments']['rubric_assessment']['outcome'] = 'fail'; receipt['verdict'] = 'fail'
    evidence = bound_quote(rt,'evidence.txt',candidate=candidate)
    receipt['review_evidence']['semantic_audit'].update(consistent=False,contradictions=[{'id':'cost-defect','check':'rubric_assessment','item':'assessment:rubric_assessment','route':'shaping',
     'rationale_path':'scores.dimensions.cost.rationale','rationale_quote':receipt['scores']['dimensions']['cost']['rationale'],'source':evidence,'explanation':'FAKE independent unlimited-cost interpretation'}])
    finding(package,'shaping','rubric_assessment','cost-defect'); receipt['findings'][-1]['source']=evidence
    assess(package,False)
    receipt['review_evidence']['semantic_audit']['contradictions'][0]['rationale_quote']='arbitrary prose'
    with pytest.raises(Exception,match='rationale quote mismatch'): assess(package,False)


def test_existing_passive_mermaid_svg_contract_is_preserved(runtime):
    svg = b'''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><style>.node { fill: #fff; stroke: #333; } .edge { marker-end: url(#arrow); }</style><defs><marker id="arrow"><path d="M0,0 L5,5"/></marker><linearGradient id="shade"><stop offset="0%" stop-color="#fff"/></linearGradient><clipPath id="clip"><rect width="10" height="10"/></clipPath><filter id="shadow"><feDropShadow dx="1"/></filter><symbol id="node"><rect width="20" height="20"/></symbol></defs><use href="#node"/><text x="1" y="20">FAKE diagram label</text></svg>'''
    assert runtime.validate_review_svg(svg) == [100,50]


@pytest.mark.parametrize('css', ['@import "evil"', 'fill: url(https://evil.example/x)', 'animation: pulse 1s', 'fill: expression(alert(1))'])
def test_svg_active_css_holds(runtime, css):
    raw = f'<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"><style>{css}</style><rect width="2" height="2"/></svg>'.encode()
    with pytest.raises(runtime.Hold): runtime.validate_review_svg(raw)


@pytest.mark.parametrize('special', ['predicate','question'])
def test_generic_audit_cannot_alias_existing_special_failure(package, special):
    rt, order, candidate, receipt = package; evidence = receipt['review_evidence']
    if special == 'predicate':
        evidence['seams'][0]['predicate_status']='missing'; finding(package,'research','contracts_security','land'); check='contracts_security'
    else:
        evidence['questions'][0]['depends']=True; finding(package,'respondent','workstreams_proof','Q1'); check='workstreams_proof'
    evidence['semantic_audit'].update(consistent=False, contradictions=[{'id':'alias','check':check,'item':'assessment:'+check,'route':'shaping',
      'rationale_path':f'assessments.{check}.explanation','rationale_quote':receipt['assessments'][check]['explanation'],
      'source':bound_quote(rt,'evidence.txt',candidate=candidate),'explanation':'FAKE generic alias'}])
    with pytest.raises(Exception,match='cannot be relabelled as generic'): assess(package,False)


def test_two_independent_generic_contradictions_share_assessment(package):
    rt, order, candidate, receipt = package
    receipt['assessments']['rubric_assessment']['outcome']='fail'; receipt['verdict']='fail'
    evidence = bound_quote(rt,'evidence.txt',candidate=candidate)
    contradictions=[]
    for dimension, identifier in [('cost','cost-defect'),('appetite_fit','appetite-defect')]:
        receipt['scores']['dimensions'][dimension]['rationale']=f'FAKE independent contradiction: {dimension} rationale violates accepted scope.'
        contradictions.append({'id':identifier,'check':'rubric_assessment','item':'assessment:rubric_assessment','route':'shaping',
          'rationale_path':f'scores.dimensions.{dimension}.rationale','rationale_quote':receipt['scores']['dimensions'][dimension]['rationale'],
          'source':evidence,'explanation':f'FAKE independent semantic interpretation for {dimension}'})
        finding(package,'shaping','rubric_assessment',identifier); receipt['findings'][-1]['source']=evidence
    receipt['review_evidence']['semantic_audit'].update(consistent=False,contradictions=contradictions)
    assess(package,False)
    assert len(receipt['findings']) == 2


def test_independent_generic_and_special_failure_share_check(package):
    rt, order, candidate, receipt = package
    receipt['review_evidence']['seams'][0]['predicate_status']='missing'
    finding(package,'research','contracts_security','land')
    receipt['scores']['dimensions']['cost']['rationale']='FAKE independent cost contradiction outside the receiving seam.'
    source=bound_quote(rt,'evidence.txt',candidate=candidate)
    receipt['review_evidence']['semantic_audit'].update(consistent=False,contradictions=[{'id':'independent-cost','check':'contracts_security','item':'assessment:contracts_security','route':'shaping',
       'rationale_path':'scores.dimensions.cost.rationale','rationale_quote':receipt['scores']['dimensions']['cost']['rationale'],
       'source':source,'explanation':'FAKE independent semantic observation; source span distinct from receiving seam'}])
    finding(package,'shaping','contracts_security','independent-cost'); receipt['findings'][-1]['source']=source
    assess(package,False)
    assert {(f['route'],f['item']) for f in receipt['findings']} == {('research','land'),('shaping','independent-cost')}


def test_generic_score_alias_overlapping_special_read_span_holds(package):
    rt, order, candidate, receipt = package
    receipt['review_evidence']['seams'][0]['predicate_status']='missing'
    finding(package,'research','contracts_security','land')
    source=bound_quote(rt,'sources/receiver.py','1:2')
    receipt['evidence']['E2']='sources/receiver.py'; receipt['scores']['dimensions']['cost']['evidence_ids']=['E2']
    receipt['review_evidence']['semantic_audit'].update(consistent=False,contradictions=[{'id':'alias-cost','check':'contracts_security','item':'assessment:contracts_security','route':'shaping',
       'rationale_path':'scores.dimensions.cost.rationale','rationale_quote':receipt['scores']['dimensions']['cost']['rationale'],
       'source':source,'explanation':'FAKE aliased source span'}])
    with pytest.raises(Exception,match='overlaps special subject evidence'): assess(package,False)


def test_v2_score_evidence_can_reference_pinned_packet_input(package):
    receipt=package[3];receipt['evidence']['E2']='sources/receiver.py';receipt['scores']['dimensions']['cost']['evidence_ids']=['E2']
    assess(package)
