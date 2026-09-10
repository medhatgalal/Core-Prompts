"""Real shell-wrapper contracts, using disposable homes and generated capsules.

Historical population coverage lives in test_installation_history. These tests
exercise supported runtimes, selection, ownership, JSON preview and recovery.
"""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import pytest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = ROOT / "scripts/deploy-surfaces.sh"
INSTALL_SCRIPT = ROOT / "scripts/install-local.sh"
ARCH = "engos-design-architecture"
REVIEW = "engos-quality-code-review"
AUTO = "engos-optimization-auto-research"


def test_reporting_skill_installs_standalone_command_and_preserves_custom_launcher(tmp_path):
    reporting='engos-audit-engineering-progress'
    first=external(INSTALL_SCRIPT,tmp_path,'--cli','kiro','--slug',reporting)
    document(first)
    launcher=tmp_path/'.local/bin/eng-report'
    assert launcher.is_file()
    result=subprocess.run([str(launcher),'run','--help'],cwd=tmp_path,env={**os.environ,'PYTHON_BIN':sys.executable},capture_output=True,text=True)
    assert result.returncode==0 and '--json' in result.stdout
    custom=b'#!/bin/sh\necho custom reporting\n';launcher.write_bytes(custom)
    report=document(external(INSTALL_SCRIPT,tmp_path),2)
    assert any(p.get('package')=='runtime:eng-report-launcher' for p in report['preserved'])
    assert launcher.read_bytes()==custom


def run_script(script, *args, target_root=None, cli_bins=(), use_system_bash=True,
               env_overrides=None, allow_nonlocal_target=False, timeout=90):
    # Isolate CLI detection while making the supported test interpreter available.
    with tempfile.TemporaryDirectory(prefix="core-wrapper-bin-") as directory:
        bin_dir = Path(directory)
        (bin_dir / "python3").symlink_to(sys.executable)
        for name in cli_bins:
            executable = bin_dir / name
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o755)
        env = os.environ.copy()
        env.update(env_overrides or {})
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        command = [str(script), *args]
        if target_root is not None:
            command += ["--target", str(target_root)]
        if allow_nonlocal_target:
            command.append("--allow-nonlocal-target")
        if use_system_bash:
            command.insert(0, "/bin/bash")
        return subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, timeout=timeout)


def external(script, target, *args, **kwargs):
    return run_script(script, *args, target_root=target, allow_nonlocal_target=True, **kwargs)


def document(result, code=0):
    assert result.returncode == code, result.stdout
    return json.loads(result.stdout)


def state(target):
    return json.loads((target / ".core-prompts-state/installation.json").read_text())


def paths(plan):
    return {action["path"] for action in plan["actions"]}


