# Milestones

## v1.2 Next (Shipped: 2026-03-06)

**Delivered:** Deterministic traceability parity closure and extension-governance decisions (`EXT-01=defer`, `EXT-02=defer`) with no runtime-scope expansion.

**Phases completed:** 6-7 (6 plans total)

**Key accomplishments:**
- Closed TRACE-01/02/03 with explicit requirement-level parity across summaries, roadmap, requirements, and validation artifacts.
- Published deterministic extension governance rubric and decision matrix for `EXT-01` and `EXT-02`.
- Synchronized boundary-safe defer/defer policy language across PROJECT/REQUIREMENTS/ROADMAP.
- Produced phase-level validation and verification artifacts for phases 06 and 07 with Nyquist-compliant status.

**Archives:**
- [Roadmap Archive](./milestones/v1.2-ROADMAP.md)
- [Requirements Archive](./milestones/v1.2-REQUIREMENTS.md)
- [Audit](./milestones/v1.2-MILESTONE-AUDIT.md)

---

## v1.0 milestone (Shipped: 2026-03-05)

**Delivered:** Deterministic local-intent pipeline from ingestion through output/help/runtime preflight, with strict no-execution boundaries.

**Phases completed:** 1-5 (15 plans total)

**Key accomplishments:**
- Delivered strict local-file ingestion + two-pass sanitization + deterministic roleplay-free summary output.
- Added schema-versioned uplift engine contracts with deterministic context/intent/decomposition/constraints/acceptance outputs.
- Implemented deterministic semantic routing and canonical Rosetta route-spec translation with explicit ambiguity handling.
- Added fail-closed target validation, deterministic dry-run mock execution, and deterministic fallback degradation.
- Delivered deterministic Phase 5 output/help/runtime preflight surfaces with boundary and cross-process determinism guarantees.

**Stats:**
- 467 files changed in milestone implementation range
- 6,473 lines of Python under `src/`
- 5 phases, 15 plans, 45 tasks
- 2 days from first phase feature commit to final phase feature commit (2026-03-04 -> 2026-03-05)

**Git range:** `feat(01-01)` -> `feat(05-03)`

**Known gaps accepted at completion:**
- Phase 4 summary frontmatter requirement mapping gaps (`VAL-01..03`, `MOCK-01..02`, `FALLBACK-01..02`, `DET-04`, `BOUND-04`)
- Nyquist validation partial for phases `01`, `02`, `03`, `05`

**What's next:** Start v1.1 definition with `$gsd-new-milestone`.

---
