# Roadmap: Local Intent Sanitizer

## Overview

Deliver a deterministic, summary-only intent pipeline in Phase 1 by constraining ingestion to local files, enforcing two-pass sanitization, and producing clean roleplay-free intent summaries.

## Phases

- [x] **Phase 1: Local Ingestion + Two-Pass Sanitization + Intent Summary** - Build strict local-only ingestion and summary-only output path. (completed 2026-03-04)
- [x] **Phase 2: 2026 Uplift Engine (Context/Intent/Task Decomposition/Constraints/Acceptance)** - Build deterministic uplift artifacts from sanitized inputs. (completed 2026-03-04)
- [x] **Phase 3: Semantic Routing & Rosetta Translation** - Build deterministic semantic routing and canonical route-spec translation. (completed 2026-03-05)
- [ ] **Phase 4: Target Tool Validation + Mock Execution + Fallback Degradation** - Build fail-closed target validation, dry-run mock execution, and deterministic fallback handling.
- [ ] **Phase 5: Output Generation + Help Module + Runtime Dependency Checks** - Build final output/help/runtime dependency surfaces.

## Phase Details

### Phase 1: Local Ingestion + Two-Pass Sanitization + Intent Summary
**Goal:** Deliver Phase 1 with strict local-file ingestion, two-pass sanitization, and clean deterministic intent summaries while excluding URL ingestion and downstream execution.
**Depends on:** Nothing (first phase)
**Requirements**: [INGEST-01, INGEST-02, SAN-01, SAN-02, SUM-01, SUM-02, SUM-03, BOUND-01, BOUND-02]
**Success Criteria:** (what must be TRUE)
  1. Inputs are accepted only from local file paths.
  2. URL/URI/network ingestion attempts are rejected.
  3. Sanitization always runs as two passes before summary generation.
  4. Output is clean, deterministic, and roleplay-free.
  5. No downstream routing or execution is performed in this phase.
**Plans:** 3/3 plans complete

Plans:
- [x] 01-01: Implement local-file ingestion boundary and validation
- [x] 01-02: Implement two-pass sanitization pipeline
- [x] 01-03: Implement deterministic roleplay-free intent summary output

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Local Ingestion + Two-Pass Sanitization + Intent Summary | 3/3 | Complete   | 2026-03-04 |
| 2. 2026 Uplift Engine (Context/Intent/Task Decomposition/Constraints/Acceptance) | 3/3 | Complete | 2026-03-04 |
| 3. Semantic Routing & Rosetta Translation | 3/3 | Complete | 2026-03-05 |
| 4. Target Tool Validation + Mock Execution + Fallback Degradation | 3/3 | Complete | 2026-03-05 |
| 5. Output Generation + Help Module + Runtime Dependency Checks | 0/0 | Planned | - |

### Phase 2: 2026 Uplift Engine (Context/Intent/Task Decomposition/Constraints/Acceptance)

**Goal:** Transform sanitized intent input into deterministic context/intent/task-decomposition/constraint artifacts that can safely feed later routing phases.
**Requirements**: [UPLIFT-CTX, UPLIFT-INTENT, UPLIFT-DECOMP, UPLIFT-CONSTRAINTS, UPLIFT-ACCEPTANCE]
**Depends on:** Phase 1
**Plans:** 3/3 plans complete

Plans:
- [x] 02-01: Implement deterministic context and intent layers
- [x] 02-02: Implement deterministic task decomposition and constraint resolver
- [x] 02-03: Implement deterministic acceptance criteria and evidence evaluation

### Phase 3: Semantic Routing & Rosetta Translation

**Goal:** Build a deterministic semantic routing layer and canonical Rosetta route-spec translation over Phase 2 uplift artifacts, without introducing validation/execution/output-generation concerns.
**Requirements**: [ROUTE-CTX-01, ROUTE-ENUM-01, ROUTE-PREC-01, ROUTE-UNK-01, ROSETTA-01, ROSETTA-02, DET-03, BOUND-03]
**Depends on:** Phase 2
**Plans:** 3/3 plans complete

Plans:
- [x] 03-01: Implement routing contracts and uplift signal normalization
- [x] 03-02: Implement deterministic semantic router precedence and ambiguity handling
- [x] 03-03: Implement Rosetta route-spec translation and Phase 3 integration boundary guards

### Phase 4: Target Tool Validation + Mock Execution + Fallback Degradation

**Goal:** Add deterministic, fail-closed target validation and dry-run mock execution with fixed fallback degradation, while explicitly excluding output/help/runtime-check concerns.
**Requirements**: [VAL-01, VAL-02, VAL-03, MOCK-01, MOCK-02, FALLBACK-01, FALLBACK-02, DET-04, BOUND-04]
**Depends on:** Phase 3
**Plans:** 3/3 plans complete

Plans:
- [x] 04-01: Implement typed contracts and fail-closed target validation
- [x] 04-02: Implement deterministic dry-run mock execution
- [x] 04-03: Implement fixed fallback degradation and Phase 4 composition engine

### Phase 5: Output Generation + Help Module + Runtime Dependency Checks

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 4
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 5 to break down)
