# Project: Local Intent Sanitizer

## What This Is

Local Intent Sanitizer is a deterministic, boundary-first intent-processing pipeline for local input files. v1.0 shipped the full path from local ingestion through output/help/runtime preflight with strict no-execution guarantees. v1.2 closed traceability and governance debt by locking `EXT-01` and `EXT-02` as explicit defer decisions.

## Core Value

Convert local and policy-admitted source content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## Current Milestone: v1.3 Controlled Extension Re-entry

**Goal:** Re-enter `EXT-01` and `EXT-02` through deterministic, fail-closed policy contracts and staged rollout gates without regressing existing local-only guarantees.

**Target features:**
- `EXT-01`: policy-gated URL ingestion via canonical normalization and immutable snapshot ingestion.
- `EXT-02`: simulate-first downstream execution gating with explicit approval contracts and closed capability mapping.
- Cross-cutting deterministic governance: versioned policy artifacts, typed evidence paths, and contradiction-free planning traceability.

## Current State

- v1.2 Next shipped on 2026-03-06.
- Phase 4 traceability parity (`TRACE-01/02/03`) is closed with deterministic, auditable evidence.
- Extension governance decisions were finalized in v1.2 as `EXT-01=defer`, `EXT-02=defer`.
- v1.3 is now active to evaluate controlled extension re-entry using explicit re-entry criteria.

## Requirements

### Validated

- ✓ Deterministic local intent pipeline from ingestion through output/help/runtime preflight shipped in v1.0.
- ✓ Nyquist validation closure for archived phases 01, 02, 03, and 05.
- ✓ `TRACE-01` / `TRACE-02` / `TRACE-03` completed in Phase 6 with explicit deterministic evidence parity.
- ✓ `EXTG-01` and `EXTG-02` completed in Phase 7 with synchronized defer/defer governance language.

### Active

- `EXT1-*`: Deterministic URL-ingestion re-entry requirements for policy admission, snapshot provenance, and fail-closed ingestion behavior.
- `EXT2-*`: Controlled execution re-entry requirements for approval contracts, closed registry mapping, and deterministic simulation-first behavior.
- `XDET-*` / `XBND-*`: Cross-cutting determinism and boundary invariants for extension-safe rollout.

### Out of Scope

- Open-ended autonomous execution without explicit approval and capability contracts.
- Authenticated browsing, recursive crawling, or dynamic rendering as part of URL ingestion.
- Runtime policy mutation without versioned and auditable policy artifact updates.

## Context

- v1.0 and v1.2 milestones are archived under `.planning/milestones/`.
- v1.3 planning starts from a shipped no-execution baseline and governance-complete defer decisions.
- Research outputs for v1.3 are captured in `.planning/research/`.

## Constraints

- **Determinism:** Identical inputs and policy versions must produce byte-stable decisions and evidence.
- **Boundary Safety:** No fail-open admission or execution paths; all uncertain states terminate as typed deterministic blocks.
- **Traceability:** Every requirement must map to exactly one roadmap phase with observable closure criteria.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Start v1.3 with policy-first extension re-entry | Preserve safety while unblocking deferred scope under explicit controls | ✓ Accepted |
| Sequence phases as contracts -> URL ingestion -> controlled execution | Lowest-risk ordering that limits blast radius and validates evidence chain first | ✓ Accepted |
| Keep execution simulate-first by default in v1.3 | Avoid accidental side effects until approval and capability gates are proven deterministic | ✓ Accepted |

---
*Last updated: 2026-03-06 at milestone v1.3 kickoff*
