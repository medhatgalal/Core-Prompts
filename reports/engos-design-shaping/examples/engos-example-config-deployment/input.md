# Configuration deployment scenario

Constructed teaching fixture. The system facts and decisions below are explicit
example premises, not assertions about a live product or a performed spike.

Raw input: "Deploy cost settings with the process package without overwriting
settings someone changed in the target environment. Older packages must still work."

Scenario decision C1: one week, two engineers; stop if target override protection
cannot be preserved. Include currency and activity-cost definitions. Exclude cost
results, unrelated configuration and new permission roles. A target admin owns
any explicit force-overwrite decision; default behavior must preserve local edits.
Why now: the scenario customer manually re-enters cost settings after every deploy.

Fixture facts:
- PackageExporter and PackageImporter already deploy process metadata between
  environments. Importer verifies admin deployment permission and compares a
  base revision against the target's current revision before applying an update.
- Target-local configuration edits increment the revision. Mismatched revision
  causes a visible conflict, with no write, unless an authorized admin explicitly
  selects the existing force-overwrite behavior.
- CostConfigStore holds currency and activity costs keyed by stable process UUID.
  Export reads these settings; results and customer transaction data are separate.
- Old package format omits cost configuration entirely. Import treats absent
  optional sections as "leave target unchanged"; it must never mean delete.
- The existing deployment transaction supports validating all included configuration
  before writing and committing it atomically. Validation failure keeps prior state.
- RunningAnalysis reads cost configuration at the start of its next scheduled run.
  This example must not initiate a full data reload or recompute historical results.
- Scenario scale: 100 processes/package, each at most 200 activity entries.
  The existing deployment transaction supports 25,000 configuration records.
- No new transport or credentials: existing encrypted deployment channel and
  deployment authorization apply. The analysis library owns no deployment auth.

Target: local HTML reference. No live deployment, mutation or integration test is
authorized or claimed by this teaching case.
