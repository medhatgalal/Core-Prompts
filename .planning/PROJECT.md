# Project: Core-Prompts / Capability Fabric

## What This Is

Core-Prompts is evolving from a deterministic intent-processing pipeline into Capability Fabric: a provider layer that publishes reusable skills, agent surfaces, prompts, commands, descriptors, and advisory handoff metadata for external orchestrators.

## Core Value

Convert source content into safe, deterministic capability artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## Current State

- v1.3 shipped controlled extension re-entry and the deterministic URL / controlled execution baseline.
- Capability Fabric vNext foundation is now in place:
  - layered manifests
  - descriptor sidecars under `.meta/capabilities/`
  - anti-complecting cross-analysis
  - real repo-mutating `apply`
  - repo-family clustering for broad imports
  - repomix-assisted source reduction
  - advisory orchestrator handoff contract
  - thin generated vendor surfaces with bundled resources
- Broad release slice is now in place:
  - built-in UAC quality loop
  - architecture promoted to `both` with advisory artifact-writer agent surfaces
  - smoke validation repaired and made surface-aware
  - shell wrappers standardized on `python3`
  - orchestrator-facing contract and packaging docs added
  - review evidence moved to `reports/quality-reviews/`
- Next product slice: complete remaining SSOT review wave and run the next external family comparisons.

## Active Requirements
- Keep orchestration out of Core-Prompts/UAC.
- Keep `ssot/` human-readable and canonical.
- Keep rich metadata machine-readable in `.meta/capabilities/`.
- Require build + strict validation after every apply.
- Keep deployment explicit and separate from apply.

## Out of Scope
- Runtime routing or delegation.
- Workflow execution engines.
- Autonomous orchestration logic.

---
*Last updated: 2026-03-17 after the broad release slice*
