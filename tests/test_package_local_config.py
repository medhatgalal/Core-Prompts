from __future__ import annotations

import shutil
import json
import runpy
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


@pytest.mark.parametrize(
    "config_key", [".codex/config.toml", ".codex//config.toml", ".codex/./config.toml"]
)
def test_runtime_inventory_excludes_and_rejects_local_config(
    tmp_path: Path, config_key: str
) -> None:
    bundle = runpy.run_path(str(ROOT / "scripts/install_bundle.py"))
    for relative in (
        "VERSION", "scripts/deploy-profile.py", "scripts/update-core-prompts.py",
        ".codex/agents/sample.toml", ".codex/config.toml",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture: {relative}\n", encoding="utf-8")
    (tmp_path / ".meta").mkdir()
    bundle["build"](tmp_path)
    assert ".codex/config.toml" not in bundle["verified"](tmp_path)
    assert ".codex/agents/sample.toml" in bundle["verified"](tmp_path)

    manifest = tmp_path / bundle["MANIFEST"]
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["files"][config_key] = bundle["identity"](
        tmp_path / ".codex/config.toml"
    )
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        bundle["verified"](tmp_path)
    assert (tmp_path / ".codex/config.toml").read_text() == "fixture: .codex/config.toml\n"


def test_standalone_copy_excludes_source_local_config(tmp_path: Path) -> None:
    from test_deploy_surfaces import run_script

    repo = tmp_path / "repo"
    shutil.copytree(
        ROOT, repo,
        ignore=shutil.ignore_patterns(".git", "reports", "__pycache__", ".pytest_cache"),
    )
    source_config = repo / ".codex/config.toml"
    source_config.write_text('[agents.source_only]\nconfig_file = "/private/source.toml"\n')
    source_before = source_config.read_bytes()
    target = tmp_path / "home"
    result = run_script(
        repo / "scripts/deploy-surfaces.sh", "--cli", "codex",
        target_root=target, cli_bins=("codex",), allow_nonlocal_target=True,
    )
    assert result.returncode == 0, result.stdout
    assert not (target / ".core-prompts-updater/.codex/config.toml").exists()
    assert (target / ".codex/config.toml").is_file()
    assert source_config.read_bytes() == source_before
