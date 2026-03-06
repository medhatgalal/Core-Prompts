# Requirements: Local Intent Sanitizer

**Defined:** 2026-03-06
**Core Value:** Convert local and policy-admitted source content into safe, deterministic intent artifacts that preserve explicit boundaries, traceability, and stable decision semantics.

## v1 Requirements

### URL Ingestion Re-entry (`EXT-01`)

- [ ] **EXT1-01**: System canonicalizes URL input to a single normalized form before any admission-policy decision.
- [ ] **EXT1-02**: System evaluates URL admission against explicit allow/deny policy dimensions (scheme, host/domain, path, content type, size, redirect budget, timeout budget) and fails closed with typed rejection codes.
- [ ] **EXT1-03**: Approved URL inputs are materialized into immutable local snapshots identified by content hash before downstream sanitization.
- [ ] **EXT1-04**: Rejected or policy-incomplete URL inputs never enter sanitization or downstream phases and deterministically terminate as `NEEDS_REVIEW` with evidence paths.
- [ ] **EXT1-05**: URL-sourced payloads carry deterministic provenance fields (`source_type`, `normalized_source`, `policy_rule_id`, `content_hash`) through Phase 5 outputs.

### Controlled Execution Re-entry (`EXT-02`)

- [ ] **EXT2-01**: System permits execute-eligible flow only when route validation passes, fallback state is execute-eligible, and explicit execution approval contract is present and valid.
- [ ] **EXT2-02**: Route-profile to executor/tool mapping is closed and static; unmapped or ambiguous mappings deterministically block execution.
- [ ] **EXT2-03**: Default extension behavior is simulate-first; missing approvals, capability mismatches, or policy gaps deterministically return `NEEDS_REVIEW` without side effects.
- [ ] **EXT2-04**: Execution attempts (including blocked attempts) produce deterministic evidence entries with idempotency key, policy version, decision code, and trace references.
- [ ] **EXT2-05**: Dry-run/mock execution paths remain side-effect free and are enforced by boundary checks that reject network/process/file-mutation behaviors.

### Cross-Cutting Determinism and Boundary Invariants

- [ ] **XDET-01**: Extension decisions are byte-stable across repeated identical input, configuration, and policy-version runs.
- [ ] **XDET-02**: Policy artifacts are explicitly versioned and include stable rule IDs used by deterministic evidence outputs.
- [ ] **XBND-01**: Local-file-only behavior remains unchanged when extension modes are disabled.
- [ ] **XBND-02**: v1.3 excludes recursive crawling, authenticated browsing, open-ended shell execution, and dynamic runtime capability expansion.

## v2 Requirements

### Deferred Expansion

- **EXT1-06**: Support authenticated URL retrieval profiles with explicit secret-scope contracts.
- **EXT1-07**: Support bounded multi-document URL collection under deterministic crawl policy.
- **EXT2-06**: Permit limited write-capable execution profiles after adapter-specific rollback/idempotency proof.
- **EXT2-07**: Add multi-tool transactional orchestration with deterministic conflict resolution semantics.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Browser-rendered ingestion (JS execution) | Breaks deterministic retrieval assumptions and expands attack surface |
| Autonomous tool selection from free-form model output | Violates closed capability mapping boundary |
| Implicit execution fallback when approvals are missing | Conflicts with fail-closed deterministic guardrails |
| Runtime mutation of policy without version bump | Breaks replayability and audit trace consistency |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXT1-01 | Phase TBD | Pending |
| EXT1-02 | Phase TBD | Pending |
| EXT1-03 | Phase TBD | Pending |
| EXT1-04 | Phase TBD | Pending |
| EXT1-05 | Phase TBD | Pending |
| EXT2-01 | Phase TBD | Pending |
| EXT2-02 | Phase TBD | Pending |
| EXT2-03 | Phase TBD | Pending |
| EXT2-04 | Phase TBD | Pending |
| EXT2-05 | Phase TBD | Pending |
| XDET-01 | Phase TBD | Pending |
| XDET-02 | Phase TBD | Pending |
| XBND-01 | Phase TBD | Pending |
| XBND-02 | Phase TBD | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 0
- Unmapped: 14 ⚠️

---
*Requirements defined: 2026-03-06*
*Last updated: 2026-03-06 after milestone v1.3 definition kickoff*
