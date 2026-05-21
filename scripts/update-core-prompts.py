#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


STATUSES = {"current", "pending-install", "remote-error", "remote-divergence"}
SCHEDULE_MARKER = "# CORE_PROMPTS_SCHEDULED_UPDATE"
DEFAULT_SNAPSHOT_RETENTION = 2


@dataclass(frozen=True)
class Paths:
    support_root: Path
    home: Path

    @property
    def state_root(self) -> Path:
        return self.home / ".core-prompts-state"

    @property
    def state_file(self) -> Path:
        return self.state_root / "release-watch.json"

    @property
    def snapshot_root(self) -> Path:
        return self.state_root / "snapshots"

    @property
    def cache_root(self) -> Path:
        return self.home / ".core-prompts-release-cache"

    @property
    def mirror_path(self) -> Path:
        return self.cache_root / "repo"

    @property
    def schedule_runner(self) -> Path:
        return self.home / ".local" / "bin" / "core-prompts-scheduled-update"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def run(command: list[str], *, cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)


def resolve_support_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_root = os.environ.get("CORE_PROMPTS_SUPPORT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def read_first_line(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").splitlines()[0].strip()


def read_release_source(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def read_state(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): "" if value is None else str(value) for key, value in data.items()}


def write_state(paths: Paths, *, installed_version: str, latest_version: str, pending_version: str, status: str, note: str, last_notified_at: str | None = None) -> dict[str, str]:
    previous = read_state(paths.state_file)
    doc = {
        "installed_version": installed_version,
        "latest_version": latest_version,
        "pending_version": pending_version,
        "mirror_path": str(paths.mirror_path),
        "last_checked_at": now_iso(),
        "last_notified_at": previous.get("last_notified_at", "") if last_notified_at is None else last_notified_at,
        "status": status if status in STATUSES else "remote-error",
        "note": note,
    }
    paths.state_file.parent.mkdir(parents=True, exist_ok=True)
    paths.state_file.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def render_state(doc: dict[str, str]) -> str:
    if not doc:
        return "Release watch state is not initialized.\n"
    lines = [
        "Release watch",
        "-------------",
        f"  Status    : {doc.get('status', 'unknown')}",
        f"  Installed : {doc.get('installed_version') or 'unknown'}",
        f"  Latest    : {doc.get('latest_version') or 'unknown'}",
        f"  Pending   : {doc.get('pending_version') or 'none'}",
        f"  Mirror    : {doc.get('mirror_path') or 'unset'}",
    ]
    if doc.get("note"):
        lines.append(f"  Note      : {doc['note']}")
    if doc.get("last_checked_at"):
        lines.append(f"  Checked   : {doc['last_checked_at']}")
    if doc.get("last_notified_at"):
        lines.append(f"  Notified  : {doc['last_notified_at']}")
    return "\n".join(lines) + "\n"


def safe_label(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value)
    return cleaned.strip("-") or "unknown"


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def installed_support_root(paths: Paths) -> Path:
    default = paths.home / ".core-prompts-updater"
    try:
        if paths.support_root.resolve().is_relative_to(paths.home.resolve()):
            return paths.support_root
    except FileNotFoundError:
        if paths.support_root.parent.resolve().is_relative_to(paths.home.resolve()):
            return paths.support_root
    return default


def managed_surface_targets(paths: Paths) -> list[Path]:
    plan_script = paths.support_root / "scripts" / "deploy-copy-plan.py"
    manifest = paths.support_root / ".meta" / "manifest.json"
    if not plan_script.is_file() or not manifest.is_file():
        return []
    proc = run(
        [
            sys.executable,
            str(plan_script),
            str(paths.support_root),
            str(paths.home),
            "gemini",
            "claude",
            "kiro",
            "codex",
            "--",
        ]
    )
    if proc.returncode != 0:
        return []
    targets: set[Path] = set()
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            targets.add(Path(parts[1]).expanduser().resolve())
    targets.add((paths.home / ".codex" / "config.toml").resolve())
    return sorted(targets)


