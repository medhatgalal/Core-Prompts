from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = ROOT / "scripts" / "deploy-surfaces.sh"
INSTALL_SCRIPT = ROOT / "scripts" / "install-local.sh"


def make_fake_cli_bin(bin_dir: Path, *names: str) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        path = bin_dir / name
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def run_script(
    script: Path,
    *args: str,
    target_root: Path | None = None,
    cli_bins: tuple[str, ...] = (),
    use_system_bash: bool = False,
    env_overrides: dict[str, str] | None = None,
    allow_nonlocal_target: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    bin_dir = target_root / "fake-bin" if target_root is not None else None
    if cli_bins:
        if bin_dir is None:
            bin_dir = Path(tempfile.mkdtemp())
        make_fake_cli_bin(bin_dir, *cli_bins)
        path = f"{bin_dir}:/usr/bin:/bin"
    else:
        path = "/usr/bin:/bin"

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    env["PATH"] = path

    command = [str(script), *args]
    if target_root is not None:
        command.extend(["--target", str(target_root)])
    if target_root is not None and allow_nonlocal_target:
        command.append("--allow-nonlocal-target")
    if use_system_bash:
        command = ["/bin/bash", *command]
    try:
        return subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    finally:
        if target_root is None and bin_dir is not None:
            shutil.rmtree(bin_dir, ignore_errors=True)


def _collect_copy_destinations(output: str) -> set[Path]:
    copied: set[Path] = set()
    for line in output.splitlines():
        if line.startswith(("DRY-RUN COPY ", "COPIED ")):
            _, dst = line.rsplit(" -> ", 1)
            copied.add(Path(dst))
    return copied


def _collect_register_lines(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.startswith("DRY-RUN REGISTER")]


def test_deploy_defaults_to_repo_root_for_target_all() -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "all",
        "--dry-run",
        cli_bins=("codex", "gemini", "claude", "kiro-cli"),
        use_system_bash=True,
    )
    assert result.returncode == 0, result.stdout
    assert "Target CLIs: gemini claude kiro codex" in result.stdout

    copy_dests = _collect_copy_destinations(result.stdout)
    assert copy_dests
    root = str(ROOT)
    assert all(str(dst).startswith(root) for dst in copy_dests)
    for cli in (".codex", ".gemini", ".claude", ".kiro"):
        assert any(str(dst).startswith(f"{root}/{cli}/") for dst in copy_dests)

    register_lines = _collect_register_lines(result.stdout)
    assert any(f"DRY-RUN REGISTER codex agents in {ROOT}/.codex/config.toml" in line for line in register_lines)


