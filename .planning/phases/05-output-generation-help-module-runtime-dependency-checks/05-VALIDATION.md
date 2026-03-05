---
phase: 05
slug: output-generation-help-module-runtime-dependency-checks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-05
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none |
| **Quick run command** | `PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 LANG=C.UTF-8 PYTHONPATH=src pytest -q tests/test_phase5_contracts.py tests/test_phase5_engine.py` |
| **Full suite command** | `PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 LANG=C.UTF-8 PYTHONPATH=src pytest -q tests/test_phase5_contracts.py tests/test_phase5_engine.py tests/test_phase5_boundary.py tests/test_phase5_determinism.py` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 LANG=C.UTF-8 PYTHONPATH=src pytest -q tests/test_phase5_contracts.py tests/test_phase5_engine.py`
- **After every plan wave:** Run `PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 LANG=C.UTF-8 PYTHONPATH=src pytest -q tests/test_phase5_contracts.py tests/test_phase5_engine.py tests/test_phase5_boundary.py tests/test_phase5_determinism.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | OUT-01, OUT-02 | unit | `PYTHONPATH=src pytest -q tests/test_phase5_contracts.py -k "out and schema"` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | OUT-03 | unit | `PYTHONPATH=src pytest -q tests/test_phase5_engine.py -k "preserve or needs_review"` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | HELP-01, HELP-02 | unit | `PYTHONPATH=src pytest -q tests/test_phase5_contracts.py tests/test_phase5_engine.py -k "help and template"` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | HELP-03 | unit | `PYTHONPATH=src pytest -q tests/test_phase5_engine.py -k "non_executing or remediation"` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 3 | RUNTIME-01, RUNTIME-02 | integration | `PYTHONPATH=src pytest -q tests/test_phase5_engine.py -k "runtime and required"` | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 3 | RUNTIME-03, RUNTIME-04 | integration | `PYTHONPATH=src pytest -q tests/test_phase5_engine.py -k "optional or ordering"` | ❌ W0 | ⬜ pending |
| 05-03-03 | 03 | 3 | DET-05, BOUND-05 | boundary | `PYTHONPATH=src pytest -q tests/test_phase5_boundary.py tests/test_phase5_determinism.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase5_contracts.py` — contract and schema validation stubs for OUT/HELP/RUNTIME contracts
- [ ] `tests/test_phase5_engine.py` — orchestration, status aggregation, and semantic preservation checks
- [ ] `tests/test_phase5_boundary.py` — forbidden import/call guardrails and typed `BOUND-05-*` diagnostics
- [ ] `tests/test_phase5_determinism.py` — repeated-run and cross-process byte-stability checks
- [ ] shared fixtures in `tests/conftest.py` for `Phase4Result`-based phase5 inputs

---

## Manual-Only Verifications

All phase behaviors are expected to have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency <= 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
