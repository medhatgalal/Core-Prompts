"""Independent reviewer-authored source-span maps, not a semantic auto-grader.

Run only after the reviewer confirms the recorded preservation findings are fixed.
The validator checks shape/binding; the rationales record the human-readable review.
"""
from pathlib import Path
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from intent_pipeline.capability_resources import effective_capability_text, load_resource_bundle
from intent_pipeline.uac_baselines import text_sha256, validate_requirement_review

SLUG = "engos-meta-supercharge"
OUT = Path(__file__).resolve().parent
ENTRY = ROOT / "reports/frontier-modernization/candidates" / f"{SLUG}.md"
RES = ROOT / "sources/capability-resources" / SLUG / "references"
FILES = {"entry": ENTRY, "help": RES / "help.md", "examples": RES / "help-examples.md",
         "shared": RES / "shared-review.md", "models": RES / "model-guidance.md"}
FILES.update({m: RES / "modules" / f"{m}.md" for m in (
    "ult", "catchup", "basis", "simple", "invert", "adversarial", "contract", "grade", "full", "gaslight", "stop-ult")})

def section(key, heading):
    text = FILES[key].read_text()
    start = text.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    rest = text[start + len(heading):]
    end = re.search(rf"(?m)^#{{1,{level}}} ", rest)
    return (heading + (rest[:end.start()] if end else rest)).strip()

def paragraph(key, needle):
    text = FILES[key].read_text()
    start = text.index(needle)
    end = text.find("\n\n", start)
    return text[start:end if end >= 0 else len(text)].strip()

def line(key, prefix):
    return next(x for x in FILES[key].read_text().splitlines() if x.startswith(prefix))

def through(key, first, after):
    text = FILES[key].read_text()
    start = text.index(first)
    return text[start:text.index(after, start + len(first))].strip()

def evidence():
    e = {"meta": FILES["entry"].read_text().split("\n\n")[0]}
    for key, heading in {
        "purpose": "## Purpose", "objective": "## Primary Objective", "agent": "## Agent Operating Contract",
        "boundaries": "## Tool Boundaries", "paths": "## Output Directory", "hints": "## Invocation Hints",
        "inputs": "## Required Inputs", "outputs": "## Required Output", "constraints": "## Constraints",
        "activation": "### Activation Triggers", "help_triggers": "### Help Triggers",
        "examples_triggers": "### Help Examples Trigger", "details_triggers": "### Details Trigger",
        "terminal": "### Terminal-Control Precedence", "grammar": "### Command Grammar",
        "stack": "### Stacking is Implicit", "route": "### Optional Routing Preview Flag",
        "goal": "### Primary Goal", "hard": "### HARD CONSTRAINTS", "questions": "### Turn-Taking Protocol",
        "order": "### Multi-Pass Pipeline Order", "auto": "### Auto-Routing",
        "modifiers": "### Reflective Controls", "independence": "### Independent Subagents",
        "delivery": "### Resource Delivery Gate", "precedence": "### Output Precedence",
        "capstone": "## 2) Auto-Catchup Capstone", "help_entry": "## HELP OUTPUT",
        "examples_entry": "## HELP EXAMPLES OUTPUT", "details": "## MODULE REFERENCE",
        "entry_examples": "## Examples", "rubric": "## Evaluation Rubric", "timing": "## Review Timing",
    }.items():
        e[key] = section("entry", heading)
    e["shared"] = FILES["shared"].read_text().strip()
    for module in ("ult", "catchup", "basis", "simple", "adversarial", "contract", "full", "gaslight"):
        e[module + "_purpose"] = section(module, "### Purpose")
        e[module + "_hard"] = section(module, "### HARD CONSTRAINTS")
    for module in ("ult", "catchup", "basis", "simple", "invert", "contract", "grade", "full"):
        e[module + "_output"] = section(module, "### Output Structure")
    e.update({
        "ult_mode": section("ult", "### Mode Behavior"),
        "ult_execute": section("ult", "### Critical Execution Rule"),
        "catchup_evidence": section("catchup", "### Evidence and Cognitive Load"),
        "catchup_validation": section("catchup", "### Catchup Validation"),
        "basis_workflow": section("basis", "### First-Principles Workflow"),
        "basis_domain": section("basis", "### Domain Mapping"),
        "basis_examples": section("basis", "### Examples"),
        "simple_diagnosis": section("simple", "### Diagnostic Checklist"),
        "simple_workflow": section("simple", "### Decomplect Workflow"),
        "simple_domains": section("simple", "### Principle-to-Practice Matrix"),
        "simple_examples": section("simple", "### Examples"),
        "simple_foundation": section("simple", "### Foundation"),
        "simple_outputs_and_examples": through("simple", "### Output Structure", "### Foundation"),
        "invert_workflow": section("invert", "### Workflow and Boundaries"),
        "adversarial_output": section("adversarial", "### Standard Output Structure"),
        "debate": section("adversarial", "### Nested Module: /adversarial /debate —"),
        "deep": section("adversarial", "### Nested Module: /adversarial /debate /deep"),
        "contract_template": section("contract", "### Contract Spec Template"),
        "contract_spec": through("contract", "### HARD CONSTRAINTS", "### QA Evaluation JSON"),
        "contract_json": section("contract", "### QA Evaluation JSON"),
        "grade_purpose": section("grade", "### Purpose"),
        "grade_activation": through("grade", "### Purpose", "### Trial Contract"),
        "grade_trials": section("grade", "### Trial Contract"),
        "gaslight_commands": section("gaslight", "### Commands"),
        "gaslight_table": section("gaslight", "### GASLIGHT 13"),
        "stop_ult": FILES["stop-ult"].read_text().strip(),
        "help_commands": section("help", "### Common Commands"),
        "help_examples": section("help", "### Per-Module Examples"),
        "help_route": section("help", "### Routing Preview"),
        "help_details": section("help", "### Full Spec"),
    })
    for i in range(1, 14):
        e[f"gaslight_{i}"] = line("gaslight", f"| {i} |")
    return e