def seed_historical_architecture(target):
    """Use real catalog-pinned v1.12.2 bytes, never target-authored provenance."""
    catalog = json.loads((ROOT / ".meta/install-profiles/legacy-installations.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "v1.12.2^{commit}"], cwd=ROOT, text=True).strip()
    assert commit == catalog["releases"]["v1.12.2"]["commit"]
    archive = subprocess.check_output(["git", "archive", commit, ".kiro/skills/architecture",
                                       ".kiro/agents/architecture.json", ".kiro/agents/resources/architecture"], cwd=ROOT)
    copied = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for member in tree.getmembers():
            if not member.isfile():
                continue
            assert member.name.startswith((".kiro/skills/architecture/", ".kiro/agents/resources/architecture/")) or member.name == ".kiro/agents/architecture.json"
            content = tree.extractfile(member).read()
            dest = target / member.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            dest.chmod(0o755 if member.mode & 0o111 else 0o644)
            copied[member.name] = content
    assert copied
    return copied


def test_deploy_defaults_to_repo_root_for_target_all():
    result = run_script(DEPLOY_SCRIPT, "--cli", "all", "--dry-run",
                        cli_bins=("codex", "gemini", "claude", "kiro-cli"))
    assert result.returncode == 0, result.stdout
    assert "Target CLIs: gemini claude kiro codex" in result.stdout
    destinations = [Path(line.rsplit(" -> ", 1)[1]) for line in result.stdout.splitlines()
                    if line.startswith("DRY-RUN COPY ")]
    assert destinations
    assert all(p.is_relative_to(ROOT) for p in destinations)
    assert all(any(p.is_relative_to(ROOT / provider) for p in destinations)
               for provider in (".codex", ".gemini", ".claude", ".kiro"))
    assert f"DRY-RUN REGISTER codex agents in {ROOT}/.codex/config.toml" in result.stdout


def test_install_wrapper_defaults_to_repo_root_and_does_not_touch_home(tmp_path):
    fake_home = tmp_path / "home"
    result = run_script(INSTALL_SCRIPT, "--cli", "all", "--dry-run",
                        cli_bins=("codex", "gemini", "claude", "kiro-cli"), env_overrides={"HOME": str(fake_home)})
    assert result.returncode == 0, result.stdout
    assert f"DRY-RUN REGISTER codex agents in {ROOT}/.codex/config.toml" in result.stdout
    assert not fake_home.exists()


@pytest.mark.parametrize("script", [DEPLOY_SCRIPT, INSTALL_SCRIPT])
def test_nonlocal_target_requires_explicit_opt_in(tmp_path, script):
    result = run_script(script, "--cli", "codex", target_root=tmp_path)
    assert result.returncode == 1
    assert "--allow-nonlocal-target" in result.stdout
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("script", [DEPLOY_SCRIPT, INSTALL_SCRIPT])
def test_unspecified_provider_without_binaries_requires_selection(tmp_path, script):
    result = document(external(script, tmp_path), 1)
    assert result["status"] == "blocked"
    assert "NO_PROVIDERS" in result["error"]
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("script", [DEPLOY_SCRIPT, INSTALL_SCRIPT])
def test_explicit_provider_supports_offline_install(tmp_path, script):
    result = document(external(script, tmp_path, "--cli", "codex", "--slug", REVIEW, "--surface-only"))
    assert result["status"] == "complete"
    skill = tmp_path / ".agents/skills" / REVIEW
    assert (skill / "SKILL.md").read_bytes() == (ROOT / ".codex/skills" / REVIEW / "SKILL.md").read_bytes()
    assert (skill / "resources/capability.json").is_file()
    assert not (tmp_path / ".codex/skills").exists()
    assert state(tmp_path)["selection"] == [f"codex:skill:{REVIEW}"]


@pytest.mark.parametrize("existing", [False, True])
def test_strict_provider_requires_binary_even_with_existing_surface(tmp_path, existing):
    if existing:
        (tmp_path / ".agents/skills").mkdir(parents=True)
    result = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "codex", "--strict-cli"), 1)
    assert "MISSING_CLI: codex" in result["error"]
    assert not (tmp_path / ".core-prompts-state").exists()


def test_surface_only_requires_explicit_slug(tmp_path):
    result = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "kiro", "--surface-only"), 1)
    assert "--surface-only requires --slug" in result["error"]
    assert list(tmp_path.iterdir()) == []


def test_surface_only_installs_selected_skill_agent_and_scoped_receipt(tmp_path):
    receipt = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "kiro", "--slug", ARCH, "--surface-only"))
    assert receipt["transaction"]
    for rel in (f".kiro/skills/{ARCH}/SKILL.md", f".kiro/skills/{ARCH}/resources/capability.json",
                f".kiro/agents/{ARCH}.json", f".kiro/agents/resources/{ARCH}/capability.json"):
        assert (tmp_path / rel).read_bytes() == (ROOT / rel).read_bytes()
    assert not (tmp_path / ".kiro/skills" / REVIEW).exists()
    assert not (tmp_path / ".core-prompts-updater").exists()
    assert not (tmp_path / "update_core_prompts.sh").exists()
    assert not (tmp_path / ".local").exists()
    assert state(tmp_path)["selection"] == [f"kiro:agent:{ARCH}", f"kiro:skill:{ARCH}"]
    assert state(tmp_path)["runtime"] == {}


def test_external_dry_run_is_json_and_writes_nothing(tmp_path):
    plan = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "kiro", "--slug", REVIEW, "--dry-run"))
    assert plan["schema"] == 2 and plan["target"] == str(tmp_path)
    assert plan["blockers"] == []
    assert f".kiro/skills/{REVIEW}/SKILL.md" in paths(plan)
    assert ".core-prompts-updater/scripts/deploy-profile.py" in paths(plan)
    assert "update_core_prompts.sh" in paths(plan)
    assert ".core-prompts-state/installation.json" in paths(plan)
    assert list(tmp_path.iterdir()) == []


