from pathlib import Path
import copy
import importlib.util
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


def test_blocked_results_are_unknown_not_faked_none_or_success():
    c,o,k,p=m.load_battery();a=m.admission();rows=m.blocked_results(c,k,a)
    assert a['status']=='blocked_no_admitted_luna_native_route_only_consumer'
    assert len(rows)==56
    for row in rows:
        for arm in row['arms'].values():
            assert arm['primary'] is None and arm['selected_skills'] is None
            assert arm['pack_size'] is None and arm['mismatches'] is None
            assert arm['provider_calls']==0 and arm['task_execution'] is False
            assert arm['context_cost_estimate']['actual_tokens'] is None


def test_registry_is_not_a_route_only_dispatcher():
    a=m.admission();ids={x['id']:x for x in a['adapters_observed']}
    assert ids['kiro-stream-json-experimental']['bootstrap_agent']=='engos-orchestration-batman'
    assert ids['codex-jsonl-experimental']['unavailable_reason']
    assert not a['native']['admitted'] and not a['agents_bootstrap']['admitted']


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


def test_frozen_files_and_current_catalog_match():
    freeze=m.verify_freeze()
    assert freeze['consumer_admitted'] is False and freeze['human_oracle_approved'] is False


def test_catalog_scope_is_visible_without_oracle_leakage():
    c,o,k,p=m.load_battery();incoming=m.routing_input(c[0],k)
    assert incoming['catalog']['catalog_scope']=='core_prompts_29_only_not_global_native_catalog'
    assert incoming['catalog']['source_commit']==k['source_commit']
    assert 'cases' not in incoming['catalog']


def test_unscoped_catalog_cannot_be_admitted():
    c,o,k,p=m.load_battery();k.pop('catalog_scope')
    with pytest.raises(ValueError,match='catalog identity'):m.validate(c,o,k,p)