def test_install_wrapper_defaults_to_repo_root_and_does_not_touch_home(tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    result = run_script(
        INSTALL_SCRIPT,
        "--cli",
        "all",
        "--dry-run",
        cli_bins=("codex", "gemini", "claude", "kiro-cli"),
        use_system_bash=True,
        env_overrides={"HOME": str(fake_home)},
    )
    assert result.returncode == 0, result.stdout
    assert "Target CLIs: gemini claude kiro codex" in result.stdout
    assert not (fake_home / ".codex" / "config.toml").exists()
    register_lines = _collect_register_lines(result.stdout)
    assert any(f"DRY-RUN REGISTER codex agents in {ROOT}/.codex/config.toml" in line for line in register_lines)


def test_deploy_succeeds_with_no_clis_in_non_strict_mode_under_system_bash(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout
    assert "warning: no target CLIs selected" in result.stdout
    assert "SUMMARY copied=0 missing_source=0 skipped_cli=1" in result.stdout


def test_install_wrapper_succeeds_with_no_clis_in_non_strict_mode(tmp_path: Path) -> None:
    result = run_script(
        INSTALL_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout
    assert "warning: no target CLIs selected" in result.stdout
    assert "SUMMARY copied=0 missing_source=0 skipped_cli=1" in result.stdout


def test_installed_bundle_syncs_existing_surfaces_under_cron_path_without_self_copy(tmp_path: Path) -> None:
    first_install = run_script(
        INSTALL_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex", "gemini", "claude", "kiro-cli"),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert first_install.returncode == 0, first_install.stdout

    installed_skill = tmp_path / ".codex" / "skills" / "instruction-editor" / "SKILL.md"
    bundled_skill = tmp_path / ".core-prompts-updater" / ".codex" / "skills" / "instruction-editor" / "SKILL.md"
    assert installed_skill.is_file()
    assert bundled_skill.is_file()
    installed_skill.write_text("stale installed skill\n", encoding="utf-8")

    bundled_deploy = tmp_path / ".core-prompts-updater" / "scripts" / "deploy-surfaces.sh"
    scheduled_sync = run_script(
        bundled_deploy,
        "--cli",
        "all",
        target_root=tmp_path,
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert scheduled_sync.returncode == 0, scheduled_sync.stdout
    assert "Target CLIs: gemini claude kiro codex" in scheduled_sync.stdout
    assert "using existing 'codex' target surface" in scheduled_sync.stdout
    assert "SameFileError" not in scheduled_sync.stdout
    assert installed_skill.read_text(encoding="utf-8") == bundled_skill.read_text(encoding="utf-8")


def test_nonlocal_install_writes_standalone_updater_bundle_and_prunes_stale_files(tmp_path: Path) -> None:
    stale = tmp_path / ".core-prompts-updater" / "scripts" / "stale.sh"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")

    result = run_script(
        INSTALL_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    assert (tmp_path / "update_core_prompts.sh").is_file()
    assert os.access(tmp_path / "update_core_prompts.sh", os.X_OK)
    assert (tmp_path / ".core-prompts-updater" / "VERSION").read_text(encoding="utf-8").strip() == (
        ROOT / "VERSION"
    ).read_text(encoding="utf-8").strip()
    assert (tmp_path / ".core-prompts-updater" / "RELEASE_SOURCE.env").is_file()
    local_repo = (tmp_path / ".core-prompts-updater" / "LOCAL_REPO.env").read_text(encoding="utf-8")
    assert f"REPO_PATH={ROOT}" in local_repo
    assert "REMOTE_NAME=origin" in local_repo
    assert (tmp_path / ".core-prompts-updater" / "scripts" / "update-core-prompts.py").is_file()
    assert (tmp_path / ".core-prompts-updater" / "scripts" / "deploy-surfaces.sh").is_file()
    assert (tmp_path / ".core-prompts-updater" / "scripts" / "install-local.sh").is_file()
    assert not stale.exists()


def test_install_help_mentions_release_watch_metadata() -> None:
    result = run_script(INSTALL_SCRIPT, "--help")

    assert result.returncode == 0
    assert "standalone updater bundle" in result.stdout
    assert "RELEASE_SOURCE.env" in result.stdout


def test_surface_only_requires_an_explicit_slug(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "kiro",
        "--surface-only",
        target_root=tmp_path,
        cli_bins=("kiro-cli",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 1
    assert "--surface-only requires at least one --slug" in result.stdout
    assert not (tmp_path / ".kiro").exists()


def test_surface_only_nonlocal_deploy_writes_only_selected_kiro_bundle(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "kiro",
        "--slug",
        "code-review",
        "--surface-only",
        target_root=tmp_path,
        cli_bins=("kiro-cli",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    assert (tmp_path / ".kiro" / "skills" / "code-review" / "SKILL.md").is_file()
    assert (tmp_path / ".kiro" / "skills" / "code-review" / "resources" / "capability.json").is_file()
    assert not (tmp_path / ".kiro" / "skills" / "architecture").exists()
    assert not (tmp_path / ".core-prompts-updater").exists()
    assert not (tmp_path / "update_core_prompts.sh").exists()
    assert not (tmp_path / ".local" / "bin" / "eng-report").exists()
    assert "STANDALONE updater=" not in result.stdout


def test_nonlocal_dry_run_does_not_write_updater_launcher_or_local_binary(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "kiro",
        "--slug",
        "code-review",
        "--dry-run",
        target_root=tmp_path,
        cli_bins=("kiro-cli",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    assert not (tmp_path / ".kiro").exists()
    assert not (tmp_path / ".core-prompts-updater").exists()
    assert not (tmp_path / "update_core_prompts.sh").exists()
    assert not (tmp_path / ".local" / "bin" / "eng-report").exists()
    assert f"DRY-RUN WRITE {tmp_path}/.local/bin/eng-report" in result.stdout


def test_deploy_fails_in_strict_mode_when_selected_cli_is_missing(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        "--strict-cli",
        target_root=tmp_path,
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 1, result.stdout
    assert "error: missing required CLI binary for target 'codex'" in result.stdout


def test_deploy_strict_mode_still_requires_binary_for_existing_managed_surface(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir()
    support = tmp_path / ".core-prompts-updater"
    support.mkdir()
    (support / "VERSION").write_text("v1.10.1\n", encoding="utf-8")

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        "--strict-cli",
        target_root=tmp_path,
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 1, result.stdout
    assert "error: missing required CLI binary for target 'codex'" in result.stdout


def test_unmanaged_cli_directory_does_not_bypass_binary_detection(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir()

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        target_root=tmp_path,
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    assert "selected CLI 'codex' is unavailable; skipping" in result.stdout
    assert "Target CLIs:" not in result.stdout


def test_deploy_with_only_codex_available_registers_only_codex_agents(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout
    assert "Target CLIs: codex" in result.stdout

    for slug in ("code-review", "resolve-conflict"):
        assert (tmp_path / ".codex" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".codex" / "skills" / slug / "resources" / "capability.json").is_file()
        assert not (tmp_path / ".codex" / "agents" / f"{slug}.toml").exists()

    assert (tmp_path / ".codex" / "skills" / "auto-research" / "resources" / "bootstrap.py").is_file()
    assert (
        tmp_path
        / ".codex"
        / "skills"
        / "auto-research"
        / "resources"
        / "templates"
        / "goal-contract.md.tmpl"
    ).is_file()
    assert (tmp_path / ".codex" / "agents" / "resources" / "auto-research" / "bootstrap.py").is_file()

    config_text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    for slug in ("converge", "supercharge"):
        assert f"[agents.{slug}]" in config_text
    for slug in ("code-review", "resolve-conflict"):
        assert f"[agents.{slug}]" not in config_text


def test_deploy_with_all_clis_available_deploys_new_skill_surfaces(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex", "gemini", "claude", "kiro-cli"),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout

    for slug in ("code-review", "resolve-conflict"):
        assert (tmp_path / ".codex" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".codex" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".claude" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".claude" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "resources" / "capability.json").is_file()
        assert not (tmp_path / ".gemini" / "agents" / f"{slug}.md").exists()
        assert not (tmp_path / ".claude" / "agents" / f"{slug}.md").exists()
        assert not (tmp_path / ".kiro" / "agents" / f"{slug}.json").exists()
        assert not (tmp_path / ".codex" / "agents" / f"{slug}.toml").exists()

    for slug in ("converge", "supercharge"):
        assert (tmp_path / ".codex" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".codex" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".codex" / "agents" / f"{slug}.toml").is_file()
        assert (tmp_path / ".codex" / "agents" / "resources" / slug / "capability.json").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".gemini" / "agents" / f"{slug}.md").is_file()
        assert (tmp_path / ".gemini" / "agents" / "resources" / slug / "capability.json").is_file()
        assert (tmp_path / ".claude" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".claude" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".claude" / "agents" / f"{slug}.md").is_file()
        assert (tmp_path / ".claude" / "agents" / "resources" / slug / "capability.json").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".kiro" / "agents" / f"{slug}.json").is_file()
        assert (tmp_path / ".kiro" / "agents" / "resources" / slug / "capability.json").is_file()

    for cli_dir in (".codex", ".gemini", ".claude", ".kiro"):
        assert (tmp_path / cli_dir / "skills" / "auto-research" / "resources" / "bootstrap.py").is_file()
        assert (
            tmp_path
            / cli_dir
            / "skills"
            / "auto-research"
            / "resources"
            / "templates"
            / "scorecard.json.tmpl"
        ).is_file()

    assert (tmp_path / ".codex" / "agents" / "resources" / "auto-research" / "bootstrap.py").is_file()
    assert (
        tmp_path
        / ".gemini"
        / "agents"
        / "resources"
        / "auto-research"
        / "templates"
        / "promotion-packet.md.tmpl"
    ).is_file()
    assert (
        tmp_path
        / ".claude"
        / "agents"
        / "resources"
        / "auto-research"
        / "templates"
        / "experiment-ledger.md.tmpl"
    ).is_file()
    assert (
        tmp_path
        / ".kiro"
        / "agents"
        / "resources"
        / "auto-research"
        / "templates"
        / "goal-contract.md.tmpl"
    ).is_file()

    legacy_direct_paths = (
        tmp_path / ".gemini" / "commands",
        tmp_path / ".claude" / "commands",
        tmp_path / ".codex" / "prompts",
        tmp_path / ".kiro" / "prompts",
        tmp_path / ".agents" / "prompts",
        tmp_path / ".agents" / "commands",
    )
    assert all(not path.exists() for path in legacy_direct_paths)


def test_install_wrapper_matches_deploy_for_partial_cli_targets(tmp_path: Path) -> None:
    result = run_script(
        INSTALL_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex", "gemini"),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout
    assert "Target CLIs: gemini codex" in result.stdout
    assert (tmp_path / ".gemini" / "skills" / "code-review" / "SKILL.md").is_file()
    assert (tmp_path / ".codex" / "skills" / "resolve-conflict" / "SKILL.md").is_file()
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".kiro").exists()


def test_deploy_codex_registration_is_idempotent(tmp_path: Path) -> None:
    first = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert first.returncode == 0, first.stdout

    second = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert second.returncode == 0, second.stdout

    config_text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    for slug in ("architecture", "converge", "docs-review-expert", "gitops-review", "supercharge"):
        assert config_text.count(f"[agents.{slug}]") == 1


def test_deploy_codex_registration_removes_legacy_duplicate_stanzas(tmp_path: Path) -> None:
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                'model = "gpt-5.4"',
                "",
                "[agents.supercharge]",
                'config_file = "/tmp/legacy-supercharge.toml"',
                "",
                "[agents.unmanaged-custom]",
                'config_file = "/tmp/custom.toml"',
                "",
                "# >>> core-prompts codex agents start >>>",
                "[agents.supercharge]",
                'config_file = "/tmp/stale-supercharge.toml"',
                "",
                "[agents.converge]",
                'config_file = "/tmp/stale-converge.toml"',
                "",
                "# <<< core-prompts codex agents end <<<",
                "",
                "[agents.docs-review-expert]",
                'config_file = "/tmp/legacy-docs-review.toml"',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout

    config_text = config_path.read_text(encoding="utf-8")
    assert config_text.count("[agents.supercharge]") == 1
    assert config_text.count("[agents.converge]") == 1
    assert config_text.count("[agents.docs-review-expert]") == 1
    assert "[agents.unmanaged-custom]" in config_text
    assert "/tmp/legacy-supercharge.toml" not in config_text
    assert "/tmp/stale-supercharge.toml" not in config_text
    assert "/tmp/stale-converge.toml" not in config_text
    assert "/tmp/legacy-docs-review.toml" not in config_text


def test_deploy_codex_registration_completes_with_populated_home_style_config(tmp_path: Path) -> None:
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                'model = "gpt-5.4"',
                "",
                "[agents.local-helper]",
                'config_file = "/tmp/local-helper.toml"',
                "",
                "# >>> core-prompts codex agents start >>>",
                "[agents.autosearch]",
                'config_file = "/tmp/stale-autosearch.toml"',
                "",
                "# <<< core-prompts codex agents end <<<",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex", "gemini", "claude", "kiro-cli"),
        allow_nonlocal_target=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout
    assert "REGISTERED codex agents in" in result.stdout
    assert "SUMMARY copied=" in result.stdout

    config_text = config_path.read_text(encoding="utf-8")
    assert "[agents.local-helper]" in config_text
    assert "[agents.autosearch]" not in config_text
    assert "/tmp/stale-autosearch.toml" not in config_text
    for slug in (
        "architecture",
        "auto-research",
        "converge",
        "docs-review-expert",
        "gitops-review",
        "supercharge",
        "weekly-intel",
    ):
        assert config_text.count(f"[agents.{slug}]") == 1


def test_deploy_retires_mentor_surfaces_and_registration_without_harming_unrelated_state(
    tmp_path: Path,
) -> None:
    mentor_paths = (
        tmp_path / ".codex" / "skills" / "mentor",
        tmp_path / ".codex" / "agents" / "mentor.toml",
        tmp_path / ".codex" / "agents" / "resources" / "mentor",
        tmp_path / ".gemini" / "skills" / "mentor",
        tmp_path / ".gemini" / "agents" / "mentor.md",
        tmp_path / ".gemini" / "agents" / "resources" / "mentor",
        tmp_path / ".claude" / "skills" / "mentor",
        tmp_path / ".claude" / "agents" / "mentor.md",
        tmp_path / ".claude" / "agents" / "resources" / "mentor",
        tmp_path / ".kiro" / "skills" / "mentor",
        tmp_path / ".kiro" / "agents" / "mentor.json",
        tmp_path / ".kiro" / "agents" / "resources" / "mentor",
    )
    for path in mentor_paths:
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stale mentor\n", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / "stale.txt").write_text("stale mentor\n", encoding="utf-8")

    preserved_skill = tmp_path / ".codex" / "skills" / "local-helper" / "SKILL.md"
    preserved_skill.parent.mkdir(parents=True, exist_ok=True)
    preserved_skill.write_text("local helper\n", encoding="utf-8")
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[agents.mentor]",
                f'config_file = "{tmp_path / ".codex" / "agents" / "mentor.toml"}"',
                "",
                "[agents.local-helper]",
                'config_file = "/tmp/local-helper.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex", "gemini", "claude", "kiro-cli"),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    assert "stale_pruned=12" in result.stdout
    assert all(not path.exists() for path in mentor_paths)
    assert preserved_skill.read_text(encoding="utf-8") == "local helper\n"
    config_text = config_path.read_text(encoding="utf-8")
    assert "[agents.mentor]" not in config_text
    assert str(tmp_path / ".codex" / "agents" / "mentor.toml") not in config_text
    assert "[agents.local-helper]" in config_text
    assert "/tmp/local-helper.toml" in config_text
    archived = tmp_path / ".core-prompts-state" / "stale-pruned"
    assert len(list(archived.glob("**/mentor*"))) == 12


def test_filtered_mentor_retirement_prunes_codex_files_and_registration(
    tmp_path: Path,
) -> None:
    mentor_paths = (
        tmp_path / ".codex" / "skills" / "mentor",
        tmp_path / ".codex" / "agents" / "mentor.toml",
        tmp_path / ".codex" / "agents" / "resources" / "mentor",
    )
    for path in mentor_paths:
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stale mentor\n", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / "stale.txt").write_text("stale mentor\n", encoding="utf-8")

    config_path = tmp_path / ".codex" / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "# >>> core-prompts codex agents start >>>",
                "[agents.batman]",
                f'config_file = "{tmp_path / ".codex" / "agents" / "batman.toml"}"',
                "",
                "[agents.mentor]",
                f'config_file = "{tmp_path / ".codex" / "agents" / "mentor.toml"}"',
                "",
                "# <<< core-prompts codex agents end <<<",
                "",
                "[agents.local-helper]",
                'config_file = "/tmp/local-helper.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        "--slug",
        "mentor",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    assert "warning: nothing to deploy for selected CLI targets" in result.stdout
    assert "stale_pruned=3" in result.stdout
    assert all(not path.exists() for path in mentor_paths)
    config_text = config_path.read_text(encoding="utf-8")
    assert "[agents.mentor]" not in config_text
    assert str(tmp_path / ".codex" / "agents" / "mentor.toml") not in config_text
    assert "[agents.batman]" in config_text
    assert str(tmp_path / ".codex" / "agents" / "batman.toml") in config_text
    assert "[agents.local-helper]" in config_text
    assert "/tmp/local-helper.toml" in config_text
    archived = tmp_path / ".core-prompts-state" / "stale-pruned"
    assert len(list(archived.glob("**/mentor*"))) == 3


def test_filtered_mentor_retirement_preserves_custom_registration(tmp_path: Path) -> None:
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                "[agents.mentor]",
                'config_file = "/opt/custom-agents/mentor.toml"',
                "",
                "[agents.local-helper]",
                'config_file = "/tmp/local-helper.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        "--slug",
        "mentor",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    config_text = config_path.read_text(encoding="utf-8")
    assert "[agents.mentor]" in config_text
    assert 'config_file = "/opt/custom-agents/mentor.toml"' in config_text
    assert "[agents.local-helper]" in config_text
    assert 'config_file = "/tmp/local-helper.toml"' in config_text


def test_deploy_slug_filter_limits_copy_and_registration(tmp_path: Path) -> None:
    stale_skill = tmp_path / ".codex" / "skills" / "autosearch" / "SKILL.md"
    stale_agent = tmp_path / ".codex" / "agents" / "autosearch.toml"
    stale_resource = tmp_path / ".codex" / "agents" / "resources" / "autosearch" / "capability.json"
    for path in (stale_skill, stale_agent, stale_resource):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("stale", encoding="utf-8")

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        "--slug",
        "auto-research",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout
    assert "Deploying managed slugs: auto-research" in result.stdout
    assert (tmp_path / ".codex" / "skills" / "auto-research" / "SKILL.md").is_file()
    assert (tmp_path / ".codex" / "skills" / "auto-research" / "resources" / "bootstrap.py").is_file()
    assert not (tmp_path / ".codex" / "skills" / "autosearch").exists()
    assert not (tmp_path / ".codex" / "agents" / "autosearch.toml").exists()
    assert not (tmp_path / ".codex" / "agents" / "resources" / "autosearch").exists()
    assert not (tmp_path / ".codex" / "skills" / "code-review" / "SKILL.md").exists()

    config_text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "[agents.auto-research]" in config_text
    assert "[agents.converge]" not in config_text


def test_deploy_legacy_autosearch_slug_installs_auto_research_and_prunes_stale(tmp_path: Path) -> None:
    stale_skill = tmp_path / ".codex" / "skills" / "autosearch" / "SKILL.md"
    stale_agent = tmp_path / ".codex" / "agents" / "autosearch.toml"
    stale_resource = tmp_path / ".codex" / "agents" / "resources" / "autosearch" / "capability.json"
    for path in (stale_skill, stale_agent, stale_resource):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("stale", encoding="utf-8")

    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        "--slug",
        "autosearch",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
        allow_nonlocal_target=True,
    )

    assert result.returncode == 0, result.stdout
    assert "Deploying managed slugs: auto-research" in result.stdout
    assert "stale_pruned=3" in result.stdout
    assert (tmp_path / ".codex" / "skills" / "auto-research" / "SKILL.md").is_file()
    assert not (tmp_path / ".codex" / "skills" / "autosearch").exists()
    assert not (tmp_path / ".codex" / "agents" / "autosearch.toml").exists()
    assert not (tmp_path / ".codex" / "agents" / "resources" / "autosearch").exists()
    assert list((tmp_path / ".core-prompts-state" / "stale-pruned").glob("**/autosearch*"))
