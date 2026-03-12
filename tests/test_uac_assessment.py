from __future__ import annotations

from pathlib import Path

from intent_pipeline.uac_assessment import assess_uac_source


def test_assess_uac_source_prefers_skill_for_structured_prompt() -> None:
    text = """# Architecture Review\n\nPrimary Objective: Consolidate the architecture prompts into one reusable workflow.\n\nIn Scope:\n- Classify incoming prompts\n- Normalize output sections\n\nOut of Scope:\n- Runtime execution\n\nConstraints:\n- Keep the result deterministic\n\nAcceptance Criteria:\n- Output one skill-ready prompt\n"""

    assessment = assess_uac_source(
        text,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": "/tmp/architecture.md",
        },
        source_hint=Path("/tmp/architecture.md"),
    )

    assert assessment.recommended_surface == "skill"
    assert assessment.content_kind in {"prompt_like", "skill_like"}
    assert "explicit objective structure detected" in assessment.signals


def test_assess_uac_source_prefers_agent_for_agent_definition() -> None:
    text = """---\nname: architecture-mentor\nkind: agent\n---\n\nYou are an architecture agent.\nmax_turns: 12\nUse sub-agent delegation when reconciling design options.\n"""

    assessment = assess_uac_source(
        text,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": "/tmp/architecture-agent.md",
        },
    )

    assert assessment.recommended_surface == "agent"
    assert assessment.content_kind == "agent_like"
    assert "agent control markers detected" in assessment.signals


def test_assess_uac_source_returns_manual_review_for_config_only() -> None:
    text = """[agents.architecture]\nconfig_file = \".codex/agents/architecture.toml\"\n"""

    assessment = assess_uac_source(
        text,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": "/tmp/config.toml",
        },
        source_hint=Path("/tmp/config.toml"),
    )

    assert assessment.recommended_surface == "manual_review"
    assert assessment.content_kind == "config_like"
