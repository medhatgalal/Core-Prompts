"""Independent state-transition controls; only write a new verification replica."""
import ast
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
REPO = ROOT.parents[2]
CONTROL = ROOT / 'transition-controls'
REPLAY = OUT / 'transition-replay'
HOST = Path('/Users/medhat.galal/.codex/sessions/2026/09/08/rollout-2026-09-08T14-21-47-01a08241-3656-7832-ae51-9d33f361756f.jsonl')
checks = []
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(p.read_bytes())
def read(p): return json.loads(p.read_text())
def save(p, obj): p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
def check(name, condition):
    checks.append({'check': name, 'pass': bool(condition)})
    if not condition: raise AssertionError(name)
def snapshot():
    return {str(p.relative_to(ROOT)): {'sha256': sha(p), 'mode': oct(p.stat().st_mode & 0o777)} for p in sorted(ROOT.rglob('*')) if p.is_file() and OUT not in p.parents}
def score_only(result): return {k: v for k, v in result.items() if k not in ('provenance', 'integrity_after')}
def state_only(state): return {**state, 'score': score_only(state['score'])}

before = snapshot()
initial_review_paths = [OUT / 'independent-review.json', OUT / 'independent-review.md', OUT / 'independent_replay.py']
initial_review_hashes = {p.name: sha(p) for p in initial_review_paths}
manifest = read(ROOT / 'protected/manifest.json')
contract = read(CONTROL / 'control-contract.json')
control_summary = read(CONTROL / 'summary.json')
initial_review = read(OUT / 'independent-review.json')
original_ledger = [json.loads(x) for x in (ROOT / 'ledger.jsonl').read_text().splitlines()]
control_ledger = [json.loads(x) for x in (CONTROL / 'ledger.jsonl').read_text().splitlines()]
seed = read(CONTROL / 'seed-state.json')
check('authorized cwd, HEAD and branch retained', Path.cwd() == REPO and subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip() == manifest['head'] and subprocess.check_output(['git','branch','--show-current'], text=True).strip() == manifest['branch'])
check('runner identical to initial independently reviewed implementation', sha(ROOT / 'run_fixture.py') == contract['implementation_sha256'] == initial_review['runner_sha256'])
check('control seed comes from accepted original scanner', seed['incumbent_sha256'] == sha(ROOT / contract['seed']['source']) == contract['seed']['sha256'] and seed['optimization_trials_completed'] == 0 and seed['score'] == read(ROOT / 'raw/trial-01.json'))
check('control-only declaration and unchanged real trial count', contract['optimization_trials_added'] == control_summary['optimization_trials_added'] == 0 and control_summary['original_optimization_trials'] == len([e for e in original_ledger if e['event'] == 'optimization_trial']) == 3)
check('control wrapper preserved original tracked inputs', control_summary['original_artifacts_hashes_before'] == control_summary['original_artifacts_hashes_after'] and all(sha(ROOT / p) == h for p,h in control_summary['original_artifacts_hashes_after'].items()))
for name, expected in manifest['package_hashes'].items(): check('package: ' + name, sha(REPO / name) == expected)
for name, expected in manifest['frozen_hashes'].items(): check('original and copied protected identity: ' + name, sha(ROOT / name) == sha(CONTROL / name) == expected)
check('control manifest is exact protected manifest copy', sha(CONTROL / 'protected/manifest.json') == sha(ROOT / 'protected/manifest.json'))

