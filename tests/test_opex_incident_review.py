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


def test_reference_replay_receipt_is_bound_to_canonical_artifacts() -> None:
    receipt = json.loads(
        (
            ROOT
            / "evals/maintenance/engos-audit-opex-incident-review/reference-replay.json"
        ).read_text(encoding="utf-8")
    )

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    assert receipt["bindings"]["candidate_sha256"] == digest(
        ROOT / "ssot/engos-audit-opex-incident-review.md"
    )
    assert receipt["bindings"]["renderer_sha256"] == digest(SCRIPT)
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
