# Roadmap: Local Intent Sanitizer

## Milestones

- ✅ **v1.0 milestone** — 5 phases, 15 plans shipped on 2026-03-05 ([Roadmap Archive](./milestones/v1.0-ROADMAP.md), [Requirements Archive](./milestones/v1.0-REQUIREMENTS.md), [Audit](./milestones/v1.0-MILESTONE-AUDIT.md))
- 💤 **v1.1 Hardening** — Superseded before execution
- 🚧 **v1.2 Next** — Active

## Active Roadmap

### Overview

Complete remaining hardening carryover by closing Phase 4 traceability mapping parity and finalizing extension governance decisions (`EXT-01=defer`, `EXT-02=defer`), without introducing new runtime capability behavior.

### Phases

- [x] **Phase 6: Phase 4 Traceability Metadata Backfill** - Close missing requirement mappings and enforce explicit 3-source parity for `VAL-01`, `VAL-02`, `VAL-03`, `MOCK-01`, `MOCK-02`, `FALLBACK-01`, `FALLBACK-02`, `DET-04`, and `BOUND-04`.
- [ ] **Phase 7: Extension Governance Decision Pack (`EXT-01`, `EXT-02`)** - Publish deterministic non-go dispositions (`defer`/`defer`) and synchronize boundary scope language across planning docs.

### Phase Details

#### Phase 6: Phase 4 Traceability Metadata Backfill
**Goal:** Backfill and verify explicit Phase 4 requirement completion metadata for strict parity across planning artifacts.
**Depends on:** Nothing (first phase of v1.2)
**Requirements:** [TRACE-01, TRACE-02, TRACE-03]
**Success Criteria:**
  1. Phase 4 summary/frontmatter explicitly maps `VAL-01`, `VAL-02`, `VAL-03`, `MOCK-01`, `MOCK-02`, `FALLBACK-01`, `FALLBACK-02`, `DET-04`, and `BOUND-04`.
  2. Requirement statuses in summary, roadmap, and requirements docs are deterministic and ID-level consistent.
  3. Evidence references are deterministic and auditable.
**Plans:** 3/3 plans complete

Plans:
- [x] 06-01: Inventory and patch missing Phase 4 requirement metadata entries
- [x] 06-02: Reconcile requirement mapping parity across summary/roadmap/requirements
- [x] 06-03: Validate deterministic evidence references and finalize Phase 6 summary

#### Phase 7: Extension Governance Decision Pack (`EXT-01`, `EXT-02`)
**Goal:** Lock deterministic extension dispositions for v1.2 (`EXT-01=defer`, `EXT-02=defer`) and publish future-milestone staging policy with boundary-safe wording.
**Depends on:** Phase 6
**Requirements:** [EXTG-01, EXTG-02]
**Success Criteria:**
  1. `EXT-01` and `EXT-02` each have explicit deterministic dispositions (`defer`, `defer`) and rationale.
  2. PROJECT, REQUIREMENTS, and ROADMAP documents contain synchronized boundary decisions.
  3. Any extension implementation work is explicitly staged for a future milestone behind re-entry criteria.
**Plans:** 2/3 plans executed

Plans:
- [x] 07-01: Define decision rubric and evaluate `EXT-01`/`EXT-02`
- [x] 07-02: Publish governance decisions with deterministic boundary statements
- [ ] 07-03: Propagate final decisions to planning documents and verify consistency

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 6. Phase 4 Traceability Metadata Backfill | 3/3 | Complete | 2026-03-05 |
| 7. Extension Governance Decision Pack (`EXT-01`, `EXT-02`) | 2/3 | In Progress|  |
