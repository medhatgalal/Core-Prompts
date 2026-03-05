# Roadmap: Local Intent Sanitizer

## Milestones

- ✅ **v1.0 milestone** — 5 phases, 15 plans shipped on 2026-03-05 ([Roadmap Archive](./milestones/v1.0-ROADMAP.md), [Requirements Archive](./milestones/v1.0-REQUIREMENTS.md), [Audit](./milestones/v1.0-MILESTONE-AUDIT.md))
- 🚧 **v1.1 Hardening** — Active

## Active Roadmap

### Overview

Harden the shipped v1.0 pipeline by closing traceability metadata gaps, completing Nyquist validation coverage, and finalizing explicit policy for deferred extensions without expanding runtime behavior.

### Phases

- [ ] **Phase 6: Phase 4 Traceability Metadata Backfill** - Close missing requirement mappings and enforce 3-source parity for Phase 4 completion evidence.
- [ ] **Phase 7: Nyquist Validation Closure (Phases 01/02/03/05)** - Eliminate remaining Nyquist validation gaps for shipped phases.
- [ ] **Phase 8: Extension Governance Decision Pack (`EXT-01`, `EXT-02`)** - Produce explicit boundary-policy decisions and synchronize scope language across planning docs.

### Phase Details

#### Phase 6: Phase 4 Traceability Metadata Backfill
**Goal:** Backfill and verify Phase 4 requirement completion metadata for strict parity across planning artifacts.
**Depends on:** Nothing (first phase of v1.1)
**Requirements:** [TRACE-01, TRACE-02, TRACE-03]
**Success Criteria:**
  1. Phase 4 summary/frontmatter includes completion mapping for all required validation, mock, fallback, determinism, and boundary requirements.
  2. Requirement statuses in summary, roadmap, and requirements docs are consistent.
  3. Evidence references are deterministic and auditable.
**Plans:** 0/3 plans complete

Plans:
- [ ] 06-01: Inventory and patch missing Phase 4 requirement metadata entries
- [ ] 06-02: Reconcile requirement mapping parity across summary/roadmap/requirements
- [ ] 06-03: Validate deterministic evidence references and finalize Phase 6 summary

#### Phase 7: Nyquist Validation Closure (Phases 01/02/03/05)
**Goal:** Close remaining Nyquist validation gaps for previously shipped phases without altering feature behavior.
**Depends on:** Phase 6
**Requirements:** [NYQ-01, NYQ-02, NYQ-03, NYQ-04]
**Success Criteria:**
  1. Each targeted phase has complete Nyquist validation artifacts.
  2. No open Nyquist gap markers remain for phases 01, 02, 03, or 05.
  3. Validation outcomes are traceable to concrete phase artifacts.
**Plans:** 0/3 plans complete

Plans:
- [ ] 07-01: Build gap matrix and required validation artifact checklist
- [ ] 07-02: Generate/patch missing validation artifacts for phases 01, 02, 03, and 05
- [ ] 07-03: Verify zero-gap Nyquist state and publish Phase 7 closure report

#### Phase 8: Extension Governance Decision Pack (`EXT-01`, `EXT-02`)
**Goal:** Finalize deterministic go/defer/reject decisions for deferred extensions and lock boundary language for future milestones.
**Depends on:** Phase 7
**Requirements:** [EXTG-01, EXTG-02]
**Success Criteria:**
  1. `EXT-01` and `EXT-02` each have explicit disposition and rationale.
  2. PROJECT, REQUIREMENTS, and ROADMAP documents contain synchronized boundary decisions.
  3. Any deferred extension work is clearly staged for a future milestone.
**Plans:** 0/3 plans complete

Plans:
- [ ] 08-01: Define decision rubric and evaluate `EXT-01`/`EXT-02`
- [ ] 08-02: Publish governance decisions with deterministic boundary statements
- [ ] 08-03: Propagate final decisions to planning documents and verify consistency

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 6. Phase 4 Traceability Metadata Backfill | 0/3 | Not started | — |
| 7. Nyquist Validation Closure (Phases 01/02/03/05) | 0/3 | Not started | — |
| 8. Extension Governance Decision Pack (`EXT-01`, `EXT-02`) | 0/3 | Not started | — |
