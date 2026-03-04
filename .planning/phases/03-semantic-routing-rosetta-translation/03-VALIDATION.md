---
phase: 03
slug: semantic-routing-rosetta-translation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-04
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none |
| **Quick run command** | `PYTHONPATH=src pytest -q tests/test_semantic_router_precedence.py tests/test_rosetta_translation.py` |
| **Full suite command** | `PYTHONPATH=src pytest -q tests/test_routing_contracts.py tests/test_semantic_router_precedence.py tests/test_semantic_router_ambiguity.py tests/test_rosetta_translation.py tests/test_phase3_determinism.py tests/test_phase3_boundary.py` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=src pytest -q tests/test_semantic_router_precedence.py tests/test_rosetta_translation.py`
- **After every plan wave:** Run `PYTHONPATH=src pytest -q tests/test_routing_contracts.py tests/test_semantic_router_precedence.py tests/test_semantic_router_ambiguity.py tests/test_rosetta_translation.py tests/test_phase3_determinism.py tests/test_phase3_boundary.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ROUTE-CTX-01 | unit | `PYTHONPATH=src pytest -q tests/test_routing_contracts.py -k "schema or contract"` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | ROUTE-PREC-01 | unit | `PYTHONPATH=src pytest -q tests/test_semantic_router_precedence.py` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | ROUTE-ENUM-01 | unit | `PYTHONPATH=src pytest -q tests/test_routing_contracts.py -k "enum"` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | ROUTE-UNK-01 | unit | `PYTHONPATH=src pytest -q tests/test_semantic_router_ambiguity.py` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 3 | ROSETTA-01 | unit | `PYTHONPATH=src pytest -q tests/test_rosetta_translation.py -k "schema"` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 3 | ROSETTA-02 | unit | `PYTHONPATH=src pytest -q tests/test_rosetta_translation.py -k "task_focus or linkage"` | ❌ W0 | ⬜ pending |
| 03-03-03 | 03 | 3 | DET-03 | integration | `PYTHONPATH=src pytest -q tests/test_phase3_determinism.py` | ❌ W0 | ⬜ pending |
| 03-03-04 | 03 | 3 | BOUND-03 | boundary | `PYTHONPATH=src pytest -q tests/test_phase3_boundary.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_routing_contracts.py` — schema contracts, enum closure, required fields
- [ ] `tests/test_semantic_router_precedence.py` — fixed precedence matrix (`hard > intent > task > acceptance`)
- [ ] `tests/test_semantic_router_ambiguity.py` — deterministic `NEEDS_REVIEW` and missing-evidence payloads
- [ ] `tests/test_rosetta_translation.py` — canonical route-spec mapping and linkage checks
- [ ] `tests/test_phase3_determinism.py` — repeated-run byte stability
- [ ] `tests/test_phase3_boundary.py` — guardrails for no execution/validation/output generation
- [ ] shared fixtures for uplift-contract inputs (`tests/conftest.py` updates)

---

## Manual-Only Verifications

All phase behaviors are expected to have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
