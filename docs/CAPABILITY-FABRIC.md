# Capability Fabric

Capability Fabric is the provider layer for reusable prompt capabilities.

## Canonical Layers
| Layer | Purpose | Canonical location |
| --- | --- | --- |
| authored prompt source | canonical prompt body and frontmatter | `ssot/` |
| fidelity baseline source | strongest preserved prompt-body baseline | `sources/ssot-baselines/` |
| machine-readable capability metadata | descriptor, manifest, and advisory handoff | `.meta/` |
| generated vendor surfaces | per-CLI skills, agents, and bundled resources | `.codex/`, `.gemini/`, `.claude/`, `.kiro/` |

## Owns
- source intake
- capability classification
- uplift and convergence
- canonical SSOT and descriptor publication
- generated CLI surfaces
- quality evidence and advisory handoff metadata

## Does Not Own
- runtime routing
- delegation policy
- workflow execution
- SDLC control loops

## Direct Surface Rule
For direct exposure, Capability Fabric standardizes on skill directories with `SKILL.md` files. Vendor `commands/` and `prompts/` locations are not direct deployment targets in this repo.

## UAC Inside Capability Fabric
UAC is the intake, classification, uplift, quality-review, and packaging subsystem.

It accepts:
- local files
- local folders
- GitHub repos and folders
- raw URLs
- multi-source runs
- repomix-reduced inputs when available

It publishes:
- canonical capability manifests
- descriptor JSON files
- repo-resident baseline source snapshots
- overlap/conflict analysis
- quality-loop evidence
- advisory orchestrator handoff metadata

## Read This Next
- [Getting started](GETTING-STARTED.md)
- [CLI reference](CLI-REFERENCE.md)
- [UAC usage](UAC-USAGE.md)
- [UAC capability model](UAC-CAPABILITY-MODEL.md)
- [Baseline source library](../sources/ssot-baselines/README.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
