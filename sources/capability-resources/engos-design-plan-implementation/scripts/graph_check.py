"""Offline mechanical assessment; no execution or semantic approval.

The bounded schema interpreter supports only the current production vocabulary.
Unknown keywords fail closed. Schema facts are read from explicit bundle files.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA_ROOT = Path(__file__).resolve().parents[1] / 'schemas'
VOCABULARY = {'$schema','title','description','type','additionalProperties','required','properties','const','enum','minLength','pattern','items','minItems','uniqueItems','anyOf','allOf','if','then','$ref'}

class AssessmentError(Exception):
    def __init__(self, code, artifact, detail):
        self.record = error(code, artifact, '', [], detail)


def error(code, artifact, pointer='', ids=(), detail='Mechanical contract failed'):
    return dict(code=code, artifact=artifact, pointer=pointer, ids=sorted(ids), detail=detail)


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise AssessmentError('duplicate_json_key','cli','Duplicate JSON object key')
        result[key] = value
    return result


def decode(raw, artifact):
    try:
        text = raw.decode('utf-8')
    except UnicodeError:
        raise AssessmentError('invalid_utf8',artifact,'Input is not UTF-8') from None
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        pending = [value]
        while pending:
            node = pending.pop()
            if isinstance(node, str) and any(0xD800 <= ord(char) <= 0xDFFF for char in node):
                raise AssessmentError('invalid_json', artifact, 'Input contains an unpaired Unicode surrogate')
            if isinstance(node, dict):
                pending.extend(node.keys())
                pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)
        return value
    except AssessmentError as exc:
        exc.record['artifact'] = artifact
        raise
    except (ValueError, RecursionError):
        raise AssessmentError('invalid_json',artifact,'Input is not strict JSON') from None


def read_input(path, artifact, identities=None):
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise AssessmentError('input_read_error',artifact,'Cannot read supplied input') from None
    if identities is not None: identities[artifact] = hashlib.sha256(raw).hexdigest()
    return raw, decode(raw, artifact)


def pointer(parent, key):
    return parent + '/' + str(key).replace('~','~0').replace('/','~1')


def equal(a, b):
    # JSON equality distinguishes booleans from numbers and compares objects unordered.
    if type(a) is not type(b):
        return type(a) in (int,float) and type(b) in (int,float) and a == b
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k],b[k]) for k in a)
    return a == b


def schema_contract(node, name):
    if not isinstance(node, dict) or set(node) - VOCABULARY:
        raise AssessmentError('package_error','package','Unsupported schema vocabulary')
    if '$schema' in node and node['$schema'] != 'https://json-schema.org/draft/2020-12/schema':
        raise AssessmentError('package_error','package','Unsupported schema dialect')
    for key in ('title','description'):
        if key in node and not isinstance(node[key],str):
            raise AssessmentError('package_error','package','Invalid schema annotation')
    if '$ref' in node and node['$ref'] != 'task-contract.schema.json':
        raise AssessmentError('package_error','package','Unsupported schema reference')
    if 'type' in node and node['type'] not in ('object','array','string','null'):
        raise AssessmentError('package_error','package','Unsupported schema type')
    if 'additionalProperties' in node and not isinstance(node['additionalProperties'],bool):
        raise AssessmentError('package_error','package','Unsupported additionalProperties contract')
    if 'required' in node and (not isinstance(node['required'],list) or any(not isinstance(x,str) for x in node['required'])):
        raise AssessmentError('package_error','package','Invalid required contract')
    for key in ('minLength','minItems'):
        if key in node and (type(node[key]) is not int or node[key] < 0):
            raise AssessmentError('package_error','package','Invalid minimum contract')
    if 'uniqueItems' in node and type(node['uniqueItems']) is not bool:
        raise AssessmentError('package_error','package','Invalid uniqueness contract')
    if 'enum' in node and (not isinstance(node['enum'],list) or not node['enum']):
        raise AssessmentError('package_error','package','Invalid enum contract')
    if 'pattern' in node:
        try:
            re.compile(node['pattern'])
        except (TypeError,re.error):
            raise AssessmentError('package_error','package','Invalid schema pattern') from None
    children=[]
    if 'properties' in node:
        if not isinstance(node['properties'],dict):
            raise AssessmentError('package_error','package','Invalid properties contract')
        children.extend(node['properties'].values())
    for key in ('items','if','then'):
        if key in node: children.append(node[key])
    for key in ('anyOf','allOf'):
        if key in node:
            if not isinstance(node[key],list) or not node[key]:
                raise AssessmentError('package_error','package','Invalid composition contract')
            children.extend(node[key])
    for child in children: schema_contract(child, name)


def load_schemas(names, result):
    schemas = {}
    for name in names:
        path = SCHEMA_ROOT / name
        if path.is_symlink() or SCHEMA_ROOT.is_symlink() or path.resolve().parent != SCHEMA_ROOT.resolve():
            raise AssessmentError('package_error','package','Unsafe bundled schema path')
        try:
            raw = path.read_bytes()
        except OSError:
            raise AssessmentError('package_error','package','Missing bundled schema') from None
        result['schema_sha256'][name] = hashlib.sha256(raw).hexdigest()
        try:
            node = decode(raw,'package'); schema_contract(node,name)
        except (AssessmentError, RecursionError) as exc:
            raise AssessmentError('package_error','package','Invalid or unsupported bundled schema') from exc
        schemas[name] = node
    if 'task-contract.schema.json' in schemas:
        # This leaf cannot create a schema cycle or introduce a second base.
        def has_ref(node):
            if isinstance(node,dict): return '$ref' in node or any(has_ref(v) for v in node.values())
            if isinstance(node,list): return any(has_ref(v) for v in node)
            return False
        if has_ref(schemas['task-contract.schema.json']):
            raise AssessmentError('package_error','package','TaskContract must be a reference-free leaf')
    return schemas


def shape(value, schema, schemas, at=''):
    issues=[]
    def bad(text): issues.append((at,text))
    if '$ref' in schema:
        target=schemas.get(schema['$ref'])
        if target is None: raise AssessmentError('package_error','package','Missing schema reference target')
        issues.extend(shape(value,target,schemas,at))
    if 'type' in schema:
        types={'object':dict,'array':list,'string':str,'null':type(None)}
        if type(value) is not types[schema['type']]: bad('Wrong JSON type')
    if 'const' in schema and not equal(value,schema['const']): bad('Wrong constant')
    if 'enum' in schema and not any(equal(value,x) for x in schema['enum']): bad('Value outside enum')
    if isinstance(value,str):
        if len(value) < schema.get('minLength',0): bad('String too short')
        if 'pattern' in schema and re.search(schema['pattern'],value) is None: bad('String pattern mismatch')
    if isinstance(value,dict):
        for key in schema.get('required',[]):
            if key not in value: issues.append((pointer(at,key),'Missing required property'))
        props=schema.get('properties',{})
        for key,item in value.items():
            if key in props: issues.extend(shape(item,props[key],schemas,pointer(at,key)))
            elif schema.get('additionalProperties',True) is False: issues.append((pointer(at,key),'Unexpected property'))
    if isinstance(value,list):
        if len(value) < schema.get('minItems',0): bad('Array too short')
        if schema.get('uniqueItems',False) and any(equal(value[i],value[j]) for i in range(len(value)) for j in range(i)):
            bad('Duplicate array item')
        if 'items' in schema:
            for i,item in enumerate(value): issues.extend(shape(item,schema['items'],schemas,pointer(at,i)))
    if 'anyOf' in schema and not any(not shape(value,s,schemas,at) for s in schema['anyOf']): bad('No anyOf branch matches')
    for child in schema.get('allOf',[]): issues.extend(shape(value,child,schemas,at))
    if 'if' in schema and not shape(value,schema['if'],schemas,at) and 'then' in schema:
        issues.extend(shape(value,schema['then'],schemas,at))
    return issues


def validate_inputs(inputs, names, result):
    schemas=load_schemas(names,result)
    for artifact,value,name in inputs:
        for at,detail in shape(value,schemas[name],schemas):
            result['errors'].append(error('schema_error',artifact,at,[],detail))
    return not result['errors']


def duplicates(rows, artifact, at, result):
    seen=set()
    for i,row in enumerate(rows):
        ident=row['id']
        if ident in seen: result['errors'].append(error('duplicate_id',artifact,pointer(at,i),[ident],'Duplicate identifier in namespace'))
        seen.add(ident)


def plan_membership(plan,result):
    duplicates(plan['tasks'],'plan','/tasks',result)
    known={t['id'] for t in plan['tasks']}
    for i,t in enumerate(plan['tasks']):
        duplicates(t['verification'],'plan',f'/tasks/{i}/verification',result)
        for j,dep in enumerate(t['depends_on']):
            if dep not in known: result['errors'].append(error('unknown_dependency','plan',f'/tasks/{i}/depends_on/{j}',[dep],'Dependency is not a plan task'))
    for i,ident in enumerate(plan['completed_task_ids']):
        if ident not in known: result['errors'].append(error('unknown_completed_task','plan',f'/completed_task_ids/{i}',[ident],'Completion is not a plan task'))


def finish(result):
    records={json.dumps(e,sort_keys=True):e for e in result['errors']}
    result['errors']=sorted(records.values(),key=lambda e:(e['artifact'],e['pointer'],e['code'],tuple(e['ids'])))
    result['mechanical_passed']=not result['errors']
    return result


def base(version):
    return dict(schema_version=version,mechanical_passed=False,errors=[],input_sha256={},schema_sha256={},semantic_correctness='not_assessed',behavioral_verification='not_assessed',authority_verification='not_assessed')

class Parser(argparse.ArgumentParser):
    def error(self,message):
        raise AssessmentError('usage_error','cli','Invalid command arguments; use --help')


def emit(result):
    finish(result)
    serialized = json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)
    try:
        serialized.encode('utf-8')
    except UnicodeEncodeError:
        # Defensive handling for a direct Python API caller bypassing decode.
        # Escaping preserves string values; valid Unicode keeps normal output.
        serialized = json.dumps(result,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)
    print(serialized)
    return 0 if result['mechanical_passed'] else (2 if any(e['code'] in {'usage_error','input_read_error','invalid_json','invalid_utf8','duplicate_json_key','package_error'} for e in result['errors']) else 1)


def empty_result():
    return base('GraphCheckResult.v1') | dict(graph_validation='not_assessed',ready_task_ids=[],completed_task_ids=[],blocked_tasks=[],completion_inconsistencies=[],readiness_holds=[],readiness_observations=[],requirement_linkage='not_assessed',implementation_correctness='not_assessed')


def cyclic_components(graph):
    """Iterative Kosaraju: bounded by graph size without Python recursion."""
    seen=set(); order=[]
    for root in sorted(graph):
        if root in seen: continue
        stack=[(root,False)]
        while stack:
            node,done=stack.pop()
            if done: order.append(node); continue
            if node in seen: continue
            seen.add(node); stack.append((node,True))
            stack.extend((dep,False) for dep in sorted(graph[node],reverse=True) if dep not in seen)
    reverse={node:[] for node in graph}
    for node,deps in graph.items():
        for dep in deps: reverse[dep].append(node)
    seen=set(); cycles=[]
    for root in reversed(order):
        if root in seen: continue
        component=[]; stack=[root]; seen.add(root)
        while stack:
            node=stack.pop(); component.append(node)
            for dep in reverse[node]:
                if dep not in seen: seen.add(dep); stack.append(dep)
        if len(component)>1 or root in graph[root]: cycles.append(sorted(component))
    return sorted(cycles)


def check_graph(plan):
    result=empty_result()
    try:
        if not validate_inputs([('plan',plan,'task-plan.schema.json')],['task-plan.schema.json','task-contract.schema.json'],result):
            result['graph_validation']='failed'; return finish(result)
        result['completed_task_ids']=sorted(plan['completed_task_ids'])
        result['readiness_holds']=list(plan['unresolved'])
        observations=[]
        if plan['spec_sha256'] is None: observations.append(dict(pointer='/spec_sha256',reason='spec_digest_not_supplied'))
        for i,t in enumerate(plan['tasks']):
            if t['authority_ref'] is None: observations.append(dict(pointer=f'/tasks/{i}/authority_ref',reason='task_authority_not_supplied'))
            for j,item in enumerate(t['consumes']):
                if item['sha256'] is None: observations.append(dict(pointer=f'/tasks/{i}/consumes/{j}/sha256',reason='consumed_digest_not_supplied'))
        result['readiness_observations']=sorted(observations,key=lambda x:(x['pointer'],x['reason']))
        plan_membership(plan,result)
        for i,t in enumerate(plan['tasks']):
            if t['id'] in t['depends_on']: result['errors'].append(error('self_dependency','plan',f'/tasks/{i}/depends_on',[t['id']],'Task depends on itself'))
        if not any(e['code'] in {'duplicate_id','unknown_dependency'} for e in result['errors']):
            graph={t['id']:t['depends_on'] for t in plan['tasks']}
            for component in cyclic_components(graph): result['errors'].append(error('dependency_cycle','plan','/tasks',component,'Cyclic task component'))
        result['graph_validation']='failed' if result['errors'] else 'passed'
        if not result['errors']:
            completed=set(plan['completed_task_ids'])
            for t in sorted(plan['tasks'],key=lambda t:t['id']):
                pending=sorted(set(t['depends_on'])-completed)
                if t['id'] in completed:
                    if pending: result['completion_inconsistencies'].append(dict(task_id=t['id'],uncompleted_dependency_ids=pending))
                elif pending: result['blocked_tasks'].append(dict(task_id=t['id'],outstanding_dependency_ids=pending))
                else: result['ready_task_ids'].append(t['id'])
    except AssessmentError as exc:
        result['errors'].append(exc.record)
    except RecursionError:
        result['errors'].append(error('package_error','package',detail='Assessment exceeds supported nesting'))
    return finish(result)


def main(argv=None):
    result=empty_result(); identities={}
    parser=Parser(description=__doc__); parser.add_argument('--plan',required=True)
    try:
        args=parser.parse_args(argv)
        raw,plan=read_input(args.plan,'plan',identities)
        result=check_graph(plan); result['input_sha256']['plan']=hashlib.sha256(raw).hexdigest()
    except AssessmentError as exc: result['errors'].append(exc.record)
    result['input_sha256']=identities
    return emit(result)

if __name__ == '__main__':
    raise SystemExit(main())
