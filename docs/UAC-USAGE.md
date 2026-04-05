# UAC Usage Guide

Use UAC, the capability intake and uplift workflow, when you want to bring new prompt-like source into canonical Core-Prompts state.

Do not start with UAC if your goal is just to use already installed Core-Prompts skills or agents. UAC is the second layer in the product model, after installed capabilities and before broader repo tooling.

Preferred shell entrypoints:

```bash
bin/uac --help
bin/capability-fabric --help
```

Direct Python entrypoint still works:

```bash
python3 scripts/uac-import.py --help
```

## What UAC Is For

Use UAC when you need to:

- inspect how an external prompt or prompt family would land in this repo
- decide whether the source should become a skill, an agent, or manual review
- benchmark a candidate before it mutates canonical repo state
- write canonical SSOT, descriptor, and baseline state after a successful review

## When Not To Use UAC

Do not start with UAC when you are:

- using installed Core-Prompts skills or agents in daily work
- browsing what already ships in the repo output
- rebuilding or validating existing canonical state without new capability intake
- copying generated surfaces into a target home after a build

For those cases, use [Getting started](GETTING-STARTED.md), [Examples](EXAMPLES.md), or [CLI reference](CLI-REFERENCE.md).

## Modes

| Mode | Use it when you want to... | Writes repo state |
| --- | --- | --- |
| `import` | inspect one or more sources without mutating the repo | no |
| `audit` | inspect current SSOT entries and generated surfaces | no |
| `explain` | print the capability model and deployment matrix | no |
| `plan` | see the proposed landing shape before writing files | no |
| `judge` | run the quality loop and get a ship or block decision | no |
| `apply` | write canonical repo state, then rebuild and validate | yes |

## The Typical Flow

```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
```

How to think about that sequence:

- `import` is the low-risk first look
- `plan` is the proposed landing shape
- `judge` is the quality and ship decision
- `apply` is the intentional repo mutation step

## Worked Examples

### Example: Plan A Landing Before You Touch Repo State

Command:

```bash
bin/uac plan /absolute/path/to/prompt-family
```

What you are asking UAC to do:

- inspect the candidate source
- cluster it into a coherent capability family
- decide the likely capability shape
- show how it would land into canonical repo state

Typical response shape:

```text
Source summary:
- 6 prompt files detected
- strongest theme: architecture review and migration safety

Proposed landing:
- slug: architecture
- likely capability type: both
- canonical targets:
  - ssot/architecture.md
  - .meta/capabilities/architecture.json
  - sources/ssot-baselines/architecture/baseline.md

Open concerns:
- one source file is mostly release-process guidance and may not belong in the same family
- benchmark fit looks strong for architecture profile, weak for generic prompting profile

Recommended next step:
- run judge with --quality-profile architecture
```

Use `plan` when you want the landing shape, naming, and overlap analysis before any repo mutation.

### Example: Judge Before Apply

Command:

```bash
bin/uac judge /absolute/path/to/prompt-family --quality-profile architecture
```

What you are asking UAC to do:

- compare the candidate against the selected benchmark
- resolve the baseline source
- produce pass or fail evidence
- stop short of mutating canonical repo state

Typical response shape:

```text
Quality status: ship

Judge summary:
- benchmark profile: architecture
- strongest scores: migration clarity, explicit boundaries, output contract
- weak areas: invocation hints are too short and examples need more concrete asks

Artifacts:
- reports/quality-reviews/architecture/LATEST.md

Decision:
- candidate is ready for apply after expanding invocation examples
```

Use `judge` when you want the quality decision, evidence, and blockers without changing the repo.

### Example: Apply A Ship-Ready Capability

Command:

```bash
bin/uac apply /absolute/path/to/prompt-family --yes
```

What `apply` does:

- writes canonical repo state under:
  - `ssot/<slug>.md`
  - `.meta/capabilities/<slug>.json`
- materializes or preserves the fidelity baseline under:
  - `sources/ssot-baselines/<slug>/baseline.md`
- may persist quality-review artifacts under:
  - `reports/quality-reviews/`
- runs:
  - `bin/capability-fabric build`
  - `bin/capability-fabric validate --strict`

Typical response shape:

```text
Applied capability:
- slug: architecture
- updated:
  - ssot/architecture.md
  - .meta/capabilities/architecture.json
  - sources/ssot-baselines/architecture/baseline.md

Post-apply:
- build: success
- validate --strict: success

Next step:
- deploy only if you want generated surfaces copied into a target root
```

Use `apply` only when you intend to change canonical repo state.

## Deploy After Apply

`apply` does not deploy to CLI homes automatically. Deploy is a separate explicit step.

```bash
bin/capability-fabric deploy --cli codex --slug autosearch --target "$HOME" --allow-nonlocal-target
```

Notes:

- `--slug` is repeatable and limits deployment to specific capabilities
- deployment copies the full emitted bundle for each selected surface
- deploy is copy-only and does not rewrite capability metadata paths

## Source Kinds

UAC can analyze:

- local files
- local folders
- raw public HTTPS URLs
- GitHub repo or folder URLs
- multiple `--source` values in one run
- repomix-reduced repo inputs

## Important Boundaries

- UAC publishes advisory metadata and handoff artifacts only. It does not decide runtime routing or delegation.
- Direct exposure lands in each vendor `skills/<slug>/SKILL.md` path when a capability is classified for direct use.
- This repo does not use UAC to target direct `commands/` or `prompts/` deployment paths.

## Related Docs

- [Getting started](GETTING-STARTED.md)
- [Examples](EXAMPLES.md)
- [UAC capability model](UAC-CAPABILITY-MODEL.md)
- [Baseline source library](../sources/ssot-baselines/README.md)
- [CLI reference](CLI-REFERENCE.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
