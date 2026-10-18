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


# Explicit Claude replacement and reproducible Python cache retirement.
# Kept here so both hosted installer test groups execute these regressions.
import copy
from core_install import transaction as tx


def replacement_put(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o644)
    return path


@pytest.fixture
def replacement(tmp_path):
    repo, target = tmp_path / 'repo', tmp_path / 'home'
    repo.mkdir(); target.mkdir()
    slug = 'engos-design-architecture'
    root = '.claude/skills/' + slug
    replacement_put(repo, root + '/SKILL.md', 'current')
    replacement_put(repo, root + '/resources/new.py', 'new')
    replacement_put(repo, '.meta/manifest.json', json.dumps({'ssot_sources': [dict(slug=slug, expected_surface_names=['claude_skill'])], 'resources': {'claude_skill': [root + '/resources/new.py']}}))
    # Provider resources are discovered from the actual source tree.
    replacement_put(repo, '.meta/install-profiles/legacy-installations.json', json.dumps(dict(schema=1, releases={}, identities={}, packages=[], runtime={}, launchers={})))
    for rel in ('VERSION', 'scripts/deploy-profile.py', 'scripts/update-core-prompts.py'):
        replacement_put(repo, rel, 'fixture')
    install_bundle.build(repo)
    replacement_put(target, root + '/SKILL.md', 'unowned old')
    replacement_put(target, root + '/local.txt', 'old local state')
    replacement_put(target, root + '/resources/new.py', 'new')
    replacement_put(target, '.claude/skills/custom/SKILL.md', 'custom')
    from core_install import replacement as rep
    manifest = dict(schema=1, target=str(target), packages={
        'claude:skill:' + slug: dict(root=root, before=rep.snapshot(target, root), after=rep.snapshot(repo, root))})
    request = dict(mode='replace_unowned', manifest=manifest)
    return repo, target, root, request


def test_complete_replacement_and_rollback(replacement):
    repo, target, root, request = replacement
    before = tx.inventory(target, [root])
    plan = planner.plan(repo, target, request)
    assert not plan['blockers'] and not plan['preserved']
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert tx.inventory(target, [root]) == tx.inventory(repo, [root])
    assert planner.read_state(target)['packages']['claude:skill:engos-design-architecture']['files'] == tx.inventory(repo, [root])
    journal = tx._load(target, result['transaction'])
    backups = {a['path']: tx.identity(target / tx.TRANSACTIONS / result['transaction'] / 'before' / str(i)) for i, a in enumerate(journal['plan']['actions']) if a['before'] and a['path'].startswith(root + '/')}
    assert backups == before  # Includes identical members and local state.
    assert (target / '.claude/skills/custom/SKILL.md').read_text() == 'custom'
    assert not planner.plan(repo, target, dict(mode='sync', providers=['claude'], runtime=False))['preserved']
    tx.rollback(target, result['transaction'])
    assert tx.inventory(target, [root]) == before
    assert planner.read_state(target) is None


@pytest.mark.parametrize('drift', ['content', 'extra', 'symlink', 'directory-mode', 'empty-directory', 'fifo'])
def test_changed_before_image_rejected_without_writes(replacement, drift):
    repo, target, root, request = replacement
    plan = planner.plan(repo, target, request)
    if drift == 'content':
        replacement_put(target, root + '/SKILL.md', 'changed')
    elif drift == 'extra':
        replacement_put(target, root + '/new.txt', 'new')
    elif drift == 'symlink':
        (target / root / 'link').symlink_to(target / '.claude/skills/custom')
    elif drift == 'directory-mode':
        (target / root).chmod(0o700)
    elif drift == 'empty-directory':
        (target / root / 'empty').mkdir()
    else:
        import os
        os.mkfifo(target / root / 'pipe')
    with pytest.raises(ValueError):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert (target / root / 'local.txt').read_text() == 'old local state'
    assert planner.read_state(target) is None


