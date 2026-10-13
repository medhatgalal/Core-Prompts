"""Actual supplied links count; mere inventory and semantic prose do not."""
import importlib.util
import json
import shutil
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[1]
BASE = REPO / 'sources/capability-resources'
OWNER = BASE / 'engos-design-specify-change'
FIXTURE = OWNER / 'evals/positive-and-near-miss.json'

@pytest.fixture
def checker(tmp_path):
    root=tmp_path/'resources'; (root/'schemas').mkdir(parents=True); (root/'scripts').mkdir()
    for slug,name in [('engos-design-specify-change','spec-contract'),('engos-design-plan-implementation','task-plan'),('engos-design-plan-implementation','task-contract'),('engos-quality-testing-review','test-design')]:
        shutil.copyfile(BASE/slug/'schemas'/f'{name}.schema.json',root/'schemas'/f'{name}.schema.json')
    shutil.copyfile(OWNER/'scripts/trace_check.py',root/'scripts/trace_check.py')
    spec=importlib.util.spec_from_file_location('trace_check',root/'scripts/trace_check.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def case(name='positive'): return json.loads(FIXTURE.read_text())[name]

def test_positive_optional_and_semantically_wrong(checker):
    for name in ['positive','semantically_wrong_but_linked']:
        c=case(name); r=checker.check_trace(**c)
        assert r['mechanical_passed']
        assert r['semantic_correctness']==r['behavioral_verification']=='not_assessed'
        assert r['test_execution']=='not_run'
    c=case(); r=checker.check_trace(c['spec'],c['plan'])
    assert r['tests_status']==r['test_link_validation']=='not_supplied'
    assert all(x['test_ids']==[] for x in r['matrix'])

@pytest.mark.parametrize('kind,code', [('missing','uncovered_requirement'),('unknown','unknown_requirement'),('duplicate','duplicate_id'),('tests','uncovered_test_requirement'),('inventory','test_inventory_mismatch'),('unlinked','unlinked_test')])
def test_near_misses(checker,kind,code):
    c=case()
    if kind=='missing': c['plan']['tasks'].pop()
    elif kind=='unknown': c['plan']['tasks'][0]['requirement_ids']=['R9']
    elif kind=='duplicate': c['plan']['tasks'][1]['id']='T1'
    elif kind=='tests': c['tests']['tests'].pop()
    elif kind=='inventory': c['tests']['requirement_ids']=['R1']
    else: c['tests']['tests'][0]['requirements']=[]
    r=checker.check_trace(**c)
    assert not r['mechanical_passed'] and r['matrix']==[]
    assert code in {x['code'] for x in r['errors']}

def test_design_mode_and_nonrequired(checker):
    c=case(); c['plan']['tasks'][0]['design_ids']=['D9']
    assert checker.check_trace(**c)['skipped_design_link_count']==1
    assert not checker.check_trace(**c,design_links=True)['mechanical_passed']
    c=case(); c['spec']['requirements'][1]['priority']='undecided'; c['plan']['tasks'].pop(); c['tests']['tests'].pop()
    r=checker.check_trace(**c)
    assert r['mechanical_passed']
    assert r['uncovered_nonrequired_requirement_ids']==r['undecided_requirement_ids']==['R2']


def test_bounded_interpreter_agrees_with_jsonschema_for_production_fields(checker):
    import copy
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    c=case(); c['spec']['source_refs'][0]['sha256']='a'*64
    c['spec']['assumptions']=[dict(id='A1',text='Pending assumption',status='open',decision_ref='decision')]
    c['spec']['design_refs']=[dict(id='D1',path='design.md',sha256='b'*64)]
    c['spec']['bug_context']=dict(current_behavior='Old',expected_behavior='New',unchanged_behavior=['Retain'])
    schemas=checker.load_schemas(['spec-contract.schema.json','task-plan.schema.json','task-contract.schema.json','test-design.schema.json'],checker.empty_result())
    registry=Registry().with_resource('task-contract.schema.json',Resource.from_contents(schemas['task-contract.schema.json']))
    total=0
    for artifact,name in [('spec','spec-contract.schema.json'),('plan','task-plan.schema.json'),('tests','test-design.schema.json')]:
        baseline=c[artifact]; oracle=Draft202012Validator(schemas[name],registry=registry)
        def paths(node,at=()):
            yield at,node
            if isinstance(node,dict):
                for k,v in node.items(): yield from paths(v,at+(k,))
            if isinstance(node,list):
                for i,v in enumerate(node): yield from paths(v,at+(i,))
        def mutate(at,value,delete=False):
            if not at: return value
            target=copy.deepcopy(baseline); parent=target
            for key in at[:-1]: parent=parent[key]
            if delete: del parent[at[-1]]
            else: parent[at[-1]]=value
            return target
        variants=[baseline]
        for at,node in paths(baseline):
            for value in [None,False,0,{},[], '', ' ', 'unknown', ['duplicate','duplicate']]: variants.append(mutate(at,value))
            if at and isinstance(at[-1],str): variants.append(mutate(at,None,delete=True))
            if isinstance(node,dict): variants.append(mutate(at,node|{'extra':True}))
            if isinstance(node,list) and node: variants.append(mutate(at,node+[copy.deepcopy(node[0])]))
        bug=copy.deepcopy(baseline)
        if artifact=='spec':
            bug['entry_order']='bugfix'; del bug['bug_context']; variants.append(bug)
        for variant in variants:
            ours=not checker.shape(variant,schemas[name],schemas)
            theirs=oracle.is_valid(variant)
            assert ours==theirs, (artifact,variant)
            total+=1
    assert total>700


def test_all_results_obey_closed_result_contract(checker):
    from jsonschema import Draft202012Validator
    schema=json.loads((OWNER/'schemas/trace-result.schema.json').read_text()); validator=Draft202012Validator(schema)
    c=case(); results=[checker.check_trace(**c),checker.check_trace(c['spec'],c['plan']),checker.empty_result()]
    for field in c['spec']:
        broken=case(); del broken['spec'][field]; results.append(checker.check_trace(**broken))
    broken=case(); broken['plan']['tasks'][0]['requirement_ids']=['R9']; results.append(checker.check_trace(**broken))
    for result in results: assert validator.is_valid(result), list(validator.iter_errors(result))
    result=results[0]|{'semantic_correctness':'passed'}
    assert not validator.is_valid(result)


def test_unknown_schema_keyword_and_missing_test_schema_fail_closed(checker):
    path=checker.SCHEMA_ROOT/'spec-contract.schema.json'; value=json.loads(path.read_text()); value['unevaluatedProperties']=False; path.write_text(json.dumps(value))
    r=checker.check_trace(**case())
    assert {e['code'] for e in r['errors']}=={'package_error'}
    assert r['matrix']==[]


def test_unselected_tests_do_not_load_test_schema(checker):
    (checker.SCHEMA_ROOT/'test-design.schema.json').unlink()
    c=case()
    assert checker.check_trace(c['spec'],c['plan'])['mechanical_passed']
    assert not checker.check_trace(**c)['mechanical_passed']


def test_detached_stdlib_cli_byte_binding_and_structured_failures(checker,tmp_path):
    import hashlib
    import subprocess
    import sys
    from jsonschema import Draft202012Validator
    script=Path(checker.__file__); c=case()
    sp=tmp_path/'spec.json'; pp=tmp_path/'plan.json'; tp=tmp_path/'tests.json'
    sp.write_text(json.dumps(c['spec'])+'\n'); pp.write_text(json.dumps(c['plan'])); tp.write_text(json.dumps(c['tests']))
    schema=json.loads((OWNER/'schemas/trace-result.schema.json').read_text()); validator=Draft202012Validator(schema)
    def run(*args):
        p=subprocess.run([sys.executable,'-I','-S',str(script),*map(str,args)],cwd=tmp_path,capture_output=True,text=True)
        assert p.stderr==''
        r=json.loads(p.stdout); assert validator.is_valid(r), list(validator.iter_errors(r)); return p,r
    p,r=run('--spec',sp,'--plan',pp)
    assert p.returncode==0 and r['source_binding']=='not_supplied'
    assert run('--spec',sp,'--plan',pp)[0].stdout==p.stdout
    c['plan']['spec_sha256']=hashlib.sha256(sp.read_bytes()).hexdigest(); pp.write_text(json.dumps(c['plan']))
    assert run('--spec',sp,'--plan',pp,'--tests',tp)[1]['source_binding']=='matched'
    sp.write_bytes(sp.read_bytes()+b' ')
    p,r=run('--spec',sp,'--plan',pp)
    assert p.returncode==1 and r['source_binding']=='mismatch' and r['matrix']==[]
    for raw,code in [(b'{','invalid_json'),(b'{"a":1,"a":2}','duplicate_json_key'),(b'\xff','invalid_utf8'),(b'NaN','invalid_json'),(b'Infinity','invalid_json')]:
        sp.write_bytes(raw); p,r=run('--spec',sp,'--plan',pp)
        assert p.returncode==2 and r['errors'][0]['code']==code
        assert r['input_sha256']['spec']==hashlib.sha256(raw).hexdigest()
    assert run('--spec',tmp_path/'absent','--plan',pp)[0].returncode==2
    assert run('--wat')[1]['errors'][0]['code']=='usage_error'


@pytest.mark.parametrize('namespace',['requirements','source_refs','assumptions','design_refs','tasks','verification','tests'])
def test_duplicate_ids_fail_in_each_namespace(checker,namespace):
    c=case()
    if namespace=='assumptions': c['spec'][namespace]=[dict(id='A',text='Assumption',status='open')]*2
    elif namespace=='design_refs': c['spec'][namespace]=[dict(id='D',path='design',sha256='a'*64)]*2
    elif namespace in ('requirements','source_refs'): c['spec'][namespace].append(c['spec'][namespace][0])
    elif namespace=='tasks': c['plan']['tasks'].append(c['plan']['tasks'][0])
    elif namespace=='verification': c['plan']['tasks'][0]['verification']*=2
    else: c['tests']['tests'].append(c['tests']['tests'][0])
    r=checker.check_trace(**c)
    assert {e['code'] for e in r['errors']}=={'duplicate_id'}
    assert r['matrix']==[]


@pytest.mark.parametrize('kind,code',[('unknown_inventory','unknown_requirement'),('zero_tests','uncovered_test_requirement'),('unknown_completion','unknown_completed_task'),('unknown_dep','unknown_dependency')])
def test_selected_inventory_and_plan_membership(checker,kind,code):
    c=case()
    if kind=='unknown_inventory': c['tests']['requirement_ids'].append('R9')
    elif kind=='zero_tests': c['tests']['tests']=[]
    elif kind=='unknown_completion': c['plan']['completed_task_ids']=['T9']
    else: c['plan']['tasks'][0]['depends_on']=['T9']
    r=checker.check_trace(**c)
    assert not r['mechanical_passed'] and code in {e['code'] for e in r['errors']}


def test_namespace_collision_is_allowed_and_cycles_belong_to_graph(checker):
    c=case(); c['spec']['source_refs'][0]['id']='R1'; c['spec']['id']=c['plan']['id']=c['tests']['id']='same'
    c['plan']['tasks'][0]['depends_on']=['T2']; c['plan']['tasks'][1]['depends_on']=['T1']
    r=checker.check_trace(**c,design_links=True)
    assert r['mechanical_passed'] and r['graph_validation']=='not_assessed'


@pytest.mark.parametrize('selected', [None,False,[], 'invalid', 7])
def test_selected_invalid_tests_cannot_downgrade_to_omission(checker,tmp_path,selected):
    import hashlib
    import subprocess
    import sys
    from jsonschema import Draft202012Validator
    c=case(); paths={name:tmp_path/f'{name}.json' for name in ('spec','plan','tests')}
    for name in ('spec','plan'): paths[name].write_text(json.dumps(c[name]))
    paths['tests'].write_text(json.dumps(selected))
    result=subprocess.run([sys.executable,'-I','-S',checker.__file__,'--spec',str(paths['spec']),'--plan',str(paths['plan']),'--tests',str(paths['tests'])],capture_output=True,text=True)
    assert result.returncode==1 and result.stderr==''
    payload=json.loads(result.stdout)
    assert payload['tests_status']=='supplied' and payload['test_link_validation']=='not_assessed'
    assert payload['test_execution']=='not_run' and payload['matrix']==[]
    assert not payload['mechanical_passed']
    assert payload['errors']==[{'artifact':'tests','code':'schema_error','detail':'Wrong JSON type','ids':[],'pointer':''}]
    assert payload['input_sha256']['tests']==hashlib.sha256(paths['tests'].read_bytes()).hexdigest()
    assert 'test-design.schema.json' in payload['schema_sha256']
    validator=Draft202012Validator(json.loads((OWNER/'schemas/trace-result.schema.json').read_text()))
    assert validator.is_valid(payload)


@pytest.mark.parametrize('artifact,location', [('spec','key'),('plan','id'),('tests','id')])
@pytest.mark.parametrize('bad', ['\ud800','\udfff'])
def test_trace_cli_rejects_lone_surrogate_keys_and_values(checker,tmp_path,artifact,location,bad):
    import subprocess
    import sys
    c=case()
    if location=='key': c[artifact][bad]=True
    elif artifact=='plan': c[artifact]['tasks'][0]['id']='T'+bad
    else: c[artifact]['tests'][0]['id']='TEST'+bad
    paths={name:tmp_path/f'{name}.json' for name in c}
    for name,path in paths.items(): path.write_text(json.dumps(c[name],ensure_ascii=True))
    result=subprocess.run([sys.executable,'-I','-S',checker.__file__,'--spec',str(paths['spec']),'--plan',str(paths['plan']),'--tests',str(paths['tests'])],capture_output=True,text=True)
    assert result.returncode==2 and result.stderr==''
    payload=json.loads(result.stdout)
    assert not payload['mechanical_passed'] and payload['matrix']==[]
    assert payload['errors']==[{'artifact':artifact,'code':'invalid_json','detail':'Input contains an unpaired Unicode surrogate','ids':[],'pointer':''}]
    assert payload['tests_status']=='supplied' and payload['test_link_validation']=='not_assessed'


def test_trace_cli_preserves_valid_unicode_in_success_and_error_pointer(checker,tmp_path):
    import subprocess
    import sys
    c=case(); ident='Ré漢😀'
    c['spec']['requirements'][0]['id']=ident; c['plan']['tasks'][0]['requirement_ids']=[ident]
    c['tests']['requirement_ids'][0]=ident; c['tests']['tests'][0]['requirements']=[ident]
    paths={name:tmp_path/f'{name}.json' for name in c}
    def run():
        for name,path in paths.items(): path.write_text(json.dumps(c[name],ensure_ascii=True))
        return subprocess.run([sys.executable,'-I','-S',checker.__file__,'--spec',str(paths['spec']),'--plan',str(paths['plan']),'--tests',str(paths['tests'])],capture_output=True,text=True)
    result=run(); payload=json.loads(result.stdout)
    assert result.returncode==0 and result.stderr==''
    assert ident in [row['requirement_id'] for row in payload['matrix']]
    c['spec']['extra/'+ident]=True
    result=run(); payload=json.loads(result.stdout)
    assert result.returncode==1 and result.stderr==''
    assert payload['errors'][0]['pointer']=='/extra~1'+ident


def test_trace_emitter_defensively_escapes_python_api_surrogates(checker,capsys):
    c=case(); c['plan']['tasks'][0]['id']='T\ud800'
    result=checker.check_trace(**c)
    assert checker.emit(result)==0
    text=capsys.readouterr().out
    assert '\\ud800' in text and json.loads(text)['matrix'][0]['task_ids']==['T\ud800']
    text.encode('utf-8')
