# Examples

Use this page for full, concrete examples of how to use each currently shipped skill. The order matches the intended product order:

1. installed capabilities first
2. UAC second
3. repo tooling third

Each current skill example uses the same pattern:

- use when
- why this skill first
- ask
- expected output
- follow with

## Installed Skill Examples

### `analyze-context`

Use when:

- the task spans many files or sources
- you need to keep a durable analysis trail across a long session
- you want structured investigation before recommending changes

Why this skill first:

- start here when the main risk is losing context across files, not choosing between architectural options or writing tests yet

Ask:

> Use `analyze-context` to inspect this subsystem across the relevant files, keep a durable analysis trail, and tell me the smallest safe change plan.

Expected output:

- current state and file map
- accumulated findings
- unresolved questions
- a scoped change plan

Follow with:

> Now tell me the smallest reversible change worth making first.

### `architecture`

Use when:

- interfaces, boundaries, or migration risk matter
- a design choice has long-lived consequences
- rollback and compatibility need to be explicit

Why this skill first:

- start here when the core problem is design shape and migration safety, not prompt quality or release readiness

Ask:

> Use `architecture` to recommend the safest design for this capability layout, including migration and rollback considerations.

Expected output:

- options and tradeoffs
- boundary decisions
- migration and rollback guidance
- a final recommendation

Follow with:

> Now turn that recommendation into the smallest migration-safe implementation plan.

### `auto-research`

Use when:

- a prompt or workflow is underperforming
- you need evidence, not just a better guess
- one-shot improvements have not been reliable enough

Why this skill first:

- start here when you need experiments and measured promotion logic, not a one-pass rewrite

Ask:

> Use `auto-research` to improve our code-review prompt so it catches more behavioral regressions without increasing review noise.

Expected output:

- goal contract
- evaluation criteria
- bounded experiment plan
- promotion guidance only after a verified winner exists

Also use `auto-research` when a candidate import or revised capability needs bounded behavioral proof before promotion.

Follow with:

> Now tell me the minimum experiment set that will separate the strongest two variants.

### `supercharge /basis`

Use when:

- a software plan, research workflow, or knowledge-work process feels expensive or bloated
- you need the irreducible primitives before improving the current approach
- you want to identify waste drivers before deciding what to automate, delete, combine, or prove

Why this module first:

- start here when the right question is "what work is fundamentally necessary?" rather than "how do we polish the current version?"

Ask:

> Use `supercharge /basis` to audit this literature-review workflow for irreducible inputs, actual-to-minimum ratio, waste drivers, and redesign moves.

Expected output:

- basis map
- theoretical minimum
- actual-to-minimum ratio
- waste drivers
- redesign moves
- proof needed

Follow with:

> Now route only the unproven redesign claims to `auto-research` for measured comparison.

### `supercharge /adversarial /debate`

Use when:

- a plan, prompt, architecture decision, review conclusion, or thesis needs explicit structured dissent
- you want the strongest case for and against a decision before choosing
- normal critique is too one-sided, but a full deep debate would be more ceremony than the decision needs

Why this module first:

- use this when the next useful move is not a rewrite, but a Bull/Bear/Decider pressure test with risks, mitigants, flip conditions, and uncertainty

Ask:

> Use `supercharge /adversarial /debate` to decide whether this rollout plan is worth shipping now. Include the strongest Bull case, strongest Bear case, Decider verdict, confidence, risks, mitigants, and flip conditions.

Expected output:

- Bull case
- Bear case
- Decider verdict
- confidence score
- risks and mitigants
- flip conditions
- uncertainty or human-judgment areas

Follow with:

> Now turn the Decider verdict into a `supercharge /contract` acceptance checklist.

### `supercharge /adversarial /debate /deep`

Use when:

- the decision is high-stakes, high-uncertainty, or likely to have hidden asymmetric downside
- the first Bear case deserves a Bull counter and final Bear challenge before synthesis
- the output may feed a decision record, release gate, or follow-up `auto-research` proof loop