def snapshot_file(snapshot_dir: Path, target: Path, logical_name: str, records: list[dict[str, str | bool]]) -> None:
    target = target.expanduser().resolve()
    digest = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:16]
    rel_snapshot = Path("files") / f"{safe_label(logical_name)}-{digest}"
    copy_target = snapshot_dir / rel_snapshot
    record: dict[str, str | bool] = {
        "kind": "file",
        "target": str(target),
        "snapshot": str(rel_snapshot),
        "existed": target.exists() or target.is_symlink(),
    }
    if record["existed"]:
        copy_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, copy_target, follow_symlinks=False)
    records.append(record)


def snapshot_dir_path(snapshot_dir: Path, target: Path, logical_name: str, records: list[dict[str, str | bool]]) -> None:
    target = target.expanduser().resolve()
    rel_snapshot = Path("dirs") / safe_label(logical_name)
    copy_target = snapshot_dir / rel_snapshot
    record: dict[str, str | bool] = {
        "kind": "dir",
        "target": str(target),
        "snapshot": str(rel_snapshot),
        "existed": target.exists(),
    }
    if record["existed"]:
        if target.is_dir() and not target.is_symlink():
            shutil.copytree(target, copy_target, symlinks=True)
        else:
            copy_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, copy_target, follow_symlinks=False)
            record["kind"] = "file"
    records.append(record)


def prune_snapshots(paths: Paths, keep: int) -> None:
    if keep <= 0 or not paths.snapshot_root.is_dir():
        return
    snapshots = sorted(path for path in paths.snapshot_root.iterdir() if path.is_dir())
    for snapshot in snapshots[:-keep]:
        if snapshot.resolve().is_relative_to(paths.snapshot_root.resolve()):
            shutil.rmtree(snapshot)


