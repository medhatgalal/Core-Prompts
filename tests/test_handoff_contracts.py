"""Executable handoff integrity tests. These do not assert independent semantic review."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from test_review_package import git_repo, invoke, commit, load_collector, SOURCE

VERIFY = SOURCE / 'scripts/verify_review_package.py'


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


@pytest.fixture
def bound(git_repo, tmp_path):
    repo, git, base = git_repo
    commit(git, repo, 'first\n'); head = commit(git, repo, 'second\n')
    producer = load_collector()
    args = type('Args', (), {'repo':str(repo),'base':base,'head':head})()
    _, _, admin, algorithm = producer.repository_preflight(args)
    # Caller identity and owner sources captured before collector execution.
    expected = {'schema_version':'ReviewPackageExpectation.v1','scope':'current_committed_candidate',
        'task':{'id':'D6.S2','owner':'fixture','generation':1},
        'repository':{'id':'fixture-repo','object_format':algorithm,'local_identity_sha256':producer.digest(
            producer.canonical({'common_git_dir':admin[0].as_posix(),'object_format':algorithm}))},
        'base':base,'head':head,'candidate_ref':'HEAD','spec_sha256':None,'plan_sha256':None,
        'producer':{'owner':'engos-quality-code-review', **{key:hash_bytes((SOURCE/path).read_bytes()) for key,path in (
            ('script_sha256','scripts/review_package.py'),('schema_sha256','schemas/review-package.schema.json'),
            ('resource_map_sha256','resource-map.json'))}},
        'verifier':{'script_sha256':hash_bytes(VERIFY.read_bytes()),'expectation_schema_sha256':hash_bytes(
            (SOURCE/'schemas/review-package-expectation.schema.json').read_bytes())}}
    package = tmp_path/'package'; result = invoke(repo,base,head,package)
    assert result.returncode == 0, result.stderr
    stdout = tmp_path/'result.json'; stdout.write_bytes(result.stdout)
    expected.update(collector_exit_code=result.returncode,collection_result_sha256=hash_bytes(result.stdout),
                    manifest_sha256=json.loads(result.stdout)['manifest_sha256'])
    expectation = tmp_path/'expect.json'; write_json(expectation, expected)
    def verify():
        return subprocess.run([sys.executable,'-I',str(VERIFY),'--repo',str(repo),'--package',str(package),
            '--result',str(stdout),'--expect',str(expectation),'--expect-sha256',hash_bytes(expectation.read_bytes())],capture_output=True)
    return repo, git, package, stdout, expectation, expected, verify


def test_exact_binding_not_review(bound):
    *_, verify = bound
    run = verify(); assert run.returncode == 0, run.stdout + run.stderr
    result = json.loads(run.stdout)
    assert result['binding_status'] == 'matched' and result['review_status'] == 'not_assessed' and result['errors'] == []


@pytest.mark.parametrize('key,value', [('id','wrong'),('owner','wrong'),('generation',2),('generation',True)])
def test_external_subject_mismatch(bound,key,value):
    _,_,_,_,expectation,expected,verify = bound
    expected['task'][key]=value; write_json(expectation,expected)
    result=verify(); assert result.returncode != 0 and json.loads(result.stdout)['binding_status'] != 'matched'


@pytest.mark.parametrize('fault', ['staged','unstaged','untracked','skip','assume','moved','sparse'])
def test_current_candidate_faults(bound,fault):
    repo,git,_,_,_,_,verify=bound
    if fault == 'moved': commit(git,repo,'later\n')
    elif fault == 'untracked': (repo/'sentinel').write_text('preserve\n')
    elif fault == 'skip': git('update-index','--skip-worktree','a')
    elif fault == 'assume': git('update-index','--assume-unchanged','a')
    elif fault == 'sparse': git('config','core.sparseCheckout','true')
    else:
        (repo/'a').write_text('dirty\n')
        if fault == 'staged': git('add','a')
    before={p.name:p.read_bytes() for p in repo.iterdir() if p.is_file()}
    result=verify(); assert result.returncode != 0, result.stdout
    assert before == {p.name:p.read_bytes() for p in repo.iterdir() if p.is_file()}


@pytest.mark.parametrize('fault',['blob','extra','partial','symlink','hardlink','duplicate','decorated','incomplete','diff_rehashed'])
def test_artifact_and_protocol_faults(bound,fault):
    _,_,package,stdout,expectation,expected,verify=bound
    manifest_path=package/'manifest.json'; manifest=json.loads(manifest_path.read_bytes())
    if fault == 'blob':
        path=package/manifest['files'][0]['new']['object']['path']; path.write_bytes(b'wrong')
    elif fault == 'extra': (package/'extra').write_bytes(b'extra')
    elif fault == 'partial': (package/'manifest.partial').write_bytes(b'partial')
    elif fault == 'symlink':
        path=package/'diff.patch'; saved=path.read_bytes(); path.unlink(); target=package.parent/'outside'; target.write_bytes(saved); path.symlink_to(target)
    elif fault == 'hardlink':
        import os
        os.link(package/'diff.patch',package.parent/'extra-link')
    elif fault in ('duplicate','decorated'):
        data=stdout.read_bytes(); stdout.write_bytes(data.replace(b'{',b'{"status":"complete",',1) if fault=='duplicate' else b'prefix\n'+data)
        expected['collection_result_sha256']=hash_bytes(stdout.read_bytes()); write_json(expectation,expected)
    else:
        if fault == 'incomplete': manifest['status']='incomplete'
        else:
            path=package/'diff.patch'; path.write_bytes(b'omitted patch\n'); manifest['diff'].update(sha256=hash_bytes(path.read_bytes()),bytes=path.stat().st_size)
        write_json(manifest_path,manifest); expected['manifest_sha256']=hash_bytes(manifest_path.read_bytes())
        result=json.loads(stdout.read_bytes()); result['manifest_sha256']=expected['manifest_sha256']; write_json(stdout,result)
        expected['collection_result_sha256']=hash_bytes(stdout.read_bytes()); write_json(expectation,expected)
    result=verify(); assert result.returncode != 0, result.stdout


def test_changed_source_pin_rejected(bound):
    _,_,_,_,expectation,expected,verify=bound
    expected['producer']['script_sha256']='0'*64; write_json(expectation,expected)
    result=verify(); assert result.returncode != 0 and json.loads(result.stdout)['binding_status']=='unverified'


def test_expiry_discriminator_actual():
    # Frozen synthetic fixture: raw observations, never a causal-review substitute.
    observed=[{'now':now,'parsed':int(str(now)),'faulty_accepts':not(int(str(now))>10),
               'contract_accepts':not(int(str(now))>=10)} for now in (9,10,11)]
    assert [r['faulty_accepts'] for r in observed] == [True,True,False]
    assert [r['contract_accepts'] for r in observed] == [True,False,False]


def test_bounded_intermit_exposure():
    schedule=[False,False,False]
    observed=[{'attempt':i+1,'failure':failure} for i,failure in enumerate(schedule)]
    assert len(observed)==3 and not any(row['failure'] for row in observed)
    # Passing synthetic exposures contain no ordering discriminator or repair evidence.


def test_actual_oracle_import_detached_and_freshness(tmp_path):
    import shutil
    from intent_pipeline.capability_resources import load_capability_bundle, load_resource_bundle, ResourceContractError
    source_root = SOURCE.parents[2]
    repo = tmp_path/'canonical'; (repo/'ssot').mkdir(parents=True)
    slugs=('engos-delivery-implement-slice','engos-quality-testing-review')
    for slug in slugs:
        (repo/'ssot'/f'{slug}.md').write_bytes((source_root/'ssot'/f'{slug}.md').read_bytes())
        shutil.copytree(source_root/'sources/capability-resources'/slug,repo/'sources/capability-resources'/slug)
    # This fixture exercises the actual oracle owner/consumer pair. Unrelated
    # registry entries require their own source trees and belong to the full
    # canonical registry checks, rather than an incomplete copied repository.
    registry=json.loads((source_root/'.meta/shared-resource-imports.json').read_text())
    registry['imports']=[row for row in registry['imports'] if row['id']=='test-oracles-v1']
    assert len(registry['imports'])==1
    (repo/'.meta').mkdir(); (repo/'.meta/shared-resource-imports.json').write_text(json.dumps(registry))
    slug=slugs[0]; bundle=load_capability_bundle(repo,slug,'','verification')
    assert len(bundle['resources'])==1
    reference=bundle['resources'][0]
    assert reference['source_path']=='sources/capability-resources/engos-quality-testing-review/references/test-oracles.md'
    assert not (repo/'sources/capability-resources'/slug/'references/test-oracles.md').exists()
    # Select only D5 resources in an independent snapshot, no installed D7 sibling.
    detached=tmp_path/'detached'; detached.mkdir()
    shutil.copytree(repo/'sources/capability-resources'/slug,detached,dirs_exist_ok=True)
    for item in bundle['resources']:
        path=detached/item['path']; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(item['content'].encode())
    (detached/'shared-resource-imports.json').write_text(json.dumps(bundle['shared_imports']))
    assert load_resource_bundle(detached,'verification')==bundle
    assert load_resource_bundle(detached,'receipt')['resources']
    owner=repo/'sources/capability-resources'/slugs[1]/'references/test-oracles.md'; owner.write_text(owner.read_text()+'\nchanged owner\n')
    with pytest.raises(ResourceContractError): load_capability_bundle(repo,slug,'','verification')
    assert load_resource_bundle(detached,'verification')==bundle
    (detached/reference['path']).write_text('tampered')
    with pytest.raises(ResourceContractError): load_resource_bundle(detached,'verification')


def test_verify_route_coexists_default_review():
    from intent_pipeline.capability_resources import load_resource_bundle
    review=load_resource_bundle(SOURCE,'review'); verification=load_resource_bundle(SOURCE,'verify-package')
    assert {r['path'] for r in review['resources']}=={'references/review-targets.md','schemas/findings.schema.json'}
    assert {r['path'] for r in verification['resources']}=={'references/review-package-consumption.md',
        'scripts/verify_review_package.py','scripts/review_package.py','schemas/review-package.schema.json',
        'schemas/review-package-expectation.schema.json'}


def test_expectation_mutation_at_final_observation_rejected(bound,monkeypatch,capfd):
    import importlib.util
    repo,_,package,stdout,expectation,_,_=bound
    spec=importlib.util.spec_from_file_location('verify_fixture',VERIFY)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    original=module.ReadSet.recheck; fired=[]
    def mutate_then_check(reads):
        expectation.write_bytes(expectation.read_bytes()+b' '); fired.append(True)
        original(reads)
    monkeypatch.setattr(module.ReadSet,'recheck',mutate_then_check)
    pinned=hash_bytes(expectation.read_bytes())
    result=module.main(['--repo',str(repo),'--package',str(package),'--result',str(stdout),
        '--expect',str(expectation),'--expect-sha256',pinned])
    output=json.loads(capfd.readouterr().out)
    assert fired and hash_bytes(expectation.read_bytes())!=pinned
    assert result==2 and output['binding_status']=='rejected'


@pytest.mark.parametrize('key,value',[('base','0'*40),('head','0'*40),('spec_sha256','1'*64),('plan_sha256','2'*64),
    ('repository.id','other'),('repository.local_identity_sha256','0'*64),('repository.object_format','sha256')])
def test_external_range_repository_and_optional_hash_mismatch(bound,key,value):
    _,_,_,_,expectation,expected,verify=bound
    if '.' in key:
        parent,field=key.split('.'); expected[parent][field]=value
    else: expected[key]=value
    write_json(expectation,expected)
    result=verify(); assert result.returncode!=0 and json.loads(result.stdout)['binding_status']!='matched'


def test_real_source_drift_then_explicit_fresh_collection(bound,tmp_path):
    import shutil
    repo,_,package,stdout,expectation,expected,_=bound
    owner=tmp_path/'selected-owner'; shutil.copytree(SOURCE,owner)
    script=owner/'scripts/review_package.py'; script.write_bytes(script.read_bytes()+b'\n# Controlled independently selected fixture source revision.\n')
    verifier=owner/'scripts/verify_review_package.py'
    def verify():
        return subprocess.run([sys.executable,'-I',str(verifier),'--repo',str(repo),'--package',str(package),
            '--result',str(stdout),'--expect',str(expectation),'--expect-sha256',hash_bytes(expectation.read_bytes())],capture_output=True)
    old=expected['producer']['script_sha256']; assert hash_bytes(script.read_bytes())!=old
    result=verify(); assert result.returncode!=0
    # Fixture caller deliberately selects changed source before fresh invocation, never reads pin from returned manifest.
    expected['producer']['script_sha256']=hash_bytes(script.read_bytes())
    package=tmp_path/'fresh-package'
    collection=subprocess.run([sys.executable,'-I',str(script),'--repo',str(repo),'--base',expected['base'],
        '--head',expected['head'],'--out',str(package),'--task-id',expected['task']['id'],'--owner',expected['task']['owner'],
        '--generation','1','--repository-id',expected['repository']['id']],capture_output=True)
    assert collection.returncode==0,collection.stderr
    stdout.write_bytes(collection.stdout); expected['collection_result_sha256']=hash_bytes(collection.stdout)
    expected['manifest_sha256']=json.loads(collection.stdout)['manifest_sha256']; write_json(expectation,expected)
    result=verify(); assert result.returncode==0,result.stdout


@pytest.mark.parametrize('driver',['clean','process'])
def test_filter_driver_never_executes_or_masks_dirty(bound,tmp_path,driver):
    repo,git,package,stdout,expectation,expected,verify=bound
    # Commit attribute before collection and independently renew exact candidate.
    (repo/'.gitattributes').write_text('a filter=probe\n'); git('add','.gitattributes'); git('commit','-qm','filter attribute')
    expected['head']=git('rev-parse','HEAD').decode().strip()
    fresh=tmp_path/'filter-package'
    collection=invoke(repo,expected['base'],expected['head'],fresh); assert collection.returncode==0
    # bound's verifier closure retains original leaf, replace only its complete inert evidence.
    import shutil
    for path in package.iterdir():
        if path.is_dir(): shutil.rmtree(path)
        else: path.unlink()
    shutil.copytree(fresh,package,dirs_exist_ok=True)
    stdout.write_bytes(collection.stdout); expected.update(collection_result_sha256=hash_bytes(collection.stdout),
        manifest_sha256=json.loads(collection.stdout)['manifest_sha256']); write_json(expectation,expected)
    assert verify().returncode==0
    marker=tmp_path/'driver-ran'; script=tmp_path/'filter.py'
    if driver=='clean':
        text='from pathlib import Path\nimport sys\nPath('+repr(str(marker))+').write_text("executed\\n")\nsys.stdin.buffer.read()\nsys.stdout.buffer.write(b"second\\n")\n'
    else:
        text='''from pathlib import Path
import sys
marker=Path(MARKER)
def packet():
    size=int(sys.stdin.buffer.read(4),16)
    return None if size==0 else sys.stdin.buffer.read(size-4)
def group():
    values=[]
    while True:
        value=packet()
        if value is None: return values
        values.append(value)
def send(values):
    for value in values:
        sys.stdout.buffer.write(('%04x'%(len(value)+4)).encode()+value)
    sys.stdout.buffer.write(b'0000'); sys.stdout.buffer.flush()
group(); send([b'git-filter-server\\n',b'version=2\\n'])
group(); send([b'capability=clean\\n'])
while True:
    headers=group(); content=group()
    marker.write_text('executed\\n')
    send([b'status=success\\n']); send([b'second\\n']); send([])
'''.replace('MARKER',repr(str(marker)))
    script.write_text(text); git('config','filter.probe.'+driver,sys.executable+' '+str(script))
    (repo/'a').write_text('TAMPER\n')
    assert not marker.exists()
    result=verify()
    print(json.dumps({'driver':driver,'marker_exists_after':marker.exists(),
        'marker_text':marker.read_text() if marker.exists() else None,'worktree_after':(repo/'a').read_text(),
        'verifier_exit':result.returncode,'verifier_stdout':result.stdout.decode()}))
    assert result.returncode==2,result.stdout+result.stderr
    assert not marker.exists(),'verifier executed configured '+driver+' driver'
    assert (repo/'a').read_text()=='TAMPER\n'
    assert 'filter' in json.loads(result.stdout)['errors'][0]['message']


@pytest.mark.parametrize('arguments',[[],['--unknown'],['--repo'],['--help']])
def test_verifier_cli_syntax_exit_contract(arguments):
    result=subprocess.run([sys.executable,'-I',str(VERIFY),*arguments],capture_output=True)
    assert result.returncode==(0 if arguments==['--help'] else 3)
    if arguments!=['--help']: assert result.stdout==b''


@pytest.mark.parametrize('value',['unused-command',' '])
def test_configured_filter_denied_even_without_selected_attribute(bound,value):
    _,git,_,_,_,_,verify=bound
    git('config','filter.unused.clean',value)
    result=verify(); assert result.returncode==2
    assert git('config','--get','filter.unused.clean').decode().rstrip('\n')==value
    assert 'filter' in json.loads(result.stdout)['errors'][0]['message']


def test_empty_filter_config_has_no_driver(bound):
    _,git,_,_,_,_,verify=bound
    git('config','filter.unused.clean',''); git('config','filter.unused.process','')
    result=verify(); assert result.returncode==0,result.stdout


def test_local_fsmonitor_external_diff_not_executed(bound,tmp_path):
    _,git,_,_,_,_,verify=bound
    marker=tmp_path/'external-command-ran';script=tmp_path/'external.py'
    script.write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("executed")\n')
    command=sys.executable+' '+str(script)
    git('config','core.fsmonitor',command);git('config','diff.external',command)
    result=verify();assert result.returncode==0,result.stdout
    assert not marker.exists()


def test_unknown_flag_with_complete_invocation_is_exit_three(bound):
    repo,_,package,stdout,expectation,_,_=bound
    result=subprocess.run([sys.executable,'-I',str(VERIFY),'--repo',str(repo),'--package',str(package),
        '--result',str(stdout),'--expect',str(expectation),'--expect-sha256',hash_bytes(expectation.read_bytes()),
        '--unknown'],capture_output=True)
    assert result.returncode==3 and result.stdout==b''