Why this module first:

- start here when you need multi-round structured dissent, not just a compact critique

Ask:

> Use `supercharge /adversarial /debate /deep` to run a deep Bull/Bear/Decider debate on this architecture change. Include missing evidence, decision-risk table, mitigation plan, flip conditions, and recommended next validation.

Expected output:

- debate context
- Bull opening
- Bear rebuttal
- Bull counter
- Bear final challenge
- Decider verdict
- decision-risk table
- mitigation plan
- missing evidence
- recommended next validation

Follow with:

> Now route any unproven behavioral claims to `auto-research` with a bounded scorecard.

### `code-review`

Use when:

- you want to review staged changes before committing
- you want to review a commit before push or merge
- the diff may be too broad
- you suspect AI-generated over-engineering or weak commit hygiene
- you need findings and readiness guidance, not file edits

Why this skill first:

- start here when the immediate question is review judgment: scope, correctness risk, message quality, and merge readiness

Ask:

> Use `code-review` to review my staged changes before I commit.

Expected output:

- findings first
- scope and risk assessment
- commit-message or change-summary feedback
- open questions or residual risks
- readiness decision

Follow with:

> Now tell me which findings are blocking merge versus follow-up cleanup.

### `codebase-health-audit`

Use when:

- you need a read-only structural audit of a brownfield repository
- LOC hotspots, god objects, coupling, or likely dead code matter
- you want to verify prior audit claims against live files
- you need drift analysis between audit snapshots

Why this skill first:

- start here when the job is structural codebase health, not feature scope completeness, commit review, or architecture redesign
- overlap with `architecture`, `feature-status`, and `code-review` is expected; use this skill when metric-backed repository structure is the primary evidence source

Ask:

> Use `codebase-health-audit` to audit this repo for LOC hotspots, god objects, coupling, likely dead code, and drift from this prior audit block.

Expected output:

- YAML-frontmatter audit summary
- verified structural findings with severity and metrics
- claim verification when prior state is provided
- drift trajectory and rationale
- slice-ready remediation recommendations
- prior-state block for the next audit run

Follow with:

> Now route only the high-severity structural findings to `architecture` for remediation design, without editing files yet.

### `address-code-review`

Use when:

- a PR or MR has open reviewer comments
- you want targeted fixes rather than broad cleanup
- scope discipline matters after review feedback
- the user has selected which comments should be addressed

Why this skill first:

- start here when the immediate task is applying selected reviewer-requested fixes, not producing a new review
- do not start here for pre-commit review; use `code-review` first

Ask:

> Use `address-code-review` to inspect the open review comments on this MR and address only the selected fixes.

Expected output:

- comments found
- selected comments to address
- changes applied per comment
- commit guidance
- follow-up recommendation to run `code-review`

Follow with:

> Now use `code-review` on the fix commit before I push it back for reviewer verification.

### `converge`

Use when:

- several proposals overlap or conflict
- you need one final recommendation
- weak synthesis would hide the real tradeoffs

Why this skill first:

- start here when you already have multiple options and need one defended decision, not open-ended brainstorming

Ask:

> Use `converge` to compare these rollout plans and recommend one final approach.

Expected output:

- overlap map
- decision analysis
- final converged proposal
- muted or rejected ideas

Follow with:

> Now rewrite the winning proposal as the one plan we should actually execute.

### `demo-recorder`

Use when:

- you need a polished video recording of a feature for a presentation or stakeholder review
- you want to automate repetitive demo walkthroughs instead of screen-recording manually
- you need a reproducible demo script that can be re-run after UI changes

Why this skill first:

- start here when the goal is a watchable recording, not testing or CI integration

Ask:

> Use `demo-recorder` to create a Playwright demo of the agent feedback feature on our Swagger UI at https://agents.dev-01.example.com. Show creating an agent, running it, then submitting feedback. Use TypeScript and record with Playwright video.

