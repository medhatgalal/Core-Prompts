# Requirements: Local Intent Sanitizer

**Defined:** 2026-03-04
**Core Value:** Convert local file content into a safe, deterministic intent summary.

## v1 Requirements

### Ingestion

- [x] **INGEST-01**: System accepts input only from local filesystem files.
- [x] **INGEST-02**: System rejects URL/URI/network ingestion paths.

### Sanitization

- [x] **SAN-01**: System runs sanitization pass 1 over raw ingested content.
- [x] **SAN-02**: System runs sanitization pass 2 over pass-1 output before summarization.

### Intent Summary Output

- [x] **SUM-01**: System produces a clean intent summary from sanitized content.
- [x] **SUM-02**: Output is roleplay-free.
- [x] **SUM-03**: Output is deterministic for identical input and configuration.

### Execution Boundary

- [x] **BOUND-01**: No downstream routing or execution occurs in Phase 1.
- [x] **BOUND-02**: Pipeline ends at summary output in this phase.

## v2 Requirements

### Future Extensions

- **EXT-01**: URL ingestion with explicit validation and policy controls.
- **EXT-02**: Downstream intent routing/execution after explicit approval.

### Phase 2 Uplift Engine

- [x] **UPLIFT-CTX**: Context layer output is layered, deterministic, and schema-versioned.
- [x] **UPLIFT-INTENT**: Intent layer is deterministically derived from context with explicit unknown capture.
- [x] **UPLIFT-DECOMP**: Task decomposition emits a deterministic dependency-aware DAG with depth capped at two.
- [x] **UPLIFT-CONSTRAINTS**: Constraint handling uses typed hard/soft models with deterministic conflict resolution.
- [x] **UPLIFT-ACCEPTANCE**: Acceptance evaluation is deterministic and emits criterion-level evidence linked to task IDs.

### Phase 3 Semantic Routing + Rosetta Translation

- [ ] **ROUTE-CTX-01**: Routing accepts only schema-compatible uplift artifacts and rejects unsupported schema majors.
- [ ] **ROUTE-ENUM-01**: Route targets are constrained to a closed enum profile set with deterministic serialization.
- [ ] **ROUTE-PREC-01**: Signal precedence is fixed as hard constraints > intent > task graph > acceptance.
- [ ] **ROUTE-UNK-01**: Ambiguous or incomplete evidence produces deterministic `NEEDS_REVIEW` with explicit missing-evidence fields.
- [ ] **ROSETTA-01**: Rosetta translation emits a canonical schema-versioned `route_spec` contract.
- [ ] **ROSETTA-02**: Route-spec task/evidence linkage is consistent with uplift task graph and routing provenance.
- [ ] **DET-03**: Phase 3 outputs are byte-stable across repeated identical runs.
- [ ] **BOUND-03**: Phase 3 excludes target validation, execution/mock execution, output generation, and help rendering.

## Out of Scope

| Feature | Reason |
|---------|--------|
| URL ingestion | Explicitly excluded from Phase 1 scope |
| Downstream routing/execution | Explicitly excluded from Phase 1 scope |
| Non-deterministic or roleplay output styles | Violates output contract for Phase 1 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Complete |
| INGEST-02 | Phase 1 | Complete |
| SAN-01 | Phase 1 | Complete |
| SAN-02 | Phase 1 | Complete |
| SUM-01 | Phase 1 | Complete |
| SUM-02 | Phase 1 | Complete |
| SUM-03 | Phase 1 | Complete |
| BOUND-01 | Phase 1 | Complete |
| BOUND-02 | Phase 1 | Complete |
| UPLIFT-CTX | Phase 2 | Complete |
| UPLIFT-INTENT | Phase 2 | Complete |
| UPLIFT-DECOMP | Phase 2 | Complete |
| UPLIFT-CONSTRAINTS | Phase 2 | Complete |
| UPLIFT-ACCEPTANCE | Phase 2 | Complete |
| ROUTE-CTX-01 | Phase 3 | Planned |
| ROUTE-ENUM-01 | Phase 3 | Planned |
| ROUTE-PREC-01 | Phase 3 | Planned |
| ROUTE-UNK-01 | Phase 3 | Planned |
| ROSETTA-01 | Phase 3 | Planned |
| ROSETTA-02 | Phase 3 | Planned |
| DET-03 | Phase 3 | Planned |
| BOUND-03 | Phase 3 | Planned |

**Coverage:**
- Phase-scoped requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0

---
*Requirements defined: 2026-03-04*
*Last updated: 2026-03-04 after Phase 3 planning context*
