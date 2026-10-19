# Docs Home

Use this page to pick the right documentation path quickly. The intended order is:

1. installed capabilities first
2. UAC second
3. broader repo tooling and maintainer docs third

## Start Here

| Need | Start here |
| --- | --- |
| I am returning and want to know what changed in daily use | [Everyday changes](../README.md#what-changes-in-everyday-use) and [before/now examples](EXAMPLES.md#everyday-requests-before-and-now) |
| I want to use an installed Core-Prompts skill | [Getting started](GETTING-STARTED.md) |
| I need to install, repair old packages, or enable updates | [Installation and recovery](INSTALL-PROFILES.md) |
| I need the next skill and its conditional handoff | [Skill flows](SKILL-FLOWS.md) |
| I want richer, copyable example asks | [Examples](EXAMPLES.md) |
| I am importing or uplifting a capability | [UAC usage](UAC-USAGE.md) |
| I need to choose the right skill or understand neighboring boundaries | [Skill Job Map](SKILL-JOB-MAP.md) |
| I need to understand structural checks, behavioral proof, or token budgets | [Capability evaluation](CAPABILITY-EVALUATION.md) |
| I need exact commands, paths, and generated-surface locations | [CLI reference](CLI-REFERENCE.md) |
| I want to inspect what ships or what changed | [Capability catalog](CAPABILITY-CATALOG.md), [Release delta](RELEASE-DELTA.md), and [Consumer status](STATUS.md) |
| I maintain builds, releases, release-watch updates, or docs hygiene | [Maintainer hygiene](MAINTAINER-HYGIENE.md), [CLI reference](CLI-REFERENCE.md), and [Release packaging](RELEASE-PACKAGING.md) |

## Reader Paths

### Daily user of installed capabilities

1. [Getting started](GETTING-STARTED.md)
2. [Skill flows](SKILL-FLOWS.md) for the first missing job
3. [Everyday examples](EXAMPLES.md#everyday-requests-before-and-now), then the selected skill example
4. [FAQ](FAQ.md)

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

Use [Installation and recovery](INSTALL-PROFILES.md) for fresh installs, historical repairs, updater enrollment, optional scheduling, and rollback. Release checking does not install; scheduled runs accept valid releases by default and then reconcile installed packages. The guide explains preserved conflicts and compatibility with older updaters.

## Canonical Homes

- [`../README.md`](../README.md): orientation, AI handoff, real usage examples, UAC boundary, and repo-tooling fast path
- [`GETTING-STARTED.md`](GETTING-STARTED.md): first-run path in the correct order
- [`SKILL-FLOWS.md`](SKILL-FLOWS.md): conditional routes and handoff boundaries
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

- [Architecture source assessment](ARCHITECTURE-SOURCE-ASSESSMENT.md)
- [Prompt pack](prompt-pack/README.md)
- `docs/ASSETS/`
