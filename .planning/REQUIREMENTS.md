# Requirements: Local Intent Sanitizer

**Defined:** 2026-03-05
**Core Value:** Convert local file content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## v1 Requirements

### Phase 4 Traceability Hardening

- [x] **TRACE-01**: Phase 4 summary metadata explicitly marks `VAL-01`, `VAL-02`, and `VAL-03` as completed with requirement-level evidence.
- [x] **TRACE-02**: Phase 4 summary metadata explicitly marks `MOCK-01`, `MOCK-02`, `FALLBACK-01`, and `FALLBACK-02` as completed with requirement-level evidence.
- [x] **TRACE-03**: Phase 4 completion evidence is explicit and synchronized for `VAL-01`, `VAL-02`, `VAL-03`, `MOCK-01`, `MOCK-02`, `FALLBACK-01`, `FALLBACK-02`, `DET-04`, and `BOUND-04` across requirements, roadmap, and summary metadata surfaces.

### Extension Governance

- [x] **EXTG-01**: Milestone records explicit disposition (`go`, `defer`, or `reject`) for `EXT-01` and `EXT-02` with deterministic boundary rationale (`EXT-01=defer`, `EXT-02=defer` per Phase 7 decision matrix).
- [x] **EXTG-02**: Extension decisions are synchronized across PROJECT/REQUIREMENTS/ROADMAP with no contradictory scope language, explicit `EXT-01=defer` and `EXT-02=defer` dispositions, and no v1.2 runtime-scope expansion.

## v2 Requirements

### Deferred Extensions

- **EXT-01**: URL ingestion with explicit validation and policy controls.
  - Decision now (v1.2): `defer` (deterministic non-go).
  - Re-entry criteria (future milestone): approved URL policy contract, deterministic validation matrix, and boundary tests proving no unauthorized side-effect expansion.
- **EXT-02**: Downstream intent routing/execution after explicit approval.
  - Decision now (v1.2): `defer` (deterministic non-go).
  - Re-entry criteria (future milestone): approved execution authorization policy, deterministic side-effect guardrails, and repeatable verification for boundary stress cases.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Implementing URL ingestion runtime behavior | v1.2 is governance/traceability hardening only |
| Implementing downstream execution behavior | Existing no-execution boundaries remain active |
| Expanding output/help/runtime feature surface | Not required to close current carryover hardening debt |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRACE-01 | Phase 6 | Complete |
| TRACE-02 | Phase 6 | Complete |
| TRACE-03 | Phase 6 | Complete |
| EXTG-01 | Phase 7 | Complete |
| EXTG-02 | Phase 7 | Complete |

**Extension governance traceability anchors:**
- `EXT-01`: defer in v1.2, staged behind explicit policy/verification re-entry criteria.
- `EXT-02`: defer in v1.2, staged behind execution authorization and deterministic guardrail criteria.

**Coverage:**
- v1 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0

---
*Requirements defined: 2026-03-05*
*Last updated: 2026-03-05 after Phase 7 Plan 07-01 decision anchoring*
