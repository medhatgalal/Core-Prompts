"""Program membership proof against the immutable real 32-skill donor and 36 source."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from core_install import planner, transaction
from test_install_bootstrap import put, snapshot, output, detached_call

DONOR = '8e24429574d7348fca070170e2197a36d627cd2d'
ADDITIONS = {'engos-design-specify-change', 'engos-design-plan-implementation',
             'engos-debug-diagnose-failure', 'engos-delivery-implement-slice'}
DRIVER = r'''
import hashlib, importlib.util, json, sys
from pathlib import Path
old, source, target = map(Path, sys.argv[1:4])
profile = json.loads(sys.argv[4])
spec = importlib.util.spec_from_file_location('archived_capsule', old/'scripts/deploy-profile.py')
engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
assert '_CAPSULE_PAYLOAD' in engine.__dict__
assert Path(engine.install_bundle.__file__).resolve() == old/'scripts/install_bundle.py'
plan = engine.plan(source, target, profile)
print(json.dumps({'engine_sha256':hashlib.sha256((old/'scripts/deploy-profile.py').read_bytes()).hexdigest(), 'plan':plan}), flush=True)
assert not plan['blockers'], plan['blockers']
print(json.dumps(engine.apply(source, target, profile, plan)), flush=True)
'''


@pytest.fixture(scope='module')
def donor(tmp_path_factory):
    old = tmp_path_factory.mktemp('immutable-v1-16-3')
    manifest = subprocess.check_output(['git', 'show', DONOR+':.meta/install-bundle.json'], cwd=ROOT)
    files = json.loads(manifest)['files']
    archive = subprocess.check_output(['git', 'archive', DONOR], cwd=ROOT)
    allowed = set(files) | {'.meta/install-bundle.json'}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for member in tree.getmembers():
            if member.name in allowed:
                assert member.isfile() and '..' not in Path(member.name).parts
                put(old, member.name, tree.extractfile(member).read(), files.get(member.name, {'mode':0o644})['mode'])
    assert set(snapshot(old)) == allowed
    assert (old/'.meta/install-bundle.json').read_bytes() == manifest
    return old


@pytest.fixture
def legacy(donor, tmp_path):
    target = tmp_path/'target'; target.mkdir()
    profile = {'schema':1, 'scope':'skills', 'targets':['kiro'], 'slugs':[], 'retire':[]}
    for rel in snapshot(donor):
        put(target, '.core-prompts-updater/'+rel, (donor/rel).read_bytes(), (donor/rel).stat().st_mode & 0o777)
    proc = subprocess.run([sys.executable, '-I', '-B', '-c', DRIVER, str(donor), str(donor), str(target), json.dumps(profile)], cwd=tmp_path, capture_output=True, text=True, timeout=90)
    assert proc.returncode == 0, output(proc)
    receipt = json.loads((target/planner.V1_RECEIPT).read_text())
    assert receipt['schema'] == 1 and len({p.split('/')[2] for p in receipt['skill_scope']}) == 32
    assert not ADDITIONS & {p.split('/')[2] for p in receipt['skill_scope']}
    return target


def apply(target, request):
    plan = planner.plan(ROOT, target, request)
    assert not plan['blockers'], plan['blockers']
    result = transaction.apply(ROOT, target, plan, lambda: planner.plan(ROOT, target, request))
    return plan, result


def selected(plan, provider='kiro'):
    return {k.split(':', 2)[2] for k in plan['selection'] if k.startswith(provider+':skill:')}


def test_a23_saved_empty_real_receipt_nonexpanding_then_both_policies(legacy, donor, tmp_path):
    before = snapshot(legacy)
    preview = planner.plan(ROOT, legacy, {'mode':'sync'})
    assert len(selected(preview)) == 32 and not ADDITIONS & selected(preview)
    assert preview['legacy_choices'][0]['choices'] == ['curated', 'full-catalog']
    assert snapshot(legacy) == before
    for policy in ('curated', 'full_catalog'):
        target = tmp_path/policy
        shutil.copytree(legacy, target)
        plan, result = apply(target, {'mode':'sync', 'providers':['kiro'], 'selection_policy':policy})
        assert result['status'] == 'complete'
        state = planner.read_state(target)
        assert state['schema'] == 3 and state['selection_policy'] == {'kiro':policy}
        assert (ADDITIONS <= selected(plan)) == (policy == 'full_catalog')
        assert len(selected(plan)) == (36 if policy == 'full_catalog' else 32)
        journal = json.loads(next((target/transaction.TRANSACTIONS).glob('*/journal.json')).read_text())
        assert plan['schema'] == 2 and journal['schema'] == 1
        assert result['schema'] == 2
        repeat = planner.plan(ROOT, target, {'mode':'sync'})
        assert not repeat['actions']
        detached = detached_call(donor, target, '--install', '--repo', str(target/'.core-prompts-updater'), '--target', str(target), '--dry-run')
        assert detached.returncode == 0, output(detached)
        assert json.loads(detached.stdout)['selection'] == state['selection']
    # Current-only explicit empty profile has no future-catalog consent.
    fresh = tmp_path/'explicit'; fresh.mkdir()
    plan, _ = apply(fresh, {'mode':'repair', 'profile':{'schema':1,'scope':'skills','targets':['kiro'],'slugs':[]}})
    assert len(selected(plan)) == 36 and planner.read_state(fresh)['schema'] == 2


@pytest.mark.parametrize('fault', ['missing','hash','scope-missing','scope-unmapped','scope-duplicate','identity','source'])
def test_a23_unproved_saved_membership_never_writes(legacy, fault):
    receipt_path = legacy/planner.V1_RECEIPT
    receipt = json.loads(receipt_path.read_text())
    if fault == 'missing':
        receipt_path.unlink()
    else:
        if fault == 'hash': receipt['approved_profile_sha256'] = '0'*64
        elif fault == 'scope-missing': receipt.pop('skill_scope')
        elif fault == 'scope-unmapped': receipt['skill_scope'] = ['.kiro/skills/nonexistent/SKILL.md']
        elif fault == 'scope-duplicate': receipt['skill_scope'].append(receipt['skill_scope'][0])
        elif fault == 'identity': receipt['files'][receipt['skill_scope'][0]]['identity']['sha256'] = '0'*64
        elif fault == 'source': receipt['files'][receipt['skill_scope'][0]]['source'] = '.kiro/skills/wrong/SKILL.md'
        receipt_path.write_bytes(transaction.encoded(receipt))
    before = snapshot(legacy)
    with pytest.raises(ValueError, match='LEGACY_MEMBERSHIP_UNPROVEN|saved profile and ownership differ'):
        planner.plan(ROOT, legacy, {'mode':'sync'})
    assert snapshot(legacy) == before


def test_a01_a02_schema2_no_consent_and_explicit_full(legacy):
    apply(legacy, {'mode':'sync'})
    assert planner.read_state(legacy)['schema'] == 2
    assert not ADDITIONS & selected(planner.plan(ROOT, legacy, {'mode':'sync'}))
    plan, _ = apply(legacy, {'mode':'sync','providers':['kiro'],'selection_policy':'full_catalog'})
    assert ADDITIONS <= selected(plan)
    for slug in ADDITIONS:
        src = ROOT/'.kiro/skills'/slug
        for file in src.rglob('*'):
            if file.is_file():
                assert transaction.identity(file) == transaction.identity(legacy/file.relative_to(ROOT))


def test_a03_curated_add_only_one_and_empty_stays_empty(tmp_path):
    target = tmp_path/'target'; target.mkdir()
    arch = 'engos-design-architecture'
    apply(target, {'mode':'install','providers':['kiro'],'slugs':[arch],'kinds':['skill'],'selection_policy':'curated'})
    plan, _ = apply(target, {'mode':'install','providers':['kiro'],'slugs':['engos-design-specify-change'],'kinds':['skill'],'selection_policy':'curated'})
    assert selected(plan) == {arch, 'engos-design-specify-change'}
    assert selected(planner.plan(ROOT,target,{'mode':'sync'})) == selected(plan)
    with pytest.raises(ValueError, match='fresh curated'):
        planner.plan(ROOT,tmp_path/'fresh',{'mode':'sync','providers':['kiro'],'selection_policy':'curated'})


def test_a04_mixed_shared_reader_expansion_blocks_exact_joint_choice(tmp_path):
    target = tmp_path/'target'; target.mkdir()
    arch = 'engos-design-architecture'
    profile = {'schema':1,'scope':'skills','targets':['codex','gemini'],'slugs':[arch]}
    apply(target, {'mode':'repair','profile':profile,'selection_policy':'curated'})
    before = snapshot(target)
    mixed = planner.plan(ROOT,target,{'mode':'sync','providers':['codex'],'selection_policy':'full_catalog'})
    assert any('SHARED_SURFACE_POLICY_CONFLICT' in b for b in mixed['blockers'])
    assert snapshot(target) == before
    joint, _ = apply(target, {'mode':'repair','profile':dict(profile,slugs=[]),'selection_policy':'full_catalog'})
    assert ADDITIONS <= selected(joint,'codex') and ADDITIONS <= selected(joint,'gemini')
    assert planner.read_state(target)['selection_policy'] == {'codex':'full_catalog','gemini':'full_catalog'}


@pytest.mark.parametrize('fault_index', [1, 5, -1])
def test_a13_actual_policy_and_packages_fault_rollback(legacy, monkeypatch, fault_index):
    before = snapshot(legacy)
    request = {'mode':'sync','providers':['kiro'],'selection_policy':'full_catalog'}
    plan = planner.plan(ROOT,legacy,request)
    original = transaction._replace
    count = 0
    fired = False
    limit = fault_index
    def fault(*args, **kwargs):
        nonlocal count, fired
        relative = Path(args[0]).relative_to(legacy).as_posix()
        if not relative.startswith(transaction.TRANSACTIONS + '/'):
            count += 1
        if (fault_index == -1 and relative == planner.STATE) or (fault_index != -1 and count == limit and not relative.startswith(transaction.TRANSACTIONS + '/')):
            fired = True
            raise OSError('program fixture injected replacement interruption')
        return original(*args, **kwargs)
    monkeypatch.setattr(transaction,'_replace',fault)
    with pytest.raises(Exception, match='program fixture injected'):
        transaction.apply(ROOT,legacy,plan,lambda:planner.plan(ROOT,legacy,request))
    assert fired
    monkeypatch.setattr(transaction,'_replace',original)
    transaction_id = next((legacy/transaction.TRANSACTIONS).iterdir()).name
    transaction.rollback(legacy,transaction_id)
    after = {k:v for k,v in snapshot(legacy).items() if not k.startswith(transaction.TRANSACTIONS+'/') and k != '.core-prompts-state/installation.lock'}
    assert after == before


def test_a05_provider_scope_and_full_to_curated_freeze(tmp_path):
    target = tmp_path/'target'; target.mkdir()
    profile = {'schema':1,'scope':'skills','targets':['kiro','claude'],'slugs':['engos-design-architecture']}
    apply(target, {'mode':'repair','profile':profile,'selection_policy':'curated'})
    plan, _ = apply(target, {'mode':'sync','providers':['kiro'],'selection_policy':'full_catalog'})
    assert ADDITIONS <= selected(plan)
    assert selected(plan, 'claude') == {'engos-design-architecture'}
    _, _ = apply(target, {'mode':'sync','providers':['kiro'],'selection_policy':'curated'})
    state = planner.read_state(target)
    assert state['selection_policy'] == {'kiro':'curated','claude':'curated'}
    assert len(selected(planner.plan(ROOT,target,{'mode':'sync'}))) == 36


@pytest.mark.parametrize('arguments', [
    ['--selection-policy','full-catalog'],
    ['--cli','kiro','--selection-policy','full-catalog','--repair'],
    ['--cli','kiro','--selection-policy','curated','--with-agents'],
    ['--cli','kiro','--selection-policy','curated','--surface-only','--slug','engos-design-architecture'],
    ['--cli','kiro','--selection-policy','full-catalog','--slug','engos-design-architecture'],
])
def test_a06_invalid_policy_cli_is_no_write(tmp_path, arguments):
    target = tmp_path/'target'; target.mkdir()
    proc = subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/deploy-profile.py'),'--install','--repo',str(ROOT),'--target',str(target),*arguments],capture_output=True,text=True,timeout=30)
    assert proc.returncode == 1 and 'INVALID_REQUEST' in proc.stderr
    assert snapshot(target) == {}


@pytest.fixture
def actual_package(tmp_path):
    target = tmp_path/'target'; target.mkdir()
    request = {'mode':'install','providers':['kiro'],'slugs':['engos-design-specify-change'],'kinds':['skill'],'runtime':False}
    apply(target,request)
    return target


def test_a07_actual_customized_and_third_party_package_preserved(actual_package):
    target = actual_package
    rel = '.kiro/skills/engos-design-specify-change/SKILL.md'
    (target/rel).write_text('user customization\n')
    put(target,'.kiro/skills/third-party/SKILL.md',b'not owned\n')
    before = snapshot(target)
    plan = planner.plan(ROOT,target,{'mode':'sync','runtime':False})
    assert any(p['package']=='kiro:skill:engos-design-specify-change' for p in plan['preserved'])
    assert not any(a['path'].startswith('.kiro/skills/') for a in plan['actions'])
    assert snapshot(target) == before


def test_a08_actual_owned_stale_member_exact_remove_and_backup(actual_package):
    target = actual_package
    rel = '.kiro/skills/engos-design-specify-change/resources/fixture-only-stale.txt'
    put(target,rel,b'labelled synthetic stale owned member\n')
    state = planner.read_state(target)
    state['packages']['kiro:skill:engos-design-specify-change']['files'][rel] = transaction.identity(target/rel)
    (target/planner.STATE).write_bytes(transaction.encoded(state))
    before = snapshot(target)
    plan,result = apply(target,{'mode':'sync','runtime':False})
    assert [a['path'] for a in plan['actions'] if a['op']=='remove'] == [rel]
    assert not (target/rel).exists()
    transaction.rollback(target,result['transaction'])
    after = {k:v for k,v in snapshot(target).items() if not k.startswith(transaction.TRANSACTIONS+'/')}
    prior = {k:v for k,v in before.items() if not k.startswith(transaction.TRANSACTIONS+'/')}
    assert after == prior


def test_a10_actual_old_capsule_refusal_then_current_bridge(legacy, donor, tmp_path):
    before = snapshot(legacy)
    profile = json.loads((legacy/planner.V1_PROFILE).read_text())
    old = subprocess.run([sys.executable,'-I','-B','-c',DRIVER,str(donor),str(ROOT),str(legacy),json.dumps(profile)],cwd=tmp_path,capture_output=True,text=True,timeout=90)
    assert old.returncode != 0 and ('standalone bundle file scope was removed' in old.stderr or 'reviewed refresh' in old.stderr)
    assert snapshot(legacy) == before
    apply(legacy,{'mode':'sync','providers':['kiro'],'selection_policy':'curated'})
    installed = legacy/'.core-prompts-updater/scripts/deploy-profile.py'
    assert transaction.identity(installed) == transaction.identity(ROOT/'scripts/deploy-profile.py')
    # Historical schema2 reader must reject explicit state3 rather than strip policy.
    refused = subprocess.run([sys.executable,'-I','-B',str(donor/'scripts/deploy-profile.py'),'--install','--repo',str(donor),'--target',str(legacy),'--dry-run'],cwd=tmp_path,capture_output=True,text=True,timeout=90)
    assert refused.returncode == 1 and 'INVALID_STATE' in refused.stderr
    repeat = detached_call(donor,legacy,'--install','--repo',str(legacy/'.core-prompts-updater'),'--target',str(legacy),'--dry-run')
    assert repeat.returncode == 0, output(repeat)


def test_a15_actual_later_edit_blocks_rollback_without_restore(actual_package):
    target = actual_package
    state = planner.read_state(target)
    rel = '.kiro/skills/engos-design-specify-change/resources/fixture-only-stale.txt'
    put(target,rel,b'fixture owned preimage\n')
    state['packages']['kiro:skill:engos-design-specify-change']['files'][rel] = transaction.identity(target/rel)
    (target/planner.STATE).write_bytes(transaction.encoded(state))
    _, result = apply(target,{'mode':'sync','runtime':False})
    (target/planner.STATE).write_text('later state user edit\n')
    before = snapshot(target)
    with pytest.raises(ValueError):
        transaction.rollback(target,result['transaction'])
    assert snapshot(target) == before


def test_a16_actual_unowned_extra_member_is_whole_package_preserved(actual_package):
    target = actual_package
    put(target,'.kiro/skills/engos-design-specify-change/resources/unowned-extra.txt',b'fixture unowned\n')
    before = snapshot(target)
    plan = planner.plan(ROOT,target,{'mode':'sync','runtime':False})
    assert plan['preserved'] and not any(a['path'].startswith('.kiro/') for a in plan['actions'])
    assert snapshot(target) == before


def test_saved_empty_curated_preserves_policy_and_never_means_all(tmp_path):
    target = tmp_path/'target';target.mkdir()
    state = {'schema':3,'owner':'Core-Prompts','selection':[], 'packages':{},'runtime':{}, 'selection_policy':{'kiro':'curated'}}
    put(target,planner.STATE,transaction.encoded(state))
    plan,_ = apply(target,{'mode':'sync','runtime':False})
    assert not plan['selection'] and planner.read_state(target)['selection_policy'] == {'kiro':'curated'}


def test_explicit_cli_all_cannot_combine_with_profile(tmp_path):
    profile=tmp_path/'profile.json';profile.write_text(json.dumps({'schema':1,'scope':'skills','targets':['kiro'],'slugs':[]}))
    proc=subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/deploy-profile.py'),'--install','--repo',str(ROOT),'--target',str(tmp_path/'target'),'--profile',str(profile),'--cli','all','--dry-run'],capture_output=True,text=True,timeout=30)
    assert proc.returncode == 1 and 'profile cannot combine' in proc.stderr
    assert not (tmp_path/'target').exists()


def test_a14_actual_rollback_interruption_resumes_and_repeat_is_stable(actual_package, monkeypatch):
    target=actual_package
    state=planner.read_state(target)
    rel='.kiro/skills/engos-design-specify-change/resources/fixture-only-stale.txt'
    put(target,rel,b'synthetic owned preimage\n')
    state['packages']['kiro:skill:engos-design-specify-change']['files'][rel]=transaction.identity(target/rel)
    (target/planner.STATE).write_bytes(transaction.encoded(state))
    before={k:v for k,v in snapshot(target).items() if not k.startswith(transaction.TRANSACTIONS+'/')}
    _,result=apply(target,{'mode':'sync','runtime':False})
    original=transaction._replace
    fired=False
    def interrupt(path, *args):
        nonlocal fired
        if Path(path) == target/rel:
            fired=True
            raise OSError('program rollback fixture interrupted')
        return original(path,*args)
    monkeypatch.setattr(transaction,'_replace',interrupt)
    with pytest.raises(Exception,match='program rollback fixture'):
        transaction.rollback(target,result['transaction'])
    assert fired
    monkeypatch.setattr(transaction,'_replace',original)
    transaction.rollback(target,result['transaction'])
    assert {k:v for k,v in snapshot(target).items() if not k.startswith(transaction.TRANSACTIONS+'/')} == before
    again=transaction.rollback(target,result['transaction'])
    assert again['status']=='rolled-back'


RELEASE_DRIVER = r'''
import importlib.util, json, sys
from pathlib import Path
target, mirror = map(Path,sys.argv[1:3])
support=target/'.core-prompts-updater'
spec=importlib.util.spec_from_file_location('installed_update',support/'scripts/update-core-prompts.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
assert Path(module.__file__).resolve() == support/'scripts/update-core-prompts.py'
raise SystemExit(module.accept_profile_release(module.Paths(support_root=support,home=target),json.loads(sys.argv[3]),mirror))
'''


def test_a17_actual_installed_engine_accepts_fixture_only_verified_mirror(tmp_path):
    target=tmp_path/'target';target.mkdir()
    apply(target,{'mode':'install','providers':['kiro'],'slugs':['engos-design-specify-change'],'kinds':['skill'],'selection_policy':'curated'})
    support=target/'.core-prompts-updater'
    # Installed support contains exactly candidate bytes and acts as a local
    # verified mirror; the version label is synthetic acceptance input only.
    version=(support/'VERSION').read_text().strip()
    state={'pending_version':version,'verified_bundle_sha256':hashlib.sha256((support/'.meta/install-bundle.json').read_bytes()).hexdigest()}
    for bad in (dict(state,verified_bundle_sha256='0'*64),dict(state,pending_version='v0.0.0')):
        before=snapshot(target)
        proc=subprocess.run([sys.executable,'-I','-B','-c',RELEASE_DRIVER,str(target),str(support),json.dumps(bad)],capture_output=True,text=True,timeout=90)
        assert proc.returncode == 1 and 'Profile release refused' in proc.stderr
        assert snapshot(target)==before
    proc=subprocess.run([sys.executable,'-I','-B','-c',RELEASE_DRIVER,str(target),str(support),json.dumps(state)],capture_output=True,text=True,timeout=90)
    assert proc.returncode == 0,output(proc)
    saved=planner.read_state(target)
    assert saved['selection_policy']=={'kiro':'curated'} and selected({'selection':saved['selection']})=={'engos-design-specify-change'}
    assert json.loads((target/'.core-prompts-state/release-watch.json').read_text())['status']=='current'


def test_adopt_src001_empty_curated_shared_reader_blocks_full_expansion(tmp_path):
    target=tmp_path/'target';target.mkdir()
    put(target,planner.STATE,transaction.encoded({'schema':3,'owner':'Core-Prompts','selection':[], 'packages':{},'runtime':{}, 'selection_policy':{'gemini':'curated'}}))
    before=snapshot(target)
    request={'mode':'sync','providers':['codex'],'selection_policy':'full_catalog'}
    plan=planner.plan(ROOT,target,request)
    assert plan['shared_exposure']['known_readers']==['codex','gemini']
    assert any('SHARED_SURFACE_POLICY_CONFLICT' in b for b in plan['blockers'])
    with pytest.raises(ValueError,match='unresolved blockers'):
        transaction.apply(ROOT,target,plan,lambda:planner.plan(ROOT,target,request))
    after={k:v for k,v in snapshot(target).items() if k!='.core-prompts-state/installation.lock'}
    assert after==before
    assert planner.read_state(target)['selection_policy']=={'gemini':'curated'}


@pytest.mark.parametrize('clients',[['gemini'],['codex','gemini']])
def test_adopt_src002_actual_saved_shared_provider_membership(donor,tmp_path,clients):
    target=tmp_path/'target';target.mkdir()
    profile={'schema':1,'scope':'skills','targets':clients,'slugs':[],'retire':[]}
    for rel in snapshot(donor):
        put(target,'.core-prompts-updater/'+rel,(donor/rel).read_bytes(),(donor/rel).stat().st_mode&0o777)
    proc=subprocess.run([sys.executable,'-I','-B','-c',DRIVER,str(donor),str(donor),str(target),json.dumps(profile)],cwd=tmp_path,capture_output=True,text=True,timeout=90)
    assert proc.returncode==0,output(proc)
    receipt_path=target/planner.V1_RECEIPT
    receipt_bytes=receipt_path.read_bytes()
    receipt=json.loads(receipt_bytes)
    assert all(r.startswith('.agents/skills/') for r in receipt['skill_scope'])
    assert all(receipt['files'][r]['source'].startswith('.codex/skills/') for r in receipt['skill_scope'])
    before=snapshot(target)
    plan=planner.plan(ROOT,target,{'mode':'sync'})
    assert not plan['blockers']
    assert snapshot(target)==before
    for client in clients:
        assert len(selected(plan,client))==32 and not ADDITIONS&selected(plan,client)
    assert {k.split(':')[0] for k in plan['selection']}==set(clients)
    for policy in ('curated','full_catalog'):
        destination=tmp_path/policy;shutil.copytree(target,destination)
        request={'mode':'repair','profile':profile,'selection_policy':policy}
        # Explicit curated adoption of a saved empty profile freezes its prior
        # proven membership, via single-provider or concrete joint profile.
        if policy=='curated':
            request={'mode':'sync','providers':clients,'selection_policy':policy} if len(clients)==1 else {'mode':'repair','profile':dict(profile,slugs=sorted(selected(plan,'codex'))),'selection_policy':policy}
        updated,result=apply(destination,request)
        assert result['status']=='complete'
        for client in clients:
            assert len(selected(updated,client))==(36 if policy=='full_catalog' else 32)
            assert (ADDITIONS<=selected(updated,client))==(policy=='full_catalog')
        assert (destination/planner.V1_RECEIPT).read_bytes()==receipt_bytes
        assert planner.read_state(destination)['selection_policy']=={p:policy for p in clients}
        detached=detached_call(donor,destination,'--install','--repo',str(destination/'.core-prompts-updater'),'--target',str(destination),'--dry-run')
        assert detached.returncode==0,output(detached)
    # A changed proof cannot be rescued by portable-path mapping.
    first=receipt['skill_scope'][0]
    receipt['files'][first]['identity']['sha256']='0'*64
    receipt_path.write_bytes(transaction.encoded(receipt))
    damaged=snapshot(target)
    with pytest.raises(ValueError,match='LEGACY_MEMBERSHIP_UNPROVEN'):
        planner.plan(ROOT,target,{'mode':'sync'})
    assert snapshot(target)==damaged
