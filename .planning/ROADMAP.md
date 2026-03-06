# Roadmap: Local Intent Sanitizer

## Milestones

- ✅ **v1.2 Next** — 2 phases, 6 plans shipped on 2026-03-06 ([Roadmap Archive](./milestones/v1.2-ROADMAP.md), [Requirements Archive](./milestones/v1.2-REQUIREMENTS.md), [Audit](./milestones/v1.2-MILESTONE-AUDIT.md))
- ✅ **v1.0 milestone** — 5 phases, 15 plans shipped on 2026-03-05 ([Roadmap Archive](./milestones/v1.0-ROADMAP.md), [Requirements Archive](./milestones/v1.0-REQUIREMENTS.md), [Audit](./milestones/v1.0-MILESTONE-AUDIT.md))
- 💤 **v1.1 Hardening** — Superseded before execution
- 🚧 **v1.3 Controlled Extension Re-entry** — Active

## Active Roadmap

### Overview

Implement controlled re-entry for `EXT-01` and `EXT-02` using a policy-first, fail-closed sequence that preserves deterministic local-only baseline behavior while introducing URL ingestion and execution gating in bounded stages.

### Phases

- [x] **Phase 8: Shared Extension Contracts and Boundary Gates** - Establish versioned policy contracts, deterministic decision invariants, and extension-safe boundary defaults.
- [ ] **Phase 9: EXT-01 Deterministic URL Ingestion** - Add canonical URL admission, immutable snapshot ingestion, and provenance-safe integration into existing sanitization flow.
- [ ] **Phase 10: EXT-02 Simulate-First Controlled Execution** - Add explicit execution approval contracts, closed executor mapping, deterministic journal evidence, and side-effect-safe simulation guardrails.

### Phase Details

#### Phase 8: Shared Extension Contracts and Boundary Gates
**Goal:** Define and enforce shared fail-closed contracts and deterministic invariants required before enabling any extension behavior.
**Depends on:** Nothing (first phase of v1.3)
**Requirements:** [XDET-01, XDET-02, XBND-01, XBND-02]
**Success Criteria:**
  1. Versioned policy artifacts with stable rule IDs exist and are required by extension decision surfaces.
  2. Determinism checks confirm identical input + policy versions produce byte-stable extension decisions.
  3. Local-file baseline behavior remains unchanged when extension modes are disabled and forbidden expansion paths stay blocked.
**Plans:** 3/3 plans complete

Plans:
- [x] 08-01: Define shared policy/versioning contracts and deterministic serialization rules
- [x] 08-02: Implement fail-closed boundary gates and extension mode defaults
- [x] 08-03: Add deterministic/boundary regression suite for shared extension invariants

#### Phase 9: EXT-01 Deterministic URL Ingestion
**Goal:** Introduce policy-admitted URL ingestion as immutable local snapshot input without regressing two-pass sanitization and downstream determinism.
**Depends on:** Phase 8
**Requirements:** [EXT1-01, EXT1-02, EXT1-03, EXT1-04, EXT1-05]
**Success Criteria:**
  1. URL normalization and admission policy decisions are deterministic, typed, and fail closed.
  2. Approved URL payloads are ingested through immutable local snapshots with canonical provenance metadata.
  3. Rejected URLs terminate deterministically with explicit evidence and never enter sanitization or routing paths.
**Plans:** 0/3 plans complete

Plans:
- [ ] 09-01: Implement canonical source resolver and URL admission policy gate
- [ ] 09-02: Implement immutable URL snapshot ingestion and provenance envelope wiring
- [ ] 09-03: Add deterministic and boundary tests for URL rejection/acceptance paths

#### Phase 10: EXT-02 Simulate-First Controlled Execution
**Goal:** Add controlled execution eligibility and evidence flow while keeping default behavior simulate-first and fail closed.
**Depends on:** Phase 9
**Requirements:** [EXT2-01, EXT2-02, EXT2-03, EXT2-04, EXT2-05]
**Success Criteria:**
  1. Execution path is unreachable without valid approval contract, capability match, and execute-eligible validation state.
  2. Route-to-executor mapping is closed/static and ambiguous mappings deterministically block execution.
  3. Simulation remains side-effect free and all execution decisions emit deterministic audit entries with idempotency evidence.
**Plans:** 0/3 plans complete

Plans:
- [ ] 10-01: Implement execution approval contracts and closed executor registry mapping
- [ ] 10-02: Implement simulate-first gating and deterministic `NEEDS_REVIEW` fallback for unmet invariants
- [ ] 10-03: Implement execution evidence journal, idempotency checks, and boundary enforcement tests

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. Shared Extension Contracts and Boundary Gates | 3/3 | Complete | 2026-03-06 |
| 9. EXT-01 Deterministic URL Ingestion | 0/3 | Pending | — |
| 10. EXT-02 Simulate-First Controlled Execution | 0/3 | Pending | — |
