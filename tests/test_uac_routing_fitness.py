"""Source facts, authority and drift checks; no simulated behavioral scores."""
from pathlib import Path
import copy
import json
import pytest
from intent_pipeline.skill_jobs import compile_skill_job, build_advisory_job_map, load_skill_job_map, validate_routing_fitness

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/uac-routing-fitness'
SLUG = 'engos-example-route-check'


def prepare(tmp_path, text=None, existing=None):
    text = text or (FIXTURES/'new-skill.md').read_text()
    p=tmp_path/'ssot'/f'{SLUG}.md';p.parent.mkdir(exist_ok=True);p.write_text(text)
    (p.parent/'engos-quality-code-review.md').write_text('# Peer review\n')
    job=compile_skill_job(tmp_path,SLUG,text,display_name='Route Check',description='Inspect a saved route.',existing=existing)
    return text,job


def test_new_skill_receives_actual_contract_not_placeholder(tmp_path):
    text,j=prepare(tmp_path)
    assert j['primary_job']=='Identify broken destinations with exact source evidence.'
    assert 'diagnosis before an edit' in j['use_when']
    assert 'Broken destinations' in j['main_output']
    assert 'Changing a route' in j['not_for']
    f=j['routing_fitness']
    assert f['mapping_status']=='source_derived_draft'
    assert f['activation']['mode']=='unknown'  # An example cannot impose invocation policy.
    assert f['risk_authority_ceiling']['grants_authority'] is False
    assert len(f['conditional_companions'])==1
    assert 'after a separately authorized fix' in f['conditional_companions'][0]['condition_and_handoff']
    assert f['pack_hints']['default_bulk_activation'] is False
    for clauses in f['provenance']['field_sources'].values():
        for c in clauses:
            ref=c['source'];assert c['text']=='\n'.join(text.splitlines()[ref['start_line']-1:ref['end_line']])
    validate_routing_fitness(j,tmp_path,SLUG)


def test_existing_curation_survives_and_second_compile_is_identical(tmp_path):
    old=json.loads((FIXTURES/'curated-descriptor.json').read_text())
    text,j=prepare(tmp_path,existing=old)
    assert {k:j[k] for k in old}==old
    again=compile_skill_job(tmp_path,SLUG,text,display_name='Route Check',description='Inspect a saved route.',existing=j)
    assert again==j


def test_explicit_only_source_and_batman_remain_explicit(tmp_path):
    _,j=prepare(tmp_path,(FIXTURES/'explicit-only.md').read_text())
    assert j['routing_fitness']['activation']['mode']=='explicit_only'
    slug='engos-orchestration-batman';raw=(ROOT/'ssot'/f'{slug}.md').read_text()
    j=compile_skill_job(ROOT,slug,raw,display_name='Batman',description='Delivery')
    assert j['routing_fitness']['activation']['mode']=='explicit_only'
    assert j['routing_fitness']['risk_authority_ceiling']['grants_authority'] is False


def test_fenced_activation_claims_cannot_become_rules(tmp_path):
    text=(FIXTURES/'new-skill.md').read_text().replace('## Purpose','## Agent Operating Contract\n```text\nThis capability is active only when the user explicitly invokes it.\n```\n\n## Purpose')
    _,j=prepare(tmp_path,text)
    assert j['routing_fitness']['activation']['mode']=='unknown'


def test_changed_source_invalidates_binding_and_stays_stale(tmp_path):
    text,j=prepare(tmp_path)
    changed=text.replace('missing destinations','missing endpoints')
    (tmp_path/'ssot'/f'{SLUG}.md').write_text(changed)
    with pytest.raises(ValueError,match='binding mismatch'):validate_routing_fitness(j,tmp_path,SLUG)
    newer=compile_skill_job(tmp_path,SLUG,changed,display_name='Route Check',description='',existing=j)
    assert newer['routing_fitness']['mapping_status']=='stale'
    assert compile_skill_job(tmp_path,SLUG,changed,display_name='Route Check',description='',existing=newer)==newer


def test_resource_change_is_detected_without_entry_change(tmp_path):
    text,j=prepare(tmp_path)
    root=tmp_path/'sources/capability-resources'/SLUG;root.mkdir(parents=True)
    (root/'resource-map.json').write_text(json.dumps({'schema_version':'CapabilityResourceMap.v1','shared':['rule.md'],'routes':{},'dependencies':{}}))
    (root/'rule.md').write_text('## Constraints\nNever publish.\n')
    j=compile_skill_job(tmp_path,SLUG,text,display_name='Route Check',description='',existing=j)
    (root/'rule.md').write_text('## Constraints\nNever publish or delete.\n')
    with pytest.raises(ValueError,match='binding mismatch'):validate_routing_fitness(j,tmp_path,SLUG)


