---
name: "testing"
description: "Testing Studio for unit-test generation, end-to-end test design, edge-case discovery, and coverage gap analysis."
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
- escalation: if the request is actually a release gate or CI readiness question, recommend `gitops-review`

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
Every substantial response must include:
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


Capability resource: `.gemini/skills/testing/resources/capability.json`
