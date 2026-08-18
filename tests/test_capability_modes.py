from __future__ import annotations

import json
from pathlib import Path

from intent_pipeline.uac_modes import extract_declared_modes


ROOT = Path(__file__).resolve().parents[1]


def test_multi_mode_capabilities_have_descriptor_modes() -> None:
    for slug in ("supercharge", "pulse", "auto-research", "ic-assistant", "instruction-editor"):
        descriptor = json.loads((ROOT / ".meta" / "capabilities" / f"{slug}.json").read_text(encoding="utf-8"))
        assert descriptor["modes"], f"{slug} descriptor lost its declared mode index"
        assert all(mode["source_refs"] == [f"ssot/{slug}.md"] for mode in descriptor["modes"])


def test_generated_descriptors_do_not_expose_legacy_ship_as_promotion() -> None:
    for path in (ROOT / ".meta" / "capabilities").glob("*.json"):
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        assert descriptor.get("quality_status") != "ship"


def test_supercharge_index_contains_only_explicit_modules() -> None:
    body = (ROOT / "ssot" / "supercharge.md").read_text(encoding="utf-8")
    entries = extract_declared_modes("supercharge", body)
    names = {entry["display_name"] for entry in entries}

    assert "/ult — ULT-Agent++ (Prompt Engineer Mode)" in names
    assert "/adversarial /debate — Surface Bull/Bear/Decider Debate" in names
    assert "Agentic Orchestration (Core Principle, Not a Module)" not in names
    assert "Mode Behavior" not in names
    assert all(entry["entry_kind"] == "module" for entry in entries)


def test_pulse_command_variants_are_combined() -> None:
    body = (ROOT / "ssot" / "pulse.md").read_text(encoding="utf-8")
    entries = extract_declared_modes("pulse", body)
    by_slug = {entry["mode_slug"]: entry for entry in entries}

    assert "deep" in by_slug
    assert "pulse /deep" in by_slug["deep"]["invocations"]
    assert "pulse /deep <N>" in by_slug["deep"]["invocations"]
    assert len([entry for entry in entries if entry["mode_slug"] == "deep"]) == 1


def test_general_headings_are_not_modes() -> None:
    body = """## Purpose\n\n### Failure Mode To Avoid\n\n## Workflow\n\n### Step 1: Inspect\n"""
    assert extract_declared_modes("sample", body) == []


def test_numbered_modes_of_operation_are_explicit() -> None:
    body = """## 2. Modes of Operation\n\n### 2.1 Standard Help Mode\n\n### 2.2 Diagnostic Mode\n"""
    assert [entry["display_name"] for entry in extract_declared_modes("sample", body)] == [
        "Standard Help Mode",
        "Diagnostic Mode",
    ]
