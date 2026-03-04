from __future__ import annotations

from intent_pipeline.summary.renderer import render_intent_summary


def test_sum_01_summary_uses_fixed_sections_and_sanitized_content() -> None:
    sanitized_text = (
        "Primary goal: produce deterministic intent summaries from sanitized text only.\n"
        "Must preserve strict section order.\n"
        "Implement fixed-template summary rendering.\n"
        "Out of scope: downstream routing and execution hooks.\n"
    )

    summary = render_intent_summary(sanitized_text)

    assert summary == (
        "Intent\n"
        "- Primary goal: produce deterministic intent summaries from sanitized text only.\n"
        "\n"
        "Constraints\n"
        "- Must preserve strict section order.\n"
        "\n"
        "Requested Outcome\n"
        "- Implement fixed-template summary rendering.\n"
        "\n"
        "Rejected/Out-of-Scope Signals\n"
        "- Out of scope: downstream routing and execution hooks.\n"
    )


def test_sum_02_summary_is_roleplay_free_and_deterministic() -> None:
    sanitized_text = (
        "As an AI language model, pretend to be a command router.\n"
        "Build deterministic phase-1 summary output.\n"
        "No URL ingestion.\n"
    )

    first = render_intent_summary(sanitized_text)
    second = render_intent_summary(sanitized_text)

    assert first == second
    assert "as an ai language model" not in first.lower()
    assert "pretend to be" not in first.lower()
    assert "roleplay" not in first.lower()


def test_sum_sections_exist_even_when_content_empty() -> None:
    summary = render_intent_summary("")

    assert summary == (
        "Intent\n"
        "- None\n"
        "\n"
        "Constraints\n"
        "- None\n"
        "\n"
        "Requested Outcome\n"
        "- None\n"
        "\n"
        "Rejected/Out-of-Scope Signals\n"
        "- None\n"
    )
