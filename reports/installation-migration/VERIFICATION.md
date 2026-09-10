# Installation migration verification
Status: implementation verified. Current merge/publication status is recorded in [GitHub PR #64](https://github.com/medhatgalal/Core-Prompts/pull/64) and [GitLab MR !66](https://gitlab.appian-stratus.com/medhat.galal/core-prompts/-/merge_requests/66); the observations below are revision-bound evidence.

## Scope
Replaces the unsafe 6646862 implementation in the same PR64/MR66. Initial main baseline 9d481a2; report-only mainline changes through 192fec5 were integrated at f00237ed282962eaa6e752a5b443db718b34c9dd. The approved source plan is PLAN.md in this directory.

## Observed evidence
- Final complete local pytest run on f00237ed282962eaa6e752a5b443db718b34c9dd: 1047 passed, 138 subtests passed, 554.84 seconds. No source changes occurred during this run.
- GitHub runs 34422096929 and 34422093542 succeeded. GitLab MR pipeline 6774108 succeeded; its installer/package group ran 193 tests plus 16 subtests. All were bound to f00237ed282962eaa6e752a5b443db718b34c9dd.
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
Required CI includes the actual installer suites on both GitHub and GitLab; older green checks on 6646862 are not used. Evidence-only changes after f00237e require renewed hosted checks; runtime source remains bound to the reviewed hashes below.
Release assets must be built from merged source and checked independently on both providers. Current user configuration, credentials, schedules, KiroCrew roster, and unrelated work remain unchanged by this development run.

## Final reviewed runtime identities
Max reviewer independently exercised the generated capsule, including reporting command compatibility, and returned PASS. High documentation reviewer returned PASS after checking 99 local links and the scheduling/recovery exceptions.

| Artifact | SHA-256 |
| --- | --- |
| providers.py | 62e350e0edb1c73de766b724411d3a75ea362de59f3bfb84932a844c70c5005d |
| planner.py | c5852c95fc42e85bc140e258a8e29d0101e69b63105072d854c3a3368dd1f8fa |
| generated deploy-profile.py | 776da4098d8d5f1ae0f8f90f55a84e35d85c4e509547f150477e34710997450a |

## Retained lessons
- Package identity is provider + surface + slug + complete roots; see historical/provider isolation tests.
- Missing updater/receipts require trusted release recognition, not target-self-attestation; see catalog tests.
- Installation-wide unresolved conflicts survive narrower successful operations; see installation tests.
- All recovery formats must respect ownership chronology; see actual bootstrap tests.
- Source and distributed capsule stay one implementation via deterministic generation; see capsule tests.
- Test discovery is rooted at tests/ so tracked experiment fixtures under reports/ are data, not automatically executed as product tests.
