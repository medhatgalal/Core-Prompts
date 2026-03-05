# Project: Local Intent Sanitizer

## What This Is

Local Intent Sanitizer is a deterministic, boundary-first intent-processing pipeline for local input files. v1.0 shipped the full path from local ingestion through output/help/runtime preflight with strict no-execution guarantees. v1.1 is a hardening milestone focused on traceability, validation completeness, and extension policy clarity.

## Core Value

Convert local file content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## Current Milestone: v1.1 Hardening

**Goal:** Harden v1.0 deliverables by closing traceability and validation debt without expanding runtime behavior.

**Target features:**
- Close Phase 4 summary/frontmatter requirement-mapping gaps.
- Raise Nyquist validation coverage to fully compliant for phases 01, 02, 03, and 05.
- Re-evaluate deferred extensions `EXT-01` and `EXT-02` and record explicit boundary policy.

## Requirements

### Validated

- ✓ Deterministic local intent pipeline from ingestion through output/help/runtime preflight shipped in v1.0.
- ✓ Phase-scoped requirement coverage delivered across phases 1-5 (`INGEST-*` through `BOUND-05`).

### Active

- [ ] `TRACE-01`: Backfill Phase 4 summary metadata so all validation requirements are explicitly mapped.
- [ ] `TRACE-02`: Backfill Phase 4 summary metadata so all mock/fallback requirements are explicitly mapped.
- [ ] `TRACE-03`: Enforce 3-source parity for Phase 4 requirement completion evidence.
- [ ] `NYQ-01`: Close Nyquist validation gaps for Phase 01.
- [ ] `NYQ-02`: Close Nyquist validation gaps for Phase 02.
- [ ] `NYQ-03`: Close Nyquist validation gaps for Phase 03.
- [ ] `NYQ-04`: Close Nyquist validation gaps for Phase 05.
- [ ] `EXTG-01`: Record explicit go/defer/no-go decision for `EXT-01` and `EXT-02` with boundary rationale.
- [ ] `EXTG-02`: Synchronize PROJECT/REQUIREMENTS/ROADMAP scope boundaries to extension decisions.

### Out of Scope

- Implementing new URL-ingestion runtime paths in v1.1 — this milestone is governance and hardening only.
- Implementing new downstream execution behavior in v1.1 — execution boundaries from v1.0 stay intact.
- Introducing non-deterministic output behavior — violates the core contract.

## Context

- v1.0 milestone is fully archived under `.planning/milestones/` with roadmap, requirements, and audit artifacts.
- Remaining debt is documentation/traceability hardening and validation completeness, not missing core runtime capabilities.
- Extension candidates (`EXT-01`, `EXT-02`) remain deferred and require explicit policy before any implementation planning.

## Constraints

- **Determinism**: Any hardening artifact must be stable and reproducible across repeated runs.
- **Boundary Safety**: No new runtime execution or network-side effects may be introduced under hardening scope.
- **Traceability**: Requirement status must be provable through phase summaries and requirement mapping parity.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep v1.1 as hardening-only milestone | Preserve delivery momentum while closing audit debt before new capability work | — Pending |
| Treat `EXT-01` and `EXT-02` as governance items first | Prevent accidental scope expansion before boundary policy is explicit | — Pending |

---
*Last updated: 2026-03-05 after starting milestone v1.1 Hardening*
