---
name: "engos-quality-testing-review"
description: "Design or generate tests, edge cases, and coverage-gap analysis for a defined behavior without claiming tests were run. Use when test design is the primary deliverable; use GitOps review for release readiness."
---
# Testing Studio — Test Design and Coverage Analysis

## Purpose
Use this capability to design tests, identify missing coverage, and turn vague quality concerns into concrete test work without silently running the test suite.

## Primary Objective
Produce deterministic, framework-aware testing recommendations or test artifacts that improve confidence while making assumptions, risk, and remaining gaps explicit.

## Output Directory
When the user wants analysis artifacts instead of direct test files, default to:
- `reports/testing/<timestamp>-plan.md`
- `reports/testing/<timestamp>-coverage-gap.md`
- `reports/testing/<timestamp>-edge-cases.md`

When the user asks for concrete test outputs, place them under the repository's existing test layout. If the repo has no established layout, propose one before writing files.

## Workflow
1. Determine whether the task is unit tests, E2E design, edge-case discovery, or coverage analysis.
2. Inspect the current repository testing stack and existing tests before recommending changes.
3. Produce the minimum useful test set or gap analysis for the requested mode.
4. Separate what can be generated now from what still needs repo-specific validation or execution.
5. End with explicit priorities, risks, and follow-up work.

## Tool Boundaries
- allowed: inspect source code and existing tests, design test cases, and write test artifacts when asked
- forbidden: silently executing tests, inventing framework choices that contradict the repo, or claiming coverage numbers without evidence
- escalation: if the request is actually a release gate or CI readiness question, recommend `engos-quality-gitops-review`

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- generate unit tests
- design end-to-end tests
- find edge cases we are missing
- show me coverage gaps
- tell me what to test first for this change

## Required Inputs
- source code, feature description, or failing scenario
- repository testing stack when known
- risk areas or priority workflows
- existing tests or coverage report when available

## Required Output
Every substantial writer-authored artifact must include:
- `Scope`
- `Assumptions`
- `Recommended Tests or Gaps`
- `Priority or Risk`
- `Framework Notes`
- `Follow-up Work`

## Rules
- Respect the existing test framework and project conventions.
- Separate generation of tests from execution of tests.
- Prefer readable test names and explicit assertions.
- Include failure cases and boundary cases, not only happy path.
- Call out when a repository needs integration or E2E coverage instead of more unit tests.

## Modes
### Generate Unit Tests
Use when the job is creating or improving isolated tests around functions, classes, or modules.

Produce:
- framework-aware test file
- happy-path, error-path, and boundary tests
- mocks or fixtures only where needed
- clear assertions and setup notes

### Generate E2E Tests
Use when the job is validating a real workflow across interfaces or services.

Produce:
- critical user journeys
- setup and teardown strategy
- waiting and synchronization guidance
- environment and test-data notes
- failure capture or diagnostics expectations

### Edge Cases
Use when the job is finding what the current design or tests are likely missing.

Produce:
- categorized edge cases
- risk level
- likely impact
- suggested tests to add first

### Coverage Analysis
Use when the job is deciding where coverage is weak.

Produce:
- current coverage summary if data exists
- specific untested branches, functions, or scenarios
- risk-based prioritization
- recommended next tests

## Examples
### Example Request
> Review this change and tell me which tests to add first, including edge cases we are currently missing.

### Example Output Shape
- scope and assumptions
- recommended tests by priority
- unresolved risks
- framework-specific notes

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Mode selection | The response chooses the correct testing mode for the task |
| Framework fit | Recommendations respect the repo’s existing testing stack |
| Risk coverage | Happy path, failures, and boundary cases are all considered |
| Actionability | A developer can implement the proposed tests directly |
| Boundary clarity | The response does not pretend tests were run when they were not |

## Constraints
- Do not execute tests automatically.
- Do not replace project-specific framework decisions when the repository already has a clear testing stack.
- Do not claim coverage metrics without a coverage artifact or direct evidence.

## Recommendation Artifact Review

Apply this review only to substantial authored test plans, designed test sets, coverage-gap plans or requested test artifacts. A narrow lookup or externally authored test review keeps its existing route. The writer owns the authored plan or tests; the separate reviewer checks specified behavior, existing framework, risks, assertions and gaps against the sources. Source inspection and design acceptance do not establish test execution, observed coverage or release readiness. No participant silently runs tests through this review.

Existing domain checks, source rules, uncertainty labels, required artifact contents and permission boundaries remain mandatory. Producing an artifact includes its domain observations or findings; the independent review findings below are a separate list of defects in that artifact. Required output formats apply to the writer's artifact, not coordinator dispatches or reviewer findings. Completing an author checklist or assigning an author score does not accept the artifact. This review does not replace another workflow's approval, identity, path-fit or bounded return protocol, and grants no wider execution authority.

### Three Roles
- **Coordinator**: dispatches and counts the reviewer's current open findings. The coordinator does not write the artifact, findings or repairs, and cannot waive a finding.
- **Writer**: writes the artifact only and repairs it from the review findings. Resume the same writer for every revision; do not start a fresh writer for a revision.
- **Reviewer**: did not write the artifact, checks claims against the sources and retained domain rules, and writes findings only. The reviewer does not rewrite the artifact. Resume the same reviewer for every later round.

Use actual separate participants. If they or their resumed contexts are unavailable, report required review as incomplete; do not substitute self-review, coordinator authorship or simulated roles. Each participant stays within the existing allowed reads, writes and checks.

### Finding and Repair Cycle
1. The coordinator dispatches the scoped task, sources, constraints and retained domain requirements to the writer. The writer produces the artifact using the domain workflow.
2. The coordinator dispatches the current artifact, original task and sources to the separate reviewer. The reviewer is hostile in the ordinary sense: verify each material claim, cite the source, and do not invent a defect to fill a section. Unsupported claims, misleading certainty or omitted required uncertainty warrant source-grounded findings; a clearly labeled permitted gap is not itself proof of a defect.
3. Each review finding has an identifier, severity, artifact location, what is wrong, a concrete repair, source evidence and status `open`. With no defects, return an empty finding list and explicitly report zero open findings.
4. The coordinator returns every open finding to the same writer. The writer repairs the artifact and responds to each received identifier with `addressed` and what changed, `wontfix` and a technical reason, or `needs-user-input` when only a human can choose. These are repair dispositions, not authored review findings or acceptance decisions. Findings awaiting a human answer remain unresolved.
5. The same reviewer checks the revised artifact and rewrites the current finding list: drop fixed findings; keep bad repairs open; add new defects as open. The writer cannot close a finding. If the reviewer reopens a finding marked `wontfix`, ask the user about that stalemate and treat the answer as final for that finding. The writer applies the answer; the reviewer honors it when rewriting the list. Unrelated findings still require resolution.
6. The coordinator counts the reviewer's current open findings and resumes the same writer and reviewer until the reviewer explicitly reports zero open findings on the current artifact. There is no round cap. Do not finalize while any finding is open, while a required human answer is pending or while required review is incomplete. The inner finding count does not decide acceptance by a wider workflow.


Capability resource: `resources/capability.json`
