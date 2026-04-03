# Core-Prompts / Capability Fabric

> Good prompts rarely fail all at once.
>
> They get copied, repackaged, weakened for one tool, duplicated in another repo, and quietly stop being trustworthy.

Core-Prompts exists to stop that decay.

The default way to benefit from it is simple: use the Core-Prompts skills that are already deployed into your CLI. The repo, UAC, and Capability Fabric workflows are the maintainer and advanced-authoring layer that keep those deployed skills trustworthy over time.

For installed users, the repo now also emits a thin consumer shell from canonical metadata:
- a generated capability catalog
- a release delta report
- a user-facing status snapshot

Those outputs help users answer what they have, what changed, and what is healthy without turning this repo into a runtime platform.

## Why Invest In This?

If you work with serious AI prompts long enough, you usually hit the same problems:

- a prompt works well in one place, then drifts as it gets copied to other tools
- the strongest version gets lost during cleanup, formatting, or "optimization"
- nobody is fully sure which version is canonical anymore
- docs, metadata, and generated outputs stop matching each other
- shipping an AI capability feels ad hoc instead of reviewable and repeatable

Capability Fabric removes that pain by giving you:

| Pain | What this repo gives you |
| --- | --- |
| prompt drift across tools | one SSOT that generates consistent surfaces |
| prompt weakening over time | repo-resident baseline sources that preserve the strongest known body |
| unclear ownership and format sprawl | one canonical model for skills, agents, descriptors, and packaged outputs |
| low trust in generated AI assets | validation, deploy, packaging, and release gates |
| repeated manual rework | deterministic wrappers and rebuildable surfaces |

## Who This Is For

- prompt engineers who want durable assets instead of scattered markdown
- AI-heavy engineering teams who need reviewable, releasable capabilities
- maintainers who want docs, metadata, and generated surfaces to stay aligned
- advanced users who want one prompt family to land cleanly across Codex, Gemini, Claude, and Kiro

## Start Here First

For most users, the original and primary usage model is:

1. use the Core-Prompts skills already deployed into your CLI
2. come to this repo when you need to inspect, update, rebuild, validate, or release those capabilities

The advanced repo wrappers are for maintainers, contributors, and prompt authors who need to change canonical state.

## Repo Fast Path
Use the repo wrappers when you are intentionally working on the capability source, build, validation, or release layers. They select a supported Python runtime automatically and keep the common flows consistent.

```bash
bin/uac --help
bin/capability-fabric --help
```

## What You Get
- canonical SSOT prompts in `ssot/`
- strongest preserved baseline prompt bodies in `sources/ssot-baselines/`
- machine-readable descriptors in `.meta/capabilities/`
- generated surfaces for Codex, Gemini, Claude, and Kiro
- advisory aggregate handoff in `.meta/capability-handoff.json`
- deterministic import and uplift through UAC

## Typical Maintainer Flow

When you are changing or importing capability source, the path is:

1. bring in a prompt or prompt family through UAC
2. compare it against the preserved baseline and quality gates
3. land the canonical source in `ssot/`
4. generate skill and agent surfaces
5. validate, deploy, package, and release from one consistent repo state

```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
bin/capability-fabric build
bin/capability-fabric validate --strict
scripts/deploy-surfaces.sh --dry-run --cli all
scripts/install-local.sh --dry-run --target "$HOME" --allow-nonlocal-target
```

## Why The Model Matters

This repo treats prompts more like software than scratch notes.

That means:

- canonical authored source
- preserved strongest baseline
- machine-readable metadata
- generated runtime surfaces
- validation before deployment
- deterministic packaging and release

Capability types:

- `skill`
- `agent`
- `both`
- `manual_review`

Commands, plugins, powers, and extensions are deployment wrappers, not peer capability types.

Direct skill exposure is standardized on `skills/<slug>/SKILL.md` across Codex, Gemini, Claude, and Kiro. This repo no longer treats `commands/` or `prompts/` directories as direct deployment targets.

Canonical state:
- `ssot/<slug>.md`
- `.meta/capabilities/<slug>.json`
- `sources/ssot-baselines/<slug>/baseline.md`

Generated surfaces are derived artifacts under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`.

## Apply vs Deploy vs Package

<details>
<summary><strong>What these words mean in practice</strong></summary>

- `apply`: mutate canonical repo state, rebuild surfaces, and validate
- `deploy`: copy generated surfaces and bundled resources to a target root
- `install-local.sh`: convenience wrapper for explicit copy installs into a home-like target
- `package`: produce release archives from the curated runtime and integration boundary

</details>

## Documentation

Use the docs in layers:

- [Docs hub](docs/README.md)
- [Getting started](docs/GETTING-STARTED.md)
- [Capability catalog](docs/CAPABILITY-CATALOG.md)
- [Release delta](docs/RELEASE-DELTA.md)
- [Consumer status](docs/STATUS.md)
- [CLI reference](docs/CLI-REFERENCE.md)
- [UAC usage](docs/UAC-USAGE.md)
- [Capability model](docs/UAC-CAPABILITY-MODEL.md)
- [Baseline source library](sources/ssot-baselines/README.md)
- [Orchestrator contract](docs/ORCHESTRATOR-CONTRACT.md)
- [Technical docs hub](docs/README_TECHNICAL.md)
- [Release packaging](docs/RELEASE-PACKAGING.md)

## Bottom Line

Use Core-Prompts if you want AI capabilities that are:

- easier to trust
- easier to maintain
- harder to accidentally weaken
- portable across tools
- reviewable and releasable like real engineering assets
