---
name: "engos-meta-uac-import"
description: "Inspect an external prompt-like source, classify its fit, and prepare a quality-gated Core-Prompts plan, judge, or apply result. Use for capability intake; do not use for ordinary prompt editing or deployment."
display_name: "UAC Import — Capability Intake, Quality Review, and Uplift"
kind: "skill"
capability_type: "skill"
---
# UAC Import — Capability Intake, Quality Review, and Uplift

## Purpose
Take one or more external prompt-like sources and turn them into deterministic UAC assessments, layered manifests, canonical SSOT entries, machine-readable descriptors, quality-review artifacts, and advisory handoff contracts.

Supported inputs:
- local file path
- local folder path
- raw public HTTPS URL
- GitHub repo or folder URL
- multiple `--source` values in one run
- repomix-reduced repo input when available

Supported modes:
- `import`
- `audit`
- `explain`
- `plan`
- `judge`
- `apply`

Deterministic clarity lint from `instruction_clarity.v1` is available in every mode and enabled by default for `audit`, `plan`, and `judge`. It is advisory and never counts as behavioral evidence.

## Primary Objective
Exhaustively improve the source’s clarity, completeness, coherence, structure, and usability during onboarding while preserving its intended capability. Classify safely, recommend the right surfaces, and refuse landing until the structural and reviewed requirement gates pass. Structural diagnostics do not prove downstream model efficacy.

When structural quality is near the bar but behavioral confidence is still weak, escalate to a bounded behavioral proof workflow instead of overstating readiness.

## Invocation Contract
Use this capability as the AI-facing intake contract.

Primary entrypoints:
- `bin/uac` for intake, audit, planning, judging, and apply
- `bin/capability-fabric` for surface build, validation, and deploy steps after landing

