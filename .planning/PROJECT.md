# Project: Local Intent Sanitizer

## What This Is

Local Intent Sanitizer is a deterministic, boundary-first intent-processing pipeline for local input files. v1.0 shipped the full path from local ingestion through output/help/runtime preflight with strict no-execution guarantees. v1.2 focuses on remaining planning hardening gaps: Phase 4 traceability parity and extension-boundary governance.

## Core Value

Convert local file content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## Current Milestone: v1.2 Next

**Goal:** Complete remaining hardening carryover by closing Phase 4 traceability parity and locking extension boundary decisions with deterministic non-go dispositions for `EXT-01` and `EXT-02` in v1.2.

**Target features:**
- Finish Phase 4 requirement-mapping parity and metadata closure (`TRACE-*`).
- Publish finalized deterministic dispositions for `EXT-01` and `EXT-02` (`EXT-01=defer`, `EXT-02=defer`) with governance-only re-entry gates.
- Synchronize scope/boundary language across PROJECT/REQUIREMENTS/ROADMAP.

## Requirements

### Validated

- ✓ Deterministic local intent pipeline from ingestion through output/help/runtime preflight shipped in v1.0.
- ✓ Nyquist validation closure for archived phases 01, 02, 03, and 05.
- ✓ `TRACE-01` / `TRACE-02` / `TRACE-03` completed in Phase 6 with explicit, deterministic evidence parity across summary, roadmap, requirements, and validation/audit artifacts.

### Active

- [x] `EXTG-01`: Record explicit go/defer/reject decision for `EXT-01` and `EXT-02` with deterministic boundary rationale (`EXT-01=defer`, `EXT-02=defer` in Phase 7 Plan 07-01).
- [ ] `EXTG-02`: Synchronize PROJECT/REQUIREMENTS/ROADMAP scope boundaries to extension decisions while preserving no-execution and no-runtime-expansion guarantees; no extension implementation is authorized in v1.2.

### Out of Scope

- Implementing new URL-ingestion runtime paths in v1.2 — this milestone finalizes governance, not new capability build-out.
- Implementing new downstream execution behavior in v1.2 — existing no-execution boundaries remain in force.
- Expanding output/help/runtime feature surface in v1.2 — outside current carryover hardening scope.

## Context

- v1.0 milestone is archived under `.planning/milestones/`.
- Nyquist gap closures for phases 01/02/03/05 were completed before this v1.2 rollover.
- Remaining work is documentation traceability parity and explicit extension policy governance.

## Constraints

- **Determinism**: Hardening artifacts must remain stable across repeated runs.
- **Boundary Safety**: No new runtime execution or network side effects in this milestone.
- **Traceability**: Requirement status must be provable across summaries, requirements, and roadmap.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Start v1.2 now with carryover scope | Continue momentum while reducing active scope to unresolved items only | ✓ Phase 6 traceability closure complete |
| Keep extensions as governance decisions in v1.2 | Avoid accidental capability expansion before explicit policy lock | ✓ `EXT-01` defer, `EXT-02` defer (deterministic non-go in v1.2, governance-only re-entry criteria required) |
| Require explicit canonical requirement IDs for parity closure | Prevent inferred mappings and make regressions detectable in deterministic scans | ✓ Adopted in Phase 6 |

---
*Last updated: 2026-03-05 after Phase 6 transition to Phase 7*