Expected output:

- demo plan (4-5 ordered steps with rationale)
- complete TypeScript Playwright script with `recordVideo` enabled, `slowMo` for pacing, and JWT auth via env var
- run command: `npx playwright test demo-script.spec.ts`
- output location: `./recordings/*.webm`

Follow with:

> The pauses between steps are too short — increase them to 3 seconds and add a scroll-into-view before each major action.

### `dynamic-html-presentations`

Use when:

- you need a polished slide deck whose editable source should remain portable HTML
- browser navigation, fullscreen, presenter notes, or deep links matter
- the same visual output must also be delivered as PNG images or PPTX
- deterministic 16:9 export and artifact verification matter more than native PPTX editability

Why this skill first:

- start here when the job is presentation narrative, visual composition, and multi-format delivery; use `demo-recorder` instead when the primary artifact is a watchable product video

Ask:

> Use `dynamic-html-presentations` to turn this quarterly product review into a polished portable HTML deck package with speaker notes. Use my approved local photos and screenshots, prepare deck-ready copies under `images/` with descriptive filenames and intentional crops, and do not fetch remote imagery. Deliver 1920×1080 PNGs and an image-faithful PPTX too, and label all sample metrics as illustrative.

Expected output:

- a slide-level narrative with one principal claim per slide
- a portable 16:9 HTML deck package with keyboard navigation, hash links, fullscreen, notes, help, and export mode
- approved image assets under `images/` with relative paths, descriptive names, preserved aspect ratios, eager loading, intentional alternative text, and validated crops
- one verified exact-size PNG per slide from a single long-lived renderer
- a verified widescreen PPTX with one full-slide image per page
- clear disclosure that PPTX content is flattened rather than independently editable
- exact artifact paths, checks run, and unresolved evidence assumptions

Follow with:

> Validate every slide at 1920×1080, confirm there is exactly one active slide, and report any clipping, control collision, broken or distorted image, absolute image path, unapproved network dependency, or unlabeled illustrative value before final export.

### `docs-review-expert`

Use when:

- docs feel bloated, contradictory, or hard to navigate
- you suspect drift between README, examples, and reference docs
- release-facing commands or examples changed

Why this skill first:

- start here when the problem is information architecture, explanation quality, or docs drift, not branch gating or code correctness

Ask:

> Use `docs-review-expert` to review our onboarding docs, identify drift, tell me what belongs in `README.md` versus `docs/`, and recommend the smallest rewrite that restores clarity.

Expected output:

- current state summary
- what belongs where
- drift findings
- recommended changes
- review timing

Follow with:

> Now give me the exact README and docs outline you would ship.

### `eng-report`

Use when:

- you need a progress report from git history
- velocity, release timeline, code churn, or architecture movement should be visible
- the report must be generated from deterministic repo data rather than Jira or sprint estimates

Why this skill first:

- start here when the job is observing git activity and rendering a report, not reviewing code quality or changing repository state

Ask:

> Use `eng-report` to generate an HTML progress report for this repo since 2026-06-01 and open it.

Expected output:

- deterministic git metrics for the selected window
- standalone HTML report path
- optional `_index.html` for fleet reports
- narrative tied to files, counts, releases, or modules visible in the data
- no invented Jira, story-point, or PR-review metrics

Follow with:

> Now rerun it with `--json` first so I can inspect the metrics before writing the narrative.

### `gitops-review`

Use when:

- you think a branch is ready for PR or release
- docs, CI, packaging, or release behavior changed
- you need a real gate instead of a generic opinion

Why this skill first:

- start here when you need a merge or release decision with blockers and evidence, not a content rewrite

Ask:

> Use `gitops-review` to judge whether this branch is ready for PR and release. Check docs drift, validation evidence, and any remaining blockers.

Expected output:

