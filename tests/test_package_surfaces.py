from __future__ import annotations

import subprocess
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package-surfaces.sh"


def test_package_version_must_match_version_file(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(PACKAGE_SCRIPT), "--version", "v0.0.0", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    assert result.returncode != 0
    assert "must match repo VERSION" in result.stdout


def test_package_boundary_includes_release_watch_contract(tmp_path: Path) -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    result = subprocess.run(
        [str(PACKAGE_SCRIPT), "--version", version, "--output-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )

    tar_path = tmp_path / f"core-prompts-{version}-surfaces.tar.gz"
    zip_path = tmp_path / f"core-prompts-{version}-surfaces.zip"
    assert tar_path.is_file(), result.stdout
    assert zip_path.is_file(), result.stdout

    with tarfile.open(tar_path, "r:gz") as archive:
        tar_names = set(archive.getnames())
    with zipfile.ZipFile(zip_path) as archive:
        zip_names = set(archive.namelist())

    expected = {
        "VERSION",
        "RELEASE_SOURCE.env",
        "scripts/update-core-prompts.py",
        "scripts/deploy-surfaces.sh",
        "scripts/install-local.sh",
    }
    assert expected <= tar_names
    assert expected <= zip_names
