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


def add_release_commit(path: Path, tag: str) -> None:
    (path / "VERSION").write_text(f"{tag}\n", encoding="utf-8")
    run_git(path, "add", "VERSION")
    run_git(path, "commit", "-qm", f"release {tag}")
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


def snapshot_dirs(tmp_path: Path) -> list[Path]:
    root = tmp_path / "home" / ".core-prompts-state" / "snapshots"
    if not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir())


def test_help_output_contains_release_flags() -> None:
    result = subprocess.run(["python3", str(SCRIPT_PATH), "--help"], cwd=ROOT, capture_output=True, text=True, check=True)
    assert "--check-release" in result.stdout
    assert "--accept-release" in result.stdout
    assert "--rollback" in result.stdout
    assert "--list-snapshots" in result.stdout
    assert "--notify-only" in result.stdout
    assert "Default: 2" in result.stdout
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


def test_check_release_current_when_installed_version_omits_v_prefix(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    gitlab = tmp_path / "gitlab"
    create_release_repo(origin, "v1.7.1")
    clone_release_repo(origin, gitlab)
    support = write_support(tmp_path, "1.7.1", origin, gitlab)

    result = run_update(tmp_path, support, "--check-release", "--json")

    assert result.returncode == 0, result.stderr
    state = json.loads(result.stdout)
    assert state["status"] == "current"
    assert state["installed_version"] == "1.7.1"
    assert state["latest_version"] == "v1.7.1"
    assert state["pending_version"] == ""


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
    snapshots = snapshot_dirs(tmp_path)
    assert len(snapshots) == 1
    manifest = json.loads((snapshots[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["installed_version"] == "v1.7.1"
    assert manifest["target_version"] == "v1.7.2"


def test_accept_release_allows_installed_version_without_v_prefix(tmp_path: Path) -> None:
    mirror = create_fake_mirror(tmp_path / "mirror", version="1.7.2")
    support = tmp_path / "home" / ".core-prompts-updater"
    support.mkdir(parents=True)
    (support / "VERSION").write_text("v1.7.1\n", encoding="utf-8")
    write_pending_state(tmp_path, mirror, pending="v1.7.2")

    result = run_update(tmp_path, support, "--accept-release", "--yes")

    assert result.returncode == 0, result.stderr
    state = read_state(tmp_path)
    assert state["status"] == "current"
    assert state["pending_version"] == ""
    assert state["installed_version"] == "1.7.2"
    assert state["latest_version"] == "v1.7.2"


def test_accept_release_fast_forwards_recorded_source_repo_before_install(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    local_repo = tmp_path / "local-repo"
    create_release_repo(origin, "v1.7.1")
    clone_release_repo(origin, local_repo)
    branch = subprocess.run(["git", "-C", str(local_repo), "branch", "--show-current"], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    add_release_commit(origin, "v1.7.2")
    gitlab = tmp_path / "gitlab"
    clone_release_repo(origin, gitlab)
    support = write_support(tmp_path, "v1.7.1", origin, gitlab)
    (support / "LOCAL_REPO.env").write_text(
        f"REPO_PATH={local_repo}\nBRANCH={branch}\nREMOTE_NAME=origin\nREMOTE_URL={origin}\n",
        encoding="utf-8",
    )

    check = run_update(tmp_path, support, "--check-release")
    assert check.returncode == 0, check.stderr
    result = run_update(tmp_path, support, "--accept-release", "--yes")

    assert result.returncode == 0, result.stderr
    assert "Updated recorded source checkout" in result.stderr
    assert (local_repo / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.2"
    assert (support / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.2"
    state = read_state(tmp_path)
    assert state["status"] == "current"
    assert "Updated recorded source checkout" in state["note"]


def test_accept_release_falls_back_to_mirror_when_recorded_source_repo_is_dirty(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    local_repo = tmp_path / "local-repo"
    create_release_repo(origin, "v1.7.1")
    clone_release_repo(origin, local_repo)
    branch = subprocess.run(["git", "-C", str(local_repo), "branch", "--show-current"], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    (local_repo / "local-change.txt").write_text("dirty\n", encoding="utf-8")
    add_release_commit(origin, "v1.7.2")
    gitlab = tmp_path / "gitlab"
    clone_release_repo(origin, gitlab)
    support = write_support(tmp_path, "v1.7.1", origin, gitlab)
    (support / "LOCAL_REPO.env").write_text(
        f"REPO_PATH={local_repo}\nBRANCH={branch}\nREMOTE_NAME=origin\nREMOTE_URL={origin}\n",
        encoding="utf-8",
    )

    check = run_update(tmp_path, support, "--check-release")
    assert check.returncode == 0, check.stderr
    result = run_update(tmp_path, support, "--accept-release", "--yes")

    assert result.returncode == 0, result.stderr
    assert "local changes; using release mirror" in result.stderr
    assert (local_repo / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.1"
    assert (support / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.2"


def test_rollback_restores_previous_support_bundle_and_managed_surface(tmp_path: Path) -> None:
    mirror = create_fake_mirror(tmp_path / "mirror")
    home = tmp_path / "home"
    support = home / ".core-prompts-updater"
    scripts = support / "scripts"
    scripts.mkdir(parents=True)
    (support / "VERSION").write_text("v1.7.1\n", encoding="utf-8")
    (support / ".meta").mkdir()
    (support / ".meta" / "manifest.json").write_text('{"ssot_sources":[]}\n', encoding="utf-8")
    (scripts / "deploy-copy-plan.py").write_text(
        """#!/usr/bin/env python3
from pathlib import Path
import sys
target = Path(sys.argv[2])
print(f"/unused\\t{target / '.codex/skills/demo/SKILL.md'}\\tcodex_skill\\tdemo")
""",
        encoding="utf-8",
    )
    managed_surface = home / ".codex" / "skills" / "demo" / "SKILL.md"
    managed_surface.parent.mkdir(parents=True)
    managed_surface.write_text("previous skill\n", encoding="utf-8")
    write_pending_state(tmp_path, mirror)

    result = run_update(tmp_path, support, "--accept-release", "--yes")

    assert result.returncode == 0, result.stderr
    assert (support / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.2"
    managed_surface.write_text("new skill\n", encoding="utf-8")
    rollback = run_update(tmp_path, support, "--rollback", "previous")
    assert rollback.returncode == 0, rollback.stderr
    assert (support / "VERSION").read_text(encoding="utf-8").strip() == "v1.7.1"
    assert managed_surface.read_text(encoding="utf-8") == "previous skill\n"
    assert read_state(tmp_path)["status"] == "pending-install"


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


def test_auto_accept_refuses_remote_divergence_without_snapshot(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    gitlab = tmp_path / "gitlab"
    create_release_repo(origin, "v1.7.2")
    create_release_repo(gitlab, "v1.7.3")
    support = write_support(tmp_path, "v1.7.1", origin, gitlab)

    result = run_update(tmp_path, support, "--auto-accept-release")

    assert result.returncode == 0, result.stderr
    state = read_state(tmp_path)
    assert state["status"] == "remote-divergence"
    assert snapshot_dirs(tmp_path) == []


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


def test_schedule_runner_auto_accepts_by_default_before_normal_update(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(update_core_prompts, "run", fake_run)
    monkeypatch.setattr(update_core_prompts.shutil, "which", lambda name: None)
    paths = update_core_prompts.Paths(support_root=tmp_path / "support", home=tmp_path / "home")

    assert update_core_prompts.install_schedule(paths, "11:00", notify_only=False, snapshot_retention=2) == 0

    runner = paths.schedule_runner.read_text(encoding="utf-8")
    assert '"$UPDATE_SCRIPT" --check-release' in runner
    assert '"$UPDATE_SCRIPT" --accept-release --yes --snapshot-retention 2' in runner
    assert runner.index('--check-release') < runner.index('--accept-release')
    assert runner.index('--accept-release') < runner.rindex('--yes')
    assert calls == []


def test_schedule_runner_notify_only_preserves_check_only_release_mode(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(update_core_prompts, "run", fake_run)
    monkeypatch.setattr(update_core_prompts.shutil, "which", lambda name: None)
    paths = update_core_prompts.Paths(support_root=tmp_path / "support", home=tmp_path / "home")

    assert update_core_prompts.install_schedule(paths, "11:00", notify_only=True, snapshot_retention=2) == 0

    runner = paths.schedule_runner.read_text(encoding="utf-8")
    assert '"$UPDATE_SCRIPT" --check-release' in runner
    assert '"$UPDATE_SCRIPT" --accept-release --yes' not in runner
    assert calls == []


def test_snapshot_retention_keeps_latest_entries(tmp_path: Path) -> None:
    support = tmp_path / "home" / ".core-prompts-updater"
    support.mkdir(parents=True)
    (support / "VERSION").write_text("v1.7.1\n", encoding="utf-8")
    paths = update_core_prompts.Paths(support_root=support, home=tmp_path / "home")

    for index in range(4):
        update_core_prompts.create_snapshot(paths, installed_version=f"v1.7.{index}", target_version=f"v1.8.{index}", retention=2)

    snapshots = snapshot_dirs(tmp_path)
    assert len(snapshots) == 2
    assert "v1.7.2-to-v1.8.2" in snapshots[0].name
    assert "v1.7.3-to-v1.8.3" in snapshots[1].name
