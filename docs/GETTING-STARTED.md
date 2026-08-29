# Getting Started

Use this page in the same order Core-Prompts is meant to be used:

1. installed capabilities first
2. UAC second
3. broader repo tooling third

## Step 1: Use Installed Capabilities

Start in your CLI, not in the repo.

If Core-Prompts is already installed in Codex, Gemini, Claude, or Kiro, begin with one of these asks:

| Capability | Example ask | What good output looks like |
| --- | --- | --- |
| `analyze-context` | "Use `analyze-context` to inspect this subsystem across several files and keep resumable state in the active non-main worktree." | one gitignored context/todo/insights set in the active worktree; legacy main-checkout state may be read for continuity but is never updated |
| `docs-review-expert` | "Use `docs-review-expert` to review our docs IA and recommend the smallest rewrite that restores clarity." | placement decisions, drift findings, and rewrite guidance |
| `gitops-review` | "Use `gitops-review` to tell me whether this branch is ready for PR and what blockers remain." | gate type, blockers, companion reviews, and next steps |
| `codebase-health-audit` | "Use `codebase-health-audit` to audit this repo for LOC hotspots, god objects, coupling, likely dead code, and drift from this prior audit block." | metric-backed structural findings, drift analysis, and slice-ready remediation |
| `code-review` | "Use `code-review` to review my staged changes, including resource cleanup, concurrency, operational readiness, and API/schema compatibility." | evidence-based findings, scope assessment, lifecycle and contract risks, message guidance, and merge readiness |
| `address-code-review` | "Use `address-code-review` to inspect the open MR comments and apply only the selected reviewer-requested fixes." | comments found, targeted fixes, changed files, commit guidance, and follow-up review |
| `eng-report` | "Use `eng-report` to generate an HTML progress report for this repo since 2026-06-01." | git-derived metrics, report path, and narrative tied to deterministic data |
| `ic-assistant` | "Use `ic-assistant` to track this active incident and tell me the current phase, overdue items, and next required action." | mode, phase, next action, status-update timer, and escalation flags |
| `supercharge` | "Use `supercharge /adversarial /debate /deep` to stress-test this release decision with Bull/Bear/Decider analysis, risks, mitigants, and flip conditions." | stronger framing, constraints, sequencing, first-principles accounting, and adversarial debate when requested |
| `auto-research` | "Use `auto-research` to improve our review prompt so it catches more regressions without increasing noise." | experiment design, evaluation, and a validated winner |
| `batman` | "Batman: verify this request, publish the Host-Fit Plan, then implement this shipped-defect correction through independent-subagent TDD, blocking milestone reviews, verification, docs, PR, authorized merge, release, install, and cleanup." | instruction-integrity and host-fit decisions, independent subagent evidence, provenance-qualified red and mutation checks, progress reports, milestone decisions, and state-specific landing receipts |
| `demo-recorder` | "Use `demo-recorder` to create a Playwright demo of the new dashboard feature with video recording." | demo plan, complete Playwright script, run command, and output path |
| `dynamic-html-presentations` | "Use `dynamic-html-presentations` to create a standalone HTML deck and ask me whether I want PNG, PPTX, or all formats." | narrative-first deck, polished 16:9 visuals, interaction behavior, and validated requested exports |
| `testing` | "Use `testing` to identify the edge cases and tests this change needs." | prioritized tests and missing edge cases |

If you want an agent surface rather than a direct skill invocation, start with the table below. Capability Fabric metadata is advisory; explicit invocation follows the selected capability's operating contract.

| Agent | Example ask | Best when you need... |
| --- | --- | --- |
| `batman` | "Batman: take this implementation through instruction integrity, a Host-Fit Plan, independent-subagent TDD, all applicable blocking reviews, and authorized landing. Report initial, stage, blocker, and 15-minute progress." | explicitly invoked implementation through subagents, all applicable blocking milestone reviews, evidence-class honesty, and authorized landing |
| `docs-review-expert` | "Use `docs-review-expert` to review our onboarding docs for drift before release." | structured documentation review |
| `gitops-review` | "Use `gitops-review` to judge whether we are ready to merge and release." | a merge or release gate |
| `ic-assistant` | "Use `ic-assistant` to keep the incident process on-track and flag the next required action." | generic phase-aware guidance, with internal runbook mode only on request |
| `weekly-intel` | "Use `weekly-intel` to produce this week's update from our source set." | a multi-source status summary |

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

If `judge` says the landing is structurally close but still needs bounded behavioral proof, use `auto-research` for that proof step. During the advisory rollout, a structurally ready apply may land as `behavioral_pending`, but it cannot advance the behavioral baseline or claim promotion.

