from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_architecture_ssot_contains_strict_quality_contract() -> None:
    text = (ROOT / "ssot" / "architecture.md").read_text(encoding="utf-8")
    required_headings = [
        "## Purpose",
        "## Output Directory",
        "## Core Principles",
        "## Standard Workflow",
        "## Universal Deliverables",
        "## Universal Output Format",
        "## Mode Playbooks",
        "## Review Gate",
        "## Architecture Quality Scorecard",
    ]
    for heading in required_headings:
        assert heading in text

    required_mode_headings = [
        "### 1. API Design Playbook",
        "### 2. Database Design Playbook",
        "### 3. Design Patterns Playbook",
        "### 4. System Design Playbook",
    ]
    for heading in required_mode_headings:
        assert heading in text

    assert "reports/architecture/" in text
    assert "architecture/spec.md" in text
    assert "Rejected Alternatives" in text
    assert "migration and rollback guidance" in text.lower()
    assert "Endpoint Catalog Template" in text
    assert "Pattern Fit Matrix Template" in text
    assert "System Component Template" in text


def test_architecture_descriptor_enforces_benchmark_gate() -> None:
    descriptor_path = ROOT / ".meta" / "capabilities" / "architecture.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))

    expanded = descriptor["layers"]["expanded"]
    quality_criteria = expanded["quality_criteria"]
    assert any("scorecard" in item.lower() for item in quality_criteria)
    assert any("rejected alternative" in item.lower() for item in quality_criteria)

    quality_gate = expanded["quality_gate"]
    assert quality_gate["min_pass_score"] >= 9
    required = set(quality_gate["required_no_zero_for"])
    for field in {"Failure-Aware Decisions", "Migration Clarity", "Benchmark Fit"}:
        assert field in required

    expected_benchmarks = {item["label"] for item in descriptor["benchmark_sources"]}
    assert "Code Review benchmark" in expected_benchmarks
    assert "Resolve Conflict benchmark" in expected_benchmarks

    modes = descriptor["modes"]
    assert any("quality scorecard" in output.lower() for mode in modes for output in mode["expected_outputs"])
    assert any("rollback" in item.lower() for mode in modes for item in mode["uplift_notes"] + mode["expected_outputs"])
