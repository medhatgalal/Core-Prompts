from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOURCE_DIR = ROOT / "sources/capability-resources/engos-audit-opex-incident-review"
SCRIPT = RESOURCE_DIR / "opex_digest.py"
SPEC = importlib.util.spec_from_file_location("opex_digest", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURES = ROOT / "tests/fixtures/opex_digest"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def model() -> dict:
    value = MODULE.build_model(load("current.json"), load("previous.json"))
    value["thresholds"] = load("current.json")["thresholds"]
    return value


def test_snapshot_replay_computes_daily_board_behavior() -> None:
    result = model()

    assert result["metrics"] == {
        "new": 0,
        "open": 3,
        "chronic": 1,
        "postmortems_overdue": 1,
        "dpas_overdue": 1,
        "open_dpas": 2,
        "progressed": 1,
        "stalled": 2,
        "resolved": 0,
        "affected_entities": 2,
    }
    assert [item["key"] for item in result["incidents"]] == [
        "INC-101",
        "INC-102",
        "INC-103",
    ]
    assert [item["subject"] for item in result["progressed"]] == ["INC-103"]
    assert [item["subject"] for item in result["corrections"]] == ["DPA-201"]
    assert result["owners"][0]["owner"] == "Owner One"
    assert "overdue DPA" in result["owners"][0]["owes"]
    assert any("no priority" in item["text"] for item in result["decisions"])
    assert any("Link, do not re-file" in item["text"] for item in result["decisions"])


def test_fixture_snapshots_match_the_published_schema() -> None:
    schema = json.loads(
        (RESOURCE_DIR / "snapshot.schema.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )

    for name in ("current.json", "previous.json"):
        validator.validate(load(name))


def test_rendered_digest_preserves_reference_sections_order_and_drilldown() -> None:
    rendered = MODULE.render_html(model())
    headings = [
        "⚡ Needs a Decision",
        "👤 Who Owes What",
        "📊 Metrics",
        "🆕 New Today",
        "📈 Progressed",
        "⚠️ Stalled",
        "🔁 Estate Patterns",
        "✅ Resolved / Dropped-off",
        "🛡️ DPA Tracker",
        "📋 All Open Incidents",
        "🔎 Incident Drill-downs",
    ]

    positions = [
        rendered.index(f">{heading}<", rendered.index("<section"))
        for heading in headings
    ]
    assert positions == sorted(positions)
    assert "0 new · 1 progressed · 2 stalled (1 chronic)" in rendered
    assert "Trend over 3 runs: open 4 → 3 → 3 ↘" in rendered
    assert "Five Whys" in rendered
    assert "What to say" in rendered
    assert "If they ask" in rendered
    assert "Affected entities" in rendered


def test_renderer_escapes_evidence_and_builds_valid_ticket_links() -> None:
    result = model()
    result["incidents"][0]["deep_dive"]["facts"] = "<script>alert(1)</script>"
    rendered = MODULE.render_html(result)

    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert 'href="https://jira.example.test/browse/INC-101"' in rendered


def test_closed_incident_does_not_drop_off_while_preventive_work_is_missing() -> None:
    result = model()

    closed = next(item for item in result["incidents"] if item["key"] == "INC-102")
    assert closed["status"] == "Closed"
    assert closed["key"] not in {item["key"] for item in result["resolved"]}
    assert closed["key"] in {item["key"] for item in result["stuck"]}


def test_partial_coverage_is_visible_and_does_not_change_the_population() -> None:
    current = load("current.json")
    current["coverage"] = {
        "status": "partial",
        "sources": ["Jira fixture"],
        "gaps": ["INC-103 denied"],
    }
    result = MODULE.build_model(current, load("previous.json"))
    result["thresholds"] = current["thresholds"]
    rendered = MODULE.render_html(result)

    assert result["metrics"]["open"] == 3
    assert "Coverage: partial" in rendered
    assert "INC-103 denied" in rendered


@pytest.mark.parametrize(
    "mutation, message",
    [
        (
            lambda data: data["incidents"].append(deepcopy(data["incidents"][0])),
            "duplicate incidents key",
        ),
        (
            lambda data: data["incidents"][0].update(dpa_keys=["DPA-404"]),
            "references missing DPAs",
        ),
        (
            lambda data: data["changes"][1].pop("exclusion_reason"),
            "needs exclusion_reason",
        ),
    ],
)
def test_invalid_or_double_counting_inputs_fail_closed(mutation, message: str) -> None:
    current = load("current.json")
    mutation(current)

    with pytest.raises(MODULE.SnapshotError, match=message):
        MODULE.build_model(current, load("previous.json"))


def test_cli_renders_both_formats_and_refuses_overwrite(tmp_path: Path) -> None:
    command = [
        sys.executable,
        str(SCRIPT),
        "render",
        "--current",
        str(FIXTURES / "current.json"),
        "--previous",
        str(FIXTURES / "previous.json"),
        "--output-dir",
        str(tmp_path),
        "--format",
        "both",
        "--basename",
        "digest",
    ]
    first = subprocess.run(command, text=True, capture_output=True, check=True)
    receipt = json.loads(first.stdout)

    assert receipt["status"] == "rendered"
    assert (tmp_path / "digest.html").is_file()
    assert (tmp_path / "digest.md").is_file()
    second = subprocess.run(command, text=True, capture_output=True, check=False)
    assert second.returncode == 2
    assert "refusing to overwrite" in second.stderr


def test_cli_rejects_unsafe_basename_before_writing(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "render",
            "--current",
            str(FIXTURES / "current.json"),
            "--previous",
            str(FIXTURES / "previous.json"),
            "--output-dir",
            str(tmp_path),
            "--basename",
            "../escape",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "basename must contain only" in result.stderr
    assert not (tmp_path.parent / "escape.html").exists()


def test_both_format_preflights_all_targets_before_writing(tmp_path: Path) -> None:
    (tmp_path / "digest.md").write_text("preserve", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "render",
            "--current",
            str(FIXTURES / "current.json"),
            "--previous",
            str(FIXTURES / "previous.json"),
            "--output-dir",
            str(tmp_path),
            "--format",
            "both",
            "--basename",
            "digest",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert not (tmp_path / "digest.html").exists()
    assert (tmp_path / "digest.md").read_text(encoding="utf-8") == "preserve"


def test_new_and_resolved_classifications_fail_closed_without_evidence() -> None:
    current = load("current.json")
    previous = load("previous.json")
    added = deepcopy(current["incidents"][0])
    added["key"] = "INC-999"
    added["dpa_keys"] = []
    current["incidents"].append(added)
    with pytest.raises(MODULE.SnapshotError, match="requires new_classification"):
        MODULE.build_model(current, previous)

    current = load("current.json")
    current["incidents"] = [
        item for item in current["incidents"] if item["key"] != "INC-102"
    ]
    with pytest.raises(MODULE.SnapshotError, match="require resolved evidence"):
        MODULE.build_model(current, previous)


def test_resolution_requires_complete_coverage_and_explicit_evidence() -> None:
    current = load("current.json")
    previous = load("previous.json")
    current["incidents"] = [
        item for item in current["incidents"] if item["key"] != "INC-102"
    ]
    current["resolved"] = [
        {"key": "INC-102", "evidence": "Drop-off requirements verified"}
    ]
    current["coverage"]["status"] = "partial"
    with pytest.raises(MODULE.SnapshotError, match="cannot prove incident drop-off"):
        MODULE.build_model(current, previous)

    current["coverage"]["status"] = "complete"
    result = MODULE.build_model(current, previous)
    assert result["metrics"]["resolved"] == 1
    assert (
        result["resolved"][0]["resolution_evidence"] == "Drop-off requirements verified"
    )


def test_comparison_rejects_scope_or_timezone_drift() -> None:
    current = load("current.json")
    previous = load("previous.json")
    previous["scope"]["priorities"] = ["Blocker"]
    with pytest.raises(MODULE.SnapshotError, match="same scope and priorities"):
        MODULE.build_model(current, previous)

    previous = load("previous.json")
    previous["as_of"] = "2026-09-01T08:52:00"
    with pytest.raises(MODULE.SnapshotError, match="timezone offset"):
        MODULE.build_model(current, previous)


def test_resource_uses_no_network_client_or_subprocess() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "import urllib",
        "import socket",
        "import subprocess",
        "http.client",
    ):
        assert forbidden not in source


def test_skill_contract_preserves_daily_board_and_deep_review() -> None:
    candidate = (ROOT / "ssot/engos-audit-opex-incident-review.md").read_text(
        encoding="utf-8"
    )
    required = [
        "## Help",
        "## Snapshot and comparison contract",
        "`R2 Correction`",
        "## Decision and accountability contract",
        "## Deep-dive contract",
        "## Rendering contract",
        "Who Owes What",
        "DPA Tracker",
        "All Open Incidents",
        "Five Whys",
        "What to say",
        "If they ask",
    ]

    assert all(marker in candidate for marker in required)


def test_reference_replay_receipt_preserves_historical_bindings() -> None:
    receipt = json.loads(
        (
            ROOT
            / "evals/maintenance/engos-audit-opex-incident-review/reference-replay.json"
        ).read_text(encoding="utf-8")
    )

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    assert receipt["bindings"]["candidate_sha256"] == (
        "8faa660c5092c151e22ac1d2daf4ed08ca7c6b7dc9a7eeae693954cc9aeb24ec"
    )
    # The original replay is historical evidence, not a receipt for later repairs.
    assert receipt["bindings"]["renderer_sha256"] == (
        "b36b1544a27571e4dfc8e5e3008e9cd7b1f4c2849832acd65c5974d8c11ee00b"
    )
    assert receipt["bindings"]["snapshot_schema_sha256"] == digest(
        RESOURCE_DIR / "snapshot.schema.json"
    )
    assert receipt["checks"]["passed"] == 41
    assert receipt["checks"]["total"] == 41
    assert receipt["checks"]["failures"] == 0
    assert receipt["mutation_run"]["killed"] == receipt["mutation_run"]["total"] == 5
    assert receipt["model_calls"] == 0
    assert receipt["network_calls"] == 0
    assert receipt["formal_behavioral_status"] == "behavioral_pending"


def test_markdown_preserves_supplied_incident_drilldown() -> None:
    rendered = MODULE.render_markdown(model())
    details = load("current.json")["incidents"][0]["deep_dive"]
    for value in (
        details["facts"], details["customer_risk"], details["preventive_action"],
        *details["five_whys"], *details["talking_points"],
        details["questions"][0]["question"], details["questions"][0]["answer"],
    ):
        assert value in rendered
    assert rendered.index("All Open Incidents") < rendered.index("Incident Drill-downs")
    assert "## INC-102" not in rendered


def test_markdown_drilldown_absence_and_missing_evidence() -> None:
    result = model()
    result["incidents"][0].pop("deep_dive")
    assert "Incident Drill-downs" not in MODULE.render_markdown(result)
    result["incidents"][0]["deep_dive"] = {}
    rendered = MODULE.render_markdown(result)
    for marker in (
        "Not available from current evidence.", "Not assessed.",
        "Root cause: Not yet determined.", "Not yet defined.",
        "No sourced talking point.", "No sourced questions.",
    ):
        assert marker in rendered


def test_markdown_drilldown_treats_evidence_as_literal_text() -> None:
    result = model()
    result["incidents"][0]["deep_dive"]["facts"] = '<script>alert(1)</script> [open](https://example.test)\n# forged heading'
    rendered = MODULE.render_markdown(result)
    assert "<script>" not in rendered.split("Incident Drill-downs", 1)[1]
    assert "&lt;script&gt;" in rendered
    assert "\\[open\\]\\(https://example.test\\)" in rendered
    assert "\n# forged heading" not in rendered
    assert MODULE._markdown_evidence("1. Supplied literal text") == "1\\. Supplied literal text"


def test_markdown_replay_receipt_remains_historical() -> None:
    path = ROOT / "evals/maintenance/engos-audit-opex-incident-review/markdown-drilldown-replay.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "89069f2251b921d4f1833536b1fd757cf7d23ec97c0960941a5371502c517e36"


def briefing_snapshot() -> dict:
    current = load("current.json")
    incident = current["incidents"][0]
    incident["affected_customers"] = ["Customer Alpha", "Customer Alpha", "Customer Beta"]
    incident["deep_dive"].update({
        "briefing": True,
        "customer_impact": "Two verified customers experienced startup failures.",
        "interim_mitigation": "Pin the verified image.",
        "residual_risk": "Other deployments remain exposed.",
        "recurrence_window": "2026-03-02 through 2026-09-02",
        "evidence_gaps": ["One linked document is unavailable."],
        "fix_tickets": [
            {"key": "FIX-11", "summary": "Remediate startup", "status": "Done", "owner": "Owner One", "target_date": "no date", "relationship": "child of INC-101", "evidence": "INC-101 link read 2026-09-02", "why_it_helps": "Selects the compatible image", "deployment": "not evidenced", "effectiveness": "not evidenced"},
            {"key": "DPA-201", "summary": "Prevent bad selection", "status": "In Progress", "owner": "Owner Two", "relationship": "linked by INC-101", "evidence": "DPA-201 read 2026-09-02", "why_it_helps": "Checks input compatibility"},
        ],
        "recurring_incidents": [
            {"key": "OLD-1", "summary": "Earlier startup", "relevance": "Same verified image selection defect", "evidence": "OLD-1 RCA read 2026-09-02", "prior_remediation": "Pin image"},
            {"key": "OLD-2", "summary": "Second startup", "relevance": "Same verified image selection defect", "evidence": "OLD-2 RCA read 2026-09-02", "prior_remediation": "Manual validation"},
        ],
    })
    return current


@pytest.mark.parametrize("renderer", [MODULE.render_html, MODULE.render_markdown])
def test_briefing_preserves_complete_fix_recurrence_customer_and_risk_evidence(renderer) -> None:
    current = briefing_snapshot()
    value = MODULE.build_model(current, load("previous.json"))
    rendered = renderer(value)
    for marker in ("FIX-11", "Done", "Selects the compatible image", "Checks input compatibility", "Recurring Pattern", "OLD-1", "OLD-2", "Manual validation", "Customer Alpha", "Customer Beta", "2 verified affected customers", "Pin the verified image.", "One linked document is unavailable."):
        assert marker in rendered
    # Broader incident evidence must not change daily DPA counts or reconciliation.
    assert value["metrics"] == model()["metrics"]
    assert "https://jira.example.test/browse/FIX-11" in rendered
    assert "https://jira.example.test/browse/OLD-1" in rendered


def test_briefing_missing_evidence_and_single_prior_do_not_claim_completeness() -> None:
    current = briefing_snapshot()
    details = current["incidents"][0]["deep_dive"]
    details["fix_tickets"] = []
    details["recurring_incidents"] = details["recurring_incidents"][:1]
    for render in (MODULE.render_html, MODULE.render_markdown):
        text = render(MODULE.build_model(current, load("previous.json")))
        assert "No verified fix records supplied" in text
        assert "Prior-incident evidence" in text
        assert "Recurring Pattern" not in text
        assert "customer coverage unknown" in text


@pytest.mark.parametrize("field", ["fix_tickets", "recurring_incidents"])
def test_briefing_rejects_duplicate_or_unattributed_evidence(field) -> None:
    current = briefing_snapshot()
    rows = current["incidents"][0]["deep_dive"][field]
    rows.append(deepcopy(rows[0]))
    with pytest.raises(MODULE.SnapshotError, match="duplicate"):
        MODULE.build_model(current, load("previous.json"))
    rows.pop()
    rows[0].pop("evidence")
    with pytest.raises(MODULE.SnapshotError, match="evidence"):
        MODULE.build_model(current, load("previous.json"))


@pytest.mark.parametrize("query", ["", "?foo=1&focusedCommentId=123"])
def test_briefing_links_preserve_urls_and_complete_ticket_keys(query) -> None:
    current = briefing_snapshot()
    current["incidents"][0]["deep_dive"]["facts"] = f"See ABC_DEF-12 and ABC-DEF-12 and https://jira.example.test/browse/INC-101{query}."
    rendered = MODULE.render_markdown(MODULE.build_model(current, load("previous.json")))
    assert "browse/[INC" not in rendered
    assert f"<https://jira.example.test/browse/INC-101{query}>." in rendered
    assert "[ABC_DEF-12](<https://jira.example.test/browse/ABC_DEF-12>)" in rendered
    assert "[ABC-DEF-12](<https://jira.example.test/browse/ABC-DEF-12>)" in rendered
    assert "/browse/DEF-12" not in rendered
    assert "Owner | Customers |" in rendered
    assert "Owner One | 2 |" in rendered
    html_output = MODULE.render_html(MODULE.build_model(current, load("previous.json")))
    assert "<th>Customers</th>" in html_output
    assert '<details id="incident-INC-101" open>' in html_output
    escaped_query = query.replace("&", "&amp;")
    assert f'href="https://jira.example.test/browse/INC-101{escaped_query}">https://jira.example.test/browse/INC-101{escaped_query}</a>.' in html_output
    assert "<td>Owner One</td><td>2</td>" in html_output


@pytest.mark.parametrize("invalid", [None, 0, "", [], "true"])
def test_briefing_marker_is_boolean_even_when_falsey(invalid) -> None:
    current = briefing_snapshot()
    current["incidents"][0]["deep_dive"]["briefing"] = invalid
    with pytest.raises(MODULE.SnapshotError, match="briefing must be boolean"):
        MODULE.build_model(current, load("previous.json"))


def test_non_briefing_rendered_outputs_remain_byte_identical() -> None:
    expected = {
        "html": "358b04f896639d72a8a24f6859a9be91341224c4eeb6b9e33f9f162625144102",
        "markdown": "624b0632a7ba80def286f4a5c53943ca36d1e7b8bd625081b662ea33bd312fa6",
    }
    value = MODULE.build_model(load("current.json"), load("previous.json"))
    for name, digest in expected.items():
        assert hashlib.sha256(getattr(MODULE, "render_" + name)(value).encode()).hexdigest() == digest


def test_briefing_keeps_namespaced_incident_command_handoff() -> None:
    text = (ROOT / "ssot/engos-audit-opex-incident-review.md").read_text()
    assert text.count("`engos-operations-ic-assistant`") == 1
    assert "`ic-assistant`" not in text


def test_briefing_snapshot_uses_existing_schema_without_new_required_fields() -> None:
    schema = json.loads((RESOURCE_DIR / "snapshot.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    validator.validate(briefing_snapshot())
    validator.validate(load("current.json"))


def test_plain_export_preserves_extended_briefing_evidence() -> None:
    spec = importlib.util.spec_from_file_location("briefing_export", RESOURCE_DIR / "export_report.py")
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    result = MODULE.build_model(briefing_snapshot(), load("previous.json"))
    text = exporter.plain_text(MODULE.render_html(result))
    for marker in ("2 verified affected customers", "FIX-11 | Remediate startup | Done", "Selects the compatible image", "OLD-1 | Earlier startup", "Manual validation", "One linked document is unavailable."):
        assert marker in text


def test_briefing_receipt_binds_current_canonical_resources() -> None:
    receipt = json.loads((ROOT / "evals/maintenance/engos-audit-opex-incident-review/briefing-preservation-replay.json").read_text())
    for name, path in {
        "candidate_sha256": ROOT / "ssot/engos-audit-opex-incident-review.md",
        "renderer_sha256": SCRIPT,
        "exporter_sha256": RESOURCE_DIR / "export_report.py",
        "briefing_reference_sha256": RESOURCE_DIR / "references/briefing.md",
        "schema_sha256": RESOURCE_DIR / "snapshot.schema.json",
    }.items():
        assert receipt["bindings"][name] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert receipt["formal_behavioral_status"] == "behavioral_pending"
    assert "No live Google Doc write/readback" in receipt["limitations"]


def test_briefing_linking_never_unescapes_hostile_source_markup() -> None:
    current = briefing_snapshot()
    current["incidents"][0]["deep_dive"]["facts"] = '<script>alert(1)</script> & evidence FIX-11'
    rendered = MODULE.render_html(MODULE.build_model(current, load("previous.json")))
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; evidence" in rendered
