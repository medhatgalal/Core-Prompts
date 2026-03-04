# Roadmap: Local Intent Sanitizer

## Overview

Deliver a deterministic, summary-only intent pipeline in Phase 1 by constraining ingestion to local files, enforcing two-pass sanitization, and producing clean roleplay-free intent summaries.

## Phases

- [x] **Phase 1: Local Ingestion + Two-Pass Sanitization + Intent Summary** - Build strict local-only ingestion and summary-only output path. (completed 2026-03-04)

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
| 2. 2026 Uplift Engine (Context/Intent/Task Decomposition/Constraints/Acceptance) | 2/3 | In Progress | - |

### Phase 2: 2026 Uplift Engine (Context/Intent/Task Decomposition/Constraints/Acceptance)

**Goal:** Transform sanitized intent input into deterministic context/intent/task-decomposition/constraint artifacts that can safely feed later routing phases.
**Requirements**: [UPLIFT-CTX, UPLIFT-INTENT, UPLIFT-DECOMP, UPLIFT-CONSTRAINTS]
**Depends on:** Phase 1
**Plans:** 2/3 plans complete

Plans:
- [x] 02-01: Implement deterministic context and intent layers
- [x] 02-02: Implement deterministic task decomposition and constraint resolver
- [ ] 02-03: Implement deterministic acceptance criteria and evidence evaluation

### Phase 3: Semantic Routing & Rosetta Translation

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 2
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 3 to break down)

### Phase 4: Target Tool Validation + Mock Execution + Fallback Degradation

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 3
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 4 to break down)

### Phase 5: Output Generation + Help Module + Runtime Dependency Checks

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 4
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 5 to break down)
