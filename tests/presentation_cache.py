"""Opt-in, task-owned Swift module cache for native exporter tests only.

The approval receipt is immutable. Successful runs advance a locked inventory;
failed runs retain evidence and never bless changed cache contents. No binaries
are reused, caches relocated, retries performed, or user caches selected.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import tempfile
import threading
import time

CACHE_RECEIPT_ENV = "CORE_PROMPTS_EXPORTER_CACHE_RECEIPT"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inventory(cache: Path) -> dict:
    result = {}
    for path in sorted(cache.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Cache symlink refused: {path}")
        if path.is_file():
            result[str(path.relative_to(cache))] = {
                "sha256": digest(path), "bytes": path.stat().st_size,
            }
    return result


def identity(source: Path, compiler: str, xcrun: str, sdk: str) -> dict:
    def query(*args):
        return subprocess.check_output(args, text=True, timeout=10).strip()
    real_compiler = Path(query(xcrun, "--find", "swiftc")).resolve()
    sdk_path = Path(sdk).resolve()
    options = {
        "args": ["<source>", "-o", "<fresh-executable>", "-module-cache-path", "<owned-cache>"],
        "timeout": 120,
        "environment": {key: os.environ.get(key) for key in (
            "DEVELOPER_DIR", "SDKROOT", "TOOLCHAINS", "SWIFT_EXEC",
            "SWIFT_DRIVER_SWIFT_FRONTEND_EXEC", "SWIFT_MODULECACHE_PATH",
            "CLANG_MODULE_CACHE_PATH", "CPATH", "CPLUS_INCLUDE_PATH",
            "C_INCLUDE_PATH", "LIBRARY_PATH", "MACOSX_DEPLOYMENT_TARGET",
        )},
    }
    return {
        "source_sha256": digest(source), "compiler": str(Path(compiler).resolve()),
        "selected_compiler_sha256": digest(Path(compiler).resolve()),
        "xcrun_sha256": digest(Path(xcrun).resolve()),
        "compiler_version": query(compiler, "--version"),
        "toolchain_compiler": str(real_compiler), "compiler_sha256": digest(real_compiler),
        "frontend_sha256": digest(real_compiler.parent / "swift-frontend"),
        "sdk": str(sdk_path), "sdk_version": query(xcrun, "--sdk", "macosx", "--show-sdk-version"),
        "sdk_settings_sha256": digest(sdk_path / "SDKSettings.json"),
        "host": [platform.machine(), platform.mac_ver()[0]],
        "configuration_sha256": hashlib.sha256(json.dumps(options, sort_keys=True).encode()).hexdigest(),
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


@contextmanager
def selected_cache(work: Path, inputs: dict | None):
    supplied = os.environ.get(CACHE_RECEIPT_ENV)
    if not supplied:
        cache = work / "module-cache"
        cache.mkdir()
        yield cache, {"mode": "fresh"}
        return
    import fcntl  # Only the macOS test fixture opts in; import remains portable.
    receipt = Path(supplied)
    if not receipt.is_absolute() or receipt != receipt.resolve():
        raise ValueError("Cache receipt must use its exact absolute, non-symlink path")
    root = receipt.parent
    # Only explicitly owned temporary task data; never a home/global cache.
    temporary_roots = (Path("/private/tmp"), Path(tempfile.gettempdir()).resolve())
    if not any(root.is_relative_to(base) and root != base for base in temporary_roots):
        raise ValueError("Cache receipt must be in a task-owned temporary directory")
    if root.stat().st_uid != os.getuid() or receipt.stat().st_uid != os.getuid():
        raise ValueError("Cache owner mismatch")
    lock = root / "cache.lock"
    if lock.is_symlink():
        raise ValueError("Cache lock symlink refused")
    with lock.open("a+") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        approval = json.loads(receipt.read_text())
        receipt_hash = digest(receipt)
        cache = root / "module-cache"
        if (approval.get("schema") != 1 or not approval.get("task_id")
                or approval.get("uid") != os.getuid()
                or approval.get("cache") != str(cache)
                or cache != cache.resolve() or cache.stat().st_uid != os.getuid()
                or approval.get("identity") != inputs):
            raise ValueError("Cache approval path, owner, or source/toolchain/config identity mismatch")
        state = root / "cache-state.json"
        if state.is_symlink():
            raise ValueError("Cache state symlink refused")
        prior = json.loads(state.read_text()) if state.exists() else {
            "approval_sha256": receipt_hash, "files": approval["files"],
        }
        before = inventory(cache)
        if prior.get("approval_sha256") != receipt_hash or prior.get("files") != before:
            raise ValueError("Cache inventory drift; explicit new approval required")
        record = {"mode": "approved-task-cache", "approval_sha256": receipt_hash,
                  "task_id": approval["task_id"], "identity": inputs, "before": before}
        try:
            yield cache, record
        except BaseException:
            record["after"] = inventory(cache)
            record["state_advanced"] = False
            raise
        else:
            record["after"] = inventory(cache)
            write_json(state, {"approval_sha256": receipt_hash, "files": record["after"]})
            record["state_advanced"] = True
        finally:
            write_json(work / "cache-readback.json", record)


class CompilerChildren:
    """Track actual child identities, including Swift workers with their own PGID."""

    def __init__(self, process, source):
        self.process, self.source = process, str(source)
        self.known, self.events, self.errors = {}, [], []
        self.done = threading.Event()
        self.thread = threading.Thread(target=self.monitor, daemon=True)

    @staticmethod
    def snapshot():
        output = subprocess.check_output(
            ["ps", "-axo", "pid=,ppid=,pgid=,lstart=,comm="], text=True, timeout=8,
        )
        rows = {}
        for line in output.splitlines():
            fields = line.split(None, 8)
            if len(fields) == 9:
                rows[int(fields[0])] = {
                    "pid": int(fields[0]), "ppid": int(fields[1]), "pgid": int(fields[2]),
                    "start": " ".join(fields[3:8]), "executable": fields[8],
                }
        return rows

    @staticmethod
    def key(row):
        return row["start"], row["executable"]

    def owned(self, rows):
        selected = {pid for pid, row in rows.items()
                    if self.known.get(pid) == self.key(row)}
        if self.process.poll() is None and self.process.pid in rows:
            selected.add(self.process.pid)
        # Recover a reparented Swift worker by the unique build source path.
        family = {"swiftc", "swift-driver", "swift-frontend", "clang", "clang++", "ld"}
        candidates = [pid for pid, row in rows.items()
                      if Path(row["executable"]).name in family and pid not in selected]
        if candidates:
            output = subprocess.run(["ps", "-p", ",".join(map(str, candidates)), "-o", "pid=,args="],
                                    capture_output=True, text=True, timeout=8)
            for line in output.stdout.splitlines():
                fields = line.split(None, 1)
                if len(fields) == 2 and self.source in fields[1]:
                    selected.add(int(fields[0]))
        while True:
            children = {pid for pid, row in rows.items() if row["ppid"] in selected}
            if children <= selected:
                break
            selected |= children
        for pid in selected:
            self.known[pid] = self.key(rows[pid])
        result = [rows[pid] for pid in sorted(selected)]
        self.events.append(result)
        return result

    def monitor(self):
        while not self.done.is_set():
            try:
                self.owned(self.snapshot())
            except Exception as error:
                self.errors.append(repr(error))
            self.done.wait(0.5)

    def cleanup(self):
        self.done.set()
        self.thread.join(timeout=18)
        if self.thread.is_alive():
            raise RuntimeError("Compiler process observer did not stop")
        killed = []
        for _ in range(3):
            members = self.owned(self.snapshot())
            if not members:
                return {"killed": killed, "remaining": [], "observations": self.events,
                        "observation_errors": self.errors}
            verified = self.snapshot()
            for row in members:
                current = verified.get(row["pid"])
                if current and self.key(current) == self.known[row["pid"]]:
                    try:
                        os.kill(row["pid"], signal.SIGKILL)
                        killed.append(row["pid"])
                    except ProcessLookupError:
                        pass
            time.sleep(0.2)
        return {"killed": killed, "remaining": self.owned(self.snapshot()),
                "observations": self.events, "observation_errors": self.errors}


def compile_exporter(compiler: str, source: Path, executable: Path, cache: Path) -> None:
    """One fresh compile; preserve failure and stop verified compiler descendants."""
    if executable.exists():
        raise ValueError("Refusing to reuse an existing exporter executable")
    argv = [compiler, str(source), "-o", str(executable), "-module-cache-path", str(cache)]
    CompilerChildren.snapshot()  # Refuse to launch if lifecycle inspection is unavailable.
    started = time.monotonic()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    children = CompilerChildren(process, source)
    children.thread.start()
    record = {"argv": argv, "pid": process.pid, "pgid": process.pid, "timeout": 120}
    failure = None
    try:
        stdout, stderr = process.communicate(timeout=120)
        record.update(exit=process.returncode, stdout=stdout, stderr=stderr)
        assert process.returncode == 0, stdout + stderr
        assert executable.is_file(), "Compiler did not produce an executable"
        record["executable_sha256"] = digest(executable)
    except BaseException as error:
        failure = error
        record["failure"] = type(error).__name__
    finally:
        try:
            record["cleanup"] = children.cleanup()
            cleanup = record["cleanup"]
            if cleanup["remaining"] or cleanup["observation_errors"] or cleanup["killed"]:
                if failure is None:
                    failure = RuntimeError("Compiler workers did not exit cleanly; see receipt")
        except BaseException as error:
            record["cleanup_error"] = repr(error)
            # Fail closed and still terminate/reap the owned driver group.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if failure is None:
                failure = error
        try:
            stdout, stderr = process.communicate(timeout=10)
            record.update(stdout=stdout, stderr=stderr)
        except BaseException as error:
            record["reap_error"] = repr(error)
            if failure is None:
                failure = error
        record.update(seconds=time.monotonic() - started, exit=process.returncode)
        write_json(source.parent / "compile-receipt.json", record)
    if failure is not None:
        raise failure
