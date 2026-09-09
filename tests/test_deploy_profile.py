"""Disposable-home contract tests; never inspect installed user skills."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
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


class MigrationTests(unittest.TestCase):
    apply = ProfileTests.apply
    put = ProfileTests.put

    def setUp(self):
        ProfileTests.setUp(self)
        self.profile['slugs'] = ['demo']
        for rel in ('VERSION', 'scripts/deploy-profile.py', 'scripts/update-core-prompts.py'):
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('old runtime\n')
        deploy.install_bundle.build(self.repo)
        for rel, identity in deploy.install_bundle.verified(self.repo).items():
            deploy.atomic_write(self.home / '.core-prompts-updater' / rel,
                                (self.repo / rel).read_bytes(), identity['mode'])
        self.apply()

    def files(self):
        return {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mode & 0o777)
                for p in self.home.rglob('*') if p.is_file()}

    def add_resource(self):
        manifest_path = self.repo / '.meta/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for cli in self.profile['targets']:
            rel = f'.{cli}/skills/demo/references/new.md'
            manifest['resources'][cli + '_skill'].append(rel)
            (self.repo / rel).write_text('new declared resource\n')
        manifest_path.write_text(json.dumps(manifest))
        (self.repo / 'VERSION').write_text('new runtime\n')
        (self.repo / '.codex/skills/demo/SKILL.md').write_text('new skill body\n')
        deploy.install_bundle.build(self.repo)

    def migration_plan(self):
        return deploy.plan(self.repo, self.home, self.profile, migration=True)

    def assert_blocked_without_writes(self, expected):
        before = self.files()
        plan = self.migration_plan()
        self.assertTrue(any(expected in blocker for blocker in plan['blockers']), plan['blockers'])
        with self.assertRaisesRegex(ValueError, 'profile install blocked'):
            deploy.apply(self.repo, self.home, self.profile, plan, migration=True)
        self.assertEqual(before, self.files())
        return plan

    def test_sync_rejects_additions_but_migration_updates_owned_runtime_and_skills(self):
        self.add_resource()
        before = self.files()
        sync = deploy.plan(self.repo, self.home, self.profile, routine=True)
        self.assertIn('selected skill file scope changed; reviewed migration required', sync['blockers'])
        with self.assertRaisesRegex(ValueError, 'profile install blocked'):
            deploy.apply(self.repo, self.home, self.profile, sync)
        self.assertEqual(before, self.files())
        plan = self.migration_plan()
        self.assertFalse(plan['blockers'])
        self.assertTrue(plan['migration'])
        additions = [a['path'] for a in plan['actions']
                     if a['before'] is None and not a['path'].startswith('.core-prompts-updater/')]
        self.assertEqual(additions, ['.agents/skills/demo/references/new.md',
                                    '.grok/skills/demo/references/new.md', '.kiro/skills/demo/references/new.md'])
        self.assertTrue(any(a['path'] == '.core-prompts-updater/VERSION' for a in plan['actions']))
        self.assertEqual({a['action'] for a in plan['actions']}, {'copy'})
        result = deploy.apply(self.repo, self.home, self.profile, plan, migration=True)
        self.assertEqual(result['status'], 'applied')
        self.assertEqual((self.home / '.core-prompts-updater/VERSION').read_text(), 'new runtime\n')
        self.assertEqual(before[deploy.PROFILE], self.files()[deploy.PROFILE])
        old_receipt = json.loads(before[deploy.RECEIPT][0])
        receipt = deploy.read_receipt(self.home)
        self.assertEqual(receipt['approved_profile_sha256'], old_receipt['approved_profile_sha256'])
        self.assertEqual(receipt['skill_scope'], sorted(plan['source_files']))
        self.assertEqual(receipt['bundle_files'], deploy.install_bundle.verified(self.repo))
        self.assertFalse(deploy.plan(self.repo, self.home, self.profile, routine=True)['blockers'])

    def test_migration_rollback_restores_prior_bytes_modes_and_only_removes_new_owned_files(self):
        unrelated = self.put('.agents/skills/third-party/SKILL.md', 'third party\n')
        unrelated.chmod(0o600)
        self.add_resource()
        before = self.files()
        tx = deploy.apply(self.repo, self.home, self.profile, self.migration_plan(), migration=True)['transaction']
        deploy.rollback(self.home, tx)
        after = {rel: value for rel, value in self.files().items()
                 if not rel.startswith(deploy.STATE + '/transactions/')}
        retained = {rel: value for rel, value in before.items()
                    if not rel.startswith(deploy.STATE + '/transactions/')}
        self.assertEqual(after, retained)
        self.assertTrue((self.home / deploy.STATE / 'transactions' / tx / 'journal.json').is_file())

    def test_migration_requires_explicit_apply_opt_in_and_matching_mode(self):
        self.add_resource()
        before = self.files()
        plan = self.migration_plan()
        with self.assertRaisesRegex(ValueError, 'migration mode'):
            deploy.apply(self.repo, self.home, self.profile, plan)
        ordinary = deploy.plan(self.repo, self.home, self.profile)
        with self.assertRaisesRegex(ValueError, 'migration mode'):
            deploy.apply(self.repo, self.home, self.profile, ordinary, migration=True)
        edited = json.loads(json.dumps(plan))
        edited['migration'] = False
        with self.assertRaisesRegex(ValueError, 'approved plan differs'):
            deploy.apply(self.repo, self.home, self.profile, edited)
        self.assertEqual(before, self.files())

    def test_migration_rejects_profile_target_and_slug_changes(self):
        self.add_resource()
        for change in ({'targets': ['codex']}, {'slugs': []}, {'retire': ['.codex/skills/demo/SKILL.md']}):
            with self.subTest(change=change):
                original = dict(self.profile)
                self.profile.update(change)
                self.assert_blocked_without_writes('saved target profile differs')
                self.profile = original

    def test_migration_rejects_changed_saved_profile_and_missing_prior_ownership(self):
        self.add_resource()
        original = (self.home / deploy.PROFILE).read_bytes()
        self.put(deploy.PROFILE, original.decode() + '\n')
        self.assert_blocked_without_writes('saved profile file differs')
        (self.home / deploy.PROFILE).write_bytes(original)
        receipt = deploy.read_receipt(self.home)
        receipt['files'].pop('.agents/skills/demo/SKILL.md')
        self.put(deploy.RECEIPT, json.dumps(receipt))
        self.assert_blocked_without_writes('prior skill ownership')

    def test_migration_rejects_removed_skill_and_runtime_scope(self):
        self.add_resource()
        manifest_path = self.repo / '.meta/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['resources']['codex_skill'].remove('.codex/skills/demo/references/a.md')
        manifest_path.write_text(json.dumps(manifest))
        deploy.install_bundle.build(self.repo)
        self.assert_blocked_without_writes('skill file scope was removed')
        inventory_path = self.repo / deploy.install_bundle.MANIFEST
        inventory = json.loads(inventory_path.read_text())
        inventory['files'].pop('.codex/skills/demo/references/a.md')
        inventory_path.write_text(json.dumps(inventory))
        self.assert_blocked_without_writes('standalone bundle file scope was removed')

    def test_empty_slug_profile_cannot_expand_to_new_packages(self):
        self.profile['slugs'] = []
        self.apply()
        self.add_resource()
        manifest_path = self.repo / '.meta/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['ssot_sources'].append({'slug': 'extra', 'expected_surface_names': ['codex_skill']})
        path = self.repo / '.codex/skills/extra/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text('new package\n')
        manifest_path.write_text(json.dumps(manifest))
        deploy.install_bundle.build(self.repo)
        self.assert_blocked_without_writes('already approved skill packages')

    def test_migration_preserves_custom_unknown_missing_and_symlinked_packages(self):
        self.add_resource()
        cases = [('custom', '.agents/skills/demo/references/a.md'),
                 ('unknown', '.agents/skills/demo/references/new.md'),
                 ('unlisted', '.agents/skills/demo/references/custom.md'),
                 ('missing', '.agents/skills/demo/SKILL.md'),
                 ('symlink', '.agents/skills/demo/references/new.md')]
        for kind, rel in cases:
            with self.subTest(kind=kind):
                path = self.home / rel
                previous = path.read_bytes() if path.exists() else None
                if kind == 'missing':
                    path.unlink()
                elif kind == 'symlink':
                    path.symlink_to(self.repo / '.codex/skills/demo/references/new.md')
                else:
                    self.put(rel, 'new declared resource\n' if kind == 'unknown' else 'custom\n')
                plan = self.assert_blocked_without_writes('selected skills have customized')
                if kind != 'missing':
                    self.assertFalse(any(a['path'].startswith('.agents/skills/demo/') for a in plan['actions']))
                if path.exists() or path.is_symlink():
                    path.unlink()
                if previous is not None:
                    path.write_bytes(previous)

    def test_migration_rejects_custom_runtime_and_unverified_runtime_source(self):
        self.add_resource()
        path = self.home / '.core-prompts-updater/VERSION'
        before = path.read_text()
        path.write_text('user runtime change\n')
        self.assert_blocked_without_writes('customized or unknown standalone file')
        path.write_text(before)
        (self.repo / 'VERSION').write_text('changed after runtime inventory\n')
        self.assert_blocked_without_writes('standalone bundle identity mismatch')

    def test_managed_updates_block_unlisted_live_and_broken_package_symlinks(self):
        bundle = '.agents/skills/demo'
        link = self.home / bundle / 'custom-symlink'
        for migration in (False, True):
            if migration:
                self.add_resource()
            for broken in (False, True):
                with self.subTest(migration=migration, broken=broken):
                    destination = self.repo / ('missing-file' if broken else '.codex/skills/demo/SKILL.md')
                    link.symlink_to(destination)
                    before = self.files()
                    before_paths = sorted(str(p.relative_to(self.home)) for p in self.home.rglob('*'))
                    plan = deploy.plan(self.repo, self.home, self.profile,
                                       routine=not migration, migration=migration)
                    reason = plan['inventories'][bundle]['blocked']
                    self.assertIn('symlink is preserved', reason)
                    self.assertIn({'path': bundle, 'reason': reason}, plan['preserved'])
                    self.assertIn('selected skills have customized, unknown, or missing files', plan['blockers'])
                    with self.assertRaisesRegex(ValueError, 'profile install blocked'):
                        deploy.apply(self.repo, self.home, self.profile, plan, migration=migration)
                    self.assertEqual(before, self.files())
                    self.assertEqual(before_paths, sorted(str(p.relative_to(self.home)) for p in self.home.rglob('*')))
                    self.assertEqual(link.readlink(), destination)
                    self.assertFalse((self.home / bundle / 'references/new.md').exists())
                    self.assertNotIn(bundle + '/references/new.md', deploy.read_receipt(self.home)['skill_scope'])
                link.unlink()

    def test_migration_requires_prior_runtime_ownership_and_preserves_later_added_file_edits(self):
        self.add_resource()
        original = (self.home / deploy.RECEIPT).read_bytes()
        receipt = deploy.read_receipt(self.home)
        receipt['bundle_files'] = {}
        self.put(deploy.RECEIPT, json.dumps(receipt))
        self.assert_blocked_without_writes('prior standalone bundle ownership')
        (self.home / deploy.RECEIPT).write_bytes(original)
        tx = deploy.apply(self.repo, self.home, self.profile, self.migration_plan(), migration=True)['transaction']
        self.put('.agents/skills/demo/references/new.md', 'later user edit\n')
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'rollback preserves changed file'):
            deploy.rollback(self.home, tx)
        self.assertEqual(before, self.files())

    def test_migration_stale_source_target_receipt_profile_and_destination_are_rejected(self):
        self.add_resource()
        for rel, root in [('.codex/skills/demo/references/new.md', self.repo),
                          ('.agents/skills/demo/SKILL.md', self.home),
                          (deploy.RECEIPT, self.home), (deploy.PROFILE, self.home)]:
            with self.subTest(rel=rel):
                plan = self.migration_plan()
                path = root / rel
                original = path.read_bytes()
                path.write_bytes(original + b'\n')
                before = self.files()
                with self.assertRaisesRegex(ValueError, 'approved plan differs'):
                    deploy.apply(self.repo, self.home, self.profile, plan, migration=True)
                self.assertEqual(before, self.files())
                path.write_bytes(original)
        plan = self.migration_plan()
        other = Path(self.tmp.name) / 'other-home'
        other.mkdir()
        with self.assertRaisesRegex(ValueError, 'approved plan differs'):
            deploy.apply(self.repo, other, self.profile, plan, migration=True)
        self.assertEqual(list(other.iterdir()), [])

    def test_cli_migration_requires_review_and_matching_opt_in(self):
        self.add_resource()
        command = [sys.executable, str(Path(deploy.__file__)), '--repo', str(self.repo),
                   '--target', str(self.home), '--profile', str(self.home / deploy.PROFILE)]
        before = self.files()
        for flags in (['--migrate'], ['--migrate', '--sync', '--dry-run'],
                      ['--migrate', '--rollback', '0' * 32, '--dry-run']):
            result = subprocess.run([*command, *flags], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout)
        dry = subprocess.run([*command, '--migrate', '--dry-run'], capture_output=True, text=True)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertFalse(json.loads(dry.stdout)['blockers'])
        plan_path = Path(self.tmp.name) / 'migration-plan.json'
        plan_path.write_text(dry.stdout)
        missing = subprocess.run([*command, '--apply-plan', str(plan_path)], capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn('migration mode', missing.stderr)
        self.assertEqual(before, self.files())
        result = subprocess.run([*command, '--migrate', '--apply-plan', str(plan_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'applied')


if __name__ == '__main__':
    unittest.main()
