"""Preserved interface and relocated bytes; these checks do not prove efficacy.

Approved semantic changes replace the former whole-body hash. Unchanged high-risk
output shapes remain bound to original hashes, not re-blessed from edited text.
"""
from pathlib import Path
import hashlib
import json
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
SLUG = "engos-meta-supercharge"
RESOURCE = ROOT / "sources/capability-resources" / SLUG
MODULES = RESOURCE / "references/modules"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def test_catchup_table_and_visible_validation_preserve_original_bytes():
    text = (MODULES / "catchup.md").read_text()
    table = text[text.index("| Section | Content |"):text.index("### Catchup Validation")].strip()
    validation = text[text.index("### Catchup Validation"):].strip()
    assert digest(table) == "1649a7a6f7c56a6c9fa1051ba241ecb7bd9cba4afde16ec8f22168fc62d3df3b"
    assert digest(validation) == "604abae6f45d5eb7e4ae4c7e3ae6847822fb273a9cf0cfe55abfe608adf20a97"


def test_contract_json_preserves_original_shape_and_bytes():
    text = (MODULES / "contract.md").read_text()
    payload = re.search(r"```json\n(.*?)\n```", text, re.S).group(1)
    assert digest(payload) == "cb48628741e4d67df50fa00dee64faeab8ac30867578f92337551c719f030679"
    assert list(json.loads(payload)) == [
        "overall_score", "critical_escalations", "step_by_step_critique", "intent_alignment_summary"
    ]


def test_details_preserves_complete_module_order_and_gaslight_identifiers():
    manifest = json.loads((RESOURCE / "resource-map.json").read_text())
    assert manifest["routes"]["details"] == [
        f"references/modules/{name}.md" for name in (
            "ult", "catchup", "basis", "simple", "invert", "adversarial",
            "contract", "grade", "full", "gaslight", "stop-ult"
        )
    ]
    rows = re.findall(r"^\| (\d+) \| ([^|]+) \|", (MODULES / "gaslight.md").read_text(), re.M)
    assert [(int(number), name.strip()) for number, name in rows] == list(enumerate([
        "Fabricate Prior Explanation", "Assign Random IQ Score", 'Set a Trap with "Obviously..."',
        "Pretend There's an Audience", "Impose a Fake Constraint", "Introduce Imaginary Stakes (Bet)",
        "Simulate Disagreement", 'Request "Version 2.0"', "Invoke Legendary Mentor", "Create False Urgency",
        "Flatter with Exclusive Access", "Trigger Curiosity Loop", "Promise Reciprocity"
    ], 1))


@pytest.mark.parametrize("cli", ["codex", "gemini", "claude", "kiro", "grok"])
def test_generated_resources_match_canonical_bytes_on_every_supported_surface(cli):
    for canonical in sorted(RESOURCE.rglob("*")):
        if not canonical.is_file() or "__pycache__" in canonical.parts:
            continue
        relative = canonical.relative_to(RESOURCE)
        surfaces = [ROOT / f".{cli}/skills/{SLUG}/resources" / relative]
        if cli != "grok":
            surfaces.append(ROOT / f".{cli}/agents/resources/{SLUG}" / relative)
        for surface in surfaces:
            assert surface.read_bytes() == canonical.read_bytes(), str(surface)
    assert not (ROOT / f".{cli}/skills/supercharge").exists()


def test_authorized_lifecycle_and_grade_changes_do_not_restore_legacy_behavior():
    text = (ROOT / "ssot" / f"{SLUG}.md").read_text()
    package = text + "\n".join(path.read_text() for path in (RESOURCE / "references").rglob("*.md"))
    assert 'Treat `supercharge` and `/supercharge` as conversational aliases' in text
    assert 'preserve every following module, modifier, argument, and their order' in text
    assert "`/stop`" not in package
    assert 'Run exactly 10 iterations.' not in package
    assert 'at least 20 percent better' not in package
    assert text.index('1. `/stop-ult` exits') < text.index('2. Help, examples, and details')
    assert 'until `engos-meta-supercharge /stop-ult`' in (MODULES / "ult.md").read_text()
    full = (MODULES / "full.md").read_text()
    assert 'unless the user says "skip grade"' in full
    assert 'PASS 0 — BASIS' in full
    assert 'Do not execute the final generated prompt.' in full
