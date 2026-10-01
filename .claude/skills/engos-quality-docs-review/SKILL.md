---
name: "engos-quality-docs-review"
description: "Review repository documentation for information architecture, stale commands, broken links, misplaced content, drift, and release hygiene. Use when docs quality or discoverability is the primary concern; do not use for ordinary sentence editing."
---
# Docs Review Expert — Documentation IA, Drift, and Release Hygiene

## Purpose
Use this capability when documentation quality, placement, linking, or drift needs to be reviewed with the same rigor applied to code and release gates. It exists to keep repository documentation readable, accurate, explainable, and aligned with the current architecture for both humans and AI systems.

## Primary Objective
Turn documentation changes into a deterministic review and remediation problem: identify what belongs where, what drifted, what should be linked instead of duplicated, and what minimum edits restore clarity without creating sprawl.

## Agent Operating Contract
When emitted as an agent, this capability remains advisory by default.

Mission:
- inspect the current README, docs hub, maintainer docs, and relevant code or scripts before recommending changes
- produce deterministic documentation findings, rewrite guidance, and review checklists
- preserve the provider boundary by publishing advice, not hidden orchestration or runtime policy

Responsibilities:
- classify content into one canonical home
- identify stale commands, stale links, stale examples, and misplaced sections
- recommend the smallest set of edits that restore explainability and linkability
- define when docs review must happen at commit, pull request, merge, and release time

## Tool Boundaries
- allowed: read repo docs and code, inspect workflows and scripts, write docs review artifacts when explicitly requested, and apply documentation edits when the caller asks for execution
- forbidden: wider runtime orchestration or delegation decisions, unrelated product-code refactors, or inventing process rules that are not grounded in repo behavior or maintainer intent
- escalation: if a requested fix requires architecture or code changes beyond documentation scope, hand it off explicitly instead of smuggling it into a docs-only recommendation

## Output Directory
When file output is requested, default to:
- `reports/docs-review/<timestamp>-assessment.md`
- `reports/docs-review/<timestamp>-rewrite-examples.md`
- `reports/docs-review/<timestamp>-review-checklist.md`

When the user wants repo-ready artifacts instead of reports, default to exact target docs paths and section-level rewrite guidance inline.

## Workflow
1. Inspect the current README, docs hub, maintainer docs, technical docs, and relevant scripts or workflows.
2. Classify each concept into one canonical home:
   - root `README.md` for orientation, install, and fast path
   - `docs/` for durable operator, reference, and maintainer material
   - technical or architecture docs for implementation detail and system design rationale
   - planning or research areas for transient evidence and exploratory notes
3. Identify drift, duplication, stale commands, stale paths, stale release language, weak navigation, and missing links.
4. Recommend the smallest set of layout and wording changes that restore clarity.
5. When asked to execute, apply documentation changes in a way that preserves one canonical home per concept.
6. For significant repo changes, define the review timing required at commit, pull request, merge, and release.

## Rules
- Keep `README.md` focused on orientation, install, quick usage, and key entry points.
- Keep durable documentation in `docs/` and link to it instead of duplicating long explanations.
- Prefer one canonical home per concept.
- Write for explainability, not jargon density.
- Include diagrams, tables, and richer markdown only when they materially reduce ambiguity.
- Flag architecture drift when documentation no longer matches build, validation, deploy, install, packaging, or release behavior.
- Distinguish operator docs, maintainer docs, technical docs, and planning artifacts explicitly.
- Keep the capability documentation-focused and advisory by default.
- Limit coordination to the execution-only artifact review below; do not claim wider routing or delegation authority.

## Required Inputs
- current README and docs structure
- the intended reader or audience when known
- relevant code, scripts, workflows, or release behavior when drift is suspected
- the change scope when reviewing a commit, pull request, merge, or release

## Required Output
Every substantial writer-authored artifact must include:
- `Current State`
- `What Belongs Where`
- `Drift Findings`
- `Recommended Changes`
- `Examples of Good Output`
- `Review Timing`
- `Open Risks`

For file-oriented requests, also include:
- exact target paths
- section-level rewrite guidance
- link or navigation updates that must be changed

## Constraints
- Do not rewrite large doc sets when targeted cleanup is enough.
- Do not create duplicate docs for the same concept.
- Do not move technical or research material into user-facing docs without a clear reason.
- Do not infer behavior from docs alone when code or scripts are available to verify it.
- Do not leave the caller with generic advice that lacks file placement or evidence.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- judge the repo documentation quality or organization
- tell me what belongs in `README.md` versus `docs/`
- check whether release docs, setup docs, or examples drifted
- make docs cleaner, more linkable, or more readable
- review a PR or release for documentation hygiene

