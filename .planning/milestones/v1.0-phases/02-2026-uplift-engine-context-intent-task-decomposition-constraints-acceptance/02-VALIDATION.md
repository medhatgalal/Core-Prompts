---
phase: 02
slug: 2026-uplift-engine-context-intent-task-decomposition-constraints-acceptance
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-04
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `tests/conftest.py` |
| **Quick run command** | `pytest -q tests/test_uplift_engine_*.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q tests/test_uplift_engine_*.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | UPLIFT-CTX | unit | `pytest -q tests/test_uplift_engine_context.py -q` | ✅ | ✅ green |
| 02-01-02 | 01 | 1 | UPLIFT-INTENT | unit | `pytest -q tests/test_uplift_engine_intent.py -q` | ✅ | ✅ green |
| 02-02-01 | 02 | 1 | UPLIFT-DECOMP | unit | `pytest -q tests/test_uplift_engine_decomposition.py -q` | ✅ | ✅ green |
| 02-02-02 | 02 | 1 | UPLIFT-CONSTRAINTS | unit | `pytest -q tests/test_uplift_engine_constraints.py -q` | ✅ | ✅ green |
| 02-03-01 | 03 | 2 | UPLIFT-ACCEPTANCE | integration | `pytest -q tests/test_uplift_engine_acceptance.py -q` | ✅ | ✅ green |
| 02-03-02 | 03 | 2 | UPLIFT-ACCEPTANCE | integration | `pytest -q tests/test_uplift_engine_pipeline.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_uplift_engine_context.py` — schema and versioning stubs for UPLIFT-CTX
- [x] `tests/test_uplift_engine_intent.py` — explicit/inferred marker tests for UPLIFT-INTENT
- [x] `tests/test_uplift_engine_decomposition.py` — deterministic DAG and ordering tests for UPLIFT-DECOMP
- [x] `tests/test_uplift_engine_constraints.py` — hard/soft conflict and failure payload tests for UPLIFT-CONSTRAINTS
- [x] `tests/test_uplift_engine_acceptance.py` and `tests/test_uplift_engine_pipeline.py` — gate/scoring/evidence + integration flow tests for UPLIFT-ACCEPTANCE

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Clarity/usability of acceptance evidence payload for human review | UPLIFT-ACCEPTANCE | Human judgment of readability and debugging value | Run engine on 3 representative intents and verify evidence is understandable and actionable |

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