@pytest.mark.parametrize('field,value',[('activation',{'mode':'implicit_eligible'}),('mapping_status','reviewed')])
def test_tampering_cannot_create_review_or_invocation_grants(tmp_path,field,value):
    _,j=prepare(tmp_path);j['routing_fitness'][field]=value
    with pytest.raises(ValueError):validate_routing_fitness(j)


def test_map_receipt_binds_values_and_references(tmp_path):
    raw=(FIXTURES/'new-skill.md').read_text().replace('engos-quality-code-review','native reviewer')
    _,j=prepare(tmp_path,raw)
    p=tmp_path/'map.json';m=build_advisory_job_map({SLUG:j});p.write_text(json.dumps(m))
    assert load_skill_job_map(p,[SLUG])==m
    m['skills'][SLUG]['main_output']='Forged output';p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='hash mismatch'):load_skill_job_map(p,[SLUG])


def test_missing_inputs_remain_explicitly_unknown(tmp_path):
    _,j=prepare(tmp_path,'# Sparse\n\n## Purpose\nInspect a thing.\n')
    f=j['routing_fitness']
    assert {'task_phases','risk_authority_ceiling','negative_examples'}<=set(f['unresolved_fields'])
    assert f['mapping_status']=='source_derived_draft'


def test_write_authorization_is_not_explicit_invocation_policy(tmp_path):
    _,j=prepare(tmp_path, "# Check\n\n## Purpose\nThis skill changes production only when explicitly authorized.\n")
    assert j['routing_fitness']['activation']['mode']=='unknown'


def test_nested_example_is_not_phase_evidence(tmp_path):
    _,j=prepare(tmp_path, "# Check\n\n## Workflow\n### Example\nAfter deployment, announce a success.\n")
    assert j['routing_fitness']['task_phases']['clauses']==[]


def test_rehashed_unsubstantiated_metadata_is_rejected(tmp_path):
    from intent_pipeline.skill_jobs import _digest
    _,j=prepare(tmp_path)
    j['routing_fitness']['task_phases']='unsupported-label'
    j['routing_fitness']['provenance'].pop('mapping_sha256')
    j['routing_fitness']['provenance']['mapping_sha256']=_digest(j)
    with pytest.raises(ValueError,match='field types'):validate_routing_fitness(j,tmp_path,SLUG)


@pytest.mark.parametrize('field,value',[('review_status','reviewed'),('plain_english_note','Behavior proven.')])
def test_map_cannot_promote_itself_with_valid_entry_receipt(tmp_path,field,value):
    raw=(FIXTURES/'new-skill.md').read_text().replace('engos-quality-code-review','native reviewer')
    _,j=prepare(tmp_path,raw)
    p=tmp_path/'map.json';m=build_advisory_job_map({SLUG:j});m[field]=value;p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='cannot assert review'):load_skill_job_map(p,[SLUG])


@pytest.mark.parametrize('sentence',[
    'This capability is active only when the user has supplied a diff.',
    'This skill is active only when explicit mode is enabled.',
    'This capability is invoked only when explicit credentials are configured.',
    'For example: This capability is active only when the user explicitly invokes it.',
    'This capability is active only when the user explicitly invokes it unless automatic mode applies.',
])
def test_activation_needs_an_unambiguous_operative_invocation_sentence(tmp_path,sentence):
    _,j=prepare(tmp_path,'# Check\n\n## Purpose\n'+sentence+'\n')
    assert j['routing_fitness']['activation']['mode']=='unknown'


def test_self_companion_is_visible_as_unresolved_source_evidence(tmp_path):
    raw=(FIXTURES/'new-skill.md').read_text().replace('engos-quality-code-review',SLUG)
    _,j=prepare(tmp_path,raw)
    f=j['routing_fitness']
    assert not f['conditional_companions']
    assert 'self_companion_reference' in f['unresolved_fields']
    assert f['provenance']['unresolved_companion_clauses'][0]['issue']=='self_reference'


def test_positive_constraints_do_not_become_non_use_or_authority_rules(tmp_path):
    _,j=prepare(tmp_path,'# Check\n\n## Purpose\nSummarize prose.\n\n## Constraints\nAlways cite sources.\n')
    assert j['not_for'] != 'Always cite sources.'
    assert j['authority'] != 'Always cite sources.'
    assert {'job_contract.not_for','job_contract.authority'} <= set(j['routing_fitness']['unresolved_fields'])
