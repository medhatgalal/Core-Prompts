# Design tests that expose the failure and recover cleanly

For relevant state, consider sequences rather than only isolated inputs: create,
use, reject, retry, expire/cancel, clean up and use again. Select the sequences the
contract permits; avoid inventing concurrency or monotonic-time guarantees. Include
the exact boundary and at least one nearby allowed input when an inequality matters.

Control time, randomness, I/O outcomes and asynchronous readiness through the
repository's supported seams. Preserve error type/identity only if it is part of
the contract. Verify the fault was injected at the intended seam; a failed fixture
import does not prove application failure handling. For resource ownership, pair
successful acquisition with cleanup even when subsequent setup or assertions fail.
Keep tests independent of order, ambient state and another test's leftovers.

For integrations, distinguish evidence from a fake's configured response from
evidence of real adapter behavior. Assert persisted/reconciled state for a contract
about durable effects. A unit fake can still exercise a consumer's failure policy.
For E2E, prefer user-facing locators and readiness assertions; do not substitute
long fixed sleeps or automatic retries for an understood synchronization boundary.
List fixture setup, teardown, diagnostics and effects on approved test data.

Before handing off generated code, inspect imports, fixture signatures, framework
conventions, oracle independence and failure readability. Reading code is not
executing it. If a dependency or selector cannot be verified, give a concrete
design plus the missing input; do not bury placeholders in a claimed runnable test.

Practice basis: [Playwright best practices](https://playwright.dev/docs/best-practices),
[pytest safe fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#safe-fixture-structure),
and [Hypothesis stateful tests](https://hypothesis.readthedocs.io/en/latest/stateful.html),
reviewed 2026-09-10. Apply equivalent mechanisms in the actual framework.
