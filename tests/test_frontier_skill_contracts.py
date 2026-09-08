"""Static package contracts for frontier modernization, not behavioral scores."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "sources/capability-resources/engos-meta-supercharge"
MODULES = RES / "references/modules"
AUTO_RES = ROOT / "sources/capability-resources/engos-optimization-auto-research"


def module(name):
    return (MODULES / f"{name}.md").read_text()


def test_selected_route_inventory_covers_public_module_aliases_and_nested_debate():
    data = json.loads((RES / "resource-map.json").read_text())
    assert data["schema_version"] == "CapabilityResourceMap.v1"
    routes = data["routes"]
    for alias in ("/debate", "/debate /deep", "/adversarial /debate", "/adversarial /debate /deep"):
        assert routes[alias] == routes["/adversarial"]
    assert set(routes["/full"]) == {
        f"references/modules/{name}.md" for name in ("full", "simple", "invert", "adversarial", "contract", "grade")
    }
    assert "references/modules/basis.md" not in routes["/full"]
    assert all((RES / path).is_file() for paths in routes.values() for path in paths)
    assert all((RES / path).is_file() for path in data["shared"])


def test_independence_and_delivery_rules_are_in_entry_before_optional_resources():
    text = (ROOT / "ssot/engos-meta-supercharge.md").read_text()
    assert "Actual independent subagents are mandatory" in text
    assert "Self-review and simulated agent roles are not acceptable substitutes" in text
    assert "without the author's self-grade or preferred verdict" in text
    assert text.index("### Resource Delivery Gate") < text.index("## MODULE REFERENCE")
    assert "truncated excerpt" in text
    assert "full required module resources" in text
    assert "Delivery does not prove comprehension" in text


def test_grade_preserves_four_sections_and_distinguishes_real_trials_from_scores():
    text = module("grade")
    section = text.split("### Output Structure (MANDATORY)\n", 1)[1]
    assert re.findall(r"^\d\. `([^`]+)`$", section, re.M) == [
        "Rubric", "Iteration Ladder", "Final Artifact", "Top 3 Remaining Gaps"
    ]
    for boundary in (
        "up to 10 actual candidate trials", "at least two substantive candidates",
        "two distinct substantive unsuccessful attempts", "same rubric",
        "An actual independent reviewer", "final artifact may be an earlier candidate or the original",
        "explicit user count runs that count", "hard budget", "do not count"
    ):
        assert boundary in text, boundary
    assert "only when the user explicitly invokes it or selects `/full`" in text


def test_preserved_simple_and_contract_requirements_remain_operational():
    simple = module("simple")
    for requirement in (
        "1–2 worked examples tailored to the user's domain",
        "Only when the domain is unknown, include one general example",
        "one-way dependencies", "Validate invariants as well as outputs",
        "MUST / MUST NOT invariants from PREFER guidance"
    ):
        assert requirement in simple
    assert "primary value and outcome over secondary benefits" in module("contract")


def test_ult_full_keeps_scope_and_execution_payload_without_fake_results():
    ult = module("ult")
    assert ult.index("`Generated Prompt`") < ult.index("`Execution Output`")
    assert "Display the improved prompt" in ult
    assert "Explicit draft-only or review-only requests suppress execution" in ult
    assert 'This stack reviews and grades the improved prompt; it will not execute its task.' in ult
    assert "not measured superiority across tasks" in ult
    assert "no-execution rule overrides `/ult` execution" in module("full")


def test_model_guidance_has_provenance_and_research_only_refresh_boundary():
    text = (RES / "references/model-guidance.md").read_text()
    assert "Last checked: 2026-09-08" in text
    assert "locally unmeasured" in text
    assert "research-only refresh monthly" in text
    assert "newly available/selected model or updated official practice" in text
    assert "never silently rewrite skills" in text
    assert "does not itself create an automation" in text
    assert all(host in text for host in ("platform.claude.com", "developers.openai.com", "docs.x.ai"))


def test_autoresearch_executed_loop_has_distinct_state_and_protected_measurement():
    entry = (ROOT / "ssot/engos-optimization-auto-research.md").read_text()
    loop = (AUTO_RES / "references/experiment-loop.md").read_text()
    assert "read `resources/references/experiment-loop.md` on a skill surface" in entry
    assert "or `references/experiment-loop.md` directly relative" in entry
    for boundary in (
        "original baseline (immutable reference)", "incumbent (best accepted state)",
        "trial (isolated candidate", "Protect evaluator code, evaluation data, scoring rules",
        "one or several coordinated elements", "recording the exact set and joint hypothesis",
        "Record invalid/crashed trials separately", "Explore again after both wins and losses",
        "equivalent quality with worthwhile speed/cost/simplicity gains",
        "not proof of a global optimum", "Keeping an incumbent is distinct from formal promotion",
        "simulated score is not an executed trial"
    ):
        assert boundary in loop, boundary
    ledger = (AUTO_RES / "templates/experiment-ledger.md.tmpl").read_text()
    assert "Parent Incumbent" in ledger and "Resulting Incumbent" in ledger
    assert "Accepted / Rejected / Tied / Invalid" in ledger
    assert "Stop once the winner is obvious" not in entry


def test_autoresearch_effective_review_binds_workflow_and_template_bytes(tmp_path):
    import shutil
    from intent_pipeline.capability_resources import effective_capability_text, load_resource_bundle

    slug = "engos-optimization-auto-research"
    copied = tmp_path / "sources/capability-resources" / slug
    shutil.copytree(AUTO_RES, copied)
    entry = "Read `resources/references/experiment-loop.md`."
    before_bundle = load_resource_bundle(copied, "all")
    before = effective_capability_text(tmp_path, slug, entry)
    assert "# Executed Improvement Loop" in before
    assert "Parent Incumbent" in before
    assert "# Resource Delivery for Auto-Research" in before
    assert {item["path"] for item in before_bundle["resources"]} == {
        "references/resource-delivery.md", "references/experiment-loop.md", "bootstrap.py",
        "templates/goal-contract.md.tmpl", "templates/experiment-ledger.md.tmpl",
        "templates/scorecard.json.tmpl", "templates/promotion-packet.md.tmpl"
    }
    workflow = copied / "references/experiment-loop.md"
    workflow.write_text(workflow.read_text() + "\nTest-only changed acceptance rule.\n")
    assert load_resource_bundle(copied, "all")["sha256"] != before_bundle["sha256"]
    assert effective_capability_text(tmp_path, slug, entry) != before
