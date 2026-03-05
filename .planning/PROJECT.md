# Project: Local Intent Sanitizer

## What This Is

Local Intent Sanitizer is a deterministic, boundary-first intent-processing pipeline for local input files. v1.0 shipped the full path from local ingestion through output/help/runtime preflight with strict no-execution guarantees. v1.2 focuses on remaining planning hardening gaps: Phase 4 traceability parity and extension-boundary governance.

## Core Value

Convert local file content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## Current Milestone: v1.2 Next

**Goal:** Complete remaining hardening carryover by closing Phase 4 traceability parity and locking extension boundary decisions.

**Target features:**
- Finish Phase 4 requirement-mapping parity and metadata closure (`TRACE-*`).
- Record deterministic go/defer/reject decisions for `EXT-01` and `EXT-02` (`EXTG-*`).
- Synchronize scope/boundary language across PROJECT/REQUIREMENTS/ROADMAP.

## Requirements

### Validated

- ✓ Deterministic local intent pipeline from ingestion through output/help/runtime preflight shipped in v1.0.
- ✓ Nyquist validation closure for archived phases 01, 02, 03, and 05.

### Active

- [ ] `TRACE-01`: Backfill Phase 4 summary metadata so all validation requirements are explicitly mapped.
- [ ] `TRACE-02`: Backfill Phase 4 summary metadata so all mock/fallback requirements are explicitly mapped.
- [ ] `TRACE-03`: Enforce 3-source parity for Phase 4 requirement completion evidence.
- [ ] `EXTG-01`: Record explicit go/defer/no-go decision for `EXT-01` and `EXT-02` with boundary rationale.
- [ ] `EXTG-02`: Synchronize PROJECT/REQUIREMENTS/ROADMAP scope boundaries to extension decisions.

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
| Start v1.2 now with carryover scope | Continue momentum while reducing active scope to unresolved items only | — Pending |
| Keep extensions as governance decisions in v1.2 | Avoid accidental capability expansion before explicit policy lock | — Pending |

---
*Last updated: 2026-03-05 after starting milestone v1.2 Next (carryover scope)*