# Verify the historical wrapper bytes and actual three trial() outputs.
history = [json.loads(x) for x in HOST.read_text().splitlines()]
calls = {o['payload']['call_id']: (i,o['payload']) for i,o in enumerate(history,1) if o.get('type') == 'response_item' and o.get('payload',{}).get('type') in ('custom_tool_call','function_call')}
host_record = None
for line,obj in enumerate(history,1):
    p=obj.get('payload',{})
    if obj.get('type') != 'response_item' or p.get('type') != 'custom_tool_call_output': continue
    for b in p.get('output',[]):
        text=b.get('text',''); marker='{"chunk_id":"37ca1f"'
        if marker not in text: continue
        tool=json.JSONDecoder().raw_decode(text[text.index(marker):])[0]
        call_line,call=calls[p['call_id']]
        commands=[json.loads(s) for s in re.findall(r'cmd:("(?:[^"\\]|\\.)*")',call.get('input',call.get('arguments','')))]
        wrapper=commands[0].split("<<'PY'\n",1)[1].split('\nPY\n',1)[0] + '\n'
        check('host-called wrapper byte-identical to reviewed wrapper', sha_bytes(wrapper.encode()) == sha(ROOT / 'run_transition_controls.py'))
        check('host actual wrapper process succeeded', tool['exit_code'] == 0)
        pending=tool['output']; objects=[]
        while pending.strip():
            pending=pending.lstrip(); parsed,end=json.JSONDecoder().raw_decode(pending)
            objects.append(parsed); pending=pending[end:]
        check('host actual outputs equal control ledger and summary', objects == control_ledger + [control_summary])
        host_record={'chunk':'37ca1f','call_id':p['call_id'],'call_line':call_line,'output_line':line,'timestamp':obj['timestamp'],'exit_code':tool['exit_code'],'wrapper_sha256':sha_bytes(wrapper.encode()),'tool_output_sha256':sha_bytes(tool['output'].encode())}
check('actual host transition tool record located', host_record is not None)

REPLAY.mkdir(exist_ok=False)
for directory in ['protected','original','incumbent','active','raw','trials']: (REPLAY / directory).mkdir()
for name in manifest['frozen_hashes']:
    target=REPLAY / name; target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT / name,target); target.chmod(0o444)
shutil.copyfile(ROOT / 'protected/manifest.json',REPLAY / 'protected/manifest.json')
(REPLAY / 'protected/manifest.json').chmod(0o444)
shutil.copyfile(ROOT / contract['seed']['source'],REPLAY / 'incumbent/normalize.py')
# Re-execute the seed, rather than trusting its historical cached score.
argv=[sys.executable,'-I','-B',str(REPLAY / 'protected/evaluator.py'),str(REPLAY / 'incumbent/normalize.py')]
proc=subprocess.run(argv,cwd=REPLAY / 'active',capture_output=True,timeout=5)
(REPLAY / 'raw/seed.stdout.txt').write_bytes(proc.stdout)
(REPLAY / 'raw/seed.stderr.txt').write_bytes(proc.stderr)
check('fresh seed execution exactly matches accepted scanner', proc.returncode == 0 and not proc.stderr and json.loads(proc.stdout) == score_only(seed['score']))
replay_seed={**seed,'score':json.loads(proc.stdout)}
save(REPLAY / 'state.json',replay_seed)
save(REPLAY / 'seed-state.json',replay_seed)
spec=importlib.util.spec_from_file_location('independent_unchanged_fixture',ROOT / 'run_fixture.py')
fixture=importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
untouched={'REPO':fixture.REPO,'MANIFEST':fixture.MANIFEST,'CONTRACT':fixture.CONTRACT,'trial_code':fixture.trial.__code__}
fixture.ROOT=REPLAY
check('only runner ROOT context redirected', fixture.REPO == untouched['REPO'] == REPO and fixture.MANIFEST is untouched['MANIFEST'] and fixture.CONTRACT is untouched['CONTRACT'] and fixture.trial.__code__ is untouched['trial_code'])
check('trial code loaded from original unchanged source path', Path(fixture.trial.__code__.co_filename) == ROOT / 'run_fixture.py')

