---
phase: 09-ext-01-deterministic-url-ingestion
plan: "02"
subsystem: ingestion
tags: [url-ingestion, snapshot, pipeline, bounded-fetch]
requires:
  - phase: 09-01
    provides: canonical URL normalization and explicit URL admission policy
provides:
  - Immutable content-addressed URL snapshot materialization
  - Bounded fetch path with redirect revalidation and address-safety enforcement
  - Phase-1 pipeline integration that reads approved URL content from local snapshots only
affects: [phase1-pipeline, ingestion-reader, phase2-provenance]
tech-stack:
  added: []
  patterns: [snapshot-first ingestion, public-address enforcement, local-read-only sanitize flow]
key-files:
  created:
    - src/intent_pipeline/ingestion/url_snapshot_store.py
    - tests/test_url_snapshot_store.py
    - tests/test_url_ingestion_pipeline.py
  modified:
    - src/intent_pipeline/ingestion/reader.py
    - src/intent_pipeline/pipeline.py
key-decisions:
  - "Approved URL responses are materialized to local content-addressed snapshots before sanitization."
  - "Redirect hops are re-resolved and revalidated against URL policy on every transition."
patterns-established:
  - "URL ingestion remains bounded and deterministic by ending the network boundary at snapshot creation."
  - "Phase-1 summary output remains unchanged for local inputs while approved URLs flow through the same sanitize and summary path."
requirements-completed: [EXT1-02, EXT1-03, EXT1-04]
completed: 2026-03-06
---

# Phase 9 Plan 02: Snapshot Ingestion Summary

**Approved URL sources now enter the pipeline only through bounded retrieval and immutable local snapshots.**

## Accomplishments
- Added `url_snapshot_store.py` with bounded stdlib transport, redirect handling, IP boundary checks, and content-addressed snapshot writes.
- Added `read_snapshot_text` to keep downstream sanitize flow local-file-only.
- Reworked the phase-1 pipeline to ingest URL sources through shared gate approval, URL policy, snapshot materialization, and local snapshot reads.
- Added snapshot and approved/rejected pipeline integration tests.

## Verification
- `pytest -q tests/test_url_snapshot_store.py tests/test_url_ingestion_pipeline.py`
- `pytest -q tests/test_ingestion_boundary.py tests/test_phase_boundary.py`

## Notes
- No git task commits were created during execution; changes remain in the current branch worktree.

---
*Phase: 09-ext-01-deterministic-url-ingestion*
*Completed: 2026-03-06*