def create_snapshot(paths: Paths, *, installed_version: str, target_version: str, retention: int) -> Path:
    created = now_iso()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_snapshot_id = f"{stamp}-{safe_label(installed_version)}-to-{safe_label(target_version)}"
    snapshot_id = base_snapshot_id
    snapshot_dir = paths.snapshot_root / snapshot_id
    suffix = 2
    while snapshot_dir.exists():
        snapshot_id = f"{base_snapshot_id}-{suffix}"
        snapshot_dir = paths.snapshot_root / snapshot_id
        suffix += 1
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, str | bool]] = []

    support = installed_support_root(paths)
    snapshot_dir_path(snapshot_dir, support, "core-prompts-updater", records)
    snapshot_file(snapshot_dir, paths.state_file, "release-watch", records)
    for target in managed_surface_targets(paths):
        snapshot_file(snapshot_dir, target, "managed-surface", records)

    manifest = {
        "id": snapshot_id,
        "created_at": created,
        "installed_version": installed_version,
        "target_version": target_version,
        "home": str(paths.home),
        "support_root": str(support),
        "paths": records,
    }
    (snapshot_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    prune_snapshots(paths, retention)
    return snapshot_dir


def read_snapshot_manifest(snapshot_dir: Path) -> dict[str, object]:
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def snapshot_dirs(paths: Paths) -> list[Path]:
    if not paths.snapshot_root.is_dir():
        return []
    return sorted(path for path in paths.snapshot_root.iterdir() if path.is_dir() and (path / "manifest.json").is_file())


def list_snapshots(paths: Paths, *, as_json: bool) -> int:
    snapshots = []
    for snapshot in snapshot_dirs(paths):
        manifest = read_snapshot_manifest(snapshot)
        snapshots.append(
            {
                "id": manifest.get("id", snapshot.name),
                "created_at": manifest.get("created_at", ""),
                "installed_version": manifest.get("installed_version", ""),
                "target_version": manifest.get("target_version", ""),
                "path": str(snapshot),
            }
        )
    if as_json:
        print(json.dumps(snapshots, indent=2))
        return 0
    if not snapshots:
        print("No Core-Prompts rollback snapshots found.")
        return 0
    print("Core-Prompts rollback snapshots")
    print("--------------------------------")
    for item in snapshots:
        print(f"  {item['id']}  {item['installed_version']} -> {item['target_version']}  {item['created_at']}")
    return 0


def resolve_snapshot(paths: Paths, selector: str) -> Path | None:
    snapshots = snapshot_dirs(paths)
    if not snapshots:
        return None
    if selector in {"", "previous", "latest"}:
        return snapshots[-1]
    for snapshot in snapshots:
        if snapshot.name == selector:
            return snapshot
    return None


def restore_snapshot(paths: Paths, selector: str) -> int:
    snapshot = resolve_snapshot(paths, selector)
    if snapshot is None:
        print(f"No Core-Prompts rollback snapshot found for selector: {selector or 'previous'}", file=sys.stderr)
        return 1
    manifest = read_snapshot_manifest(snapshot)
    records = manifest.get("paths", [])
    if not isinstance(records, list):
        print(f"Invalid rollback snapshot manifest: {snapshot / 'manifest.json'}", file=sys.stderr)
        return 1
    for raw_record in records:
        if not isinstance(raw_record, dict):
            continue
        target = Path(str(raw_record.get("target", ""))).expanduser()
        if not target:
            continue
        try:
            if not target.resolve().is_relative_to(paths.home.resolve()):
                print(f"Refusing to restore outside target home: {target}", file=sys.stderr)
                return 1
        except FileNotFoundError:
            if not target.parent.resolve().is_relative_to(paths.home.resolve()):
                print(f"Refusing to restore outside target home: {target}", file=sys.stderr)
                return 1
        source = snapshot / str(raw_record.get("snapshot", ""))
        existed = bool(raw_record.get("existed"))
        kind = str(raw_record.get("kind", "file"))
        if not existed:
            remove_path(target)
            continue
        if not source.exists() and not source.is_symlink():
            print(f"Rollback snapshot is missing stored path: {source}", file=sys.stderr)
            return 1
        remove_path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if kind == "dir" and source.is_dir() and not source.is_symlink():
            shutil.copytree(source, target, symlinks=True)
        else:
            shutil.copy2(source, target, follow_symlinks=False)
    print(f"Restored Core-Prompts snapshot {manifest.get('id', snapshot.name)}.")
    return 0


def latest_tag_ref_for_url(repo_url: str) -> tuple[str, str]:
    if not repo_url:
        return "", ""
    proc = run(["git", "ls-remote", "--tags", "--refs", repo_url, "v*"])
    if proc.returncode != 0:
        return "", ""
    tags: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith("refs/tags/"):
            tags.append((parts[1].removeprefix("refs/tags/"), parts[0]))
    if not tags:
        return "", ""
    try:
        tag_names = [tag for tag, _ in tags]
        sorted_tags = subprocess.run(["sort", "-V"], input="\n".join(tag_names) + "\n", stdout=subprocess.PIPE, text=True, check=True).stdout.splitlines()
        latest = sorted_tags[-1] if sorted_tags else ""
    except Exception:
        latest = sorted(tag for tag, _ in tags)[-1]
    refs = dict(tags)
    return latest, refs.get(latest, "")


def latest_tag_for_url(repo_url: str) -> str:
    return latest_tag_ref_for_url(repo_url)[0]


def tag_is_newer(candidate: str, installed: str) -> bool:
    if not candidate or not installed or candidate == installed:
        return False
    try:
        ordered = subprocess.run(
            ["sort", "-V"],
            input=f"{installed}\n{candidate}\n",
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        ).stdout.splitlines()
        return bool(ordered and ordered[-1] == candidate)
    except Exception:
        return candidate > installed


def prepare_mirror(paths: Paths, origin_url: str, gitlab_url: str, release_tag: str) -> bool:
    paths.cache_root.mkdir(parents=True, exist_ok=True)
    if not (paths.mirror_path / ".git").is_dir():
        if paths.mirror_path.exists():
            if paths.mirror_path.resolve().is_relative_to(paths.cache_root.resolve()):
                shutil.rmtree(paths.mirror_path)
            else:
                return False
        proc = run(["git", "clone", "--quiet", origin_url, str(paths.mirror_path)])
        if proc.returncode != 0:
            return False
    if run(["git", "-C", str(paths.mirror_path), "remote", "set-url", "origin", origin_url]).returncode != 0:
        return False
    if run(["git", "-C", str(paths.mirror_path), "remote", "get-url", "gitlab"]).returncode == 0:
        if run(["git", "-C", str(paths.mirror_path), "remote", "set-url", "gitlab", gitlab_url]).returncode != 0:
            return False
    else:
        if run(["git", "-C", str(paths.mirror_path), "remote", "add", "gitlab", gitlab_url]).returncode != 0:
            return False
    if run(["git", "-C", str(paths.mirror_path), "fetch", "--all", "--prune", "--no-tags"]).returncode != 0:
        return False
    if release_tag:
        refspec = f"+refs/tags/{release_tag}:refs/tags/{release_tag}"
        if run(["git", "-C", str(paths.mirror_path), "fetch", "origin", refspec]).returncode != 0:
            return False
    return True


def checkout_mirror(paths: Paths, tag: str) -> bool:
    return run(["git", "-C", str(paths.mirror_path), "checkout", "--detach", tag]).returncode == 0


def should_notify(paths: Paths, pending_version: str, status: str) -> bool:
    state = read_state(paths.state_file)
    previous_key = state.get("pending_version") if status == "pending-install" else state.get("status")
    current_key = pending_version if status == "pending-install" else status
    if previous_key != current_key:
        return True
    return state.get("last_notified_at") != today()


def notify(title: str, message: str) -> bool:
    if platform.system() != "Darwin" or not shutil.which("osascript"):
        return False
    script = "display notification item 1 of argv with title item 2 of argv"
    proc = run(["osascript", "-e", script, message, title])
    return proc.returncode == 0


def check_release(paths: Paths, *, notify_mode: bool) -> dict[str, str]:
    installed_version = read_first_line(paths.support_root / "VERSION")
    source = read_release_source(paths.support_root / "RELEASE_SOURCE.env")
    origin_url = source.get("ORIGIN_URL", "")
    gitlab_url = source.get("GITLAB_URL", "")
    if not origin_url or not gitlab_url:
        return write_state(paths, installed_version=installed_version, latest_version="", pending_version="", status="remote-error", note="Missing installed release source metadata")

    latest_origin, origin_ref = latest_tag_ref_for_url(origin_url)
    latest_gitlab, gitlab_ref = latest_tag_ref_for_url(gitlab_url)
    if not latest_origin or not latest_gitlab:
        return write_state(paths, installed_version=installed_version, latest_version="", pending_version="", status="remote-error", note="Unable to resolve latest release tag from both remotes")
    if latest_origin != latest_gitlab or origin_ref != gitlab_ref:
        note = f"Remote latest tags differ: origin={latest_origin}, gitlab={latest_gitlab}"
        if latest_origin == latest_gitlab:
            note = f"Remote latest tag objects differ for {latest_origin}: origin={origin_ref}, gitlab={gitlab_ref}"
        last_notified = None
        if notify_mode and should_notify(paths, latest_origin, "remote-divergence"):
            if notify("Core-Prompts Release Divergence", note):
                last_notified = today()
        return write_state(paths, installed_version=installed_version, latest_version=latest_origin, pending_version="", status="remote-divergence", note=note, last_notified_at=last_notified)

    latest_version = latest_origin
    if not prepare_mirror(paths, origin_url, gitlab_url, latest_version):
        return write_state(paths, installed_version=installed_version, latest_version=latest_version, pending_version="", status="remote-error", note="Failed to prepare dedicated release mirror")
    if not checkout_mirror(paths, latest_version):
        return write_state(paths, installed_version=installed_version, latest_version=latest_version, pending_version="", status="remote-error", note=f"Failed to check out {latest_version} in dedicated release mirror")

    if tag_is_newer(latest_version, installed_version):
        note = "Run ~/update_core_prompts.sh --accept-release to refresh the installed bundle"
        last_notified = None
        if notify_mode and should_notify(paths, latest_version, "pending-install"):
            message = f"Install {latest_version} to refresh Core-Prompts surfaces (installed: {installed_version})."
            if notify("Core-Prompts Release Available", message):
                last_notified = today()
        return write_state(paths, installed_version=installed_version, latest_version=latest_version, pending_version=latest_version, status="pending-install", note=note, last_notified_at=last_notified)

    return write_state(paths, installed_version=installed_version, latest_version=latest_version, pending_version="", status="current", note="Installed standalone bundle matches the latest release")


def pending_warning(paths: Paths) -> str:
    state = read_state(paths.state_file)
    if state.get("status") != "pending-install":
        return ""
    version = state.get("pending_version") or state.get("latest_version") or "unknown"
    return (
        "\nRelease Watch Warning\n"
        "---------------------\n"
        f"  A newer Core-Prompts release is available: {version}\n"
        "  Normal deploy/update sync can continue, but newer bundled Core-Prompts changes require:\n"
        "    ~/update_core_prompts.sh --accept-release\n\n"
    )


def default_sync(paths: Paths, args: argparse.Namespace) -> int:
    warning = pending_warning(paths)
    if warning:
        print(warning, file=sys.stderr, end="")
    deploy = paths.support_root / "scripts" / "deploy-surfaces.sh"
    if not deploy.is_file():
        print(f"Missing bundled deploy script: {deploy}", file=sys.stderr)
        return 1
    command = [str(deploy), "--target", str(paths.home), "--allow-nonlocal-target", *args.deploy_args]
    proc = subprocess.run(command, cwd=paths.support_root)
    return proc.returncode


def accept_release(paths: Paths, *, assume_yes: bool, snapshot_retention: int = DEFAULT_SNAPSHOT_RETENTION) -> int:
    if not paths.state_file.is_file():
        check_release(paths, notify_mode=False)
    state = read_state(paths.state_file)
    pending = state.get("pending_version", "")
    if state.get("status") != "pending-install" or not pending:
        print("No pending Core-Prompts release requires acceptance.", file=sys.stderr)
        return 0
    mirror_path = Path(state.get("mirror_path") or paths.mirror_path)
    install_script = mirror_path / "scripts" / "install-local.sh"
    if not install_script.is_file():
        print(f"Release mirror install script is unavailable: {install_script}", file=sys.stderr)
        return 1
    support = installed_support_root(paths)
    installed = read_first_line(support / "VERSION") or "unknown"
    print("\nPending Core-Prompts Release", file=sys.stderr)
    print("----------------------------", file=sys.stderr)
    print(f"  Installed : {installed}", file=sys.stderr)
    print(f"  Pending   : {pending}", file=sys.stderr)
    print(f"  Mirror    : {mirror_path}\n", file=sys.stderr)
    approved = assume_yes
    if not approved:
        answer = input(f"Refresh the installed standalone bundle from {pending} now? [y/N] ").strip().lower()
        approved = answer in {"y", "yes"}
    if not approved:
        print("Release acceptance declined; pending install remains queued.", file=sys.stderr)
        return 0
    snapshot = create_snapshot(paths, installed_version=installed, target_version=pending, retention=snapshot_retention)
    print(f"Snapshot saved: {snapshot}", file=sys.stderr)
    proc = subprocess.run([str(install_script), "--target", str(paths.home), "--allow-nonlocal-target"], cwd=mirror_path, env={**os.environ, "HOME": str(paths.home)})
    if proc.returncode != 0:
        return proc.returncode
    installed_after = read_first_line(support / "VERSION")
    if installed_after == pending:
        write_state(
            paths,
            installed_version=installed_after,
            latest_version=pending,
            pending_version="",
            status="current",
            note="Accepted pending Core-Prompts release",
        )
        print(f"Accepted Core-Prompts release {pending}.", file=sys.stderr)
        return 0
    print(f"Core-Prompts install completed, but installed version is {installed_after or 'unknown'} instead of {pending}.", file=sys.stderr)
    return 1


def auto_accept_release(paths: Paths, *, snapshot_retention: int) -> int:
    state = check_release(paths, notify_mode=False)
    if state.get("status") != "pending-install":
        print(render_state(state), end="")
        return 0
    return accept_release(paths, assume_yes=True, snapshot_retention=snapshot_retention)


def install_schedule(paths: Paths, hhmm: str, *, notify_only: bool, snapshot_retention: int) -> int:
    if not hhmm or len(hhmm) != 5 or hhmm[2] != ":":
        print("Invalid time format for --schedule-daily. Expected HH:MM.", file=sys.stderr)
        return 1
    hour, minute = hhmm.split(":", 1)
    if not (hour.isdigit() and minute.isdigit() and 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
        print("Invalid time format for --schedule-daily. Expected HH:MM.", file=sys.stderr)
        return 1
    paths.schedule_runner.parent.mkdir(parents=True, exist_ok=True)
    runner = f"""#!/usr/bin/env bash
set -euo pipefail

UPDATE_SCRIPT="${{UPDATE_SCRIPT:-$HOME/update_core_prompts.sh}}"
STATE_HOME="$HOME/.core-prompts-state"
LOCK_DIR="$STATE_HOME/schedule.lock"
LOG_DIR="$STATE_HOME/schedule/logs"

mkdir -p "$LOG_DIR"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[WARN] Skipping scheduled Core-Prompts update: another run is active" >> "$LOG_DIR/scheduler.log"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" >/dev/null 2>&1 || true' EXIT

log_file="$LOG_DIR/update-$(date +%Y%m%d_%H%M%S).log"
release_check_ok=0
if "$UPDATE_SCRIPT" --check-release >> "$log_file" 2>&1; then
  release_check_ok=1
  echo "[INFO] Scheduled Core-Prompts release check completed" >> "$LOG_DIR/scheduler.log"
else
  rc=$?
  echo "[WARN] Scheduled Core-Prompts release check failed (exit=$rc)" >> "$LOG_DIR/scheduler.log"
fi

"""
    if not notify_only:
        runner += f"""if [[ "$release_check_ok" -eq 1 ]]; then
  if "$UPDATE_SCRIPT" --accept-release --yes --snapshot-retention {snapshot_retention} >> "$log_file" 2>&1; then
    echo "[INFO] Scheduled Core-Prompts release acceptance completed" >> "$LOG_DIR/scheduler.log"
  else
    rc=$?
    echo "[ERROR] Scheduled Core-Prompts release acceptance failed (exit=$rc)" >> "$LOG_DIR/scheduler.log"
    exit "$rc"
  fi
else
  echo "[WARN] Skipping scheduled Core-Prompts release acceptance because release check failed" >> "$LOG_DIR/scheduler.log"
fi

"""
    runner += """\
if "$UPDATE_SCRIPT" --yes >> "$log_file" 2>&1; then
  echo "[INFO] Scheduled Core-Prompts update completed" >> "$LOG_DIR/scheduler.log"
else
  rc=$?
  echo "[ERROR] Scheduled Core-Prompts update failed (exit=$rc)" >> "$LOG_DIR/scheduler.log"
  exit "$rc"
fi
"""
    paths.schedule_runner.write_text(runner, encoding="utf-8")
    paths.schedule_runner.chmod(0o755)
    current = run(["crontab", "-l"]).stdout if shutil.which("crontab") else ""
    lines = [line for line in current.splitlines() if SCHEDULE_MARKER not in line]
    lines.append(f"{int(minute)} {int(hour)} * * * \"{paths.schedule_runner}\" {SCHEDULE_MARKER}")
    if shutil.which("crontab"):
        subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=False)
    print(f"Scheduled Core-Prompts update runner: {paths.schedule_runner}")
    return 0


def disable_schedule() -> int:
    if not shutil.which("crontab"):
        return 0
    current = run(["crontab", "-l"]).stdout
    lines = [line for line in current.splitlines() if SCHEDULE_MARKER not in line]
    subprocess.run(["crontab", "-"], input="\n".join(lines) + ("\n" if lines else ""), text=True, check=False)
    print("Disabled scheduled Core-Prompts updates.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Sync installed Core-Prompts surfaces and manage release-watch state.",
        epilog=(
            "--check-release checks only and never auto-installs. "
            "Scheduled updates auto-accept valid releases by default; use --notify-only to keep scheduling check-only. "
            "--rollback previous restores the latest pre-release snapshot."
        ),
    )
    parser.add_argument("--support-root")
    parser.add_argument("--target-home")
    parser.add_argument("--check-release", action="store_true", help="Compare installed version vs latest release and update release-watch state")
    parser.add_argument("--accept-release", action="store_true", help="Refresh from the synced release mirror after confirmation")
    parser.add_argument("--auto-accept-release", action="store_true", help="Check for a release and auto-accept a valid pending release")
    parser.add_argument("--rollback", nargs="?", const="previous", metavar="SNAPSHOT_ID|previous", help="Restore a pre-release snapshot")
    parser.add_argument("--list-snapshots", action="store_true", help="List available rollback snapshots")
    parser.add_argument("--snapshot-retention", type=int, default=DEFAULT_SNAPSHOT_RETENTION, help=f"Number of rollback snapshots to retain. Default: {DEFAULT_SNAPSHOT_RETENTION}")
    parser.add_argument("--schedule-daily", metavar="HH:MM", help="Run daily via cron; release check auto-accepts valid releases before normal sync")
    parser.add_argument("--notify-only", action="store_true", help="With --schedule-daily, check for releases without auto-accepting them")
    parser.add_argument("--schedule-disable", action="store_true", help="Disable the cron schedule installed by --schedule-daily")
    parser.add_argument("--json", action="store_true", help="Print release-watch state as JSON for release modes")
    parser.add_argument("--yes", "-y", action="store_true", help="Assume yes for explicit acceptance or scheduled normal sync")
    parser.add_argument("deploy_args", nargs=argparse.REMAINDER, help="Arguments forwarded to bundled deploy-surfaces.sh during normal sync")
    args = parser.parse_args(argv)

    if args.snapshot_retention < 1:
        parser.error("--snapshot-retention must be at least 1")
    if args.notify_only and not args.schedule_daily:
        parser.error("--notify-only can only be used with --schedule-daily")

    special_count = sum(
        bool(value)
        for value in (
            args.check_release,
            args.accept_release,
            args.auto_accept_release,
            args.rollback is not None,
            args.list_snapshots,
            args.schedule_daily,
            args.schedule_disable,
        )
    )
    if special_count > 1:
        parser.error("Use only one special mode at a time")
    home = Path(args.target_home or os.environ.get("HOME", "~")).expanduser().resolve()
    support_root = resolve_support_root(args.support_root)
    release_mode = args.check_release or args.accept_release or args.auto_accept_release
    installed_bundle = home / ".core-prompts-updater"
    if not args.support_root and release_mode and (installed_bundle / "VERSION").is_file():
        support_root = installed_bundle
    paths = Paths(support_root=support_root, home=home)
    if args.check_release:
        state = check_release(paths, notify_mode=True)
        print(json.dumps(state, indent=2) if args.json else render_state(state), end="")
        return 0
    if args.accept_release:
        rc = accept_release(paths, assume_yes=args.yes, snapshot_retention=args.snapshot_retention)
        if args.json:
            print(json.dumps(read_state(paths.state_file), indent=2))
        return rc
    if args.auto_accept_release:
        rc = auto_accept_release(paths, snapshot_retention=args.snapshot_retention)
        if args.json:
            print(json.dumps(read_state(paths.state_file), indent=2))
        return rc
    if args.rollback is not None:
        return restore_snapshot(paths, args.rollback)
    if args.list_snapshots:
        return list_snapshots(paths, as_json=args.json)
    if args.schedule_daily:
        return install_schedule(paths, args.schedule_daily, notify_only=args.notify_only, snapshot_retention=args.snapshot_retention)
    if args.schedule_disable:
        return disable_schedule()
    return default_sync(paths, args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
