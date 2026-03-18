from __future__ import annotations

from pathlib import Path

from intent_pipeline.uac_ssot import audit_ssot_entries, build_ssot_handoff_contract, render_audit_table


ROOT = Path(__file__).resolve().parents[1]


def test_audit_ssot_entries_reports_known_entries() -> None:
    audits = audit_ssot_entries(ROOT)
    slugs = {entry.slug for entry in audits}

    assert 'supercharge' in slugs
    assert 'uac-import' in slugs


def test_audit_ssot_entries_detects_hybrid_capability() -> None:
    audits = {entry.slug: entry for entry in audit_ssot_entries(ROOT)}

    assert audits['supercharge'].inferred.capability_type == 'both'
    assert audits['mentor'].inferred.capability_type == 'both'


def test_architecture_entry_publishes_display_name_and_agent_surfaces() -> None:
    audits = {entry.slug: entry for entry in audit_ssot_entries(ROOT)}
    architecture = audits['architecture']

    assert architecture.manifest['display_name'] == 'Architecture Studio'
    assert 'codex_agent' in architecture.expected_surface_names
    assert 'kiro_agent' in architecture.expected_surface_names


def test_render_audit_table_includes_headers() -> None:
    table = render_audit_table(audit_ssot_entries(ROOT))

    assert 'slug' in table.splitlines()[0]
    assert 'status' in table.splitlines()[0]


def test_audit_ssot_entries_include_manifest_and_fit_analysis() -> None:
    audits = audit_ssot_entries(ROOT)

    assert audits[0].manifest["manifest_version"] == "capability-fabric.v0"
    assert "fit_assessment" in audits[0].cross_analysis


def test_build_ssot_handoff_contract_is_advisory() -> None:
    payload = build_ssot_handoff_contract(ROOT)

    assert payload["advisory_only"] is True
    assert payload["capabilities"]


def test_audit_ssot_entries_persist_repo_relative_source_refs() -> None:
    audits = {entry.slug: entry for entry in audit_ssot_entries(ROOT)}
    architecture = audits["architecture"].manifest["layers"]["minimal"]

    assert architecture["resources"] == ["ssot/architecture.md"]
    assert architecture["source_provenance"]["normalized_source"] == "ssot/architecture.md"
