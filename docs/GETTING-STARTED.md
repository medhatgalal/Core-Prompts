# Getting Started

Use this page in the same order Core-Prompts is meant to be used:

1. installed capabilities first
2. UAC second
3. broader repo tooling third

Core-authored skills use the `engos-<category>-<skill-name>` namespace. Use the full prefixed name in autocomplete or direct invocation; the category keeps related Core-Prompts skills together across supported CLI and app surfaces. The pinned upstream `loopy` capability retains its familiar name as an explicit exception.

Conversational `Supercharge /full` and stacked forms such as `supercharge /simple /invert /contract <task>` remain supported by `engos-meta-supercharge`. Use the full namespaced name for native skill selection; no separate short-name package or native menu alias is emitted. Ask `supercharge help` or `supercharge /help examples` for the bundled terminal guide; help does not execute examples. `/full` includes up to ten actual independently graded candidate trials unless you explicitly say `skip grade`; an independently checked target and documented plateau can finish it early.

For engineering activity, start with `engos-audit-engineering-progress help`. Supply a repository configuration and reporting window when ready; JSON collection leaves HTML reports untouched, then a separate rendering pass uses your narrative. See the [worked example](EXAMPLES.md#engos-audit-engineering-progress).

## Step 1: Use Installed Capabilities

For a product/engineering shaping workshop, use `engos-design-shaping` with the
documents you already have. It should summarize the problem and ask a few useful
questions, not require a complete form or choose an architecture immediately.
No repository access is required merely to start: choose AI-led, human-led or
hybrid research. [Start or resume guided Shape Up](engos-design-shaping.md).
Check that page's current pilot status before assuming every host or publishing
adapter has been validated.

During a shaping run, ask “Show the current stage, blocker, owner and next step.”
The assistant uses the existing run record, marks simulated/unknown evidence and
keeps the latest accepted revision separate from drafts. A framing-only request
can finish without treating later shaping/publication as failed work.

Start in your CLI with the job you want done:

> Supercharge this plan: replace our onboarding checklist with the fewest steps that still verify access, setup, and a successful first task.

Expect a stronger plan with tradeoffs, failure modes, and acceptance criteria. The assistant must arrange any required independent review; unavailable workers are a reported limitation, not a reason to call self-review independent. If the skill is not discovered, explicitly select `engos-meta-supercharge` and repeat the request. Ordinary-language discovery depends on the host and installed setup.

The shipped setup is skills-only. [Skills, agents, and prompts](FAQ.md#what-is-the-difference-between-a-skill-an-agent-and-a-prompt) explains optional execution configurations. Batman remains explicitly invoked.

If Core-Prompts is already installed in Codex, Gemini, Claude, Kiro, or Grok, begin with one of these asks:

| Capability | Example ask | What good output looks like |
| --- | --- | --- |
| `engos-memory-context-continuity` | "Use `engos-memory-context-continuity` to inspect this subsystem across several files and keep its context, todo, and insights files current until every TODO is complete." | one three-file task set under `~/.analyze-context/<project>/<task-id>/`; milestone/size-triggered consolidation keeps current state first and reports before/after counts; hooks never delete state |
| `engos-quality-docs-review` | "Use `engos-quality-docs-review` to review our docs IA and recommend the smallest rewrite that restores clarity." | placement decisions, drift findings, and rewrite guidance |
| `engos-quality-gitops-review` | "Use `engos-quality-gitops-review` to tell me whether this branch is ready for PR and what blockers remain." | gate type, blockers, companion reviews, and next steps |
| `engos-audit-code-health` | "Use `engos-audit-code-health` to audit this repo for LOC hotspots, god objects, coupling, likely dead code, and drift from this prior audit block." | metric-backed structural findings, drift analysis, and slice-ready remediation |
| `engos-quality-code-review` | "Use `engos-quality-code-review` to review my staged changes, including resource cleanup, concurrency, operational readiness, and API/schema compatibility." | evidence-based findings, scope assessment, lifecycle and contract risks, message guidance, and merge readiness |
| `engos-delivery-address-code-review` | "Use `engos-delivery-address-code-review` to inspect the open MR comments and apply only the selected reviewer-requested fixes." | comments found, targeted fixes, changed files, commit guidance, and follow-up review |
| `engos-delivery-diagram-contract-artifacts` | "Use `engos-delivery-diagram-contract-artifacts` to turn this shaped pitch into Mermaid component/sequence/data-flow diagrams plus contract and security-owner tables." | source-backed artifact manifest, diagrams, tables, evidence ledger, no-gos, and completeness judgment |
| `engos-delivery-artifact-embed` | "Use `engos-delivery-artifact-embed` to place this unchanged shaping bundle on the HTML site and Google Doc, preserving source identity." | one placement receipt per surface, visual/readback evidence, or an explicit human step/blocker |
| `engos-audit-engineering-progress` | "Use `engos-audit-engineering-progress` to generate an HTML progress report for this repo since 2026-06-01." | git-derived metrics, report path, and narrative tied to deterministic data |
| `engos-audit-opex-incident-review` | "Use `engos-audit-opex-incident-review` to build today's Daily OpEx Digest and compare it with yesterday's snapshot." | decisions, owner obligations, reconciled incident and DPA metrics, progress/correction separation, stalled cohorts, evidence caveats, and the local report path |
| `engos-operations-ic-assistant` | "Use `engos-operations-ic-assistant` to track this active incident and tell me the current phase, overdue items, and next required action." | mode, phase, next action, status-update timer, and escalation flags |
| `engos-design-plan-to-goal` | "Use `engos-design-plan-to-goal` to inspect this rollout plan and repository, then compile a compact goal plus a sealed spec/verifier packet without starting execution." | research receipt, bounded mechanism-proof anchor, empty population/exclusion intersection, per-criterion flip evidence, packet status, and host-correct next action |
| `engos-meta-supercharge` | "Use `engos-meta-supercharge /adversarial /debate /deep` to stress-test this release decision with Bull/Bear/Decider analysis, risks, mitigants, and flip conditions." | stronger framing, constraints, sequencing, first-principles accounting, and adversarial debate when requested |
| `engos-optimization-auto-research` | "Use `engos-optimization-auto-research` to improve our review prompt so it catches more regressions without increasing noise." | experiment design, evaluation, and a validated winner |
| `engos-orchestration-batman` | "Batman: verify this request, publish the Host-Fit Plan, then implement this shipped-defect correction through independent-subagent TDD, blocking milestone reviews, verification, docs, PR, authorized merge, release, install, and cleanup." | instruction-integrity and host-fit decisions, independent subagent evidence, provenance-qualified red and mutation checks, progress reports, milestone decisions, and state-specific landing receipts |
| `engos-browser-demo-recorder` | "Use `engos-browser-demo-recorder` to create a Playwright demo of the new dashboard feature with video recording." | demo plan, complete Playwright script, run command, and output path |
| `engos-content-dynamic-html-presentations` | "Use `engos-content-dynamic-html-presentations` to create a standalone HTML deck and ask me whether I want PNG, PPTX, or all formats." | narrative-first deck, polished 16:9 visuals, interaction behavior, and validated requested exports |
| `engos-quality-testing-review` | "Use `engos-quality-testing-review` to identify the edge cases and tests this change needs." | prioritized tests and missing edge cases |

For complete OpEx meeting preparation, request `briefing` with incident keys; it defaults to `BRIEFING.html` and `BRIEFING.md` in your chosen directory and preserves the daily board. For an individual deep review, request `deep-dive` with the incident keys and choose Markdown or both formats. The renderer includes supplied drill-down evidence and labels missing evidence explicitly.

For a complete Plan to Goal walkthrough, including a two-criterion verifier and the lint/seal/check commands, see [Plan to Goal Design](EXAMPLES.md#engos-design-plan-to-goal).

No named-agent configurations ship. Use the skill examples above directly; independent workers receive the same skill and required resources. Future named adapters require explicit user approval. See the [agent FAQ](FAQ.md#what-is-the-difference-between-a-skill-an-agent-and-a-prompt).

### How Batman starts and resolves companions

Batman starts with instruction integrity. It verifies that the request has a coherent outcome, observable success criteria, boundaries, and authority. A terse or ambiguous request is not expanded silently; Batman states the missing contract and pauses when proceeding would materially change the result.

After preflight, Batman inventories the live repository and host and publishes a Host-Fit Plan. The plan names the implementation language, available build/test/lint/type/smoke/CI tools, usable independent subagents and Core-Prompts companions, safe parallel work, and cost/quality/speed trade-offs. It adapts execution to what exists. It cannot waive a milestone gate, collapse controller/implementer/reviewer separation, invent a budget, or grant write, merge, deploy, release, install, or cleanup authority.

Companion names identify capabilities, not guaranteed agent registrations. For each required companion, Batman uses a usable registered agent first, otherwise dispatches a fresh default independent subagent that applies the installed skill with the same name, and stops the dependent stage or gate when neither surface is available. Context researcher, challenger, designer, implementer, reviewer, attacker, adversarial reviewer, and fixer are role briefs rather than agent names.

### How Batman reports proof and landing state

The controller owns the written plan, evidence ledger, progress, and four blocking milestone gates. Independent implementers author code and failing tests. Fresh reviewers and attackers provide backpressure and cannot fix or approve their own work.

Batman accepts red evidence only when the assigned implementer wrote or took explicit ownership of the test in the current task and observed it fail against the unfixed behavior for the expected reason. Controller-authored tests, prior-session tests, and tests first seen green are context, not red proof. Mutation evidence must reverse or remove the owned fix, observe the expected failure, restore it, and rerun green.

Keep these outcomes separate:

- local targeted checks and the full offline suite prove only the tested local revision
- hosted CI proves only the reported forge revision and completed required checks
- authorized live verification proves only the named environment, time, and claim it exercised
- merge, tag, package release, deployment, and installation are distinct completed states with distinct receipts
- UAC `structural_ready` permits structural landing; it does not mean behavioral promotion
- cleanup is complete only after durable evidence is preserved and authorized run-scoped branches, worktrees, and scratch are removed; unknown or failed cleanup is reported, never rewritten as success

## Step 2: Use UAC When You Are Landing New Capability Source

Use UAC, the capability intake and uplift workflow, only when you are bringing in a new prompt-like source or intentionally changing canonical capability state.

Use UAC when you need to:

- plan how an external capability family would land in `ssot/` and `.meta/capabilities/`
- benchmark a candidate before it mutates the repo
- apply a ship-ready capability into canonical state

Typical UAC progression:

```bash
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
```

Practical rule:

- use `plan` for landing shape
- use `judge` for the quality decision
- use `apply` only when you intend to change canonical repo state

If `judge` says the landing is structurally close but still needs bounded behavioral proof, use `engos-optimization-auto-research` for that proof step. During the advisory rollout, a structurally ready apply may land as `behavioral_pending`, but it cannot advance the behavioral baseline or claim promotion.

To move an already-canonical candidate from `behavioral_pending` to `promote`, use an independently signed public evidence bundle. The approved evaluator trust policy must already be on protected main and on the evaluated baseline's ancestry; a candidate cannot authorize its own evaluator. See [Capability evaluation](CAPABILITY-EVALUATION.md#from-behavioral_pending-to-promote) for the status model and [UAC usage](UAC-USAGE.md#example-finalize-an-existing-candidate-after-behavioral-proof) for the exact command.

For the full flow, go to [UAC usage](UAC-USAGE.md).

## Step 3: Use Repo Tooling To Verify Or Operate The Repo

Compile the skill's goal and topology before claiming that an instruction change is behavior-neutral:

```bash
bin/capability-eval compile --skill engos-meta-supercharge
bin/capability-eval calibrate --static-only
bin/capability-eval probe
```

These commands make zero model calls. `structural_ready` means deterministic gates passed; only an independent, current `PromotionVerdict.v2` can mean `promote`. Version 1 verdicts remain readable but cannot authorize promotion.

Live comparison is available only through explicit run plans and operator-authorized model calls. Behavioral promotion additionally requires the separately operated protected evaluator, conforming adapters, protected credentials and runner identities, external sealed data, qualified judges, purpose-separated signatures, and reproduction evidence. The bundled Codex adapter is fail-closed until a separately approved credential broker or equivalent isolation boundary exists. Missing prerequisites return `inconclusive`; the checked-in template cannot manufacture a promotion. `engos-meta-instruction-editor` remains experimental, and Google-style rewriting remains off by default in UAC.

Once you are working at the repo layer, this is the shortest useful verification loop:

```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

What this proves:

- `build` regenerates CLI skills, agents, bundled resources, and generated inspection views
- `validate --strict` checks generated surfaces, manifests, and contract integrity
- `smoke-clis.py` probes local vendor CLIs and expected surface visibility where supported

## Install Or Repair Your CLI Setup

Use a trusted current release or verified checkout. The same command handles an
existing Kiro installation without an updater or receipts:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --cli kiro --repair --dry-run > /tmp/core-prompts-install-plan.json
```

Review the plan's selected packages, file actions, preserved packages, and blockers.
Then apply that exact plan:

```bash
bash scripts/install-local.sh --target "$HOME" --allow-nonlocal-target \
  --apply-plan /tmp/core-prompts-install-plan.json
```

For a fresh target, omit `--repair`; the current package contains skills only.
Existing skills and agents are recognized independently from trusted historical
identities. Repair plans retirement of recognized owned agent variants and keeps
or installs their same-job skill on the selected provider. Customized or unowned
packages remain preserved. `--with-agents` selects only emitted agents (currently
none) and cannot authorize source creation.

The resulting `.core-prompts-state/installation.json` saves concrete provider,
surface, and slug selection. Routine updates reconcile owned package resources
and keep that selection. Unknown, customized, symlinked, and unrecognized partial
packages are preserved and reported; exit `2` means migration still needs attention.
Schema-1 receipt conversion may restore missing receipted files; see
[recognition and preservation](INSTALL-PROFILES.md#historical-recognition-and-preservation)
when reviewing the plan.

For a narrow repair, use `--surface-only` with a selected slug to skip updater and
launcher refresh:

```bash
bash scripts/deploy-surfaces.sh --target "$HOME" --allow-nonlocal-target \
  --cli kiro --slug engos-quality-code-review --surface-only --dry-run \
  > /tmp/core-prompts-surface-plan.json
```

This uses the same reviewed-plan apply step. It is ownership-aware; a familiar
filename alone does not authorize removing historical residues or custom files.

## Installed Release Watch

Installation also supplies the standalone updater when absent:

```bash
~/update_core_prompts.sh --check-release
~/update_core_prompts.sh --accept-release
~/update_core_prompts.sh --list-snapshots
```

Checking compares canonical release tags and prepares a clean release mirror;
it never installs. New-engine acceptance updates the saved installation through a
recoverable transaction, independently of the development checkout.

Scheduling is optional and separate from install:

```bash
~/update_core_prompts.sh --schedule-daily 09:00
# --notify-only disables automatic release acceptance; existing-bundle sync still runs.
```

Existing schedules are preserved. A compatible older updater may receive the new
runtime before its next invocation converts the saved selection. If an older
engine's scope guards reject that bridge, run the current installer once.

Use the installer `--rollback TRANSACTION_ID --dry-run` to preview recovery,
then `--rollback TRANSACTION_ID` to restore. The updater also supports
`--rollback previous`. See the [recovery contract](INSTALL-PROFILES.md#recover-an-installation)
for exact-file checks and the release-watch observation exception. New transaction journals
are retained; older-journal retention candidates are advisory, not automatic
deletions. See [installation, migration, and recovery](INSTALL-PROFILES.md)
for the full selection and recovery contract.

## What The Generated Views Are For

When you want to inspect the current emitted state without reading raw manifests or directories:

- [Capability catalog](CAPABILITY-CATALOG.md): what ships and where it lands
- [Release delta](RELEASE-DELTA.md): what changed versus the previous manifest
- [Consumer status](STATUS.md): generated build, validation, and smoke summary

These are useful inspection aids, not the first thing a new user should read.

## Where The Important Files Live

- `ssot/`: canonical authored capability source
- `sources/ssot-baselines/`: preserved strongest baselines used for future judging
- `.meta/capabilities/`: machine-readable capability descriptors
- `.codex/`, `.gemini/`, `.claude/`, `.kiro/`: generated runtime surfaces
- `docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, `docs/STATUS.md`: generated inspection views

## Next Docs

- [Examples](EXAMPLES.md)
- [UAC usage](UAC-USAGE.md)
- [CLI reference](CLI-REFERENCE.md)
- [FAQ](FAQ.md)

## Selected local skill targets

Choose agy, Codex, Kiro, or Grok with an explicit skills-only profile. agy uses `.gemini/config/skills`. Codex skills install
under `.agents/skills`, shared with Gemini; Gemini settings and agents stay under `.gemini`. Grok gets native `.grok/skills` packages. Preview the exact
write set and preserve unknown or customized copies before applying. See
[installation profiles and rollback](INSTALL-PROFILES.md).

### Loopy: bounded agent loops

Use `$loopy` in Codex or `/loopy` in Kiro and Grok to find, audit, craft, run, or
debrief a loop. For example: “Use Loopy to audit this loop and repair only material
weaknesses.” Expect a concise verdict and a minimally repaired loop; execution,
scheduling, and publication retain their separate authorization boundaries.

### Improve with independent review

Use `supercharge /ult /full skip grade <prompt>` to improve and independently review a prompt without running its task. Use `supercharge /grade <artifact>` for actual candidate revisions and independent grades; the final artifact is the best retained candidate, not necessarily the last. Real subagents are required for substantive review. The visible catchup tables remain unchanged.

For measured optimization, ask Auto-Research to run a stated number of trials against a protected scorecard: it keeps a best candidate, discards unsuccessful trial changes, and continues until the search condition is met. Keep requested deliverables at stable project paths and revisions in Git. Supercharge otherwise responds inline; experimental candidates can remain in temporary working storage with one results ledger. [Examples and evidence limits](FRONTIER-MODERNIZATION.md).

Routine updates automatically remove identified retired Core-Prompts agents,
including locally modified copies, while retaining skills and third-party agents
such as Kiro Crew. See [installation cleanup](INSTALL-PROFILES.md#automatic-agent-cleanup-on-update).
