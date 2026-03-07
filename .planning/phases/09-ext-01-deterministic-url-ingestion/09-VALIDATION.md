---
phase: 09
slug: ext-01-deterministic-url-ingestion
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-06
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for bounded URL-ingestion re-entry.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — direct pytest invocation |
| **Quick run command** | `pytest -q tests/test_url_source_resolver.py tests/test_url_policy_contracts.py tests/test_url_ingestion_boundary.py` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~180 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q tests/test_url_source_resolver.py tests/test_url_policy_contracts.py tests/test_url_ingestion_boundary.py`
- **After every plan wave:** Run `pytest -q tests/test_url_snapshot_store.py tests/test_url_ingestion_pipeline.py tests/test_uplift_engine_context.py`
- **Before verification:** Run `pytest -q`
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | EXT1-01 | unit | `pytest -q tests/test_url_source_resolver.py::test_url_resolver_canonicalizes_http_variants_to_one_form` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | EXT1-02 | unit | `pytest -q tests/test_url_policy_contracts.py::test_url_policy_requires_explicit_rule_dimensions` | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | EXT1-04 | integration | `pytest -q tests/test_url_ingestion_boundary.py::test_rejected_url_never_reaches_sanitizer` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | EXT1-03 | unit | `pytest -q tests/test_url_snapshot_store.py::test_snapshot_store_materializes_content_addressed_file` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | EXT1-02 | integration | `pytest -q tests/test_url_snapshot_store.py::test_redirect_targets_are_revalidated_against_policy` | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 2 | EXT1-03 | integration | `pytest -q tests/test_url_ingestion_pipeline.py::test_approved_url_pipeline_reads_snapshot_not_live_stream` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 3 | EXT1-05 | unit | `pytest -q tests/test_uplift_engine_context.py::test_context_layer_preserves_url_provenance_fields` | ❌ W0 | ⬜ pending |
| 09-03-02 | 03 | 3 | EXT1-04 | integration | `pytest -q tests/test_url_ingestion_pipeline.py::test_rejected_url_pipeline_returns_typed_needs_review_evidence` | ❌ W0 | ⬜ pending |
| 09-03-03 | 03 | 3 | EXT1-01 | determinism | `pytest -q tests/test_url_ingestion_determinism.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_url_source_resolver.py` — canonical source classification and normalization
- [ ] `tests/test_url_policy_contracts.py` — URL-policy parsing, fail-closed validation, typed rejection reasons
- [ ] `tests/test_url_snapshot_store.py` — bounded fetch, redirect revalidation, immutable snapshot materialization
- [ ] `tests/test_url_ingestion_boundary.py` — rejected URLs block before sanitize/read
- [ ] `tests/test_url_ingestion_pipeline.py` — approved URL integration through snapshot to summary
- [ ] `tests/test_url_ingestion_determinism.py` — repeated-run and cross-process byte stability for URL flows

---

## Manual-Only Verifications

None — all phase requirements have automated targets.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verification targets or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all new files introduced by the plan
- [x] No watch-mode flags
- [x] Feedback latency target documented
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
