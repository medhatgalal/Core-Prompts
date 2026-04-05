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

### `autosearch`

Use when:

- a prompt or workflow is underperforming
- you need evidence, not just a better guess
- one-shot improvements have not been reliable enough

Why this skill first:

- start here when you need experiments and measured promotion logic, not a one-pass rewrite

Ask:

> Use `autosearch` to improve our code-review prompt so it catches more behavioral regressions without increasing review noise.

Expected output:

- goal contract
- evaluation criteria
- bounded experiment plan
- promotion guidance only after a verified winner exists

Also use `autosearch` when a candidate import or revised capability needs bounded behavioral proof before promotion.

Follow with:

> Now tell me the minimum experiment set that will separate the strongest two variants.

### `code-review`

Use when:

- you want to review a commit before merge
- the diff may be too broad
- you suspect AI-generated over-engineering or weak commit hygiene

Why this skill first:

- start here when the immediate question is commit quality and review findings, not CI health or release packaging

Ask:

> Use `code-review` to review the latest commit for scope creep, risky changes, and weak commit messaging.

Expected output:

- findings first
- scope and risk assessment
- commit-quality feedback
- open questions or residual risks

Follow with:

> Now tell me which findings are blocking merge versus follow-up cleanup.

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

> Use `mentor` to tell me the next reversible move on this branch.

Use this when you want scoped sequencing and risk-aware guidance.

### `docs-review-expert`

> Use `docs-review-expert` to review the docs set before release and call out drift.

Use this when you want documentation findings, rewrite targets, and release-facing doc checks.

### `gitops-review`

> Use `gitops-review` to judge whether we are ready to merge and release.

Use this when you want a merge or release gate with blockers and next actions.

### `autosearch`

> Use `autosearch` to improve this workflow and prove which version wins.

Use this when you want an experiment loop, not a one-shot rewrite.

### `supercharge`

> Use `supercharge` to harden this operating prompt before we ship it.

Use this when you want a stronger plan or prompt before execution.

### `converge`

> Use `converge` to synthesize these sources into one final recommendation.

Use this when several proposals overlap and you want one coherent answer.

### `architecture`

> Use `architecture` to review this system change for migration and rollback risk.

Use this when the decision will shape interfaces or system boundaries.

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
