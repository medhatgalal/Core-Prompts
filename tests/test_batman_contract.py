from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_batman_is_subagent_driven_implementation_not_parent_authorship() -> None:
    text = _read("ssot/batman.md")

    assert "Batman delivers implementation through independent subagents" in text
    assert "The controller must not author production code, failing tests, or implementation fixes." in text
    assert "Skipping implementation means Batman did not run." in text


def test_batman_has_four_blocking_milestone_review_gates() -> None:
    text = _read("ssot/batman.md")

    assert "All four milestone gates are blocking." in text
    assert re.findall(r"^\| [1-4] \|", text, flags=re.MULTILINE) == [
        "| 1 |",
        "| 2 |",
        "| 3 |",
        "| 4 |",
    ]
    for milestone in ("Scope", "Design readiness", "Task implementation", "Landing readiness"):
        assert milestone in text
    assert "a fresh reviewer role brief independent of the design author" in text
    assert "Every applicable milestone gate reviews its declared evidence and blocks downstream work on failure." in text
    assert "All four milestone gates review the actual saved revision or diff" not in text


def test_batman_landing_gate_follows_pr_and_hosted_ci() -> None:
    text = _read("ssot/batman.md")
    stage_six = text.split("### Stage 6 — Document, land, and clean", 1)[1].split("\n## Rules", 1)[0]
    ordered_steps = (
        "Update documentation and examples",
        "Open a scoped PR or MR",
        "Verify current hosted CI",
        "Run milestone gate 4",
        "When landing is authorized, merge",
    )

    positions = [stage_six.index(step) for step in ordered_steps]
    assert positions == sorted(positions)
    assert "fresh documentation and GitOps reviewer role briefs" in stage_six
    assert "fresh adversarial reviewer role brief applies `supercharge /adversarial`" in stage_six


def test_batman_progress_reporting_is_event_driven_and_time_bounded() -> None:
    text = _read("ssot/batman.md")

    for trigger in (
        "initial status immediately after preflight",
        "stage status at every stage transition",
        "blocker status immediately when a blocker appears",
        "heartbeat status every 15 minutes during long-running work",
    ):
        assert trigger in text
    assert "against the written delivery plan" in text


def test_batman_is_portable_and_uses_one_alias_body() -> None:
    text = _read("ssot/batman.md")
    kiro_skill = _read(".kiro/skills/batman/SKILL.md")
    supercharge = _read("ssot/supercharge.md")
    fixture = _read("evals/fixtures/supercharge/module-preservation.json")

    assert "`superman` invokes this exact Batman body" in text
    assert "Use only the host's subagent mechanism" in text
    assert "Core-Prompts companions available in the active installation and named in this contract" in text
    for companion in (
        "architecture",
        "auto-research",
        "supercharge",
        "converge",
        "testing",
        "code-review",
        "address-code-review",
        "docs-review-expert",
        "gitops-review",
    ):
        assert f"- `{companion}`" in text

    banned = (
        "WorkGraph",
        "workgraph-jira",
        "globally installed",
        "orchestrate_subagent",
        "Grok",
        "Kiro",
    )
    for term in banned:
        assert term not in text
    assert "repository-local Core-Prompts companions" not in text
    assert re.search(r"\b(?:PT|AT)\b", text) is None
    assert re.search(r"/Users/|~/|https?://", text) is None

    assert "Internal milestone findings return to the original implementer or a bounded default fixer." in text
    assert "Use `address-code-review` only for selected comments on an existing PR or MR." in text
    assert "all applicable milestone gates" in text

    assert "## MODULE: /batman" not in supercharge
    assert '"heading": "## MODULE: /batman"' not in fixture
    assert "Batman delivers implementation through independent subagents" in kiro_skill
    assert "`superman` invokes this exact Batman body" in kiro_skill


def test_batman_job_map_and_benchmark_are_ship_ready() -> None:
    job_map = json.loads(_read(".meta/skill-job-map.json"))["skills"]["batman"]
    benchmark = _read(".planning/initiatives/capability-review-pilots/BENCHMARK-MATRIX.md")

    assert job_map["shape"] == "implementation_delivery_controller"
    assert job_map["portfolio_action"] == "ship_and_preserve_superman_alias"
    assert "draft" not in " ".join(str(value) for value in job_map.values()).lower()
    assert "pending" not in " ".join(str(value) for value in job_map.values()).lower()
    assert "| batman | 5 | 5 | 5 | 5 | 5 | 5 | 5 | structural_ready |" in benchmark
