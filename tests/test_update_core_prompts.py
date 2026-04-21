from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "update-core-prompts.py"
SPEC = importlib.util.spec_from_file_location("update_core_prompts", SCRIPT_PATH)
assert SPEC and SPEC.loader
update_core_prompts = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = update_core_prompts
SPEC.loader.exec_module(update_core_prompts)


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def create_release_repo(path: Path, tag: str, release_source: str | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    run_git(path, "config", "user.name", "Core Prompts Test")
    run_git(path, "config", "user.email", "core-prompts-test@example.com")
    (path / "scripts").mkdir()
    (path / "VERSION").write_text(f"{tag}\n", encoding="utf-8")
    (path / "scripts" / "install-local.sh").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
target="$HOME"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) shift; target="$1" ;;
  esac
  shift
done
mkdir -p "$target/.core-prompts-updater"
cp "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/VERSION" "$target/.core-prompts-updater/VERSION"
cp "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/RELEASE_SOURCE.env" "$target/.core-prompts-updater/RELEASE_SOURCE.env" 2>/dev/null || true
""",
        encoding="utf-8",
    )
    (path / "scripts" / "install-local.sh").chmod(0o755)
    (path / "RELEASE_SOURCE.env").write_text(release_source or "ORIGIN_URL=unused\nGITLAB_URL=unused\n", encoding="utf-8")
    run_git(path, "add", ".")
    run_git(path, "commit", "-qm", "release")
    run_git(path, "tag", tag)


def clone_release_repo(source: Path, path: Path) -> None:
    subprocess.run(["git", "clone", "-q", str(source), str(path)], check=True)


def write_support(root: Path, version: str, origin: Path, gitlab: Path) -> Path:
    support = root / "home" / ".core-prompts-updater"
    support.mkdir(parents=True)
    (support / "VERSION").write_text(f"{version}\n", encoding="utf-8")
    (support / "RELEASE_SOURCE.env").write_text(
        f"ORIGIN_URL={origin}\nGITLAB_URL={gitlab}\n",
        encoding="utf-8",
    )
    return support


def run_update(tmp_path: Path, support: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return subprocess.run(
        ["python3", str(SCRIPT_PATH), "--support-root", str(support), "--target-home", str(home), *args],
        cwd=ROOT,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def read_state(tmp_path: Path) -> dict[str, str]:
    return json.loads((tmp_path / "home" / ".core-prompts-state" / "release-watch.json").read_text(encoding="utf-8"))


def write_pending_state(tmp_path: Path, mirror: Path, pending: str = "v1.7.2") -> None:
    state_file = tmp_path / "home" / ".core-prompts-state" / "release-watch.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "installed_version": "v1.7.1",
                "latest_version": pending,
                "pending_version": pending,
                "mirror_path": str(mirror),
                "last_checked_at": "2026-04-21T00:00:00Z",
                "last_notified_at": "",
                "status": "pending-install",
                "note": "Run ~/update_core_prompts.sh --accept-release to refresh the installed bundle",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def create_fake_mirror(path: Path, version: str = "v1.7.2") -> Path:
    scripts = path / "scripts"
    scripts.mkdir(parents=True)
    (path / "VERSION").write_text(f"{version}\n", encoding="utf-8")
    (scripts / "install-local.sh").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
target="$HOME"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) shift; target="$1" ;;
  esac
  shift
done
mkdir -p "$target/.core-prompts-updater"
cp "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/VERSION" "$target/.core-prompts-updater/VERSION"
""",
        encoding="utf-8",
    )
    (scripts / "install-local.sh").chmod(0o755)
    return path


