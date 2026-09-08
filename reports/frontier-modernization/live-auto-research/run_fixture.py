"""Local fixture runner. The protected contract is the authority for its decisions."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
MANIFEST = json.loads((ROOT / 'protected/manifest.json').read_text())
CONTRACT = json.loads((ROOT / 'protected/goal-contract.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def protected_check():
    mismatches = []
    for path, expected in MANIFEST['frozen_hashes'].items():
        if sha(ROOT / path) != expected:
            mismatches.append(path)
    for path, expected in MANIFEST['package_hashes'].items():
        if sha(REPO / path) != expected:
            mismatches.append(path)
    if mismatches:
        raise RuntimeError('Protected identity drift: ' + repr(mismatches))
    return {'frozen_hashes_match': True, 'package_hashes_match': True}


def execute(label, candidate, evaluator=None):
    protected_check()
    evaluator = evaluator or ROOT / 'protected/evaluator.py'
    if sha(evaluator) != MANIFEST['frozen_hashes']['protected/evaluator.py']:
        result = {'status': 'invalid_evaluator_identity', 'executed': False,
                  'observed_sha256': sha(evaluator),
                  'expected_sha256': MANIFEST['frozen_hashes']['protected/evaluator.py']}
        save(ROOT / 'raw' / (label + '.json'), result)
        return result
    command = [sys.executable, '-I', '-B', str(evaluator), str(candidate)]
    start = time.monotonic()
    proc = subprocess.run(command, cwd=ROOT / 'active', capture_output=True, text=True, timeout=5)
    elapsed = time.monotonic() - start
    (ROOT / 'raw' / (label + '.stdout.txt')).write_text(proc.stdout)
    (ROOT / 'raw' / (label + '.stderr.txt')).write_text(proc.stderr)
    result = json.loads(proc.stdout) if proc.returncode == 0 else {'status': 'invalid', 'error': 'nonzero process exit'}
    result['provenance'] = {'argv': command, 'cwd': str(ROOT / 'active'), 'exit_code': proc.returncode,
                            'elapsed_seconds_observed_not_ranked': elapsed, 'timeout_seconds': 5,
                            'stdout_sha256': hashlib.sha256(proc.stdout.encode()).hexdigest(),
                            'candidate_path': str(candidate.relative_to(ROOT)),
                            'evaluator_sha256': sha(evaluator), 'python': sys.version}
    result['integrity_after'] = protected_check()
    save(ROOT / 'raw' / (label + '.json'), result)
    return result


def read_state():
    return json.loads((ROOT / 'state.json').read_text())


def append_event(event):
    event['at'] = datetime.datetime.now(datetime.UTC).isoformat()
    with (ROOT / 'ledger.jsonl').open('a') as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + '\n')


def initialize():
    if (ROOT / 'state.json').exists():
        raise RuntimeError('Already initialized')
    result = execute('baseline', ROOT / 'original/normalize.py')
    state = {'incumbent_id': 'original', 'incumbent_sha256': sha(ROOT / 'original/normalize.py'),
             'score': result, 'optimization_trials_completed': 0}
    append_event({'event': 'baseline', 'baseline_sha256': state['incumbent_sha256'], 'score': result,
                  'contract_sha256': MANIFEST['frozen_hashes']['protected/goal-contract.json']})
    save(ROOT / 'state.json', state)
    print(json.dumps({'baseline': {'passed': result['passed'], 'total': result['case_count'], 'ast_nodes': result['ast_nodes']},
                      'failed_cases': [c['id'] for c in result['cases'] if not c['passed']]}))


def trial(number, source, hypothesis):
    state = read_state()
    assert number == state['optimization_trials_completed'] + 1 and number <= 3
    protected_check()
    assert sha(ROOT / 'incumbent/normalize.py') == state['incumbent_sha256']
    trial_id = f'trial-{number:02}'
    folder = ROOT / 'trials' / trial_id
    folder.mkdir()
    active = ROOT / 'active' / (trial_id + '.py')
    shutil.copyfile(ROOT / 'incumbent/normalize.py', active)
    parent_hash = sha(active)
    assert parent_hash == state['incumbent_sha256']
    # A single coordinated module replacement is the declared editable mutation set.
    active.write_text(source)
    shutil.copyfile(active, folder / 'normalize.py')
    (folder / 'normalize.py').chmod(0o444)
    result = execute(trial_id, active)
    previous = state['score']
    regressions = [old['id'] for old, new in zip(previous['cases'], result.get('cases', [])) if old['passed'] and not new['passed']]
    if result['status'] != 'valid':
        decision, reason = 'invalid', 'Evaluation could not validly execute.'
    elif regressions:
        decision, reason = 'rejected', 'A previously passing protected case regressed.'
    elif result['passed'] > previous['passed']:
        decision, reason = 'accepted', 'Strict correctness gain without regression.'
    elif result['passed'] == previous['passed'] and result['ast_nodes'] < previous['ast_nodes']:
        decision, reason = 'accepted', 'Equivalent correctness with fewer AST nodes.'
    elif result['passed'] == previous['passed'] and result['ast_nodes'] == previous['ast_nodes']:
        decision, reason = 'tied', 'Equal correctness and complexity; keep incumbent.'
    else:
        decision, reason = 'rejected', 'No correctness gain and greater complexity; keep incumbent.'
    event = {'event': 'optimization_trial', 'trial_id': trial_id, 'trial_number': number,
             'parent_incumbent': state['incumbent_id'], 'parent_sha256': parent_hash,
             'hypothesis': hypothesis, 'mutation_set': [str(active.relative_to(ROOT))],
             'candidate_archive': str((folder / 'normalize.py').relative_to(ROOT)),
             'candidate_sha256': sha(active), 'evaluator_sha256': MANIFEST['frozen_hashes']['protected/evaluator.py'],
             'contract_sha256': MANIFEST['frozen_hashes']['protected/goal-contract.json'],
             'score_before': {'passed': previous['passed'], 'ast_nodes': previous['ast_nodes']},
             'score_after': {'passed': result.get('passed'), 'ast_nodes': result.get('ast_nodes')},
             'regressions': regressions, 'decision': decision, 'reason': reason,
             'resulting_incumbent': trial_id if decision == 'accepted' else state['incumbent_id'],
             'raw_result': 'raw/' + trial_id + '.json', 'repetitions': 1,
             'remaining_trial_budget': 3 - number}
    # Persist the decision before advancing the incumbent.
    append_event(event)
    if decision == 'accepted':
        shutil.copyfile(active, ROOT / 'incumbent/normalize.py')
        state.update(incumbent_id=trial_id, incumbent_sha256=sha(active), score=result)
    state['optimization_trials_completed'] = number
    save(ROOT / 'state.json', state)
    # Dispose only the exact task-owned active trial; keep its immutable evidence archive.
    active.unlink()
    cleanup = {'active_removed': not active.exists(), 'archive_preserved': (folder / 'normalize.py').is_file(),
               'incumbent_preserved': sha(ROOT / 'incumbent/normalize.py') == state['incumbent_sha256'], **protected_check()}
    save(folder / 'disposal.json', cleanup)
    print(json.dumps(event, ensure_ascii=False, indent=2))


def controls():
    state = read_state()
    assert state['optimization_trials_completed'] == 3
    incumbent_before = sha(ROOT / 'incumbent/normalize.py')
    sources = {
      'negative-control-wrong-output': 'def normalize(value):\n    return value.strip()\n',
      'negative-control-invalid-syntax': 'def normalize(value)\n    return value\n',
    }
    results = []
    for label, source in sources.items():
        candidate = ROOT / 'controls' / (label + '.py')
        candidate.write_text(source)
        result = execute(label, candidate)
        disposition = 'rejected_quality_regression' if label.endswith('wrong-output') else 'invalid_candidate_rejected'
        assert result['passed'] < state['score']['passed']
        if label.endswith('invalid-syntax'):
            assert result['status'] == 'invalid'
        results.append({'label': label, 'optimization_trial': False, 'disposition': disposition, 'result': result})
    changed = ROOT / 'controls/negative-control-mutated-evaluator.py'
    changed.write_bytes((ROOT / 'protected/evaluator.py').read_bytes() + b'\n# Deliberately changed copy for an integrity negative control.\n')
    result = execute('negative-control-evaluator-mutation', ROOT / 'incumbent/normalize.py', evaluator=changed)
    assert result['status'] == 'invalid_evaluator_identity' and not result['executed']
    results.append({'label': 'negative-control-evaluator-mutation', 'optimization_trial': False,
                    'disposition': 'rejected_before_execution', 'result': result})
    assert incumbent_before == sha(ROOT / 'incumbent/normalize.py')
    save(ROOT / 'controls/results.json', results)
    append_event({'event': 'negative_controls', 'optimization_trial_count_added': 0,
                  'labels': [r['label'] for r in results], 'incumbent_unchanged': True, **protected_check()})
    print(json.dumps([{'label': r['label'], 'disposition': r['disposition']} for r in results], indent=2))


def finalize():
    state = read_state()
    assert state['optimization_trials_completed'] == 3
    baseline = execute('final-baseline', ROOT / 'original/normalize.py')
    incumbent = execute('final-incumbent', ROOT / 'incumbent/normalize.py')
    summary = {'run_kind': 'actual deterministic local fixture; not formal capability promotion',
               'stop_reason': 'declared 3-trial budget exhausted', 'optimization_trials': 3,
               'baseline': {'passed': baseline['passed'], 'total': baseline['case_count'], 'ast_nodes': baseline['ast_nodes']},
               'incumbent': {'id': state['incumbent_id'], 'sha256': sha(ROOT / 'incumbent/normalize.py'),
                             'passed': incumbent['passed'], 'total': incumbent['case_count'], 'ast_nodes': incumbent['ast_nodes']},
               'genuine_correctness_gain_cases': incumbent['passed'] - baseline['passed'],
               'evaluator_sha256': sha(ROOT / 'protected/evaluator.py'), 'negative_controls_count': 3,
               'active_trial_files_remaining': [p.name for p in (ROOT / 'active').iterdir()],
               'formal_promotion': 'hold; not requested or evaluated', 'independent_review': 'pending', **protected_check()}
    save(ROOT / 'summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['baseline','trial','controls','finalize'])
    parser.add_argument('--number', type=int)
    parser.add_argument('--source-file')
    parser.add_argument('--hypothesis')
    args = parser.parse_args()
    if args.action == 'baseline': initialize()
    elif args.action == 'trial': trial(args.number, Path(args.source_file).read_text(), args.hypothesis)
    elif args.action == 'controls': controls()
    else: finalize()
