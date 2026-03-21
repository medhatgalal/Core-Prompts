# Getting Started

This is the shortest safe path to prove the repo is working and understand what value you get from it.

## What Success Looks Like

By the end of this page, you should have:

- one working build of the generated surfaces
- one successful strict validation pass
- a clear sense of where canonical prompt sources live
- a concrete understanding of how this repo turns prompts into maintainable capabilities

## Prerequisites
- Python `3.14` preferred, Python `3.11+` supported
- repository checked out locally
- optional CLI binaries if you want smoke checks or deploy dry-runs

Preferred entrypoints:
- `bin/capability-fabric` for build, validate, and deploy
- `bin/uac` for import, plan, judge, and apply

These wrappers choose the highest available supported Python runtime automatically. If you need to pin one explicitly, set `PYTHON_BIN=python3.11` or `PYTHON_BIN=python3.14`.

## Why This Is Worth Doing

If you are deciding whether to invest time here, the payoff is this:

- you stop managing prompt variants by hand across tools
- you gain one canonical source plus preserved strongest baselines
- you can validate and package AI capabilities instead of treating them like loose notes
- you make drift visible before it becomes release debt

## Fast Path
```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

## What Those Commands Actually Do

| Command | Why it matters |
| --- | --- |
| `build` | regenerates all CLI skill and agent surfaces from canonical repo state |
| `validate --strict` | checks that generated surfaces, manifests, and contracts are internally consistent |
| `smoke-clis.py` | probes the installed CLIs and verifies expected surface visibility where supported |

## UAC Fast Path
```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
```

Use `apply` only when you want canonical repo state to change:
```bash
bin/uac apply /absolute/path/to/family-folder --yes
```

## Success Checklist
- build completes
- strict validation passes
- smoke checks pass when local CLIs are installed
- dry-run deploy shows the intended copies
- you can point to:
  - `ssot/` as the canonical authored source
  - `sources/ssot-baselines/` as the preserved strongest baseline source
  - generated surfaces under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`

## Deploy Modes
Repo-local dry run:
```bash
bin/capability-fabric deploy --dry-run --cli all
```

Home-targeted dry run:
```bash
scripts/install-local.sh --dry-run --target "$HOME" --allow-nonlocal-target
```

## Direct Surface Standard
Direct exposure is skill-only for all supported CLIs:
- `.codex/skills/<slug>/SKILL.md`
- `.gemini/skills/<slug>/SKILL.md`
- `.claude/skills/<slug>/SKILL.md`
- `.kiro/skills/<slug>/SKILL.md`

This repo does not deploy direct surfaces to vendor `commands/` or `prompts/` directories.

## Where To Go Next

<details>
<summary><strong>I want the exact commands and paths</strong></summary>

Go to [CLI reference](CLI-REFERENCE.md).

</details>

<details>
<summary><strong>I want to understand UAC, baselines, and quality gates</strong></summary>

Go to [UAC usage](UAC-USAGE.md) and [Baseline source library](../sources/ssot-baselines/README.md).

</details>

<details>
<summary><strong>I want the architecture and maintainer model</strong></summary>

Go to [Repository architecture](ARCHITECTURE.md), [Technical README](README_TECHNICAL.md), and [Maintainer hygiene rules](MAINTAINER-HYGIENE.md).

</details>

## Next Docs
- [Examples](EXAMPLES.md)
- [FAQ](FAQ.md)
- [CLI reference](CLI-REFERENCE.md)
