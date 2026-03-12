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
    assert payload["uac"]["recommended_surface"] == "skill"
    assert payload["source"]["normalized_source"] == str(sample.resolve())
    assert payload["routing"]["decision"] in {"PASS_ROUTE", "NEEDS_REVIEW"}


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
