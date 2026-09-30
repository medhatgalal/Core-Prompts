# Independent runtime repair recheck

## Scope

Rechecked only the current runtime, runtime/policy schemas, loop tests, and fixture adaptations against the five findings in `runtime-review.md`. No tests were run. This report does not expand the review beyond those findings.

## Prior findings

| Prior finding | Status | Current evidence |
| --- | --- | --- |
| P1: Unrelated G2 evidence clears the floor-only retry stop | **Resolved** | G3 `prepare` requires `shape_basis`, validates each cited span against accepted G2 coverage, and compares it with newly opened facts. The order retains `retry_new_facts`; `seal` requires the selected claim basis to consume one of them. Tests reject both unrelated new evidence at prepare and declared-but-unused evidence at seal, and accept a retry that uses the new source. |
| P1: Placeholder selected ID with no claims can seal without source evidence | **Resolved** | `seal` requires every selected ID to map to a claim; a selected existing claim needs evidence, and a selected extension needs grounded existing basis. The regression test sets a placeholder selection with no claims and expects a hold. |
| P2: Changing an unchecked locator can look like a new fact | **Resolved** | Locators use canonical 1-based `N:M` ranges, are checked against retained UTF-8 source bytes and opened line coverage, and novelty is based on exact line-byte digests rather than locator strings or paths. Tests cover invalid/out-of-range locators and splitting an inspected range without manufacturing novelty. |
| P2: Reviewer bookkeeping inputs can ground existing claims | **Resolved** | `_bookkeeping_path` excludes bound policy files, candidate/draft artifacts, assignment/context inputs, review receipt provenance, and state/accepted/candidate paths from eligible evidence. A test rejects assignment evidence while a separate test accepts a genuine `sources/resources/...` module as evidence. |
| P2: Malformed applicable journal entries are silently skipped | **Resolved** | `_floor_only_failure_facts` validates relevant G3 review-returned events against their sealed subject and receipt structure; classification errors raise `recovery_pending` rather than being skipped. A corrupted score-dimension journal entry is tested to hold before another G3 prepare and leave the state pointer unchanged. |

## Remaining findings

No unresolved P1 or P2 findings remain among the five reviewed items. The current profile also prevents disabling `shaping_loop` for `shaping-gates.v3+rubric.v4`, and retains the 3/4 score floors in the reviewed schema/policy path. These are static code and test-source observations; the focused test results were not independently run or verified in this recheck.

**Recheck result: READY for the five-item repair scope.** This is not a broader release, documentation, or behavioral evaluation.
