from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_uac_import_local_file_flow(tmp_path: Path) -> None:
    sample = tmp_path / "prompt.md"
    sample.write_text(
        """# API Design\n\nPrimary Objective: Produce a reusable API design prompt.\n\nIn Scope:\n- Normalize endpoint requirements\n- Preserve acceptance criteria\n\nOut of Scope:\n- Live API calls\n\nConstraints:\n- Deterministic output only\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--source", str(sample)],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "accepted"
    assert payload["uac"]["capability_type"] == "skill"
    assert payload["uac"]["recommended_surface"] == "skill"
    assert payload["source"]["normalized_source"] == str(sample.resolve())
    assert payload["routing"]["decision"] in {"PASS_ROUTE", "NEEDS_REVIEW"}
    assert "manifest" in payload
    assert "cross_analysis" in payload
    assert payload["handoff_contract"]["advisory_only"] is True


def test_uac_import_respects_target_system_override(tmp_path: Path) -> None:
    sample = tmp_path / "prompt.md"
    sample.write_text(
        """Primary Objective: Normalize this prompt.\n\nIn Scope:\n- Package for Codex\n\nConstraints:\n- Deterministic output only\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "uac-import.py"),
            "--source",
            str(sample),
            "--target-system",
            "codex",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["recommendation"]["primary_target_systems"] == ["codex"]
    assert payload["recommendation"]["install_target"]["recommended"] in {"repo_local", "global", "both"}


def test_uac_import_local_directory_flow(tmp_path: Path) -> None:
    (tmp_path / "design-api.toml").write_text(
        'prompt = """Primary Objective: Design an API prompt.\n\nIn Scope:\n- Request contracts\n\nConstraints:\n- Deterministic\n"""\n',
        encoding="utf-8",
    )
    (tmp_path / "system-design.toml").write_text(
        'prompt = """Primary Objective: Design a system prompt.\n\nIn Scope:\n- Architecture review\n\nConstraints:\n- Explicit trade-offs\n"""\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--source", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "accepted"
    assert payload["source"]["type"] == "LOCAL_DIRECTORY"
    assert payload["collection"]["collection_type"] == "skill_family"
    assert payload["items"][0]["extraction"]["wrapper_kind"] == "toml_prompt"
    assert len(payload["items"]) == 2
    assert payload["manifest"]["layers"]["minimal"]["install_target"]["recommended"] in {"repo_local", "global", "both"}


def test_uac_import_can_emit_rubric(tmp_path: Path) -> None:
    sample = tmp_path / "prompt.md"
    sample.write_text(
        """Primary Objective: Normalize this prompt.\n\nIn Scope:\n- Package for Codex\n\nConstraints:\n- Deterministic output only\n""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--source", str(sample), "--show-rubric"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert "classification_rubric" in payload
    assert "skill" in payload["classification_rubric"]
    assert "agent" in payload["classification_rubric"]


def test_uac_import_audit_mode_returns_table_and_items() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--mode", "audit"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["mode"] == "audit"
    assert "audit_table" in payload
    assert payload["summary"]["entry_count"] >= 1
    assert payload["handoff_contract"]["advisory_only"] is True


def test_uac_import_explain_mode_returns_deployment_matrix() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uac-import.py"), "--mode", "explain"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["mode"] == "explain"
    assert "deployment_matrix" in payload
    assert "both" in payload["deployment_matrix"]["capability_types"]
