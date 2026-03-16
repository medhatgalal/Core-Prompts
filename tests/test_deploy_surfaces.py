from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


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
    target_root: Path,
    cli_bins: tuple[str, ...] = (),
    use_system_bash: bool = False,
) -> subprocess.CompletedProcess[str]:
    bin_dir = target_root / "fake-bin"
    if cli_bins:
        make_fake_cli_bin(bin_dir, *cli_bins)
        path = f"{bin_dir}:/usr/bin:/bin"
    else:
        path = "/usr/bin:/bin"

    env = os.environ.copy()
    env["PATH"] = path
    command = [str(script), *args, "--target", str(target_root)]
    if use_system_bash:
        command = ["/bin/bash", str(script), *args, "--target", str(target_root)]
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def test_deploy_succeeds_with_no_clis_in_non_strict_mode_under_system_bash(tmp_path: Path) -> None:
    result = run_script(DEPLOY_SCRIPT, "--cli", "all", target_root=tmp_path, use_system_bash=True)
    assert result.returncode == 0, result.stdout
    assert "warning: no target CLIs selected" in result.stdout
    assert "SUMMARY copied=0 missing_source=0 skipped_cli=1" in result.stdout


def test_install_wrapper_succeeds_with_no_clis_in_non_strict_mode(tmp_path: Path) -> None:
    result = run_script(INSTALL_SCRIPT, "--cli", "all", target_root=tmp_path)
    assert result.returncode == 0, result.stdout
    assert "warning: no target CLIs selected" in result.stdout
    assert "SUMMARY copied=0 missing_source=0 skipped_cli=1" in result.stdout


def test_deploy_fails_in_strict_mode_when_selected_cli_is_missing(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "codex",
        "--strict-cli",
        target_root=tmp_path,
        use_system_bash=True,
    )
    assert result.returncode == 1, result.stdout
    assert "error: missing required CLI binary for target 'codex'" in result.stdout


def test_deploy_with_only_codex_available_registers_only_codex_agents(tmp_path: Path) -> None:
    result = run_script(
        DEPLOY_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex",),
        use_system_bash=True,
    )
    assert result.returncode == 0, result.stdout
    assert "Target CLIs: codex" in result.stdout

    for slug in ("code-review", "resolve-conflict"):
        assert (tmp_path / ".codex" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".codex" / "skills" / slug / "resources" / "capability.json").is_file()
        assert not (tmp_path / ".codex" / "agents" / f"{slug}.toml").exists()

    config_text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    for slug in ("converge", "mentor", "supercharge"):
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
    )
    assert result.returncode == 0, result.stdout

    for slug in ("code-review", "resolve-conflict"):
        assert (tmp_path / ".codex" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".codex" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".gemini" / "commands" / f"{slug}.toml").is_file()
        assert (tmp_path / ".claude" / "commands" / f"{slug}.md").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".kiro" / "prompts" / f"{slug}.md").is_file()
        assert not (tmp_path / ".gemini" / "agents" / f"{slug}.md").exists()
        assert not (tmp_path / ".claude" / "agents" / f"{slug}.md").exists()
        assert not (tmp_path / ".kiro" / "agents" / f"{slug}.json").exists()
        assert not (tmp_path / ".codex" / "agents" / f"{slug}.toml").exists()

    for slug in ("converge", "mentor", "supercharge"):
        assert (tmp_path / ".codex" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".codex" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".codex" / "agents" / f"{slug}.toml").is_file()
        assert (tmp_path / ".codex" / "agents" / "resources" / slug / "capability.json").is_file()
        assert (tmp_path / ".gemini" / "commands" / f"{slug}.toml").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".gemini" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".gemini" / "agents" / f"{slug}.md").is_file()
        assert (tmp_path / ".gemini" / "agents" / "resources" / slug / "capability.json").is_file()
        assert (tmp_path / ".claude" / "commands" / f"{slug}.md").is_file()
        assert (tmp_path / ".claude" / "agents" / f"{slug}.md").is_file()
        assert (tmp_path / ".claude" / "agents" / "resources" / slug / "capability.json").is_file()
        assert (tmp_path / ".kiro" / "prompts" / f"{slug}.md").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "SKILL.md").is_file()
        assert (tmp_path / ".kiro" / "skills" / slug / "resources" / "capability.json").is_file()
        assert (tmp_path / ".kiro" / "agents" / f"{slug}.json").is_file()
        assert (tmp_path / ".kiro" / "agents" / "resources" / slug / "capability.json").is_file()


def test_install_wrapper_matches_deploy_for_partial_cli_targets(tmp_path: Path) -> None:
    result = run_script(
        INSTALL_SCRIPT,
        "--cli",
        "all",
        target_root=tmp_path,
        cli_bins=("codex", "gemini"),
        use_system_bash=True,
    )
    assert result.returncode == 0, result.stdout
    assert "Target CLIs: gemini codex" in result.stdout
    assert (tmp_path / ".gemini" / "commands" / "code-review.toml").is_file()
    assert (tmp_path / ".codex" / "skills" / "resolve-conflict" / "SKILL.md").is_file()
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".kiro").exists()
