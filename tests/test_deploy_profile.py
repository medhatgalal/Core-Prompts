"""Disposable-home contract tests; never inspect installed user skills."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('deploy_profile', Path(__file__).parents[1] / 'scripts/deploy-profile.py')
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.home = Path(self.tmp.name) / 'home'
        self.repo.mkdir(); self.home.mkdir()
        self.profile = {'schema': 1, 'scope': 'skills', 'targets': ['codex', 'kiro', 'grok'], 'retire': []}
        manifest = {'ssot_sources': [{'slug': 'demo', 'expected_surface_names': ['codex_skill', 'kiro_skill', 'grok_skill']}], 'resources': {}}
        for cli in self.profile['targets']:
            prefix = f'.{cli}/skills/demo'
            members = ['references/a.md', 'agents/openai.yaml', 'scripts/run.py', 'resources/capability.json']
            manifest['resources'][cli + '_skill'] = [f'{prefix}/{rel}' for rel in members]
            for rel in ['SKILL.md', *members]:
                p = self.repo / prefix / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('same portable content\n')
                if rel.endswith('.py'):
                    p.chmod(0o755)
        (self.repo / '.meta').mkdir()
        (self.repo / '.meta/manifest.json').write_text(json.dumps(manifest))

    def apply(self):
        return deploy.apply(self.repo, self.home, self.profile, deploy.plan(self.repo, self.home, self.profile))

    def put(self, rel, text):
        p = self.home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def test_selected_targets_full_resources_and_rollback(self):
        before = list(self.home.rglob('*'))
        plan = deploy.plan(self.repo, self.home, self.profile)
        self.assertEqual(list(self.home.rglob('*')), before)
        self.assertEqual(len(plan['actions']), 15)
        tx = self.apply()['transaction']
        for cli, root in [('codex', '.agents'), ('kiro', '.kiro'), ('grok', '.grok')]:
            self.assertEqual((self.home / root / 'skills/demo/scripts/run.py').stat().st_mode & 0o777, 0o755)
            self.assertTrue((self.home / root / 'skills/demo/agents/openai.yaml').is_file())
        self.assertFalse((self.home / '.claude').exists())
        self.assertFalse((self.home / '.codex').exists())
        deploy.rollback(self.home, tx)
        self.assertFalse(any(p.is_file() for p in (self.home / '.agents').rglob('*')))

    def test_unknown_customizations_block_entire_bundle(self):
        p = self.put('.kiro/skills/demo/references/a.md', 'independent customization')
        result = self.apply()
        self.assertTrue(result['preserved'])
        self.assertEqual(p.read_text(), 'independent customization')
        self.assertFalse((self.home / '.kiro/skills/demo/SKILL.md').exists())
        self.assertTrue((self.home / '.agents/skills/demo/SKILL.md').exists())

    def test_unknown_identical_file_is_not_adopted(self):
        self.put('.agents/skills/demo/SKILL.md', 'same portable content\n')
        plan = deploy.plan(self.repo, self.home, self.profile)
        self.assertTrue(plan['preserved'])
        self.assertFalse(any(a['path'].startswith('.agents/') for a in plan['actions']))

    def test_third_party_and_installer_metadata_untouched(self):
        paths = ['.agents/skills/gws-gmail/SKILL.md', '.kiro/skills/third-party/SKILL.md', '.agents/.skill-lock.json']
        for rel in paths:
            self.put(rel, 'owned elsewhere')
        self.apply()
        for rel in paths:
            self.assertEqual((self.home / rel).read_text(), 'owned elsewhere')

    def test_stale_plan_and_rollback_preserve_later_edits(self):
        plan = deploy.plan(self.repo, self.home, self.profile)
        self.put('.grok/skills/demo/SKILL.md', 'new user copy')
        with self.assertRaisesRegex(ValueError, 'approved plan differs'):
            deploy.apply(self.repo, self.home, self.profile, plan)
        tx = self.apply()['transaction']
        p = self.put('.agents/skills/demo/SKILL.md', 'later customization')
        with self.assertRaisesRegex(ValueError, 'rollback preserves'):
            deploy.rollback(self.home, tx)
        self.assertEqual(p.read_text(), 'later customization')

    def test_symlink_parent_is_preserved(self):
        external = Path(self.tmp.name) / 'external'; external.mkdir()
        (self.home / '.agents').symlink_to(external, target_is_directory=True)
        self.assertTrue(self.apply()['preserved'])
        self.assertFalse(list(external.rglob('*')))

    def test_retirement_needs_provenance_and_reader_evidence(self):
        legacy = '.codex/skills/demo/SKILL.md'
        p = self.put(legacy, 'same portable content\n')
        self.profile['retire'] = [legacy]
        self.assertFalse(any(a['action'] == 'retire' for a in deploy.plan(self.repo, self.home, self.profile)['actions']))
        receipt = {'schema': 1, 'owner': 'Core-Prompts', 'files': {legacy: {'identity': deploy.snapshot(p), 'source': legacy}}}
        self.put(deploy.RECEIPT, json.dumps(receipt))
        (self.repo / 'reader.json').write_text('{"verified": true}')
        self.profile['reader_evidence'] = 'reader.json'
        tx = self.apply()['transaction']
        self.assertFalse(p.exists())
        deploy.rollback(self.home, tx)
        self.assertEqual(p.read_text(), 'same portable content\n')

    def test_source_changed_after_plan_is_rejected(self):
        plan = deploy.plan(self.repo, self.home, self.profile)
        (self.repo / '.codex/skills/demo/SKILL.md').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'approved plan differs'):
            deploy.apply(self.repo, self.home, self.profile, plan)

    def test_managed_update_and_modified_resource_preservation(self):
        self.apply()
        (self.repo / '.codex/skills/demo/SKILL.md').write_text('version two')
        self.put('.agents/skills/demo/references/a.md', 'user edit')
        result = self.apply()
        self.assertEqual(result['status'], 'no-op')
        self.assertEqual((self.home / '.agents/skills/demo/SKILL.md').read_text(), 'same portable content\n')

    def test_rollback_dry_run_does_not_write(self):
        tx = self.apply()['transaction']
        before = {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        result = deploy.rollback(self.home, tx, dry_run=True)
        self.assertEqual(result['status'], 'rollback-planned')
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()})

    def test_profile_only_change_is_saved_and_planned(self):
        self.apply()
        self.profile['targets'] = ['codex']
        plan = deploy.plan(self.repo, self.home, self.profile)
        self.assertFalse(plan['actions'])
        self.assertTrue(any(a['path'] == deploy.PROFILE for a in plan['state_actions']))
        self.assertTrue(plan['transaction_artifacts'])
        self.apply()
        self.assertEqual(json.loads((self.home / deploy.PROFILE).read_text())['targets'], ['codex'])

    def test_legacy_custom_resource_blocks_entrypoint_retirement(self):
        legacy = '.codex/skills/demo/SKILL.md'
        p = self.put(legacy, 'same portable content\n')
        self.put('.codex/skills/demo/resources/custom.json', 'installer owned')
        self.put(deploy.RECEIPT, json.dumps({'schema': 1, 'owner': 'Core-Prompts', 'files': {
            legacy: {'identity': deploy.snapshot(p), 'source': legacy}}}))
        self.profile['retire'] = [legacy]
        (self.repo / 'reader.json').write_text('{}')
        self.profile['reader_evidence'] = 'reader.json'
        self.apply()
        self.assertTrue(p.exists())

    def test_atomic_replace_failure_leaves_preimage_recoverable(self):
        from unittest.mock import patch
        self.apply()
        p = self.home / '.agents/skills/demo/SKILL.md'
        before = p.read_bytes()
        with patch.object(deploy.os, 'replace', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                deploy.atomic_write(p, b'new content')
        self.assertEqual(p.read_bytes(), before)
        self.assertFalse(list(p.parent.glob('.core-prompts-stage-*')))

    def test_install_after_rollback_uses_new_reviewed_transaction(self):
        first = self.apply()['transaction']
        deploy.rollback(self.home, first)
        second = self.apply()['transaction']
        self.assertNotEqual(first, second)

    def test_old_standalone_updater_blocks_profile_before_writes(self):
        self.put('.core-prompts-updater/scripts/deploy-surfaces.sh', 'legacy writer')
        before = {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        plan = deploy.plan(self.repo, self.home, self.profile)
        self.assertTrue(plan['blockers'])
        with self.assertRaisesRegex(ValueError, 'profile install blocked'):
            deploy.apply(self.repo, self.home, self.profile, plan)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