- gate type
- findings
- required companion reviews
- recommended commands or actions
- release or merge readiness

Follow with:

> Now separate the blocking issues from the nice-to-have follow-ups.

### `ic-assistant`

Use when:

- you are acting as Incident Commander
- the incident needs phase-aware checklist guidance
- status updates, escalation thresholds, or postmortem deadlines may be missed
- you need generic guidance by default, or an internal runbook only when explicitly requested

Why this skill first:

- start here when the risk is process drift during an active incident, not root-cause analysis or technical remediation

Ask:

> Use `ic-assistant` to track this incident, identify the current phase, and tell me the next required action.

Expected output:

- mode and current incident phase
- next required action
- time since last status update
- overdue items or escalation flags

Follow with:

> Now generate the handoff summary for the next Incident Commander.

### `mentor`

Use when:

- you need the next best move, not a big plan dump
- the work has risk or sequencing uncertainty
- you want a senior perspective on scope control

Why this skill first:

- start here when the main need is sequencing and scope control, not deep analysis or formal gating

Ask:

> Use `mentor` to tell me the next reversible move on this branch.

Expected output:

- the next move
- why it is the next move
- what to avoid mixing in

Follow with:

> Now tell me the next move after that one if the first step succeeds cleanly.

Tmux follow-up:

> Use `mentor` to look at the left pane and tell me what happened before you recommend the next reversible move.

Expected output:

- a short read of the terminal context from tmux
- the likely failure or state transition that matters
- the next reversible move after reading that context

### `pitch`

Use when:

- you are shaping a Shape Up pitch
- you need to score pitch quality before betting
- appetite, risks, or boundaries are unclear

Why this skill first:

- start here when the artifact under review is a pitch, not a generic plan or architecture proposal

Ask:

> Use `pitch` to review this Shape Up pitch for appetite, risks, and betting readiness.

Expected output:

- pitch score
- strengths and risks
- missing decisions
- concrete rewrite guidance

Follow with:

> Now rewrite the weakest section so it is ready for betting.

### `pulse`

Use when:

- Gmail and Google Chat need triage
- you want priorities without taking action yet
- you need a low-noise summary of what needs attention

Why this skill first:

- start here when the job is communication triage, not drafting or sending replies

Ask:

> Use `pulse` to triage what needs my attention across Gmail and Google Chat, then propose next actions without sending anything.

Expected output:

- priority buckets
- source summaries
- proposed next actions
- explicit action/approval boundary

Follow with:

> Now draft the highest-priority reply, but do not send it.

### `resolve-conflict`

Use when:

- two branches or edits conflict
- you need additive resolution rather than a sloppy merge
- you want to separate orthogonal changes from real contradictions

Why this skill first:

- start here when the hard part is reconciling competing edits, not deciding whether the branch is release-ready

Ask:

> Use `resolve-conflict` to compare these conflicting branch edits and tell me what should survive, what can combine cleanly, and what needs an explicit choice.

Expected output:

- conflict map
- additive merge opportunities
- explicit contradictions
- recommended resolution

Follow with:

> Now draft the merged shape and call out the few lines that still require a human decision.

### `supercharge`

Use when:

- a prompt, brief, or plan is underspecified
- failure modes are not obvious yet
- the team needs a stronger execution brief before acting

Why this skill first:

- start here when the problem is weak framing and execution quality, not experimental evaluation

Ask:

> Use `supercharge` to turn this rough feature idea into an execution-ready plan with tradeoffs and failure modes.

Expected output:

- sharper framing
- decomposed plan
- acceptance criteria
- stronger execution-ready language

Follow with:

> Now condense that into the exact prompt or execution brief I should use next.

If the decision itself is contentious, use:

> Use `supercharge /debate /deep` to stress-test this feature direction before we turn it into an execution brief.

### `testing`

Use when:

- you do not want a long unprioritized test list
- the change has edge-case risk
- you need a coverage-first recommendation

