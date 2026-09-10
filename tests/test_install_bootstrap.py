"""Execute the real v1.14.0 installer across the portable-runtime bridge.

Every legacy call runs in an isolated interpreter with the historical sibling
install_bundle.py. No current in-process installer can stand in for that proof.
The installed capsule is then executed with source-checkout reads denied.
"""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARCH = "engos-design-architecture"
PROFILE = {"schema": 1, "scope": "skills", "targets": ["codex", "kiro"],
           "slugs": [ARCH], "retire": []}
V1_PROFILE = ".core-prompts-state/profile-install/profile.json"
V1_RECEIPT = ".core-prompts-state/profile-install/ownership.json"
V2_STATE = ".core-prompts-state/installation.json"

OLD_DRIVER = r'''
import hashlib, importlib.util, json, sys
from pathlib import Path
old, source, target = (Path(p) for p in sys.argv[1:4])
profile = json.loads(sys.argv[4])
routine = sys.argv[5] == 'routine'
spec = importlib.util.spec_from_file_location('historical_engine', old / 'scripts/deploy-profile.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
assert Path(engine.install_bundle.__file__).resolve() == old / 'scripts/install_bundle.py'
assert '_CAPSULE_PAYLOAD' not in engine.__dict__
plan = engine.plan(source, target, profile, routine=routine)
print(json.dumps({'plan': plan, 'bundle_module': engine.install_bundle.__file__,
    'engine_sha256': hashlib.sha256((old / 'scripts/deploy-profile.py').read_bytes()).hexdigest()}), flush=True)
result = engine.apply(source, target, profile, plan)
print(json.dumps({'result': result}), flush=True)
'''

DETACHED_DRIVER = r'''
import os, runpy, sys
from pathlib import Path
script = Path(sys.argv[1])
forbidden = [Path(p) for p in sys.argv[2].split(os.pathsep)]
arguments = sys.argv[3:]
def deny_source_reads(event, args):
    if event not in ('open', 'os.listdir', 'os.scandir') or not args:
        return
    raw = args[0]
    if not isinstance(raw, (str, bytes, os.PathLike)):
        return
    path = Path(os.fsdecode(raw)).absolute()
    if any(path == root or root in path.parents for root in forbidden):
        raise PermissionError('source checkout is unavailable: ' + str(path))
sys.addaudithook(deny_source_reads)
for root in forbidden:
    try:
        open(root / 'VERSION', 'rb')
    except PermissionError:
        pass
    else:
        raise AssertionError('source isolation guard did not reject a read')
sys.argv = [str(script), *arguments]
runpy.run_path(str(script), run_name='__main__')
'''


def put(root, relative, content, mode=0o644):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    path.chmod(mode)


def snapshot(root):
    return {p.relative_to(root).as_posix():
            (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o777)
            for p in root.rglob("*") if p.is_file()}


def output(process):
    return f"exit={process.returncode}\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}"


def old_call(old, source, target, profile=PROFILE, routine=False):
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", OLD_DRIVER, str(old), str(source),
         str(target), json.dumps(profile), "routine" if routine else "seed"],
        cwd=target.parent, text=True, capture_output=True, timeout=90)


def detached_call(old, target, *arguments):
    capsule = target / ".core-prompts-updater/scripts/deploy-profile.py"
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", DETACHED_DRIVER, str(capsule),
         str(ROOT) + ":" + str(old), *arguments],
        cwd=target.parent, text=True, capture_output=True, timeout=90)


@pytest.fixture(scope="module")
def old_runtime(tmp_path_factory):
    old = tmp_path_factory.mktemp("actual-v1-14-runtime")
    manifest_bytes = subprocess.check_output(
        ["git", "show", "v1.14.0:.meta/install-bundle.json"], cwd=ROOT)
    inventory = json.loads(manifest_bytes)["files"]
    archive = subprocess.check_output(["git", "archive", "v1.14.0"], cwd=ROOT)
    selected = set(inventory) | {".meta/install-bundle.json"}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for member in tree.getmembers():
            if member.name in selected:
                assert member.isfile(), member.name
                assert not Path(member.name).is_absolute() and ".." not in Path(member.name).parts
                mode = inventory.get(member.name, {"mode": 0o644})["mode"]
                put(old, member.name, tree.extractfile(member).read(), mode)
    assert selected == set(snapshot(old))
    # The archived inventory itself is not regenerated or weakened for the test.
    assert (old / ".meta/install-bundle.json").read_bytes() == manifest_bytes
    return old