Canonical state:
- `ssot/<slug>.md` is the human-readable prompt source of truth
- `.meta/capabilities/<slug>.json` is the machine-readable descriptor source of truth
- `sources/ssot-baselines/<slug>/baseline.md` is the baseline prompt-body fidelity source of truth used by UAC quality judging
- generated surfaces under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/` are derived artifacts

Operational rule:
- `apply` may mutate canonical repo state after confirmation
- deploy is separate and must never be implied by `apply`
- when shell entrypoints are required to complete the workflow, say so explicitly instead of assuming the caller knows them

## Agent Operating Contract
When exposed as an agent, inspect the supplied source and repository context, prepare exhaustive onboarding findings and candidate repairs, and return the same UAC deliverables. Use an actual independent subagent to review material meaning changes before supplying a requirement-review attestation. The invoking host retains runtime and authorization control. A judge run returns analysis and candidate artifacts without landing canonical state; an authorized apply performs the documented write/build/validation sequence.

## Output Directory
Canonical application writes `ssot/<slug>.md` and `.meta/capabilities/<slug>.json`, plus generated surfaces and evaluation contracts. Quality review evidence belongs in `reports/quality-reviews/<slug>/`; baseline lineage lives in `sources/ssot-baselines/<slug>/` and changes only under the independent promotion policy. These are UAC-owned onboarding artifacts, not output paths imposed on the imported capability's own task.

## Workflow
1. Ingest the source through the deterministic pipeline.
2. Produce a clean summary.
3. Run uplift to extract objective, scope, and constraints.
4. Run semantic routing.
5. If the source is a folder or repo subtree, inventory prompt-like files and classify them one by one.
6. Cluster broad repos into candidate families before recommending any landing.
7. Classify accepted sources as `skill`, `agent`, `both`, or `manual_review`.
8. Build layered manifests, cross-analysis, and advisory handoff data.
9. Select a quality profile and benchmark set.
10. Resolve the canonical baseline source from `sources/ssot-baselines/` before judging fidelity.
11. On `judge`, do not land or modify canonical repository state. Mechanical repairs produce a candidate artifact only. Inspect structure, formatting, style, ambiguity, contradictions, missing details, references, outputs, boundaries, and preservation. Return an explicit disposition for each applicable dimension. Apply only targeted mechanical repairs; request source-grounded semantic repairs from the invoking agent and an independent reviewer when meaning is unresolved. Do not append generic obligations to satisfy a count.
12. If `judge` finds that structural quality is close to passing but behavioral confidence is insufficient, route to `engos-optimization-auto-research` for bounded capability evaluation instead of guessing.
13. Search for benchmark sources only when the source is generic or fit confidence is weak.
14. Report `structural_ready` only for structural checks. Keep semantic review attestations, assembled resource content, host delivery evidence, and measured behavioral results distinct. No average score can waive an unresolved blocker.
15. Emit `EvalImpactPlan.v1` when requested and on `judge` or `apply` so the behavioral evaluator can select the minimum safe profile.
16. On `apply`, refuse landing unless the quality loop reaches `structural_ready`. Validate any supplied `PromotionVerdict.v2`; reject stale hashes or a mismatched slug. Treat `PromotionVerdict.v1` as read-only legacy evidence that cannot authorize promotion. During advisory rollout, an absent verdict leaves the result `behavioral_pending` and cannot materialize a new behavioral baseline.
17. On authorized `apply`, write canonical SSOT and the descriptor, persist the quality reviews, then rebuild and validate generated surfaces. Materialize a new baseline only after an independent `promote` verdict, or preserve a valid historical baseline without rewriting its lineage.
18. Keep deployment separate from apply.

## Tool Boundaries
- allowed: inventory sources, run deterministic uplift and classification, produce advisory manifests, and land canonical SSOT plus descriptor state when the quality gate passes
- forbidden: inventing capability strength that the source does not support, deploying to user homes during `apply`, or silently widening surface recommendations to satisfy packaging preferences
- escalation: if the work shifts from intake to architecture, docs quality, testing, or release readiness, route to the companion capability with a concrete handoff instead of stretching the import workflow

## Rules
- Evaluate outputs against the operative output contract for the selected route, including terminal and stacked precedence; unrelated bullets are not output evidence. Review contradictions using applicable scope and exceptions. Quoted examples are source material and do not become operative obligations merely by containing a keyword.
- Judge the entry and its explicitly routed resource dependencies together. Missing required files, cycles, path escapes, or mismatched content bindings block the affected operation. A model-authored read receipt is not delivery evidence.
- Repair the authoritative location of a defect; reuse equivalent existing content before adding a section. Preserve commands, schemas, quoted material, user decisions, and task scope. Do not invent missing facts or fixed procedures.
- Exact relocation, reviewed reformulation, and authorized retirement are different changes. Use `--requirement-review <path>` for an operator-supplied `UACRequirementReview.v1` binding the original, candidate, effective resource content, independent reviewer, and complete requirement dispositions. The operator must establish review provenance; the code validates bindings and coverage, not reviewer authenticity or semantic correctness. This record is not a `PromotionVerdict`.
- Stop automatic refinement when candidate and findings stagnate or cycle; report unresolved work. Repeated application to an unchanged accepted artifact must not add obligations or oscillate between styles.
- Prefer existing pipeline code over ad-hoc parsing.
- Keep results deterministic and roleplay-free.
- Fail closed for unsuitable URL content.
- For folders or repo trees, only group files that were actually inventoried.
- If the source is config-only, require manual review instead of pretending it is a prompt.
- If the source is already an agent definition, preserve its control-plane boundaries.
- Never make orchestration or delegation decisions for the imported runtime or control plane. Publish advisory metadata only. Independent subagents may review onboarding repairs under the invoking host’s authorized review workflow; that does not grant runtime policy authority.
- Run cross-analysis against current SSOT before any apply is considered safe.
- Treat commands, plugins, powers, and extensions as deployment wrappers, not capability types.
- Quality review artifacts are advisory evidence; they must not encode runtime routing policy.
- Do not make UAC the long-term owner of behavioral evaluation logic; route to `engos-optimization-auto-research` when bounded behavioral proof is needed.
- Do not ingest the Google Style Guide as permissive HTML. Use the reviewed local `instruction_clarity.v1` adapter and preserve the URL content-type rejection boundary.
- Do not let UAC author a candidate, define or view the sealed promotion set, judge the candidate, and waive its own failures.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- import a prompt, prompt pack, or capability into this repo
- classify whether this source should become a skill, agent, or manual review
- explain how this external source would land into SSOT and descriptors
- judge whether a candidate is ready to apply
- tell me whether this import needs stronger behavioral proof before landing

## Required Inputs
- one or more explicit sources
- desired mode such as `plan`, `judge`, or `apply`
- target system or install target when that materially affects the recommendation
- any benchmark or quality expectations when the caller wants a stricter gate

## Required Output
Return a concise structured result with these sections:
- Source
- Summary
- Uplift
- Routing
- UAC Classification
- Collection Recommendation
- Layered Manifest
- Cross-Analysis
- Quality Plan / Judge Reports
- Install Target
- Advisory Handoff Contract
- Recommended Surface
- Modernization Focus
- Next Actions

When `judge` escalates to behavioral proof, also include:
- Behavioral Confidence
- Escalation Reason
- Auto-Research Handoff
- Goal Contract and Capability Topology hashes when available
- Eval Impact Plan and hard token cap
- Structural Status (`structural_ready` is not `promote`)

## Companion Capability Matrix
| If the import uncovers this need | Route to | Required handoff |
| --- | --- | --- |
| The candidate needs deeper prompt hardening before it can pass the benchmark gate | `engos-meta-supercharge` | source excerpt, intended user outcome, weak sections, target capability style |
| The candidate is structurally close to passing but needs bounded behavioral proof against baseline or competing variants | `engos-optimization-auto-research` | baseline artifact, candidate artifact or variants, claimed job, bounded task set or examples, pass/fail threshold |
| The candidate is structurally sound but needs final decision synthesis across several landing options | `engos-reconciliation-converge` | candidate options, trade-offs, target install surfaces, decision criteria |
| The imported capability is fundamentally architectural or system-design oriented | `engos-design-architecture` | source summary, design scope, affected boundaries, unresolved design questions |
| The imported capability needs documentation-quality review before landing | `engos-quality-docs-review` | draft SSOT, descriptor summary, naming questions, drift or IA concerns |
| The imported capability requires stronger validation or test coverage in this repo | `engos-quality-testing-review` | changed scripts, validator paths, expected behaviors, missing coverage risks |
| The imported capability is ready to land but release, packaging, or CI readiness is the real question | `engos-quality-gitops-review` | applied diff, generated artifacts, validation output, release and deploy intent |

## Constraints
- No hidden execution. UAC coordinates exhaustive onboarding checks; it does not require a separate paid model API for every import. The invoking agent may prepare semantic repairs within authorized scope, and a separate subagent reviews them.
- No packaging claims without evidence.
- No deployment during `apply`.
- For local folders or GitHub repos, inventory the files first and justify whether they belong under one roof.

## Examples
### Example Request
> Import this prompt folder, tell me whether it belongs as one capability or several, and refuse apply if it misses the benchmark bar.

### Example Output Shape
- source inventory
- classification and fit assessment
- benchmark and quality status
- canonical landing recommendation
- next actions

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Source fidelity | The recommendation reflects the actual source set rather than guessed structure |
| Baseline fidelity | The candidate is judged against the repo-resident baseline source, not against metadata polish alone |
| Classification rigor | The result explains why the source is `skill`, `agent`, `both`, or `manual_review` |
| Landing safety | `apply` is blocked until benchmark and quality gates pass |
| Canonical output | The result names the SSOT, descriptor, and generated-surface consequences clearly |
| Boundary clarity | Deployment wrappers are not confused with capability types |
