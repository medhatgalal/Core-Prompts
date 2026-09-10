# Installation migration verification
Status: local verification complete; current-candidate hosted checks and publication pending.

## Scope
Replaces the unsafe 6646862 implementation in the same PR64/MR66. Initial main baseline 9d481a2; upstream report-only changes will be integrated before landing. The approved source plan is PLAN.md in this directory.

## Observed evidence
- Complete local pytest run: 1046 passed, 138 subtests passed. The reporter-launcher compatibility regression added after collection passed separately.
- Trusted catalog: 54 matching pinned release refs; 1482 distinct package versions; 1399 file identities. Real historical fixtures cover v1.12.2's 24 skills/11 agents, mentor, autosearch, missing updater/receipt, and independent Kiro surfaces.
- Actual v1.14.0 old engine installs the new compatible capsule. Newly installed runtime succeeds with source checkout reads denied, creates v2 state, and repeats without scope expansion. Incompatible old saved scope fails without mutation. Reverse-order rollback guard is exercised.
- Transaction tests cover locks, stale plans, interrupted apply/restore, full replacement verification before retirement, later edits, corrupt backups, polling observations and equivalent version prefixes.
- Independent Max implementation review replayed invalid profiles, recursive and cross-provider dependencies, scope preservation, custom registrations/comments, polling and partial-install status. Runtime review passed after fixes; reporter addition separately reviewed.
- Independent High docs review passed; 99 local links/anchors checked. Documentation separates scheduled release acceptance from routine sync and explains observation-aware rollback.
- Two in-memory mutation checks removed successor ownership protection and made a skill imply an agent. Both were rejected by the specific behavioral regression.
- Strict surface validation passed. Runtime capsule and historical catalog deterministic checks passed.
- Native Kiro 2.21.2 validated an installed test agent; list output identified the workspace definition. Global listing also contained pre-existing MCP/resource errors, so global native health is not claimed.
- CLI smoke completed with Gemini discovery exit 41 warning. No model calls or behavioral promotion claimed.
- Read-only live-home preview preserved all unrecognized Kiro agent variants and refused apply because a third-party symlink prevented complete dependency inspection. No home installation was applied.

## Delivery gates
Full tests will be repeated on the final merged candidate. CI must include the actual installer suites on both GitHub and GitLab; older green checks on 6646862 are not used.
Release assets must be built from merged source and checked independently on both providers. Current user configuration, credentials, schedules, KiroCrew roster, and unrelated work remain unchanged by this development run.

## Retained lessons
- Package identity is provider + surface + slug + complete roots; see historical/provider isolation tests.
- Missing updater/receipts require trusted release recognition, not target-self-attestation; see catalog tests.
- Installation-wide unresolved conflicts survive narrower successful operations; see installation tests.
- All recovery formats must respect ownership chronology; see actual bootstrap tests.
- Source and distributed capsule stay one implementation via deterministic generation; see capsule tests.
- Test discovery is rooted at tests/ so tracked experiment fixtures under reports/ are data, not automatically executed as product tests.
