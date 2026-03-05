---
phase: 04
slug: target-tool-validation-mock-execution-fallback-degradation
status: draft
nyquist_compliant: false
wave_0_complete: false
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
- **Max feedback latency:** 35 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | VAL-01 | unit | `PYTHONPATH=src pytest -q tests/test_target_validation.py -k "typed_matrix or schema"` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | VAL-02 | unit | `PYTHONPATH=src pytest -q tests/test_target_validation.py -k "fail_closed"` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | VAL-03 | unit | `PYTHONPATH=src pytest -q tests/test_target_validation.py -k "error_code and evidence_path"` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | MOCK-01 | unit | `PYTHONPATH=src pytest -q tests/test_mock_execution.py -k "dry_run or side_effect"` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | MOCK-02 | unit | `PYTHONPATH=src pytest -q tests/test_mock_execution.py -k "trace and evidence"` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 3 | FALLBACK-01 | integration | `PYTHONPATH=src pytest -q tests/test_fallback_degradation.py -k "tier_order"` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 3 | FALLBACK-02 | integration | `PYTHONPATH=src pytest -q tests/test_fallback_degradation.py -k "needs_review"` | ❌ W0 | ⬜ pending |
| 04-03-03 | 03 | 3 | DET-04 | integration | `PYTHONPATH=src pytest -q tests/test_phase4_determinism.py` | ❌ W0 | ⬜ pending |
| 04-03-04 | 03 | 3 | BOUND-04 | boundary | `PYTHONPATH=src pytest -q tests/test_phase4_boundary.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_target_validation.py` — typed capability matrix, fail-closed behavior, deterministic code/evidence payloads
- [ ] `tests/test_mock_execution.py` — dry-run semantics, deterministic step trace, no side effects
- [ ] `tests/test_fallback_degradation.py` — fixed fallback tier ordering and deterministic terminal state
- [ ] `tests/test_phase4_determinism.py` — repeated-run byte stability for full Phase 4 outputs
- [ ] `tests/test_phase4_boundary.py` — guardrails for no real execution/output/help/runtime checks
- [ ] shared Phase 4 fixtures in `tests/conftest.py` for route-spec + capability matrix inputs

---

## Manual-Only Verifications

All phase behaviors are expected to have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 35s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
