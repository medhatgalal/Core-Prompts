"""Behavioral installation checks against disposable targets and trusted fixtures."""
import base64
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from core_install import planner, transaction
from core_install import providers, catalog
import install_bundle


def put(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data.encode() if isinstance(data, str) else data)
    target.chmod(0o644)
    return target


@pytest.fixture
def installation(tmp_path):
    repo, target = tmp_path / 'source', tmp_path / 'target'
    repo.mkdir(); target.mkdir()
    slug = 'engos-design-architecture'
    members = {}
    entries = []
    for provider in ('kiro', 'codex', 'gemini'):
        kind = provider + '_skill'
        path = f'.{provider}/skills/{slug}/SKILL.md'
        put(repo, path, 'current skill\n')
        members[kind] = []
        ext = {'kiro': 'json', 'codex': 'toml', 'gemini': 'md'}[provider]
        agent = f'.{provider}/agents/{slug}.{ext}'
        put(repo, agent, '{"name":"engos-design-architecture","resources":[]}' if provider == 'kiro' else 'current agent\n')
    manifest = {'ssot_sources': [{'slug': slug, 'expected_surface_names': [f'{p}_{k}' for p in ('kiro', 'codex', 'gemini') for k in ('skill', 'agent')]}], 'resources': members}
    put(repo, '.meta/manifest.json', json.dumps(manifest))
    for rel in ('VERSION', 'scripts/deploy-profile.py', 'scripts/update-core-prompts.py'):
        put(repo, rel, 'new runtime\n')
    identities, packages = {}, []
    for provider in ('kiro', 'codex', 'gemini'):
        for old, successor in [('architecture', slug), ('mentor', None)]:
            for kind in ('skill', 'agent'):
                ext = {'kiro': 'json', 'codex': 'toml', 'gemini': 'md'}[provider]
                rel = f'.{provider}/skills/{old}/SKILL.md' if kind == 'skill' else f'.{provider}/agents/{old}.{ext}'
                token = f'{provider}-{old}-{kind}'
                data = ('{"name":"'+old+'","resources":[]}') if provider == 'kiro' and kind == 'agent' else token + '\n'
                identities[token] = {'sha256': hashlib.sha256(data.encode()).hexdigest(), 'mode': 0o644}
                roots = [str(Path(rel).parent)] if kind == 'skill' else [rel, f'.{provider}/agents/resources/{old}']
                packages.append(dict(provider=provider,kind=kind,slug=old,successor=catalog.successor(provider,kind,old),roots=roots,files={rel:token},releases=['v1.12.2']))
    trusted_catalog = dict(schema=1,releases={'v1.12.2':{'commit':'a'*40,'tag_object':'a'*40}},identities=identities,packages=packages,runtime={},launchers={})
    put(repo, '.meta/install-profiles/legacy-installations.json',json.dumps(trusted_catalog))
    install_bundle.build(repo)
    return repo,target


def execute(repo, target, **request):
    plan = planner.plan(repo, target, request)
    return transaction.apply(repo, target, plan, lambda: planner.plan(repo, target, request))


def test_receiptless_kiro_repair_then_two_updates_preserve_surface_scope(installation):
    repo,target=installation
    put(target,'.kiro/skills/architecture/SKILL.md','kiro-architecture-skill\n')
    request={'providers':['kiro','codex','gemini'],'mode':'repair'}
    result=execute(repo,target,**request)
    assert (target/'.kiro/skills/engos-design-architecture/SKILL.md').read_text()=='current skill\n'
    assert not (target/'.kiro/skills/architecture/SKILL.md').exists()
    assert not (target/'.kiro/agents/engos-design-architecture.json').exists()
    assert not (target/'.agents/skills/engos-design-architecture/SKILL.md').exists()
    for _ in range(2):
        execute(repo,target,mode='sync')
    assert not (target/'.gemini').exists()
    assert not (target/'.kiro/agents').exists()
    assert (target/'update_core_prompts.sh').is_file()
    assert (target/'.core-prompts-state/installation.json').is_file()


