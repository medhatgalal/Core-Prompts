"""Bounded native transport tests: no AGY installation or model calls."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "sources/capability-resources/engos-route-intent"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX launcher/process groups")


@pytest.fixture
def package(tmp_path):
    import shutil
    skill = tmp_path / "catalog with spaces" / "engos-route-intent"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("Fixture skill; no native discovery claim")
    shutil.copytree(RESOURCES, skill / "resources")
    bindir = tmp_path / "fake bin"
    bindir.mkdir()
    fake = bindir / "agy"
    fake.write_text("#!" + sys.executable + "\n" + r'''
import json, os, pathlib, signal, subprocess, sys, time
if os.environ.get("FAKE_MODE") == "unsupported":
    sys.stderr.write("unsupported --json-schema\n")
    raise SystemExit(7)
record = pathlib.Path(os.environ["FAKE_RECORD"])
record.write_text(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
    "marker": os.environ.get("CORE_PROMPTS_AGY_INTAKE_ACTIVE"),
    "inherited": os.environ.get("FAKE_DEFAULT"), "pid": os.getpid()}))
mode = os.environ.get("FAKE_MODE", "normal")
if mode in {"early0", "early9"}:
    ready = os.environ["FAKE_DESCENDANT"] + ".ready"
    code = ("import pathlib,signal,time; "
            "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
            "pathlib.Path(" + repr(ready) + ").write_text('ready'); time.sleep(60)")
    descendant = subprocess.Popen([sys.executable, "-c", code])
    pathlib.Path(os.environ["FAKE_DESCENDANT"]).write_text(str(descendant.pid))
    while not pathlib.Path(ready).exists(): time.sleep(0.01)
    os.write(1, b"leader output before exit\n")
    os.write(2, b"leader diagnostic before exit\n")
    raise SystemExit(0 if mode == "early0" else 9)
if mode == "wait":
    descendant = subprocess.Popen([sys.executable, "-c",
        "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)"])
    pathlib.Path(os.environ["FAKE_DESCENDANT"]).write_text(str(descendant.pid))
    def received(sig, _):
        pathlib.Path(os.environ["FAKE_SIGNAL"]).write_text(str(sig))
        # Leader exits on TERM before its TERM-ignoring descendant.
        if sig == signal.SIGTERM:
            raise SystemExit(0)
    signal.signal(signal.SIGTERM, received)
    signal.signal(signal.SIGINT, received)
    while True: time.sleep(0.02)
os.write(1, b'raw \xff stdout\r\n{"result":"untouched?"}\n')
os.write(2, b'raw \xfe stderr\r\n')
raise SystemExit(int(os.environ.get("FAKE_EXIT", "0")))
''')
    fake.chmod(0o755)
    env = os.environ.copy()
    env.pop("CORE_PROMPTS_AGY_INTAKE_ACTIVE", None)
    env.update(PATH=str(bindir), FAKE_RECORD=str(tmp_path / "record.json"),
               FAKE_DESCENDANT=str(tmp_path / "descendant"),
               FAKE_SIGNAL=str(tmp_path / "signal"), FAKE_DEFAULT="unchanged")
    return skill / "resources/scripts/agy_intake.py", env, tmp_path


def run(package, *args, request=b"A bounded request\n", **extra):
    helper, env, cwd = package
    return subprocess.run([sys.executable, str(helper), *args], input=request,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, cwd=cwd, timeout=5, **extra)


def wait_file(path, child):
    end = time.monotonic() + 3
    while not path.exists():
        assert child.poll() is None, child.communicate()
        assert time.monotonic() < end, path
        time.sleep(0.01)
    return path.read_text()


def is_running(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # Linux keeps orphan zombies visible until init reaps them; they cannot run.
    proc_stat = Path(f"/proc/{pid}/stat")
    try:
        return proc_stat.read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return os.name == "posix" and not Path("/proc").is_dir()


def test_exact_prompt_schema_argv_and_raw_native_streams(package):
    request = b"Read only. \r\n' $() `not a command` \xc3\xa9\n\n"
    result = run(package, request=request)
    assert result.returncode == 0
    assert result.stdout == b'raw \xff stdout\r\n{"result":"untouched?"}\n'
    assert result.stderr == b'raw \xfe stderr\r\n'
    helper, env, cwd = package
    observed = json.loads(Path(env["FAKE_RECORD"]).read_text())
    assert observed["argv"] == ["--mode", "plan", "--sandbox", "--add-dir",
        str(helper.parents[3]), "--output-format", "stream-json", "--json-schema",
        (RESOURCES / "schemas/agy-intake.schema.json").read_bytes().decode(),
        "-p", request.decode()]
    assert observed["marker"] == "1"
    assert observed["inherited"] == "unchanged"
    assert observed["cwd"] == str(cwd)


def test_prompt_file_is_exact_and_does_not_consume_stdin(package):
    _, env, cwd = package
    source = cwd / "request with spaces.txt"
    source.write_bytes(b"\xef\xbb\xbfRequest\r\n\n")
    result = run(package, "--prompt-file", str(source), request=b"ignored")
    assert result.returncode == 0
    assert json.loads(Path(env["FAKE_RECORD"]).read_text())["argv"][-1] == source.read_bytes().decode()


@pytest.mark.parametrize("request_bytes", [b"", b" \r\n", b"bad\x00value", b"\xff"])
def test_invalid_input_never_launches(package, request_bytes):
    assert run(package, request=request_bytes).returncode == 2
    assert not Path(package[1]["FAKE_RECORD"]).exists()


@pytest.mark.parametrize("value", ["0", "-1", "241", "nan", "inf", "bad"])
def test_invalid_time_budget_never_launches(package, value):
    assert run(package, "--timeout-seconds", value).returncode == 2
    assert not Path(package[1]["FAKE_RECORD"]).exists()


@pytest.mark.parametrize("fault", ["missing-runtime", "schema", "entry", "nested"])
def test_setup_errors_do_not_dispatch(package, fault):
    helper, env, _ = package
    if fault == "missing-runtime": env["PATH"] = "/nonexistent"
    elif fault == "schema": (helper.parents[1] / "schemas/agy-intake.schema.json").unlink()
    elif fault == "entry": (helper.parents[2] / "SKILL.md").unlink()
    else: env["CORE_PROMPTS_AGY_INTAKE_ACTIVE"] = "1"
    assert run(package).returncode == 2
    assert not Path(env["FAKE_RECORD"]).exists()


@pytest.mark.parametrize("mode,code", [("normal", 9), ("unsupported", 7)])
def test_native_errors_propagate_without_retry_or_fallback(package, mode, code):
    package[1].update(FAKE_MODE=mode, FAKE_EXIT=str(code))
    result = run(package)
    assert result.returncode == code
    if mode == "unsupported": assert result.stderr == b"unsupported --json-schema\n"


def test_stalled_stdin_consumes_total_budget_without_dispatch(package):
    helper, env, cwd = package
    started = time.monotonic()
    child = subprocess.Popen([sys.executable, str(helper), "--timeout-seconds", "0.25"],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=cwd, env=env)
    try:
        child.wait(timeout=2)  # Keep stdin open without sending EOF.
        assert child.returncode == 124
        assert time.monotonic() - started < 1.5
        assert not Path(env["FAKE_RECORD"]).exists()
    finally:
        if child.poll() is None: child.kill(); child.wait()
        child.communicate()


def test_prompt_fifo_is_rejected_without_waiting(package):
    fifo = package[2] / "request.fifo"
    os.mkfifo(fifo)
    assert run(package, "--prompt-file", str(fifo)).returncode == 2
    assert not Path(package[1]["FAKE_RECORD"]).exists()


@pytest.mark.parametrize("stop_signal", [None, signal.SIGINT, signal.SIGTERM])
def test_owned_group_stops_even_when_leader_exits_and_descendant_ignores_term(package, stop_signal):
    helper, env, cwd = package
    env["FAKE_MODE"] = "wait"
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
    child = subprocess.Popen([sys.executable, str(helper), "--timeout-seconds", "1.5"],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=cwd, env=env)
    descendant = None
    started = time.monotonic()
    try:
        child.stdin.write(b"Read-only bounded intake\n"); child.stdin.close(); child.stdin = None
        descendant = int(wait_file(Path(env["FAKE_DESCENDANT"]), child))
        if stop_signal is not None:
            time.sleep(0.1)  # Allow the fake descendant to install its TERM handler.
            child.send_signal(stop_signal)
        out, err = child.communicate(timeout=4)
        assert child.returncode == (124 if stop_signal is None else 128 + stop_signal), (out, err)
        assert Path(env["FAKE_SIGNAL"]).read_text() == str(stop_signal or signal.SIGTERM)
        end = time.monotonic() + 1
        while is_running(descendant) and time.monotonic() < end: time.sleep(0.02)
        assert not is_running(descendant)
        assert unrelated.poll() is None
        assert time.monotonic() - started < 3
    finally:
        if child.poll() is None: child.kill(); child.wait()
        if descendant and is_running(descendant): os.kill(descendant, signal.SIGKILL)
        unrelated.terminate(); unrelated.wait()


def test_schema_contract_and_resource_route():
    from intent_pipeline.capability_resources import load_resource_bundle
    schema = json.loads((RESOURCES / "schemas/agy-intake.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) - set(schema["required"]) == {"toolAction", "toolSummary"}
    assert schema["properties"]["questions"]["maxItems"] == 1
    assert all(schema["properties"][field]["type"] == "string" for field in ["toolAction", "toolSummary"])
    assert "conditional" in schema["properties"]["bounded_result"]["description"]
    bundle = load_resource_bundle(RESOURCES, "agy_intake")
    assert {r["path"] for r in bundle["resources"]} == {
        "scripts/agy_intake.py", "schemas/agy-intake.schema.json", "references/agy-intake.md"}


@pytest.mark.parametrize("code", [0, 9])
def test_normal_leader_exit_cleans_term_ignoring_descendant_and_inherited_streams(package, code):
    _, env, _ = package
    env["FAKE_MODE"] = f"early{code}"
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
    descendant = None
    try:
        result = run(package, "--timeout-seconds", "2")
        descendant = int(Path(env["FAKE_DESCENDANT"]).read_text())
        assert result.returncode == code
        assert result.stdout == b"leader output before exit\n"
        assert result.stderr == b"leader diagnostic before exit\n"
        end = time.monotonic() + 1
        while is_running(descendant) and time.monotonic() < end: time.sleep(0.02)
        assert not is_running(descendant)
        assert unrelated.poll() is None
    finally:
        if descendant and is_running(descendant): os.kill(descendant, signal.SIGKILL)
        unrelated.terminate(); unrelated.wait()


@pytest.fixture
def cleanup_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("agy_cleanup_contract", RESOURCES / "scripts/agy_intake.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CleanupChild:
    pid = 12345
    returncode = None
    def poll(self):
        return self.returncode
    def wait(self, *args, **kwargs):
        raise AssertionError("cleanup must never use a blocking wait")


@pytest.mark.parametrize("denied_signal", [signal.SIGTERM, 0, signal.SIGKILL])
def test_transient_denial_is_retried_not_assumed_absent(cleanup_module, monkeypatch, denied_signal):
    m = cleanup_module; child = CleanupChild(); clock = [0.0]; denied = [0]; calls = []
    def killpg(group, signum):
        calls.append((group, signum))
        if signum == denied_signal and denied[0] < 3:
            denied[0] += 1
            raise PermissionError("injected startup permission denial")
        if child.returncode is not None:
            raise ProcessLookupError
        if signum == signal.SIGKILL:
            child.returncode = -signal.SIGKILL
    monkeypatch.setattr(m.os, "killpg", killpg)
    monkeypatch.setattr(m.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(m.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    assert m.stop_group(child, signal.SIGTERM, .5) is None
    assert denied[0] == 3
    assert all(group == child.pid for group, _ in calls)
    assert child.returncode is not None and clock[0] <= .5


@pytest.mark.parametrize("denied_signal", [None, 0])
def test_never_permitted_cleanup_is_bounded_and_not_success(cleanup_module, monkeypatch, denied_signal):
    m = cleanup_module; child = CleanupChild(); clock = [0.0]; calls = []
    def killpg(group, signum):
        calls.append((group, signum))
        if denied_signal is None or signum == denied_signal:
            raise PermissionError("injected persistent denial")
        if signum == signal.SIGKILL: child.returncode = -9
    monkeypatch.setattr(m.os, "killpg", killpg)
    monkeypatch.setattr(m.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(m.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    problem = m.stop_group(child, signal.SIGTERM, .1)
    assert "unverified" in problem and "permission denied" in problem
    assert clock[0] <= .1 and all(group == child.pid for group, _ in calls)


def test_absent_group_with_unreaped_child_never_waits_forever(cleanup_module, monkeypatch):
    m = cleanup_module; child = CleanupChild(); clock = [0.0]; calls = []
    def absent(group, signum):
        calls.append((group, signum)); raise ProcessLookupError
    monkeypatch.setattr(m.os, "killpg", absent)
    monkeypatch.setattr(m.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(m.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    assert "reaping unverified" in m.stop_group(child, signal.SIGTERM, .1)
    assert clock[0] <= .1 and len(calls) == 1


@pytest.mark.parametrize("primary", [0, 9, 124, 130, 143])
@pytest.mark.parametrize("unexpected", [False, True])
def test_cleanup_failure_preserves_primary_failure_and_restores_handlers(cleanup_module, monkeypatch, capsys, primary, unexpected):
    m = cleanup_module; child = CleanupChild()
    child.returncode = primary if primary in (0, 9) else None
    before = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    monkeypatch.setattr(m, "read_request", lambda *args: "bounded request")
    monkeypatch.setattr(m, "invocation", lambda *args: ["fake-native"])
    def spawn(*args, **kwargs):
        assert kwargs["start_new_session"] and kwargs["shell"] is False
        if primary in (130, 143): os.kill(os.getpid(), primary - 128)
        return child
    def fail_cleanup(*args):
        if unexpected: raise RuntimeError("private exception payload must not be echoed")
        return "group absence unverified; permission denied for signals 0,15"
    monkeypatch.setattr(m.subprocess, "Popen", spawn)
    monkeypatch.setattr(m, "stop_group", fail_cleanup)
    result = m.main(["--timeout-seconds", ".04"])
    assert result == (2 if primary == 0 else primary)
    captured = capsys.readouterr()
    assert "cleanup incomplete" in captured.err and f"original_status={primary}" in captured.err
    assert "Traceback" not in captured.err and "private exception payload" not in captured.err
    assert captured.out == ""
    assert {sig: signal.getsignal(sig) for sig in before} == before


def test_real_owned_process_recovers_from_denied_probe_without_touching_unrelated(cleanup_module, monkeypatch):
    m = cleanup_module
    child = subprocess.Popen([sys.executable, "-c", "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('ready',flush=True);time.sleep(10)"],
                             stdout=subprocess.PIPE, start_new_session=True)
    unrelated = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(10)"])
    original = m.signal_group; denied = [0]; calls = []
    def transient(proc, signum):
        calls.append(proc.pid)
        if signum == 0 and denied[0] < 3:
            denied[0] += 1
            return "denied"
        return original(proc, signum)
    try:
        assert child.stdout.readline() == b"ready\n"
        monkeypatch.setattr(m, "signal_group", transient)
        assert m.stop_group(child, signal.SIGTERM, time.monotonic() + .5) is None
        assert denied[0] == 3 and child.poll() is not None
        assert unrelated.poll() is None and all(pid == child.pid for pid in calls)
    finally:
        if child.poll() is None: child.kill()
        child.wait(timeout=2)
        unrelated.terminate(); unrelated.wait(timeout=2)