To move an already-canonical candidate from `behavioral_pending` to `promote`, use an independently signed public evidence bundle. The approved evaluator trust policy must already be on protected main and on the evaluated baseline's ancestry; a candidate cannot authorize its own evaluator. See [Capability evaluation](CAPABILITY-EVALUATION.md#from-behavioral_pending-to-promote) for the status model and [UAC usage](UAC-USAGE.md#example-finalize-an-existing-candidate-after-behavioral-proof) for the exact command.

For the full flow, go to [UAC usage](UAC-USAGE.md).

## Step 3: Use Repo Tooling To Verify Or Operate The Repo

Compile the skill's goal and topology before claiming that an instruction change is behavior-neutral:

```bash
bin/capability-eval compile --skill supercharge
bin/capability-eval calibrate --static-only
bin/capability-eval probe
```

These commands make zero model calls. `structural_ready` means deterministic gates passed; only an independent, current `PromotionVerdict.v2` can mean `promote`. Version 1 verdicts remain readable but cannot authorize promotion.

Live comparison is available only through explicit run plans and operator-authorized model calls. Behavioral promotion additionally requires the separately operated protected evaluator, conforming adapters, protected credentials and runner identities, external sealed data, qualified judges, purpose-separated signatures, and reproduction evidence. The bundled Codex adapter is fail-closed until a separately approved credential broker or equivalent isolation boundary exists. Missing prerequisites return `inconclusive`; the checked-in template cannot manufacture a promotion. `instruction-editor` remains experimental, and Google-style rewriting remains off by default in UAC.

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

Optional deploy dry run:

```bash
bin/capability-fabric deploy --dry-run --cli all
```

For a narrow external-target repair, use `--surface-only` with an explicit slug. It copies only that emitted bundle and skips the standalone updater, launcher, and local binaries:

```bash
bin/capability-fabric deploy --dry-run --surface-only --cli kiro --slug code-review --target "$HOME" --allow-nonlocal-target
```

For Batman on Kiro, the same dry-run also previews the bounded cleanup of obsolete source files:

```bash
bin/capability-fabric deploy --dry-run --surface-only --cli kiro --slug batman --target "$HOME" --allow-nonlocal-target
```

When all three residues exist, the prune plan lists exactly:

- `.kiro/skills/batman/PROTOCOL.md`
- `.kiro/skills/batman/PROMPT-AMENDMENT.md`
- `.kiro/skills/batman/CODEX-UAC-INTAKE.md`

Dry-run prints one `DRY-RUN PRUNE` line per existing residue and does not move anything. The live command recoverably archives only those existing files under `.core-prompts-state/stale-pruned/<timestamp>/...` and prints a `source -> archive` receipt for each move. It preserves `.kiro/skills/batman/SKILL.md`, `resources/`, and unrelated files in the Batman skill directory.

Use the printed receipt to recover an individual file from its timestamped archive to the original source path. If the cleanup occurred as part of an accepted release install, `~/update_core_prompts.sh --rollback previous` can instead restore the pre-install rollback snapshot.

For the breaking `autosearch` rename, deploy `auto-research` to replace installed stale surfaces:

```bash
bin/capability-fabric deploy --cli all --slug auto-research --target "$HOME" --allow-nonlocal-target
```

Deploying `auto-research` prunes the old installed `autosearch` skill, agent, and resource paths for the selected CLIs.

## Installed Release Watch

When you install into a home target, Core-Prompts writes the installed version and release metadata into the standalone updater bundle:

- `~/.core-prompts-updater/VERSION`
- `~/.core-prompts-updater/RELEASE_SOURCE.env`
- `~/.core-prompts-updater/LOCAL_REPO.env`
- `~/update_core_prompts.sh`

Daily scheduled updater runs execute `~/update_core_prompts.sh --check-release` before normal update sync. The check compares the installed standalone bundle against the latest immutable release tag agreed by the canonical remotes, updates `~/.core-prompts-state/release-watch.json`, and never auto-installs when run directly. Scheduled runs auto-accept valid releases by default after that check. Accepted releases safely fast-forward the recorded source checkout first when it is clean, then run the installer from that checkout; if that is unsafe, they install from the clean release mirror.

Use the explicit acceptance step when you want to refresh the installed bundle manually. `--accept-release` is the explicit install/apply step:

```bash
~/update_core_prompts.sh --check-release
~/update_core_prompts.sh --accept-release
~/update_core_prompts.sh --rollback previous
```

Install `--schedule-daily HH:MM --notify-only` if you want scheduled release checks without automatic release acceptance. Scheduled runs use deterministic user, package-manager, and system executable paths; an existing managed CLI surface remains an update target even when cron cannot discover that CLI binary. Every accepted release writes a pre-install rollback snapshot under `~/.core-prompts-state/snapshots/`; older snapshots are pruned so the latest 2 are retained by default. `--list-snapshots` lists rollback points and `--rollback previous` restores the latest snapshot.

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
