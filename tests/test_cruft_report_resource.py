from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
RESOURCE = ROOT / "sources" / "capability-resources" / "codebase-health-audit" / "cruft-report"
HELPER = RESOURCE.with_name("cruft_report.py")


def make_home(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    home = tmp_path / "home"
    paths = {
        "dotfiles-bak": home / ".agents" / "config.bak.123",
        "kiro-agent-bak": home / ".kiro" / "agents" / "agent.json.bak.1",
        "cli-state-bak": home / ".codex" / "state.json.bak",
        "beads-temp": home / "Desktop" / "AI_Repos" / "EngOS" / ".beads" / ".~issues.jsonl.1",
        "worktree-temp": home / ".codex" / "worktrees" / "fixture" / "issues.jsonl.XXXXXX.tmp",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    (home / ".claude").mkdir(parents=True)
    (home / ".codex" / "skills").mkdir(parents=True)
    (home / ".local" / "bin").mkdir(parents=True)
    return home, paths


def run_report(home: Path, *args: str, path_prefix: Path | None = None, timeout: int = 5) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    if path_prefix is not None:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"
    return subprocess.run(
        ["bash", str(RESOURCE), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=env,
    )


def test_help_documents_noninteractive_interface_and_exit_codes(tmp_path: Path) -> None:
    home, _ = make_home(tmp_path)
    result = run_report(home, "--help")
    assert result.returncode == 0
    assert "Cleanup requires a reviewed dry-run selection digest" in result.stdout
    assert "--expect-sha256 DIGEST" in result.stdout
    assert "Exit codes:" in result.stdout
    assert result.stderr == ""


def test_json_report_is_parseable_read_only_and_complete(tmp_path: Path) -> None:
    home, paths = make_home(tmp_path)
    result = run_report(home, "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["read_only"] is True
    assert payload["total_count"] == 5
    assert {item["name"]: item["count"] for item in payload["categories"]} == {
        "dotfiles-bak": 1,
        "kiro-agent-bak": 1,
        "cli-state-bak": 1,
        "beads-temp": 1,
        "worktree-temp": 1,
    }
    assert all(path.exists() for path in paths.values())
    assert result.stderr == ""
    assert "\x1b" not in result.stdout
    assert all(sample.startswith("~/") for item in payload["categories"] for sample in item["sample"])
    assert all(not item["newest_at"] or item["newest_at"].endswith("Z") for item in payload["categories"])


def test_cleanup_without_confirm_returns_immediately_and_changes_nothing(tmp_path: Path) -> None:
    home, paths = make_home(tmp_path)
    result = run_report(home, "--json", "--trash", "dotfiles-bak", timeout=2)
    assert result.returncode == 4
    assert json.loads(result.stdout)["status"] == "confirmation_required"
    assert "--confirm" in result.stderr
    assert paths["dotfiles-bak"].exists()


def test_dry_run_previews_exact_category_without_moving_files(tmp_path: Path) -> None:
    home, paths = make_home(tmp_path)
    result = run_report(home, "--json", "--dry-run", "--trash", "dotfiles-bak")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "dry_run"
    assert payload["category"] == "dotfiles-bak"
    assert payload["count"] == 1
    assert len(payload["selection_sha256"]) == 64
    assert paths["dotfiles-bak"].exists()


def test_confirmed_cleanup_uses_explicit_trash_command(tmp_path: Path) -> None:
    home, paths = make_home(tmp_path)
    preview = run_report(home, "--json", "--dry-run", "--trash", "dotfiles-bak")
    selection_sha256 = json.loads(preview.stdout)["selection_sha256"]
    fake_bin = tmp_path / "bin"
    fake_trash = tmp_path / "trash"
    fake_bin.mkdir()
    fake_trash.mkdir()
    helper = fake_bin / "trash"
    helper.write_text(
        "#!/bin/sh\necho 'noisy child stdout'\nfor item in \"$@\"; do mv \"$item\" \"$FAKE_TRASH/\" || exit 1; done\n",
        encoding="utf-8",
    )
    helper.chmod(0o755)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["FAKE_TRASH"] = str(fake_trash)
    result = subprocess.run(
        [
            "bash",
            str(RESOURCE),
            "--json",
            "--trash",
            "dotfiles-bak",
            "--confirm",
            "--expect-sha256",
            selection_sha256,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "moved"
    assert payload["moved"] == 1
    assert not paths["dotfiles-bak"].exists()
    assert (fake_trash / paths["dotfiles-bak"].name).exists()
    assert "moved 1 file" in result.stderr


def test_unknown_category_is_usage_error(tmp_path: Path) -> None:
    home, _ = make_home(tmp_path)
    result = run_report(home, "--json", "--trash", "everything")
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "usage_error"
    assert "unknown category" in result.stderr


def test_confirm_without_category_is_usage_error(tmp_path: Path) -> None:
    home, paths = make_home(tmp_path)
    result = run_report(home, "--confirm")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "--confirm requires --trash CATEGORY" in result.stderr
    assert all(path.exists() for path in paths.values())


@pytest.mark.parametrize("mutation", ["addition", "removal", "replacement"])
def test_confirm_rejects_selection_drift(tmp_path: Path, mutation: str) -> None:
    home, paths = make_home(tmp_path)
    selected = paths["dotfiles-bak"]
    preview = run_report(home, "--json", "--dry-run", "--trash", "dotfiles-bak")
    digest = json.loads(preview.stdout)["selection_sha256"]
    if mutation == "addition":
        (selected.parent / "added.bak.456").write_text("added\n", encoding="utf-8")
    elif mutation == "removal":
        selected.unlink()
    else:
        selected.write_text("replacement\n", encoding="utf-8")

    result = run_report(
        home,
        "--json",
        "--trash",
        "dotfiles-bak",
        "--confirm",
        "--expect-sha256",
        digest,
    )
    assert result.returncode == 6
    assert json.loads(result.stdout)["status"] == "stale_selection"
    assert "changed since the reviewed dry-run" in result.stderr


@pytest.mark.parametrize(
    "args",
    [
        ("--json", "--dry-run"),
        ("--json", "--json"),
        ("--json", "--trash", "dotfiles-bak", "--trash", "dotfiles-bak"),
        ("--json", "--dry-run", "--trash", "dotfiles-bak", "--confirm"),
        ("--json", "--expect-sha256", "0" * 64),
    ],
)
def test_ambiguous_flags_are_structured_usage_errors(tmp_path: Path, args: tuple[str, ...]) -> None:
    home, _ = make_home(tmp_path)
    result = run_report(home, *args)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "usage_error"
    assert result.stderr.startswith("cruft-report:")


def test_unset_home_is_structured_environment_error(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.pop("HOME", None)
    result = subprocess.run(
        ["bash", str(RESOURCE), "--json"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
        env=env,
    )
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "environment_error"
    assert "HOME is unset" in result.stderr


def test_unsupported_python_is_structured_environment_error(tmp_path: Path) -> None:
    home, _ = make_home(tmp_path)
    fake_bin = tmp_path / "old-python"
    fake_bin.mkdir()
    python = fake_bin / "python3"
    python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    python.chmod(0o755)
    result = run_report(home, "--json", path_prefix=fake_bin)
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "environment_error"
    assert "Python 3.11 or newer is required" in result.stderr


def test_empty_confirmed_selection_is_no_op_without_trash_dependency(tmp_path: Path) -> None:
    home = tmp_path / "empty-home"
    home.mkdir()
    preview = run_report(home, "--json", "--dry-run", "--trash", "dotfiles-bak")
    digest = json.loads(preview.stdout)["selection_sha256"]
    result = run_report(
        home,
        "--json",
        "--trash",
        "dotfiles-bak",
        "--confirm",
        "--expect-sha256",
        digest,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "no_op"
    assert payload["moved"] == 0


def test_partial_trash_failure_reports_failed_home_relative_path(tmp_path: Path) -> None:
    home, paths = make_home(tmp_path)
    failing = paths["dotfiles-bak"].parent / "fail.bak.456"
    failing.write_text("fixture\n", encoding="utf-8")
    preview = run_report(home, "--json", "--dry-run", "--trash", "dotfiles-bak")
    digest = json.loads(preview.stdout)["selection_sha256"]
    fake_bin = tmp_path / "bin"
    fake_trash = tmp_path / "trash"
    fake_bin.mkdir()
    fake_trash.mkdir()
    helper = fake_bin / "trash"
    helper.write_text(
        "#!/bin/sh\nname=${1##*/}\ncase \"$name\" in fail.*) echo rejected >&2; exit 9;; esac\nmv \"$1\" \"$FAKE_TRASH/\"\n",
        encoding="utf-8",
    )
    helper.chmod(0o755)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["FAKE_TRASH"] = str(fake_trash)
    result = subprocess.run(
        [
            "bash",
            str(RESOURCE),
            "--json",
            "--trash",
            "dotfiles-bak",
            "--confirm",
            "--expect-sha256",
            digest,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
        env=env,
    )
    assert result.returncode == 5
    payload = json.loads(result.stdout)
    assert payload["status"] == "partial_failure"
    assert payload["moved"] == 1
    assert payload["failed_files"] == ["~/.agents/fail.bak.456"]
    assert failing.exists()


def test_json_handles_control_characters_and_is_deterministic(tmp_path: Path) -> None:
    home, _ = make_home(tmp_path)
    unusual = home / ".agents" / 'line\nquote".bak.999'
    unusual.write_text("fixture\n", encoding="utf-8")
    first = run_report(home, "--json", "--dry-run", "--trash", "dotfiles-bak")
    second = run_report(home, "--json", "--dry-run", "--trash", "dotfiles-bak")
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert payload["files"] == sorted(payload["files"])
    assert any("\n" in item and '"' in item for item in payload["files"])


def test_authored_resource_is_644_and_contains_no_tty_read() -> None:
    assert RESOURCE.stat().st_mode & 0o777 == 0o644
    assert HELPER.stat().st_mode & 0o777 == 0o644
    source = RESOURCE.read_text(encoding="utf-8") + HELPER.read_text(encoding="utf-8")
    assert re.search(r"\bread\s+-r\s+a\b", source) is None
    assert "Proceed?" not in source


def test_build_surfaces_copies_cruft_report_to_all_skill_surfaces(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store", ".venv", "node_modules"),
    )
    bytecode = (
        workspace
        / "sources"
        / "capability-resources"
        / "codebase-health-audit"
        / "__pycache__"
        / "cruft_report.cpython-999.pyc"
    )
    bytecode.parent.mkdir()
    bytecode.write_bytes(b"machine-specific-bytecode")
    subprocess.run(
        ["python3", str(workspace / "scripts" / "build-surfaces.py")],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    for surface in (".codex", ".gemini", ".claude", ".kiro"):
        resources = workspace / surface / "skills" / "codebase-health-audit" / "resources"
        for name in ("cruft-report", "cruft_report.py"):
            deployed = resources / name
            authored = workspace / "sources" / "capability-resources" / "codebase-health-audit" / name
            assert deployed.read_bytes() == authored.read_bytes()
            assert deployed.stat().st_mode & 0o777 == 0o644
        assert not list(resources.rglob("*.pyc"))
        assert not list(resources.rglob("__pycache__"))
    manifest = (workspace / ".meta" / "manifest.json").read_text(encoding="utf-8")
    assert "__pycache__" not in manifest
    assert ".pyc" not in manifest
