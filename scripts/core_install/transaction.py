"""Journaled POSIX installation, with per-file atomic writes and explicit recovery.

The lock coordinates cooperating installers. Journals and preimages are retained;
multi-file installation is recoverable, not atomic. Empty directories are kept.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import unicodedata
import uuid


STATE = ".core-prompts-state"
INSTALLATION = STATE + "/installation.json"
RELEASE_WATCH = STATE + "/release-watch.json"
TRANSACTIONS = STATE + "/install-transactions"


class InstallError(ValueError):
    def __init__(self, message, code="installation-error", transaction=None):
        super().__init__(message)
        self.code = code
        self.transaction = transaction


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _checked(path):
    """Check all existing ancestors without resolving away symlink evidence."""
    path = Path(path).absolute()
    for item in [*reversed(path.parents), path]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise InstallError(f"symlink path rejected: {item}", "unsafe-path")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise InstallError(f"non-directory ancestor: {item}", "unsafe-path")
    return path


def safe(root, rel):
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise InstallError(f"invalid relative path: {rel!r}", "unsafe-path")
    if rel.startswith("/") or any(part in ("", ".", "..") for part in rel.split("/")):
        raise InstallError(f"noncanonical relative path: {rel!r}", "unsafe-path")
    root = _checked(root)
    if root.exists() and not root.is_dir():
        raise InstallError(f"root is not a directory: {root}", "unsafe-path")
    return _checked(root / rel)


def identity(path):
    path = _checked(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise InstallError(f"not a regular file: {path}", "unsafe-path")
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mode": stat.S_IMODE(info.st_mode)}


def inventory(root, roots):
    result = {}
    for rel in roots:
        path = safe(root, rel)
        if not path.exists():
            continue
        if path.is_dir():
            for directory, dirs, files in os.walk(path, followlinks=False):
                for name in sorted(dirs + files):
                    entry = Path(directory) / name
                    entry_rel = entry.relative_to(Path(root).absolute()).as_posix()
                    checked = safe(root, entry_rel)
                    if not checked.is_dir():
                        result[entry_rel] = identity(checked)
        else:
            result[rel] = identity(path)
    return dict(sorted(result.items()))


def _sync_dir(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _replace(path, data, mode):
    path = _checked(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _checked(path)
    fd, temporary = tempfile.mkstemp(prefix=".core-install-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fchmod(handle.fileno(), mode)
            os.fsync(handle.fileno())
        _checked(path)
        os.replace(temporary, path)
        _sync_dir(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _remove(path):
    _checked(path)
    path.unlink()
    _sync_dir(path.parent)


@contextmanager
def _lock(target):
    state = safe(target, STATE)
    state.mkdir(parents=True, exist_ok=True)
    path = safe(target, STATE + "/installation.lock")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise InstallError("installation lock is not a regular file", "unsafe-path")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InstallError("installation lock is held by another operation", "locked") from exc
        yield
    finally:
        os.close(fd)


def _valid_identity(value):
    if value is None:
        return
    if (not isinstance(value, dict) or set(value) != {"sha256", "mode"}
            or not isinstance(value["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is None
            or type(value["mode"]) is not int or not 0 <= value["mode"] <= 0o777):
        raise InstallError("invalid file identity", "invalid-plan")


def _actions(plan, target, repo=None):
    if (not isinstance(plan, dict) or plan.get("schema") != 2
            or plan.get("target") != str(target)
            or not isinstance(plan.get("actions"), list)):
        raise InstallError("invalid plan schema or target", "invalid-plan")
    if repo is not None and plan.get("repo") != str(repo):
        raise InstallError("plan repository does not match", "invalid-plan")
    seen = set()
    for action in plan["actions"]:
        if not isinstance(action, dict) or action.get("op") not in ("write", "remove"):
            raise InstallError("invalid action", "invalid-plan")
        rel = action.get("path")
        safe(target, rel)
        # Reject portable aliases, including case-insensitive macOS state paths.
        key = unicodedata.normalize("NFC", rel).casefold()
        if key in seen or (key == STATE or key.startswith(STATE + "/") and rel not in (INSTALLATION, RELEASE_WATCH)):
            raise InstallError(f"duplicate or reserved action path: {rel}", "invalid-plan")
        if "before" not in action or "after" not in action:
            raise InstallError("action missing before or after identity", "invalid-plan")
        _valid_identity(action["before"])
        _valid_identity(action["after"])
        if action["op"] == "write":
            if action["after"] is None or ("source" in action) == ("content" in action):
                raise InstallError("write needs after identity and one byte source", "invalid-plan")
        elif action["after"] is not None or action["before"] is None:
            raise InstallError("remove needs before identity and absent after", "invalid-plan")
        seen.add(key)
    for rel in seen:
        if any(parent.as_posix() in seen for parent in Path(rel).parents if parent != Path(".")):
            raise InstallError("overlapping file action paths", "invalid-plan")
    return plan["actions"]


def _data_identity(data, mode):
    return {"sha256": hashlib.sha256(data).hexdigest(), "mode": mode}


def _source(repo, action):
    if "source" in action:
        path = safe(repo, action["source"])
        if identity(path) != action["after"]:
            raise InstallError(f"source drift: {action['source']}", "stale-source")
        data = path.read_bytes()
    else:
        try:
            data = base64.b64decode(action["content"], validate=True)
        except (ValueError, TypeError) as exc:
            raise InstallError("invalid base64 content", "invalid-plan") from exc
    if _data_identity(data, action["after"]["mode"]) != action["after"]:
        raise InstallError(f"source hash mismatch: {action['path']}", "stale-source")
    return data


def _journal_path(target, transaction):
    if not isinstance(transaction, str) or re.fullmatch(r"[0-9a-f]{32}", transaction) is None:
        raise InstallError("invalid transaction id", "invalid-transaction")
    return safe(target, f"{TRANSACTIONS}/{transaction}/journal.json")


def _load(target, transaction):
    path = _journal_path(target, transaction)
    try:
        identity(path)
        journal = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise InstallError(f"unreadable transaction journal: {transaction}", "invalid-journal", transaction) from exc
    if (not isinstance(journal, dict) or journal.get("schema") != 1
            or journal.get("transaction") != transaction
            or type(journal.get("created_ns")) is not int
            or type(journal.get("restoring", False)) is not bool
            or journal.get("status") not in ("prepared", "applying", "complete", "rolled-back")):
        raise InstallError("invalid transaction journal", "invalid-journal", transaction)
    _actions(journal.get("plan"), target)
    return journal


def _journals(target):
    directory = safe(target, TRANSACTIONS)
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise InstallError("transaction storage is not a directory", "invalid-journal")
    result = []
    for entry in sorted(directory.iterdir()):
        # Unknown metadata is preserved and blocks writes, never silently removed.
        safe(target, f"{TRANSACTIONS}/{entry.name}")
        result.append(_load(target, entry.name))
    return result


def _save(target, journal):
    _replace(_journal_path(target, journal["transaction"]), encoded(journal), 0o600)


def _receipt(journal):
    return {"schema": 2, "transaction": journal["transaction"], "status": journal["status"],
            "target": journal["plan"]["target"], "actions": len(journal["plan"]["actions"])}


def _retention_candidates(target, journals):
    """Advisory only: exact, intact old journals; this function never deletes."""
    finished = sorted(journals, key=lambda item: item["created_ns"], reverse=True)
    candidates = []
    for journal in finished[2:]:
        if journal["status"] not in ("complete", "rolled-back"):
            continue
        directory = _journal_path(target, journal["transaction"]).parent
        expected = {"journal.json": identity(directory / "journal.json")}
        for index, action in enumerate(journal["plan"]["actions"]):
            for kind in ("before", "after"):
                if action[kind] is not None:
                    expected[f"{kind}/{index}"] = action[kind]
        try:
            if inventory(directory, ["journal.json", "before", "after"]) != expected:
                continue
            if any(entry.name not in ("journal.json", "before", "after") for entry in directory.iterdir()):
                continue
            if any(dirs for _, dirs, _ in os.walk(directory / "before")):
                continue
            if any(dirs for _, dirs, _ in os.walk(directory / "after")):
                continue
        except (InstallError, OSError):
            continue
        candidates.append(journal["transaction"])
    return candidates


def _order(actions):
    return sorted(enumerate(actions), key=lambda item: (
        item[1]["path"] == INSTALLATION, item[1]["op"] == "remove", item[0]))


def apply(repo: Path, target: Path, approved: dict, replan):
    repo, target = _checked(repo), _checked(target)
    # Detach approval from a caller which might mutate its dict during replan.
    approved = json.loads(encoded(approved))
    transaction = None
    with _lock(target):
        journals = _journals(target)
        if any(item["status"] in ("prepared", "applying") for item in journals):
            raise InstallError("unfinished transaction requires rollback", "unfinished-transaction")
        actions = _actions(approved, target, repo)
        if approved.get("blockers"):
            raise InstallError("approved plan contains unresolved blockers", "blocked-plan")
        if encoded(replan()) != encoded(approved):
            raise InstallError("stale approved plan: replan differs", "stale-plan")
        preserved = approved.get("preserved", [])
        if not actions:
            return {"schema": 2, "transaction": None,
                    "status": "no-op-with-preserved" if preserved else "no-op",
                    "target": str(target), "actions": 0, "preserved": preserved,
                    "retention_candidates": _retention_candidates(target, journals)}
        preimages, postimages = {}, {}
        for index, action in enumerate(actions):
            path = safe(target, action["path"])
            if identity(path) != action["before"]:
                raise InstallError(f"target drift: {action['path']}", "stale-target")
            if action["before"] is not None:
                preimages[index] = path.read_bytes()
                if _data_identity(preimages[index], action["before"]["mode"]) != action["before"]:
                    raise InstallError(f"target changed while reading: {action['path']}", "stale-target")
            if action["op"] == "write":
                postimages[index] = _source(repo, action)
        transaction = uuid.uuid4().hex
        journal = {"schema": 1, "transaction": transaction, "status": "prepared",
                   "created_ns": time.time_ns(), "plan": approved}
        try:
            _save(target, journal)
            directory = _journal_path(target, transaction).parent
            for index, data in preimages.items():
                _replace(safe(directory, f"before/{index}"), data, actions[index]["before"]["mode"])
            for index, data in postimages.items():
                _replace(safe(directory, f"after/{index}"), data, actions[index]["after"]["mode"])
            journal["status"] = "applying"
            _save(target, journal)
            retirement_started = False
            for index, action in _order(actions):
                path = safe(target, action["path"])
                if identity(path) != action["before"]:
                    raise InstallError(f"target drift during apply: {action['path']}", "stale-target")
                if action["op"] == "write":
                    staged = safe(directory, f"after/{index}")
                    if identity(staged) != action["after"]:
                        raise InstallError("staged postimage changed", "invalid-stage")
                    _replace(path, staged.read_bytes(), action["after"]["mode"])
                else:
                    if not retirement_started:
                        # A subsequent copy or external edit can invalidate an
                        # earlier successful replacement. Recheck the complete
                        # replacement set before retiring any predecessor.
                        for replacement in actions:
                            if replacement["op"] == "write" and replacement["path"] != INSTALLATION:
                                if identity(safe(target, replacement["path"])) != replacement["after"]:
                                    raise InstallError(f"replacement drift before retirement: {replacement['path']}",
                                                       "verification-failed")
                        retirement_started = True
                    _remove(path)
                if identity(path) != action["after"]:
                    raise InstallError(f"write verification failed: {action['path']}", "verification-failed")
            journal["status"] = "complete"
            _save(target, journal)
            receipt = _receipt(journal)
            receipt["preserved"] = preserved
            if preserved:
                receipt["status"] = "applied-with-preserved"
            receipt["retention_candidates"] = _retention_candidates(target, [*journals, journal])
            return receipt
        except Exception as exc:
            if not _journal_path(target, transaction).exists():
                raise InstallError(f"preparation failed before installed files changed; inspect transaction metadata "
                                   f"{transaction}: {exc}", "prepare-failed", transaction) from exc
            raise InstallError(f"installation failed; recoverable transaction {transaction}: {exc}",
                               "apply-failed", transaction) from exc


def _verified_bytes(path, expected, description):
    if identity(path) != expected:
        raise InstallError(f"missing or corrupt {description}", "invalid-backup")
    data = path.read_bytes()
    if _data_identity(data, expected["mode"]) != expected:
        raise InstallError(f"{description} changed while reading", "invalid-backup")
    return data


def _release_document(data):
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise InstallError("malformed release-watch JSON", "invalid-release-state") from exc
    if (not isinstance(value, dict) or not isinstance(value.get("installed_version"), str)
            or not value["installed_version"] or not isinstance(value.get("latest_version", ""), str)):
        raise InstallError("release-watch needs a recorded installed_version", "invalid-release-state")
    return value


def _release_rollback(target, directory, index, action, current, expected, journal):
    """Permit release observations to drift, while guarding installed transitions.