def test_custom_successor_blocks_retirement_and_is_not_overwritten(installation):
    repo,target=installation
    put(target,'.kiro/skills/architecture/SKILL.md','kiro-architecture-skill\n')
    custom=put(target,'.kiro/skills/engos-design-architecture/SKILL.md','my edits\n')
    plan=planner.plan(repo,target,{'providers':['kiro'],'mode':'repair'})
    assert plan['preserved']
    assert not any(a['path'].startswith('.kiro/') for a in plan['actions'])
    execute(repo,target,providers=['kiro'],mode='repair')
    assert custom.read_text()=='my edits\n'
    assert (target/'.kiro/skills/architecture/SKILL.md').is_file()


def test_mentor_registration_survives_when_agent_package_is_custom(installation):
    repo,target=installation
    put(target,'.codex/skills/mentor/SKILL.md','codex-mentor-skill\n')
    put(target,'.codex/agents/mentor.toml','custom agent\n')
    config=put(target,'.codex/config.toml',f'[agents.mentor]\nconfig_file = "{target}/.codex/agents/mentor.toml"\n')
    before=config.read_bytes()
    execute(repo,target,providers=['codex'],mode='repair')
    assert config.read_bytes()==before
    assert (target/'.codex/agents/mentor.toml').read_text()=='custom agent\n'


def test_missing_resources_or_extra_members_preserve_whole_agent(installation):
    repo,target=installation
    put(target,'.kiro/agents/architecture.json','{"name":"architecture","resources":[]}')
    put(target,'.kiro/agents/resources/architecture/custom.txt','local\n')
    plan=planner.plan(repo,target,{'providers':['kiro'],'mode':'repair'})
    assert plan['preserved']
    assert not any(a['path'].startswith('.kiro/agents/') for a in plan['actions'])


def test_rollback_restores_migration_and_removes_only_new_files(installation):
    repo,target=installation
    rel='.kiro/skills/architecture/SKILL.md'
    put(target,rel,'kiro-architecture-skill\n')
    result=execute(repo,target,providers=['kiro'],mode='repair')
    transaction.rollback(target,result['transaction'])
    assert (target/rel).read_text()=='kiro-architecture-skill\n'
    assert not (target/'.kiro/skills/engos-design-architecture/SKILL.md').exists()
    assert not (target/'update_core_prompts.sh').exists()


def test_target_authored_manifest_is_not_an_ownership_receipt(installation):
    repo,target=installation
    rel='.kiro/skills/architecture/SKILL.md'
    put(target,rel,'forged arbitrary content\n')
    put(target,'.core-prompts-updater/'+rel,'forged arbitrary content\n')
    put(target,'.core-prompts-updater/.meta/manifest.json',json.dumps({'surfaces':{'kiro_skill':[rel]}}))
    plan=planner.plan(repo,target,{'providers':['kiro'],'mode':'repair'})
    assert plan['preserved']
    assert not any(a['path']==rel for a in plan['actions'])


def test_repair_preserves_explicit_schema1_skill_selection(installation):
    repo,target=installation
    other='engos-meta-supercharge'; rel=f'.kiro/skills/{other}/SKILL.md'
    put(repo,rel,'selected skill\n'); put(target,rel,'selected skill\n')
    manifest=json.loads((repo/'.meta/manifest.json').read_text())
    manifest['ssot_sources'].append({'slug':other,'expected_surface_names':['kiro_skill']})
    put(repo,'.meta/manifest.json',json.dumps(manifest))
    put(target,'.kiro/skills/architecture/SKILL.md','kiro-architecture-skill\n')
    profile={'schema':1,'scope':'skills','targets':['kiro'],'slugs':[other]}
    put(target,planner.V1_PROFILE,transaction.encoded(profile))
    receipt={'schema':1,'owner':'Core-Prompts','approved_profile_sha256':hashlib.sha256(transaction.encoded(profile)).hexdigest(),'files':{rel:{'identity':transaction.identity(target/rel)}},'bundle_files':{}}
    put(target,planner.V1_RECEIPT,json.dumps(receipt)); install_bundle.build(repo)
    plan=planner.plan(repo,target,{'mode':'repair','providers':['kiro'],'runtime':False})
    assert plan['selection']==[f'kiro:skill:{other}']
    assert not any(a['path'].startswith('.kiro/skills/architecture/') for a in plan['actions'])


