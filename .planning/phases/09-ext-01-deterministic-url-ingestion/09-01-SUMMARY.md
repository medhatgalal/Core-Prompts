---
phase: 09-ext-01-deterministic-url-ingestion
plan: "01"
subsystem: ingestion
tags: [url-ingestion, resolver, policy, boundary, fail-closed]
requires: []
provides:
  - Deterministic source classification and canonical URL normalization
  - Explicit URL admission policy contracts with typed fail-closed rejection semantics
  - Boundary tests proving rejected URLs stop before sanitize or fetch continuation
affects: [phase1-pipeline, phase2-provenance, phase-10-ext-02-controlled-execution]
tech-stack:
  added: []
  patterns: [resolver-before-policy, typed rejection codes, canonical normalization]
key-files:
  created:
    - src/intent_pipeline/ingestion/source_resolver.py
    - src/intent_pipeline/ingestion/url_policy.py
    - tests/test_url_source_resolver.py
    - tests/test_url_policy_contracts.py
    - tests/test_url_ingestion_boundary.py
  modified:
    - src/intent_pipeline/ingestion/policy.py
key-decisions:
  - "Canonical URL normalization happens before any admission-policy decision."
  - "URL-policy parsing fails closed and returns deterministic NEEDS_REVIEW-style rejection evidence."
patterns-established:
  - "Local-file validation reuses the shared source resolver to keep classification logic single-sourced."
  - "URL rejection paths are typed and terminate before sanitize."
requirements-completed: [EXT1-01, EXT1-02, EXT1-04]
completed: 2026-03-06
---

# Phase 9 Plan 01: Deterministic URL Ingestion Summary

**Phase 9 now has a deterministic front door: source resolution, canonical URL normalization, and explicit URL admission policy checks.**

## Accomplishments
- Added `source_resolver.py` to classify local paths vs URLs and canonicalize supported `http`/`https` sources.
- Added `url_policy.py` with typed policy contracts, rejection codes, and fail-closed parsing/evaluation behavior.
- Updated local ingestion policy to reuse shared source resolution.
- Added focused tests for canonicalization, policy validation, and early rejection behavior.

## Verification
- `pytest -q tests/test_url_source_resolver.py tests/test_url_policy_contracts.py tests/test_url_ingestion_boundary.py`

## Notes
- No git task commits were created during execution; changes remain in the current branch worktree.

---
*Phase: 09-ext-01-deterministic-url-ingestion*
*Completed: 2026-03-06*
