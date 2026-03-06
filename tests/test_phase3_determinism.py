from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

from intent_pipeline.routing.engine import run_semantic_routing
from intent_pipeline.uplift.engine import run_uplift_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _phase3_input_text() -> str:
    return "\n".join(
        [
            "Primary Objective: build deterministic semantic routing contracts.",
            "Secondary Objectives: preserve schema-major compatibility and explicit provenance.",
            "In Scope: routing precedence, route-spec translation, deterministic tests.",
            "Out of Scope: target validation, execution, output generation, help rendering.",
            "Must keep deterministic canonical serialization.",
            "Acceptance Criteria: phase 3 emits route_spec contracts with evidence linkage.",
        ]
    )


def _run_phase3_in_fresh_process(input_text: str) -> bytes:
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path.cwd() / 'src'))\n"
        "from intent_pipeline.uplift.engine import run_uplift_engine\n"
        "from intent_pipeline.routing.engine import run_semantic_routing\n"
        "uplift = run_uplift_engine(sys.argv[1])\n"
        "sys.stdout.write(run_semantic_routing(uplift).to_json())\n"
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["TZ"] = "UTC"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"

    completed = subprocess.run(
        [sys.executable, "-c", code, input_text],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
        env=env,
    )
    return completed.stdout


def test_det_03_phase3_in_process_output_is_byte_identical() -> None:
    uplift = run_uplift_engine(_phase3_input_text())
    outputs = [run_semantic_routing(uplift).to_json().encode("utf-8") for _ in range(25)]

    assert "DET-03"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1


def test_det_03_phase3_cross_process_output_is_byte_identical() -> None:
    outputs = [_run_phase3_in_fresh_process(_phase3_input_text()) for _ in range(10)]

    assert "DET-03"
    assert len(set(outputs)) == 1
    digests = [hashlib.sha256(output).hexdigest() for output in outputs]
    assert len(set(digests)) == 1
