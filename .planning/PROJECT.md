# Project: Local Intent Sanitizer

## What This Is

Local Intent Sanitizer is a deterministic intent-processing system that currently includes:
- A strict local-file-only ingestion boundary
- Mandatory two-pass sanitization
- Deterministic, roleplay-free intent summary output
- Phase 2 uplift artifacts (context, intent, task decomposition, constraints, and acceptance contract) for downstream phases

Current project status:
- Milestone: `v1.0`
- Completed phases: `2/5` (Phases 1 and 2 complete)
- Completed plans: `6/6` currently defined plans complete
- Next phase: `Phase 3 — Semantic Routing & Rosetta Translation`

## Core Value

Convert local file content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## Requirements

### Delivered

- [x] `INGEST-01`: System accepts input only from local filesystem files.
- [x] `INGEST-02`: System rejects URL/URI/network ingestion paths.
- [x] `SAN-01`: System runs sanitization pass 1 over raw ingested content.
- [x] `SAN-02`: System runs sanitization pass 2 over pass-1 output before summarization.
- [x] `SUM-01`: System produces a clean intent summary from sanitized content.
- [x] `SUM-02`: Output is roleplay-free.
- [x] `SUM-03`: Output is deterministic for identical input and configuration.
- [x] `BOUND-01`: No downstream routing or execution occurs in Phase 1.
- [x] `BOUND-02`: Pipeline ends at summary output in this phase.
- [x] `UPLIFT-CTX`: Context layer output is layered, deterministic, and schema-versioned.
- [x] `UPLIFT-INTENT`: Intent layer is deterministically derived from context with explicit unknown capture.
- [x] `UPLIFT-DECOMP`: Task decomposition emits a deterministic dependency-aware DAG with depth capped at two.
- [x] `UPLIFT-CONSTRAINTS`: Constraint handling uses typed hard/soft models with deterministic conflict resolution.
- [x] `UPLIFT-ACCEPTANCE`: Acceptance evaluation is deterministic and emits criterion-level evidence linked to task IDs.

### Active (Next)

- [ ] `ROUTE-SEM`: Semantic routing behavior and Rosetta translation rules for mapped intents (Phase 3 scope).

### Deferred

- `EXT-01`: URL ingestion with explicit validation and policy controls.
- `EXT-02`: Downstream intent routing/execution after explicit approval.

---
*Last updated: 2026-03-04 after Phase 2*
