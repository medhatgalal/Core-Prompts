"""Six offline controls for the real preparation/pytest entrypoint.

Only pytest (the runner itself) is real. Other Python dependencies and external
tools are shims, so these controls do not depend on the CI image's tool inventory.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validation_environment.py"


@pytest.fixture
def isolated(tmp_path):
    tools = tmp_path / "bin"
    tools.mkdir()
    for tool in ("bash", "git", "python3", "tar", "zip", "ps"):
        shim = tools / tool
        shim.write_text(f"#!{sys.executable}\nraise SystemExit(0)\n")
        shim.chmod(0o700)
    modules = tmp_path / "modules"
    modules.mkdir()
    for module in ("jsonschema", "cryptography", "docx", "PIL"):
        (modules / f"{module}.py").write_text("# Isolated dependency shim.\n")
    temp = tmp_path / "temporary"
    temp.mkdir()
    config = tmp_path / "pytest.ini"
    config.write_text("[pytest]\n")
    marker = tmp_path / "executed"
    case = tmp_path / "test_child.py"
    case.write_text(f"from pathlib import Path\ndef test_child():\n    Path({str(marker)!r}).write_text('ran')\n")
    environment = os.environ.copy()
    for name in ("PYTEST_ADDOPTS", "PYTEST_DEBUG_TEMPROOT", "CORE_PROMPTS_EXPORTER_CACHE_RECEIPT"):
        environment.pop(name, None)
    environment.update(PATH=str(tools), PYTHONPATH=str(modules), TMPDIR=str(temp),
                       PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")

    def run(*args, script=SCRIPT):
        return subprocess.run([sys.executable, str(script), *args], cwd=tmp_path,
                              env=environment, capture_output=True, text=True, timeout=30)

    return run, environment, tools, modules, temp, config, marker, case


def test_missing_executable_stops_before_child(isolated):
    run, _, tools, _, _, config, marker, case = isolated
    (tools / "zip").unlink()
    result = run("--pytest", "-c", str(config), str(case))
    assert result.returncode == 1
    assert "missing executable 'zip'" in result.stderr
    assert "install it and add it to PATH" in result.stderr
    assert not marker.exists()


def test_missing_python_dependency_stops_before_child(isolated):
    run, _, _, modules, _, config, marker, case = isolated
    (modules / "docx.py").write_text("raise ImportError('controlled missing dependency')\n")
    result = run("--pytest", "-c", str(config), str(case))
    assert result.returncode == 1
    assert "controlled missing dependency" in result.stderr
    assert "pip install 'python-docx>=1.2,<2'" in result.stderr
    assert not marker.exists()


def test_accepted_temporary_root_runs_child(isolated):
    run, environment, _, _, temp, config, marker, case = isolated
    before = environment.copy()
    result = run("--basetemp", str(temp / "task"), "--pytest", "-q", "-c", str(config), str(case))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert marker.read_text() == "ran"
    assert environment == before
    # Equality is also allowed: fixture receipts still live below this root.
    assert run("--basetemp", str(temp)).returncode == 0


def test_conflicting_temporary_root_stops_before_collection(isolated):
    run, environment, _, _, temp, config, marker, case = isolated
    outside = temp.parent / "outside"
    # A collection-time marker proves the hook rejects before importing tests.
    case.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('collected')\n")
    for mode in ("command", "environment", "configuration", "debug-root"):
        args = []
        if mode == "command":
            args = ["--basetemp", str(outside)]
        elif mode == "environment":
            environment["PYTEST_ADDOPTS"] = f"--basetemp={outside}"
        elif mode == "configuration":
            environment.pop("PYTEST_ADDOPTS", None)
            config.write_text(f"[pytest]\naddopts = --basetemp={outside}\n")
        else:
            config.write_text("[pytest]\n")
            environment["PYTEST_DEBUG_TEMPROOT"] = str(outside)
        result = run("--pytest", "-c", str(config), *args, str(case))
        assert result.returncode == 4, (mode, result.stdout, result.stderr)
        assert "outside the presentation cache's accepted roots" in result.stderr
        assert "TMPDIR" in result.stderr
        assert not marker.exists()
        assert not outside.exists()


def test_relocated_checkout_uses_its_own_root(isolated):
    run, _, _, _, temp, config, marker, case = isolated
    relocated = temp.parent / "checkout with spaces"
    scripts = relocated / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / SCRIPT.name
    shutil.copyfile(SCRIPT, script)
    case.write_text(
        f"from pathlib import Path\ndef test_child():\n"
        f"    assert Path.cwd() == Path({str(relocated)!r})\n"
        f"    Path({str(marker)!r}).write_text('relocated')\n"
    )
    result = run("--pytest", "-q", "-c", str(config), str(case), script=script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.read_text() == "relocated"


def test_child_failure_is_propagated(isolated):
    run, _, _, _, _, config, marker, case = isolated
    case.write_text(f"from pathlib import Path\ndef test_child():\n    Path({str(marker)!r}).write_text('ran')\n    assert False, 'controlled child failure'\n")
    result = run("--pytest", "-q", "-c", str(config), str(case))
    assert result.returncode == 1
    assert marker.read_text() == "ran"
    assert "1 failed" in result.stdout
    assert "controlled child failure" in result.stdout
