# Capability Fabric

Capability Fabric is the provider layer for reusable prompt capabilities.

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
- overlap/conflict analysis
- quality-loop evidence
- advisory orchestrator handoff metadata

## Read This Next
- [UAC usage](UAC-USAGE.md)
- [UAC capability model](UAC-CAPABILITY-MODEL.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
