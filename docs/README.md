# Docs Home

Use this page to pick the right documentation path quickly. The intended order is:

1. installed capabilities first
2. UAC second
3. broader repo tooling and maintainer docs third

## Start Here

| Need | Start here |
| --- | --- |
| I want to use an installed Core-Prompts skill or agent | [Getting started](GETTING-STARTED.md) |
| I want richer, copyable example asks | [Examples](EXAMPLES.md) |
| I want to design or improve a report, web, desktop, or mobile experience | [Experience design examples](EXAMPLES.md#engos-design-experience) |
| I need a reviewed home installation or discovery diagnosis | [Installation profiles](INSTALL-PROFILES.md) and [home-install quickstart](quickstart.md) |
| I am importing or uplifting a capability | [UAC usage](UAC-USAGE.md) |
| I need to choose the right skill or understand neighboring boundaries | [Skill Job Map](SKILL-JOB-MAP.md) |
| I need to understand structural checks, behavioral proof, or token budgets | [Capability evaluation](CAPABILITY-EVALUATION.md) |
| I need exact commands, paths, and generated-surface locations | [CLI reference](CLI-REFERENCE.md) |
| I want to inspect what ships or what changed | [Capability catalog](CAPABILITY-CATALOG.md), [Release delta](RELEASE-DELTA.md), and [Consumer status](STATUS.md) |
| I maintain builds, releases, release-watch updates, or docs hygiene | [Maintainer hygiene](MAINTAINER-HYGIENE.md), [CLI reference](CLI-REFERENCE.md), and [Release packaging](RELEASE-PACKAGING.md) |

## Reader Paths

### Daily user of installed capabilities

1. [Getting started](GETTING-STARTED.md)
2. [Examples](EXAMPLES.md)
3. [FAQ](FAQ.md)

### Capability author or importer

1. [UAC usage](UAC-USAGE.md)
2. [UAC capability model](UAC-CAPABILITY-MODEL.md)
3. [CLI reference](CLI-REFERENCE.md)
4. [Baseline source library](../sources/ssot-baselines/README.md)

### Maintainer or releaser

1. [CLI reference](CLI-REFERENCE.md)
2. [Maintainer hygiene](MAINTAINER-HYGIENE.md)
3. [Release packaging](RELEASE-PACKAGING.md)
4. [Technical README](README_TECHNICAL.md)

Installed update commands live in the [CLI reference](CLI-REFERENCE.md#check-or-accept-installed-releases). The [release-watch contract](RELEASE-PACKAGING.md#installed-release-watch-contract) explains saved-profile and legacy installations, scheduling, acceptance, and recovery.

## Canonical Homes

- [`../README.md`](../README.md): orientation, first-use examples, and links to authoring and maintenance
- [`GETTING-STARTED.md`](GETTING-STARTED.md): first-run path in the correct order
- [`EXAMPLES.md`](EXAMPLES.md): deeper scenario-style asks and expected outputs
- [`UAC-USAGE.md`](UAC-USAGE.md): intake, uplift, `plan`, `judge`, and `apply`
- [`CLI-REFERENCE.md`](CLI-REFERENCE.md): exact commands, paths, generated surfaces, and deploy behavior
- [`MAINTAINER-HYGIENE.md`](MAINTAINER-HYGIENE.md): human maintainer guide and review checklist, with policy routed to steering

## Generated Views

These are useful inspection aids, not the main onboarding path:

- [Capability catalog](CAPABILITY-CATALOG.md): current capability inventory and surface placement
- [Skill Job Map](SKILL-JOB-MAP.md): plain-English purpose, non-purpose, neighbors, and portfolio recommendation for every skill
- [Release delta](RELEASE-DELTA.md): generated comparison against the previous manifest
- [Consumer status](STATUS.md): generated build, validation, and smoke snapshot

## Technical And Maintainer Docs

- [Repository architecture](ARCHITECTURE.md)
- [Capability Fabric](CAPABILITY-FABRIC.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
- [Technical README](README_TECHNICAL.md)
- [Release packaging](RELEASE-PACKAGING.md)

## Research And Authoring Material

These stay in-repo but are not the first-stop user docs:

- [Historical architecture source assessment](ARCHITECTURE-SOURCE-ASSESSMENT.md)
- [Archived docs-authoring prompt pack](prompt-pack/README.md)
- `docs/ASSETS/`
