from __future__ import annotations

from pathlib import Path

from intent_pipeline.uac_ssot import audit_ssot_entries, render_audit_table


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


def test_render_audit_table_includes_headers() -> None:
    table = render_audit_table(audit_ssot_entries(ROOT))

    assert 'slug' in table.splitlines()[0]
    assert 'status' in table.splitlines()[0]
