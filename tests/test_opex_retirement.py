"""Exact legacy retirement and non-discovery boundaries after controller approval."""
from pathlib import Path
import hashlib
from intent_pipeline.uac_ssot import load_ssot_entries

ROOT = Path(__file__).resolve().parents[1]


def test_opex_archive_preserves_exact_sources_without_active_entry():
    archive = ROOT / "sources/retired/opex-briefing"
    expected = {
        "original-skill.md": "31af8e2a648ef066533e030abedaa62622a2b5bd973a437c8ec0b5b4cb7dbc67",
        "original-metadata.json": "cb5a2570157519a6725341171d262be39214c964c93c5cec7868140b5d82800b",
    }
    for name, digest in expected.items():
        assert hashlib.sha256((archive / name).read_bytes()).hexdigest() == digest
    assert not (ROOT / "skills/opex-briefing/SKILL.md").exists()
    assert not (ROOT / "skills/opex-briefing/metadata.json").exists()
    assert not (archive / "SKILL.md").exists()
    marker = (archive / "README.md").read_text()
    for flag in ("archive_only: true", "auto_discovery: false", "promotion_eligible: false"):
        assert flag in marker
    slugs = [entry.slug for entry in load_ssot_entries(ROOT / "ssot")]
    assert slugs.count("engos-audit-opex-incident-review") == 1
    assert "opex-briefing" not in slugs and "engos-content-opex-briefing" not in slugs
    for cli in ("codex", "gemini", "claude", "kiro"):
        assert not (ROOT / f".{cli}/skills/opex-briefing").exists()
        assert not (ROOT / f".{cli}/skills/engos-content-opex-briefing").exists()
