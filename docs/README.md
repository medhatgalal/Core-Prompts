# Docs Home

Use this page to choose the right documentation path without reading the entire repo.

## Fast Paths
| Need | Start here |
| --- | --- |
| I want to use the deployed Core-Prompts skills the normal way | [Getting started](GETTING-STARTED.md) |
| I want to browse what Core-Prompts ships right now | [Capability catalog](CAPABILITY-CATALOG.md) |
| I want to know what changed in the latest build | [Release delta](RELEASE-DELTA.md) |
| I want a quick health snapshot before I trust the package | [Consumer status](STATUS.md) |
| I want to know why this repo exists | [Root README](../README.md) |
| first build, validate, and inspect loop | [Getting started](GETTING-STARTED.md) |
| direct surface paths, deploy rules, and runtime expectations | [CLI reference](CLI-REFERENCE.md) |
| UAC intake, judge, and apply behavior | [UAC usage](UAC-USAGE.md) |
| release gate, package boundary, and CI parity | [Release packaging](RELEASE-PACKAGING.md) |
| implementation model and generated-surface architecture | [Repository architecture](ARCHITECTURE.md) |

## Reader Guides

### If you are evaluating the repo
Start with:

1. [Root README](../README.md)
2. [Getting started](GETTING-STARTED.md)
3. [Examples](EXAMPLES.md)
4. [Capability catalog](CAPABILITY-CATALOG.md)

### If you are just trying to use Core-Prompts
Start with:

1. [Getting started](GETTING-STARTED.md)
2. [Examples](EXAMPLES.md)
3. [FAQ](FAQ.md)
4. [Capability catalog](CAPABILITY-CATALOG.md)

### If you are adopting or operating it
Start with:

1. [Getting started](GETTING-STARTED.md)
2. [CLI reference](CLI-REFERENCE.md)
3. [UAC usage](UAC-USAGE.md)
4. [Consumer status](STATUS.md)

### If you are maintaining or extending it
Start with:

1. [Technical README](README_TECHNICAL.md)
2. [Repository architecture](ARCHITECTURE.md)
3. [Maintainer hygiene rules](MAINTAINER-HYGIENE.md)
4. [Release packaging](RELEASE-PACKAGING.md)

## Product / Operator Docs
- [Getting started](GETTING-STARTED.md)
- [Capability catalog](CAPABILITY-CATALOG.md)
- [Release delta](RELEASE-DELTA.md)
- [Consumer status](STATUS.md)
- [Examples](EXAMPLES.md)
- [FAQ](FAQ.md)

## Core Reference Docs
- [Capability Fabric](CAPABILITY-FABRIC.md)
- [UAC usage](UAC-USAGE.md)
- [UAC capability model](UAC-CAPABILITY-MODEL.md)
- [Baseline source library](../sources/ssot-baselines/README.md)
- [CLI reference](CLI-REFERENCE.md)

## Integration Contract
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)

## Maintainer / Release Docs
- [Technical README](README_TECHNICAL.md)
- [Repository architecture](ARCHITECTURE.md)
- [Maintainer hygiene rules](MAINTAINER-HYGIENE.md)
- [Release packaging](RELEASE-PACKAGING.md)

## Documentation Design Principles

- deployed Core-Prompts skills are the primary user-facing entrypoint
- the root README explains value, pains solved, and the fast path
- this docs hub routes by user intent
- technical docs keep exact commands, paths, and maintainer behavior
- one concept should have one canonical home, with links instead of duplication

## Research / Authoring Docs
These stay in-repo but are not part of the packaged operator doc set.
- [Architecture source assessment](ARCHITECTURE-SOURCE-ASSESSMENT.md)
- [Prompt pack](prompt-pack/README.md)
- `docs/ASSETS/`
