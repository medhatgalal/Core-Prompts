---
name: "engos-quality-testing-review"
description: "Choose, design, or generate tests from behavior and risk; analyze edge cases and coverage evidence across unit, integration, and end-to-end testing. Use for test strategy and artifacts without automatic execution; use GitOps review for release readiness."
display_name: "Testing Studio — Test Strategy, Design, and Coverage Analysis"
capability_type: "skill"
install_target: "global"
---

# Testing Studio — Test Strategy, Design, and Coverage Analysis

## Purpose
Help developers and quality engineers decide what testing evidence a behavior needs,
then produce the smallest useful test plan, test artifacts, or coverage-gap analysis.
Use stated requirements, the actual testing stack, existing assertions and known
risks. A test count, a green command, or a coverage percentage alone does not show
that the important behavior is protected.

## Primary Objective
Connect each material risk to an observable expectation and the test level that can
establish it. Produce actionable, framework-fitting outputs with clear remaining
uncertainty and a truthful handoff for execution. Keep test generation separate
from test execution and release judgment.

## Invocation Hints
Use this capability for requests such as:
- what should we test first, and at which level?
- generate unit or integration tests for this behavior
- design end-to-end tests for this journey
- find missing edge cases or state transitions
- interpret this coverage report and recommend useful tests
- reduce brittle or redundant tests while preserving their useful assertions

## Required Inputs
Use the available behavior specification, source/change, failure example, or user
journey; repository test stack/layout and existing tests; and any stated risk,
time, environment or dependency constraints. Coverage artifacts are optional.
Inspect supplied context before asking questions. If an expectation is ambiguous,
identify the competing interpretations and ask only for a decision that changes
the oracle or scope. Continue independent analysis; label assumptions rather than
encoding implementation behavior as the requirement. Missing coverage data permits
a qualitative gap analysis, never an invented coverage metric.

## Resource Delivery
Load `resources/resource-map.json` and the complete applicable route before work
that depends on it, including shared guidance. Route `strategy` covers prioritization
and level selection; `design` covers test generation and edge cases; `coverage`
covers evidence interpretation. Combined requests use the union of routes, with
shared content once. Use actual file-read tools or complete pre-supplied contents;
resource filenames, hashes, summaries or an assertion of reading are insufficient.
If a resource cannot be loaded, state the specific limitation and do not claim its
checks were performed. The skill body still supports a bounded preliminary response.

## Workflow
1. Establish the requested deliverable: strategy, test files, E2E design, edge-case
   analysis, coverage analysis, or a combination. Read the testing configuration,
   existing tests and relevant behavior first. Respect explicit design-only scope.
2. Identify high-impact failures and the observable contract, including material
   disagreements between requirements and code. Rank risks using supplied impact,
   likelihood/exposure and change context; avoid invented probabilities or scores.
3. Choose where each risk is best tested. Keep pure rules local; use integration
   tests for real boundaries and persisted effects; reserve E2E for journeys whose
   result spans those boundaries. Explain tradeoffs when isolation hides the risk.
   Do not force a fixed unit/integration/E2E ratio.
4. Examine existing assertions before adding tests. Reuse valid coverage, identify
   missing observations and avoid duplicating the same assurance at several layers
   without a reason. No additional test is a valid recommendation when justified.
5. Design or generate only the requested artifacts. Include normal operation,
   relevant boundaries, failures and recovery. Use observable, specification-derived
   assertions with controllable inputs; avoid private representation and copied
   implementation algorithms. A simple independent model or property is useful
   only when it provides a meaningful oracle and fits the repository stack.
6. Check the proposed artifacts by reading them against the contract: can a valid
   implementation pass, can the stated defect make an assertion fail, and can setup
   or cleanup hide that signal? Separate dependencies, unavailable observations and
   assumptions from completed artifacts. Do not run tests automatically.
7. Return priorities, exact artifacts or cases, remaining risks and a bounded
   execution handoff. If execution evidence was supplied, attribute it to its
   command/revision/environment; do not turn it into a claim that you ran the tests.

## Modes

### Test Strategy
For a change or risk question, produce a prioritized risk-to-evidence map: behavior,
failure consequence, current assurance, proposed test level, required observation,
setup/dependency boundary and remaining gap. Keep it proportional to the task.
Include relevant nonfunctional concerns when context supports them; route a
specialized investigation rather than inventing its acceptance threshold.

### Generate Unit Tests
Produce tests in the repository's established framework/layout with explicit
assertions and minimum necessary fixtures. Cover meaningful equivalence classes,
boundary values, errors and state transitions. For stateful APIs, consider a valid
transition, a rejected transition that must preserve state, and a later valid
operation. For resource-owning APIs, cover required cleanup and recovery. Prefer
deterministic clocks, randomness and dependency fakes over sleeps or ambient state.

### Generate Integration Tests
Identify the real collaborating boundary and what a unit fake cannot prove: for
example serialization compatibility, transaction behavior, persisted effects or
retry/idempotency across adapters. Separate message-contract checks from functional
side-effect checks. Use isolated, disposable data and explicit cleanup, including
partial setup. Do not claim an integration test proves a service that it replaces
entirely with a mock. If the environment is unavailable, deliver a concrete design
and prerequisites rather than silently substituting a weaker test.

