---
phase: 10
slug: ext-02-simulate-first-controlled-execution
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-09
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for simulate-first controlled execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — direct pytest invocation |
| **Quick run command** | `pytest -q tests/test_phase6_contracts.py tests/test_phase6_authorizer.py tests/test_phase6_registry.py` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~240 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q tests/test_phase6_contracts.py tests/test_phase6_authorizer.py tests/test_phase6_registry.py`
- **After every plan wave:** Run `pytest -q tests/test_phase6_engine.py tests/test_phase6_journal.py tests/test_phase6_boundary.py`
- **Before verification:** Run `pytest -q`
- **Max feedback latency:** 240 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | EXT2-01 | unit | `pytest -q tests/test_phase6_contracts.py::test_approval_contract_requires_exact_execute_binding_fields` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | EXT2-02 | unit | `pytest -q tests/test_phase6_registry.py::test_registry_rejects_duplicate_route_tool_bindings` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | EXT2-01 | integration | `pytest -q tests/test_phase6_authorizer.py::test_execute_eligible_requires_phase4_phase5_and_approval_alignment` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 2 | EXT2-03 | integration | `pytest -q tests/test_phase6_engine.py::test_missing_approval_returns_needs_review_without_execution` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 2 | EXT2-03 | integration | `pytest -q tests/test_phase6_engine.py::test_simulate_only_approval_uses_hermetic_adapter_and_no_side_effects` | ❌ W0 | ⬜ pending |
| 10-02-03 | 02 | 2 | EXT2-02 | integration | `pytest -q tests/test_phase6_engine.py::test_unmapped_or_ambiguous_registry_path_blocks_deterministically` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 3 | EXT2-04 | unit | `pytest -q tests/test_phase6_journal.py::test_journal_records_blocked_attempts_with_canonical_evidence` | ❌ W0 | ⬜ pending |
| 10-03-02 | 03 | 3 | EXT2-04 | determinism | `pytest -q tests/test_phase6_determinism.py` | ❌ W0 | ⬜ pending |
| 10-03-03 | 03 | 3 | EXT2-05 | boundary | `pytest -q tests/test_phase6_boundary.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase6_contracts.py` — approval contract parsing, schema and expiry validation, exact-match binding rules
- [ ] `tests/test_phase6_registry.py` — closed executor registry parsing, duplicate/unmapped/unsupported resolution checks
- [ ] `tests/test_phase6_authorizer.py` — execute-eligibility gating against Phase 4, Phase 5, approval, and capability facts
- [ ] `tests/test_phase6_engine.py` — simulate-first control flow, deterministic `NEEDS_REVIEW`, hermetic adapter behavior
- [ ] `tests/test_phase6_journal.py` — append-only evidence, idempotency, canonical record layout
- [ ] `tests/test_phase6_boundary.py` — forbidden import/call enforcement for simulation and execution control paths
- [ ] `tests/test_phase6_determinism.py` — repeated-run and cross-process byte stability for identical approved/blocked inputs

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
