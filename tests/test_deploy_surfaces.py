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

    for slug in ("converge", "mentor", "supercharge"):
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
    for slug in ("architecture", "converge", "docs-review-expert", "gitops-review", "mentor", "supercharge"):
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
