# Interpret what the evidence measures

Read report provenance before its percentage: revision or source identity, command,
environment, included files, exclusions and metric type. Missing provenance limits
the claim; stale line numbers must be reconciled before assigning current gaps.
Distinguish executable lines, branch destinations, assertions and behavior. Do not
infer a missing assertion only from an uncovered line or infer correctness from
full line coverage. Preserve legitimate generated/dead-code exclusions and explain
uncertainty rather than demanding percentage inflation.

For a gap report, connect the specific behavior at risk to existing assertions,
the missing observation and its proposed level/priority. If tests already establish
the contract, say so and avoid a filler list of new tests. If only source and tests
are available, produce a qualitative inventory and a future measurement command
when known; do not claim a measured rate.

When supplied mutation evidence exists, keep its original categories and denominator.
Survival may indicate a weak oracle, an equivalent mutation or an irrelevant change;
inspect the behavior before recommending a test. Runtime/compile failures and
timeouts need their own explanation. Different tools count them differently, so
declare any alternative semantic-detection metric rather than relabeling results.

Execution handoff: identify the test selection, working directory, verified command,
required runtime/configuration and permitted test data; say which logs/report files
should be retained and what outcome distinguishes a product failure from a fixture
or runner failure. Do not run the command automatically or imply release approval.

Practice basis: [Coverage.py branches](https://coverage.readthedocs.io/en/latest/branch.html)
and [Stryker result categories](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/),
reviewed 2026-09-10. Their tool-specific behavior does not define the product oracle.