# Each tuple closes the next ordered source span; starts are derived from the
# preceding end. Blank separators belong to the adjoining meaningful section.
# Values are: last source line, section label, disposition, evidence key, rationale.
CURRENT = [
    (11, "Identity and surface metadata", "reformulated", "meta", "Canonical identity, advisory agent plus skill surfaces, and tool metadata remain; version is advanced for the authorized modernization."),
    (19, "Purpose, objective, behavioral-proof boundary", "preserved", "objective", "Prompt and plan hardening remains the objective; measured superiority still routes to Auto-Research."),
    (34, "Agent mission and responsibilities", "reformulated", "agent", "The mission and four existing responsibilities remain; optional partitioning becomes actual independent delegation as explicitly authorized."),
    (39, "Tool authority boundaries", "reformulated", "boundaries", "Inspection and advisory artifacts remain allowed; new wording permits authorized subagent tools without claiming host ownership or destructive authority."),
    (48, "File and inline output destinations", "preserved", "paths", "All four report paths and their inline equivalents remain exact."),
    (59, "Invocation intent examples", "preserved", "hints", "All task classes and the debate/deep invocation hint are retained."),
    (66, "Required inputs", "preserved", "inputs", "Artifact, sources, claimed differences, constraints, and risk context remain required inputs."),
    (88, "General and specialized response requirements", "reformulated", "outputs", "The general wrapper and comparison, debate, and proof-handoff fields remain; exact terminal/module schemas take precedence to avoid contradicting their preserved shapes."),
    (97, "Framework and authority constraints", "reformulated", "constraints", "Minimum useful passes, no invented preferences, and substantive grades remain; authorized delegation replaces the blanket runtime-delegation prohibition."),
    (106, "Four activation forms and alias normalization", "preserved", "activation", "All namespaced and short conversational forms, case behavior, argument order, and no alias-package claim remain."),
    (113, "Help triggers", "preserved", "help_triggers", "All four help spellings still select help-only output."),
    (120, "Examples triggers", "preserved", "examples_triggers", "The three help-example spellings retain their terminal output contract."),
    (124, "Details triggers", "preserved", "details_triggers", "Both details spellings retain full-reference output."),
    (126, "Terminal precedence heading", "reformulated", "terminal", "Terminal controls remain ahead of routing and stacking after the approved removal of global stop."),
    (127, "Global stop precedence", "retired", None, "The global /stop command is intentionally removed; /stop-ult remains the mode exit."),
    (131, "Remaining terminal controls", "reformulated", "terminal", "Stop-ULT priority, section-only help controls, and the multiple-control clarification remain; obsolete references to global stop are removed."),
    (147, "Command grammar and examples", "preserved", "grammar", "Zero or more slash commands, basis and stack examples, debate shortcuts, full, examples, and catchup remain."),
    (150, "Implicit sequential stacking", "preserved", "stack", "Multiple modules still form a mandatory multi-pass stack without a /stack command."),
    (155, "Optional routing preview", "preserved", "route", "The exact first-line Routing shape and proceed behavior remain."),
    (165, "Core quality objectives", "preserved", "goal", "Prompt, plan, reasoning, safety, and execution quality goals are retained."),
    (174, "Global hard constraints", "preserved", "hard", "No fabrication, at-most-three questions or assumption packs, sequential frameworks, hidden-reasoning prohibition, and unsafe/destructive confirmation remain."),
    (183, "Turn taking and assumption packs", "preserved", "questions", "Materiality threshold, conservative/balanced/aggressive packs, and no pretending to be the user remain."),
    (195, "Canonical pipeline and ULT mode", "reformulated", "order", "All six passes stay in order; basis and inversion descriptions implement the approved richer lenses, and grading implements real bounded trials."),
    (206, "Smart routing", "reformulated", "auto", "Task-to-route mappings and announcement remain, with actual independent subagents replacing orchestration guidance."),
    (216, "Reflective controls and conflict handling", "preserved", "modifiers", "All five modifiers, one-modifier limit, clarification on conflicts, and safe auto-routing exception remain."),
    (234, "Delegation discovery and coordination", "reformulated", "shared", "Real independent agents replace simulated roles; runtime discovery, configured default model, explicit responsibilities, stop conditions, and evidence-based synthesis remain, with cold initial review added."),
    (244, "Automatic catchup capstone", "preserved", "capstone", "Completion-only capstone, small-reply exclusion, and skip/no-catchup controls remain."),
    (247, "Terminal help resource", "reformulated", "help_entry", "Help is still loaded and returned alone; manifest-based delivery is now explicit."),
    (252, "Terminal examples resource and path semantics", "reformulated", "examples_entry", "Example generation remains terminal and nonexecuting; skill/agent relative paths and missing-resource handling remain."),
    (254, "Full module reference", "relocated", "details", "Module specifications move to complete route resources; details must return those full specifications, not the table alone."),
    (259, "Global stop module", "retired", None, "The user explicitly approved removing only global /stop, including its purpose and precedence rule."),
    (268, "ULT purpose and persistence", "reformulated", "ult_mode", "Prompt creation/evaluation remains and ULT persists across subsequent invocations until /stop-ult; only the retired stop exit is removed."),
    (274, "ULT improvement bar and controls", "reformulated", "ult_hard", "Material benefit replaces an unsupported fixed twenty-percent claim; hidden reasoning, forced scaffolding, and modifier limits remain."),
    (284, "ULT display and execution", "reformulated", "ult_execute", "Copy-ready prompt still precedes execution; authorized execution follows display, explicit draft/review-only suppresses it, and full overrides execution with an announcement."),
    (291, "ULT exact output shape", "relocated", "ult_output", "The same Approach Decision, Generated Prompt, Execution Output, and Why This Is Better fields remain in order."),
    (305, "Catchup reconstruction constraints", "relocated", "catchup_hard", "Reconstruction only, no leading prose, unknown markers, status markers, and temporal discipline are retained; independent verification adds evidence without new solutions."),
    (322, "Catchup exact visible table", "relocated", "catchup_output", "The complete two-column table, all eleven rows, and their visible text are byte-preserved from the current baseline."),
    (340, "Catchup exact validation text", "relocated", "catchup_validation", "All five checks, one revision/recheck, PASS/FAIL line, and Failed Checks output remain exact."),
    (347, "Basis purpose and activation domains", "reformulated", "basis_purpose", "First-principles sufficiency now leads the lens; cost accounting remains a supported application rather than its definition."),
    (354, "Basis hard constraints", "relocated", "basis_hard", "Unknown minima, primitive versus implementation distinctions, real costs, necessary gates, and no personality imitation remain."),
    (362, "Basis output fields", "relocated", "basis_output", "All six output headings remain, including the conditional ratio field."),
    (370, "Basis reasoning workflow", "reformulated", "basis_workflow", "Primitives, actual measurements, waste, and redesign remain. Sufficient design is derived first; evidence-free ratios and forced deletion-first ordering are replaced as authorized."),
    (376, "Basis domain mappings", "relocated", "basis_domain", "Prompt/skill, software workflow, product/operation, and knowledge-work raw-material mappings remain."),
    (385, "Basis representative examples", "relocated", "basis_examples", "Both capability and workflow before/after examples remain, including preservation of justified quality and review gates."),
    (399, "Simple purpose and hard constraints", "relocated", "simple_hard", "Simplicity remains separation from interleaving, not fewer parts or reduced scope, across technical and nontechnical domains."),
    (407, "Simple output contract", "relocated", "simple_output", "The same six required output fields remain."),
    (428, "Simple diagnostic checklist", "relocated", "simple_diagnosis", "Braids, order coupling, longevity questions, and AI-specific deterministic-interface guidance remain."),
    (434, "Simple decomplect workflow", "reformulated", "simple_workflow", "Assess/decomplect/compose/validate now requires an actual dependency removed and an independently checked example of independent change, preserving intended behavior."),
    (460, "Simple cross-domain practice matrix", "relocated", "simple_domains", "All six domains remain; historical MUST/PREFER, one-way dependency, and invariant-validation details are restored rather than lost."),
    (469, "Simple illustrative examples", "reformulated", "simple_examples", "The planning example now demonstrates actual requirements/implementation independence; the separate speed/safety/scalability claims example remains."),
    (479, "Inversion purpose and failure analysis", "reformulated", "invert_workflow", "Backward causal reasoning replaces the fixed top-three quota; missing signals and guarded forward output remain, with explicit observation-channel checks."),
    (484, "Inversion output fields", "relocated", "invert_output", "Inversion Analysis, Dogs Not Barking, and Guarded Forward Solution are unchanged."),
    (491, "Adversarial purpose and route choices", "relocated", "adversarial_purpose", "Compact attack, surface debate, and deep debate retain their task/risk fit."),
    (499, "Adversarial evidence and scope limits", "reformulated", "adversarial_hard", "Specific grounded critique, assumptions, no unsolicited total rewrite, fresh evidence, and no efficacy claims remain; real attackers and valid no-issue outcomes are added."),
    (505, "Standard adversarial output", "relocated", "adversarial_output", "All four attack/gap/fix/residual-risk fields remain."),
    (517, "Surface debate purpose, shortcut, and flow", "reformulated", "debate", "Bull/Bear/Decider and shortcut remain; separate cold initial agents and an independent decider strengthen the same flow."),
    (529, "Surface debate required output", "relocated", "debate", "All ten required fields, confidence scale, flip conditions, and human judgment remain."),
    (535, "Debate task profiles", "relocated", "debate", "General reasoning, code review, architecture decision, and investing analysis profiles and focus areas remain."),
    (549, "Deep debate activation and boundaries", "reformulated", "deep", "Deep remains debate-only, rejects invalid standalone use, requires strongest-point engagement and verdict-flip evidence, and keeps investing-data boundaries; council independence is added."),
    (557, "Deep debate round sequence", "relocated", "deep", "Context, Bull opening, Bear rebuttal, Bull counter, Bear final, and Decider order remain."),
    (571, "Deep debate output shape", "relocated", "deep", "All twelve fields remain, including decision-risk table, mitigation plan, missing evidence, and recommended validation."),
    (582, "Contract purpose and hard constraints", "reformulated", "contract_hard", "Define then verify remains; obligation-source-acceptance-evidence mapping and versioned independent review add rigor while preserving missing-info and escalation boundaries."),
    (593, "Contract outputs and specification template", "relocated", "contract_spec", "Contract Spec plus QA Evaluation JSON remain, with the five bracketed specification fields and historical primary-value ordering restored."),
    (611, "Strict QA JSON schema", "relocated", "contract_json", "Every field and nested step/critique/actionable_recommendation object is unchanged; no new QA schema is introduced."),
    (620, "Grade purpose and trial rules", "reformulated", "grade_trials", "Exactly-ten self-grading becomes up-to-ten actual independent candidate trials, at least two absent a user/hard limit, best retention, and explicit target-plus-plateau stopping as authorized."),
    (627, "Grade visible output", "relocated", "grade_output", "The four original output headings remain; only actual trials are shown and the final retained artifact remains complete."),
    (639, "Full purpose and execution boundaries", "reformulated", "full_hard", "Sequential pass output, no final task execution, missing-info handling, grade-by-default with skip, and basis opt-in remain; finding carryforward and ULT conflict resolution are explicit."),
    (648, "Full pass wrappers", "reformulated", "full_output", "SIMPLE/INVERT/ADVERSARIAL/CONTRACT/GRADE order and optional PASS 0 BASIS remain; the grade caption accurately reflects the authorized trial budget."),
    (658, "Gaslight purpose and hard boundaries", "reformulated", "gaslight_hard", "Explicit-only activation, one-to-three techniques, intent, and requested-output discipline remain; false premises are fictional framing and independent review is required."),
    (668, "Gaslight commands and output", "reformulated", "gaslight_commands", "Task/list/help/exact-ID-selection commands and three-part prompt output remain; intended effect with uncertainty replaces a guaranteed improvement implication."),
    (672, "Gaslight table headings", "reformulated", "gaslight_table", "The same thirteen-ID template/example table is retained; the claims column is relabeled to intended effects and limits."),
]
TECHNIQUE_RATIONALE = "ID, technique name, prompt template, and example remain. Unsupported universal efficacy becomes a conditional intended effect with explicit limits under the authorized fictional-framing modernization."
CURRENT += [(672+i, f"Gaslight technique {i}", "reformulated", f"gaslight_{i}", TECHNIQUE_RATIONALE) for i in range(1,14)]
CURRENT += [
    (690, "Stop-ULT mode exit", "relocated", "stop_ult", "Exit remains limited to ULT mode and does not disable SuperCharge."),
    (704, "Representative usage and failure avoidance", "reformulated", "entry_examples", "Concrete first-principles stack, ULT/full, and real grading examples replace generic output illustration while retaining minimum-useful-framework and improvement requirements."),
    (714, "Evaluation rubric", "reformulated", "rubric", "Routing, meaningful improvement, truthful evidence, usable surfaces, and authority remain; delivery, independence, retained behavior, and real candidate grading are now explicit review checks."),
    (722, "Review timing and version terminator", "reformulated", "timing", "Major rewrites, plan adoption, high-stakes decisions, and UAC onboarding remain the timing; version changes and critique-versus-efficacy distinction are explicit."),
]

