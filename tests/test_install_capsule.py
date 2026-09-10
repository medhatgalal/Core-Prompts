"""Portable installer capsule preserves v1 and isolates embedded module imports."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def builder():
    return load(ROOT / "scripts/build-install-runtime.py", "capsule_builder")


def test_generation_is_deterministic_and_sources_unchanged():
    module = builder()
    before = {p: p.read_bytes() for p in (ROOT / "scripts/core_install").glob("*.py")}
    first = module.render(module.sources(ROOT))
    second = module.render(dict(reversed(list(module.sources(ROOT).items()))))
    assert first == second
    compile(first, "deploy-profile.py", "exec")
    assert before == {p: p.read_bytes() for p in before}


def test_preserves_legacy_api_globals_and_file(tmp_path, monkeypatch):
    deployed = load(ROOT / "scripts/deploy-profile.py", "capsule_legacy")
    source = load(ROOT / "scripts/core_install/profile_v1.py", "source_legacy")
    assert deployed.digest(b"same") == source.digest(b"same")
    assert deployed.encoded({"z": 1, "a": 2}) == source.encoded({"a": 2, "z": 1})
    assert deployed.safe(tmp_path, "nested/file") == source.safe(tmp_path, "nested/file")
    assert deployed.plan.__globals__ is deployed.__dict__
    assert deployed.plan.__globals__["__file__"] == str(ROOT / "scripts/deploy-profile.py")
    monkeypatch.setattr(deployed, "digest", lambda data: "patched")
    target = tmp_path / "a"
    target.write_text("content")
    assert deployed.snapshot(target)["sha256"] == "patched"


def test_capsule_ignores_sibling_modules_and_isolates_instances(tmp_path, monkeypatch):
    generator = builder()
    fake = types.ModuleType("core_install")
    fake.__path__ = []
    poison = types.ModuleType("core_install.planner")
    poison.plan = lambda *args: "untrusted"
    monkeypatch.setitem(sys.modules, "core_install", fake)
    monkeypatch.setitem(sys.modules, "core_install.planner", poison)
    minimal = {
        "__init__": "",
        "profile_v1": "def main(): return 0\n",
        "planner": "from . import providers\ndef plan(*args): return providers.VALUE\n",
        "providers": "VALUE = 'first'\n",
    }
    one = tmp_path / "one.py"
    two = tmp_path / "two.py"
    one.write_text(generator.render(minimal))
    minimal["providers"] = "VALUE = 'second'\n"
    two.write_text(generator.render(minimal))
    first = load(one, "capsule_one")
    second = load(two, "capsule_two")
    assert first.installation_plan(None, None, None) == "first"
    assert second.installation_plan(None, None, None) == "second"
    assert first.installation_plan(None, None, None) == "first"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["__pycache__", "one.py", "two.py"]


def test_cli_dispatch_is_lazy_and_preserves_legacy_arguments(tmp_path):
    minimal = {
        "__init__": "",
        "profile_v1": "import sys\ndef main():\n print('legacy', repr(sys.argv[1:]))\n return 0\n",
        "cli": "def main(argv):\n print('install', repr(argv))\n return 0\n",
    }
    path = tmp_path / "capsule.py"
    path.write_text(builder().render(minimal))
    legacy = subprocess.check_output([sys.executable, str(path), "--old", "value"], text=True)
    install = subprocess.check_output([sys.executable, str(path), "--install", "--new", "value"], text=True)
    assert legacy.strip() == "legacy ['--old', 'value']"
    assert install.strip() == "install ['--new', 'value']"


def test_check_rejects_source_and_generated_drift_without_writing(tmp_path):
    root = tmp_path / "scripts/core_install"
    root.mkdir(parents=True)
    (root / "__init__.py").write_text("")
    (root / "profile_v1.py").write_text("def main(): return 0\n")
    command = [sys.executable, str(ROOT / "scripts/build-install-runtime.py"), "--repo", str(tmp_path)]
    subprocess.run(command, check=True, capture_output=True)
    output = tmp_path / "scripts/deploy-profile.py"
    generated = output.read_bytes()
    assert subprocess.run(command + ["--check"], capture_output=True).returncode == 0
    (root / "profile_v1.py").write_text("def main(): return 1\n")
    assert subprocess.run(command + ["--check"], capture_output=True).returncode != 0
    assert output.read_bytes() == generated
    (root / "profile_v1.py").write_text("def main(): return 0\n")
    output.write_bytes(generated + b"# changed\n")
    assert subprocess.run(command + ["--check"], capture_output=True).returncode != 0
    assert output.read_bytes() == generated + b"# changed\n"
