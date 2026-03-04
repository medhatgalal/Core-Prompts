# Roadmap: Local Intent Sanitizer

## Overview

Deliver a deterministic, summary-only intent pipeline in Phase 1 by constraining ingestion to local files, enforcing two-pass sanitization, and producing clean roleplay-free intent summaries.

## Phases

- [ ] **Phase 1: Local Ingestion + Two-Pass Sanitization + Intent Summary** - Build strict local-only ingestion and summary-only output path.

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
**Plans:** TBD

Plans:
- [x] 01-01: Implement local-file ingestion boundary and validation
- [x] 01-02: Implement two-pass sanitization pipeline
- [ ] 01-03: Implement deterministic roleplay-free intent summary output

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Local Ingestion + Two-Pass Sanitization + Intent Summary | 2/3 | In Progress | - |
