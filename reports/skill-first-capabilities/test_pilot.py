"""Offline collector safety checks; no provider/model calls."""
import importlib.util
from pathlib import Path
import sys
import json
import os
import signal
import tempfile
import time
import unittest

SPEC = importlib.util.spec_from_file_location('pilot', Path(__file__).with_name('pilot.py'))
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)

class SafetyTests(unittest.TestCase):
    def test_expired_deadline_prevents_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'unexpected'
            result = pilot.collect([sys.executable, '-c', f'open({str(target)!r}, "w").close()'], time.monotonic()-1, directory)
            self.assertEqual(result['status'], 'not_run')
            self.assertFalse(target.exists())

    def test_timeout_stops_child_that_would_write_later(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'unexpected'
            child = f'import time;time.sleep(0.7);open({str(target)!r}, "w").close()'
            parent = f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);print("started",flush=True);time.sleep(10)'
            result = pilot.collect([sys.executable,'-c',parent], time.monotonic()+0.2,directory)
            self.assertEqual(result['status'], 'timeout')
            self.assertIn('started', result['stdout'])
            time.sleep(0.8)
            self.assertFalse(target.exists())

    def test_detached_child_holding_pipes_does_not_hang(self):
        with tempfile.TemporaryDirectory() as directory:
            pidfile = Path(directory)/'child.pid'
            child = 'import time;time.sleep(20)'
            parent = f'import subprocess,sys; p=subprocess.Popen([sys.executable,"-c",{child!r}],start_new_session=True);open({str(pidfile)!r},"w").write(str(p.pid))'
            started = time.monotonic()
            try:
                result = pilot.collect([sys.executable,'-c',parent], started+0.3, directory)
                self.assertLess(time.monotonic()-started, 1.0)
                self.assertEqual(result['status'], 'containment_unverified')
                self.assertFalse(result['model_admission'])
            finally:
                if pidfile.exists():
                    try:
                        os.kill(int(pidfile.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_success_stops_group_child_with_redirected_pipes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'unexpected'
            child = f'import time;time.sleep(0.6);open({str(target)!r},"w").close()'
            parent = f'import subprocess,sys;subprocess.Popen([sys.executable,"-c",{child!r}],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)'
            result = pilot.collect([sys.executable,'-c',parent], time.monotonic()+1, directory)
            self.assertEqual(result['status'], 'completed')
            time.sleep(0.7)
            self.assertFalse(target.exists())

    def test_stale_preparation_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            prep = Path(directory)/'preparation.json'
            paths = [Path(pilot.__file__).resolve(), Path(pilot.__file__).with_name('fixtures.json').resolve(), pilot.ROOT/'evals/adapters/registry.json']
            binding = {str(p.relative_to(pilot.ROOT)): pilot.digest(p) for p in paths}
            prep.write_text(json.dumps({'source_bindings': binding}))
            pilot.verify_preparation(prep)
            binding[next(iter(binding))] = '0'*64
            prep.write_text(json.dumps({'source_bindings': binding}))
            with self.assertRaisesRegex(ValueError, 'frozen preparation changed'):
                pilot.verify_preparation(prep)

    def test_registry_capability_cannot_replace_actual_negative_observation(self):
        registry = {'adapters': [{'id': 'codex-experimental', 'supported_tool_policy_modes': ['repo-write-subagents']}]}
        result = pilot.admission('codex', registry)
        self.assertFalse(result['admitted'])
        self.assertEqual(result['decision'], 'retain')
        self.assertFalse(result['metrics_available_before_trials']['complete_native_tokens'])

if __name__ == '__main__':
    unittest.main()
