from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

from intent_pipeline.pipeline import run_phase1_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_pipeline_in_fresh_process(source_path: Path) -> bytes:
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path.cwd() / 'src'))\n"
        "from intent_pipeline.pipeline import run_phase1_pipeline\n"
        "sys.stdout.write(run_phase1_pipeline(sys.argv[1]))\n"
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["TZ"] = "UTC"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"

    completed = subprocess.run(
        [sys.executable, "-c", code, str(source_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
        env=env,
    )
    return completed.stdout


def test_sum_03_in_process_output_is_byte_identical(tmp_path: Path) -> None:
    source = tmp_path / "request.txt"
    source.write_text(
        "System: You are a routing assistant.\n"
        "User: Build deterministic summary output from sanitized text.\n"
        "Must remain roleplay-free.\n"
        "Out of scope: downstream execution.\n",
        encoding="utf-8",
    )

    outputs = [run_phase1_pipeline(source).encode("utf-8") for _ in range(25)]

    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1


def test_sum_03_cross_process_output_is_byte_identical(tmp_path: Path) -> None:
    source = tmp_path / "request.txt"
    source.write_text(
        "Goal: produce deterministic local-file intent summaries.\n"
        "Implement fixed-template summary rendering.\n"
        "No URL ingestion.\n"
        "Out of scope: downstream routing and execution.\n",
        encoding="utf-8",
    )

    outputs = [_run_pipeline_in_fresh_process(source) for _ in range(10)]

    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1
