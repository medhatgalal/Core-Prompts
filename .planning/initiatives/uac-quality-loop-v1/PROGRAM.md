# UAC Quality Iteration Framework v1 Program

## Goal
Add a built-in UAC quality loop that can plan, judge, and gate apply operations with persistent review artifacts and advisory-only handoff metadata.

## Boundary
- UAC owns classification, uplift, packaging, evidence, and advisory metadata.
- UAC does not own orchestration, routing, delegation, or runtime execution.
- EngOS or Symphony-like orchestrators consume the published metadata and decide how to act.

## Scope
1. Quality profiles and persistent review artifacts
2. `plan` / `judge` / `apply` quality-loop support
3. Advisory handoff contract extensions
4. Architecture exemplar alignment
5. Focused verification and cleanup

## Exit Criteria
- `bin/uac judge` exists and is non-mutating
- `plan` and `apply` accept quality-loop flags
- `apply` refuses landing on failed quality status
- quality review artifacts persist under `reports/quality-reviews/`
- architecture descriptor and handoff expose the new advisory fields