Why this skill first:

- start here when the next decision is test scope and edge-case priority, not architecture or prompt design

Ask:

> Use `testing` to identify the highest-value tests and edge cases for this change.

Expected output:

- top-priority tests
- edge cases
- gaps in current coverage
- suggested order of attack

Follow with:

> Now turn the top three items into concrete test cases with names and expected behavior.

### `threader`

Use when:

- you want a reusable transcript or handoff
- another engineer or model needs the current context
- a long conversation should become an artifact

Why this skill first:

- start here when the value is preserving context for handoff, not generating new recommendations

Ask:

> Use `threader` to turn this chat into a reusable handoff for another engineer or model.

Expected output:

- a durable transcript or handoff artifact
- the important context preserved
- clear next-step continuity

Follow with:

> Now trim that handoff so another engineer can start in under five minutes.

### `uac-import`

Use when:

- you are bringing new prompt-like source into canonical repo state
- you need intake, classification, and uplift guidance
- you want to know how a candidate should land before `apply`

Why this skill first:

- start here when the question is how new source should land into SSOT, not how to use what already ships

Ask:

> Use `uac-import` to inspect this external prompt family and tell me how it should land into SSOT before apply.

Expected output:

- capability classification
- landing shape
- baseline and benchmark implications
- next UAC steps

Follow with:

> Now tell me whether the candidate should stay one capability or split into two before judge.

### `weekly-intel`

Use when:

- you need a weekly summary from multiple sources
- an executive and technical view should be produced together
- fact-checking matters

Why this skill first:

- start here when the job is multi-source reporting with auditability, not a one-off summary from one local artifact

Ask:

> Use `weekly-intel` to produce a weekly status report from these sources.

Expected output:

- executive summary
- technical appendix
- fact-check or source audit

Follow with:

> Now shorten that into a one-screen executive update for leadership.

## Advisory Agent Examples

These examples are for the current advisory agents emitted by the repo.

### `mentor`

> Use `mentor` to tell me the next reversible move on this branch, or look at the left pane and review this error if I am in tmux.

Use this when you want scoped sequencing, risk-aware guidance, or direct tmux-aware terminal context recovery without copy-pasting logs.

### `docs-review-expert`

> Use `docs-review-expert` to review the docs set before release and call out drift.

Use this when you want documentation findings, rewrite targets, and release-facing doc checks.

### `gitops-review`

> Use `gitops-review` to judge whether we are ready to merge and release.

Use this when you want a merge or release gate with blockers and next actions.

### `auto-research`

> Use `auto-research` to improve this workflow and prove which version wins.

Use this when you want an experiment loop, not a one-shot rewrite.

### `supercharge`

> Use `supercharge /basis` to harden this operating prompt by finding the irreducible work, waste, and proof gaps before we ship it.

Use this when you want a stronger plan or prompt before execution.

> Use `supercharge /adversarial /debate /deep` to run a Bull/Bear/Decider debate on this operating decision before we ship it.

Use this when you want structured dissent before committing to a plan.

### `converge`

> Use `converge` to synthesize these sources into one final recommendation.

Use this when several proposals overlap and you want one coherent answer.

### `architecture`

> Use `architecture` to review this system change for migration and rollback risk.

Use this when the decision will shape interfaces or system boundaries.

### `ic-assistant`

> Use `ic-assistant` to track this incident and keep me on the required checklist.

Use this when you need phase-aware Incident Commander process guidance without taking incident decisions for the IC. It uses generic guidance by default and consults the internal runbook resource only when explicitly requested.

### `pitch`

> Use `pitch` to review this Shape Up pitch before betting.

Use this when you want pitch scoring, risks, and rewrite guidance.

### `pulse`

> Use `pulse` to triage Gmail and Google Chat and propose next actions without sending anything.

Use this when you want communication prioritization with explicit approval boundaries.

### `weekly-intel`

