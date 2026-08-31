#!/usr/bin/env python3
"""Resolve and safely write Analyze Context task state."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, NoReturn


TASK_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,78}[a-z0-9])?$")
FILE_KINDS = ("context", "todo", "insights")


class StateStoreError(ValueError):
    """Raised when state paths or writes violate the storage contract."""


@dataclass(frozen=True)
class StateLayout:
    common_dir: Path
    project_id: str
    state_root: Path
    task_id: str
    task_dir: Path
    context_path: Path
    todo_path: Path
    insights_path: Path

    @property
    def files(self) -> dict[str, Path]:
        return {
            "context": self.context_path,
            "todo": self.todo_path,
            "insights": self.insights_path,
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "analyze-context-state.v1",
            "common_dir": str(self.common_dir),
            "project_id": self.project_id,
            "state_root": str(self.state_root),
            "task_id": self.task_id,
            "task_dir": str(self.task_dir),
            "files": {key: str(value) for key, value in self.files.items()},
        }


def fail(message: str) -> NoReturn:
    raise StateStoreError(message)


def _run_git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        fail(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def validate_task_id(task_id: str) -> str:
    if not TASK_ID_PATTERN.fullmatch(task_id):
        fail("task ID must be 1-80 lowercase letters, digits, hyphens, or underscores, start and end alphanumeric")
    return task_id


def normalized_common_dir(cwd: Path) -> Path:
    cwd = cwd.expanduser().resolve(strict=True)
    raw = Path(_run_git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return raw.expanduser().resolve(strict=True)


def _project_slug(common_dir: Path) -> str:
    repository_dir = common_dir.parent if common_dir.name == ".git" else common_dir
    slug = re.sub(r"[^a-z0-9]+", "-", repository_dir.name.lower()).strip("-")
    return slug or "repository"


def derive_project_id(cwd: Path) -> tuple[Path, str]:
    common_dir = normalized_common_dir(cwd)
    digest = hashlib.sha256(os.fsencode(str(common_dir))).hexdigest()[:12]
    return common_dir, f"{_project_slug(common_dir)}--{digest}"


def _resolved_external_root(state_home: Path | None) -> Path:
    configured = state_home or Path(os.environ.get("ANALYZE_CONTEXT_STATE_HOME", "~/.analyze-context"))
    resolved = configured.expanduser().absolute().resolve(strict=False)
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve(strict=True):
        fail("state home must be a dedicated directory, not a filesystem root or user home")
    return resolved


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _worktree_roots(cwd: Path) -> tuple[Path, ...]:
    output = _run_git(cwd, "worktree", "list", "--porcelain")
    roots: list[Path] = []
    for line in output.splitlines():
        if line.startswith("worktree "):
            roots.append(Path(line.removeprefix("worktree ")).expanduser().resolve(strict=False))
    return tuple(roots)


def resolve_layout(cwd: Path, task_id: str, state_home: Path | None = None) -> StateLayout:
    task_id = validate_task_id(task_id)
    common_dir, project_id = derive_project_id(cwd)
    state_root = _resolved_external_root(state_home)
    task_dir = (state_root / project_id / task_id).resolve(strict=False)
    if not _is_within(task_dir, state_root) or task_dir == state_root:
        fail("resolved task directory escapes the Analyze Context state root")
    for worktree_root in _worktree_roots(cwd):
        if _is_within(state_root, worktree_root) or _is_within(task_dir, worktree_root):
            fail(f"Analyze Context state must remain outside Git worktrees: {worktree_root}")
    return StateLayout(
        common_dir=common_dir,
        project_id=project_id,
        state_root=state_root,
        task_id=task_id,
        task_dir=task_dir,
        context_path=task_dir / f"{task_id}-context.md",
        todo_path=task_dir / f"{task_id}-todo.md",
        insights_path=task_dir / f"{task_id}-insights.md",
    )


@contextlib.contextmanager
def _private_umask() -> Iterator[None]:
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)


def _ensure_private_directories(layout: StateLayout) -> None:
    with _private_umask():
        layout.task_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    for directory in (layout.state_root, layout.task_dir.parent, layout.task_dir):
        directory.chmod(0o700)


@contextlib.contextmanager
def task_write_lock(layout: StateLayout) -> Iterator[None]:
    lock_dir = layout.state_root / ".locks"
    with _private_umask():
        lock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_dir.chmod(0o700)
    lock_name = hashlib.sha256(f"{layout.project_id}\0{layout.task_id}".encode()).hexdigest()
    lock_path = lock_dir / f"{lock_name}.lock"
    acquired = False
    try:
        try:
            lock_path.mkdir(mode=0o700)
            acquired = True
        except FileExistsError as exc:
            fail("another writer currently holds this Analyze Context task")
            raise AssertionError from exc
        yield
    finally:
        if acquired:
            with contextlib.suppress(OSError):
                lock_path.rmdir()


def _atomic_write_unlocked(layout: StateLayout, kind: str, content: str) -> Path:
    if kind not in layout.files:
        fail(f"unknown file kind: {kind}")
    destination = layout.files[kind]
    if destination.parent.resolve(strict=True) != layout.task_dir.resolve(strict=True):
        fail("canonical file destination escaped the task directory")
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=layout.task_dir
        )
        temporary_path = Path(temporary_name)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            if not content.endswith("\n"):
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        destination.chmod(0o600)
        directory_descriptor = os.open(layout.task_dir, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return destination


def atomic_write(layout: StateLayout, kind: str, content: str) -> Path:
    _ensure_private_directories(layout)
    with task_write_lock(layout):
        return _atomic_write_unlocked(layout, kind, content)


def _templates(layout: StateLayout) -> dict[str, str]:
    return {
        "context": (
            f"---\ntask_id: {layout.task_id}\nstatus: active\nproject_id: {layout.project_id}\n"
            "branch: unknown\nworktree: unknown\nupdated_at: unknown\n---\n\n# Goal\n\n# Success Criteria\n\n# Scope\n\n# Next\n"
        ),
        "todo": "# Todo\n\n- [ ] Record the next analysis item\n",
        "insights": "# Insights\n\n# Evidence\n\n# Final Summary\n",
    }


def _initialize_unlocked(layout: StateLayout) -> None:
    for kind, content in _templates(layout).items():
        if not layout.files[kind].exists():
            _atomic_write_unlocked(layout, kind, content)


def initialize(layout: StateLayout) -> None:
    _ensure_private_directories(layout)
    with task_write_lock(layout):
        _initialize_unlocked(layout)


def initialize_and_write(layout: StateLayout, kind: str, content: str) -> Path:
    _ensure_private_directories(layout)
    with task_write_lock(layout):
        _initialize_unlocked(layout)
        return _atomic_write_unlocked(layout, kind, content)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("paths", "init", "write"))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--state-home", type=Path)
    parser.add_argument("--kind", choices=FILE_KINDS)
    parser.add_argument("--input", type=Path, help="UTF-8 input file, or omit to read stdin")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        layout = resolve_layout(args.cwd, args.task_id, args.state_home)
        if args.command == "init":
            initialize(layout)
        elif args.command == "write":
            if args.kind is None:
                fail("write requires --kind")
            content = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
            initialize_and_write(layout, args.kind, content)
        print(json.dumps(layout.as_dict(), indent=2, sort_keys=True))
        return 0
    except (OSError, StateStoreError) as exc:
        print(f"analyze-context-state: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
