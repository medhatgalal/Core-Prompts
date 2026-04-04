from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intent_pipeline.consumer_shell import (  # noqa: E402
    build_capability_catalog,
    build_release_delta,
    build_status_payload,
    render_catalog_markdown,
    render_release_delta_markdown,
    render_status_markdown,
)


def _entry(
    slug: str,
    *,
    display_name: str,
    summary: str,
    capability_type: str = "skill",
    supported_clis: dict[str, list[str]] | None = None,
    supported_agents: list[str] | None = None,
    invocation_hints: list[str] | None = None,
    domain_tags: list[str] | None = None,
    compatibility: str | None = None,
) -> dict[str, object]:
    return {
        "slug": slug,
        "display_name": display_name,
        "invocation_hints": invocation_hints or [],
        "quality_profile": "default",
        "quality_status": "ship",
        "layers": {
            "minimal": {
                "summary": summary,
                "capability_type": capability_type,
                "install_target": {"recommended": "repo_local"},
                "emitted_surfaces": supported_clis or {"codex": ["skill"], "claude": ["skill"]},
                "supported_agents": supported_agents or [],
                "required_inputs": ["repo context"],
                "expected_outputs": ["deterministic summary"],
                "domain_tags": domain_tags or ["analysis"],
                "compatibility": compatibility,
            },
            "expanded": {
                "overlap_candidates": [],
            },
        },
        "consumption_hints": {
            "preferred_use_cases": ["analysis"],
            "artifact_conventions": ["reports/example.md"],
            "invocation_style": "interactive",
            "requires_human_confirmation": False,
        },
        "expected_surface_names": ["codex_skill", "claude_skill"],
    }


def test_build_capability_catalog_groups_entries_for_consumers() -> None:
    manifest = {
        "ssot_sources": [
            _entry(
                "architecture",
                display_name="Architecture Studio",
                summary="Design systems and APIs.",
                capability_type="both",
                supported_clis={"codex": ["skill", "agent"], "claude": ["skill"]},
                supported_agents=["codex"],
                invocation_hints=["Use for API design."],
                domain_tags=["architecture", "analysis"],
                compatibility="codex>=0.1",
            ),
            _entry(
                "testing",
                display_name="Testing Studio",
                summary="Design test plans.",
                invocation_hints=["Use for test planning."],
                domain_tags=["testing"],
            ),
        ]
    }

    catalog = build_capability_catalog(manifest)

    assert catalog["entry_count"] == 2
    assert "architecture" in catalog["views"]["start_here"]
    assert catalog["views"]["by_cli"]["codex"] == ["architecture", "testing"]
    assert catalog["views"]["by_use_case"]["architecture"] == ["architecture"]
    assert catalog["capabilities"][0]["display_name"] == "Architecture Studio"
    rendered = render_catalog_markdown(catalog)
    assert "# Capability Catalog" in rendered
    assert "Architecture Studio" in rendered
    assert "Compatibility: codex>=0.1" in rendered


def test_build_release_delta_tracks_material_changes() -> None:
    previous = {"ssot_sources": [_entry("architecture", display_name="Architecture Studio", summary="Old summary.")]}
    current = {
        "ssot_sources": [
            _entry(
                "architecture",
                display_name="Architecture Studio",
                summary="New summary.",
                invocation_hints=["Use for migration plans."],
            ),
            _entry("testing", display_name="Testing Studio", summary="Design test plans."),
        ]
    }

    delta = build_release_delta(current, previous)

    assert delta["summary"]["new_count"] == 1
    assert delta["summary"]["material_change_count"] == 1
    assert delta["new_capabilities"] == [{"slug": "testing", "display_name": "Testing Studio"}]
    assert delta["material_changes"][0]["slug"] == "architecture"
    assert "summary" in delta["material_changes"][0]["material_fields"]
    rendered = render_release_delta_markdown(delta)
    assert "# Release Delta" in rendered
    assert "`testing`" in rendered


def test_build_status_payload_reports_health_from_validation_and_smoke() -> None:
    manifest = {"ssot_sources": [_entry("architecture", display_name="Architecture Studio", summary="Design systems.")]}
    status = build_status_payload(
        manifest,
        build_report={"generated_at": "2026-04-02T00:00:00Z"},
        validation_report={"validated_at": "2026-04-02T00:05:00Z", "validation_errors": 1, "validation_warnings": 0},
        smoke_report={"smoked_at": "2026-04-02T00:06:00Z", "failures": ["missing surface"], "warnings": []},
    )

    assert status["health"] == "error"
    assert status["entry_count"] == 1
    rendered = render_status_markdown(status)
    assert "# Consumer Status" in rendered
    assert "Overall health: `error`" in rendered


def test_build_status_payload_warns_on_smoke_warnings_without_failures() -> None:
    manifest = {"ssot_sources": [_entry("testing", display_name="Testing Studio", summary="Design tests.")]}
    status = build_status_payload(
        manifest,
        build_report={"generated_at": "2026-04-02T00:00:00Z"},
        validation_report={"validated_at": "2026-04-02T00:05:00Z", "validation_errors": 0, "validation_warnings": 0},
        smoke_report={"smoked_at": "2026-04-02T00:06:00Z", "failures": [], "warnings": ["missing optional binary"]},
    )

    assert status["health"] == "warn"
