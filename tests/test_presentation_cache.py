"""Cache selection must never substitute a stale executable or hide a failure."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from presentation_cache import (
    CACHE_RECEIPT_ENV, compile_exporter, inventory, selected_cache, write_json,
)


@pytest.fixture
def approved(tmp_path, monkeypatch):
    root = tmp_path / "owned"
    root.mkdir()
    cache = root / "module-cache"
    cache.mkdir()
    (cache / "module.pcm").write_bytes(b"module")
    inputs = {"source_sha256": "current", "configuration_sha256": "options"}
    receipt = root / "approval.json"
    write_json(receipt, {"schema": 1, "uid": os.getuid(), "task_id": "test-task",
                         "cache": str(cache), "identity": inputs, "files": inventory(cache)})
    monkeypatch.setenv(CACHE_RECEIPT_ENV, str(receipt))
    work = tmp_path / "build"
    work.mkdir()
    return root, cache, inputs, receipt, work


def test_default_is_new_temporary_cache(tmp_path, monkeypatch):
    monkeypatch.delenv(CACHE_RECEIPT_ENV, raising=False)
    with selected_cache(tmp_path, None) as (cache, record):
        assert cache == tmp_path / "module-cache"
        assert not list(cache.iterdir())
        assert record == {"mode": "fresh"}


def test_success_tracks_changes_and_reuses_identical_path(approved):
    root, expected, inputs, receipt, work = approved
    original_receipt = receipt.read_bytes()
    with selected_cache(work, inputs) as (cache, _):
        assert cache == expected
        (cache / "another.pcm").write_bytes(b"another")
    with selected_cache(work, inputs) as (cache, _):
        assert cache == expected
    assert receipt.read_bytes() == original_receipt
    assert json.loads((root / "cache-state.json").read_text())["files"] == inventory(expected)


def test_failed_compile_does_not_approve_mutated_cache(approved):
    root, cache, inputs, _, work = approved
    with pytest.raises(subprocess.TimeoutExpired):
        with selected_cache(work, inputs):
            (cache / "incomplete.pcm").write_bytes(b"partial")
            raise subprocess.TimeoutExpired("swiftc", 120)
    assert not (root / "cache-state.json").exists()
    assert json.loads((work / "cache-readback.json").read_text())["state_advanced"] is False
    with pytest.raises(ValueError, match="inventory drift"):
        with selected_cache(work, inputs):
            pytest.fail("Failure was hidden")


@pytest.mark.parametrize("change", ["source", "config", "owner", "path", "inventory", "symlink"])
def test_rejects_unapproved_changes(approved, change):
    root, cache, inputs, receipt, work = approved
    data = json.loads(receipt.read_text())
    if change == "source":
        inputs = dict(inputs, source_sha256="changed")
    elif change == "config":
        inputs = dict(inputs, configuration_sha256="changed")
    elif change == "owner":
        data["uid"] = -1
    elif change == "path":
        data["cache"] = str(root / "elsewhere")
    elif change == "inventory":
        (cache / "module.pcm").write_bytes(b"changed")
    elif change == "symlink":
        (cache / "linked").symlink_to(receipt)
    write_json(receipt, data)
    with pytest.raises(ValueError):
        with selected_cache(work, inputs):
            pytest.fail("Unapproved cache accepted")


def test_concurrent_cache_use_fails_without_waiting(approved):
    _, _, inputs, _, work = approved
    with selected_cache(work, inputs):
        with pytest.raises(BlockingIOError):
            with selected_cache(work, inputs):
                pytest.fail("Concurrent use accepted")


def test_existing_executable_is_never_reused(tmp_path):
    executable = tmp_path / "exporter"
    executable.write_bytes(b"stale")
    with pytest.raises(ValueError, match="existing exporter"):
        compile_exporter("never-called", tmp_path / "source", executable, tmp_path)


def test_timeout_kills_child_in_separate_process_group(tmp_path, monkeypatch):
    import presentation_cache as helper
    import sys
    import time
    source = tmp_path / "source.swift"
    child_marker = tmp_path / "child.json"
    driver = tmp_path / "fake-swiftc"
    driver.write_text(
        f"#!{sys.executable}\n"
        "import subprocess,sys,time,json,os\n"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'], start_new_session=True)\n"
        f"open({str(child_marker)!r},'w').write(json.dumps([child.pid,os.getpgid(child.pid)]))\n"
        "time.sleep(30)\n"
    )
    driver.chmod(0o700)
    real_popen = helper.subprocess.Popen
    class TimeoutCompiler:
        def __init__(self, *args, **kwargs):
            self.real = real_popen(*args, **kwargs)
            self.pid = self.real.pid
            self.first = True
        @property
        def returncode(self):
            return self.real.returncode
        def poll(self):
            return self.real.poll()
        def communicate(self, timeout):
            if self.first:
                self.first = False
                assert timeout == 120
                deadline = time.monotonic() + 8
                while not child_marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                assert child_marker.exists()
                time.sleep(1)  # Let the real observer see the separate-group child.
                raise subprocess.TimeoutExpired("fake-swiftc", timeout)
            return self.real.communicate(timeout=timeout)
    # Only replace the compiler Popen; ps probes retain subprocess's real behavior.
    monkeypatch.setattr(helper.subprocess, "Popen", lambda args, **kw:
                        TimeoutCompiler(args, **kw) if args[0] == str(driver) else real_popen(args, **kw))
    with pytest.raises(subprocess.TimeoutExpired):
        compile_exporter(str(driver), source, tmp_path / "exporter", tmp_path)
    child_pid, child_pgid = json.loads(child_marker.read_text())
    receipt = json.loads((tmp_path / "compile-receipt.json").read_text())
    assert child_pgid != receipt["pgid"]
    assert child_pid in receipt["cleanup"]["killed"]
    assert receipt["cleanup"]["remaining"] == []
    assert receipt["failure"] == "TimeoutExpired"
    assert receipt["exit"] == -9


def test_cleanup_probe_failure_retains_original_compile_error(tmp_path, monkeypatch):
    import presentation_cache as helper
    class Compiler:
        pid = 123456789
        returncode = -9
        def communicate(self, timeout):
            if timeout == 120:
                raise subprocess.TimeoutExpired("swiftc", timeout)
            return "partial", "detail"
    monkeypatch.setattr(helper.subprocess, "Popen", lambda *a, **kw: Compiler())
    monkeypatch.setattr(helper.CompilerChildren, "snapshot", staticmethod(lambda: {}))
    monkeypatch.setattr(helper.CompilerChildren, "monitor", lambda self: None)
    def fail_cleanup(self):
        raise RuntimeError("ps unavailable")
    monkeypatch.setattr(helper.CompilerChildren, "cleanup", fail_cleanup)
    killed = []
    monkeypatch.setattr(helper.os, "killpg", lambda pid, sig: killed.append(pid))
    with pytest.raises(subprocess.TimeoutExpired):
        compile_exporter("swiftc", tmp_path / "source", tmp_path / "exporter", tmp_path)
    record = json.loads((tmp_path / "compile-receipt.json").read_text())
    assert "ps unavailable" in record["cleanup_error"]
    assert record["failure"] == "TimeoutExpired"
    assert killed == [123456789]
