"""Surface retirement preserves skill identities and uses journaled ownership."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from core_install import catalog, planner, transaction
import install_bundle

SLUG = 'engos-design-architecture'
EXT = {'codex': 'toml', 'claude': 'md', 'gemini': 'md', 'kiro': 'json'}


def put(root, rel, data):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    path.chmod(0o644)
    return path


def fixture(tmp_path, provider, old='architecture', receipt=False):
    repo, target = tmp_path / 'source', tmp_path / 'target'
    repo.mkdir(); target.mkdir()
    skill = f'.{provider}/skills/{SLUG}/SKILL.md'
    put(repo, skill, 'skill survives\n')
    put(repo, 'VERSION', '1.20.0\n')
    for rel in ('scripts/deploy-profile.py', 'scripts/update-core-prompts.py'):
        put(repo, rel, '# fixture\n')
    put(repo, '.meta/manifest.json', json.dumps({'ssot_sources': [dict(slug=SLUG, expected_surface_names=[provider+'_skill'])], 'resources': {}}))
    if provider == 'gemini':
        put(repo, f'.codex/skills/{SLUG}/SKILL.md', 'skill survives\n')
        manifest = json.loads((repo/'.meta/manifest.json').read_text())
        manifest['ssot_sources'][0]['expected_surface_names'].append('codex_skill')
        put(repo, '.meta/manifest.json', json.dumps(manifest))
    agent = f'.{provider}/agents/{old}.{EXT[provider]}'
    resource = f'.{provider}/agents/resources/{old}/guide.md'
    put(target, agent, f'guide: {resource}\n')
    put(target, resource, 'required resource\n')
    files = {r: transaction.identity(target/r) for r in (agent, resource)}
    spec = dict(provider=provider, kind='agent', slug=old, successor=None,
                roots=[agent, str(Path(resource).parent)], files=files)
    package = dict(spec, files={r: str(i) for i,r in enumerate(files)}, releases=['v1.12.2'])
    identities = {str(i): ident for i, ident in enumerate(files.values())}
    put(repo, catalog.CATALOG_PATH, json.dumps(dict(schema=1, releases={'v1.12.2': dict(commit='a'*40, tag_object='a'*40)}, identities=identities, packages=[package], runtime={}, launchers={})))
    key = f'{provider}:agent:{old}'
    if receipt:
        put(target, planner.STATE, transaction.encoded(dict(schema=2, owner='Core-Prompts', selection=[key], packages={key:spec}, runtime={}, registrations={})))
    if provider == 'codex':
        put(target, '.codex/config.toml', f'[agents.{old}]\nconfig_file = "{target}/.codex/agents/{old}.toml"\n')
    install_bundle.build(repo)
    return repo, target, agent, resource, key


def execute(repo, target, request):
    plan = planner.plan(repo, target, request)
    result = transaction.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    return plan, result


@pytest.mark.parametrize('provider', EXT)
@pytest.mark.parametrize('old', ['architecture', SLUG])
@pytest.mark.parametrize('receipt', [False, True])
def test_known_agent_retired_and_rollback_restores(tmp_path, provider, old, receipt):
    repo,target,agent,resource,key = fixture(tmp_path,provider,old,receipt)
    before = (target/agent).read_bytes()
    request = dict(mode='sync' if receipt else 'repair',providers=[provider],runtime=False)
    plan,result = execute(repo,target,request)
    assert not plan['preserved'] and not plan['blockers']
    assert not (target/agent).exists() and not (target/resource).exists()
    state = planner.read_state(target)
    assert key not in state['selection'] and key not in state['packages']
    skill_key = f'{provider}:skill:{SLUG}'
    assert state['selection'] == [skill_key]
    skill_root = '.agents' if provider in ('codex', 'gemini') else f'.{provider}'
    assert (target/f'{skill_root}/skills/{SLUG}/SKILL.md').read_text() == 'skill survives\n'
    again = planner.plan(repo,target,dict(mode='sync',runtime=False))
    assert not again['actions']
    transaction.rollback(target,result['transaction'])
    assert (target/agent).read_bytes() == before
    assert (target/resource).is_file()
    if receipt:
        assert planner.read_state(target)['selection'] == [key]
    assert not (target/f'{skill_root}/skills/{SLUG}/SKILL.md').exists()
    if provider == 'codex':
        assert f'[agents.{old}]' in (target/'.codex/config.toml').read_text()


@pytest.mark.parametrize('change', ['custom', 'extra', 'dependent', 'symlink'])
def test_preserves_custom_or_depended_on_packages(tmp_path, change):
    repo,target,agent,resource,key = fixture(tmp_path,'kiro',SLUG,True)
    if change == 'custom': put(target,agent,'custom\n')
    if change == 'extra': put(target,str(Path(resource).parent/'custom.md'),'extra\n')
    if change == 'dependent': put(target,'.kiro/agents/personal.json',json.dumps({'resources':[resource]}))
    if change == 'symlink':
        (target/resource).unlink()
        (target/resource).symlink_to(target/agent)
    plan = planner.plan(repo,target,dict(mode='sync',runtime=False))
    assert plan['preserved'] or plan['blockers']
    assert not any(a['op']=='remove' for a in plan['actions'])
    assert key in plan['selection']


def test_unknown_removed_selection_still_blocks(tmp_path):
    repo,target,*_ = fixture(tmp_path,'kiro',SLUG,True)
    state = planner.read_state(target)
    state['selection'].append('kiro:agent:personal')
    put(target,planner.STATE,transaction.encoded(state))
    with pytest.raises(ValueError,match='SOURCE_SCOPE_REMOVED'):
        planner.plan(repo,target,dict(mode='sync',runtime=False))


def test_surface_specific_retirement_preserves_skills():
    assert len(catalog.RETIRED_AGENT_SLUGS) == 11
    for provider in EXT:
        for old, successor in catalog.SUCCESSORS.items():
            if successor in catalog.RETIRED_AGENT_SLUGS:
                assert catalog.successor(provider,'agent',old) is None
                assert catalog.successor(provider,'skill',old) == successor


def test_schema1_skills_receipt_does_not_own_agents_but_catalog_does(tmp_path):
    import hashlib
    repo,target,agent,resource,key = fixture(tmp_path,'kiro')
    skill = f'.kiro/skills/{SLUG}/SKILL.md'
    put(target,skill,'skill survives\n')
    profile = dict(schema=1,scope='skills',targets=['kiro'],slugs=[SLUG])
    put(target,planner.V1_PROFILE,transaction.encoded(profile))
    put(target,planner.V1_RECEIPT,transaction.encoded(dict(schema=1,owner='Core-Prompts',
        approved_profile_sha256=hashlib.sha256(transaction.encoded(profile)).hexdigest(),
        files={skill:dict(identity=transaction.identity(target/skill))})))
    plan,_ = execute(repo,target,dict(mode='sync',runtime=False))
    assert not plan['preserved']
    assert not (target/agent).exists()
    assert (target/skill).read_text() == 'skill survives\n'
    assert plan['selection'] == [f'kiro:skill:{SLUG}']


def test_reintroduced_current_agent_supersedes_historical_retirement(tmp_path):
    repo,target,agent,resource,key = fixture(tmp_path,'kiro',SLUG,True)
    put(repo,agent,'{"name":"engos-design-architecture","resources":[]}')
    manifest = json.loads((repo/'.meta/manifest.json').read_text())
    manifest['ssot_sources'][0]['expected_surface_names'].append('kiro_agent')
    put(repo,'.meta/manifest.json',json.dumps(manifest))
    install_bundle.build(repo)
    plan,_ = execute(repo,target,dict(mode='sync',runtime=False))
    assert not plan['preserved']
    assert key in plan['selection']
    assert (target/agent).read_bytes() == (repo/agent).read_bytes()


def test_changed_target_rejects_reviewed_retirement(tmp_path):
    repo,target,agent,resource,key = fixture(tmp_path,'kiro',SLUG,True)
    request = dict(mode='sync',runtime=False)
    plan = planner.plan(repo,target,request)
    put(target,resource,'changed after preview\n')
    with pytest.raises(transaction.InstallError):
        transaction.apply(repo,target,plan,lambda: planner.plan(repo,target,request))
    assert (target/agent).exists()
    assert (target/resource).read_text() == 'changed after preview\n'


def test_custom_skill_counterpart_retains_agent_without_other_enrollment(tmp_path):
    repo,target,agent,resource,key = fixture(tmp_path,'kiro',SLUG,True)
    counterpart = put(target,f'.kiro/skills/{SLUG}/SKILL.md','custom skill\n')
    plan,_ = execute(repo,target,dict(mode='sync',runtime=False))
    assert plan['preserved']
    assert (target/agent).is_file() and (target/resource).is_file()
    assert counterpart.read_text() == 'custom skill\n'
    assert set(plan['selection']) <= {key, f'kiro:skill:{SLUG}'}


def test_unavailable_skill_counterpart_retains_agent(tmp_path):
    repo,target,agent,resource,key = fixture(tmp_path,'kiro',SLUG,True)
    put(repo,'.meta/manifest.json',json.dumps(dict(ssot_sources=[],resources={})))
    install_bundle.build(repo)
    plan,_ = execute(repo,target,dict(mode='sync',runtime=False))
    assert any('no available skill counterpart' in p['reason'] for p in plan['preserved'])
    assert (target/agent).is_file() and plan['selection'] == [key]


def test_agent_migration_does_not_enroll_other_jobs(tmp_path):
    repo,target,agent,resource,key = fixture(tmp_path,'kiro',SLUG,True)
    other = 'engos-meta-supercharge'
    put(repo,f'.kiro/skills/{other}/SKILL.md','unselected\n')
    manifest = json.loads((repo/'.meta/manifest.json').read_text())
    manifest['ssot_sources'].append(dict(slug=other, expected_surface_names=['kiro_skill']))
    put(repo,'.meta/manifest.json',json.dumps(manifest))
    install_bundle.build(repo)
    plan,_ = execute(repo,target,dict(mode='sync',runtime=False,kinds=['agent']))
    assert plan['selection'] == [f'kiro:skill:{SLUG}']
    assert not (target/f'.kiro/skills/{other}/SKILL.md').exists()
    assert not (target/agent).exists()


def identify_core(target, provider, agent, resource):
    """Modified generated package: identity survives while byte hashes differ."""
    if provider == 'kiro':
        body = json.dumps({'name': SLUG, 'prompt': 'locally modified'})
    elif provider == 'codex':
        body = f'name = "{SLUG}"\ndeveloper_instructions = "locally modified"\n'
    else:
        body = f'---\nname: {SLUG}\n---\nlocally modified\n'
    put(target,agent,body)
    descriptor = str(Path(resource).parent/'capability.json')
    put(target,descriptor,json.dumps(dict(slug=SLUG,descriptor_version='CapabilityDescriptor.v1',
                                         expected_surface_names=[provider+'_agent'])))
    return descriptor


@pytest.mark.parametrize('provider', EXT)
@pytest.mark.parametrize('custom_skill', [False, True])
def test_routine_sync_cleans_identified_core_modifications_and_backups(tmp_path,provider,custom_skill):
    repo,target,agent,resource,key = fixture(tmp_path,provider,SLUG,True)
    descriptor=identify_core(target,provider,agent,resource)
    backup=put(target,agent+'.bak.2','old local instructions')
    unrelated=put(target,f'.{provider}/agents/kirocrew.json','{"name":"kirocrew"}')
    skill_root='.agents' if provider in ('codex','gemini') else f'.{provider}'
    skill=f'{skill_root}/skills/{SLUG}/SKILL.md'
    if custom_skill: put(target,skill,'my customized skill')
    before=transaction.inventory(target,[agent,resource,descriptor,agent+'.bak.2'])
    request=dict(mode='sync',runtime=False)
    plan,result=execute(repo,target,request)
    assert not plan['blockers']
    assert not (target/agent).exists() and not backup.exists()
    assert not (target/descriptor).exists() and not (target/resource).exists()
    assert unrelated.read_text()=='{"name":"kirocrew"}'
    assert (target/skill).read_text()==('my customized skill' if custom_skill else 'skill survives\n')
    again=planner.plan(repo,target,request)
    assert not again['actions']
    transaction.rollback(target,result['transaction'])
    assert transaction.inventory(target,[agent,resource,descriptor,agent+'.bak.2'])==before


@pytest.mark.parametrize('case',['wrong_name','wrong_slug','no_agent_surface','dependent','backup_symlink','backup_directory'])
def test_identified_retirement_still_protects_other_owners_and_readers(tmp_path,case):
    repo,target,agent,resource,key=fixture(tmp_path,'kiro',SLUG,True)
    descriptor=identify_core(target,'kiro',agent,resource)
    if case=='wrong_name': put(target,agent,'{"name":"kirocrew"}')
    if case=='wrong_slug': put(target,descriptor,'{"slug":"kirocrew"}')
    if case=='no_agent_surface': put(target,descriptor,json.dumps(dict(slug=SLUG,descriptor_version='1',expected_surface_names=['kiro_skill'])))
    if case=='dependent': put(target,'.kiro/agents/kirocrew.json',json.dumps({'resources':[resource]}))
    if case=='backup_symlink': (target/(agent+'.bak')).symlink_to(target/agent)
    if case=='backup_directory': put(target,agent+'.bak/personal.txt','unrelated')
    plan=planner.plan(repo,target,dict(mode='sync',runtime=False))
    assert plan['preserved'] or plan['blockers']
    assert not any(a['path']==agent and a['op']=='remove' for a in plan['actions'])


def test_added_backup_after_preview_stales_cleanup(tmp_path):
    repo,target,agent,resource,key=fixture(tmp_path,'kiro',SLUG,True)
    identify_core(target,'kiro',agent,resource)
    request=dict(mode='sync',runtime=False)
    plan=planner.plan(repo,target,request)
    put(target,agent+'.bak','new backup')
    with pytest.raises(transaction.InstallError):
        transaction.apply(repo,target,plan,lambda:planner.plan(repo,target,request))
    assert (target/agent).exists()


@pytest.mark.parametrize('release', [False, True])
def test_installed_updater_automatically_cleans_core_agents(tmp_path,release):
    import hashlib
    import subprocess
    target=tmp_path/'home';target.mkdir()
    seed=dict(mode='install',providers=['kiro'],kinds=['skill'],slugs=[SLUG])
    execute(ROOT,target,seed)
    agent=f'.kiro/agents/{SLUG}.json'
    resource=f'.kiro/agents/resources/{SLUG}/guide.md'
    put(target,resource,'old core resource')
    identify_core(target,'kiro',agent,resource)
    crew=put(target,'.kiro/agents/kirocrew.json','{"name":"kirocrew"}')
    script=target/'.core-prompts-updater/scripts/update-core-prompts.py'
    cmd=[sys.executable,str(script),'--target-home',str(target)]
    if release:
        put(target,'.core-prompts-state/release-watch.json',json.dumps(dict(
            status='pending-install',pending_version=(ROOT/'VERSION').read_text().strip(),
            mirror_path=str(ROOT),verified_bundle_sha256=hashlib.sha256((ROOT/'.meta/install-bundle.json').read_bytes()).hexdigest())))
        cmd+=['--accept-release','--yes']
    result=subprocess.run(cmd,cwd=tmp_path,text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    assert not (target/agent).exists() and not (target/resource).exists()
    assert crew.read_text()=='{"name":"kirocrew"}'
    again=subprocess.run([sys.executable,str(script),'--target-home',str(target)],cwd=tmp_path,text=True,capture_output=True,timeout=60)
    assert again.returncode==0,again.stdout+again.stderr
    assert json.loads(again.stdout)['actions']==0


def test_retirement_preserves_both_shared_skill_receipts(tmp_path):
    repo,target,agent,resource,key=fixture(tmp_path,'gemini',SLUG,True)
    identify_core(target,'gemini',agent,resource)
    rel=f'.agents/skills/{SLUG}/SKILL.md'
    put(target,rel,'previous owned skill')
    old_files={rel:transaction.identity(target/rel)}
    state=planner.read_state(target)
    for host in ['codex','gemini']:
        k=f'{host}:skill:{SLUG}'
        state['selection'].append(k)
        state['packages'][k]=dict(provider=host,kind='skill',slug=SLUG,roots=[str(Path(rel).parent)],files=old_files)
    put(target,planner.STATE,transaction.encoded(state))
    put(target,rel,'user customized shared skill')
    request=dict(mode='sync',providers=['gemini'],runtime=False)
    _,result=execute(repo,target,request)
    after=planner.read_state(target)
    for host in ['codex','gemini']:
        assert after['packages'][f'{host}:skill:{SLUG}']==state['packages'][f'{host}:skill:{SLUG}']
    assert (target/rel).read_text()=='user customized shared skill'
    assert not (target/agent).exists()
    assert not planner.plan(repo,target,request)['actions']
