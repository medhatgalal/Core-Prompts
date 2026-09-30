from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_architecture_ssot_contains_strict_quality_contract() -> None:
    text = (ROOT / "ssot" / "engos-design-architecture.md").read_text(encoding="utf-8")
    required_headings = [
        "## Purpose",
        "## Output Directory",
        "## Core Principles",
        "## Standard Workflow",
        "## Universal Deliverables",
        "## Universal Output Format",
        "## Mode Playbooks",
        "## Review Gate",
        "## Recommendation Roles",
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
    descriptor_path = ROOT / ".meta" / "capabilities" / "engos-design-architecture.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))

    expanded = descriptor["layers"]["expanded"]
    quality_criteria = expanded["quality_criteria"]
    assert any("separate" in item.lower() and "zero open findings" in item.lower() for item in quality_criteria)
    assert any("rejected alternative" in item.lower() for item in quality_criteria)

    quality_gate = expanded["quality_gate"]
    assert quality_gate["reviewer_must_differ_from_writer"] is True
    assert quality_gate["required_open_findings"] == 0
    assert quality_gate["round_cap"] is None
    assert quality_gate["same_writer_and_reviewer_on_revision"] is True
    assert "min_pass_score" not in quality_gate

    expected_benchmarks = {item["label"] for item in descriptor["benchmark_sources"]}
    assert "Code Review benchmark" in expected_benchmarks
    assert "Resolve Conflict benchmark" in expected_benchmarks

    modes = descriptor["modes"]
    assert all("separate reviewer finding list with zero open findings" in mode["expected_outputs"] for mode in modes)
    assert not any("scorecard" in output.lower() for mode in modes for output in mode["expected_outputs"])
    assert any("rollback" in item.lower() for mode in modes for item in mode["uplift_notes"] + mode["expected_outputs"])


def test_architecture_retains_domain_checks_without_a_self_score_gate() -> None:
    text = (ROOT / "ssot" / "engos-design-architecture.md").read_text(encoding="utf-8")
    for phrase in [
        "The coordinator does not write the recommendation artifact, findings, or repairs",
        "Resume the same writer for every revision",
        "The reviewer does not rewrite the artifact",
        "Resume the same reviewer for every later round",
        "severity, artifact location, what is wrong, a concrete repair, source evidence, and status `open`",
        "`addressed` with what changed",
        "`wontfix` with a technical reason",
        "`needs-user-input` when only a human can choose",
        "drop fixed findings; keep a bad repair open; add any new defect as open",
        "treat the user's answer as final for that finding",
        "There is no round cap",
        "reviewer explicitly reports zero open findings on the current artifact",
        "Never confuse module boundaries with deployment boundaries",
        "Never present a convention as an enforced boundary",
        "Never claim a component is removable, isolated, or decoupled without naming a falsifier",
        "ownership boundaries are unclear",
    ]:
        assert phrase in text
    assert "## Architecture Quality Scorecard" not in text
    assert "Overall Score" not in text
    assert "Stripe" not in text
    assert "/engos-design-architecture " not in text
