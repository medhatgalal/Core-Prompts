---
phase: 04
slug: target-tool-validation-mock-execution-fallback-degradation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-04
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none |
| **Quick run command** | `PYTHONPATH=src pytest -q tests/test_target_validation.py tests/test_mock_execution.py` |
| **Full suite command** | `PYTHONPATH=src pytest -q tests/test_target_validation.py tests/test_mock_execution.py tests/test_fallback_degradation.py tests/test_phase4_determinism.py tests/test_phase4_boundary.py` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=src pytest -q tests/test_target_validation.py tests/test_mock_execution.py`
- **After every plan wave:** Run `PYTHONPATH=src pytest -q tests/test_target_validation.py tests/test_mock_execution.py tests/test_fallback_degradation.py tests/test_phase4_determinism.py tests/test_phase4_boundary.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | VAL-01 | unit | `PYTHONPATH=src pytest -q tests/test_target_validation.py -k "typed_matrix or schema"` | ✅ | ✅ green |
| 04-01-02 | 01 | 1 | VAL-02 | unit | `PYTHONPATH=src pytest -q tests/test_target_validation.py -k "fail_closed"` | ✅ | ✅ green |
| 04-01-03 | 01 | 1 | VAL-03 | unit | `PYTHONPATH=src pytest -q tests/test_target_validation.py -k "error_code and evidence_path"` | ✅ | ✅ green |
| 04-02-01 | 02 | 2 | MOCK-01 | unit | `PYTHONPATH=src pytest -q tests/test_mock_execution.py -k "dry_run or side_effect"` | ✅ | ✅ green |
| 04-02-02 | 02 | 2 | MOCK-02 | unit | `PYTHONPATH=src pytest -q tests/test_mock_execution.py -k "trace and evidence"` | ✅ | ✅ green |
| 04-03-01 | 03 | 3 | FALLBACK-01, FALLBACK-02 | integration | `PYTHONPATH=src pytest -q tests/test_fallback_degradation.py` | ✅ | ✅ green |
| 04-03-02 | 03 | 3 | DET-04 | integration | `PYTHONPATH=src pytest -q tests/test_phase4_determinism.py` | ✅ | ✅ green |
| 04-03-03 | 03 | 3 | BOUND-04 | boundary | `PYTHONPATH=src pytest -q tests/test_phase4_boundary.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_target_validation.py` — typed capability matrix, fail-closed behavior, deterministic code/evidence payloads
- [x] `tests/test_mock_execution.py` — dry-run semantics, deterministic step trace, no side effects
- [x] `tests/test_fallback_degradation.py` — fixed fallback tier ordering and deterministic terminal state
- [x] `tests/test_phase4_determinism.py` — repeated-run byte stability for full Phase 4 outputs
- [x] `tests/test_phase4_boundary.py` — guardrails for no real execution/output/help/runtime checks
- [x] shared Phase 4 fixtures in `tests/conftest.py` for route-spec + capability matrix inputs

---

## Manual-Only Verifications

All phase behaviors are expected to have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency <= 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete
