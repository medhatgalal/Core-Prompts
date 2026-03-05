---
phase: 01
slug: local-ingestion-two-pass-sanitization-intent-summary
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-04
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (Wave 0 install) |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `PYTHONPATH=src pytest -q tests/test_ingestion_boundary.py tests/test_sanitization_pipeline.py tests/test_intent_summary.py` |
| **Full suite command** | `PYTHONPATH=src pytest -q tests/test_ingestion_boundary.py tests/test_sanitization_pipeline.py tests/test_intent_summary.py tests/test_determinism.py tests/test_phase_boundary.py` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=src pytest -q tests/test_ingestion_boundary.py tests/test_sanitization_pipeline.py tests/test_intent_summary.py`
- **After every plan wave:** Run `PYTHONPATH=src pytest -q tests/test_ingestion_boundary.py tests/test_sanitization_pipeline.py tests/test_intent_summary.py tests/test_determinism.py tests/test_phase_boundary.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INGEST-01 | unit | `pytest -q tests/test_ingestion_boundary.py -q` | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | INGEST-02 | unit | `pytest -q tests/test_ingestion_boundary.py -q` | ✅ | ✅ green |
| 01-02-01 | 02 | 1 | SAN-01 | unit | `pytest -q tests/test_sanitization_pipeline.py -q` | ✅ | ✅ green |
| 01-02-02 | 02 | 1 | SAN-02 | unit | `pytest -q tests/test_sanitization_pipeline.py -q` | ✅ | ✅ green |
| 01-03-01 | 03 | 2 | SUM-01 | integration | `pytest -q tests/test_intent_summary.py -q` | ✅ | ✅ green |
| 01-03-02 | 03 | 2 | SUM-02 | unit | `pytest -q tests/test_intent_summary.py -q` | ✅ | ✅ green |
| 01-03-03 | 03 | 2 | SUM-03 | integration | `pytest -q tests/test_determinism.py -q` | ✅ | ✅ green |
| 01-03-04 | 03 | 2 | BOUND-01 | integration | `pytest -q tests/test_phase_boundary.py -q` | ✅ | ✅ green |
| 01-03-05 | 03 | 2 | BOUND-02 | integration | `pytest -q tests/test_phase_boundary.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_ingestion_boundary.py` — stubs for INGEST-01, INGEST-02
- [x] `tests/test_sanitization_pipeline.py` — stubs for SAN-01, SAN-02
- [x] `tests/test_intent_summary.py` and `tests/test_determinism.py` — stubs for SUM-01, SUM-02, SUM-03
- [x] `tests/test_phase_boundary.py` — stubs for BOUND-01, BOUND-02
- [x] `pip install pytest` or project-pinned equivalent

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Summary language quality for ambiguous prompts | SUM-01 | Requires human judgement on clarity | Run pipeline on 3 representative files, verify summary is concise and intent-focused |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency <= 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

## Validation Audit 2026-03-05
| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