sources=[(ROOT / 'original/normalize.py').read_text(), (ROOT / contract['seed']['source']).read_text() + '\n# Labeled tie control: a comment does not change the AST.\n', (ROOT / 'trials/trial-03/normalize.py').read_text()]
check('tie control changes bytes but has identical AST', sha_bytes(sources[1].encode()) != seed['incumbent_sha256'] and ast.dump(ast.parse(sources[1])) == ast.dump(ast.parse((ROOT / contract['seed']['source']).read_text())))
transitions=[]
parent_id=seed['incumbent_id']; parent_score=replay_seed['score']
for number,source in enumerate(sources,1):
    label=f'trial-{number:02}'; historical=control_ledger[number-1]
    check(label + ': independently constructed control source equals archived control', sha_bytes(source.encode()) == sha(CONTROL / 'trials' / label / 'normalize.py'))
    capture=io.StringIO()
    with contextlib.redirect_stdout(capture): fixture.trial(number,source,'CONTROL ONLY: ' + contract['sequence'][number-1]['label'])
    (REPLAY / 'raw' / f'transition-call-{number}.stdout.txt').write_text(capture.getvalue())
    event=json.loads(capture.getvalue()); result=read(REPLAY / 'raw' / (label + '.json'))
    state=read(REPLAY / 'state.json'); save(REPLAY / f'state-after-control-{number}.json',state)
    old_pass={c['id'] for c in parent_score['cases'] if c['passed']}
    new_pass={c['id'] for c in result['cases'] if c['passed']}
    regressed=sorted(old_pass-new_pass)
    computed=sum(isinstance(c.get('actual'),str) and c['actual']==c['expected'] for c in result['cases'])
    check(label + ': independently recomputed score and AST nodes', result['passed'] == computed and result['ast_nodes'] == sum(1 for _ in ast.walk(ast.parse(source))))
    expected='rejected' if regressed else ('accepted' if result['passed'] > parent_score['passed'] or result['passed'] == parent_score['passed'] and result['ast_nodes'] < parent_score['ast_nodes'] else 'tied')
    check(label + ': actual same-controller decision equals independent derivation', event['decision'] == expected and sorted(event['regressions']) == regressed)
    check(label + ': parent retained through loss and tie', event['parent_incumbent'] == parent_id == seed['incumbent_id'] and event['parent_sha256'] == seed['incumbent_sha256'])
    check(label + ': replay event equals historical event except timestamp', {k:v for k,v in event.items() if k!='at'} == {k:v for k,v in historical.items() if k!='at'})
    check(label + ': original transition-call output equals ledger', read(CONTROL / 'raw' / f'transition-call-{number}.stdout.txt') == historical)
    raw=(REPLAY / 'raw' / (label + '.stdout.txt')).read_bytes()
    check(label + ': identical captured evaluator output and hash', raw == (CONTROL / 'raw' / (label + '.stdout.txt')).read_bytes() and sha_bytes(raw) == result['provenance']['stdout_sha256'])
    check(label + ': original raw score consistent with output', json.loads(raw) == score_only(read(CONTROL / 'raw' / (label + '.json'))))
    check(label + ': process succeeded under original evaluator and limits', result['provenance']['exit_code'] == 0 and result['provenance']['timeout_seconds'] == 5 and result['provenance']['evaluator_sha256'] == manifest['frozen_hashes']['protected/evaluator.py'] and not (REPLAY / 'raw' / (label + '.stderr.txt')).read_bytes() and not (CONTROL / 'raw' / (label + '.stderr.txt')).read_bytes())
    check(label + ': state-after evidence agrees', state_only(state) == state_only(read(CONTROL / f'state-after-control-{number}.json')))
    if expected=='accepted': parent_id=label; parent_score=score_only(result)
    check(label + ': incumbent bytes reflect decision', state['incumbent_sha256'] == sha(REPLAY / 'incumbent/normalize.py') == parent_score['candidate_sha256'] and state['incumbent_id'] == parent_id)
    check(label + ': rejected/tied/accepted active copy disposed, archive retained', not (REPLAY / event['mutation_set'][0]).exists() and (REPLAY / event['candidate_archive']).is_file() and all(read(REPLAY / 'trials' / label / 'disposal.json').values()) and read(REPLAY / 'trials' / label / 'disposal.json') == read(CONTROL / 'trials' / label / 'disposal.json'))
    check(label + ': original fixture unchanged after controller call', before == snapshot())
    transitions.append({'control':number,'decision':expected,'parent':event['parent_incumbent'],'resulting_incumbent':event['resulting_incumbent'],'score':event['score_after'],'regressions':regressed,'candidate_sha256':event['candidate_sha256'],'incumbent_sha256':state['incumbent_sha256']})

