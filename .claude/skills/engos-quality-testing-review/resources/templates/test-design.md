# Test design

## Scope
Selected mode: Generate Unit Tests / Generate E2E Tests / Edge Cases / Coverage Analysis.
Behavior, repository boundary and requirement/source links; mark unresolved links explicitly.
Execution status: `not_run`.

## Assumptions
Contract uncertainties, fixture realism, environment and unresolved source evidence.

## Recommended Tests or Gaps
For each proposed test: ID; requirement links; independently derived expected observable outcome; plausible fault and the assertion that catches it; fixture; negative case; boundary case. State justified non-applicability or unknowns instead of inventing cases.
For coverage-only work: evidence-backed gaps and proposed next investigation; an empty test list is valid.

## Priority or Risk
Order by behavior risk and explain the smallest useful set.

## Framework Notes
Existing framework and layout; proposed command plus exact supporting source and prerequisites, or `unknown` with missing evidence. No command here is an execution receipt.

## Follow-up Work
Remaining gaps and separately authorized execution or integration checks. Record independent artifact review status without self-acceptance. Design acceptance does not establish observed coverage or release readiness.

Optional machine interchange: TestDesign.v1 uses `schema_version`, `id`, `requirement_ids`, `tests` (each with `id`, `requirements`, `expected`, `oracle`, `fixture`, `negative_case`, `boundary_case`, `command_source`), `execution_status: not_run`, and `gaps`. Requirement strings identify their sources; each command_source records a command and provenance as text, or explicitly records unknown. Preserve these six sections; a JSON sidecar is not mandatory. Schema validity is not semantic validation.
