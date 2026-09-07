"""Effective package fidelity and discovery bindings, not semantic promotion."""
from pathlib import Path
import hashlib
import json
import pytest

ROOT = Path(__file__).resolve().parents[1]
SLUG = "engos-meta-supercharge"
RESOURCE = ROOT / "sources/capability-resources" / SLUG / "references"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def test_help_relocation_reconstructs_accepted_source_exactly():
    source = (ROOT / "ssot" / f"{SLUG}.md").read_text()
    binding = json.loads((ROOT / "tests/fixtures/supercharge-help-preservation.json").read_text())
    a, b = source.index("## HELP OUTPUT"), source.index("## MODULE REFERENCE")
    help_text = (RESOURCE / "help.md").read_text() + (RESOURCE / "help-examples.md").read_text()
    assert digest(source[:a]) == binding["prefix_sha256"]
    assert digest(source[b:]) == binding["modules_and_tail_sha256"]
    assert digest(help_text) == binding["help_and_examples_sha256"]
    assert digest(source[:a] + help_text + source[b:]) == binding["source_sha256"]
    assert "report the missing resource" in source[a:b]
    assert "directory containing its bundled `capability.json`" in source[a:b]


@pytest.mark.parametrize("cli", ["codex", "gemini", "claude", "kiro"])
def test_skill_and_agent_help_resources_resolve_to_same_bytes(cli):
    for name in ("help.md", "help-examples.md"):
        for surface in (
            ROOT / f".{cli}/skills/{SLUG}/resources/references/{name}",
            ROOT / f".{cli}/agents/resources/{SLUG}/references/{name}",
        ):
            assert surface.read_bytes() == (RESOURCE / name).read_bytes()
    assert not (ROOT / f".{cli}/skills/supercharge").exists()


def test_full_grade_and_terminal_precedence_are_preserved():
    text = (ROOT / "ssot" / f"{SLUG}.md").read_text()
    assert 'Treat `supercharge` and `/supercharge` as conversational aliases' in text
    assert 'preserve every following module, modifier, argument, and their order' in text
    assert 'Run exactly 10 iterations.' in text
    assert 'unless the user says "skip grade"' in text
    assert 'PASS 0 — BASIS' in text
    assert text.index('1. `/stop` wins') < text.index('2. `/stop-ult` exits') < text.index('3. Help, examples, and details')