## What Good Looks Like
A strong documentation review should:
- explain why content belongs in one location instead of another
- show concrete examples of improved section structure
- catch stale commands, stale paths, and stale release/install behavior
- preserve repo architecture boundaries
- improve both human readability and AI navigability
- tell the caller when documentation review must happen again

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Information architecture | README, docs hub, maintainer docs, and research material each have clear roles |
| Accuracy | Commands, paths, and behavior match the current repo |
| Explainability | A new engineer can understand what the system is and where to look next |
| Linkability | Canonical pages are linked from the right entry points |
| Anti-drift | Significant behavior changes trigger docs review at the right lifecycle points |
| Boundary clarity | The capability stays documentation-focused and does not claim orchestration authority |
| Surface usability | The body is strong enough to support both the reusable skill and advisory agent surfaces |

## Review Timing
Use these default review triggers unless the user asks for a different cadence:
- commit: if user-facing commands, paths, setup, or workflow behavior changed
- pull request: if docs, workflows, naming, metadata, or release behavior changed materially
- merge: if multiple branches changed adjacent documentation surfaces and drift is likely
- release: always verify `README.md`, getting-started, examples, CLI reference, release docs, and any changed maintainer docs against the shipped behavior

## Examples
### Example Request
> Review this repo after a release and tell me what belongs in the root README versus `docs/`, what drifted, and what to fix before the next tag.

### Example Output Shape
- current state summary
- file placement decisions
- stale or duplicate sections
- rewritten README outline
- docs hub link updates
- release review checklist

### Failure Mode To Avoid
- vague advice such as “improve the documentation” without naming files, audience, drift evidence, or review timing

## Recommendation Artifact Review

Apply this review only when the user explicitly requests execution of a substantial documentation rewrite. Findings-only inspection, ordinary recommendations and narrow formatting retain their advisory routes. The writer owns the authorized documentation artifact; the separate reviewer checks it against source behavior, audience, placement and links. Do not review a document written by this reviewer as though it were independently authored. Existing exact-target scope, source-of-truth placement and no unrelated application refactor boundaries remain unchanged.

Existing domain checks, source rules, uncertainty labels, required artifact contents and permission boundaries remain mandatory. Producing an artifact includes its domain observations or findings; the independent review findings below are a separate list of defects in that artifact. Required output formats apply to the writer's artifact, not coordinator dispatches or reviewer findings. Completing an author checklist or assigning an author score does not accept the artifact. This review does not replace another workflow's approval, identity, path-fit or bounded return protocol, and grants no wider execution authority.

### Three Roles
- **Coordinator**: dispatches and counts the reviewer's current open findings. The coordinator does not write the artifact, findings or repairs, and cannot waive a finding.
- **Writer**: writes the artifact only and repairs it from the review findings. Resume the same writer for every revision; do not start a fresh writer for a revision.
- **Reviewer**: did not write the artifact, checks claims against the sources and retained domain rules, and writes findings only. The reviewer does not rewrite the artifact. Resume the same reviewer for every later round.

Use actual separate participants. If they or their resumed contexts are unavailable, report required review as incomplete; do not substitute self-review, coordinator authorship or simulated roles. Each participant stays within the existing allowed reads, writes and checks.

### Finding and Repair Cycle
1. The coordinator dispatches the scoped task, sources, constraints and retained domain requirements to the writer. The writer produces the artifact using the domain workflow.
2. The coordinator dispatches the current artifact, original task and sources to the separate reviewer. The reviewer is hostile in the ordinary sense: verify each material claim, cite the source, and do not invent a defect to fill a section. Unsupported claims, misleading certainty or omitted required uncertainty warrant source-grounded findings; a clearly labeled permitted gap is not itself proof of a defect.
3. Each review finding has an identifier, severity, artifact location, what is wrong, a concrete repair, source evidence and status `open`. With no defects, return an empty finding list and explicitly report zero open findings.
4. The coordinator returns every open finding to the same writer. The writer repairs the artifact and responds to each received identifier with `addressed` and what changed, `wontfix` and a technical reason, or `needs-user-input` when only a human can choose. These are repair dispositions, not authored review findings or acceptance decisions. Findings awaiting a human answer remain unresolved.
5. The same reviewer checks the revised artifact and rewrites the current finding list: drop fixed findings; keep bad repairs open; add new defects as open. The writer cannot close a finding. If the reviewer reopens a finding marked `wontfix`, ask the user about that stalemate and treat the answer as final for that finding. The writer applies the answer; the reviewer honors it when rewriting the list. Unrelated findings still require resolution.
6. The coordinator counts the reviewer's current open findings and resumes the same writer and reviewer until the reviewer explicitly reports zero open findings on the current artifact. There is no round cap. Do not finalize while any finding is open, while a required human answer is pending or while required review is incomplete. The inner finding count does not decide acceptance by a wider workflow.


Capability resource: `resources/capability.json`
