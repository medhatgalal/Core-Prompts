import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / 'sources/capability-resources/engos-memory-context-continuity/state_store.py'
spec = importlib.util.spec_from_file_location('context_store', HELPER)
store = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = store
spec.loader.exec_module(store)


class ConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.layout = store.resolve_layout(self.repo, 'active-task', self.root / 'state')

    def test_missing_is_read_only_and_incomplete(self):
        result = store.consolidation_report(self.layout)
        self.assertFalse(result['check_complete'])
        self.assertEqual(result['missing_files'], ['context', 'insights'])
        self.assertFalse(self.layout.state_root.exists())

    def test_boundary_counts_and_milestone_without_mutation(self):
        store.initialize(self.layout)
        store.atomic_write(self.layout, 'context', 'x\n' * 449)
        store.atomic_write(self.layout, 'insights', 'é' * 22499)
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.layout.files.values()}
        self.assertFalse(store.consolidation_report(self.layout)['consolidation_due'])
        self.assertTrue(store.consolidation_report(self.layout, True)['consolidation_due'])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.layout.files.values()})
        store.atomic_write(self.layout, 'context', 'x\n' * 450)
        result = store.consolidation_report(self.layout)
        self.assertTrue(result['size_trigger'])
        self.assertEqual(result['files']['context']['lines'], 450)
        store.atomic_write(self.layout, 'context', '')
        store.atomic_write(self.layout, 'insights', 'é' * 22500)
        result = store.consolidation_report(self.layout)
        self.assertTrue(result['size_trigger'])
        self.assertEqual(result['files']['insights']['bytes'], 45001)
        self.assertEqual(result['files']['insights']['lines'], 1)

    def test_exact_byte_boundary_and_unterminated_line(self):
        store.initialize(self.layout)
        self.layout.insights_path.write_bytes(b'x' * 45000)
        result = store.consolidation_report(self.layout)
        self.assertTrue(result['size_trigger'])
        self.assertEqual(result['files']['insights']['lines'], 1)

    def test_rewrite_preserves_todo_permissions_and_lock(self):
        store.initialize(self.layout)
        todo = self.layout.todo_path.read_bytes()
        store.atomic_write(self.layout, 'context', 'old\n' * 500)
        with store.task_write_lock(self.layout):
            with self.assertRaises(store.StateStoreError):
                store.atomic_write(self.layout, 'context', 'new')
        self.assertEqual(self.layout.context_path.read_text(), 'old\n' * 500)
        store.atomic_write(self.layout, 'context', 'new')
        self.assertEqual(self.layout.context_path.read_text(), 'new\n')
        self.assertEqual(self.layout.context_path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.layout.todo_path.read_bytes(), todo)
        self.assertEqual(len(list(self.layout.task_dir.iterdir())), 3)

    def test_cli_check_and_write_options(self):
        args = [sys.executable, str(HELPER), 'consolidate', '--cwd', str(self.repo), '--task-id', 'active-task', '--state-home', str(self.layout.state_root)]
        result = subprocess.run(args + ['--milestone'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"milestone_trigger": true', result.stdout)
        self.assertFalse(self.layout.state_root.exists())
        result = subprocess.run(args + ['--kind', 'context'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.layout.state_root.exists())


if __name__ == '__main__':
    unittest.main()
