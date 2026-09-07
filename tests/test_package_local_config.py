from __future__ import annotations

import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("existing_archive", [False, True])
def test_package_excludes_local_codex_registration(
    tmp_path: Path, existing_archive: bool
) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(
        ROOT,
        repo,
        ignore=shutil.ignore_patterns(".git", "reports", "__pycache__", ".pytest_cache"),
    )
    config = repo / ".codex" / "config.toml"
    local_config = '[agents.local]\nconfig_file = "/private/local-checkout/agent.toml"\n'
    config.write_text(local_config, encoding="utf-8")
    version = (repo / "VERSION").read_text(encoding="utf-8").strip()
    output = tmp_path / "packages"
    stem = f"core-prompts-{version}-surfaces"
    if existing_archive:
        output.mkdir()
        with zipfile.ZipFile(output / f"{stem}.zip", "w") as archive:
            archive.writestr(".codex/config.toml", local_config)
            archive.writestr("stale-output-only.txt", "previous archive member")
    subprocess.run(
        [str(repo / "scripts/package-surfaces.sh"), "--version", version,
         "--output-dir", str(output)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    with tarfile.open(output / f"{stem}.tar.gz", "r:gz") as archive:
        tar_names = set(archive.getnames())
    with zipfile.ZipFile(output / f"{stem}.zip") as archive:
        zip_names = set(archive.namelist())
    for names in (tar_names, zip_names):
        assert ".codex/config.toml" not in names
        assert "stale-output-only.txt" not in names
        assert any(
            name.startswith(".codex/agents/") and name.endswith(".toml")
            for name in names
        )
        assert any(
            name.startswith(".codex/skills/") and name.endswith("/SKILL.md")
            for name in names
        )
        assert any(
            name.startswith(".codex/agents/resources/")
            and name.endswith("/capability.json")
            for name in names
        )
    assert config.read_text(encoding="utf-8") == local_config
