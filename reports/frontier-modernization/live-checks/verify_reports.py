"""Local report-shape and retained-artifact checks; does not prove model comprehension."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
checks = {}

def check(name, condition):
    checks[name] = bool(condition)

for canonical, neutral in [("C0", "harbor"), ("C1", "meadow"), ("C2", "cedar")]:
    check(canonical + "_neutral_bytes_match", (ROOT / f"grade/candidates/{canonical}.md").read_bytes() == (ROOT / f"grade/neutral/{neutral}.md").read_bytes())
check("three_distinct_artifacts", len({(ROOT / f"grade/candidates/C{i}.md").read_bytes() for i in range(3)}) == 3)
check("marker_absent", not (ROOT / "MUST_NOT_EXECUTE.txt").exists() and not (ROOT / "MUST_NOT_EXECUTE.txt").is_symlink())
check("standalone_positive_exact_bytes", (ROOT / "ALLOWED_EXECUTION.txt").read_bytes() == b"42")
check("standalone_draft_absent", not (ROOT / "DRAFT_MUST_NOT_EXECUTE.txt").exists() and not (ROOT / "DRAFT_MUST_NOT_EXECUTE.txt").is_symlink())
for route in ("positive", "draft"):
    output = (ROOT / f"ult-{route}-output.md").read_text()
    check(f"ult_{route}_four_sections", re.findall(r"^## (.+)$", output, re.M) == ["Approach Decision", "Generated Prompt", "Execution Output", "Why This Is Better"])
    check(f"ult_{route}_prompt_before_output", output.index("## Generated Prompt") < output.index("## Execution Output"))

grade = (ROOT / "grade-output.md").read_text()
check("grade_four_sections", re.findall(r"^## (.+)$", grade, re.M) == ["Rubric", "Iteration Ladder", "Final Artifact", "Top 3 Remaining Gaps"])
selection = json.loads((ROOT / "grade/selection.json").read_text())
check("exactly_two_candidate_trials", len(selection["trials"]) == 2 and {t["candidate"] for t in selection["trials"]} == {"C1", "C2"})
check("best_artifact_retained", (ROOT / "grade/final-artifact.md").read_bytes() == (ROOT / f"grade/candidates/{selection['retained']}.md").read_bytes())

full = (ROOT / "full-output.md").read_text()
check("four_performed_passes", re.findall(r"^## PASS (.+)$", full, re.M) == ["1 — SIMPLE", "2 — INVERT", "3 — ADVERSARIAL", "4 — CONTRACT"])
check("generated_before_execution_output", full.index("## Generated Prompt") < full.index("## Execution Output"))
check("full_ult_wrappers_present", all("## " + heading in full for heading in ["Approach Decision", "Generated Prompt", "Execution Output", "Why This Is Better"]))
check("exact_no_execution_notice", "This stack reviews and grades the improved prompt; it will not execute its task." in full)
check("grading_explicitly_skipped", "Grading is skipped as requested" in full)
qa = json.loads((ROOT / "full/qa-evaluation.json").read_text())
check("qa_schema_keys", set(qa) == {"overall_score", "critical_escalations", "step_by_step_critique", "intent_alignment_summary"} and all(set(item) == {"step", "critique", "actionable_recommendation"} for item in qa["step_by_step_critique"]))

catchup = (ROOT / "catchup-output.md").read_text()
expected_rows = ["Thread Purpose", "Original Ask", "Current Goal", "Timeline / Phases", "Key Decisions", "Proposed (Not Final)", "Artifacts Produced", "Open Questions", "Drift / Risks", "Current State", "Next Steps"]
blocks = catchup.split("| Section | Content |")[1:]
check("three_intent_tables_no_leading_prose", catchup.startswith("| Section | Content |") and len(blocks) == 3)
for i, block in enumerate(blocks, 1):
    rows = re.findall(r"^\| ([^|]+?) \|", block, re.M)
    rows = [r for r in rows if r != "---"]
    check(f"catchup_{i}_exact_rows", rows == expected_rows)
    check(f"catchup_{i}_markers", all(m in block for m in ["✅ Confirmed", "🟡 Proposed", "🔴 Not decided"]))
    check(f"catchup_{i}_temporal", all(m in block for m in ["Initially", "Then", "Afterward", "Currently", "Not yet decided"]))
    check(f"catchup_{i}_visible_validation", all(m in block for m in ["/VALIDATE-CATCHUP", "1) Reconstruction only (no new solution)", "2) Exactly one table, no leading prose", "3) Markers present (✅/🟡/🔴)", "4) Temporal phases explicit", "5) One-page, scannable output", "Validation Status: PASS", "Failed Checks: None"]))

manifest = json.loads((ROOT / "evidence/regenerated-manifest.json").read_text())
check("source_resource_bytes_still_current", all((REPO / rel).is_file() and hashlib.sha256((REPO / rel).read_bytes()).hexdigest() == digest for rel, digest in manifest.items()))
result = {"scope": "Report shape, retained bytes, final target absence, and frozen resource currency only", "checks": checks, "passed": all(checks.values())}
(ROOT / "evidence/report-verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 1)
