---
phase: 01
slug: local-ingestion-two-pass-sanitization-intent-summary
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Quick run command** | `pytest -q tests/test_phase1_pipeline.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q tests/test_phase1_pipeline.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INGEST-01 | unit | `pytest -q tests/test_ingestion_boundary.py -q` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | INGEST-02 | unit | `pytest -q tests/test_ingestion_boundary.py -q` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | SAN-01 | unit | `pytest -q tests/test_sanitization_pipeline.py -q` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | SAN-02 | unit | `pytest -q tests/test_sanitization_pipeline.py -q` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | SUM-01 | integration | `pytest -q tests/test_intent_summary.py -q` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | SUM-02 | unit | `pytest -q tests/test_intent_summary.py -q` | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 2 | SUM-03 | integration | `pytest -q tests/test_determinism.py -q` | ❌ W0 | ⬜ pending |
| 01-03-04 | 03 | 2 | BOUND-01 | integration | `pytest -q tests/test_phase_boundary.py -q` | ❌ W0 | ⬜ pending |
| 01-03-05 | 03 | 2 | BOUND-02 | integration | `pytest -q tests/test_phase_boundary.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ingestion_boundary.py` — stubs for INGEST-01, INGEST-02
- [ ] `tests/test_sanitization_pipeline.py` — stubs for SAN-01, SAN-02
- [ ] `tests/test_intent_summary.py` and `tests/test_determinism.py` — stubs for SUM-01, SUM-02, SUM-03
- [ ] `tests/test_phase_boundary.py` — stubs for BOUND-01, BOUND-02
- [ ] `pip install pytest` or project-pinned equivalent

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Summary language quality for ambiguous prompts | SUM-01 | Requires human judgement on clarity | Run pipeline on 3 representative files, verify summary is concise and intent-focused |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