def test_custom_skill_resources_block_dependent_agent_migration(installation):
    repo,target=installation
    slug='engos-design-architecture'; skill=f'.kiro/skills/{slug}/SKILL.md'
    put(target,skill,'current skill\n')
    put(target,f'.kiro/skills/{slug}/resources/custom.txt','user customization\n')
    put(target,'.kiro/agents/architecture.json','{"name":"architecture","resources":[]}')
    put(repo,f'.kiro/agents/{slug}.json',json.dumps({'name':slug,'resources':['skill://'+skill]}))
    install_bundle.build(repo)
    plan=planner.plan(repo,target,{'mode':'repair','providers':['kiro'],'runtime':False})
    assert any('dependency' in p['reason'] for p in plan['preserved'])
    assert not any(a['path'].startswith('.kiro/agents/') for a in plan['actions'])


def test_obsolete_resource_is_preserved_when_custom_agent_references_it(installation):
    repo,target=installation
    slug='engos-design-architecture'; resource=f'.kiro/skills/{slug}/resources/runtime.txt'
    put(repo,resource,'old runtime\n')
    manifest=json.loads((repo/'.meta/manifest.json').read_text())
    manifest['resources']['kiro_skill']=[resource]
    put(repo,'.meta/manifest.json',json.dumps(manifest));install_bundle.build(repo)
    execute(repo,target,mode='install',providers=['kiro'],slugs=[slug],runtime=False)
    put(target,'.kiro/agents/custom.json',json.dumps({'name':'custom','resources':['file://'+resource]}))
    manifest['resources']['kiro_skill']=[]
    put(repo,'.meta/manifest.json',json.dumps(manifest));install_bundle.build(repo)
    plan=planner.plan(repo,target,{'mode':'sync','runtime':False})
    assert plan['preserved']
    assert not any(a['path']==resource for a in plan['actions'])


@pytest.mark.parametrize('comment', ['# keep my explanation\n', ''])
def test_registration_comment_never_becomes_owned_deletion_scope(tmp_path, comment):
    slug='engos-design-architecture'; rel=f'.codex/agents/{slug}.toml'
    inline='' if comment else ' # keep my explanation'
    original=f'[agents.{slug}]\n{comment}config_file = "{tmp_path}/{rel}"{inline}\n'.encode()
    updated,owned,conflicts=providers.registration_patch(original,tmp_path,{slug:rel},{},{})
    assert not conflicts and updated==original
    retired,_,conflicts=providers.registration_patch(updated,tmp_path,{}, {slug:rel},owned)
    assert conflicts and retired==original


def test_explicit_slug_does_not_migrate_another_installed_skill(installation):
    repo,target=installation
    other='engos-meta-supercharge';rel=f'.kiro/skills/{other}/SKILL.md'
    put(repo,rel,'selected skill\n')
    manifest=json.loads((repo/'.meta/manifest.json').read_text())
    manifest['ssot_sources'].append({'slug':other,'expected_surface_names':['kiro_skill']})
    put(repo,'.meta/manifest.json',json.dumps(manifest));install_bundle.build(repo)
    put(target,'.kiro/skills/architecture/SKILL.md','kiro-architecture-skill\n')
    plan=planner.plan(repo,target,{'mode':'install','providers':['kiro'],'slugs':[other],'kinds':['skill'],'runtime':False})
    assert plan['selection']==[f'kiro:skill:{other}']
    assert not any('architecture' in a['path'] for a in plan['actions'])