Only this operational file has semantic recovery. Ordinary package files and
installation.json retain their exact identity checks. The original pre/post
images remain immutable; the derived recovery image is recorded separately.
"""
    if action["path"] != RELEASE_WATCH or action["before"] is None or action["after"] is None:
        return None
    if journal["status"] == "prepared" and current == action["before"]:
        # Preparation may have stopped before images were saved; no change to
        # this path needs recovery, and missing preparation data proves nothing.
        return None
    previous = _release_document(_verified_bytes(safe(directory, f"before/{index}"), action["before"], "release preimage backup"))
    applied = _release_document(_verified_bytes(safe(directory, f"after/{index}"), action["after"], "release postimage backup"))
    record = journal.get("release_restore")
    if record is not None:
        if not isinstance(record, dict) or set(record) != {"before", "after", "content"}:
            raise InstallError("invalid derived release rollback record", "invalid-journal")
        _valid_identity(record["before"])
        _valid_identity(record["after"])
        try:
            recorded_data = base64.b64decode(record["content"], validate=True)
        except (ValueError, TypeError) as exc:
            raise InstallError("invalid derived release rollback bytes", "invalid-journal") from exc
        if (record["before"] is None or record["after"] is None
                or _data_identity(recorded_data, action["before"]["mode"]) != record["after"]
                or _release_document(recorded_data)["installed_version"] != previous["installed_version"]):
            raise InstallError("corrupt derived release rollback image", "invalid-journal")
    if current in expected and record is None:
        return None
    if current is None:
        raise InstallError("release-watch disappeared before rollback", "rollback-conflict")
    live = _release_document(_verified_bytes(safe(target, RELEASE_WATCH), current, "live release observation"))
    allowed_versions = {applied["installed_version"]}
    allowed_modes = {action["after"]["mode"]}
    if journal["status"] in ("prepared", "applying"):
        allowed_versions.add(previous["installed_version"])
        allowed_modes.add(action["before"]["mode"])
    if journal["status"] == "rolled-back":
        allowed_versions = {previous["installed_version"]}
        allowed_modes = {action["before"]["mode"]}
    if live["installed_version"].removeprefix('v') not in {value.removeprefix('v') for value in allowed_versions}:
        raise InstallError("rollback conflict: another installed-version transition in release-watch", "rollback-conflict")
    if current["mode"] not in allowed_modes:
        raise InstallError("rollback conflict: release-watch file mode changed", "rollback-conflict")
    if journal["status"] == "rolled-back":
        # A repeated rollback is read-only even if polling happened afterwards.
        return current, None
    live["installed_version"] = previous["installed_version"]
    latest = live.get("latest_version", "")
    pending = latest if latest.removeprefix("v") != live["installed_version"].removeprefix("v") else ""
    live.update(pending_version=pending, status="pending-install" if pending else "current")
    data = encoded(live)
    desired = _data_identity(data, action["before"]["mode"])
    journal["release_restore"] = {"before": current, "after": desired,
                                  "content": base64.b64encode(data).decode("ascii")}
    return desired, data


def rollback(target: Path, transaction: str, dry_run=False):
    target = _checked(target)
    with _lock(target):
        journal = _load(target, transaction)
        if any(item["transaction"] != transaction and item["status"] in ("prepared", "applying")
               for item in _journals(target)):
            raise InstallError("another unfinished transaction requires rollback first", "unfinished-transaction")
        actions = journal["plan"]["actions"]
        directory = _journal_path(target, transaction).parent
        restoring = journal.get("restoring", False)
        restore = []
        for index, action in _order(actions):
            current = identity(safe(target, action["path"]))
            expected = [action["after"]] if journal["status"] == "complete" and not restoring else [action["before"], action["after"]]
            if journal["status"] == "rolled-back":
                expected = [action["before"]]
            release = _release_rollback(target, directory, index, action, current, expected, journal)
            if release is not None:
                desired, data = release
                restore.append((action, current, desired, data))
                continue
            if current not in expected:
                raise InstallError(f"rollback conflict: {action['path']}", "rollback-conflict", transaction)
            data = None
            if current != action["before"] and action["before"] is not None:
                backup = safe(directory, f"before/{index}")
                if identity(backup) != action["before"]:
                    raise InstallError(f"missing or corrupt backup: {action['path']}", "invalid-backup", transaction)
                data = backup.read_bytes()
                if _data_identity(data, action["before"]["mode"]) != action["before"]:
                    raise InstallError("backup changed while reading", "invalid-backup", transaction)
            restore.append((action, current, action["before"], data))
        if dry_run:
            return {**_receipt(journal), "status": "rollback-ready"}
        if journal["status"] == "rolled-back":
            return _receipt(journal)
        try:
            journal["status"] = "applying"
            journal["restoring"] = True
            _save(target, journal)
            for action, current, desired, data in restore:
                path = safe(target, action["path"])
                if identity(path) != current:
                    raise InstallError(f"rollback conflict during restore: {action['path']}", "rollback-conflict")
                if current == desired:
                    continue
                if desired is None:
                    _remove(path)
                else:
                    _replace(path, data, desired["mode"])
                if identity(path) != desired:
                    raise InstallError("restore verification failed", "verification-failed")
            journal["status"] = "rolled-back"
            _save(target, journal)
            return _receipt(journal)
        except Exception as exc:
            raise InstallError(f"rollback failed; recoverable transaction {transaction}: {exc}",
                               "rollback-failed", transaction) from exc
