from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = ROOT / "scripts" / "deploy-surfaces.sh"
LEGACY_RELATIVE_PATHS = (
    Path(".kiro/skills/batman/PROTOCOL.md"),
    Path(".kiro/skills/batman/PROMPT-AMENDMENT.md"),
    Path(".kiro/skills/batman/CODEX-UAC-INTAKE.md"),
)


class BatmanCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.target = Path(self.temp_dir.name) / "target"
        self.fake_bin = Path(self.temp_dir.name) / "bin"
        self.fake_bin.mkdir(parents=True)
        for name in ("kiro-cli", "codex"):
            executable = self.fake_bin / name
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

    def run_deploy(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PATH"] = f"{self.fake_bin}:/usr/bin:/bin"
        return subprocess.run(
            [
                "/bin/bash",
                str(DEPLOY_SCRIPT),
                *args,
                "--target",
                str(self.target),
                "--allow-nonlocal-target",
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    def seed_legacy_sources(self) -> dict[Path, bytes]:
        expected: dict[Path, bytes] = {}
        for index, path in enumerate(LEGACY_RELATIVE_PATHS, start=1):
            content = bytes([index, 0, 255 - index]) + f" legacy {path.name}\n".encode()
            target = self.target / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            self.assertTrue(target.is_file())
            self.assertFalse(target.is_symlink())
            expected[path] = content
        return expected

    def archived_file_bytes(self) -> dict[Path, bytes]:
        archive = self.target / ".core-prompts-state" / "stale-pruned"
        if not archive.exists():
            return {}
        archived: dict[Path, bytes] = {}
        for timestamp_dir in archive.iterdir():
            for path in timestamp_dir.rglob("*"):
                if path.is_file():
                    archived[path.relative_to(timestamp_dir)] = path.read_bytes()
        return archived

    def test_batman_kiro_dry_run_names_exact_legacy_prune_set(self) -> None:
        original = self.seed_legacy_sources()

        result = self.run_deploy(
            "--cli",
            "kiro",
            "--slug",
            "batman",
            "--surface-only",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        prune_lines = {
            line.removeprefix("DRY-RUN PRUNE ")
            for line in result.stdout.splitlines()
            if line.startswith("DRY-RUN PRUNE ")
        }
        self.assertEqual(
            prune_lines,
            {str(self.target / path) for path in LEGACY_RELATIVE_PATHS},
        )
        self.assertEqual(
            {path: (self.target / path).read_bytes() for path in LEGACY_RELATIVE_PATHS},
            original,
        )
        self.assertFalse(
            (self.target / ".core-prompts-state" / "stale-pruned").exists()
        )

    def test_batman_kiro_deploy_archives_only_legacy_files(self) -> None:
        original = self.seed_legacy_sources()
        valid_skill = self.target / ".kiro/skills/batman/SKILL.md"
        valid_resource = self.target / ".kiro/skills/batman/resources/local.json"
        unrelated = self.target / ".kiro/skills/batman/LOCAL-NOTES.md"
        for path in (valid_skill, valid_resource, unrelated):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("preserve\n", encoding="utf-8")

        result = self.run_deploy(
            "--cli",
            "kiro",
            "--slug",
            "batman",
            "--surface-only",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.archived_file_bytes(), original)
        for path in LEGACY_RELATIVE_PATHS:
            self.assertFalse((self.target / path).exists())
        self.assertTrue(valid_skill.is_file())
        self.assertTrue(valid_resource.is_file())
        self.assertTrue(unrelated.is_file())
        self.assertIn("stale_pruned=3", result.stdout)
        receipt_lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith("PRUNED stale deprecated surface ")
        ]
        self.assertTrue(all(" -> " in line for line in receipt_lines), result.stdout)
        receipt_destinations = {
            Path(line.split(" -> ", 1)[1]) for line in receipt_lines
        }
        self.assertEqual(len(receipt_destinations), 3, result.stdout)
        self.assertTrue(all(path.is_file() for path in receipt_destinations))
        self.assertTrue(
            all(
                path.is_relative_to(
                    self.target / ".core-prompts-state" / "stale-pruned"
                )
                for path in receipt_destinations
            )
        )

    def test_symlink_receipt_names_archive_without_touching_external_target(self) -> None:
        external = Path(self.temp_dir.name) / "external-protocol.md"
        external_content = b"external source must remain untouched\x00\xff\n"
        external.write_bytes(external_content)
        source = self.target / LEGACY_RELATIVE_PATHS[0]
        source.parent.mkdir(parents=True, exist_ok=True)
        source.symlink_to(external)

        result = self.run_deploy(
            "--cli",
            "kiro",
            "--slug",
            "batman",
            "--surface-only",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(source.exists())
        self.assertFalse(source.is_symlink())
        self.assertEqual(external.read_bytes(), external_content)
        archived = list(
            (
                self.target / ".core-prompts-state" / "stale-pruned"
            ).glob(f"*/{LEGACY_RELATIVE_PATHS[0]}")
        )
        self.assertEqual(len(archived), 1)
        archived_link = archived[0]
        self.assertTrue(archived_link.is_symlink())
        self.assertEqual(archived_link.readlink(), external)
        self.assertEqual(archived_link.read_bytes(), external_content)
        receipt_line = next(
            line
            for line in result.stdout.splitlines()
            if line.startswith(f"PRUNED stale deprecated surface {source} -> ")
        )
        self.assertEqual(Path(receipt_line.split(" -> ", 1)[1]), archived_link)
        self.assertIn("stale_pruned=1", result.stdout)

    def test_non_batman_filtered_deploy_does_not_prune_legacy_files(self) -> None:
        original = self.seed_legacy_sources()

        result = self.run_deploy(
            "--cli",
            "kiro",
            "--slug",
            "code-review",
            "--surface-only",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.archived_file_bytes(), {})
        self.assertEqual(
            {path: (self.target / path).read_bytes() for path in LEGACY_RELATIVE_PATHS},
            original,
        )

    def test_batman_non_kiro_deploy_does_not_touch_kiro_residues(self) -> None:
        original = self.seed_legacy_sources()

        result = self.run_deploy(
            "--cli",
            "codex",
            "--slug",
            "batman",
            "--surface-only",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.archived_file_bytes(), {})
        self.assertEqual(
            {path: (self.target / path).read_bytes() for path in LEGACY_RELATIVE_PATHS},
            original,
        )

    def test_full_kiro_install_cleanup_remains_bounded_to_three_files(self) -> None:
        original = self.seed_legacy_sources()
        unrelated = self.target / ".kiro/skills/batman/KEEP.md"
        unrelated.write_text("preserve\n", encoding="utf-8")

        result = self.run_deploy("--cli", "kiro")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.archived_file_bytes(), original)
        self.assertTrue(unrelated.is_file())
        self.assertTrue((self.target / ".kiro/skills/batman/SKILL.md").is_file())
        self.assertTrue(
            (self.target / ".kiro/skills/batman/resources/capability.json").is_file()
        )
        self.assertIn("stale_pruned=3", result.stdout)


if __name__ == "__main__":
    unittest.main()