> Use `weekly-intel` to produce a weekly status report from these sources.

Use this when you want a multi-source weekly report with fact-checking.

## UAC Examples

Use these only when you are importing or uplifting capabilities into canonical repo state.

### Plan A Landing

```bash
bin/uac plan /absolute/path/to/family-folder
```

Expected output:

- proposed family clustering
- SSOT and descriptor landing plan
- overlap or conflict analysis
- benchmark hints

### Judge Before Apply

```bash
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
```

Expected output:

- quality status
- judge reports and evidence
- blockers or ship decision
- no canonical repo mutation

### Apply A Ship-Ready Capability

```bash
bin/uac apply /absolute/path/to/family-folder --yes
```

Expected output:

- new or updated `ssot/<slug>.md`
- updated `.meta/capabilities/<slug>.json`
- preserved baseline in `sources/ssot-baselines/<slug>/baseline.md`
- automatic `build` and `validate --strict`

## Transcript-Style Examples

### Transcript: Use A Skill To Decide What To Do Next

```text
User:
Use `mentor` to tell me the next reversible move on this branch.

Good response:
- Next move: run `bin/capability-fabric validate --strict`
- Why: the docs changed and the branch now needs current validation evidence before PR
- Avoid mixing in: do not combine unrelated cleanup or release packaging changes yet
```

### Transcript: Use A Skill To Review Documentation

```text
User:
Use `docs-review-expert` to review our onboarding docs, identify drift, tell me what belongs in README.md versus docs/, and recommend the smallest rewrite that restores clarity.

Good response:
- Current State: README and examples lead with usage, but UAC guidance is still denser than it needs to be
- What Belongs Where: README for orientation and fast examples, docs/UAC-USAGE.md for intake flow, docs/CLI-REFERENCE.md for exact commands
- Drift Findings: one command example no longer matches wrapper help
- Recommended Changes: tighten README wording, fix command example, keep generated views secondary
- Review Timing: re-check before release because onboarding changed materially
```

### Transcript: Use UAC To Inspect A Candidate

```text
User:
Use `uac-import` to inspect this external prompt family and tell me how it should land into SSOT before apply.

Good response:
- Source summary: 5 files, strongest theme is architecture review
- Proposed landing: `ssot/architecture.md`, `.meta/capabilities/architecture.json`
- Capability type: likely `both`
- Concerns: one file is mostly release-process guidance and may need to split out
- Next step: run `bin/uac judge ... --quality-profile architecture`
```

### Transcript: Use A Skill, Then Verify The Repo

```text
User:
Use `testing` to identify the highest-value tests and edge cases for this change, then tell me the smallest local verification loop I should run before PR.

Good response:
- Top-priority tests: validation contract drift, docs command examples, generated-surface path checks
- Edge cases: stale generated docs, wrong runtime assumptions, broken deploy examples
- Recommended local loop:
  - bin/capability-fabric validate --strict
  - python3 scripts/smoke-clis.py
- Why this loop: it matches the actual release gate without pulling in packaging or tagging too early
```

### Transcript: Use A Skill To Choose Between Nearby Skills

```text
User:
I am not sure whether to use `docs-review-expert`, `gitops-review`, or `mentor` on this branch. Pick the right one and explain why.

Good response:
- Start with: `docs-review-expert`
- Why first: the branch risk is doc drift and weak onboarding, not merge gating yet
- Use `gitops-review` next when the rewrites are complete and you need a PR or release gate
- Use `mentor` only if the remaining issue is sequencing or scope control
```

## Repo Tooling Examples

### Rebuild And Verify Current Repo State

```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

Expected output:

- regenerated surfaces and generated inspection views
- strict validation evidence
- smoke visibility checks where local CLIs are installed

### Preview Deployment Without Mutating A Target Home

```bash
bin/capability-fabric deploy --cli all --dry-run
```

Expected output:

- explicit copy plan
- no target mutation
