# Configuration deployment — round 2 Intake

Source identity: `engos-example-config-deployment/input.md`. Additional source: shared `examples/round-two-clarifications.md`, C2/C3/C4. All are hypothetical exercise premises, not live decisions or runtime observations (`input.md:3-4`, `round-two-clarifications.md:3-6`). Round 1 remains unchanged.

## Original statement, verbatim

> Deploy cost settings with the process package without overwriting
> settings someone changed in the target environment. Older packages must still work.

Source: `input.md:6-7`.

## Known

The customer repeatedly re-enters settings after deployment. C1 supplies one week/two engineers and a stop if target overrides cannot be protected; currency/activity definitions are included (`input.md:9-13`). C2 distinguishes absent, empty and nonempty input, excludes deletion and prohibits silently overwriting an edit made before commit (`round-two-clarifications.md:38-42`). C3 supplies commit-time comparison, rollback, value validity and ordinary scheduled analysis timing (`round-two-clarifications.md:44-49`). These are source constraints, not author inventions.

C4 newly bounds other configuration to 4,000 records and explicitly supplies the proposed one-currency-record representation, 24,100 total limit, intact rejection outside the supported envelope, currency-only/empty/absence semantics and export abort on read failure (`round-two-clarifications.md:51-62`). This is new hypothetical provenance, not evidence available in round 1.

## Assumed

No new current behavior assumed. C4's supported envelope and rejection obligation are added scenario constraints, not observed product behavior. No race test or render success is inferred (`input.md:35-36`, `round-two-clarifications.md:61-62`).

## Missing

Research must reconcile commit races/force authority, absent versus empty semantics, validation, capacity limits and ownership. Production implementations and acceptance results are deliberately absent.

## Input directions not yet selected

The source's “with the process package” direction remains attributed and unselected at Intake. Normalized need: eliminate repeated entry while preserving target-local settings and compatibility (`input.md:6-13`). No new mechanism is selected here.
