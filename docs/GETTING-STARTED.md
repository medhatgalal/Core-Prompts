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
| `docs-review-expert` | "Use `docs-review-expert` to review our docs IA and recommend the smallest rewrite that restores clarity." | placement decisions, drift findings, and rewrite guidance |
| `gitops-review` | "Use `gitops-review` to tell me whether this branch is ready for PR and what blockers remain." | gate type, blockers, companion reviews, and next steps |
| `codebase-health-audit` | "Use `codebase-health-audit` to audit this repo for LOC hotspots, god objects, coupling, likely dead code, and drift from this prior audit block." | metric-backed structural findings, drift analysis, and slice-ready remediation |
| `code-review` | "Use `code-review` to review my staged changes before I commit." | findings, scope assessment, message guidance, and merge readiness |
| `address-code-review` | "Use `address-code-review` to inspect the open MR comments and apply only the selected reviewer-requested fixes." | comments found, targeted fixes, changed files, commit guidance, and follow-up review |
| `eng-report` | "Use `eng-report` to generate an HTML progress report for this repo since 2026-06-01." | git-derived metrics, report path, and narrative tied to deterministic data |
| `ic-assistant` | "Use `ic-assistant` to track this active incident and tell me the current phase, overdue items, and next required action." | mode, phase, next action, status-update timer, and escalation flags |
| `supercharge` | "Use `supercharge /adversarial /debate /deep` to stress-test this release decision with Bull/Bear/Decider analysis, risks, mitigants, and flip conditions." | stronger framing, constraints, sequencing, first-principles accounting, and adversarial debate when requested |
| `auto-research` | "Use `auto-research` to improve our review prompt so it catches more regressions without increasing noise." | experiment design, evaluation, and a validated winner |
| `demo-recorder` | "Use `demo-recorder` to create a Playwright demo of the new dashboard feature with video recording." | demo plan, complete Playwright script, run command, and output path |
| `testing` | "Use `testing` to identify the edge cases and tests this change needs." | prioritized tests and missing edge cases |

If you want an advisory agent rather than a direct skill invocation, start with:

| Agent | Example ask | Best when you need... |
| --- | --- | --- |
| `mentor` | "Use `mentor` to tell me the next reversible move on this repo, or look at the left pane and review the error if I am in tmux." | sequencing, scope control, and tmux-aware terminal context recovery |
| `docs-review-expert` | "Use `docs-review-expert` to review our onboarding docs for drift before release." | structured documentation review |
| `gitops-review` | "Use `gitops-review` to judge whether we are ready to merge and release." | a merge or release gate |
| `ic-assistant` | "Use `ic-assistant` to keep the incident process on-track and flag the next required action." | generic phase-aware guidance, with internal runbook mode only on request |
| `weekly-intel` | "Use `weekly-intel` to produce this week's update from our source set." | a multi-source status summary |

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

If `judge` says the landing is structurally close but still needs bounded behavioral proof, use `auto-research` for that proof step before `apply`.

For the full flow, go to [UAC usage](UAC-USAGE.md).

## Step 3: Use Repo Tooling To Verify Or Operate The Repo

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

Install `--schedule-daily HH:MM --notify-only` if you want scheduled release checks without automatic release acceptance. Every accepted release writes a pre-install rollback snapshot under `~/.core-prompts-state/snapshots/`; older snapshots are pruned so the latest 2 are retained by default. `--list-snapshots` lists rollback points and `--rollback previous` restores the latest snapshot.

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
