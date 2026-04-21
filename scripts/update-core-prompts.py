#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def prepare_mirror(paths: Paths, origin_url: str, gitlab_url: str) -> bool:
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
    return run(["git", "-C", str(paths.mirror_path), "fetch", "--all", "--prune", "--tags"]).returncode == 0


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
    if not prepare_mirror(paths, origin_url, gitlab_url):
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


def accept_release(paths: Paths, *, assume_yes: bool) -> int:
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
    installed = read_first_line(paths.support_root / "VERSION") or "unknown"
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
    proc = subprocess.run([str(install_script), "--target", str(paths.home), "--allow-nonlocal-target"], cwd=mirror_path, env={**os.environ, "HOME": str(paths.home)})
    if proc.returncode != 0:
        return proc.returncode
    installed_after = read_first_line(paths.support_root / "VERSION")
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


def install_schedule(paths: Paths, hhmm: str) -> int:
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
if "$UPDATE_SCRIPT" --check-release >> "$log_file" 2>&1; then
  echo "[INFO] Scheduled Core-Prompts release check completed" >> "$LOG_DIR/scheduler.log"
else
  rc=$?
  echo "[WARN] Scheduled Core-Prompts release check failed (exit=$rc)" >> "$LOG_DIR/scheduler.log"
fi

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
            "--accept-release is the explicit install/apply step for a pending immutable release."
        ),
    )
    parser.add_argument("--support-root")
    parser.add_argument("--target-home")
    parser.add_argument("--check-release", action="store_true", help="Compare installed version vs latest release and update release-watch state")
    parser.add_argument("--accept-release", action="store_true", help="Refresh from the synced release mirror after confirmation")
    parser.add_argument("--schedule-daily", metavar="HH:MM", help="Run daily via cron; release check runs before normal update sync")
    parser.add_argument("--schedule-disable", action="store_true", help="Disable the cron schedule installed by --schedule-daily")
    parser.add_argument("--json", action="store_true", help="Print release-watch state as JSON for release modes")
    parser.add_argument("--yes", "-y", action="store_true", help="Assume yes for explicit acceptance or scheduled normal sync")
    parser.add_argument("deploy_args", nargs=argparse.REMAINDER, help="Arguments forwarded to bundled deploy-surfaces.sh during normal sync")
    args = parser.parse_args(argv)

    special_count = sum(bool(value) for value in (args.check_release, args.accept_release, args.schedule_daily, args.schedule_disable))
    if special_count > 1:
        parser.error("Use only one special mode at a time: --check-release, --accept-release, or schedule")
    home = Path(args.target_home or os.environ.get("HOME", "~")).expanduser().resolve()
    paths = Paths(support_root=resolve_support_root(args.support_root), home=home)
    if args.check_release:
        state = check_release(paths, notify_mode=True)
        print(json.dumps(state, indent=2) if args.json else render_state(state), end="")
        return 0
    if args.accept_release:
        rc = accept_release(paths, assume_yes=args.yes)
        if args.json:
            print(json.dumps(read_state(paths.state_file), indent=2))
        return rc
    if args.schedule_daily:
        return install_schedule(paths, args.schedule_daily)
    if args.schedule_disable:
        return disable_schedule()
    return default_sync(paths, args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
