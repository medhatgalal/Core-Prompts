from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def copy_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    shutil.copytree(
        ROOT,
        workspace,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".DS_Store", ".venv", "node_modules", "dist", "reports"),
    )
    return workspace


def run_script(workspace: Path, script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(workspace / "scripts" / script_name), *args],
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def test_build_and_validate_keep_manifest_content_stable(tmp_path: Path) -> None:
    workspace = copy_workspace(tmp_path)

    build_first = run_script(workspace, "build-surfaces.py")
    assert build_first.returncode == 0, build_first.stdout

    manifest_path = workspace / ".meta" / "manifest.json"
    first_manifest = manifest_path.read_text(encoding="utf-8")
    manifest_payload = json.loads(first_manifest)
    assert "generated_at" not in manifest_payload
    assert "validation" not in manifest_payload

    build_second = run_script(workspace, "build-surfaces.py")
    assert build_second.returncode == 0, build_second.stdout
    assert manifest_path.read_text(encoding="utf-8") == first_manifest

    validate_first = run_script(workspace, "validate-surfaces.py")
    assert validate_first.returncode == 0, validate_first.stdout
    after_validate = manifest_path.read_text(encoding="utf-8")
    assert after_validate == first_manifest

    validation_dir = workspace / "reports" / "validation"
    build_report_dir = workspace / "reports" / "build-surfaces"
    assert (validation_dir / "latest.json").is_file()
    assert (build_report_dir / "latest.json").is_file()
    latest_validation = json.loads((validation_dir / "latest.json").read_text(encoding="utf-8"))
    assert latest_validation["manifest_file"] == ".meta/manifest.json"
    assert "validated_at" in latest_validation

    time.sleep(0.02)
    validate_second = run_script(workspace, "validate-surfaces.py")
    assert validate_second.returncode == 0, validate_second.stdout
    assert manifest_path.read_text(encoding="utf-8") == first_manifest

    validation_reports = sorted(validation_dir.glob("*.json"))
    assert len(validation_reports) >= 3  # latest.json + two timestamped runs
