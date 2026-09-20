from pathlib import Path
import copy
import importlib.util
import json
import shutil
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('route_only',ROOT/'scripts/eval-routing-only.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_battery_has_twelve_four_way_families_and_eight_transitions():
    c,o,k,p=m.load_battery();v=m.validate(c,o,k,p)
    assert (v['cases'],v['ordinary'],v['families'],v['followups'])==(56,48,12,8)
    assert len({x['prompt'] for x in c})==56


def test_oracle_never_enters_router_input():
    c,o,k,p=m.load_battery()
    for case in c:
        incoming=m.routing_input(case,k)
        assert set(incoming)=={'id','prompt','context','history','catalog'}
        assert 'oracle' not in incoming and 'expected_primary' not in incoming


def registry_root(tmp_path, adapters):
    path=tmp_path/'evals/adapters/registry.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'adapters':adapters}))
    return tmp_path


def test_blocked_results_are_unknown_not_faked_none_or_success(tmp_path):
    c,o,k,p=m.load_battery()
    a=m.admission(registry_root(tmp_path,[]));rows=m.blocked_results(c,k,a)
    assert a['status']=='blocked_no_declared_route_only_adapter'
    assert len(rows)==56
    for row in rows:
        for arm in row['arms'].values():
            assert arm['primary'] is None and arm['selected_skills'] is None
            assert arm['pack_size'] is None and arm['mismatches'] is None
            assert arm['provider_calls']==0 and arm['task_execution'] is False
            assert arm['context_cost_estimate']['actual_tokens'] is None


def test_current_registry_observations_do_not_hardcode_provider_state():
    registry=json.loads((ROOT/'evals/adapters/registry.json').read_text())
    a=m.admission();ids={x['id']:x for x in a['adapters_observed']}
    assert set(ids)=={x['id'] for x in registry['adapters']}
    for declared in registry['adapters']:
        observed=ids[declared['id']]
        assert observed['unavailable_reason']==declared.get('unavailable_reason')
        assert observed['bootstrap_agent']==declared.get('bootstrap_agent')
        assert observed['route_only_skill_pack_protocol']==declared.get('route_only_skill_pack_protocol',False)
    assert not a['native']['admitted'] and not a['agents_bootstrap']['admitted']
    assert not a['execution_enabled']


def test_route_only_declaration_changes_diagnostic_but_never_dispatches(tmp_path):
    adapter={'id':'future-route-only','supported_tool_policy_modes':['none'],
             'route_only_skill_pack_protocol':True}
    root=registry_root(tmp_path,[adapter]);a=m.admission(root)
    assert a['declared_candidates']==['future-route-only']
    assert a['status']=='blocked_runtime_review_required'
    assert not a['execution_enabled'] and not a['native']['admitted']
    assert a['tool_or_provider_processes_started']==0 and not a['task_execution']


@pytest.mark.parametrize('extra',[{'unavailable_reason':'not reviewed'},
    {'bootstrap_agent':'some-agent'}, {'supported_tool_policy_modes':['repo-write-subagents']},
    {'route_only_skill_pack_protocol':'true'}])
def test_ineligible_declarations_are_not_route_only_candidates(tmp_path,extra):
    adapter={'id':'candidate','supported_tool_policy_modes':['none'],
             'route_only_skill_pack_protocol':True,**extra}
    a=m.admission(registry_root(tmp_path,[adapter]))
    assert a['declared_candidates']==[]
    assert not a['execution_enabled']


@pytest.mark.parametrize('mutation',['human_review','unknown_skill','forbidden_overlap','critical_gate','execution','missing_case'])
def test_invalid_or_unsafe_battery_is_rejected(mutation):
    c,o,k,p=m.load_battery();first=o['cases'][c[0]['id']]
    if mutation=='human_review':o['review_status']='human_approved';o['human_review']={'kind':'AI'}
    elif mutation=='unknown_skill':first['primary']='engos-invented-nonexistent'
    elif mutation=='forbidden_overlap':first['primary']='engos-orchestration-batman';first['minimum_pack']=[first['primary']];first['maximum_pack_size']=1
    elif mutation=='critical_gate':p['gates']['critical_authority_opt_out_no_batman_no_unsupported_skill_no_fabricated_evidence']=0.99
    elif mutation=='execution':p['task_execution_permitted']=True
    elif mutation=='missing_case':c.pop()
    with pytest.raises(ValueError):m.validate(c,o,k,p)


@pytest.mark.parametrize('field,value',[('phase_transition_accuracy_min',0),('confidence_band_agreement_min',0),('unnecessary_companion_rate_max',1),('context_or_cost_ratio_without_improvement_max',100)])
def test_every_frozen_numeric_gate_is_enforced(field,value):
    c,o,k,p=m.load_battery();p['gates'][field]=value
    with pytest.raises(ValueError,match='numeric gates'):m.validate(c,o,k,p)


def test_every_case_requires_critical_guards():
    c,o,k,p=m.load_battery();o['cases'][c[0]['id']]['critical_guards']=[]
    with pytest.raises(ValueError,match='base guards'):m.validate(c,o,k,p)


def historical_root(tmp_path):
    directory=tmp_path/'evals/fixtures/routing';directory.mkdir(parents=True)
    for suffix in (*m.FIXTURE_SUFFIXES,'.manifest.json'):
        shutil.copy2(m.FIXTURES/(m.PREFIX+suffix),directory/(m.PREFIX+suffix))
    return tmp_path


def test_historical_fixture_is_self_contained_and_not_a_live_checkout_pin(tmp_path):
    root=historical_root(tmp_path)
    freeze=m.verify_freeze(root)
    assert freeze['consumer_admitted'] is False and freeze['human_oracle_approved'] is False
    assert len(freeze['verified_fixture_files'])==6
    assert freeze['live_source_parity_checked'] is False
    assert not (root/'ssot').exists()
    (root/'AGENTS.md').write_text('Unrelated current project instructions.\n')
    (root/'ssot').mkdir();(root/'ssot/new-skill.md').write_text('# A later skill\n')
    assert m.verify_freeze(root)==freeze
    assert m.validate(*m.load_battery(root))['cases']==56


@pytest.mark.parametrize('suffix',m.FIXTURE_SUFFIXES)
def test_historical_fixture_tampering_still_fails(tmp_path,suffix):
    root=historical_root(tmp_path);p=root/'evals/fixtures/routing'/(m.PREFIX+suffix)
    p.write_text(p.read_text()+'\nchanged\n')
    with pytest.raises(ValueError,match='Frozen input drift'):m.verify_freeze(root)


def test_historical_fixture_symlink_is_rejected(tmp_path):
    root=historical_root(tmp_path);p=root/'evals/fixtures/routing'/(m.PREFIX+'.md')
    saved=tmp_path/'outside.md';p.rename(saved);p.symlink_to(saved)
    with pytest.raises(ValueError,match='unsafe path'):m.verify_freeze(root)


def test_catalog_scope_is_visible_without_oracle_leakage():
    c,o,k,p=m.load_battery();incoming=m.routing_input(c[0],k)
    assert incoming['catalog']['catalog_scope']=='core_prompts_29_only_not_global_native_catalog'
    assert incoming['catalog']['source_commit']==k['source_commit']
    assert 'cases' not in incoming['catalog']


def test_unscoped_catalog_cannot_be_admitted():
    c,o,k,p=m.load_battery();k.pop('catalog_scope')
    with pytest.raises(ValueError,match='catalog identity'):m.validate(c,o,k,p)
