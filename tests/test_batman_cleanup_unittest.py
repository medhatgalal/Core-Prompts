"""Unrecognized obsolete Batman files are user data, not deletion authority."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = ROOT / "scripts/deploy-surfaces.sh"
BATMAN = "engos-orchestration-batman"
PACKAGE = Path(f".kiro/skills/{BATMAN}")
LEGACY_RELATIVE_PATHS = tuple(PACKAGE / name for name in (
    "PROTOCOL.md", "PROMPT-AMENDMENT.md", "CODEX-UAC-INTAKE.md"))


class BatmanCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        # macOS tempfile may spell its physical directory through /var; the
        # installer correctly rejects symlink ancestors, so use its real path.
        self.base = Path(self.temp_dir.name).resolve()
        self.target = self.base / "target"
        self.fake_bin = self.base / "bin"
        self.fake_bin.mkdir()
        for name in ("kiro-cli", "codex"):
            executable = self.fake_bin / name
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o755)

    def run_deploy(self, *args):
        env = os.environ.copy()
        env["PATH"] = f"{self.fake_bin}:/usr/bin:/bin"
        env["PYTHON_BIN"] = sys.executable
        return subprocess.run(
            ["/bin/bash", str(DEPLOY_SCRIPT), *args, "--target", str(self.target), "--allow-nonlocal-target"],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, check=False, timeout=90)

    def seed_unrecognized_files(self):
        expected = {}
        for index, relative in enumerate(LEGACY_RELATIVE_PATHS, start=1):
            content = bytes([index, 0, 255 - index]) + f" custom {relative.name}\n".encode()
            path = self.target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            expected[relative] = content
        return expected

    def assert_preserved(self, expected):
        self.assertEqual({rel: (self.target / rel).read_bytes() for rel in expected}, expected)
        self.assertFalse((self.target / ".core-prompts-state/stale-pruned").exists())

    def document(self, result, code):
        self.assertEqual(result.returncode, code, result.stdout)
        return json.loads(result.stdout)

    def test_dry_run_reports_selected_package_preserved_without_delete_actions(self):
        original = self.seed_unrecognized_files()
        plan = self.document(self.run_deploy("--cli", "kiro", "--slug", BATMAN, "--surface-only", "--dry-run"), 0)
        self.assertTrue(any(row.get("slug") == BATMAN and row.get("kind") == "skill" for row in plan["preserved"]))
        self.assertFalse(any(action["path"].startswith(PACKAGE.as_posix() + "/") for action in plan["actions"]))
        self.assertFalse(any(action["op"] == "remove" for action in plan["actions"]))
        self.assert_preserved(original)
        self.assertFalse((self.target / ".core-prompts-state").exists())

    def test_selected_custom_package_preserves_every_byte_and_reports_attention(self):
        original = self.seed_unrecognized_files()
        for relative in (PACKAGE / "SKILL.md", PACKAGE / "resources/local.json", PACKAGE / "LOCAL-NOTES.md"):
            path = self.target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"preserve custom package bytes\n")
            original[relative] = path.read_bytes()
        receipt = self.document(self.run_deploy("--cli", "kiro", "--slug", BATMAN, "--surface-only"), 2)
        self.assertEqual(receipt["status"], "applied-with-preserved")
        self.assertTrue(any(row.get("slug") == BATMAN for row in receipt["preserved"]))
        self.assert_preserved(original)
        self.assertFalse((self.target / f".kiro/agents/{BATMAN}.json").exists())
        self.assertFalse((self.target / PACKAGE / "resources/capability.json").exists())
        journal = self.target / ".core-prompts-state/install-transactions" / receipt["transaction"] / "journal.json"
        actions = json.loads(journal.read_bytes())["plan"]["actions"]
        self.assertFalse(any(action["path"].startswith(PACKAGE.as_posix() + "/") for action in actions))
        self.assertFalse(any(action["op"] == "remove" for action in actions))

    def test_symlink_stays_in_place_and_preserves_external_referent(self):
        external = self.base / "external-protocol.md"
        content = b"external source must remain untouched\x00\xff\n"
        external.write_bytes(content)
        link = self.target / LEGACY_RELATIVE_PATHS[0]
        link.parent.mkdir(parents=True)
        link.symlink_to(external)
        receipt = self.document(self.run_deploy("--cli", "kiro", "--slug", BATMAN, "--surface-only"), 2)
        self.assertTrue(any("symlink" in row["reason"] for row in receipt["preserved"]))
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.readlink(), external)
        self.assertEqual(link.read_bytes(), content)
        self.assertEqual(external.read_bytes(), content)
        self.assertFalse((self.target / ".core-prompts-state/stale-pruned").exists())
        self.assertFalse((self.target / PACKAGE / "SKILL.md").exists())

    def test_other_slug_does_not_touch_or_report_unselected_batman_package(self):
        original = self.seed_unrecognized_files()
        review = "engos-quality-code-review"
        receipt = self.document(self.run_deploy("--cli", "kiro", "--slug", review, "--surface-only"), 0)
        self.assertEqual(receipt["preserved"], [])
        self.assert_preserved(original)
        installed = self.target / f".kiro/skills/{review}/SKILL.md"
        self.assertEqual(installed.read_bytes(), (ROOT / f".kiro/skills/{review}/SKILL.md").read_bytes())
        selection = json.loads((self.target / ".core-prompts-state/installation.json").read_bytes())["selection"]
        self.assertEqual(selection, [f"kiro:skill:{review}"])

    def test_codex_deploy_does_not_touch_or_report_kiro_residues(self):
        original = self.seed_unrecognized_files()
        receipt = self.document(self.run_deploy("--cli", "codex", "--slug", BATMAN, "--surface-only"), 0)
        self.assertEqual(receipt["preserved"], [])
        self.assert_preserved(original)
        self.assertTrue((self.target / f".agents/skills/{BATMAN}/SKILL.md").is_file())
        self.assertTrue((self.target / f".codex/agents/{BATMAN}.toml").is_file())
        selection = json.loads((self.target / ".core-prompts-state/installation.json").read_bytes())["selection"]
        self.assertEqual(selection, [f"codex:agent:{BATMAN}", f"codex:skill:{BATMAN}"])

    def test_unfiltered_repair_never_claims_random_named_files_as_owned(self):
        original = self.seed_unrecognized_files()
        extra = PACKAGE / "KEEP.md"
        (self.target / extra).write_bytes(b"preserve extra custom file\n")
        original[extra] = (self.target / extra).read_bytes()
        receipt = self.document(self.run_deploy("--cli", "kiro", "--repair"), 2)
        self.assertTrue(any(row.get("slug") == BATMAN for row in receipt["preserved"]))
        self.assert_preserved(original)
        self.assertFalse((self.target / PACKAGE / "SKILL.md").exists())
        self.assertFalse((self.target / PACKAGE / "resources/capability.json").exists())
        ownership = json.loads((self.target / ".core-prompts-state/installation.json").read_bytes())
        self.assertNotIn(f"kiro:skill:{BATMAN}", ownership["packages"])


if __name__ == "__main__":
    unittest.main()
