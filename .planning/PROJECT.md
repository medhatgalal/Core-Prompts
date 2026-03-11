# Project: Local Intent Sanitizer

## What This Is

Local Intent Sanitizer is a deterministic, boundary-first intent-processing pipeline that now supports both local files and policy-admitted public raw-text URLs. It converts admitted sources into structured intent artifacts, validates downstream eligibility, and supports simulate-first controlled execution through a hermetic, explicitly approved Phase 6 control plane.

## Core Value

Convert source content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## Current State

- v1.0 shipped the local-only path from ingestion through output/help/runtime preflight with strict no-execution guarantees.
- v1.2 closed traceability and governance debt and established explicit defer decisions for `EXT-01` and `EXT-02`.
- v1.3 shipped controlled extension re-entry:
  - policy-first extension contracts and boundary gates
  - deterministic URL ingestion with immutable snapshots and provenance
  - simulate-first controlled execution with approvals, closed registry mapping, deterministic journal evidence, and hermetic adapter behavior
- Real-source validation now includes:
  - accepted public prompt/spec-style URL flows
  - rejected non-intent-bearing public raw-text sources
  - one-URL end-to-end operator runner via `scripts/run-url-e2e.py`

## Requirements

### Validated

- ✓ Deterministic local-only intent pipeline shipped in v1.0.
- ✓ Traceability parity and governance closure shipped in v1.2.
- ✓ `XDET-01`, `XDET-02`, `XBND-01`, and `XBND-02` shipped in v1.3.
- ✓ `EXT1-01` through `EXT1-05` shipped in v1.3.
- ✓ `EXT2-01` through `EXT2-05` shipped in v1.3.

### Active

- None. Define the next milestone before adding new active requirements.

### Out of Scope

- Authenticated browsing or secret-passthrough retrieval.
- Recursive crawling or multi-document expansion beyond explicit future policy work.
- Autonomous tool selection from free-form model output.
- Implicit execution fallback when approvals are absent.
- Runtime policy mutation without versioned artifact updates.

## Context

- Archived milestone records live under `.planning/milestones/`.
- Release packaging is handled by `scripts/package-surfaces.sh` after build/validate/smoke gates pass.
- The current shipped baseline includes a reusable end-to-end URL runner for operator understanding and validation.

## Constraints

- **Determinism:** identical inputs and policy versions must produce byte-stable decisions and evidence.
- **Boundary Safety:** no fail-open admission or execution paths.
- **Traceability:** every shipped requirement must map to phase evidence and audit artifacts.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use policy-first extension re-entry | Preserves safety while reopening deferred capabilities | ✓ Shipped in v1.3 |
| End URL network behavior at immutable snapshots | Keeps sanitization local and replayable | ✓ Shipped in v1.3 |
| Keep execution simulate-first by default | Prevents accidental side effects while allowing explicit hermetic proof paths | ✓ Shipped in v1.3 |

---
*Last updated: 2026-03-11 after v1.3 shipment*
