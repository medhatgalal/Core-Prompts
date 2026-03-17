from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_uac_wrapper_explain_runs() -> None:
    result = subprocess.run([str(ROOT / 'bin' / 'uac'), 'explain'], cwd=ROOT, capture_output=True, text=True, check=True)
    assert 'classification_rubric' in result.stdout


def test_capability_fabric_wrapper_validate_runs() -> None:
    # Keep test parity with CI which refreshes schema cache before strict validation.
    subprocess.run([str(ROOT / 'scripts' / 'sync-surface-specs.py'), '--refresh'], cwd=ROOT, check=True)
    result = subprocess.run([str(ROOT / 'bin' / 'capability-fabric'), 'validate', '--strict'], cwd=ROOT, capture_output=True, text=True, check=True)
    assert 'Validation passed.' in result.stdout