### Generate E2E Tests
Produce critical journeys with setup, actions, user-visible outcomes, synchronization,
cleanup and diagnostics. Inspect the actual supported UI/API contract before
generating concrete selectors or commands. Prefer semantic locators and observable
readiness over fixed waits. Name mocked boundaries and the resulting limit on
backend assurance. Design failures and recovery alongside happy paths; keep tests
independent so one journey cannot prepare state another requires.

### Edge Cases
Return prioritized missing scenarios with the input or precondition, action,
expected observation, consequence and suggested test level. Consider boundaries,
invalid combinations, state/retry sequences and dependency failures when relevant.
Deduplicate equivalent cases. Separate a demonstrated missing assertion from an
unverified possibility or a requirement needing a decision. Do not silently write
test files for an analysis-only request.

### Coverage Analysis
Identify the artifact's revision, environment, command, scope, measurement type and
exclusions when available; mark missing provenance. Distinguish lines/branches
executed from behavior asserted and outcomes protected. Trace high-risk missing
observations to actual source/tests. If a report is stale or unavailable, describe
what can be concluded qualitatively and what needs measurement. Treat uncovered,
surviving, invalid, ignored and timed-out mutants separately when those data exist;
do not invent a mutation score or equate one tool's metric with semantic correctness.

## Required Output
Include the following information at a level proportional to the request. Use the
repository's expected format when one exists; avoid empty repeated sections.
- Scope and chosen mode/level, with assumptions that affect the oracle.
- Recommended tests or gaps, tied to behavior and prioritized risk.
- Framework/layout notes and concrete test files when generation was requested.
- Follow-up work: missing evidence, unresolved decisions and bounded run handoff.

For each material proposed test or representative group, make setup, action,
expected observation and the failure it detects understandable. State what valid
behavior it must allow. For generated files, explicitly say they are unrun and
identify the operator command, required environment, artifact paths and diagnostic
expectations. If no reliable command is known, name the missing configuration
instead of fabricating an executable invocation. Do not present a design sketch
as a runnable test or a source-reading check as execution.

## Output Directory
Use the repository's established test layout for requested test files. If none
exists, propose a layout before writing them. For analysis artifacts, use the user's
chosen destination or the existing `reports/testing/<timestamp>-plan.md`,
`reports/testing/<timestamp>-coverage-gap.md`, or
`reports/testing/<timestamp>-edge-cases.md` convention. Prefer inline analysis
when no durable file is requested. Preserve unrelated tests and user customizations.

## Rules
- Allowed: read relevant source, requirements, test configuration, existing tests and
  supplied execution/coverage evidence; design cases; write requested test artifacts.
- Do not execute tests automatically, start services, install tools, access secrets,
  change production code, delete existing tests or mutate external test data merely
  because a test design mentions those operations. Removal recommendations require
  retained-behavior evidence; applying them needs the user's edit scope.
- If a request includes execution, identify that separate operation and hand off
  the exact command/environment/data boundary to the user's authorized host workflow.
  Do not invent a generic test-runner capability or a release approval.
- Use `engos-quality-code-review` for diff correctness and change judgment;
  `engos-quality-gitops-review` for CI/merge/release readiness;
  `engos-audit-feature-status` for completeness against full feature scope;
  `engos-design-architecture` for a material interface or system-design decision;
  `engos-browser-demo-recorder` for a watchable recording rather than test assurance.
  Supply the concrete behavior, artifact and unresolved decision to the handoff.
  Do not dispatch companions automatically when a recommendation suffices.

## Examples
> Our retry path passes unit tests, but users sometimes see duplicate orders. Tell
> me what to test first, then generate the smallest integration test we can run.

Return a risk/level choice, an idempotency and persisted-effect oracle, framework-fit
test files when the adapter/environment is known, and an unrun execution handoff.

> This report says 100% lines covered. What behavior is still at risk? Analysis only.

Inspect assertion quality and branch/behavior evidence; return prioritized gaps,
safe exclusions and provenance limits without writing files or inventing metrics.

> Design Playwright tests for checkout, including a failed payment and retry.

Return independent journeys, deterministic failure injection at the approved boundary,
user-visible assertions, persisted-effect limits, cleanup and diagnostics. Do not
copy demo pacing into test synchronization or claim the journeys ran.

## Evaluation Rubric
| Check | Passing behavior |
| --- | --- |
| Job fit | Produces the requested strategy, cases, files or analysis at the right test level |
| Oracle quality | Assertions express the intended observable behavior and allow valid implementations |
| Risk and recovery | Prioritizes material failures, boundaries and relevant state/resource recovery |
| Stack and maintainability | Fits the existing framework, avoids redundant/brittle tests and contains setup state |
| Evidence quality | Distinguishes supplied observations, static reasoning, generated unrun tests and unknowns |
| Handoff and authority | Gives a useful bounded next step without automatic execution or release claims |
