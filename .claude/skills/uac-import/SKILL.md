---
name: "uac-import"
description: "UAC Import for capability intake, quality review, uplift, and canonical SSOT plus descriptor landing."
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

## Primary Objective
Classify the source safely, recommend the right surface area, and refuse landing until the candidate is structurally strong enough to become canonical SSOT plus descriptor state.

## Invocation Contract
Use this capability as the AI-facing intake contract.

Primary entrypoints:
- `bin/uac` for intake, audit, planning, judging, and apply
- `bin/capability-fabric` for surface build, validation, and deploy steps after landing

Canonical state:
- `ssot/<slug>.md` is the human-readable prompt source of truth
- `.meta/capabilities/<slug>.json` is the machine-readable descriptor source of truth
- generated surfaces under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/` are derived artifacts

Operational rule:
- `apply` may mutate canonical repo state after confirmation
- deploy is separate and must never be implied by `apply`
- when shell entrypoints are required to complete the workflow, say so explicitly instead of assuming the caller knows them

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
10. On `judge`, run the built-in quality loop and return judge packets plus pass/fail reports without landing repo state.
11. Search for benchmark sources only when the source is generic or fit confidence is weak.
12. On `apply`, refuse landing unless the quality loop reaches `ship`; if it does, write canonical repo state under `ssot/` and `.meta/capabilities/`, persist quality reviews, then rebuild and validate generated surfaces.
13. Keep deployment separate from apply.

## Tool Boundaries
- allowed: inventory sources, run deterministic uplift and classification, produce advisory manifests, and land canonical SSOT plus descriptor state when the quality gate passes
- forbidden: inventing capability strength that the source does not support, deploying to user homes during `apply`, or silently widening surface recommendations to satisfy packaging preferences
- escalation: if the work shifts from intake to architecture, docs quality, testing, or release readiness, route to the companion capability with a concrete handoff instead of stretching the import workflow

## Rules
- Prefer existing pipeline code over ad-hoc parsing.
- Keep results deterministic and roleplay-free.
- Fail closed for unsuitable URL content.
- For folders or repo trees, only group files that were actually inventoried.
- If the source is config-only, require manual review instead of pretending it is a prompt.
- If the source is already an agent definition, preserve its control-plane boundaries.
- Never make orchestration or delegation decisions. Publish advisory metadata only.
- Run cross-analysis against current SSOT before any apply is considered safe.
- Treat commands, plugins, powers, and extensions as deployment wrappers, not capability types.
- Quality review artifacts are advisory evidence; they must not encode runtime routing policy.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- import a prompt, prompt pack, or capability into this repo
- classify whether this source should become a skill, agent, or manual review
- explain how this external source would land into SSOT and descriptors
- judge whether a candidate is ready to apply

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

## Companion Capability Matrix
| If the import uncovers this need | Route to | Required handoff |
| --- | --- | --- |
| The candidate needs deeper prompt hardening before it can pass the benchmark gate | `supercharge` | source excerpt, intended user outcome, weak sections, target capability style |
| The candidate is structurally sound but needs final decision synthesis across several landing options | `converge` | candidate options, trade-offs, target install surfaces, decision criteria |
| The imported capability is fundamentally architectural or system-design oriented | `architecture` | source summary, design scope, affected boundaries, unresolved design questions |
| The imported capability needs documentation-quality review before landing | `docs-review-expert` | draft SSOT, descriptor summary, naming questions, drift or IA concerns |
| The imported capability requires stronger validation or test coverage in this repo | `testing` | changed scripts, validator paths, expected behaviors, missing coverage risks |
| The imported capability is ready to land but release, packaging, or CI readiness is the real question | `gitops-review` | applied diff, generated artifacts, validation output, release and deploy intent |

## Constraints
- No hidden execution.
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
| Classification rigor | The result explains why the source is `skill`, `agent`, `both`, or `manual_review` |
| Landing safety | `apply` is blocked until benchmark and quality gates pass |
| Canonical output | The result names the SSOT, descriptor, and generated-surface consequences clearly |
| Boundary clarity | Deployment wrappers are not confused with capability types |


Capability resource: `.claude/skills/uac-import/resources/capability.json`
