"""Task-specific offline preparation and timed non-model admission diagnostics.

This collector does not dispatch model calls. The existing reviewed adapter
boundary remains authoritative; a new native invocation cannot bypass it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ('codex', 'claude', 'gemini', 'kiro', 'grok')
COMMANDS = {'codex': 'codex', 'claude': 'claude', 'gemini': 'gemini', 'kiro': 'kiro-cli', 'grok': 'grok'}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_preparation(path):
    preparation = json.loads(path.read_text())
    expected = [Path(__file__).resolve(), Path(__file__).with_name('fixtures.json').resolve(), ROOT/'evals/adapters/registry.json']
    actual = {str(p.relative_to(ROOT)): digest(p) for p in expected}
    if preparation.get('source_bindings') != actual:
        raise ValueError('frozen preparation changed; review and explicitly prepare again before dispatch')
    return digest(path)

def stop_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        return False
    return True

def collect(argv, deadline, cwd):
    """Bound owned process group; detached descendants are not contained."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return {'status': 'not_run', 'reason': 'deadline elapsed', 'argv': argv}
    started = time.monotonic()
    proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)
    timed_out = False
    pipes_closed = False
    out = err = b''
    try:
        out, err = proc.communicate(timeout=max(0.001, remaining - 0.1))
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        out, err = exc.output or b'', exc.stderr or b''
    finally:
        # Also stop group children when the main probe exited successfully.
        group_stopped = stop_group(proc)
    if timed_out:
        try:
            out, err = proc.communicate(timeout=max(0.001, min(0.1, deadline-time.monotonic())))
        except subprocess.TimeoutExpired as exc:
            out, err = exc.output or out, exc.stderr or err
            # An escaped child may hold inherited pipes indefinitely. Do not
            # wait on it or claim that process-group cleanup contained it.
            proc.stdout.close()
            proc.stderr.close()
            pipes_closed = True
            try:
                proc.wait(timeout=0.01)
            except subprocess.TimeoutExpired:
                pass
    return {'argv': argv, 'status': 'containment_unverified' if pipes_closed or not group_stopped else ('timeout' if timed_out else 'completed'),
            'exit_code': proc.returncode, 'elapsed_seconds': time.monotonic() - started,
            'stdout': out.decode(errors='replace'), 'stderr': err.decode(errors='replace'),
            'containment_scope': 'owned process group only; detached descendants unverified',
            'model_admission': False, 'model_calls': 0, 'tokens': None}

def admission(provider, registry):
    entries = [x for x in registry['adapters'] if x['id'].startswith(provider + '-')]
    blockers = []
    if not entries:
        blockers.append('No registered native collection adapter for this provider.')
    for entry in entries:
        if entry.get('unavailable_reason'):
            blockers.append(entry['unavailable_reason'])
        if 'repo-write-subagents' not in entry.get('supported_tool_policy_modes', []):
            blockers.append('Registered adapter cannot observe native delegated resource and tool-boundary cases.')
    # These are actual native observations, never replaceable with booleans or
    # claimed receipts from a model. This diagnostic run has performed none.
    blockers.append('Native success/fault/resource/action observations and complete A/B accounting have not passed.')
    return {'provider': provider, 'admitted': False, 'decision': 'retain',
            'comparison': 'inapplicable' if provider == 'grok' else 'not_run',
            'blockers': blockers, 'comparative_model_calls': 0,
            'metrics_available_before_trials': {'elapsed_seconds': True, 'complete_native_tokens': False}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'start', 'probe'])
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--provider', choices=PROVIDERS)
    parser.add_argument('--preparation', type=Path, default=Path(__file__).with_name('preparation.json'))
    args = parser.parse_args()
    if args.action == 'prepare':
        binding = {'schema': 'SkillFirstPilotPreparation.v1', 'clock_started': False,
                   'model_calls': 0, 'source_bindings': {str(p.relative_to(ROOT)): digest(p)
                    for p in [Path(__file__), Path(__file__).with_name('fixtures.json'), ROOT/'evals/adapters/registry.json']},
                   'admission': [admission(p, json.loads((ROOT/'evals/adapters/registry.json').read_text())) for p in PROVIDERS]}
        print(json.dumps(binding, indent=2))
        return
    try:
        preparation_hash = verify_preparation(args.preparation)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.action == 'start':
        anchor = time.time()
        state = {'schema': 'SkillFirstPilotClock.v1', 'anchor_epoch': anchor, 'deadline_epoch': anchor + 3600,
                 'monotonic_anchor': time.monotonic(), 'pid': os.getpid(), 'preparation_sha256': preparation_hash,
                 'stop_action': 'No new trials; SIGKILL owned probe process group at slot deadline.',
                 'provider_windows': {}, 'provider_allowance_seconds': 600, 'unused_time_transferable': False,
                 'setup': [0,120], 'synthesis': [3120,3600]}
        with args.state.open('x') as f:
            json.dump(state, f, indent=2)
        print(json.dumps(state, indent=2))
        return
    if not args.provider:
        parser.error('probe requires --provider')
    state = json.loads(args.state.read_text())
    if state.get('preparation_sha256') != preparation_hash:
        parser.error('preparation differs from started clock; no dispatch')
    now = time.monotonic()
    global_deadline = state['monotonic_anchor'] + 3600
    if now >= global_deadline:
        parser.error('global deadline elapsed; no dispatch')
    windows = state['provider_windows']
    if args.provider not in windows:
        windows[args.provider] = {'start_monotonic': now, 'deadline_monotonic': min(now + 600, global_deadline)}
        args.state.write_text(json.dumps(state, indent=2) + '\n')
    deadline = windows[args.provider]['deadline_monotonic']
    if now >= deadline:
        parser.error('provider allowance elapsed; no dispatch and no borrowed time')
    registry = json.loads((ROOT/'evals/adapters/registry.json').read_text())
    result = admission(args.provider, registry)
    result['clock_state_sha256'] = digest(args.state)
    result['registry_sha256'] = digest(ROOT/'evals/adapters/registry.json')
    binary = shutil.which(COMMANDS[args.provider])
    result['probes'] = []
    if binary:
        for flag in ['--version', '--help']:
            result['probes'].append(collect([binary, flag], min(deadline, time.monotonic()+20), ROOT))
    else:
        result['blockers'].append('Native CLI binary unavailable.')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
