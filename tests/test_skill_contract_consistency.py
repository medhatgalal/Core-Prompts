from pathlib import Path

from core_prompts_eval.topology import compile_topology


ROOT = Path(__file__).resolve().parents[1]


def _text(slug: str) -> str:
    return (ROOT / "ssot" / f"{slug}.md").read_text(encoding="utf-8")


def test_supercharge_declares_one_terminal_precedence_and_modifier_failure_path() -> None:
    text = _text("supercharge")

    assert "### Terminal-Control Precedence" in text
    assert "`/stop` wins over every other command" in text
    assert "If the user supplies more than one reflective control, stop and ask them to choose one" in text
    assert "`/deep` without `/debate` is invalid" in text


def test_supercharge_ult_and_gaslight_counts_are_consistent() -> None:
    text = _text("supercharge")

    assert "Separate response into exactly:" not in text
    assert "Use 2–4 techniques" not in text
    assert "Use 1–3 techniques maximum per request" in text
    assert "auto-select 1–3 techniques" in text


def test_pulse_write_boundaries_and_composition_are_explicit() -> None:
    text = _text("pulse")

    assert "all commands compose" not in text.lower()
    assert "only during `/delete` or `/sweep`, with user approval" in text
    assert "only during `/archive` or `/sweep`, with user approval" in text
    assert "wait for explicit approval before calling a write command" in text
    assert "Config lives in the SKILL.md itself" not in text


def test_auto_research_numbered_modes_and_profiles_are_unique() -> None:
    topology = compile_topology(ROOT / "ssot" / "auto-research.md")

    assert topology["known_ambiguities"] == []
    assert _text("auto-research").count("### Mode 6: Trace-to-Eval") == 1
    assert _text("auto-research").count("### Profile 4: Bounded Execution") == 1


def test_known_multi_mode_contracts_are_no_longer_blocked_by_contradictions() -> None:
    for slug in ("supercharge", "pulse", "auto-research"):
        topology = compile_topology(ROOT / "ssot" / f"{slug}.md")
        assert topology["known_ambiguities"] == [], (slug, topology["known_ambiguities"])
