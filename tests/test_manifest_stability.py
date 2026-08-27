from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_SURFACES_PATH = ROOT / "scripts" / "build-surfaces.py"
BUILD_SURFACES_SPEC = importlib.util.spec_from_file_location(
    "build_surfaces_script",
    BUILD_SURFACES_PATH,
)
assert BUILD_SURFACES_SPEC is not None and BUILD_SURFACES_SPEC.loader is not None
BUILD_SURFACES = importlib.util.module_from_spec(BUILD_SURFACES_SPEC)
BUILD_SURFACES_SPEC.loader.exec_module(BUILD_SURFACES)


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


def test_write_kiro_agent_is_portable_and_preserves_runtime_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_dir = tmp_path / ".kiro" / "agents"
    agent_dir.mkdir(parents=True)
    monkeypatch.setattr(BUILD_SURFACES, "ROOT", tmp_path)
    monkeypatch.setattr(BUILD_SURFACES, "KIRO_AGENT_DIR", agent_dir)

    generated_path = BUILD_SURFACES.write_kiro_agent(
        "sample-agent",
        "Sample agent description.",
        "Follow the portable protocol.",
        "file://.kiro/agents/resources/sample-agent/capability.json",
        include_skill_ref=True,
    )

    payload = json.loads((tmp_path / generated_path).read_text(encoding="utf-8"))
    assert payload == {
        "name": "sample-agent",
        "description": "Sample agent description.",
        "prompt": (
            "# Sample Agent\n\n"
            "Follow the portable protocol.\n\n"
            "Capability resource: "
            "`file://.kiro/agents/resources/sample-agent/capability.json`\n"
        ),
        "resources": [
            "file://.kiro/agents/resources/sample-agent/capability.json",
            "skill://.kiro/skills/sample-agent/SKILL.md",
        ],
        "hooks": {},
        "tools": ["*"],
    }
    serialized = json.dumps(payload)
    assert "agentSpawn" not in serialized
    assert "./scripts/engos" not in serialized
    assert "./engos" not in serialized


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