def test_install_wrapper_and_deploy_emit_identical_plans(tmp_path):
    args = ("--cli", "codex", "--slug", ARCH, "--surface-only", "--dry-run")
    deploy = document(external(DEPLOY_SCRIPT, tmp_path, *args))
    install = document(external(INSTALL_SCRIPT, tmp_path, "--mode", "copy", *args))
    assert install == deploy
    assert list(tmp_path.iterdir()) == []


def test_default_detected_providers_install_skills_without_agent_expansion(tmp_path):
    document(external(DEPLOY_SCRIPT, tmp_path, cli_bins=("codex", "gemini")))
    installed = state(tmp_path)
    assert {k.split(":")[0] for k in installed["selection"]} == {"codex", "gemini"}
    assert {k.split(":")[1] for k in installed["selection"]} == {"skill"}
    for provider in (".agents", ".gemini"):
        for slug in (REVIEW, AUTO):
            assert (tmp_path / provider / "skills" / slug / "SKILL.md").is_file()
            assert (tmp_path / provider / "skills" / slug / "resources/capability.json").is_file()
        assert (tmp_path / provider / "skills" / AUTO / "resources/bootstrap.py").is_file()
    assert not (tmp_path / ".codex/config.toml").exists()
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".kiro").exists()
    assert not (tmp_path / ".codex/agents").exists()


def test_with_agents_installs_full_resources_for_detected_providers(tmp_path):
    document(external(DEPLOY_SCRIPT, tmp_path, "--with-agents",
                      cli_bins=("codex", "gemini", "claude", "kiro-cli")))
    for provider, skill_root, extension in (("codex", ".agents", "toml"), ("gemini", ".gemini", "md"),
                                             ("claude", ".claude", "md"), ("kiro", ".kiro", "json")):
        for slug in (ARCH, AUTO, REVIEW):
            assert (tmp_path / skill_root / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / f".{provider}/agents/{ARCH}.{extension}").is_file()
        assert (tmp_path / f".{provider}/agents/resources/{ARCH}/capability.json").is_file()
        assert (tmp_path / f".{provider}/agents/resources/{AUTO}/bootstrap.py").is_file()
        assert not (tmp_path / f".{provider}/agents/{REVIEW}.{extension}").exists()
    text = (tmp_path / ".codex/config.toml").read_text()
    assert f"[agents.{ARCH}]" in text
    assert f"[agents.{REVIEW}]" not in text


def test_standalone_runtime_repeats_under_no_cli_path_without_scope_change(tmp_path):
    document(external(INSTALL_SCRIPT, tmp_path, "--cli", "codex", "--slug", ARCH))
    snapshot = state(tmp_path)
    bundled = tmp_path / ".core-prompts-updater"
    assert (bundled / "VERSION").read_bytes() == (ROOT / "VERSION").read_bytes()
    for rel in ("RELEASE_SOURCE.env", "scripts/deploy-profile.py", "scripts/deploy-surfaces.sh",
                "scripts/install-local.sh", "scripts/update-core-prompts.py"):
        assert (bundled / rel).is_file()
    assert os.access(tmp_path / "update_core_prompts.sh", os.X_OK)
    for _ in range(2):
        receipt = document(external(bundled / "scripts/deploy-surfaces.sh", tmp_path))
        assert receipt["status"] == "no-op"
        assert state(tmp_path) == snapshot
    assert not (tmp_path / ".gemini").exists()


def test_runtime_keeps_unknown_extra_files(tmp_path):
    stale = tmp_path / ".core-prompts-updater/scripts/custom.sh"
    stale.parent.mkdir(parents=True)
    stale.write_text("my independent script\n")
    document(external(INSTALL_SCRIPT, tmp_path, "--cli", "codex", "--slug", REVIEW))
    assert stale.read_text() == "my independent script\n"
    assert ".core-prompts-updater/scripts/custom.sh" not in state(tmp_path)["runtime"]


