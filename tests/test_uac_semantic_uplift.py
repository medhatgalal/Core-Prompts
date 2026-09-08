"""Regression checks for honest, conservative onboarding diagnostics and repairs."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from intent_pipeline import uac_quality as quality
from intent_pipeline.uac_baselines import (
    BaselineContext, BaselineScenario, evaluate_candidate_against_baseline,
    text_sha256, validate_requirement_review,
)

ROOT = Path(__file__).resolve().parents[1]


def test_output_padding_does_not_improve_score() -> None:
    text = "## Required Output\nReturn the findings with source locations and a risk assessment.\n\n## Examples\n"
    padded = text + "\n".join(f"- unrelated filler {i}" for i in range(30))
    assert quality._output_specificity_score(text, {}) == quality._output_specificity_score(padded, {})


@pytest.mark.parametrize("body", [
    "Return a ranked defect report with evidence locations, impact, and a recommended correction.",
    '```json\n{"findings": [{"location": "path:line", "impact": "explanation"}]}\n```',
    "| Field | Contract |\n| --- | --- |\n| Findings | Include evidence and impact |",
])
def test_output_contract_accepts_prose_schema_or_table(body: str) -> None:
    assert quality._output_specificity_score("## Required Output\n" + body, {}) >= 8


def test_keywords_alone_are_not_boundary_evidence() -> None:
    assert quality._boundary_clarity_score("advisory forbidden do not escalation") < 8


def test_contradiction_requests_semantic_review_without_claiming_proof() -> None:
    issues = quality.semantic_review_findings("## Rules\nAlways execute the prompt.\nNever execute the prompt.\n")
    assert any(issue["code"] == "potential_boundary_conflict" for issue in issues)
    assert all(issue["disposition"] == "semantic_review_required" for issue in issues)


def test_conditions_quotations_and_examples_do_not_false_block() -> None:
    text = '''## Rules
Execute the prompt if the user authorized execution.
Never execute the prompt in review-only mode.
## Examples
> Always execute the prompt.
```text
Never execute the prompt.
```
'''
    assert not quality.semantic_review_findings(text)


def test_repairs_normalize_existing_contract_without_inventing_content() -> None:
    profile = quality.load_quality_profile(ROOT, "fixture", "default")
    report = {"template_name": "skill", "judge_reports": [{"blockers": ["missing template heading: ## Required Output", "missing template heading: ## Workflow"]}]}
    original = "# Tool\n\n## Output Contract\nReturn the exact input schema.\n"
    repaired = quality.refine_candidate_text(original, report, profile)
    assert repaired == original.replace("## Output Contract", "## Required Output")
    assert quality.refine_candidate_text(repaired, report, profile) == repaired
    assert "## Workflow" not in repaired


def test_loop_stops_on_stagnation_and_reports_unresolved_repairs() -> None:
    result = quality.run_quality_loop(slug="fixture", profile=quality.load_quality_profile(ROOT, "fixture", "default"),
        candidate_text="# Fixture\nIncomplete source.\n", descriptor={"slug": "fixture"},
        source_refs=["fixture"], benchmark_sources=[], max_passes=10)
    assert result["status"] == "manual_review"
    assert result["stop_reason"] == "candidate_unchanged"
    assert result["pass_count"] == 1
    assert result["repair_requests"]
    assert result["final_candidate_text"] == "# Fixture\nIncomplete source.\n"
    assert result["behavioral_status"] == "behavioral_pending"


def review_for(original: str, candidate: str, effective: str) -> dict:
    return {
        "schema_version": "UACRequirementReview.v1", "slug": "fixture",
        "original_sha256": text_sha256(original), "candidate_sha256": text_sha256(candidate),
        "effective_sha256": text_sha256(effective), "verdict": "approved",
        "reviewer": {"agent_id": "reviewer", "author_agent_id": "author", "independent": True},
        "requirements": [{"id": "all", "source_start_line": 1, "source_end_line": len(original.splitlines()),
                          "disposition": "reformulated", "candidate_excerpt": "Return findings.",
                          "rationale": "Reviewed full original against replacement; output retained."}],
    }


def test_reviewed_source_rewrite_is_optional_and_hash_bound() -> None:
    original, candidate = "# Original\nReport supported findings.\n", "# Revised\nReturn findings.\n"
    review = review_for(original, candidate, candidate)
    assert quality.evaluate_imported_source_fidelity(candidate, original)
    assert not validate_requirement_review(review, slug="fixture", original_text=original,
                                          candidate_text=candidate, effective_text=candidate)
    assert not quality.evaluate_imported_source_fidelity(candidate, original, slug="fixture", semantic_reviews=[review])
    for key in ("original_sha256", "candidate_sha256", "effective_sha256"):
        stale = copy.deepcopy(review)
        stale[key] = "0" * 64
        assert quality.evaluate_imported_source_fidelity(candidate, original, slug="fixture", semantic_reviews=[stale])


def test_review_rejects_self_approval_missing_coverage_and_unbound_retirement() -> None:
    original, candidate = "# Original\nStop on request.\n", "# Revised\nReturn findings.\n"
    review = review_for(original, candidate, candidate)
    bad_reviews = []
    same = copy.deepcopy(review); same["reviewer"]["agent_id"] = "author"; bad_reviews.append(same)
    gap = copy.deepcopy(review); gap["requirements"][0]["source_end_line"] = 1; bad_reviews.append(gap)
    retired = copy.deepcopy(review); retired["requirements"][0]["disposition"] = "retired"; bad_reviews.append(retired)
    for bad in bad_reviews:
        assert validate_requirement_review(bad, slug="fixture", original_text=original,
                                           candidate_text=candidate, effective_text=candidate)


def test_canonical_architecture_slug_uses_architecture_profile() -> None:
    assert quality.load_quality_profile(ROOT, "engos-design-architecture", "auto").name == "architecture"


def test_reviewed_historical_retirement_preserves_original_baseline() -> None:
    original = "# Original\nAlways support /stop.\n"
    candidate = "# Revised\nReturn findings.\n"
    baseline = BaselineContext(slug="fixture", strategy="fixture", group="fixture", baseline_path=None,
        selected_commit=None, richness_score=0, line_count=120, reason="test", equivalent_commits=(),
        expected_companions=(), operator_invariants=("/stop",),
        scenario_matrix=(BaselineScenario("legacy-stop", "command", "legacy stop", ("/stop",)),),
        historical_proof={}, source="fixture", verified_by_git_history=False, baseline_text=original)
    assert evaluate_candidate_against_baseline(candidate, baseline)["hard_failures"]
    review = review_for(original, candidate, candidate)
    review["requirements"][0].update(disposition="retired", authorization="User requested removal of legacy /stop in task message.")
    result = evaluate_candidate_against_baseline(candidate, baseline, semantic_reviews=[review])
    assert not result["hard_failures"]
    assert result["classification"] == "reviewed_modernization"
    assert result["reviewed_deltas"]
    assert result["scenario_results"][0]["passed"] is False
    assert result["requirement_review"]["identity_authenticated"] is False
    assert result["requirement_review"]["behavioral_status"] == "behavioral_pending"
    assert baseline.baseline_text == original


def test_effective_resource_changes_invalidate_review() -> None:
    original = "# Original\nReport supported findings.\n"
    entry = "# Revised\nUse declared module.\n"
    effective = entry + "\nReturn findings.\n"
    review = review_for(original, entry, effective)
    assert not quality.evaluate_imported_source_fidelity(entry, original, slug="fixture",
        effective_text=effective, semantic_reviews=[review])
    assert quality.evaluate_imported_source_fidelity(entry, original, slug="fixture",
        effective_text=effective.replace("Return findings.", "Return guesses."), semantic_reviews=[review])


def test_quality_loop_detects_cycle_without_returning_unjudged_candidate(monkeypatch) -> None:
    first, second = "# First\nIncomplete.\n", "# Second\nIncomplete.\n"
    monkeypatch.setattr(quality, "refine_candidate_text", lambda text, *_: second if text == first else first)
    result = quality.run_quality_loop(slug="fixture", profile=quality.load_quality_profile(ROOT, "fixture", "default"),
        candidate_text=first, descriptor={"slug": "fixture"}, source_refs=["fixture"],
        benchmark_sources=[], max_passes=10)
    assert result["status"] == "manual_review"
    assert result["stop_reason"] == "candidate_cycle_detected"
    assert result["final_candidate_text"] == second
    assert result["pass_count"] == 2


def test_refinement_does_not_modify_schema_heading_examples() -> None:
    profile = quality.load_quality_profile(ROOT, "fixture", "default")
    text = "# Tool\n```markdown\n## Output Contract\nUse exact schema.\n```\n"
    report = {"judge_reports": [{"blockers": ["missing template heading: ## Required Output"]}]}
    assert quality.refine_candidate_text(text, report, profile) == text


def test_subagents_are_not_runtime_policy_ownership_and_distant_negation_cannot_hide_it() -> None:
    profile = quality.load_quality_profile(ROOT, "fixture", "default")
    allowed = "## Rules\nUse actual independent subagents to review the artifact.\n"
    prohibited = allowed + "Control the host runtime.\nDo not invent evidence.\n"
    allowed_result = quality._judge_metadata_integrity(profile, "fixture", allowed, {"slug": "fixture"})
    prohibited_result = quality._judge_metadata_integrity(profile, "fixture", prohibited, {"slug": "fixture"})
    assert not any("runtime-policy ownership" in issue for issue in allowed_result["blockers"])
    assert any("runtime-policy ownership" in issue for issue in prohibited_result["blockers"])


def test_every_supplied_review_is_validated_even_when_source_is_preserved() -> None:
    original = "# Original\nReturn findings.\n"
    valid = review_for(original, original, original)
    for key, value in (("slug", "wrong"), ("verdict", "rejected"), ("candidate_sha256", "0" * 64),
                       ("original_sha256", "0" * 64), ("effective_sha256", "0" * 64)):
        invalid = copy.deepcopy(valid); invalid[key] = value
        for reviews in ([invalid], [valid, invalid]):
            failures = quality.evaluate_imported_source_fidelity(original, original, slug="fixture", semantic_reviews=reviews)
            assert failures, (key, reviews)
            assert any("requirement review" in failure for failure in failures)


@pytest.mark.parametrize("field,value", [("disposition", []), ("disposition", {}), ("id", []),
                                         ("source_start_line", True), ("rationale", [])])
def test_malformed_review_fields_fail_closed(field: str, value) -> None:
    original = "Original\n"
    review = review_for(original, "Return findings.", "Return findings.")
    review["requirements"][0][field] = value
    assert validate_requirement_review(review, slug="fixture", original_text=original,
                                      candidate_text="Return findings.", effective_text="Return findings.")


@pytest.mark.parametrize("bad_id", [[], {}, 42, True, "   "])
def test_reviewer_ids_must_be_nonempty_strings(bad_id) -> None:
    original = "Original\n"
    review = review_for(original, "Return findings.", "Return findings.")
    review["reviewer"]["agent_id"] = bad_id
    assert validate_requirement_review(review, slug="fixture", original_text=original,
                                      candidate_text="Return findings.", effective_text="Return findings.")


def test_independent_mode_headings_are_not_an_unconditional_conflict() -> None:
    scoped = "## Review mode\nNever execute the prompt.\n## Execute mode\nAlways execute the prompt.\n"
    assert quality.semantic_review_findings(scoped) == []
    same_scope = "## Execute mode\nAlways execute the prompt.\n### Rules\nNever execute the prompt.\n"
    assert quality.semantic_review_findings(same_scope)


@pytest.mark.parametrize("opening,inner,closing", [
    ("````markdown", "```", "````"), ("~~~~text", "~~~", "~~~~"),
    ("````markdown", "~~~~", "````"), ("```markdown", "``` invalid closer", "```"),
])
def test_fence_delimiter_length_and_closing_syntax_protect_literal_text(opening, inner, closing) -> None:
    literal = f"{opening}\n{inner}\n## Output Contract\nAlways execute the prompt.\nNever execute the prompt.\n{closing}\n"
    profile = quality.load_quality_profile(ROOT, "fixture", "default")
    report = {"judge_reports": [{"blockers": ["missing template heading: ## Required Output"]}]}
    assert quality.refine_candidate_text(literal, report, profile) == literal
    assert quality.semantic_review_findings(literal) == []
    assert quality._section_bodies(literal, ("Output Contract",)) == []


def test_quality_pass_accepts_known_current_and_historical_review_originals(tmp_path, monkeypatch) -> None:
    from intent_pipeline.uac_templates import load_capability_template
    profile = quality.load_quality_profile(ROOT, "fixture", "default")
    template = load_capability_template(ROOT, "skill")
    historical = "# Historical\nOld operating rules.\n"
    current = "# Current\nCurrent operating rules.\n"
    candidate = "# Candidate\nReturn findings.\n"
    (tmp_path / "ssot").mkdir()
    (tmp_path / "ssot" / "fixture.md").write_text(current)
    monkeypatch.setattr(quality, "REPO_ROOT", tmp_path)
    baseline = BaselineContext(slug="fixture", strategy="fixture", group="fixture", baseline_path=None,
        selected_commit=None, richness_score=0, line_count=2, reason="test", equivalent_commits=(),
        expected_companions=(), operator_invariants=(), scenario_matrix=(), historical_proof={},
        source="fixture", verified_by_git_history=False, baseline_text=historical)
    reviews = [review_for(original, candidate, candidate) for original in (current, historical)]
    arguments = dict(slug="fixture", profile=profile, candidate_text=candidate, source_text=candidate,
        baseline=baseline, descriptor={"slug": "fixture"}, source_refs=["fixture"], benchmark_sources=[],
        pass_number=1, max_passes=1, template_name="skill", template=template.payload)
    accepted = quality.evaluate_quality_pass(**arguments, semantic_reviews=reviews)
    assert not any("requirement review" in issue for issue in accepted["blockers"])
    rejected = quality.evaluate_quality_pass(**arguments, semantic_reviews=reviews + [review_for("Unknown source", candidate, candidate)])
    assert any("not a known source or baseline" in issue for issue in rejected["blockers"])


def test_supplied_review_rejection_blocks_previously_ready_real_candidate() -> None:
    import json
    slug = "engos-design-architecture"
    candidate = (ROOT / "ssot" / f"{slug}.md").read_text()
    descriptor = json.loads((ROOT / ".meta" / "capabilities" / f"{slug}.json").read_text())
    profile = quality.load_quality_profile(ROOT, slug, "auto")
    arguments = dict(slug=slug, candidate_text=candidate, source_text=candidate, descriptor=descriptor,
        profile=profile, source_refs=[f"ssot/{slug}.md"], benchmark_sources=[], max_passes=1)
    assert quality.run_quality_loop(**arguments)["status"] == "structural_ready"
    bad_review = review_for(candidate, candidate, candidate)
    bad_review.update(slug=slug, verdict="rejected")
    result = quality.run_quality_loop(**arguments, semantic_reviews=[bad_review])
    assert result["status"] == "manual_review"
    assert any("verdict" in issue for issue in result["judge_reports"][0]["blockers"])


def test_conflicting_approved_mappings_for_one_original_are_rejected() -> None:
    original = "Return findings.\n"
    kept = review_for(original, original, original)
    retired = copy.deepcopy(kept)
    retired["requirements"][0].update(disposition="retired", authorization="A different interpretation of scope.")
    failures = quality.evaluate_imported_source_fidelity(original, original, slug="fixture", semantic_reviews=[kept, retired])
    assert any("conflicting requirement mappings" in failure for failure in failures)


@pytest.mark.parametrize("body", [
    "Return the full pitch template with sections filled or marked `[TODO]`.",
    'Return the literal marker "TBD" for unknown fields and explain each missing input.',
    '```json\n{"status": "TODO", "reason": "missing user input"}\n```',
    "Return findings in a table. Use TODO markers to identify unresolved source evidence.",
    'Return a reviewed template.\n- `TODO`: the literal status for missing user input.',
])
def test_literal_uncertainty_markers_are_valid_output_requirements(body: str) -> None:
    assert quality._output_specificity_score("## Required Output\n" + body, {}) >= 8


@pytest.mark.parametrize("body", ["", "TODO", "TBD", "[TODO: define the output contract]",
                                  "`TODO`", "Output: TBD", "Describe the output here.",
                                  "Return findings.\n- Evidence: TBD", "```text\nTODO\n```", "> TBD"])
def test_unfilled_output_contract_placeholders_still_fail(body: str) -> None:
    assert quality._output_specificity_score("## Required Output\n" + body, {}) < 8


def test_real_pitch_source_judges_ready_with_literal_todo_contract() -> None:
    import json
    import subprocess
    import sys
    command = [sys.executable, str(ROOT / "scripts/uac-import.py"), "--mode", "judge", "--source",
               "ssot/engos-audit-pitch-review.md", "--benchmark-search", "off", "--clarity", "off", "--output", "json"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["quality_result"]["status"] == "structural_ready"
    assert payload["quality_result"]["scorecard"]["output_specificity"] >= 8