@pytest.mark.parametrize('drift', ['content', 'extra', 'directory-mode', 'empty-directory'])
def test_rollback_preserves_later_edits(replacement, drift):
    repo, target, root, request = replacement
    plan = planner.plan(repo, target, request)
    receipt = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    if drift == 'content':
        replacement_put(target, root + '/SKILL.md', 'later')
    elif drift == 'extra':
        replacement_put(target, root + '/later.txt', 'later')
    elif drift == 'directory-mode':
        (target / root).chmod(0o700)
    else:
        (target / root / 'later').mkdir()
    with pytest.raises(ValueError):
        tx.rollback(target, receipt['transaction'])
    assert not (target / root / 'local.txt').exists()


@pytest.mark.parametrize('bad', ['unlisted', 'source', 'provider', 'owned'])
def test_manifest_refuses_scope_or_source_ambiguity(replacement, bad):
    repo, target, root, request = replacement
    request = copy.deepcopy(request)
    package = request['manifest']['packages']['claude:skill:engos-design-architecture']
    if bad == 'unlisted':
        package['before']['files']['.claude/skills/custom/SKILL.md'] = tx.identity(target / '.claude/skills/custom/SKILL.md')
    elif bad == 'source':
        replacement_put(repo, root + '/SKILL.md', 'different source')
        install_bundle.build(repo)
    elif bad == 'provider':
        request['manifest']['packages']['kiro:skill:engos-design-architecture'] = package
    else:
        replacement_put(target, planner.STATE, json.dumps(dict(schema=2, owner='Core-Prompts', selection=['claude:skill:engos-design-architecture'], packages={'claude:skill:engos-design-architecture': dict(provider='claude', kind='skill', slug='engos-design-architecture', roots=[root], files=tx.inventory(target, [root]))}, runtime={}, registrations={})))
    with pytest.raises(ValueError):
        planner.plan(repo, target, request)


def test_new_source_directory_and_old_empty_directory_are_guarded(replacement):
    repo, target, root, request = replacement
    from core_install import replacement as rep
    # Empty old directories are retained and recorded, not silently deleted.
    (target / root / 'old-empty').mkdir(mode=0o700)
    replacement_put(repo, root + '/nested/deeper/tool.py', 'new tool')
    (repo / root / 'nested').chmod(0o750)
    manifest_path = repo / '.meta/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['resources']['claude_skill'].append(root + '/nested/deeper/tool.py')
    manifest_path.write_text(json.dumps(manifest))
    install_bundle.build(repo)
    record = request['manifest']['packages']['claude:skill:engos-design-architecture']
    record.update(before=rep.snapshot(target, root), after=rep.snapshot(repo, root))
    plan = planner.plan(repo, target, request)
    receipt = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert (target / root / 'nested').stat().st_mode & 0o777 == 0o750
    assert (target / root / 'old-empty').stat().st_mode & 0o777 == 0o700
    tx.rollback(target, receipt['transaction'])
    assert tx.inventory(target, [root]) == record['before']['files']
    assert (target / root / 'nested/deeper').is_dir()
    assert tx.rollback(target, receipt['transaction'])['status'] == 'rolled-back'


def test_failed_apply_is_recoverable_and_restores_unowned_state(replacement, monkeypatch):
    repo, target, root, request = replacement
    plan = planner.plan(repo, target, request)
    replace = tx._replace
    def fail(path, data, mode):
        if path == target / root / 'resources/new.py':
            raise OSError('simulated interrupted install')
        replace(path, data, mode)
    monkeypatch.setattr(tx, '_replace', fail)
    with pytest.raises(tx.InstallError) as error:
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    monkeypatch.setattr(tx, '_replace', replace)
    tx.rollback(target, error.value.transaction)
    assert (target / root / 'SKILL.md').read_text() == 'unowned old'
    assert planner.read_state(target) is None


def test_concurrent_extra_blocks_ownership_commit(replacement, monkeypatch):
    repo, target, root, request = replacement
    plan = planner.plan(repo, target, request)
    replace = tx._replace
    def concurrent(path, data, mode):
        replace(path, data, mode)
        if path == target / root / 'SKILL.md':
            replacement_put(target, root + '/concurrent.txt', 'retain this')
    monkeypatch.setattr(tx, '_replace', concurrent)
    with pytest.raises(tx.InstallError):
        tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert planner.read_state(target) is None
    assert (target / root / 'concurrent.txt').read_text() == 'retain this'