def test_customized_owned_skill_is_preserved_on_routine_update(tmp_path):
    document(external(INSTALL_SCRIPT, tmp_path, "--cli", "codex", "--slug", REVIEW))
    skill = tmp_path / ".agents/skills" / REVIEW / "SKILL.md"
    skill.write_text("my customized review\n")
    receipt = document(external(INSTALL_SCRIPT, tmp_path), 2)
    assert receipt["status"] == "applied-with-preserved"  # persists the newly detected conflict
    assert any(item.get("slug") == REVIEW for item in receipt["preserved"])
    assert skill.read_text() == "my customized review\n"
    repeat = document(external(INSTALL_SCRIPT, tmp_path), 2)
    assert repeat['status'] == 'no-op-with-preserved'


def test_historical_repair_migrates_only_proven_kiro_packages_and_can_rollback(tmp_path):
    original = seed_historical_architecture(tmp_path)
    receipt = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "kiro", "--repair"))
    assert state(tmp_path)["selection"] == [f"kiro:agent:{ARCH}", f"kiro:skill:{ARCH}"]
    assert all(not (tmp_path / rel).exists() for rel in original)
    assert (tmp_path / f".kiro/agents/{ARCH}.json").is_file()
    assert not (tmp_path / ".kiro/skills" / REVIEW).exists()
    restored = document(external(INSTALL_SCRIPT, tmp_path, "--rollback", receipt["transaction"]))
    assert restored["status"] == "rolled-back"
    assert all((tmp_path / rel).read_bytes() == content for rel, content in original.items())
    assert not (tmp_path / f".kiro/agents/{ARCH}.json").exists()


def test_forged_local_bundle_does_not_prove_legacy_ownership(tmp_path):
    rel = ".kiro/skills/architecture/SKILL.md"
    for root in (tmp_path, tmp_path / ".core-prompts-updater"):
        path = root / rel
        path.parent.mkdir(parents=True)
        path.write_text("arbitrary alleged legacy bytes\n")
    manifest = tmp_path / ".core-prompts-updater/.meta/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"surfaces": {"kiro_skill": [rel]}, "resources": {}}))
    plan = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "kiro", "--repair", "--dry-run"))
    assert any(item.get("slug") == "architecture" for item in plan["preserved"])
    assert all(action["path"] != rel for action in plan["actions"])
    blocked = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "kiro", "--repair"), 1)
    assert blocked["status"] == "blocked"
    assert any("RUNTIME_CONFLICT" in item for item in blocked["blockers"])
    assert (tmp_path / rel).read_text() == "arbitrary alleged legacy bytes\n"
    assert not (tmp_path / ".core-prompts-state").exists()


def test_custom_mentor_package_and_registration_remain_byte_exact(tmp_path):
    mentor = tmp_path / ".codex/agents/mentor.toml"
    mentor.parent.mkdir(parents=True)
    mentor.write_text('name = "my custom mentor"\n')
    config = tmp_path / ".codex/config.toml"
    original = '[agents.mentor]\nconfig_file = "/opt/custom-agents/mentor.toml"\n\n[agents.local-helper]\nconfig_file = "/tmp/local-helper.toml"\n'
    config.write_text(original)
    receipt = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "codex", "--repair"), 2)
    assert any(item.get("slug") == "mentor" for item in receipt["preserved"])
    assert mentor.read_text() == 'name = "my custom mentor"\n'
    assert config.read_text() == original


def test_symlinked_selected_package_preserves_referent_and_reports_attention(tmp_path):
    custom = tmp_path / "custom"
    custom.mkdir()
    (custom / "SKILL.md").write_text("outside package\n")
    package = tmp_path / ".kiro/skills" / REVIEW
    package.parent.mkdir(parents=True)
    package.symlink_to(custom, target_is_directory=True)
    receipt = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "kiro", "--slug", REVIEW, "--surface-only"), 2)
    assert receipt["preserved"]
    assert package.is_symlink()
    assert (custom / "SKILL.md").read_text() == "outside package\n"
    assert not (custom / "resources").exists()


