# Test oracles for design work

Use this reference when designing or challenging recommended tests in any of the four modes. It supplies design criteria, not permission to execute tests or change implementation.

## Ground the assertion

For each proposed test, identify the requirement and its inspected source location. Derive an expected observable result independently of the implementation under test. Name a plausible faulty behavior and explain which assertion would distinguish it from the required behavior. A requirement ID, a plausible-sounding oracle description or schema validity cannot establish source truth, meaningfulness, acceptance, execution or coverage. Unverified requirements remain assumptions or gaps for review.

Prefer outputs, externally visible state and contractual effects. Internal method ordering or mock call counts alone cannot establish a behavioral claim. Instrumentation can legitimately observe a contractual effect such as an emitted event, attempted delivery, absence of a write or retry limit; state the boundary it observes and the remaining integration gap. Do not ban mocks or instrumentation categorically. Keep state essential to the claim real or use a justified faithful fixture; mocking away rejection or persistence cannot prove it works.

## Worked design challenges

These are hypothetical contracts, not facts about the receiving repository. Confirm its actual contract before adopting them. No examples below were executed.

| Contract assumption | Fixture and expected outcome | Plausible fault and discriminating oracle | Limits |
| --- | --- | --- | --- |
| A token expires at `now >= expires_at` | Fixed clock and otherwise valid token; at equality reject; immediately before accept; immediately after reject | Changing `>=` to `>` wrongly accepts equality. Assert the rejection result at equality and the acceptance result just before it, so always-reject also fails | Clock precision and rejection shape must come from the actual contract |
| A redeemed token cannot be redeemed again | Seed a redeemed token in the persistence boundary used by redemption; second attempt returns the contract's rejection and causes no additional grant | Ignoring redeemed state returns success or repeats the grant. Observe the rejection and grant state; merely asserting a mocked lookup was called still permits that defect | A mocked rejection response does not exercise redemption; identify real integration coverage needed |
| A successful operation emits one contractual notification | Invoke the operation through its public boundary and observe the emitted payload at the controlled delivery boundary | Omitting delivery or sending twice violates the contract even if the return value is correct | Instrumentation is appropriate for the effect; it does not prove remote delivery |

## Command provenance and scope

Read existing test configuration, checked-in wrappers, neighboring tests and relevant repository/CI documentation. Record each proposed command together with the file/section or supplied instruction that supports it and any prerequisites. If a runner or command is unknown, write `unknown` and the missing evidence. Do not guess a package-manager command or imply a command ran because it was discovered. Conflicting sources remain a gap until resolved. Choose the smallest useful designed test set for the requested risk; this capability imposes no blanket full-suite run.

Coverage-only analysis may describe evidenced gaps without inventing tests or requirement IDs. Distinguish source-inspection gaps from measured coverage and cite any actual coverage artifact. Preserve existing tests and implementation; designing a stronger oracle is not a direction to delete code, execute TDD or invoke another skill automatically.

## Optional interchange

When machine interchange is requested, use TestDesign.v1 with the accompanying schema. `execution_status` is always `not_run`; observed execution belongs in separate evidence. `tests` may be empty for coverage-only work, with useful `gaps`. Keep the six required human artifact sections even when JSON is supplied; no JSON sidecar is required for ordinary requests. Empty requirement links explicitly mean unresolved traceability, never verified coverage. The schema checks shape only; the independent reviewer challenges source links, fixtures and faulty-behavior discrimination.

## Source attribution

This guidance is independently expressed synthesis, not copied donor prose, code or templates. Repository-aware command discovery and outcome assertions were informed by [Addy Osmani's TDD guidance](https://github.com/addyosmani/agent-skills/blob/1be8e34187e34647bb83adc3a1323b26ae6f6abe/skills/test-driven-development/SKILL.md). Plausible-fault and independent-expectation checks were informed by [Superpowers Writing Good Tests](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/test-driven-development/writing-good-tests.md). Both inspected revisions use MIT licenses. Their implementation execution, blanket suite and code-deletion instructions are not adopted. No comparative or behavioral benefit is established by this synthesis.
