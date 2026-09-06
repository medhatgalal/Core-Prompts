#!/usr/bin/env python3
"""Inventory known agent-tool backup and temporary-file categories."""

from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_USAGE = 2
EXIT_ENVIRONMENT = 3
EXIT_CONFIRMATION_REQUIRED = 4
EXIT_ACTION_FAILED = 5
EXIT_STALE_SELECTION = 6

HELP = """Usage: bash resources/cruft-report [OPTIONS]

Inventory known backup and temporary-file categories. The default is read-only.
This tool never prompts. Cleanup requires a reviewed dry-run selection digest.

Options:
  --json                    Emit one JSON object to stdout; diagnostics stay on stderr.
  --dry-run                 Preview one --trash category and emit its selection digest.
  --trash CATEGORY          Select exactly one explicit category for cleanup.
  --confirm                 Authorize the selected --trash action; never prompts.
  --expect-sha256 DIGEST    Require the exact digest emitted by the reviewed dry-run.
  -h, --help                Show this help.

Categories:
  dotfiles-bak              Timestamped backups under agent/tool homes.
  kiro-agent-bak            Kiro agent JSON backups.
  cli-state-bak             Codex CLI state backups and interrupted writes.
  beads-temp                Beads export/atomic-write temporary files.
  worktree-temp             Beads temporary files in abandoned Codex worktrees.

Exit codes:
  0  success, clean no-op, report, or dry-run preview
  1  unexpected internal failure
  2  usage error, conflicting flags, or unknown category
  3  required command or configured root is unavailable
  4  cleanup requested without --confirm and the reviewed digest
  5  one or more requested Trash moves failed
  6  selected files changed since the reviewed dry-run

Examples:
  bash resources/cruft-report
  bash resources/cruft-report --json
  bash resources/cruft-report --json --dry-run --trash dotfiles-bak
  bash resources/cruft-report --json --trash dotfiles-bak --confirm \\
    --expect-sha256 <digest-from-dry-run>
"""


@dataclass(frozen=True)
class Options:
    json_output: bool = False
    dry_run: bool = False
    trash_category: str | None = None
    confirm: bool = False
    expected_sha256: str | None = None


@dataclass(frozen=True)
class Category:
    roots: tuple[str, ...]
    max_depth: int
    patterns: tuple[str, ...]
    writer: str


@dataclass(frozen=True)
class FileRecord:
    path: Path
    display_path: str
    size: int
    mtime_ns: int
    device: int
    inode: int
    content_sha256: str

    def digest_payload(self) -> dict[str, object]:
        return {
            "path": self.display_path,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "device": self.device,
            "inode": self.inode,
            "content_sha256": self.content_sha256,
        }


CATEGORIES: dict[str, Category] = {
    "dotfiles-bak": Category(
        roots=(".agents", ".claude", ".codex/skills", ".local/bin"),
        max_depth=4,
        patterns=("*.bak.[0-9]*",),
        writer="dotfiles install.sh (no retention)",
    ),
    "kiro-agent-bak": Category(
        roots=(".kiro/agents",),
        max_depth=1,
        patterns=("*.json.bak*",),
        writer="UNATTRIBUTED",
    ),
    "cli-state-bak": Category(
        roots=(".codex",),
        max_depth=1,
        patterns=("*.json.bak", "*.bak.tmp-*"),
        writer="codex CLI self-managed",
    ),
    "beads-temp": Category(
        roots=("Desktop/AI_Repos/EngOS/.beads",),
        max_depth=1,
        patterns=(".~*", "*.tmp"),
        writer="beads export/atomic write",
    ),
    "worktree-temp": Category(
        roots=(".codex/worktrees",),
        max_depth=3,
        patterns=("*.jsonl.XXXXXX.tmp",),
        writer="abandoned test worktrees",
    ),
}


def diagnostic(message: str) -> None:
    print(f"cruft-report: {message}", file=sys.stderr)


def fail(message: str, exit_code: int, status: str, json_output: bool) -> NoReturn:
    diagnostic(message)
    if json_output:
        print(
            json.dumps(
                {
                    "schema_version": "cruft-report.v1",
                    "status": status,
                    "error": message,
                    "exit_code": exit_code,
                },
                sort_keys=True,
            )
        )
    raise SystemExit(exit_code)