def test_custom_registration_preserves_old_agent_and_its_skill_dependency(installation):
    repo,target=installation
    oldskill='.codex/skills/architecture/SKILL.md'; oldagent='.codex/agents/architecture.toml'
    put(target,oldskill,'codex-architecture-skill\n')
    content=f'prompt = "Read {oldskill}"\n'
    put(target,oldagent,content)
    path=repo/'.meta/install-profiles/legacy-installations.json'
    data=json.loads(path.read_text());data['identities']['codex-architecture-agent']=planner.byte_identity(content.encode())
    put(repo,str(path.relative_to(repo)),json.dumps(data));install_bundle.build(repo)
    config=put(target,'.codex/config.toml',f'[agents.architecture]\nconfig_file = "{target}/{oldagent}"\ncustom = true\n')
    before=config.read_bytes()
    plan=planner.plan(repo,target,{'mode':'repair','providers':['codex'],'runtime':False})
    assert plan['preserved']
    assert not any(a['path'] in [oldagent,oldskill,'.codex/config.toml'] for a in plan['actions'])
    assert config.read_bytes()==before


@pytest.mark.parametrize('value',[{},None,[],{'schema':99},
    {'schema':1,'scope':'skills','targets':['kiro'],'slugs':{}},
    {'schema':1,'scope':'skills','targets':['kiro'],'slugs':''}])
def test_malformed_profile_never_falls_back_to_install_everything(installation,value):
    repo,target=installation
    with pytest.raises(ValueError,match='PROFILE'):
        planner.plan(repo,target,{'mode':'repair','providers':['kiro'],'profile':value})
    put(target,planner.V1_PROFILE,json.dumps(value))
    with pytest.raises(ValueError,match='PROFILE'):
        planner.plan(repo,target,{'mode':'sync','providers':['kiro']})
    assert not (target/'.kiro').exists()


@pytest.mark.parametrize('uri',[
    'file://.kiro/skills/architecture/**',
    'file://.kiro/skills/architecture/**/*.md',
    'file://../skills/architecture/**',
    'file://~/.kiro/skills/architecture',
    'skill://.kiro/skills/architecture/*',
])
def test_custom_agent_glob_and_directory_dependencies_preserve_legacy(installation,uri):
    repo,target=installation
    old='.kiro/skills/architecture/SKILL.md'
    put(target,old,'kiro-architecture-skill\n')
    put(target,'.kiro/agents/custom.json',json.dumps({'name':'custom','resources':[uri]}))
    plan=planner.plan(repo,target,{'mode':'repair','providers':['kiro'],'runtime':False})
    assert plan['preserved']
    assert not any(a['path']==old for a in plan['actions'])