def test_codex_registration_is_idempotent_and_preserves_custom_settings(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    custom = 'model = "my-custom-model"\n\n[agents.local-helper]\nconfig_file = "/opt/local-helper.toml"\n'
    config.write_text(custom)
    args = ("--cli", "codex", "--slug", ARCH, "--surface-only")
    document(external(DEPLOY_SCRIPT, tmp_path, *args))
    first = config.read_bytes()
    result = document(external(INSTALL_SCRIPT, tmp_path, *args))
    assert result["status"] == "no-op"
    assert config.read_bytes() == first
    assert config.read_text().startswith(custom)
    assert config.read_text().count(f"[agents.{ARCH}]") == 1


def test_invalid_duplicate_registration_is_preserved_instead_of_rewritten(tmp_path):
    config = tmp_path / ".codex/config.toml"
    config.parent.mkdir()
    original = f'[agents.{ARCH}]\nconfig_file = "/opt/one.toml"\n\n[agents.{ARCH}]\nconfig_file = "/opt/two.toml"\n'
    config.write_text(original)
    result = document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "codex", "--slug", ARCH, "--surface-only"), 2)
    assert any(".codex/config.toml" in item.get("roots", []) for item in result["preserved"])
    assert config.read_text() == original
    assert not (tmp_path / f".codex/agents/{ARCH}.toml").exists()


def test_reviewed_plan_is_applied_by_wrapper_and_changed_target_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    args = ("--cli", "kiro", "--slug", REVIEW, "--surface-only")
    plan = document(external(DEPLOY_SCRIPT, target, *args, "--dry-run"))
    saved = tmp_path / "approved.json"
    saved.write_text(json.dumps(plan))
    receipt = document(external(INSTALL_SCRIPT, target, "--apply-plan", str(saved)))
    assert receipt["status"] == "complete"
    second = document(external(INSTALL_SCRIPT, target, "--apply-plan", str(saved)), 1)
    assert second["code"] == "stale-plan"
    assert (target / f".kiro/skills/{REVIEW}/SKILL.md").is_file()


def test_install_help_and_copy_compatibility_contract(tmp_path):
    help_result = run_script(INSTALL_SCRIPT, "--help")
    assert help_result.returncode == 0
    assert "standalone updater bundle" in help_result.stdout
    assert "RELEASE_SOURCE.env" in help_result.stdout
    rejected = external(INSTALL_SCRIPT, tmp_path, "--mode", "link")
    assert rejected.returncode == 1
    assert "no longer supports link mode" in rejected.stdout
    assert list(tmp_path.iterdir()) == []


def test_explicit_unsupported_python_stops_before_capsule_or_target_changes(tmp_path):
    unsupported = tmp_path / "unsupported-python"
    unsupported.write_text("#!/bin/sh\nexit 1\n")
    unsupported.chmod(0o755)
    target = tmp_path / "target"
    target.mkdir()
    result = external(DEPLOY_SCRIPT, target, "--cli", "codex", env_overrides={"PYTHON_BIN": str(unsupported)})
    assert result.returncode == 1
    assert "requires Python 3.11+" in result.stdout
    assert "Traceback" not in result.stdout
    assert list(target.iterdir()) == []


def test_symlinked_target_root_is_rejected_without_changing_referent(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    result = document(external(DEPLOY_SCRIPT, alias, "--cli", "kiro", "--slug", REVIEW, "--surface-only"), 1)
    assert "symlink" in result["error"]
    assert alias.is_symlink()
    assert list(real.iterdir()) == []


def test_legacy_slug_alias_selects_canonical_codex_skill_and_agent(tmp_path):
    document(external(DEPLOY_SCRIPT, tmp_path, "--cli", "codex", "--slug", "autosearch", "--surface-only"))
    assert state(tmp_path)["selection"] == [f"codex:agent:{AUTO}", f"codex:skill:{AUTO}"]
    assert (tmp_path / f".agents/skills/{AUTO}/resources/bootstrap.py").is_file()
    assert (tmp_path / f".codex/agents/resources/{AUTO}/bootstrap.py").is_file()
    assert (tmp_path / f".codex/agents/{AUTO}.toml").is_file()
    assert not (tmp_path / ".codex/skills/autosearch").exists()
    assert not (tmp_path / ".agents/skills" / REVIEW).exists()
