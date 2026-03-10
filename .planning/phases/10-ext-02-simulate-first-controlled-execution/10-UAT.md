---
phase: "10-ext-02-simulate-first-controlled-execution"
status: passed
started: 2026-03-09
updated: 2026-03-10
session_type: conversational_uat
---

# Phase 10 UAT

## Goal

Validate Phase 10 from the user perspective: simulate-first controlled execution should be understandable, deterministic, and fail closed.

## Scope Under Test

- Simulate-only approved flow produces a useful hermetic result
- Missing or invalid approval returns deterministic `NEEDS_REVIEW`
- Closed registry behavior blocks unmapped or ambiguous execution targets
- Idempotency replay prevents duplicate approved attempts from re-running
- Journal evidence is present and traceable for every terminal outcome

## Session Status

- Current step: all required Phase 10 UAT scenarios completed
- Automated baseline: Phase 10 verification passed (`10-VERIFICATION.md`)
- Human UAT findings: all required Phase 10 scenarios passed; simulate-only and execute-approved hermetic paths remain deterministic and traceable; fail-closed cases block cleanly without side effects

## Test Log

### Covered Scenarios
1. Simulate-only approved path
2. Missing approval fail-closed path
3. Idempotency replay path
4. Registry unmapped fail-closed path
5. Registry ambiguity fail-closed path
6. Expired approval fail-closed path
7. Upstream ineligible fail-closed path
8. Execute-approved hermetic path

### Results
- 2026-03-09 — Scenario 1: Simulate-only approved path — PASS
  - Input routed to `VALIDATION` with Phase 4 `PASS`, fallback `USE_PRIMARY`, and Phase 5 terminal status `USE_PRIMARY`.
  - `run_phase6(...)` returned `SIMULATED` with `EXEC-017-SIMULATION-COMPLETED`.
  - Hermetic adapter artifacts were present and journal evidence recorded one deterministic entry.
  - User-facing interpretation: the simulate-only path is understandable and traceable; output clearly remains non-executing while preserving audit evidence.
- 2026-03-09 — Scenario 2: Missing approval fail-closed path — PASS
  - Input remained execute-eligible upstream (`PASS` / `USE_PRIMARY` / `USE_PRIMARY`) to isolate the approval gate itself.
  - `run_phase6(...)` returned `NEEDS_REVIEW` with `EXEC-001-APPROVAL-MISSING`.
  - No adapter artifacts were produced and the journal still recorded one deterministic blocked-attempt entry.
  - User-facing interpretation: missing approval fails closed in a clear and traceable way without accidental execution.
- 2026-03-10 — Scenario 3: Idempotency replay path — PASS
  - First approved attempt returned `EXECUTED` with `EXEC-018-EXECUTION-COMPLETED`.
  - Second identical approved attempt reused the same `idempotency_key` and returned `EXECUTED` with `EXEC-019-IDEMPOTENT-REPLAY`.
  - `replayed_from_journal` was `true`, no second execution ran, and the journal stayed at one canonical record for that key.
  - User-facing interpretation: duplicate approved requests are traceable and non-replaying in practice, not just by contract.
- 2026-03-10 — Scenario 4: Registry unmapped fail-closed path — PASS
  - Upstream eligibility remained valid to isolate registry behavior.
  - `run_phase6(...)` returned `NEEDS_REVIEW` with `EXEC-013-REGISTRY-UNMAPPED`.
  - No adapter artifacts were produced; journal evidence recorded one blocked attempt with registry evidence path `phase6.registry.entries`.
  - User-facing interpretation: unknown route/tool mappings block deterministically instead of falling through to execution.
- 2026-03-10 — Scenario 5: Registry ambiguity fail-closed path — PASS
  - A duplicated route/tool registry entry was introduced to simulate ambiguity.
  - `run_phase6(...)` returned `NEEDS_REVIEW` with `EXEC-014-REGISTRY-DUPLICATE`.
  - No adapter artifacts were produced; journal evidence recorded one blocked attempt with evidence path `phase6.registry.entries[1]`.
  - User-facing interpretation: ambiguous executor resolution blocks cleanly and leaves auditable evidence.
- 2026-03-10 — Scenario 6: Expired approval fail-closed path — PASS
  - Approval contract was present and otherwise valid, but `expires_at` was intentionally set in the past.
  - `run_phase6(...)` returned `NEEDS_REVIEW` with `EXEC-006-APPROVAL-EXPIRED`.
  - No adapter artifacts were produced; journal evidence recorded one blocked attempt with evidence path `approval_contract.expires_at`.
  - User-facing interpretation: stale approvals cannot execute and fail closed with an explicit reason.
- 2026-03-10 — Scenario 7: Upstream ineligible fail-closed path — PASS
  - Input was forced into upstream validation failure to ensure execute-eligibility gates were respected.
  - `run_phase6(...)` returned `NEEDS_REVIEW` with `EXEC-003-UPSTREAM-VALIDATION-BLOCKED`.
  - No adapter artifacts were produced; journal evidence recorded one blocked attempt with evidence paths `phase4.validation.can_proceed` and `phase4.validation.decision`.
  - User-facing interpretation: Phase 6 does not bypass Phase 4/5 safety decisions and remains strictly downstream of eligible states.
- 2026-03-10 — Scenario 8: Execute-approved hermetic path — PASS
  - Approval mode was upgraded to `EXECUTE_APPROVED` against the closed registry and hermetic adapter.
  - `run_phase6(...)` returned `EXECUTED` with `EXEC-018-EXECUTION-COMPLETED`.
  - Produced artifacts were limited to deterministic hermetic evidence entries: `phase6:execute:adapter:hermetic-adapter`, `phase6:execute:route:VALIDATION`, and `phase6:execute:tool:tool-validation`.
  - Journal evidence recorded one canonical execution entry.
  - User-facing interpretation: execute-approved flow remains tightly bounded and auditable, with no behavior beyond the explicitly allowed hermetic path.