def parse_args(argv: list[str]) -> Options:
    json_requested = "--json" in argv
    if argv in (["--help"], ["-h"]):
        print(HELP, end="")
        raise SystemExit(EXIT_OK)
    if "--help" in argv or "-h" in argv:
        fail("--help cannot be combined with other options", EXIT_USAGE, "usage_error", json_requested)

    values: dict[str, object] = {
        "json_output": False,
        "dry_run": False,
        "trash_category": None,
        "confirm": False,
        "expected_sha256": None,
    }
    seen: set[str] = set()
    index = 0
    while index < len(argv):
        option = argv[index]
        if option in {"--json", "--dry-run", "--confirm"}:
            if option in seen:
                fail(f"option may be supplied only once: {option}", EXIT_USAGE, "usage_error", json_requested)
            seen.add(option)
            key = {"--json": "json_output", "--dry-run": "dry_run", "--confirm": "confirm"}[option]
            values[key] = True
            index += 1
            continue
        if option in {"--trash", "--expect-sha256"}:
            if option in seen:
                fail(f"option may be supplied only once: {option}", EXIT_USAGE, "usage_error", json_requested)
            if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
                fail(f"{option} requires a value", EXIT_USAGE, "usage_error", json_requested)
            seen.add(option)
            key = "trash_category" if option == "--trash" else "expected_sha256"
            values[key] = argv[index + 1]
            index += 2
            continue
        fail(f"unknown argument: {option}", EXIT_USAGE, "usage_error", json_requested)

    options = Options(**values)  # type: ignore[arg-type]
    if options.trash_category is not None and options.trash_category not in CATEGORIES:
        fail(f"unknown category: {options.trash_category}", EXIT_USAGE, "usage_error", options.json_output)
    if options.dry_run and options.trash_category is None:
        fail("--dry-run requires --trash CATEGORY", EXIT_USAGE, "usage_error", options.json_output)
    if options.confirm and options.trash_category is None:
        fail("--confirm requires --trash CATEGORY", EXIT_USAGE, "usage_error", options.json_output)
    if options.expected_sha256 is not None and not options.confirm:
        fail("--expect-sha256 requires --confirm", EXIT_USAGE, "usage_error", options.json_output)
    if options.dry_run and (options.confirm or options.expected_sha256 is not None):
        fail("--dry-run cannot be combined with confirmation options", EXIT_USAGE, "usage_error", options.json_output)
    if options.expected_sha256 is not None and (
        len(options.expected_sha256) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in options.expected_sha256)
    ):
        fail("--expect-sha256 requires a 64-character hexadecimal digest", EXIT_USAGE, "usage_error", options.json_output)
    return options


def configured_home(json_output: bool) -> Path:
    value = os.environ.get("HOME")
    if not value:
        fail("HOME is unset", EXIT_ENVIRONMENT, "environment_error", json_output)
    home = Path(value)
    if not home.is_dir():
        fail(f"HOME is not an accessible directory: {home}", EXIT_ENVIRONMENT, "environment_error", json_output)
    return home.resolve()


def matches(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def candidate_paths(home: Path, category_name: str, json_output: bool) -> list[Path]:
    category = CATEGORIES[category_name]
    candidates: list[Path] = []
    scan_errors: list[str] = []

    def record_error(error: OSError) -> None:
        scan_errors.append(str(error))

    for relative_root in category.roots:
        root = home / relative_root
        if not root.exists():
            continue
        if not root.is_dir():
            scan_errors.append(f"configured root is not a directory: {root}")
            continue
        for directory, subdirectories, filenames in os.walk(root, onerror=record_error, followlinks=False):
            directory_path = Path(directory)
            directory_depth = len(directory_path.relative_to(root).parts)
            if directory_depth >= category.max_depth:
                subdirectories.clear()
            if directory_depth + 1 > category.max_depth:
                continue
            for filename in filenames:
                if not matches(filename, category.patterns):
                    continue
                candidate = directory_path / filename
                try:
                    mode = candidate.lstat().st_mode
                except OSError as error:
                    scan_errors.append(str(error))
                    continue
                if stat.S_ISREG(mode):
                    candidates.append(candidate)
    if scan_errors:
        fail(
            "cannot inventory configured roots: " + "; ".join(sorted(scan_errors)),
            EXIT_ENVIRONMENT,
            "environment_error",
            json_output,
        )
    return sorted(set(candidates), key=lambda item: os.fsencode(str(item)))


def display_path(path: Path, home: Path) -> str:
    try:
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        return str(path)


def snapshot_file(path: Path, home: Path) -> FileRecord:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"selected path is no longer a regular file: {path}")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        raise OSError(f"selected file changed while it was inspected: {path}")
    return FileRecord(
        path=path,
        display_path=display_path(path, home),
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        device=after.st_dev,
        inode=after.st_ino,
        content_sha256=digest.hexdigest(),
    )


def collect_records(home: Path, category_name: str, json_output: bool) -> list[FileRecord]:
    try:
        return [snapshot_file(path, home) for path in candidate_paths(home, category_name, json_output)]
    except OSError as error:
        fail(str(error), EXIT_ENVIRONMENT, "environment_error", json_output)


