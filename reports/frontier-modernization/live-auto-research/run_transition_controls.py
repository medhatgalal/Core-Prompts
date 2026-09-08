"""Clearly labeled state-machine controls; not additional optimization trials."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
CONTROL = ROOT / 'transition-controls'
CONTROL.mkdir(exist_ok=False)
for directory in ['protected', 'original', 'incumbent', 'active', 'raw', 'trials']:
    (CONTROL / directory).mkdir()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


preserved = ['ledger.jsonl', 'state.json', 'summary.json', 'incumbent/normalize.py',
             'original/normalize.py', 'protected/evaluator.py', 'protected/goal-contract.json',
             'protected/manifest.json', 'run_fixture.py']
before = {path: sha(ROOT / path) for path in preserved}
contract = {
    'kind': 'separate stateful control replay, not optimization search',
    'optimization_trials_added': 0,
    'implementation_under_test': 'run_fixture.py:trial',
    'implementation_sha256': before['run_fixture.py'],
    'isolation': 'Exact runner module is imported unchanged; ROOT alone is redirected to this copied control state. The original REPO, MANIFEST, CONTRACT, function code and decision logic remain unchanged.',
    'seed': {'source': 'trials/trial-01/normalize.py', 'sha256': sha(ROOT / 'trials/trial-01/normalize.py'),
             'score': {'passed': 16, 'ast_nodes': 60}, 'counter_reset': 'Three control-only calls start at local counter zero.'},
    'sequence': [
        {'number': 1, 'label': 'known lower-quality negative control', 'source': 'original/normalize.py', 'expected': 'rejected; incumbent unchanged; exact active control file disposed; archive retained'},
        {'number': 2, 'label': 'equal-score tie control', 'source': 'accepted scanner plus a comment; changed bytes, identical AST', 'expected': 'tied; incumbent unchanged; exact active control file disposed; archive retained'},
        {'number': 3, 'label': 'accepted-transition positive control after loss and tie', 'source': 'trials/trial-03/normalize.py', 'expected': 'accepted; incumbent advances under equal correctness and lower AST count'}],
    'claim_boundary': 'Inner runner event names and counters are unchanged for code fidelity. Every inner call belongs to this labeled control replica and adds zero trials or gains to the original optimization run.'}
save(CONTROL / 'control-contract.json', contract)
manifest = json.loads((ROOT / 'protected/manifest.json').read_text())
for rel in manifest['frozen_hashes']:
    target = CONTROL / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / rel, target)
    target.chmod(0o444)
shutil.copyfile(ROOT / 'protected/manifest.json', CONTROL / 'protected/manifest.json')
(CONTROL / 'protected/manifest.json').chmod(0o444)
shutil.copyfile(ROOT / 'trials/trial-01/normalize.py', CONTROL / 'incumbent/normalize.py')
seed_state = {'incumbent_id': 'seed-from-original-trial-01',
              'incumbent_sha256': sha(CONTROL / 'incumbent/normalize.py'),
              'score': json.loads((ROOT / 'raw/trial-01.json').read_text()),
              'optimization_trials_completed': 0}
save(CONTROL / 'state.json', seed_state)
save(CONTROL / 'seed-state.json', seed_state)
spec = importlib.util.spec_from_file_location('unaltered_fixture_runner', ROOT / 'run_fixture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
assert sha(ROOT / 'run_fixture.py') == contract['implementation_sha256']
fixture.ROOT = CONTROL
sources = [
    (ROOT / 'original/normalize.py').read_text(),
    (ROOT / 'trials/trial-01/normalize.py').read_text() + '\n# Labeled tie control: a comment does not change the AST.\n',
    (ROOT / 'trials/trial-03/normalize.py').read_text()]
for number, source in enumerate(sources, start=1):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        fixture.trial(number, source, 'CONTROL ONLY: ' + contract['sequence'][number - 1]['label'])
    (CONTROL / 'raw' / f'transition-call-{number}.stdout.txt').write_text(out.getvalue())
    state = json.loads((CONTROL / 'state.json').read_text())
    save(CONTROL / f'state-after-control-{number}.json', state)
    assert before == {path: sha(ROOT / path) for path in preserved}
    print(out.getvalue(), end='')
ledger = [json.loads(line) for line in (CONTROL / 'ledger.jsonl').read_text().splitlines()]
assert [entry['decision'] for entry in ledger] == ['rejected', 'tied', 'accepted']
assert ledger[0]['resulting_incumbent'] == ledger[1]['resulting_incumbent'] == seed_state['incumbent_id']
assert ledger[2]['parent_incumbent'] == seed_state['incumbent_id']
assert sha(CONTROL / 'incumbent/normalize.py') == sha(ROOT / 'trials/trial-03/normalize.py')
assert not list((CONTROL / 'active').iterdir())
assert len([json.loads(line) for line in (ROOT / 'ledger.jsonl').read_text().splitlines() if json.loads(line)['event'] == 'optimization_trial']) == 3
summary = {'kind': 'stateful controls only', 'control_calls': 3, 'optimization_trials_added': 0,
           'decisions': [entry['decision'] for entry in ledger],
           'original_artifacts_hashes_before': before,
           'original_artifacts_hashes_after': {path: sha(ROOT / path) for path in preserved},
           'original_run_unchanged': True, 'exact_runner_implementation_unchanged': True,
           'original_optimization_trials': 3, 'control_evaluator_hash': sha(CONTROL / 'protected/evaluator.py'),
           'control_evaluator_unchanged': sha(CONTROL / 'protected/evaluator.py') == manifest['frozen_hashes']['protected/evaluator.py'],
           'active_control_files_remaining': [], 'archives_preserved': True,
           'independent_verification': 'pending'}
save(CONTROL / 'summary.json', summary)
print(json.dumps(summary, indent=2))
