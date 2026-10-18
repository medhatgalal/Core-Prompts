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


@pytest.mark.parametrize('bad',['\ud800','\udfff'])
@pytest.mark.parametrize('location',['id','key'])
def test_graph_cli_rejects_lone_surrogate_keys_and_values(tmp_path,bad,location):
    import subprocess
    import sys
    from jsonschema import Draft202012Validator
    p=plan()
    if location=='id': p['tasks'][0]['id']='T'+bad
    else: p['unexpected'+bad]=True
    path=tmp_path/'plan.json'; path.write_text(json.dumps(p,ensure_ascii=True))
    process=subprocess.run([sys.executable,'-I','-S',str(OWNER/'scripts/graph_check.py'),'--plan',str(path)],capture_output=True,text=True)
    assert process.returncode==2 and process.stderr==''
    result=json.loads(process.stdout)
    assert result['errors']==[{'artifact':'plan','code':'invalid_json','detail':'Input contains an unpaired Unicode surrogate','ids':[],'pointer':''}]
    assert not result['mechanical_passed'] and result['ready_task_ids']==[]
    assert Draft202012Validator(json.loads((OWNER/'schemas/graph-result.schema.json').read_text())).is_valid(result)


def test_graph_cli_preserves_valid_unicode_in_success_and_error_pointer(tmp_path):
    import subprocess
    import sys
    p=plan(); ident='Té漢😀'; p['tasks'][0]['id']=ident
    path=tmp_path/'plan.json'
    def run():
        path.write_text(json.dumps(p,ensure_ascii=True))
        return subprocess.run([sys.executable,'-I','-S',str(OWNER/'scripts/graph_check.py'),'--plan',str(path)],capture_output=True,text=True)
    process=run(); result=json.loads(process.stdout)
    assert process.returncode==0 and process.stderr=='' and ident in result['ready_task_ids']
    p['extra/'+ident]=True
    process=run(); result=json.loads(process.stdout)
    assert process.returncode==1 and process.stderr==''
    assert result['errors'][0]['pointer']=='/extra~1'+ident


def test_graph_emitter_defensively_escapes_python_api_surrogates(capsys):
    m=module(); p=plan(); p['tasks'][0]['id']='T\udfff'
    assert m.emit(m.check_graph(p))==0
    text=capsys.readouterr().out
    assert '\\udfff' in text and 'T\udfff' in json.loads(text)['ready_task_ids']
    text.encode('utf-8')


def test_unknown_completion_hold_survives_conditional_frontier():
    p = plan()
    t3 = copy.deepcopy(p['tasks'][1])
    t3['id'] = 'T3'
    p['tasks'].append(t3)
    p['tasks'][0]['depends_on'] = []
    for task in p['tasks'][1:]:
        task['depends_on'] = ['T1']
    p['completed_task_ids'] = []
    hold = 'Completion state unknown; frontier conditional on no evidenced completions.'
    p['unresolved'] = [hold]
    result = module().check_graph(p)
    assert result['mechanical_passed']
    assert result['ready_task_ids'] == ['T1']
    assert result['blocked_tasks'] == [
        {'task_id': 'T2', 'outstanding_dependency_ids': ['T1']},
        {'task_id': 'T3', 'outstanding_dependency_ids': ['T1']},
    ]
    assert result['readiness_holds'] == [hold]
    assert result['semantic_correctness'] == 'not_assessed'
    assert result['authority_verification'] == 'not_assessed'
    # An explicit empty source list has the same topology, but no unknown-state hold.
    p['unresolved'] = []
    explicit_empty = module().check_graph(p)
    assert explicit_empty['ready_task_ids'] == result['ready_task_ids']
    assert explicit_empty['readiness_holds'] == []
    # A supplied completed prerequisite changes the projection without inventing state.
    p['completed_task_ids'] = ['T1']
    assert module().check_graph(p)['ready_task_ids'] == ['T2', 'T3']


def test_documented_inline_map_binds_concrete_plan_identity():
    import re
    examples = (REPO / 'docs/EXAMPLES.md').read_text()
    section = examples.split('## Optional planning link checks', 1)[1]
    identity_examples = [json.loads(block) for block in re.findall(r'```json\n(.*?)\n```', section, re.S)
                         if '"task_plan_id"' in block]
    assert len(identity_examples) == 1
    example = identity_examples[0]
    projection = example['dependency_map']
    assert projection['plan_ref'] == example['task_plan_id']
    assert projection['plan_ref'] not in {'TaskPlan.v1', 'inline:TaskPlan.v1'}
    assert projection['plan_sha256'] is None
    # This protects the published example, not native output or source-provenance verification.
    template = json.loads((OWNER / 'templates/dependency-map.json').read_text())
    assert template['plan_ref'] is None and template['plan_sha256'] is None
    assert 'exact id' in template['instructions']['plan_binding']
    assert 'never the schema name' in template['instructions']['plan_binding']
