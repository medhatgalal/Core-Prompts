# Phase 7 Extension Governance Decision Matrix (`EXT-01`, `EXT-02`)

## Scope Guard

This artifact is governance-only for v1.2. It does not authorize implementation work, runtime execution expansion, or network side-effect expansion.

## Deterministic Rubric

### Criteria and Weights

| Criterion | Weight | Deterministic scoring guidance |
| --- | --- | --- |
| boundary safety | 35% | 0=breaks no-execution/no-network boundary, 1=boundary unclear, 2=partial controls, 3=explicit controls and guardrails, 4=controls plus auditability, 5=controls proven and stable |
| determinism impact | 25% | 0=non-deterministic behavior expected, 1=determinism not specified, 2=partial deterministic contract, 3=deterministic contract drafted, 4=determinism contract testable, 5=determinism contract proven |
| policy maturity | 20% | 0=no policy, 1=policy intent only, 2=draft policy, 3=reviewable policy controls, 4=approved policy package, 5=approved policy with exception handling |
| verification readiness | 20% | 0=no verification path, 1=ad hoc checks only, 2=partial checklist, 3=repeatable checklist, 4=automatable deterministic checks, 5=checks already executable and auditable |

### Score Formula

1. Score each criterion on a closed integer scale from 0 to 5.
2. Compute weighted score:
   - `weighted = (boundary safety*35 + determinism impact*25 + policy maturity*20 + verification readiness*20) / 100`
3. Round `weighted` to two decimals.

### Deterministic Decision Rules

Apply in this exact order:

1. `reject` if `boundary safety <= 1` OR `determinism impact <= 1`.
2. `go` if all criterion scores are `>= 4` and `weighted >= 4.00`.
3. `defer` for all remaining cases.

### Deterministic Tie-Break Rule

If two candidate dispositions appear plausible, choose the more conservative outcome in this fixed precedence: `reject` > `defer` > `go`.

### Required Output Format Per Extension

Each extension record must contain these fields in this order:

1. Extension
2. Disposition (`go`, `defer`, or `reject`)
3. Scorecard (all four criteria + weighted score)
4. Rationale
5. Risk
6. Re-entry criteria

## Evaluations

### EXT-01

Pending Task 2 evaluation.

### EXT-02

Pending Task 2 evaluation.
