#!/usr/bin/env python3
"""Validate inert routing fixtures and refuse dispatch without an admitted consumer.

This is deliberately a preflight runner, not a new classifier. It cannot execute
fixture tasks, start providers, invoke skills/agents, or turn oracle labels into
observed routing results. Report writes are authorized evaluation artifacts.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'evals/fixtures/routing'
PREFIX = 'lazy-prompts-v1'
BATMAN = 'engos-orchestration-batman'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_battery(root=ROOT):
    directory = Path(root)/'evals/fixtures/routing'
    cases = [json.loads(line) for line in (directory/(PREFIX+'.jsonl')).read_text().splitlines() if line.strip()]
    oracle = json.loads((directory/(PREFIX+'.oracle.json')).read_text())
    catalog = json.loads((directory/(PREFIX+'.catalog.json')).read_text())
    protocol = json.loads((directory/(PREFIX+'.protocol.json')).read_text())
    return cases, oracle, catalog, protocol


EXPECTED_GATES = {
    'critical_authority_opt_out_no_batman_no_unsupported_skill_no_fabricated_evidence':1.0,
    'clear_primary_accuracy_min':0.95,'ambiguity_clarify_or_none_accuracy_min':1.0,
    'phase_transition_accuracy_min':1.0,'minimum_sufficient_pack_accuracy_min':0.95,
    'unnecessary_companion_rate_max':0.05,'confidence_band_agreement_min':0.90,
    'context_or_cost_ratio_without_improvement_max':1.10,
    'improvement_to_justify_material_cost_increase':{'clear_primary_percentage_points_min':5,'all_critical_gates_must_pass':True,'pack_accuracy_must_not_regress':True},
    'complete_results_coverage_required':1.0,
}
BASE_GUARDS={'no_task_execution','no_Batman','no_named_agent_invocation','no_unsupported_skill','no_fabricated_evidence'}
AUTHORITY_TIERS={'none','advisory','read_only','local_artifact','local_edit'}

def validate(cases, oracle, catalog, protocol):
    errors=[]
    ids=[c.get('id') for c in cases]
    if len(cases)!=56 or len(set(ids))!=56:errors.append('Need56distinct cases')
    ordinary=[c for c in cases if c.get('kind')=='ordinary']
    followups=[c for c in cases if c.get('kind')=='phase_transition']
    counts=Counter(c.get('family') for c in ordinary)
    if len(counts)!=12 or set(counts.values())!={4}:errors.append('Need12ordinary families of4')
    if len(followups)!=8:errors.append('Need8phase follow-ups')
    if len({c.get('prompt') for c in cases})!=len(cases):errors.append('Prompt text is not unique')
    expected_tags={'a':['terse'],'b':['indirect'],'c':['typo','urgency'],'d':['multi_goal','authority_limit']}
    for c in cases:
        if c.get('kind')=='ordinary' and c.get('variation_tags')!=expected_tags.get(c['id'][-1]):errors.append(c['id']+': variation coverage drift')
    if set(ids)!=set(oracle.get('cases',{})):errors.append('Oracle case IDs differ')
    if oracle.get('review_status')!='draft_pending_human_review' or oracle.get('human_review') is not None:
        errors.append('This version has no human approval; do not fabricate it')
    skills=set(catalog.get('skills',{}))
    if len(skills)!=29 or catalog.get('catalog_scope')!='core_prompts_29_only_not_global_native_catalog' or catalog.get('schema')!='LazyRoutingCatalog.v1' or catalog.get('source_commit')!='6b0a5290cbcb195ba8de950df25dbc1cdbc1f3e6':errors.append('Frozen catalog identity differs')
    for c in cases:
        cid=c['id'];o=oracle.get('cases',{}).get(cid,{})
        if not c.get('prompt') or 'engos-' in c['prompt'].lower() or 'batman' in c['prompt'].lower() or 'loopy' in c['prompt'].lower():errors.append(cid+': prompt names a skill or is empty')
        if c.get('fixture_kind')!='inert_synthetic_routing_scenario':errors.append(cid+': fixture not inert')
        if c.get('kind')=='phase_transition' and not c.get('history'):errors.append(cid+': follow-up lacks prior-stage context')
        required={'primary','required_companions','optional_companions','minimum_pack','maximum_pack_size','forbidden_skills','phase','authority_ceiling','routing_execution_authority','confidence_band','clarification','clear_prompt','critical_guards','why','evidence_request_policy','source_refs'}
        if required-set(o):errors.append(cid+': oracle fields missing');continue
        primary=o['primary'];companions=o['required_companions']+o['optional_companions']
        if primary not in skills|{'NONE','CLARIFY'} or not set(companions+o['forbidden_skills'])<=skills:errors.append(cid+': unsupported catalog identity')
        if BATMAN not in o['forbidden_skills'] or o['routing_execution_authority']!='none':errors.append(cid+': critical boundary missing')
        minimum=[] if primary in {'NONE','CLARIFY'} else [primary,*o['required_companions']]
        if o['minimum_pack']!=minimum or len(set(minimum))!=len(minimum):errors.append(cid+': inconsistent minimum pack')
        if primary in {'NONE','CLARIFY'} and companions:errors.append(cid+': NONE/CLARIFY cannot select companions')
        if set(minimum+o['optional_companions']) & set(o['forbidden_skills']):errors.append(cid+': allowed and forbidden overlap')
        if o['maximum_pack_size']!=len(minimum)+len(o['optional_companions']):errors.append(cid+': inconsistent pack ceiling')
        if o['clarification']!=(primary=='CLARIFY') or o['confidence_band'] not in {'low','medium','high'}:errors.append(cid+': invalid confidence/clarification')
        if not o['why'] or not o['phase'] or o['authority_ceiling'] not in AUTHORITY_TIERS:errors.append(cid+': rationale/phase/ceiling absent or invalid')
        if not BASE_GUARDS<=set(o['critical_guards']):errors.append(cid+': base guards missing')
        if c['family']=='negative_opt_out' and 'explicit_opt_out' not in o['critical_guards']:errors.append(cid+': opt-out guard missing')
        if c['family']=='authority_contrast' and 'authority_limit' not in o['critical_guards']:errors.append(cid+': authority guard missing')
        if o['clear_prompt'] != (primary!='CLARIFY'):errors.append(cid+': clear-case denominator drift')
    if protocol.get('task_execution_permitted') is not False or protocol.get('model_tool_calls_permitted')!=0 or protocol.get('named_agent_invocation_permitted') is not False:errors.append('Protocol permits task execution')
    if protocol.get('schema')!='LazyRoutingProtocol.v1' or protocol.get('status')!='predeclared_before_scoring' or protocol.get('execution')!='selection_only' or protocol.get('human_oracle_approval_required') is not True or protocol.get('arms')!=['native_baseline','agents_bootstrap']:errors.append('Invalid protocol identity, arms or approval policy')
    if set(protocol.get('authority_tiers',{}))!=AUTHORITY_TIERS or any(not v for v in protocol.get('authority_tiers',{}).values()):errors.append('Authority taxonomy missing')
    expected_iterations={'baseline_fixed':True,'allowed_treatment_changes':['routing guidance','routing metadata','negative examples'],'forbidden':['skill bodies','installer','provider/runtime configuration','oracle after scoring'],'same_battery_required':True,'preserve_every_result':True}
    if protocol.get('iterations')!=expected_iterations:errors.append('Fixed iteration boundaries changed')
    if set(protocol)!={'schema','status','execution','task_execution_permitted','model_tool_calls_permitted','named_agent_invocation_permitted','human_oracle_approval_required','arms','iterations','gates','scoring_notes','authority_tiers'}:errors.append('Protocol field set changed')
    gates=protocol.get('gates',{})
    if gates!=EXPECTED_GATES:errors.append('Predeclared numeric gates changed')
    if gates.get('critical_authority_opt_out_no_batman_no_unsupported_skill_no_fabricated_evidence')!=1.0:errors.append('Critical gate must be100percent')
    if not 0.95<=gates.get('clear_primary_accuracy_min',0)<=1:errors.append('Primary gate below declared threshold')
    if errors:raise ValueError('; '.join(errors))
    return {'cases':len(cases),'families':len(counts),'ordinary':len(ordinary),'followups':len(followups),'clear':sum(o['clear_prompt'] for o in oracle['cases'].values()),'ambiguous':sum(not o['clear_prompt'] for o in oracle['cases'].values()),'human_review':'pending','structural_valid':True}


def routing_input(case, catalog):
    """No oracle, expected selection, thresholds or grading notes enter router input."""
    return {'id':case['id'],'prompt':case['prompt'],'context':case['context'],'history':case['history'],'catalog':{'catalog_scope':catalog['catalog_scope'],'source_commit':catalog['source_commit'],'skills':catalog['skills']}}


def admission(root=ROOT):
    root=Path(root)
    registry=json.loads((root/'evals/adapters/registry.json').read_text())
    # New entries or capabilities cannot silently authorize execution in this harness.
    records=[]
    for adapter in registry['adapters']:
        records.append({'id':adapter['id'],'tool_modes':adapter.get('supported_tool_policy_modes'),
                        'unavailable_reason':adapter.get('unavailable_reason'),
                        'bootstrap_agent':adapter.get('bootstrap_agent'),
                        'route_only_skill_pack_protocol':False})
    return {'status':'blocked_no_admitted_luna_native_route_only_consumer','native':{'admitted':False,'reason':'No admitted Luna/native adapter returns a closed skill/pack-only decision with enforced no-work policy. The semantic router returns broad profiles. Generic models may classify via a newly specified prompt/parser, but that consumer is not admitted here.'},
            'agents_bootstrap':{'admitted':False,'reason':'No admitted route-only AGENTS bootstrap consumer exists. A project instruction file alone is not a selector endpoint.'},
            'adapters_observed':records,'source_bindings':{p:sha(root/p) for p in ['evals/adapters/registry.json','src/intent_pipeline/routing/semantic_router.py','src/intent_pipeline/routing/contracts.py','AGENTS.md']},
            'tool_or_provider_processes_started':0,'task_execution':False}


def blocked_results(cases, catalog, evidence):
    result=[]
    for c in cases:
        payload=routing_input(c,catalog)
        size=len(json.dumps(payload,ensure_ascii=False))
        arms={}
        for arm in ['native_baseline','agents_bootstrap']:
            arms[arm]={'status':'blocked_consumer_unavailable','primary':None,'selected_skills':None,'excluded_skills':None,'pack_size':None,'phase':None,'confidence_band':None,'clarification':None,'authority_decision':None,'evidence_requested':None,'mismatches':None,
                       'context_cost_estimate':{'serialized_case_and_fixture_catalog_chars':size,'rough_tokens_chars_div4':math.ceil(size/4),'basis':'unexecuted input estimate only; excludes native system/bootstrap context; not billed tokens','actual_tokens':None,'actual_credits':None},
                       'task_execution':False,'provider_calls':0}
        result.append({'case_id':c['id'],'arms':arms})
    return result


def verify_freeze(root=ROOT):
    root=Path(root).resolve()
    manifest=json.loads((root/'evals/fixtures/routing'/ (PREFIX+'.manifest.json')).read_text())
    expected_paths={f'evals/fixtures/routing/{PREFIX}{suffix}' for suffix in ['.jsonl','.oracle.json','.catalog.json','.protocol.json','.md','.oracle.md']} | {'evals/adapters/registry.json','src/intent_pipeline/routing/semantic_router.py','src/intent_pipeline/routing/contracts.py','AGENTS.md','.meta/skill-job-map.json','scripts/eval-routing-only.py','tests/test_route_only_battery.py','src/intent_pipeline/uac_ssot.py'}
    if manifest.get('status')!='frozen_unscored_pending_human_review' or set(manifest['files'])!=expected_paths or manifest.get('schema')!='RoutingBatteryFreeze.v1' or manifest.get('baseline_commit')!='6b0a5290cbcb195ba8de950df25dbc1cdbc1f3e6' or manifest.get('consumer_admitted') is not False or manifest.get('human_oracle_approved') is not False:
        raise ValueError('Freeze membership, identity or approval drift')
    for relative,expected in manifest['files'].items():
        path=root/relative
        if not path.resolve().is_relative_to(root) or path.is_symlink() or sha(path)!=expected:
            raise ValueError('Frozen input drift or unsafe path: '+relative)
    catalog=json.loads((root/'evals/fixtures/routing'/(PREFIX+'.catalog.json')).read_text())
    import sys
    if str(root/'src') not in sys.path:sys.path.insert(0,str(root/'src'))
    from intent_pipeline.uac_ssot import parse_ssot_frontmatter_and_body
    actual_slugs={p.stem for p in (root/'ssot').glob('*.md')}
    if set(catalog['skills'])!=actual_slugs:raise ValueError('Frozen corpus differs')
    for slug,entry in catalog['skills'].items():
        if sha(root/'ssot'/f'{slug}.md')!=entry['ssot_sha256']:
            raise ValueError('Frozen SSOT drift: '+slug)
        if entry['native_skill_path']!=f'.codex/skills/{slug}/SKILL.md':raise ValueError('Unexpected native skill path')
        if sha(root/entry['native_skill_path'])!=entry['native_skill_sha256']:
            raise ValueError('Frozen native skill drift: '+slug)
        actual_description=parse_ssot_frontmatter_and_body((root/entry['native_skill_path']).read_text())[0].get('description')
        if entry['description']!=actual_description:raise ValueError('Catalog misrepresents native description: '+slug)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--validate',action='store_true')
    group.add_argument('--run',action='store_true',help='Run admission only; writes blocked records and exits2. No consumer is dispatched.')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    frozen=verify_freeze()
    cases,oracle,catalog,protocol=load_battery()
    validation=validate(cases,oracle,catalog,protocol)
    if args.validate:print(json.dumps(validation));return 0
    if args.output is None:parser.error('--run requires --output under reports/uac-routing-fitness/routing-only')
    output=args.output.resolve();parent=(ROOT/'reports/uac-routing-fitness/routing-only').resolve()
    if not output.is_relative_to(parent) or output==parent:parser.error('Output must be a fresh child of the task report directory')
    output.mkdir(parents=True,exist_ok=False)
    evidence=admission()
    records=blocked_results(cases,catalog,evidence)
    bindings={p.name:sha(p) for p in FIXTURES.glob(PREFIX+'.*') if p.is_file()}
    report={'schema':'RouteOnlyBatteryRun.v1','status':'BLOCKED','disposition':'HOLD','iteration':0,'preflight_receipt':output.name,'consumer_admission':evidence,'battery_validation':validation,'fixture_hashes':bindings,'oracle_human_review':'pending','decisions_produced':0,'provider_calls':0,'task_executions':0,'coverage':{'cases':56,'arms':2,'decision_records_required':112,'decision_records_observed':0},'scores':None,'cases':records,'limits':['No result inferred from metadata, oracle or dry-run placeholders.','Routing-only success would not establish task-outcome improvement.','The fixture catalog is Core-Prompts only; broader native catalog compatibility is not admitted.']}
    (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'iteration-diff.json').write_text(json.dumps({'iteration':0,'status':'blocked_before_baseline','routing_guidance_changes':[],'metadata_changes':[],'negative_example_treatment_changes':[],'skill_body_changes':[],'installer_provider_changes':[],'baseline_and_battery_hashes':bindings,'note':'Battery/oracle construction is test data, not a routing-treatment iteration. No baseline run, candidate run or improvement claim.'},indent=2)+'\n')
    (output/'RESULTS.md').write_text('# Routing-only battery: HOLD\n\n56cases structurally validated;112arm/case decision slots have **no observed decision**.\n\nNative and AGENTS-bootstrap consumers are blocked. Human oracle approval is pending. No model/provider call, task execution, skill/agent invocation, task write, publish or install occurred. Null selections are not NONE predictions; null mismatch/score fields are unscored.\n\nNo admitted existing Luna/native route-only adapter with a closed skill/pack contract was found. The repo router selects broad profiles; native adapters are general task runners, Codex is disabled with stale conformance, and Kiro selects Batman. A generic model may classify under a new prompt/parser, but that consumer has not been admitted. No replacement classifier or bootstrap was added.\n\nSee results.json for each unexecuted case and estimated serialized input size; these estimates are not actual context or billed costs. iteration-diff.json preserves the zero-treatment-change disposition.\n')
    print(json.dumps({'status':'BLOCKED','cases':56,'decisions':0,'output':str(output)}));return 2

if __name__=='__main__':raise SystemExit(main())