@pytest.fixture
def bridged(old_runtime, tmp_path):
    target = tmp_path / "installation"
    target.mkdir()
    for relative in snapshot(old_runtime):
        destination = target / ".core-prompts-updater" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_runtime / relative, destination)
    seed = old_call(old_runtime, old_runtime, target)
    assert seed.returncode == 0, output(seed)
    seed_plan, seed_result = [json.loads(line) for line in seed.stdout.splitlines()]
    assert not seed_plan["plan"]["blockers"]
    assert seed_result["result"]["status"] == "applied"
    receipt = json.loads((target / V1_RECEIPT).read_text())
    expected_skills = {f"{prefix}/{ARCH}/{member}"
                       for prefix in (".agents/skills", ".kiro/skills")
                       for member in ("SKILL.md", "resources/capability.json")}
    assert set(receipt["skill_scope"]) == expected_skills
    assert receipt["bundle_files"]
    assert not (target / V2_STATE).exists()
    assert not (target / ".kiro/agents").exists()
    assert not (target / ".codex/agents").exists()

    bridge = old_call(old_runtime, ROOT, target, routine=True)
    assert bridge.returncode == 0, output(bridge)
    proposal, applied = [json.loads(line) for line in bridge.stdout.splitlines()]
    plan = proposal["plan"]
    assert not plan["blockers"], plan["blockers"]
    assert not plan["preserved"], plan["preserved"]
    assert set(plan["source_files"]) == expected_skills
    assert all(a["path"] in expected_skills or a["path"].startswith(".core-prompts-updater/")
               for a in plan["actions"])
    assert {a["path"] for a in plan["state_actions"]} <= {V1_PROFILE, V1_RECEIPT}
    assert applied["result"]["status"] == "applied"
    installed = target / ".core-prompts-updater/scripts/deploy-profile.py"
    assert installed.read_bytes() == (ROOT / "scripts/deploy-profile.py").read_bytes()
    assert b"_CAPSULE_PAYLOAD" in installed.read_bytes()
    assert not (target / ".core-prompts-updater/scripts/core_install").exists()
    assert not (target / V2_STATE).exists()
    return target, applied["result"]["transaction"]


def promote(old, target):
    support = target / ".core-prompts-updater"
    result = detached_call(old, target, "--install", "--repo", str(support), "--target", str(target))
    assert result.returncode == 0, output(result)
    return json.loads(result.stdout)


def test_actual_old_engine_delivers_capsule_then_runs_without_source_checkout(old_runtime, bridged):
    target, _ = bridged
    saved_profile = (target / V1_PROFILE).read_bytes()
    promoted = promote(old_runtime, target)
    assert promoted["status"] == "complete"
    state = json.loads((target / V2_STATE).read_text())
    expected = {f"{provider}:skill:{ARCH}" for provider in ("codex", "kiro")}
    assert set(state["selection"]) == expected
    assert set(state["packages"]) == expected
    assert (target / V1_PROFILE).read_bytes() == saved_profile
    assert not (target / ".kiro/agents").exists()
    assert not (target / ".codex/agents").exists()
    assert (target / "update_core_prompts.sh").is_file()
    before = snapshot(target)
    repeat = promote(old_runtime, target)
    assert repeat["status"] == "no-op"
    assert snapshot(target) == before


def test_incompatible_pre_rename_saved_scope_fails_without_target_writes(old_runtime, tmp_path):
    """An actual older skill identity cannot silently widen the old engine."""
    older, target = tmp_path / "v1-12-source", tmp_path / "installation"
    older.mkdir()
    target.mkdir()
    manifest = subprocess.check_output(["git", "show", "v1.12.2:.meta/manifest.json"], cwd=ROOT)
    put(older, ".meta/manifest.json", manifest)
    archive = subprocess.check_output([
        "git", "archive", "v1.12.2", ".codex/skills/architecture", ".kiro/skills/architecture"], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for member in tree.getmembers():
            if member.isfile():
                put(older, member.name, tree.extractfile(member).read(), 0o755 if member.mode & 0o111 else 0o644)
    profile = {**PROFILE, "slugs": ["architecture"]}
    seed = old_call(old_runtime, older, target, profile)
    assert seed.returncode == 0, output(seed)
    assert json.loads((target / V1_PROFILE).read_text())["slugs"] == ["architecture"]
    before = snapshot(target)
    attempted = old_call(old_runtime, ROOT, target, profile, routine=True)
    assert attempted.returncode != 0, output(attempted)
    assert "profile contains unknown slugs" in attempted.stderr, output(attempted)
    assert snapshot(target) == before
    assert not (target / V2_STATE).exists()


def test_legacy_bridge_rollback_cannot_cross_completed_v2_promotion(old_runtime, bridged):
    target, bridge_transaction = bridged
    promoted = promote(old_runtime, target)
    before = snapshot(target)
    rollback = detached_call(old_runtime, target, "--repo", str(target / ".core-prompts-updater"),
                             "--target", str(target), "--rollback", bridge_transaction)
    assert rollback.returncode != 0, output(rollback)
    assert "rollback" in rollback.stderr.lower(), output(rollback)
    assert snapshot(target) == before
    # Recovery remains possible in reverse order: undo v2 before the v1 bridge.
    undo_v2 = detached_call(old_runtime, target, "--install", "--repo", str(target / ".core-prompts-updater"),
                            "--target", str(target), "--rollback", promoted["transaction"])
    assert undo_v2.returncode == 0, output(undo_v2)
    undo_bridge = detached_call(old_runtime, target, "--repo", str(target / ".core-prompts-updater"),
                                "--target", str(target), "--rollback", bridge_transaction)
    assert undo_bridge.returncode == 0, output(undo_bridge)
    assert (target / ".core-prompts-updater/scripts/deploy-profile.py").read_bytes() == (old_runtime / "scripts/deploy-profile.py").read_bytes()
    assert not (target / V2_STATE).exists()
