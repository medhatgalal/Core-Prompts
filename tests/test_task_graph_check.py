"""Dependency readiness is mechanical and never authorizes execution."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[1]
OWNER = REPO / 'sources/capability-resources/engos-design-plan-implementation'
FIXTURE = REPO / 'sources/capability-resources/engos-design-specify-change/evals/positive-and-near-miss.json'

def module():
    spec = importlib.util.spec_from_file_location('graph_check', OWNER / 'scripts/graph_check.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def plan():
    return json.loads(FIXTURE.read_text())['positive']['plan']

def test_sorted_frontier_and_null_observations():
    result = module().check_graph(plan())
    assert result['mechanical_passed']
    assert result['ready_task_ids'] == ['T1', 'T2']
    assert result['readiness_holds'] == []
    assert {'pointer': '/spec_sha256', 'reason': 'spec_digest_not_supplied'} in result['readiness_observations']
    assert result['semantic_correctness'] == result['authority_verification'] == 'not_assessed'

@pytest.mark.parametrize('kind,code', [('cycle','dependency_cycle'),('unknown','unknown_dependency'),('duplicate','duplicate_id'),('self','self_dependency'),('completed','unknown_completed_task'),('verification','duplicate_id')])
def test_invalid_graph_has_no_frontier(kind, code):
    p = plan()
    if kind == 'cycle':
        p['tasks'][0]['depends_on'] = ['T2']; p['tasks'][1]['depends_on'] = ['T1']
        p['completed_task_ids'] = ['T1','T2']
    elif kind == 'unknown': p['tasks'][0]['depends_on'] = ['T9']
    elif kind == 'duplicate': p['tasks'][1]['id'] = 'T1'
    elif kind == 'self': p['tasks'][0]['depends_on'] = ['T1']
    elif kind == 'completed': p['completed_task_ids'] = ['T9']
    else: p['tasks'][0]['verification'] *= 2
    result = module().check_graph(p)
    assert not result['mechanical_passed']
    assert result['ready_task_ids'] == []
    assert code in {e['code'] for e in result['errors']}

def test_diamond_and_historical_completion():
    p = plan(); third = copy.deepcopy(p['tasks'][0]); third['id']='T3'; third['depends_on']=['T1','T2']; p['tasks'].append(third)
    p['completed_task_ids']=['T1']
    r = module().check_graph(p)
    assert r['ready_task_ids'] == ['T2']
    assert r['blocked_tasks'] == [{'task_id':'T3','outstanding_dependency_ids':['T2']}]
    p['completed_task_ids']=['T3']
    r = module().check_graph(p)
    assert r['mechanical_passed']
    assert r['completion_inconsistencies'] == [{'task_id':'T3','uncompleted_dependency_ids':['T1','T2']}]


def test_result_contract_and_detached_stdlib_cli(tmp_path):
    import subprocess
    import sys
    import shutil
    from jsonschema import Draft202012Validator
    target=tmp_path/'resources'; shutil.copytree(OWNER,target)
    input_path=tmp_path/'plan.json'; p=plan(); p['unresolved']=['second','first']; input_path.write_text(json.dumps(p))
    args=[sys.executable,'-I','-S',str(target/'scripts/graph_check.py'),'--plan',str(input_path)]
    first=subprocess.run(args,cwd=tmp_path,capture_output=True,text=True)
    second=subprocess.run(args,cwd=tmp_path,capture_output=True,text=True)
    assert first.returncode==0 and first.stdout==second.stdout and first.stderr==''
    result=json.loads(first.stdout); assert result['readiness_holds']==['second','first']
    schema=json.loads((OWNER/'schemas/graph-result.schema.json').read_text()); validator=Draft202012Validator(schema)
    assert validator.is_valid(result)
    for field in p:
        bad=copy.deepcopy(p); del bad[field]; r=module().check_graph(bad)
        assert not r['mechanical_passed'] and r['ready_task_ids']==[]
        assert validator.is_valid(r)
    result['authority_verification']='passed'; assert not validator.is_valid(result)


def test_disconnected_components_and_large_nonrecursive_graph():
    p=plan(); tasks=[]
    for i in range(1200):
        t=copy.deepcopy(p['tasks'][0]); t['id']=f'T{i:04}'; t['depends_on']=[f'T{i-1:04}'] if i else []; tasks.append(t)
    p['tasks']=tasks
    result=module().check_graph(p)
    assert result['mechanical_passed'] and result['ready_task_ids']==['T0000']
    p['tasks'][-2]['depends_on']=['T1199']; p['completed_task_ids']=['T1198','T1199']
    result=module().check_graph(p)
    assert result['ready_task_ids']==[]
    assert next(e['ids'] for e in result['errors'] if e['code']=='dependency_cycle')==['T1198','T1199']


def test_all_completed_and_duplicate_graph_arrays():
    p=plan(); p['completed_task_ids']=['T2','T1']
    r=module().check_graph(p)
    assert r['mechanical_passed'] and r['ready_task_ids']==[]
    for key in ['completed_task_ids','depends_on']:
        broken=plan()
        if key=='completed_task_ids': broken[key]=['T1','T1']
        else: broken['tasks'][0][key]=['T2','T2']
        r=module().check_graph(broken)
        assert not r['mechanical_passed'] and r['ready_task_ids']==[]
        assert {e['code'] for e in r['errors']}=={'schema_error'}
