---
phase: 08
slug: shared-extension-contracts-and-boundary-gates
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-06
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — direct pytest invocation |
| **Quick run command** | `pytest -q tests/test_extension_gate_contracts.py tests/test_extension_gate_boundary.py` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q tests/test_extension_gate_contracts.py tests/test_extension_gate_boundary.py`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | XDET-02 | unit | `pytest -q tests/test_extension_gate_contracts.py::test_policy_contract_requires_versioned_rule_ids` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | XDET-02 | unit | `pytest -q tests/test_extension_gate_contracts.py::test_gate_payload_serialization_is_stable` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 1 | XBND-02 | unit | `pytest -q tests/test_extension_gate_boundary.py::test_unknown_modes_fail_closed` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 1 | XBND-01 | integration | `pytest -q tests/test_extension_gate_boundary.py::test_extensions_disabled_preserve_local_only_baseline` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 2 | XDET-01 | integration | `pytest -q tests/test_extension_gate_determinism.py::test_gate_decisions_are_byte_stable` | ❌ W0 | ⬜ pending |
| 08-03-02 | 03 | 2 | XBND-01 | integration | `pytest -q tests/test_extension_gate_boundary.py tests/test_phase_boundary.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_extension_gate_contracts.py` — contract validation and deterministic serialization coverage
- [ ] `tests/test_extension_gate_boundary.py` — fail-closed gate and baseline-preservation checks
- [ ] `tests/test_extension_gate_determinism.py` — repeated-run stability checks

---

## Manual-Only Verifications

None — all phase behaviors have automated verification targets.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency target documented
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