HISTORICAL = [
    (12, "Identity, intended use, and portability", "reformulated", "meta", "Swiss Army Knife purposes and both surfaces remain. Namespaced identity follows the current baseline; the user-approved actual tools and full-resource delivery replace the historical no-tools/no-path dependency claim."),
    (17, "Quick-guide and details hints", "reformulated", "activation", "Short conversational aliases still resolve the same help/details controls; the current canonical package identity avoids duplicate alias packages."),
    (24, "Activation forms", "preserved", "activation", "Leading supercharge and /supercharge remain conversational activation forms alongside their namespaced forms."),
    (31, "Help spellings and terminal behavior", "preserved", "help_triggers", "Help, /help, -h, and --help still produce help only, through the alias-normalization rule."),
    (36, "Details spellings and terminal behavior", "preserved", "details_triggers", "Both details forms still return the complete module reference through the common alias rule."),
    (46, "Slash-command grammar and examples", "preserved", "grammar", "Zero or more slash commands, default routing, ULT, stacked lenses, full, and catchup remain usable."),
    (49, "Implicit stack", "preserved", "stack", "Multiple modules still execute as sequential passes without requiring /stack."),
    (56, "Routing preview", "preserved", "route", "The exact first-line Routing schema and proceed behavior are retained."),
    (66, "Core quality objectives", "preserved", "goal", "Prompt, plan, reasoning, safety, and multi-step execution quality remain the goals."),
    (75, "Global hard constraints", "preserved", "hard", "No fabrication, limited questions/assumption packs, sequential frameworks, hidden-reasoning prohibition, determinism, and unsafe/destructive confirmation remain."),
    (84, "Turn taking", "preserved", "questions", "Materially useful questions, three named assumption packs, and no pretending to be the user remain."),
    (95, "Canonical pass order and ULT wrapper", "reformulated", "order", "The original five-pass order is preserved with the current opt-in basis predecessor; authorized real grading replaces exactly-ten self-grading while ULT remains a wrapper mode."),
    (104, "Default routing", "reformulated", "auto", "Prompt, architecture, high-stakes, options/full, and long-horizon routes remain; actual independent subagents replace orchestration advice."),
    (112, "Reflective modifiers", "preserved", "modifiers", "All five controls and the single-modifier rule remain, with explicit conflict handling from the current baseline."),
    (129, "Agent partitioning and discovery", "reformulated", "shared", "Actual discovered/default configured agents preserve explicit task partitioning; simulated roles and no-interface self-review fallback are intentionally prohibited by the user's modernization."),
    (136, "Agent coordination", "reformulated", "shared", "Explicit objectives/inputs/constraints/output/stop conditions and evidence-based conflict resolution remain; the author cannot approve itself."),
    (147, "Catchup capstone", "preserved", "capstone", "Major-work completion only, small-response exclusion, and skip/no-catchup controls remain."),
    (158, "Help identity and common operational commands", "relocated", "help_commands", "Default, ULT, full, catchup, and explicit gaslight commands remain in bundled help; canonical names are accepted through short aliases."),
    (159, "Help global stop command", "retired", None, "The global /stop help entry is removed with the explicitly retired command; /stop-ult remains listed in help controls."),
    (168, "Help representative examples", "reformulated", "help_examples", "Prompt improvement, simplification/inversion stacks, full CI-gate, gaslight, and catchup usage remain with more explicit per-module examples in bundled help."),
    (171, "Help routing preview", "relocated", "help_route", "The routing-preview usage and first-line behavior remain."),
    (178, "Help details link and module-reference entry", "relocated", "details", "Details returns complete module resources rather than stopping at the routing table; module reference remains a terminal presentation."),
    (185, "Global stop specification", "retired", None, "The global mode-exit /stop module and priority are intentionally removed by explicit user instruction."),
    (194, "ULT purpose and persistent state", "reformulated", "ult_mode", "Creation/evaluation/refinement and persistent ULT remain; /stop-ult is the sole retained explicit mode exit."),
    (200, "ULT hard constraints", "reformulated", "ult_hard", "The unmeasured fixed twenty-percent claim is replaced by material task benefit. Hidden reasoning, forced XML/ReAct/phasing, and modifier limits remain."),
    (210, "ULT prompt-first execution contract", "reformulated", "ult_execute", "Copy-ready prompt is displayed before scoped execution; generated-prompt/execution-output order remains, with authorized draft/review-only and full exceptions explicit."),
    (218, "ULT four-field output", "relocated", "ult_output", "All four mandatory fields remain; they resolve the historical core-payload wording without deleting the surrounding explanation."),
    (232, "Catchup reconstruction and marker discipline", "relocated", "catchup_hard", "One intent per reconstruction, no new solutions/leading prose, unknown markers, decision markers, and chronological clues are retained."),
    (249, "Catchup exact visible table", "relocated", "catchup_output", "The same eleven rows and meanings are preserved in the current baseline's normalized wording; no user-visible table field is removed."),
    (268, "Catchup validation", "relocated", "catchup_validation", "The five checks, one revision and recheck, and exact PASS/FAIL/Failed Checks fields remain."),
    (282, "Simple purpose and hard constraints", "reformulated", "simple_hard", "Independence from interleaving, not easy/familiar/fewer parts or smaller scope, remains; explicit boundaries and nontechnical application preserve the original lens."),
    (293, "Simple required outputs and tailored examples", "reformulated", "simple_outputs_and_examples", "All six outputs remain and the restored one-to-two tailored examples rule retains the historical one-general-example fallback when domain is unknown."),
    (314, "Simple diagnostic and longevity checklist", "relocated", "simple_diagnosis", "Braids, ordering, shared context, requirements/design entanglement, independent change, longevity questions, and AI determinism remain; the strengthened workflow addresses state/time coupling explicitly."),
    (320, "Simple Assess-Decomplect-Compose-Validate", "reformulated", "simple_workflow", "The four operations remain, strengthened with concrete independent-change proof and actual independent checking instead of cosmetic reorganization."),
    (330, "Simple planning and architecture practice", "relocated", "simple_hard", "Intent/constraint/option/decision/execution separation and contracts remain in the domain matrix. MUST-versus-PREFER distinctions and one-way dependencies are restored as explicit cross-domain hard constraints."),
    (338, "Simple implementation and operations practice", "relocated", "simple_hard", "Pure transformations, explicit side effects, modular workflows, and no invisible cache coupling remain in the domain matrix; invariant validation beyond outcomes is restored as an explicit cross-domain constraint."),
    (347, "Simple requirements and writing practice", "relocated", "simple_domains", "What-versus-how, prior invariants/acceptance, separate thesis/evidence/counterargument/conclusion, and explicit maps remain."),
    (359, "Simple representative examples", "reformulated", "simple_examples", "The prompt example now proves requirements/implementation independence instead of heading rearrangement, and the speed/safety/scalability evidence-separation example remains."),
    (369, "Inversion failure and missing-signal analysis", "reformulated", "invert_workflow", "Causal backward analysis, missing signals, and guarded forward reasoning remain; the user-authorized no-fixed-quota and observation-channel checks replace top-three enumeration."),
    (376, "Inversion required output", "relocated", "invert_output", "The same three output fields remain, with prevention/detection/recovery implementing mitigation and trigger intent."),
    (386, "Adversarial scope and constraints", "reformulated", "adversarial_hard", "Specific edge cases, assumptions, and critique/fixes before total rewrite remain; actual independent attackers and valid acquittal add the approved rigor."),
    (394, "Adversarial output", "relocated", "adversarial_output", "Attack Surface, Contradictions/Gaps, Mitigations/Fixes, and Residual Risk remain."),
    (400, "Unified contract and QA purpose", "reformulated", "contract_purpose", "Defining the contract and then independently evaluating it remains one coherent operation; adequate contracts may be retained without gratuitous restatement."),
    (406, "Contract hard constraints", "reformulated", "contract_hard", "No invented context, limited questions or packs, verifiable JSON on request, and explicit safety escalation remain; obligation evidence and fixed-criteria review are added."),
    (410, "Two contract outputs", "relocated", "contract_output", "Contract Spec and QA Evaluation JSON remain the two visible outputs."),
    (417, "Contract template and intent priority", "relocated", "contract_spec", "All five bracketed fields remain, with primary-value-over-secondary ordering restored as an explicit hard constraint and independent-observer acceptance retained."),
    (437, "Strict QA schema", "relocated", "contract_json", "Every original JSON field and nested critique object is preserved without schema additions."),
    (443, "Grade purpose and activation scope", "reformulated", "grade_activation", "The restored explicit-invocation-or-full boundary prevents grade becoming a default pass; independent real trials intentionally replace self-grading."),
    (451, "Grade trial mechanics", "reformulated", "grade_trials", "Real candidates, independent 1–10 grades, substantive deltas, compact records, and full final artifact preserve the improvement intent. Up-to-ten budget, best retention, and target-plus-two-attempt plateau replace forced ten improvements as authorized."),
    (459, "Grade four-field visible output", "reformulated", "grade_output", "Rubric, actual-trial ladder, full Final Artifact, and Top 3 Remaining Gaps remain; no fictional ladder rows or manufactured gaps are permitted."),
    (470, "Full no-execution and sequence contract", "reformulated", "full_hard", "Sequential lenses, no generated-task execution, limited missing-info questions, and default grade with skip option remain; authorized grading count and ULT precedence are explicit."),
    (479, "Full pass labels", "reformulated", "full_output", "The five original pass labels and order remain; grade's caption is updated to the authorized up-to-ten real-trial contract."),
    (490, "Gaslight purpose and bounded use", "reformulated", "gaslight_hard", "Explicit-only, intent clarity, and requested-output discipline remain. The inconsistent historical 2–4 versus 1–3 count is resolved to the current and user-approved 1–3 rule; false premises are hypothetical."),
    (499, "Gaslight command variants", "reformulated", "gaslight_commands", "Task/list/help/exact-ID selection and prompt/techniques/effect-note output remain; effects are now stated conditionally."),
    (503, "Gaslight canonical table shape", "reformulated", "gaslight_table", "The same thirteen techniques, templates, and examples remain, with an intended-effect/limits column replacing unsupported universal claims."),
]
HISTORICAL += [(503+i, f"Gaslight technique {i}", "reformulated", f"gaslight_{i}", TECHNIQUE_RATIONALE) for i in range(1,14)]
HISTORICAL += [
    (526, "Stop-ULT and version terminator", "relocated", "stop_ult", "ULT mode exit remains limited to ULT and does not disable SuperCharge; the version marker changes with the approved update."),
]

