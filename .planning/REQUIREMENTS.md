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

- [x] **ROUTE-CTX-01**: Routing accepts only schema-compatible uplift artifacts and rejects unsupported schema majors.
- [x] **ROUTE-ENUM-01**: Route targets are constrained to a closed enum profile set with deterministic serialization.
- [x] **ROUTE-PREC-01**: Signal precedence is fixed as hard constraints > intent > task graph > acceptance.
- [x] **ROUTE-UNK-01**: Ambiguous or incomplete evidence produces deterministic `NEEDS_REVIEW` with explicit missing-evidence fields.
- [x] **ROSETTA-01**: Rosetta translation emits a canonical schema-versioned `route_spec` contract.
- [x] **ROSETTA-02**: Route-spec task/evidence linkage is consistent with uplift task graph and routing provenance.
- [x] **DET-03**: Phase 3 outputs are byte-stable across repeated identical runs.
- [x] **BOUND-03**: Phase 3 excludes target validation, execution/mock execution, output generation, and help rendering.

### Phase 4 Target Validation + Mock Execution + Fallback Degradation

- [x] **VAL-01**: Target validation accepts only typed capability-matrix contracts and rejects freeform capability metadata.
- [x] **VAL-02**: Validation is fail-closed; any blocker deterministically prevents downstream execution stages.
- [x] **VAL-03**: Blocking validation outcomes emit deterministic typed error codes with explicit evidence paths.
- [x] **MOCK-01**: Mock execution remains dry-run only with no runtime/tool side effects.
- [x] **MOCK-02**: Mock execution emits deterministic step-level traces linked to validation and route evidence.
- [x] **FALLBACK-01**: Fallback degradation follows a fixed deterministic tier ladder.
- [x] **FALLBACK-02**: Exhausted fallback deterministically terminates as `NEEDS_REVIEW` with typed terminal codes.
- [x] **DET-04**: Phase 4 outputs are byte-stable for repeated identical inputs.
- [x] **BOUND-04**: Phase 4 excludes real execution, output generation, help rendering, and runtime dependency checks.

### Phase 5 Output Generation + Help Module + Runtime Dependency Checks

- [x] **OUT-01**: Phase 5 emits a typed schema-versioned machine output payload from `Phase4Result` with canonical deterministic serialization.
- [x] **OUT-02**: Phase 5 emits deterministic human-readable output using fixed section order and fixed templates.
- [x] **OUT-03**: Output generation preserves upstream Phase 4 terminal semantics (`NEEDS_REVIEW`) without status mutation.
- [ ] **HELP-01**: Help module uses a closed deterministic topic taxonomy and typed codes.
- [ ] **HELP-02**: Help text is template-driven, roleplay-free, and includes explicit evidence-path references.
- [ ] **HELP-03**: Help responses provide non-executing remediation guidance only.
- [ ] **RUNTIME-01**: Runtime dependency checks are preflight-only and side-effect free.
- [ ] **RUNTIME-02**: Missing required dependencies deterministically produce blocking outcomes with typed reason codes.
- [ ] **RUNTIME-03**: Missing optional dependencies deterministically produce degraded outcomes with typed reason codes.
- [ ] **RUNTIME-04**: Runtime dependency reports are schema-versioned and stably ordered.
- [ ] **DET-05**: Phase 5 artifact serialization is byte-stable across repeated and cross-process identical runs.
- [ ] **BOUND-05**: Phase 5 excludes real execution, auto-remediation, package installation, and network-based dependency/help operations.

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
| ROUTE-CTX-01 | Phase 3 | Complete |
| ROUTE-ENUM-01 | Phase 3 | Complete |
| ROUTE-PREC-01 | Phase 3 | Complete |
| ROUTE-UNK-01 | Phase 3 | Complete |
| ROSETTA-01 | Phase 3 | Complete |
| ROSETTA-02 | Phase 3 | Complete |
| DET-03 | Phase 3 | Complete |
| BOUND-03 | Phase 3 | Complete |
| VAL-01 | Phase 4 | Complete |
| VAL-02 | Phase 4 | Complete |
| VAL-03 | Phase 4 | Complete |
| MOCK-01 | Phase 4 | Complete |
| MOCK-02 | Phase 4 | Complete |
| FALLBACK-01 | Phase 4 | Complete |
| FALLBACK-02 | Phase 4 | Complete |
| DET-04 | Phase 4 | Complete |
| BOUND-04 | Phase 4 | Complete |
| OUT-01 | Phase 5 | Complete |
| OUT-02 | Phase 5 | Complete |
| OUT-03 | Phase 5 | Complete |
| HELP-01 | Phase 5 | Planned |
| HELP-02 | Phase 5 | Planned |
| HELP-03 | Phase 5 | Planned |
| RUNTIME-01 | Phase 5 | Planned |
| RUNTIME-02 | Phase 5 | Planned |
| RUNTIME-03 | Phase 5 | Planned |
| RUNTIME-04 | Phase 5 | Planned |
| DET-05 | Phase 5 | Planned |
| BOUND-05 | Phase 5 | Planned |

**Coverage:**
- Phase-scoped requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0

---
*Requirements defined: 2026-03-04*
*Last updated: 2026-03-05 after Phase 5 research*