def test_agent_dependency_blocks_replacement(replacement):
    repo, target, root, request = replacement
    replacement_put(target, '.kiro/agents/custom.json', json.dumps({'resources': ['file://' + str(target / root / 'local.txt')]}))
    with pytest.raises(ValueError, match='depends on removed files'):
        planner.plan(repo, target, request)


def test_unproven_named_cache_is_still_protected_by_ordinary_sync(replacement):
    """A cache-shaped filename alone never authorizes retiring local state."""
    repo, target, root, request = replacement
    plan = planner.plan(repo, target, request)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    cache = replacement_put(target, root + '/resources/__pycache__/new.cpython-314.pyc', 'generated cache')
    sync = planner.plan(repo, target, dict(mode='sync', providers=['claude'], runtime=False))
    assert sync['preserved']
    assert not any(a['path'].startswith(root + '/') for a in sync['actions'])
    assert cache.read_text() == 'generated cache'


def test_saved_plan_cannot_widen_cli_scope(replacement, tmp_path, capsys):
    from core_install import cli
    repo, target, root, request = replacement
    manifest = replacement_put(tmp_path, 'manifest.json', json.dumps(request['manifest']))
    args = ['--repo', str(repo), '--target', str(target), '--replace-unowned', str(manifest)]
    assert cli.main(args) == 1
    assert 'dry-run' in capsys.readouterr().err
    assert cli.main(args + ['--dry-run']) == 0
    plan = json.loads(capsys.readouterr().out)
    saved = replacement_put(tmp_path, 'approved.json', json.dumps(plan))
    assert cli.main(['--repo', str(repo), '--target', str(target), '--apply-plan', str(saved), '--cli', 'kiro']) == 1
    capsys.readouterr()
    assert cli.main(['--repo', str(repo), '--target', str(target), '--apply-plan', str(saved)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert tx._load(target, receipt['transaction'])['schema'] == 3


def test_replacement_journal_cannot_drop_guards(replacement):
    repo, target, root, request = replacement
    plan = planner.plan(repo, target, request)
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    path = target / tx.TRANSACTIONS / result['transaction'] / 'journal.json'
    journal = json.loads(path.read_text())
    journal['schema'] = 1
    path.write_text(json.dumps(journal))
    with pytest.raises(tx.InstallError, match='schema does not match replacement'):
        tx.rollback(target, result['transaction'])


@pytest.mark.parametrize('optimization', [0, 1, 2])
@pytest.mark.parametrize('update_source', [False, True])
def test_real_python_import_then_sync_retires_cache_with_backup(replacement, optimization, update_source):
    import os
    import subprocess
    repo, target, root, request = replacement
    # Make the fixture source importable without side effects.
    replacement_put(repo, root + '/resources/new.py', 'VALUE = 42\n')
    from core_install import replacement as rep
    request['manifest']['packages']['claude:skill:engos-design-architecture']['after'] = rep.snapshot(repo, root)
    install_bundle.build(repo)
    plan = planner.plan(repo, target, request)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    module = target / root / 'resources/new.py'
    code = "import importlib.util; s = importlib.util.spec_from_file_location('probe', " + repr(str(module)) + "); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); assert m.VALUE == 42"
    # Normal interpreter import, no test-only suppression of bytecode.
    env = {k:v for k,v in os.environ.items() if k not in ('PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX', 'PYTHONOPTIMIZE')}
    command = [sys.executable] + (['-' + 'O' * optimization] if optimization else []) + ['-c', code]
    subprocess.run(command, check=True, env=env)
    caches = list((module.parent / '__pycache__').glob('*.pyc'))
    assert len(caches) == 1
    cache_identity = tx.identity(caches[0])
    if update_source:
        replacement_put(repo, root + '/resources/new.py', 'VALUE = 84\n')
        install_bundle.build(repo)
    sync_request = dict(mode='sync', providers=['claude'], runtime=False)
    sync = planner.plan(repo, target, sync_request)
    assert not sync['preserved']
    assert len(sync['cache_retirements']) == 1
    receipt = tx.apply(repo, target, sync, lambda: planner.plan(repo, target, sync_request))
    assert not caches[0].exists()
    assert module.read_text() == ('VALUE = 84\n' if update_source else 'VALUE = 42\n')
    journal = tx._load(target, receipt['transaction'])
    index = next(i for i,a in enumerate(journal['plan']['actions']) if a['path'].endswith('.pyc'))
    assert tx.identity(target / tx.TRANSACTIONS / receipt['transaction'] / 'before' / str(index)) == cache_identity
    tx.rollback(target, receipt['transaction'])
    assert tx.identity(caches[0]) == cache_identity
    assert module.read_text() == 'VALUE = 42\n'


def test_modified_cache_preserves_whole_package(replacement):
    import py_compile
    repo, target, root, request = replacement
    from core_install import replacement as rep
    replacement_put(repo, root + '/resources/new.py', 'VALUE = 42\n')
    request['manifest']['packages']['claude:skill:engos-design-architecture']['after'] = rep.snapshot(repo, root)
    install_bundle.build(repo)
    plan = planner.plan(repo, target, request)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    cache = Path(py_compile.compile(str(target / root / 'resources/new.py'), doraise=True))
    cache.write_bytes(cache.read_bytes() + b'custom payload')
    sync = planner.plan(repo, target, dict(mode='sync', providers=['claude'], runtime=False))
    assert sync['preserved'] and not sync['cache_retirements']
    assert not any(a['path'].startswith(root + '/') for a in sync['actions'])


@pytest.mark.parametrize('failure', ['custom-source', 'custom-sibling', 'cache-link', 'stale-cache', 'unavailable-interpreter', 'changed-after-preview'])
def test_cache_retirement_preserves_unproven_content(replacement, monkeypatch, failure):
    import py_compile
    from core_install import replacement as rep, python_cache
    repo, target, root, request = replacement
    source = replacement_put(repo, root + '/resources/new.py', 'VALUE = 42\n')
    request['manifest']['packages']['claude:skill:engos-design-architecture']['after'] = rep.snapshot(repo, root)
    install_bundle.build(repo)
    plan = planner.plan(repo, target, request)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    source = target / root / 'resources/new.py'
    cache = Path(py_compile.compile(str(source), doraise=True))
    request = dict(mode='sync', providers=['claude'], runtime=False)
    approved = planner.plan(repo, target, request)
    assert approved['cache_retirements']
    if failure == 'custom-source':
        source.write_text('VALUE = 99\n')
    elif failure == 'custom-sibling':
        replacement_put(target, root + '/resources/notes.txt', 'custom')
    elif failure == 'cache-link':
        cache.unlink()
        cache.symlink_to(source)
    elif failure == 'stale-cache':
        cache.write_bytes(b'\0' * 4 + cache.read_bytes()[4:])
    elif failure == 'unavailable-interpreter':
        monkeypatch.setattr(python_cache.subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(OSError('missing interpreter')))
    else:
        cache.write_bytes(cache.read_bytes() + b'later edit')
        with pytest.raises(ValueError):
            tx.apply(repo, target, approved, lambda: planner.plan(repo, target, request))
        assert cache.read_bytes().endswith(b'later edit')
        return
    rejected = planner.plan(repo, target, request)
    assert rejected['preserved'] and not rejected['cache_retirements']
    assert not any(a['path'].startswith(root + '/') for a in rejected['actions'])


@pytest.mark.parametrize('mode', ['CHECKED_HASH', 'UNCHECKED_HASH'])
def test_hash_based_python_cache_retirement(replacement, mode):
    import py_compile
    from core_install import replacement as rep
    repo, target, root, request = replacement
    replacement_put(repo, root + '/resources/new.py', 'VALUE = 42\n')
    request['manifest']['packages']['claude:skill:engos-design-architecture']['after'] = rep.snapshot(repo, root)
    install_bundle.build(repo)
    plan = planner.plan(repo, target, request)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    py_compile.compile(str(target / root / 'resources/new.py'), doraise=True,
                       invalidation_mode=getattr(py_compile.PycInvalidationMode, mode))
    sync = planner.plan(repo, target, dict(mode='sync', providers=['claude'], runtime=False))
    assert not sync['preserved'] and len(sync['cache_retirements']) == 1


def test_reverse_rollback_coexists_with_retained_missing_recovery_journals(replacement):
    repo, target, root, request = replacement
    manifest = json.loads((repo / '.meta/manifest.json').read_text())
    manifest['ssot_sources'][0]['expected_surface_names'].append('grok_skill')
    replacement_put(repo, '.meta/manifest.json', json.dumps(manifest))
    grok = '.grok/skills/engos-design-architecture'
    replacement_put(repo, grok + '/SKILL.md', 'grok current')
    install_bundle.build(repo)
    package = planner.providers.current_packages(repo, manifest, tx.identity, tx.safe)['grok:skill:engos-design-architecture']
    state = dict(schema=2, owner='Core-Prompts', selection=['grok:skill:engos-design-architecture'], packages={'grok:skill:engos-design-architecture': {f: package[f] for f in ('provider', 'kind', 'slug', 'roots', 'files')}}, runtime={}, registrations={})
    state_path = replacement_put(target, planner.STATE, json.dumps(state))
    state_path.chmod(0o600)
    (target / '.grok/skills').mkdir(parents=True)
    before = tx.identity(state_path)
    recover_request = dict(mode='recover_missing', providers=['grok'], kinds=['skill'], slugs=['engos-design-architecture'], runtime=False)
    recover_plan = planner.plan(repo, target, recover_request)
    recovered = tx.apply(repo, target, recover_plan, lambda: planner.plan(repo, target, recover_request))
    plan = planner.plan(repo, target, request)
    adopted = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert tx.identity(state_path)['mode'] == 0o600
    tx.rollback(target, adopted['transaction'])
    tx.rollback(target, recovered['transaction'])
    assert tx.identity(state_path) == before
    assert not (target / grok).exists()


def test_exact_25_package_manifest_replaces_only_listed_roots(replacement):
    from core_install import replacement as rep
    repo, target, root, request = replacement
    manifest = json.loads((repo / '.meta/manifest.json').read_text())
    for number in range(24):
        slug = f'engos-adoption-fixture-{number:02}'
        package_root = '.claude/skills/' + slug
        replacement_put(repo, package_root + '/SKILL.md', 'current ' + slug)
        replacement_put(target, package_root + '/SKILL.md', 'old ' + slug)
        replacement_put(target, package_root + '/local-state.txt', 'retain in backup')
        manifest['ssot_sources'].append(dict(slug=slug, expected_surface_names=['claude_skill']))
        request['manifest']['packages']['claude:skill:' + slug] = dict(root=package_root,
            before=rep.snapshot(target, package_root), after=rep.snapshot(repo, package_root))
    replacement_put(repo, '.meta/manifest.json', json.dumps(manifest))
    install_bundle.build(repo)
    roots = [p['root'] for p in request['manifest']['packages'].values()]
    before = tx.inventory(target, roots)
    plan = planner.plan(repo, target, request)
    assert len(plan['replacement_packages']) == 25
    assert all(a['path'] == tx.INSTALLATION or any(a['path'].startswith(r + '/') for r in roots) for a in plan['actions'])
    result = tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    assert tx.inventory(target, roots) == tx.inventory(repo, roots)
    assert len(planner.read_state(target)['packages']) == 25
    assert (target / '.claude/skills/custom/SKILL.md').read_text() == 'custom'
    tx.rollback(target, result['transaction'])
    assert tx.inventory(target, roots) == before


def test_portable_shell_capsule_replacement_roundtrip(replacement, tmp_path):
    import os
    import subprocess
    repo, target, root, request = replacement
    for name in ('deploy-profile.py', 'deploy-surfaces.sh', 'install-local.sh', 'install_bundle.py'):
        path = repo / 'scripts' / name
        path.write_bytes((ROOT / 'scripts' / name).read_bytes())
        path.chmod(0o755)
    install_bundle.build(repo)
    manifest = replacement_put(tmp_path, 'approved-manifest.json', json.dumps(request['manifest']))
    command = [str(repo / 'scripts/install-local.sh'), '--target', str(target), '--allow-nonlocal-target']
    env = dict(os.environ, PYTHON_BIN=sys.executable)
    preview = subprocess.run(command + ['--replace-unowned', str(manifest), '--dry-run'], check=True, capture_output=True, text=True, env=env)
    plan = replacement_put(tmp_path, 'approved-plan.json', preview.stdout)
    applied = subprocess.run(command + ['--apply-plan', str(plan)], check=True, capture_output=True, text=True, env=env)
    receipt = json.loads(applied.stdout)
    assert tx.inventory(target, [root]) == tx.inventory(repo, [root])
    subprocess.run(command + ['--rollback', receipt['transaction']], check=True, capture_output=True, text=True, env=env)
    assert (target / root / 'SKILL.md').read_text() == 'unowned old'


@pytest.mark.parametrize('when', ['after-replan', 'before-retirement', 'before-ownership'])
def test_cache_source_drift_never_commits_retirement(replacement, monkeypatch, when):
    import py_compile
    from core_install import replacement as rep
    repo, target, root, request = replacement
    replacement_put(repo, root + '/resources/new.py', 'VALUE = 42\n')
    request['manifest']['packages']['claude:skill:engos-design-architecture']['after'] = rep.snapshot(repo, root)
    install_bundle.build(repo)
    plan = planner.plan(repo, target, request)
    tx.apply(repo, target, plan, lambda: planner.plan(repo, target, request))
    # Establish ordinary sync metadata first, so unchanged-source cases have
    # ONLY the cache removal action and no ownership write to hide behind.
    stable_request = dict(mode='sync', providers=['claude'], runtime=False)
    stable = planner.plan(repo, target, stable_request)
    tx.apply(repo, target, stable, lambda: planner.plan(repo, target, stable_request))
    source = target / root / 'resources/new.py'
    cache = Path(py_compile.compile(str(source), doraise=True))
    if when == 'before-retirement':
        # A legitimate package write precedes retirement; source drift during
        # that write must also be caught by the package guard.
        replacement_put(repo, root + '/SKILL.md', 'updated source entrypoint')
        install_bundle.build(repo)
    sync_request = dict(mode='sync', providers=['claude'], runtime=False)
    approved = planner.plan(repo, target, sync_request)
    if when != 'before-retirement':
        assert [a['path'] for a in approved['actions']] == [str(cache.relative_to(target))]
    state_before = (target / planner.STATE).read_bytes()
    def replan():
        refreshed = planner.plan(repo, target, sync_request)
        if when == 'after-replan':
            source.write_text('VALUE = 99\n')
        return refreshed
    original_replace, original_remove = tx._replace, tx._remove
    def replace(path, data, mode):
        original_replace(path, data, mode)
        if when == 'before-retirement' and path == target / root / 'SKILL.md':
            source.write_text('VALUE = 99\n')
    def remove(path):
        original_remove(path)
        if when == 'before-ownership' and path == cache:
            source.write_text('VALUE = 99\n')
    monkeypatch.setattr(tx, '_replace', replace)
    monkeypatch.setattr(tx, '_remove', remove)
    with pytest.raises(tx.InstallError):
        tx.apply(repo, target, approved, replan)
    assert source.read_text() == 'VALUE = 99\n'
    assert (target / planner.STATE).read_bytes() == state_before
    if when != 'before-ownership':
        assert cache.exists()


@pytest.mark.parametrize('link_path', [
    '.kiro/agents/hidden',
    '.gemini/config/agents/nested/hidden',
    '.gemini/config/plugins/custom/agents/hidden',
    '.gemini/config/plugins/linked-plugin',
    '.claude/agents',
    '.gemini/config',
])
def test_replacement_refuses_hidden_agent_directory_symlinks(replacement, link_path):
    repo, target, root, request = replacement
    external = target.parent / 'preserved-agent-target'
    # A hidden preserved agent depends on an extra file that adoption would remove.
    hidden = replacement_put(external, 'agents/custom.json', json.dumps({
        'resources': ['file://' + str(target / root / 'local.txt')]}))
    destination = external if link_path.endswith(('linked-plugin', '/config')) else hidden.parent
    link = target / link_path
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(destination, target_is_directory=True)
    before = tx.inventory(target, [root])
    hidden_before = hidden.read_bytes()
    with pytest.raises(ValueError, match='symlink'):
        planner.plan(repo, target, request)
    assert tx.inventory(target, [root]) == before
    assert (target / root / 'local.txt').read_text() == 'old local state'
    assert hidden.read_bytes() == hidden_before
    assert link.is_symlink()
    assert not (target / tx.STATE).exists()
