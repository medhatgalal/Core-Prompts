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
| `supercharge` | "Use `supercharge` to make this feature brief execution-ready." | stronger framing, constraints, and sequencing |
| `autosearch` | "Use `autosearch` to improve our review prompt so it catches more regressions without increasing noise." | experiment design, evaluation, and a validated winner |
| `testing` | "Use `testing` to identify the edge cases and tests this change needs." | prioritized tests and missing edge cases |

If you want an advisory agent rather than a direct skill invocation, start with:

| Agent | Example ask | Best when you need... |
| --- | --- | --- |
| `mentor` | "Use `mentor` to tell me the next reversible move on this repo." | sequencing and scope control |
| `docs-review-expert` | "Use `docs-review-expert` to review our onboarding docs for drift before release." | structured documentation review |
| `gitops-review` | "Use `gitops-review` to judge whether we are ready to merge and release." | a merge or release gate |
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

If `judge` says the landing is structurally close but still needs bounded behavioral proof, use `autosearch` for that proof step before `apply`.

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
