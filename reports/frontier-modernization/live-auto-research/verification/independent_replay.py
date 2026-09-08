"""Read-only fixture replay; only writes files beside this verifier. Never imports runner."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
REPO = ROOT.parents[2]
HOST = Path('/Users/medhat.galal/.codex/sessions/2026/09/08/rollout-2026-09-08T14-21-47-01a08241-3656-7832-ae51-9d33f361756f.jsonl')
checks = []
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(p.read_bytes())
def read(p): return json.loads(p.read_text())
def check(name, condition): checks.append({'check': name, 'pass': bool(condition)})
def save(name, data): (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
def snapshot():
    return {str(p.relative_to(ROOT)): {'sha256': sha(p), 'mode': oct(p.stat().st_mode & 0o777)}
            for p in sorted(ROOT.rglob('*')) if p.is_file() and OUT not in p.parents}

before = snapshot()
manifest = read(ROOT / 'protected/manifest.json')
contract = read(ROOT / 'protected/goal-contract.json')
ledger = [json.loads(x) for x in (ROOT / 'ledger.jsonl').read_text().splitlines()]
state, summary = read(ROOT / 'state.json'), read(ROOT / 'summary.json')
check('cwd and repository match authorized worktree', Path.cwd() == REPO and str(REPO) == manifest['cwd'])
check('runtime matches frozen executable', Path(sys.executable).resolve() == Path(manifest['runtime']).resolve())
check('HEAD matches frozen HEAD', subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip() == manifest['head'])
check('branch matches frozen branch', subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip() == manifest['branch'])
for group, root in [('frozen_hashes', ROOT), ('package_hashes', REPO)]:
    for name, expected in manifest[group].items(): check(f'{group}: {name}', sha(root / name) == expected)

# Parse protected case data without executing the evaluator in this process.
eval_tree = ast.parse((ROOT / 'protected/evaluator.py').read_text())
cases = next(ast.literal_eval(n.value) for n in eval_tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CASES' for t in n.targets))
check('case identifiers unique', len({c[0] for c in cases}) == len(cases))
trials = [e for e in ledger if e['event'] == 'optimization_trial']
check('exactly three optimization trials', len(trials) == contract['budget']['optimization_trials'] == 3)
check('ledger event sequence', [e['event'] for e in ledger] == ['baseline'] + ['optimization_trial'] * 3 + ['negative_controls'])
labels = [('baseline', 'original/normalize.py')]
labels += [(e['trial_id'], e['candidate_archive']) for e in trials]
labels += [('final-baseline', 'original/normalize.py'), ('final-incumbent', 'incumbent/normalize.py'),
           ('negative-control-wrong-output', 'controls/negative-control-wrong-output.py'),
           ('negative-control-invalid-syntax', 'controls/negative-control-invalid-syntax.py')]
replays = {}
for label, relative in labels:
    candidate = ROOT / relative
    argv = [manifest['runtime'], '-I', '-B', str(ROOT / 'protected/evaluator.py'), str(candidate)]
    start = time.monotonic()
    proc = subprocess.run(argv, cwd=OUT, capture_output=True, timeout=contract['budget']['per_process_timeout_seconds'])
    elapsed = time.monotonic() - start
    (OUT / (label + '.stdout.txt')).write_bytes(proc.stdout)
    (OUT / (label + '.stderr.txt')).write_bytes(proc.stderr)
    result = json.loads(proc.stdout)
    stored = read(ROOT / ('raw/' + label + '.json'))
    raw = (ROOT / ('raw/' + label + '.stdout.txt')).read_bytes()
    check(label + ': process success and empty stderr', proc.returncode == 0 and not proc.stderr)
    check(label + ': recorded raw stderr empty', not (ROOT / ('raw/' + label + '.stderr.txt')).read_bytes())
    check(label + ': recorded output hash', sha_bytes(raw) == stored['provenance']['stdout_sha256'])
    check(label + ': parsed recorded stdout equals stored score', json.loads(raw) == {k: v for k, v in stored.items() if k not in ('provenance', 'integrity_after')})
    check(label + ': replay byte-identical stdout', proc.stdout == raw)
    check(label + ': candidate hash', result['candidate_sha256'] == sha(candidate))
    prov = stored['provenance']
    check(label + ': historical process provenance', prov['argv'] == [manifest['runtime'], '-I', '-B', str(ROOT / 'protected/evaluator.py'), str(ROOT / prov['candidate_path'])] and prov['exit_code'] == 0 and prov['timeout_seconds'] == 5 and prov['cwd'] == str(ROOT / 'active') and prov['evaluator_sha256'] == sha(ROOT / 'protected/evaluator.py') and prov['python'] == manifest['python'] and 0 <= prov['elapsed_seconds_observed_not_ranked'] < 5)
    check(label + ': integrity reported after evaluation', stored['integrity_after'] == {'frozen_hashes_match': True, 'package_hashes_match': True})
    if result['status'] == 'valid':
        check(label + ': exact case inputs and answers', [(c['id'], c['input'], c['expected']) for c in result['cases']] == cases)
        computed = sum(isinstance(c.get('actual'), str) and c['actual'] == c['expected'] for c in result['cases'])
        tree = ast.parse(candidate.read_text())
        check(label + ': independently derived score', result['passed'] == computed and result['failed'] == len(cases) - computed and result['case_count'] == len(cases) and result['ast_nodes'] == sum(1 for _ in ast.walk(tree)))
        check(label + ': each pass flag independently derived', all(c['passed'] == (isinstance(c.get('actual'), str) and c['actual'] == c['expected']) for c in result['cases']))
    else:
        check(label + ': invalid syntax independently confirmed', result['status'] == 'invalid' and result['error'].startswith('SyntaxError:'))
        try: ast.parse(candidate.read_text())
        except SyntaxError: invalid_syntax = True
        else: invalid_syntax = False
        check(label + ': AST parser rejects source', invalid_syntax)
    replays[label] = {'candidate': relative, 'argv': argv, 'cwd': str(OUT), 'exit_code': proc.returncode, 'elapsed_seconds_observed_not_ranked': elapsed, 'stdout_sha256': sha_bytes(proc.stdout), 'result': result}

# Derive selection from contract, using case identities rather than runner's positional zip.
def decide(old, new):
    if new['status'] != 'valid': return 'invalid', []
    old_pass = {c['id'] for c in old['cases'] if c['passed']}
    new_pass = {c['id'] for c in new['cases'] if c['passed']}
    regressions = sorted(old_pass - new_pass)
    if regressions: return 'rejected', regressions
    if new['passed'] > old['passed']: return 'accepted', []
    if new['passed'] == old['passed']:
        if new['ast_nodes'] < old['ast_nodes']: return 'accepted', []
        if new['ast_nodes'] == old['ast_nodes']: return 'tied', []
    return 'rejected', []
incumbent_id, best = 'original', replays['baseline']['result']
transitions = []
for number, event in enumerate(trials, 1):
    current = replays[event['trial_id']]['result']
    decision, regressions = decide(best, current)
    check(event['trial_id'] + ': parent, number and budget', event['trial_number'] == number and event['parent_incumbent'] == incumbent_id and event['parent_sha256'] == best['candidate_sha256'] and event['remaining_trial_budget'] == 3 - number)
    check(event['trial_id'] + ': identities and archive match proposal', event['candidate_sha256'] == current['candidate_sha256'] and event['contract_sha256'] == sha(ROOT / 'protected/goal-contract.json') and event['evaluator_sha256'] == sha(ROOT / 'protected/evaluator.py') and sha(ROOT / f'trials/proposal-{number:02}.py') == current['candidate_sha256'])
    check(event['trial_id'] + ': independent decision and scores', event['decision'] == decision and sorted(event['regressions']) == regressions and event['score_before'] == {k: best[k] for k in ('passed', 'ast_nodes')} and event['score_after'] == {k: current[k] for k in ('passed', 'ast_nodes')} and event['repetitions'] == 1)
    transitions.append({'trial': event['trial_id'], 'parent': incumbent_id, 'decision': decision, 'passed': current['passed'], 'ast_nodes': current['ast_nodes'], 'regressions': regressions})
    if decision == 'accepted': incumbent_id, best = event['trial_id'], current
    check(event['trial_id'] + ': resulting incumbent', event['resulting_incumbent'] == incumbent_id)
    check(event['trial_id'] + ': exact active file removed and archive protected', not (ROOT / event['mutation_set'][0]).exists() and (ROOT / event['candidate_archive']).stat().st_mode & 0o222 == 0)
    check(event['trial_id'] + ': disposal assertions', all(read(ROOT / f'trials/{event["trial_id"]}/disposal.json').values()))
check('final state agrees with independently retained incumbent', state['incumbent_id'] == incumbent_id and state['incumbent_sha256'] == best['candidate_sha256'] == sha(ROOT / 'incumbent/normalize.py') and state['optimization_trials_completed'] == 3)
check('state score equals recorded retained trial', state['score'] == read(ROOT / ('raw/' + incumbent_id + '.json')))
check('summary agrees with replay and gain', summary['incumbent']['id'] == incumbent_id and summary['incumbent']['sha256'] == best['candidate_sha256'] and summary['incumbent']['passed'] == best['passed'] and summary['incumbent']['ast_nodes'] == best['ast_nodes'] and summary['genuine_correctness_gain_cases'] == best['passed'] - replays['baseline']['result']['passed'] and summary['optimization_trials'] == 3)
check('active directory empty', not list((ROOT / 'active').iterdir()))
controls = read(ROOT / 'controls/results.json')
check('controls separate from optimization count', len(controls) == 3 and all(c['optimization_trial'] is False for c in controls) and ledger[-1]['optimization_trial_count_added'] == 0 and summary['negative_controls_count'] == 3)
check('wrong output control is a regression', decide(best, replays['negative-control-wrong-output']['result'])[0] == 'rejected')
check('invalid candidate is invalid rather than gain', decide(best, replays['negative-control-invalid-syntax']['result'])[0] == 'invalid')
changed = ROOT / 'controls/negative-control-mutated-evaluator.py'
identity_control = {'status': 'invalid_evaluator_identity', 'executed': False, 'observed_sha256': sha(changed), 'expected_sha256': sha(ROOT / 'protected/evaluator.py')}
check('changed evaluator refused by independent identity preflight', identity_control['observed_sha256'] != identity_control['expected_sha256'])
check('changed evaluator control matches captured result', identity_control == read(ROOT / 'raw/negative-control-evaluator-mutation.json'))
check('all control archives match result index', all(c['result'] == read(ROOT / ('raw/' + c['label'] + '.json')) for c in controls))

# Bind historic calls/results to host history, avoiding the self-authored provenance index.
history = [json.loads(x) for x in HOST.read_text().splitlines()]
calls = {o['payload']['call_id']: (i, o['payload']) for i, o in enumerate(history, 1) if o.get('type') == 'response_item' and o.get('payload', {}).get('type') in ('custom_tool_call', 'function_call')}
wanted = ['0eead6', 'c777a4', '251dfd', '538f1b', '653cc4', 'd516df']
host_records = {}
for line, obj in enumerate(history, 1):
    p = obj.get('payload', {})
    if obj.get('type') != 'response_item' or p.get('type') != 'custom_tool_call_output': continue
    for block in p.get('output', []):
        text = block.get('text', '')
        for chunk in wanted:
            marker = '{"chunk_id":"' + chunk + '"'
            if marker not in text: continue
            result = json.JSONDecoder().raw_decode(text[text.index(marker):])[0]
            call_line, call = calls[p['call_id']]
            source = call.get('input', call.get('arguments', ''))
            commands = [json.loads(x) for x in re.findall(r'cmd:("(?:[^"\\]|\\.)*")', source)]
            host_records[chunk] = {'call_line': call_line, 'output_line': line, 'timestamp': obj['timestamp'], 'call_id': p['call_id'], 'exit_code': result['exit_code'], 'tool_output_sha256': sha_bytes(result['output'].encode()), 'command_sha256': [sha_bytes(c.encode()) for c in commands]}
            check(chunk + ': host-recorded successful actual tool result', result['exit_code'] == 0 and bool(commands))
            if chunk == '251dfd':
                created_runner = commands[0].split("<<'PY'\n", 1)[1].split('\nPY\n', 1)[0] + '\n'
                check('executed runner is byte-identical to reviewed runner', sha_bytes(created_runner.encode()) == sha(ROOT / 'run_fixture.py'))
            if chunk in ('538f1b', '653cc4', 'd516df'):
                observed_event = json.JSONDecoder().raw_decode(result['output'])[0]
                expected_event = next(e for e in trials if e['trial_id'] == observed_event['trial_id'])
                check(chunk + ': host trial event equals ledger', observed_event == expected_event)
            if chunk == '0eead6':
                check('host-delivered complete resource route matches captured bytes', result['output'].encode() == (ROOT / 'raw/resource-delivery.stdout.txt').read_bytes())
check('all required original tool chunks present in historical order', set(host_records) == set(wanted) and [host_records[k]['output_line'] for k in wanted] == sorted(host_records[k]['output_line'] for k in wanted))
loader_meta = read(ROOT / 'raw/resource-delivery-command.json')
loader = subprocess.run(loader_meta['argv'], cwd=REPO, capture_output=True, timeout=5)
check('independent full resource load matches raw delivery and recorded hash', loader.returncode == 0 and not loader.stderr and loader.stdout == (ROOT / 'raw/resource-delivery.stdout.txt').read_bytes() and sha_bytes(loader.stdout) == loader_meta['stdout_sha256'])

runner = ast.parse((ROOT / 'run_fixture.py').read_text())
trial_fn = next(n for n in runner.body if isinstance(n, ast.FunctionDef) and n.name == 'trial')
append_line = next(n.lineno for n in ast.walk(trial_fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'append_event')
advance_line = next(n.lineno for n in ast.walk(trial_fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'copyfile' and any('incumbent/normalize.py' in ast.unparse(a) for a in n.args[1:]))
check('reviewed trial function records decision before incumbent copy', append_line < advance_line)
for group, root in [('frozen_hashes', ROOT), ('package_hashes', REPO)]:
    check(group + ': unchanged after replay', all(sha(root / n) == h for n, h in manifest[group].items()))
check('all original fixture files and modes unchanged during verification', before == snapshot())
findings = [
    {'severity': 'limit', 'finding': 'No tied or losing optimization trial ran. All three optimization trials were accepted. Separate controls test scoring/identity rejection, not trial() rejected/tied state transitions or continuation after a loss.'},
    {'severity': 'limit', 'finding': 'The wrong-output and syntax-control dispositions are assigned in controls(), not routed through trial() acceptance. Independent classification confirms the outcomes, but controller rejection-state coverage remains absent.'},
    {'severity': 'limit', 'finding': 'A small visible deterministic dataset and a local AST-node proxy support only this fixture. No held-out transfer, statistical, runtime speed, cross-model, or frontier-performance conclusion follows.'},
    {'severity': 'limit', 'finding': 'Read-only modes and hashes guard a trusted fixture. Candidate execution uses exec and is not an OS security sandbox; malicious candidates and crash/timeout recovery were not evaluated.'},
    {'severity': 'limit', 'finding': 'The ledger append occurs before copy/state update in the actual historic runner, but crash-consistent durability (fsync/transaction/recovery) was neither promised nor demonstrated.'},
    {'severity': 'info', 'finding': 'All three hypotheses are plausible task improvements. Trial 1 fixes 10 cases; trials 2 and 3 simplify at equal correctness under the preregistered metric. No deliberately bad control contributes to the gain.'}
]
report = {'verdict': 'pass' if all(c['pass'] for c in checks) else 'hold', 'scope': 'Independent deterministic local fixture acceptance verification only', 'formal_promotion': 'hold; not requested or evaluated', 'created_at': datetime.datetime.now(datetime.UTC).isoformat(), 'reviewer_task_id': os.environ.get('CODEX_THREAD_ID'), 'runtime': sys.version, 'head': manifest['head'], 'manifest_sha256': sha(ROOT / 'protected/manifest.json'), 'runner_sha256': sha(ROOT / 'run_fixture.py'), 'verifier_sha256': sha(Path(__file__)), 'resource_route': 'experiment fully loaded through actual helper', 'checks': checks, 'transitions': transitions, 'retained_incumbent': {'id': incumbent_id, 'sha256': best['candidate_sha256'], 'passed': best['passed'], 'case_count': len(cases), 'ast_nodes': best['ast_nodes']}, 'gain_cases': best['passed'] - replays['baseline']['result']['passed'], 'replays': replays, 'evaluator_identity_control': identity_control, 'historical_provenance': {'host_session': str(HOST), 'records': host_records}, 'decision_before_advance': {'append_line': append_line, 'advance_line': advance_line}, 'fixture_snapshot_before_and_after': before, 'findings': findings, 'limits': {'tie_branch_demonstrated': False, 'losing_trial_transition_demonstrated': False, 'negative_controls_are_optimization_trials': False, 'formal_promotion_evidence': False, 'frontier_benchmark': False}}
save('independent-review.json', report)
print(json.dumps({'verdict': report['verdict'], 'checks': len(checks), 'failures': [c for c in checks if not c['pass']], 'transitions': transitions, 'replayed_evaluator_processes': len(replays), 'gain_cases': report['gain_cases'], 'retained_incumbent': report['retained_incumbent']}, indent=2))
