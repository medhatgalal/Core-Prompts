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
    retired_repo_paths = (
        ROOT / ".codex" / "skills" / "mentor",
        ROOT / ".codex" / "agents" / "resources" / "mentor",
        ROOT / ".gemini" / "skills" / "mentor",
        ROOT / ".gemini" / "agents" / "resources" / "mentor",
        ROOT / ".claude" / "skills" / "mentor",
        ROOT / ".claude" / "agents" / "resources" / "mentor",
        ROOT / ".kiro" / "skills" / "mentor",
        ROOT / ".kiro" / "agents" / "resources" / "mentor",
        ROOT / "sources" / "ssot-baselines" / "mentor",
    )
    assert all(not path.exists() for path in retired_repo_paths)

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
        ".meta/evaluation-policy.json",
        ".meta/instruction-clarity.json",
        ".meta/skill-job-map.json",
        "docs/CAPABILITY-EVALUATION.md",
        "docs/SKILL-JOB-MAP.md",
        "scripts/update-core-prompts.py",
        "scripts/deploy-surfaces.sh",
        "scripts/install-local.sh",
    }
    assert expected <= tar_names
    assert expected <= zip_names

    retired_package_paths = (
        ".codex/skills/mentor/",
        ".codex/agents/mentor.toml",
        ".codex/agents/resources/mentor/",
        ".gemini/skills/mentor/",
        ".gemini/agents/mentor.md",
        ".gemini/agents/resources/mentor/",
        ".claude/skills/mentor/",
        ".claude/agents/mentor.md",
        ".claude/agents/resources/mentor/",
        ".kiro/skills/mentor/",
        ".kiro/agents/mentor.json",
        ".kiro/agents/resources/mentor/",
        "sources/ssot-baselines/mentor/",
    )
    for names in (tar_names, zip_names):
        assert not any(
            name == retired.rstrip("/") or name.startswith(retired)
            for name in names
            for retired in retired_package_paths
        )
