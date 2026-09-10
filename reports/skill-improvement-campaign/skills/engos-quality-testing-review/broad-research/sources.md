# Primary-source research record

Opened 2026-09-10 UTC (2026-09-09 America/New_York). These notes record source
claims and design implications; none measures the Testing skill. Source dates
are stated when known, and current access does not make an older article new.
No vendor ranking or benchmark claim is used as efficacy evidence.

| ID | Primary source actually opened | Supported finding | Proposed application / limit |
| --- | --- | --- | --- |
| S1 | [Google Testing Blog: How Much Testing is Enough?](https://testing.googleblog.com/2021/06/how-much-testing-is-enough.html), June 2021 | Qualification combines unit, integration, critical user journeys and other relevant test types. Code covered by tests can still contain bugs; field failures can inform test gaps. | Select tests from risks and system boundaries, not a universal test-level ratio. Use incident evidence when supplied; do not invent a production incident. |
| S2 | [Playwright Best Practices](https://playwright.dev/docs/best-practices) | Prefer user-visible behavior, independent tests, suitable locators and retrying web assertions. | E2E outputs need semantic observations and isolated data. Mocked UI checks cannot establish real backend persistence. This guidance does not authorize browser access or installing Playwright. |
| S3 | [Hypothesis Stateful tests](https://hypothesis.readthedocs.io/en/latest/stateful.html), served as 6.168.0 | Stateful testing generates actions and values; a simplified model can provide an oracle across operation sequences. | Add state/sequence and invariant test design when it reduces a real gap. A separate model must express the contract, not clone the implementation. Do not mandate Hypothesis in a repository using another stack. |
| S4 | [Coverage.py Branch coverage](https://coverage.readthedocs.io/en/latest/branch.html), served as 7.16.0 | Statement coverage can miss a branch destination; branch data distinguishes that gap. Exclusions change opportunities included in the measurement. | Preserve metric type, revision, scope and exclusions when reading coverage. Do not turn coverage into correctness or require tests for an intentionally excluded impossible branch without checking its rationale. |
| S5 | [Pact: Contract Tests vs Functional Tests](https://docs.pact.io/consumer/contract_tests_not_functional_tests) | Message compatibility and provider side effects are different assertions; a request/response contract does not prove persistence. | Distinguish consumer/provider compatibility checks from integration tests using the real persistence boundary. Pact is an option only if its contract-testing job and stack fit. |
| S6 | [Stryker mutant states and metrics](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/) | Reports distinguish killed, survived, uncovered, invalid, ignored and timed-out mutants; Stryker counts timeouts as detected. | Retain tool-native categories. For this campaign's semantic detection metric, a timeout alone is insufficient and stays separately classified. That stricter local rule is deliberate, not attributed to Stryker. Equivalent or irrelevant mutations need review rather than automatic extra tests. |
| S7 | [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#safe-fixture-structure) | Bundled setup can prevent teardown when a later setup action fails; pairing state-changing setup with cleanup reduces leaked state. | Generate fixture cleanup for partial setup and failed assertions. Use the project's lifecycle hooks; do not copy pytest conventions into every framework. |
| S8 | [OpenAI Models](https://learn.chatgpt.com/docs/models) | The current catalog exposes Astra, Sol, Terra and Luna and adjustable effort; higher effort trades usage/latency for potential task benefit. Availability depends on client/sign-in/rollout. | Compare task outcomes with fixed skill/context instead of choosing from labels. Start a preregistered small model grid; no account-specific access claim follows from documentation. |
| S9 | [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model) | Current Astra guidance says `none` effort is unsupported, warns that accessible instruction files can influence behavior, and notes a tendency to over-test small coding changes. | Preserve unrun authority and bounded test scope as measured controls. Audit actual supplied instructions and runtime exposure. No temperature-based determinism claim or brand-based superiority assumption. |

## Synthesis

The incumbent's intent is useful. The strongest opportunity is an explicit bridge
from risk to test level, oracle, artifact and execution handoff. That bridge spans
all current modes; a unit-only rule patch leaves coverage and integration decisions
largely untouched. A second opportunity is evidence-aware restraint: sometimes the
right output is one omitted transition test, a coverage limitation, or no new test.
These are local design hypotheses inferred from S1–S7, not conclusions that sources
prove this candidate will work better.

No new tool is required for the first candidate. Existing repository test runners,
coverage formats, real adapters, bounded fakes and established browser test tools
are enough. Property/stateful tooling can be recommended when already supported;
mutation tools can diagnose weak assertions when evidence exists. Installing tools,
changing production code or expanding execution authority is not justified by
this research. Specialized performance/security/accessibility testing can appear
in risk strategy with an owner and acceptance oracle, without pretending this
skill is a penetration-testing or load-generation operator.
