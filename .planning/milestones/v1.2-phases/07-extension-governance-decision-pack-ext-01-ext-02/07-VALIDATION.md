---
phase: 07
slug: extension-governance-decision-pack-ext-01-ext-02
status: draft
nyquist_compliant: true
wave_3_complete: true
created: 2026-03-06
---

# Phase 07 - Validation Strategy

> Deterministic validation contract for extension-governance closure (`EXT-01`, `EXT-02`) in v1.2.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | deterministic planning-artifact and state verification |
| **Config file** | `.planning/config.json` |
| **Quick run command** | `test -f .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VALIDATION.md && test -f .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VERIFICATION.md` |
| **Full suite command** | `test -f .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VALIDATION.md && test -f .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VERIFICATION.md && rg -n "EXTG-01|EXTG-02|PROJECT|REQUIREMENTS|ROADMAP|EXT-01|EXT-02" .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VERIFICATION.md && node "$HOME/.codex/get-shit-done/bin/gsd-tools.cjs" state json --raw` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** run the deterministic task-level command mapped to the completed task.
- **After Phase 7 publication updates:** re-run cross-document scope-language scan to catch drift before closure sign-off.
- **Before final phase transition:** full suite command must pass.
- **Max feedback latency:** 30 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01 | 01 | 1 | EXTG-01 | decision matrix determinism | `rg -n "EXT-01|EXT-02|Disposition|Rationale|Risk|Re-entry|weighted score" .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-DECISION-MATRIX.md` | ✅ | ✅ green |
| 07-02 | 02 | 2 | EXTG-01, EXTG-02 | boundary-language synchronization | `rg -n "EXT-01|EXT-02|defer|governance|no-execution|no-runtime-expansion" .planning/PROJECT.md .planning/REQUIREMENTS.md .planning/ROADMAP.md` | ✅ | ✅ green |
| 07-03 | 03 | 3 | EXTG-02 | closure evidence and continuity | `test -f .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VALIDATION.md && test -f .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VERIFICATION.md && rg -n "EXTG-01|EXTG-02|PROJECT|REQUIREMENTS|ROADMAP" .planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VERIFICATION.md && node "$HOME/.codex/get-shit-done/bin/gsd-tools.cjs" state json --raw` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## EXT Governance Sign-Off Criteria

- [x] **EXTG-01 sign-off:** `EXT-01` and `EXT-02` have explicit deterministic dispositions with rationale, risk, and re-entry criteria in `.planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-DECISION-MATRIX.md`.
- [x] **EXTG-02 sign-off:** `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, and `.planning/ROADMAP.md` synchronize explicit `EXT-01=defer` and `EXT-02=defer` outcomes, with governance-only staging and no v1.2 runtime-scope expansion.
- [x] **Closure evidence sign-off:** `.planning/phases/07-extension-governance-decision-pack-ext-01-ext-02/07-VERIFICATION.md` includes contradiction scan output and residual-risk status.

---

## Manual-Only Verifications

None. Phase 07 closure checks are fully deterministic and CLI-verifiable.

---

## Validation Sign-Off

- [x] Per-task map includes all Phase 7 plans (07-01, 07-02, 07-03).
- [x] Sign-off criteria are explicit for `EXTG-01` and `EXTG-02`.
- [x] Full suite command verifies closure artifacts plus state continuity output.
- [x] `nyquist_compliant: true` remains set.

**Approval:** complete