def build(name, mappings, e, entry, effective):
    suffix = "" if name == "current" else ".historical"
    source = ROOT / "reports/frontier-modernization/baseline" / f"{SLUG}{suffix}.md"
    original = source.read_text()
    rows = []
    start = 1
    for number, (end, label, disposition, evidence_key, rationale) in enumerate(mappings, 1):
        row = {"id": f"{name.upper()}-{number:03d}", "source_start_line": start,
               "source_end_line": end, "source_label": label, "disposition": disposition,
               "rationale": rationale}
        if disposition == "retired":
            row["authorization"] = "User-approved frontier capability modernization, S19: remove global /stop only; preserve /stop-ult and ULT persistence. Scope relayed in independent review dispatch by /root."
        else:
            row["candidate_excerpt"] = e[evidence_key]
        rows.append(row)
        start = end + 1
    review = {
        "schema_version": "UACRequirementReview.v1", "slug": SLUG,
        "source_path": str(source.relative_to(ROOT)),
        "original_sha256": text_sha256(original), "candidate_sha256": text_sha256(entry),
        "effective_sha256": text_sha256(effective),
        "reviewer": {"agent_id": "review_supercharge_admission", "author_agent_id": "implement_skills", "independent": True},
        "verdict": "approved", "review_scope": "Independent source requirement preservation and approved semantic modernization; not behavioral promotion or provider-claim verification.",
        "requirements": rows,
    }
    failures = validate_requirement_review(review, slug=SLUG, original_text=original, candidate_text=entry, effective_text=effective)
    if failures:
        raise ValueError({"baseline": name, "failures": failures})
    return review

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved-after-review", action="store_true")
    args = parser.parse_args()
    if not args.approved_after_review:
        raise SystemExit("Explicit reviewer completion required; no approval artifacts written.")
    entry = ENTRY.read_text()
    effective = effective_capability_text(ROOT, SLUG, entry)
    e = evidence()
    reviews = {name: build(name, mappings, e, entry, effective) for name, mappings in (("current",CURRENT),("historical",HISTORICAL))}
    for name, review in reviews.items():
        (OUT / f"{name}-requirement-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
    bundle = load_resource_bundle(RES.parent, entry_text=entry)
    (OUT / "review-binding.json").write_text(json.dumps({
        "candidate_sha256": text_sha256(entry), "effective_sha256": text_sha256(effective),
        "manifest_sha256": bundle["manifest_sha256"],
        "resources": [{"path": r["path"], "sha256": r["sha256"]} for r in bundle["resources"]],
        "requirements": {k: len(v["requirements"]) for k,v in reviews.items()},
        "validation_failures": [], "scope": "Semantic preservation admission only; no behavioral promotion."
    }, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({name: {"requirements": len(r["requirements"]), "original_sha256": r["original_sha256"], "candidate_sha256": r["candidate_sha256"], "effective_sha256": r["effective_sha256"]} for name, r in reviews.items()},indent=2))

if __name__ == "__main__":
    main()
