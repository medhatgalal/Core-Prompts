# Technical Documentation Hub

Use this index for repository implementation and operational detail. For using installed capabilities, start with [Getting started](GETTING-STARTED.md) and [Examples](EXAMPLES.md).

| Need | Canonical guide |
| --- | --- |
| Source, resources, generators, validators, and deployment architecture | [Architecture](ARCHITECTURE.md) |
| Provider responsibilities and advisory boundaries | [Capability Fabric](CAPABILITY-FABRIC.md) |
| Capability authoring and same-slug updates | [UAC usage](UAC-USAGE.md) |
| Descriptor and surface metadata | [UAC capability model](UAC-CAPABILITY-MODEL.md) |
| External orchestrator consumption | [Orchestrator contract](ORCHESTRATOR-CONTRACT.md) |
| Commands and write effects | [CLI reference](CLI-REFERENCE.md) |
| Reviewed installation, ownership, discovery, and recovery | [Installation profiles](INSTALL-PROFILES.md) |
| Structural acceptance and independent behavioral promotion | [Capability evaluation](CAPABILITY-EVALUATION.md) |
| Hosted checks, packaging, publishing, and release watch | [Release packaging](RELEASE-PACKAGING.md) |
| Documentation checks and governing policy links | [Maintainer hygiene](MAINTAINER-HYGIENE.md) |

Canonical capability bodies live in `ssot/`, resources under `sources/`, and surface rules in `.meta/surface-rules.json`. Generated packages live under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`, and `.grok/`. Capability changes follow the [repository delivery workflow](../.kiro/steering/repo-workflow.md); a direct edit followed by deployment does not replace UAC review and delivery.
