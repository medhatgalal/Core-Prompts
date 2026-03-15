from __future__ import annotations

from intent_pipeline.uac_capabilities import (
    audit_surface_alignment,
    deployment_matrix_payload,
    emitted_surface_names,
    recommended_target_systems,
)


def test_emitted_surface_names_for_both_include_skill_and_agent() -> None:
    names = set(emitted_surface_names('both'))

    assert 'codex_skill' in names
    assert 'codex_agent' in names
    assert 'claude_command' in names
    assert 'claude_agent' in names


def test_recommended_target_systems_auto_filters_manual_review() -> None:
    assert recommended_target_systems('auto', 'manual_review') == []


def test_audit_surface_alignment_detects_over_generation() -> None:
    audit = audit_surface_alignment(
        declared_capability='skill',
        inferred_capability='skill',
        expected_surfaces={'codex_skill', 'claude_command'},
        actual_surfaces={'codex_skill', 'claude_command', 'claude_agent'},
    )

    assert audit.status == 'over-generated'


def test_deployment_matrix_payload_includes_wrapper_surfaces() -> None:
    matrix = deployment_matrix_payload()

    assert "wrappers" in matrix["capability_types"]["skill"]
    assert "gemini_extension_wrapper" in matrix["capability_types"]["skill"]["wrappers"]["gemini"]