def test_help_output_contains_release_flags() -> None:
    result = subprocess.run(["python3", str(SCRIPT_PATH), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)
    assert "--check-release" in result.stdout
    assert "--accept-release" in result.stdout
    assert "checks only and never auto-installs" in result.stdout


def test_check_release_current_when_versions_match(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    gitlab = tmp_path / "gitlab"
    create_release_repo(origin, "v1.7.1")
    clone_release_repo(origin, gitlab)
    support = write_support(tmp_path, "v1.7.1", origin, gitlab)

    result = run_update(tmp_path, support, "--check-release", "--json")

    assert result.returncode == 0, result.stderr
    state = json.loads(result.stdout)
    assert state["status"] == "current"
    assert state["installed_version"] == "v1.7.1"
    assert state["latest_version"] == "v1.7.1"
    assert state["pending_version"] == ""
    assert (tmp_path / "home" / ".core-prompts-release-cache" / "repo").is_dir()


def test_check_release_pending_when_newer_tag_exists(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    gitlab = tmp_path / "gitlab"
    release_source = f"ORIGIN_URL={origin}\nGITLAB_URL={gitlab}\n"
    create_release_repo(origin, "v1.7.2", release_source)
    clone_release_repo(origin, gitlab)
    support = write_support(tmp_path, "v1.7.1", origin, gitlab)

    result = run_update(tmp_path, support, "--check-release")

    assert result.returncode == 0, result.stderr
    state = read_state(tmp_path)
    assert state["status"] == "pending-install"
    assert state["pending_version"] == "v1.7.2"
    assert "accept-release" in state["note"]


def test_normal_update_warns_pending_without_blocking(tmp_path: Path) -> None:
    support = tmp_path / "support"
    scripts = support / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "deploy-surfaces.sh").write_text("#!/usr/bin/env bash\necho normal-sync\n", encoding="utf-8")
    (scripts / "deploy-surfaces.sh").chmod(0o755)
    home = tmp_path / "home"
    state_dir = home / ".core-prompts-state"
    state_dir.mkdir(parents=True)
    (state_dir / "release-watch.json").write_text(
        json.dumps({"status": "pending-install", "pending_version": "v1.7.2", "latest_version": "v1.7.2"}) + "\n",
        encoding="utf-8",
    )

    result = run_update(tmp_path, support)

    assert result.returncode == 0
    assert "normal-sync" in result.stdout
    assert "Release Watch Warning" in result.stderr
    assert "--accept-release" in result.stderr


def test_accept_release_decline_preserves_pending_state(tmp_path: Path) -> None:
    mirror = create_fake_mirror(tmp_path / "mirror")
    support = tmp_path / "home" / ".core-prompts-updater"
    support.mkdir(parents=True)
    (support / "VERSION").write_text("v1.7.1\n", encoding="utf-8")
    write_pending_state(tmp_path, mirror)

    result = run_update(tmp_path, support, "--accept-release", input_text="n\n")

    assert result.returncode == 0, result.stderr
    state = read_state(tmp_path)
    assert state["status"] == "pending-install"
    assert state["pending_version"] == "v1.7.2"
    assert (support / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.1"


def test_accept_release_approval_refreshes_and_clears_pending(tmp_path: Path) -> None:
    mirror = create_fake_mirror(tmp_path / "mirror")
    support = tmp_path / "home" / ".core-prompts-updater"
    support.mkdir(parents=True)
    (support / "VERSION").write_text("v1.7.1\n", encoding="utf-8")
    write_pending_state(tmp_path, mirror)

    result = run_update(tmp_path, support, "--accept-release", "--yes")

    assert result.returncode == 0, result.stderr
    state = read_state(tmp_path)
    assert state["status"] == "current"
    assert state["pending_version"] == ""
    assert (support / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.2"


def test_remote_divergence_records_status_and_does_not_advance_mirror(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    gitlab = tmp_path / "gitlab"
    create_release_repo(origin, "v1.7.2")
    create_release_repo(gitlab, "v1.7.3")
    support = write_support(tmp_path, "v1.7.1", origin, gitlab)

    result = run_update(tmp_path, support, "--check-release")

    assert result.returncode == 0, result.stderr
    state = read_state(tmp_path)
    assert state["status"] == "remote-divergence"
    assert state["pending_version"] == ""
    assert "origin=v1.7.2" in state["note"]
    assert "gitlab=v1.7.3" in state["note"]
    assert not (tmp_path / "home" / ".core-prompts-release-cache" / "repo").exists()


def test_remote_divergence_when_latest_tag_object_differs(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    gitlab = tmp_path / "gitlab"
    create_release_repo(origin, "v1.7.2", "ORIGIN_URL=origin\nGITLAB_URL=gitlab\n")
    create_release_repo(gitlab, "v1.7.2", "ORIGIN_URL=gitlab\nGITLAB_URL=origin\n")
    support = write_support(tmp_path, "v1.7.1", origin, gitlab)

    result = run_update(tmp_path, support, "--check-release")

    assert result.returncode == 0, result.stderr
    state = read_state(tmp_path)
    assert state["status"] == "remote-divergence"
    assert state["pending_version"] == ""
    assert "tag objects differ" in state["note"]
    assert not (tmp_path / "home" / ".core-prompts-release-cache" / "repo").exists()


def test_schedule_runner_executes_release_check_before_normal_update(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(update_core_prompts, "run", fake_run)
    monkeypatch.setattr(update_core_prompts.shutil, "which", lambda name: None)
    paths = update_core_prompts.Paths(support_root=tmp_path / "support", home=tmp_path / "home")

    assert update_core_prompts.install_schedule(paths, "11:00") == 0

    runner = paths.schedule_runner.read_text(encoding="utf-8")
    assert '"$UPDATE_SCRIPT" --check-release' in runner
    assert runner.index('--check-release') < runner.index('--yes')
    assert calls == []