def selection_digest(records: list[FileRecord]) -> str:
    encoded = json.dumps(
        [record.digest_payload() for record in records],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def newest_at(records: list[FileRecord]) -> str:
    if not records:
        return ""
    newest_ns = max(record.mtime_ns for record in records)
    return dt.datetime.fromtimestamp(newest_ns / 1_000_000_000, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sampled_paths(records: list[FileRecord]) -> list[str]:
    return [record.display_path for record in records[:10]]


def emit_report(home: Path, options: Options) -> None:
    reports: list[dict[str, object]] = []
    total_count = 0
    for name, category in CATEGORIES.items():
        records = collect_records(home, name, options.json_output)
        total_count += len(records)
        reports.append(
            {
                "name": name,
                "count": len(records),
                "size_bytes": sum(record.size for record in records),
                "newest_at": newest_at(records),
                "writer": category.writer,
                "sample": sampled_paths(records),
                "truncated": max(0, len(records) - 10),
            }
        )
    if options.json_output:
        print(
            json.dumps(
                {
                    "schema_version": "cruft-report.v1",
                    "status": "ok",
                    "mode": "report",
                    "read_only": True,
                    "categories": reports,
                    "total_count": total_count,
                },
                sort_keys=True,
            )
        )
        return
    print(f"{'CATEGORY':16} {'COUNT':>7} {'BYTES':>12}  {'NEWEST (UTC)':20}  WRITER")
    print(f"{'-' * 16} {'-' * 7} {'-' * 12}  {'-' * 20}  {'-' * 6}")
    for report in reports:
        print(
            f"{report['name']:16} {report['count']:7} {report['size_bytes']:12}  "
            f"{report['newest_at'] or '-':20}  {report['writer']}"
        )
    print(f"\ntotal tracked cruft files: {total_count}")
    print("preview cleanup: bash resources/cruft-report --dry-run --trash <category>")


def emit_selection(status: str, mode: str, category: str, records: list[FileRecord]) -> None:
    print(
        json.dumps(
            {
                "schema_version": "cruft-report.v1",
                "status": status,
                "mode": mode,
                "category": category,
                "count": len(records),
                "selection_sha256": selection_digest(records),
                "files": sampled_paths(records),
                "truncated": max(0, len(records) - 10),
            },
            sort_keys=True,
        )
    )


def run_action(home: Path, options: Options) -> None:
    assert options.trash_category is not None
    records = collect_records(home, options.trash_category, options.json_output)
    current_digest = selection_digest(records)
    if options.dry_run:
        if options.json_output:
            emit_selection("dry_run", "dry_run", options.trash_category, records)
        else:
            print(f"DRY RUN: would move {len(records)} file(s) from {options.trash_category} to Trash")
            print(f"selection_sha256: {current_digest}")
            for record in records[:10]:
                print(f"  {record.display_path}")
        return
    if not options.confirm or options.expected_sha256 is None:
        if options.json_output:
            emit_selection("confirmation_required", "trash", options.trash_category, records)
        diagnostic("cleanup requires --confirm and --expect-sha256 from a reviewed dry-run")
        raise SystemExit(EXIT_CONFIRMATION_REQUIRED)
    if current_digest.lower() != options.expected_sha256.lower():
        fail("selected files changed since the reviewed dry-run", EXIT_STALE_SELECTION, "stale_selection", options.json_output)
    if not records:
        payload = {
            "schema_version": "cruft-report.v1",
            "status": "no_op",
            "mode": "trash",
            "category": options.trash_category,
            "selection_sha256": current_digest,
            "moved": 0,
            "failed": 0,
            "failed_files": [],
        }
        if options.json_output:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"no_op: moved=0 failed=0 category={options.trash_category}")
        return
    trash_command = shutil.which("trash")
    if trash_command is None:
        fail("required command is unavailable: trash", EXIT_ENVIRONMENT, "environment_error", options.json_output)

    revalidated = collect_records(home, options.trash_category, options.json_output)
    if selection_digest(revalidated) != current_digest:
        fail("selected files changed immediately before cleanup", EXIT_STALE_SELECTION, "stale_selection", options.json_output)

    moved = 0
    failed_paths: list[str] = []
    for expected in records:
        try:
            current = snapshot_file(expected.path, home)
        except OSError:
            failed_paths.append(expected.display_path)
            continue
        if current.digest_payload() != expected.digest_payload():
            failed_paths.append(expected.display_path)
            continue
        result = subprocess.run(
            [trash_command, str(expected.path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            moved += 1
        else:
            failed_paths.append(expected.display_path)
            if result.stderr.strip():
                diagnostic(f"trash failed for {expected.display_path}: {result.stderr.strip()}")

    status = "moved" if not failed_paths else "partial_failure"
    diagnostic(f"moved {moved} file(s) from {options.trash_category}; {len(failed_paths)} failed")
    payload = {
        "schema_version": "cruft-report.v1",
        "status": status,
        "mode": "trash",
        "category": options.trash_category,
        "selection_sha256": current_digest,
        "moved": moved,
        "failed": len(failed_paths),
        "failed_files": failed_paths,
    }
    if options.json_output:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"{status}: moved={moved} failed={len(failed_paths)} category={options.trash_category}")
    if failed_paths:
        raise SystemExit(EXIT_ACTION_FAILED)


def main(argv: list[str]) -> int:
    options = parse_args(argv)
    home = configured_home(options.json_output)
    if options.trash_category is None:
        emit_report(home, options)
    else:
        run_action(home, options)
    return EXIT_OK


if __name__ == "__main__":
    json_requested = "--json" in sys.argv[1:]
    try:
        raise SystemExit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as error:  # pragma: no cover - last-resort agent-facing contract
        fail(str(error), EXIT_UNEXPECTED, "internal_error", json_requested)