def test_release_polling_retains_preserved_installation_attention(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('updater_attention',ROOT/'scripts/update-core-prompts.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    put(tmp_path,planner.STATE,json.dumps({'schema':2,'preserved':[{'reason':'custom agent'}]}))
    paths=module.Paths(support_root=tmp_path/'.core-prompts-updater',home=tmp_path)
    state=module.write_state(paths,installed_version='v1.14.1',latest_version='v1.14.1',pending_version='',status='current',note='version matches')
    assert state['status']=='attention-required'
    assert state['installation_status']=='attention-required'
    put(tmp_path,planner.STATE,json.dumps({'schema':2,'preserved':[]}))
    state=module.write_state(paths,installed_version='v1.14.1',latest_version='v1.14.1',pending_version='',status='current',note='version matches')
    assert state['status']=='current'


def test_legacy_profile_writer_refuses_newer_installation(installation):
    import importlib.util
    repo,target=installation
    execute(repo,target,mode='install',providers=['kiro'],runtime=False)
    spec=importlib.util.spec_from_file_location('legacy_guard',ROOT/'scripts/core_install/profile_v1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with pytest.raises(ValueError,match='newer installation'):
        module.plan(repo,target,{'schema':1,'scope':'skills','targets':['kiro']},routine=True)
    with pytest.raises(ValueError,match='newer installation'):
        module.apply(repo,target,{}, {})


def test_unselected_provider_dependency_blocks_selected_retirement(installation):
    repo,target=installation;old='.kiro/skills/architecture/SKILL.md'
    put(target,old,'kiro-architecture-skill\n')
    put(target,'.codex/agents/custom.toml',f'prompt = "Read file://{old}"\n')
    plan=planner.plan(repo,target,{'mode':'repair','providers':['kiro'],'runtime':False})
    assert plan['preserved']
    assert not any(a['path']==old for a in plan['actions'])


def test_narrow_update_keeps_unresolved_conflicts_outside_its_scope(installation):
    repo,target=installation
    execute(repo,target,mode='install',providers=['kiro','gemini'],runtime=False)
    custom='.kiro/skills/engos-design-architecture/SKILL.md'
    put(target,custom,'my edits\n')
    execute(repo,target,mode='sync',runtime=False)
    before=planner.read_state(target)['preserved']
    assert before
    result=execute(repo,target,mode='install',providers=['gemini'],slugs=['engos-design-architecture'],runtime=False)
    assert not result['preserved']
    assert planner.read_state(target)['preserved']==before
    assert (target/custom).read_text()=='my edits\n'


def test_gemini_and_codex_share_one_tree_with_scoped_updates(installation):
    repo, target = installation
    slug = 'engos-design-architecture'
    shared = f'.agents/skills/{slug}/SKILL.md'
    put(target, '.gemini/settings.json', '{"custom":true}')
    execute(repo, target, mode='install', providers=['codex', 'gemini'], kinds=['skill'], runtime=False)
    assert (target / shared).read_text() == 'current skill\n'
    assert not (target / '.gemini/skills').exists()
    assert (target / '.gemini/settings.json').read_text() == '{"custom":true}'
    for provider in ('codex', 'gemini'):
        put(repo, f'.{provider}/skills/{slug}/SKILL.md', 'updated shared skill\n')
    install_bundle.build(repo)
    execute(repo, target, mode='sync', providers=['gemini'], runtime=False)
    state = json.loads((target / planner.STATE).read_text())
    assert state['packages'][f'codex:skill:{slug}']['files'] == state['packages'][f'gemini:skill:{slug}']['files']
    again = planner.plan(repo, target, dict(mode='sync', providers=['codex'], runtime=False))
    assert not again['preserved'] and not again['blockers'] and not again['actions']


def test_gemini_migrates_receipt_owned_provider_tree_and_rolls_back(installation):
    repo, target = installation
    slug = 'engos-design-architecture'
    old = f'.gemini/skills/{slug}/SKILL.md'
    put(target, old, 'old gemini skill\n')
    key = f'gemini:skill:{slug}'
    put(target, planner.STATE, json.dumps(dict(schema=2, owner='Core-Prompts', selection=[key],
        packages={key: dict(provider='gemini', kind='skill', slug=slug, roots=[str(Path(old).parent)],
                           files={old: transaction.identity(target / old)})}, runtime={}, registrations={})))
    result = execute(repo, target, mode='sync', providers=['gemini'], runtime=False)
    assert not (target / old).exists()
    assert (target / f'.agents/skills/{slug}/SKILL.md').exists()
    transaction.rollback(target, result['transaction'])
    assert (target / old).read_text() == 'old gemini skill\n'
    assert not (target / f'.agents/skills/{slug}/SKILL.md').exists()


def test_custom_shared_skill_blocks_gemini_migration(installation):
    repo, target = installation
    put(target, '.gemini/skills/architecture/SKILL.md', 'gemini-architecture-skill\n')
    shared = '.agents/skills/engos-design-architecture/SKILL.md'
    put(target, shared, 'my customization\n')
    proposal = planner.plan(repo, target, dict(mode='repair', providers=['gemini'], runtime=False))
    assert proposal['preserved']
    assert not any(a['path'].endswith('/SKILL.md') for a in proposal['actions'])


def test_distinct_gemini_behavior_is_not_silently_replaced(installation):
    repo, target = installation
    put(repo, '.gemini/skills/engos-design-architecture/SKILL.md', 'Gemini-only behavior')
    install_bundle.build(repo)
    with pytest.raises(ValueError, match='differs across generated providers'):
        planner.plan(repo, target, dict(mode='install', providers=['gemini'], runtime=False))
    assert not list(target.iterdir())


def test_agy_installs_native_skills_without_recreating_gemini_duplicates(installation):
    repo, target = installation
    slug = 'engos-design-architecture'
    shared = put(target, f'.agents/skills/{slug}/SKILL.md', 'user shared skill\n')
    config = put(target, '.gemini/antigravity-cli/settings.json', '{"permissions":{"ask":["command(*)"]}}')
    before = config.read_bytes()
    result = execute(repo, target, mode='install', providers=['agy'], kinds=['skill'], runtime=False)
    assert (target / f'.gemini/config/skills/{slug}/SKILL.md').read_text() == 'current skill\n'
    assert shared.read_text() == 'user shared skill\n'
    assert config.read_bytes() == before
    assert not (target / '.gemini/skills').exists()
    assert not (target / '.gemini/config/agents').exists()
    assert planner.read_state(target)['selection'] == [f'agy:skill:{slug}']
    assert not planner.plan(repo, target, dict(mode='sync', runtime=False))['actions']
    transaction.rollback(target, result['transaction'])
    assert not (target / f'.gemini/config/skills/{slug}/SKILL.md').exists()
    assert shared.read_text() == 'user shared skill\n' and config.read_bytes() == before


def test_agy_custom_native_package_is_preserved(installation):
    repo, target = installation
    rel = '.gemini/config/skills/engos-design-architecture/SKILL.md'
    put(target, rel, 'custom native skill')
    proposal = planner.plan(repo, target, dict(mode='install', providers=['agy'], kinds=['skill'], runtime=False))
    assert proposal['preserved']
    assert not any(a['path'] == rel for a in proposal['actions'])


def test_agy_does_not_obstruct_native_legacy_migration(installation):
    repo, target = installation
    legacy = put(target, '.gemini/antigravity-cli/skills/custom/SKILL.md', 'legacy user skill')
    with pytest.raises(ValueError, match='AGY_LEGACY_LAYOUT'):
        planner.plan(repo, target, dict(mode='install', providers=['agy'], kinds=['skill'], runtime=False))
    assert legacy.read_text() == 'legacy user skill'
    assert not (target / '.gemini/config').exists()


def test_agy_repairs_catalog_identified_native_copy_without_touching_shared(installation):
    repo, target = installation
    old = put(target, '.gemini/config/skills/architecture/SKILL.md', 'gemini-architecture-skill\n')
    shared = put(target, '.agents/skills/personal/SKILL.md', 'personal')
    execute(repo, target, mode='repair', providers=['agy'], runtime=False)
    assert not old.exists()
    assert (target / '.gemini/config/skills/engos-design-architecture/SKILL.md').read_text() == 'current skill\n'
    assert shared.read_text() == 'personal'


@pytest.mark.parametrize('agent', ['.gemini/config/agents/custom/agent.json', '.gemini/config/plugins/local/agents/custom/agent.json'])
def test_agy_agent_references_preserve_legacy_skill(installation, agent):
    repo, target = installation
    old = '.gemini/config/skills/architecture/SKILL.md'
    put(target, old, 'gemini-architecture-skill\n')
    put(target, agent, json.dumps({'instructions': 'Read ' + old}))
    proposal = planner.plan(repo, target, dict(mode='repair', providers=['agy'], runtime=False))
    assert proposal['preserved']
    assert not any(a['path'] == old for a in proposal['actions'])