check('exact rejected/tied/accepted sequence independently executed', [t['decision'] for t in transitions] == ['rejected','tied','accepted'])
check('control and replay active directories both empty', not list((CONTROL / 'active').iterdir()) and not list((REPLAY / 'active').iterdir()))
check('final original control state equals final snapshot', read(CONTROL / 'state.json') == read(CONTROL / 'state-after-control-3.json'))
check('new replica final incumbent equals existing control result', sha(REPLAY / 'incumbent/normalize.py') == sha(CONTROL / 'incumbent/normalize.py') == sha(ROOT / 'incumbent/normalize.py'))
check('all frozen, replica and package identities still match', all(sha(ROOT / n) == sha(REPLAY / n) == h for n,h in manifest['frozen_hashes'].items()) and all(sha(REPO / n) == h for n,h in manifest['package_hashes'].items()))
check('original fixture and transition evidence unchanged', before == snapshot())
check('initial independent review unchanged', initial_review_hashes == {p.name:sha(p) for p in initial_review_paths})
report={'verdict':'pass' if all(c['pass'] for c in checks) else 'hold','scope':'Independent verification of separately labeled state-transition controls using the unchanged real trial() implementation','formal_promotion':'hold; not requested or established','created_at':datetime.datetime.now(datetime.UTC).isoformat(),'reviewer_task_id':os.environ.get('CODEX_THREAD_ID'),'runtime':sys.version,'runner_sha256':sha(ROOT / 'run_fixture.py'),'wrapper_sha256':sha(ROOT / 'run_transition_controls.py'),'verifier_sha256':sha(Path(__file__)),'control_contract_sha256':sha(CONTROL / 'control-contract.json'),'evaluator_sha256':sha(ROOT / 'protected/evaluator.py'),'checks':checks,'transitions':transitions,'original_optimization_trials':3,'optimization_trials_added':0,'claimed_optimization_gain_added':0,'actual_evaluator_processes':4,'replay_directory':str(REPLAY.relative_to(ROOT)),'historical_provenance':{'host_session':str(HOST),'record':host_record},'seed_execution':{'argv':argv,'exit_code':proc.returncode,'stdout_sha256':sha_bytes(proc.stdout)},'original_fixture_snapshot_before_and_after':before,'initial_review_hashes':initial_review_hashes,'coverage':{'same_trial_function':True,'rejection_retains_parent':True,'tie_retains_parent':True,'rejected_active_candidate_disposed':True,'tied_active_candidate_disposed':True,'archives_retained':True,'later_acceptance_after_loss_and_tie':True},'limits':['These are prescribed negative/tie/positive controls, not three new optimization hypotheses or additional gains.','The original search still had three accepted trials and no losing/tied optimization trial; controls close only its controller-state coverage gap.','Controller invalid-candidate state, timeout/crash recovery, crash-consistent durability and hostile-code isolation remain untested.','No formal promotion, held-out generalization, frontier-model benchmark, statistical or runtime-speed claim is supported.']}
save(OUT / 'independent-transition-review.json',report)
print(json.dumps({'verdict':report['verdict'],'checks':len(checks),'transitions':transitions,'actual_evaluator_processes':4,'optimization_trials_added':0,'original_fixture_unchanged':True,'initial_review_unchanged':True},indent=2))
