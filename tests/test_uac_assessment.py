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

    assert assessment.capability_type == "skill"
    assert assessment.recommended_surface == "skill"
    assert assessment.content_kind in {"prompt_like", "skill_like"}
    assert "explicit objective structure detected" in assessment.signals


def test_assess_uac_source_requires_review_for_undeclared_agent_definition() -> None:
    text = """---\nname: architecture-mentor\nkind: agent\n---\n\nYou are an architecture agent.\nmax_turns: 12\nUse sub-agent delegation when reconciling design options.\n"""

    assessment = assess_uac_source(
        text,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": "/tmp/architecture-agent.md",
        },
    )

    assert assessment.capability_type == "manual_review"
    assert assessment.recommended_surface == "manual_review"
    assert assessment.content_kind == "agent_configuration"
    assert "native agent configuration requires packaging review" in assessment.signals


def test_assess_uac_source_requires_review_for_undeclared_hybrid() -> None:
    text = """---\nname: architecture-mentor\nkind: \"agent\"\n---\n\n# Architecture Mentor\n\nYou are an architecture agent.\n\nPurpose: guide design reviews.\n\nIn Scope:\n- evaluate trade-offs\n- produce reusable checklists\n\nConstraints:\n- deterministic output\n\nResponsibilities:\n- coordinate specialists\n- preserve tool boundaries\n"""

    assessment = assess_uac_source(
        text,
        source_metadata={
            "source_type": "LOCAL_FILE",
            "normalized_source": "/tmp/architecture-agent.md",
        },
    )

    assert assessment.capability_type == "manual_review"
    assert assessment.recommended_surface == "manual_review"
    assert assessment.emitted_surfaces == {}


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


_SIMPLE = "# Rewrite\nPurpose: clarify instructions.\nInputs: a paragraph.\nWorkflow: rewrite it.\nExamples: clearer words.\n"


def test_agent_vocabulary_does_not_create_agent_surface() -> None:
    for text in [
        "Mission: clear prose.\nResponsibilities: preserve meaning.",
        "You are a reviewer. Tool boundaries apply. Use independent sub-agents.",
        "Explain developer_instructions and system prompt precedence.",
        "```yaml\nkind: agent\nmax_turns: 12\n```",
        "~~~toml\ndeveloper_instructions = 'review'\n~~~",
        "> kind: agent\n> max_turns: 12",
    ]:
        result = assess_uac_source(_SIMPLE + text)
        assert result.capability_type == "skill", text
        assert result.emitted_surfaces["codex"] == ("codex_skill",)
        assert "agent-only control semantics" not in result.rationale


def test_explicit_canonical_declarations_remain_packaging_choices() -> None:
    from intent_pipeline.uac_capabilities import emitted_surfaces_by_cli
    for declared in ("skill", "agent", "both"):
        text = f'---\nname: example\nkind: agent\ncapability_type: "{declared}"\n---\n' + _SIMPLE
        result = assess_uac_source(text)
        assert result.capability_type == declared
        assert result.emitted_surfaces == {k: v for k, v in emitted_surfaces_by_cli(declared).items() if v}
        assert "not proven" in result.rationale


def test_quoted_declaration_does_not_override_workflow_default() -> None:
    text = _SIMPLE + '\n```yaml\n---\ncapability_type: both\n---\n```'
    assert assess_uac_source(text).capability_type == "skill"
