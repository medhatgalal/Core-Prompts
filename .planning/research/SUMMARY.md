# Project Research Summary

**Project:** Local Intent Sanitizer
**Domain:** Deterministic extension re-entry for URL ingestion and controlled execution
**Researched:** 2026-03-06
**Confidence:** MEDIUM

## Executive Summary

This research pass scoped v1.3 around controlled re-entry of two previously deferred capabilities: `EXT-01` (URL ingestion) and `EXT-02` (downstream execution). The key recommendation is to treat both as additive, fail-closed extensions layered onto the existing deterministic pipeline, not as a rewrite of shipped local-only behavior.

For `EXT-01`, the highest leverage path is policy-first URL admission with canonical normalization, strict boundary checks, and immutable local snapshots before normal ingestion/sanitization. For `EXT-02`, the recommended path is simulate-first with explicit approval contracts, static route-to-tool mapping, and audit-grade evidence before any execute-eligible behavior is allowed.

Primary risk remains accidental boundary expansion (network, execution, or non-deterministic side effects). Mitigation is to enforce versioned policy artifacts, closed enums/registries, deterministic tie-break rules, and typed fail-closed outcomes (`NEEDS_REVIEW`) whenever approval evidence is incomplete.

## Key Findings

### Recommended Stack

Use Python 3.12 with dependency-light core primitives (`urllib.parse`, `ipaddress`, dataclass contracts) and targeted support (`idna`) for canonical hostname handling. Keep validation centered on deterministic tests (`pytest`) and property-based edge coverage (`hypothesis`) for canonicalization and gate behavior.

**Core technologies:**
- Python 3.12: deterministic contract runtime aligned with existing architecture
- Stdlib URL/IP primitives: canonical policy evaluation and boundary checks
- Dataclass contract model: typed, explicit, replay-safe envelopes

### Expected Features

`EXT-01` and `EXT-02` share mandatory table stakes: fail-closed defaults, explicit policy versioning, closed capability sets, typed error codes, and byte-stable outputs.

**Must have (table stakes):**
- Canonical URL normalization + strict admission policy for `EXT-01`
- Immutable URL snapshot ingestion with provenance and typed rejection paths
- Explicit approval + capability gates for `EXT-02` with `NEEDS_REVIEW` fallback
- Static route-profile to tool mapping and deterministic ledger evidence

**Should have (competitive):**
- Policy snapshot replayability across identical inputs
- Governance-as-code with deterministic rule IDs and auditable traces

**Defer (v2+):**
- Authenticated browsing, recursive crawling, and dynamic rendering
- Open-ended or model-improvised execution tool selection

### Architecture Approach

Integrate extensions at bounded points: `EXT-01` enters as source resolution and policy-gated URL materialization to local snapshot before existing ingestion; `EXT-02` enters as a post-Phase-5 gated stage with approval contracts, static executor registry, idempotency, and audit journaling. Existing Phases 4 and 5 remain non-executing control surfaces.

**Major components:**
1. Source resolver and URL policy gate — classify/normalize/admit URL inputs deterministically
2. Snapshot + provenance envelope — pin content hash and carry evidence across phases
3. Execution authorizer + closed registry + journal — controlled execution eligibility and replay-safe audit evidence

### Critical Pitfalls

1. **Canonicalization drift and redirect trust expansion** — enforce canonical-form policy checks and per-hop re-validation.
2. **SSRF and boundary bypass vectors** — block private/special IP ranges and deny non-approved schemes.
3. **Fail-open execution gates** — execute only when validation + approval + capability constraints all pass.
4. **Dry-run side effects and dynamic tool selection** — keep simulation hermetic and tool mapping static.
5. **Audit/provenance gaps** — require policy version, rule IDs, hashes, and evidence paths in all extension outcomes.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 8: Shared Extension Contracts and Boundary Gates
**Rationale:** shared policy and determinism contracts must exist before either extension can safely expand behavior.
**Delivers:** versioned policy contracts, fail-closed gates, compatibility and boundary invariants.
**Addresses:** cross-cutting table stakes and governance controls.
**Avoids:** fail-open and contradiction-prone scope expansion.

### Phase 9: EXT-01 Deterministic URL Ingestion
**Rationale:** URL ingestion is lower side-effect risk than execution when implemented as policy-gated snapshot ingestion.
**Delivers:** canonical URL admission, snapshot materialization, provenance wiring, deterministic rejection/acceptance outcomes.
**Uses:** URL/IP primitives, typed contracts, boundary tests.
**Implements:** source-resolution and ingestion integration components.

### Phase 10: EXT-02 Simulate-First Controlled Execution
**Rationale:** execution must follow proven contracts and validated provenance to prevent unsafe expansion.
**Delivers:** approval contract gate, closed executor registry, simulate-first default, idempotent audit ledger.
**Uses:** policy contracts and route/validation outputs from prior phases.
**Implements:** execution authorization and deterministic outcome reporting.

### Phase Ordering Rationale

- Shared contracts first ensures both extensions inherit identical deterministic and boundary guarantees.
- URL ingestion before execution limits blast radius while proving policy and provenance controls.
- Execution last ensures higher-risk side-effect surfaces only proceed after controls and evidence chains are mature.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 9:** URL normalization edge semantics and resolver policy tuning.
- **Phase 10:** idempotency/retry semantics for controlled execution adapters.

Phases with standard patterns (skip research-phase):
- **Phase 8:** policy/versioning contracts and fail-closed gate frameworks are established patterns in this codebase.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Based on local architecture fit and deterministic constraints; dependency versions should be validated during implementation |
| Features | HIGH | Table stakes and anti-features are explicit and consistent across research outputs |
| Architecture | HIGH | Integration points and additive component boundaries are clearly identified |
| Pitfalls | HIGH | Risk matrix is concrete, extension-specific, and includes actionable mitigations |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- URL canonicalization policy edge cases (IDN, percent-encoding, default ports) need explicit conformance tests.
- Execution adapter scope and idempotency strategy require concrete target-tool constraints before enabling non-simulated execution.

## Sources

### Primary (HIGH confidence)
- `.planning/research/ARCHITECTURE.md` — extension integration points and build order
- `.planning/research/PITFALLS.md` — extension-specific risk and mitigation matrix
- `.planning/research/FEATURES.md` — table stakes, differentiators, and dependency slicing

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` — stack and tooling fit analysis
- Existing code contracts in `src/intent_pipeline/` — current deterministic design baseline

---
*Research completed: 2026-03-06*
*Ready for roadmap: yes*
