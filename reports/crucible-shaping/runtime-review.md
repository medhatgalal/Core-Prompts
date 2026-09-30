# Bounded runtime code review: Crucible shaping loop

## Commit/diff under review

Current working-tree diffs only for:

- `sources/capability-resources/engos-quality-shaping-gate/scripts/shaping_run.py`
- `sources/capability-resources/engos-quality-shaping-gate/schemas/runtime.schema.json`
- `sources/capability-resources/engos-quality-shaping-gate/schemas/policy.example.json`
- `tests/test_shaping_loop.py` and fixture adaptations in `tests/test_shaping_runtime.py` and `tests/test_shaping_repository_fit.py`

The loop test is untracked in this worktree, so it was reviewed as a new-file diff. No tests were run in this review. The author-reported result of 134 focused runtime, loop, and repository-fit checks is recorded as supplied, not independently verified here.

## Findings

### [P1] Unrelated G2 evidence clears the floor-only retry stop

`Runtime._check_floor_only_repeat` permits another G3 prepare when the accepted G2 snapshot contains any fact absent from the failed review's predecessor. It does not require that the new fact be cited by a load-bearing claim in the retry's G3 `shape-set.json`. `Runtime._validate_shaping_candidate` then accepts claims supported by any old or new G2 fact. The new-fact test accepts a G2 snapshot with an added observation, calls `prepare` for G3, and checks only that preparation succeeds; the fixture's default G3 claim still cites the original source. Thus an unrelated added fact can unlock a same-evidence pitch retry.

Bind clearance to new accepted evidence that the retried G3 candidate actually uses in its supported claim/proof set, with the independent reviewer still judging its material relevance. Keep this as an evidence-binding check, not a runtime content score.

### [P1] A placeholder selected ID with no claims can seal without source evidence

`Runtime._validate_shaping_candidate` rejects a literal empty `selected_parts` list, but it permits a nonempty arbitrary ID with `claims: []`. It also accepts empty G2 coverage; the missing-source fixture explicitly accepts that G2 state and only checks that a later claimed-but-unopened fact is held. No runtime invariant links each selected part to a claim or requires coverage of the selected set. A candidate can therefore pass the no-selection check with a placeholder part and no grounded claims, reaching G3 seal/scoring without source support.

Require selected parts to map to a nonempty, covered claim set before sealing; preserve the explicit walk-away hold for a truly empty selection.

### [P2] Changing an unchecked locator string can look like a new fact

The retry comparison in `_opened_facts` identifies evidence by `(sha256, locator)` and drops the path to make file renames inert. Coverage validation checks the file hash and that locator strings are present, but does not verify a locator against source content. Reopening unchanged bytes and changing only the locator label can therefore add a “new” fact to the set and clear the retry stop. The rename fixture keeps the locator unchanged, so it does not exercise this case.

Use a verifiable fact identity, such as a hash of the cited source span bound to its source hash, or another canonical locator representation validated against source bytes.

### [P2] Reviewer bookkeeping inputs can ground existing claims

`_validate_coverage` accepts any hashed G2 input as opened evidence, including reviewer assignment/context inputs. `_opened_facts` explicitly excludes those paths as bookkeeping for retry novelty, but `_opened_records` does not apply that exclusion; `_validate_shaping_candidate` can consequently accept an existing claim grounded only in reviewer assignment/context material.

Apply a consistent evidence-path policy when constructing G3-eligible opened records, excluding bookkeeping inputs from product/research claim evidence.

### [P2] Malformed applicable journal entries are silently skipped

`Runtime._check_floor_only_repeat` catches `KeyError`, `TypeError`, `ValueError`, and `Hold` while reading candidate failure events and continues. If a potentially applicable `review_returned` event has malformed score or assessment data, it is omitted from the barrier calculation; with no other qualifying event, G3 preparation proceeds. This is fail-open handling for the journal state that carries the prior failure.

Distinguish unrelated legacy/nonqualifying events from malformed events that purport to be applicable. Hold with an actionable recovery message when applicable failure history cannot be classified.

## Requested control-point assessment

- **Prepare/seal:** the floor-only check runs inside G3 prepare before order/input hashes and state pointer construction. Shaping artifact checks run while building the sealed candidate, before seal publication. The two P1 findings above leave bypasses in those controls.
- **Reopen/rename:** the test verifies that reopening and copying identical bytes under a renamed path with the same locator does not clear the stop. Locator-only changes and irrelevant new facts remain uncovered.
- **New evidence:** the test shows a new G2 source can unlock G3 prepare; it does not establish that the new source is relevant to or used by the retry candidate.
- **Legacy profiles:** `shaping_loop` is optional and defaults to the old path when absent; loop validation and retry checks are gated on it. The fixture adaptation removes the flag and loop outputs for the legacy profile. No regression was identified in the diff for omitted-flag policies.
- **Missing source / empty selection:** a claim citing a source absent from accepted G2 coverage is held, and literal empty selection is held before seal. The placeholder/no-claims route in P1 bypasses both protections.
- **Grounded proposals:** proposed extensions require `basis_claims` to identify grounded existing claims; they do not require the proposed behavior itself to have evidence or execution.
- **Scoring:** the example and validator retain the ordered twelve dimensions and minimum dimension/overall floors of 3/4. The new runtime code does not score content; it reads the existing receipt's scores to detect the average-only retry case.
- **Sequence source:** the mechanical validator requires `sequenceDiagram` and rejects `alt`/`else`. It does not validate color, label length, background, or rendered pixels; visual acceptance remains an independent review observation, not runtime self-scoring.
- **Schema/code:** the new research-coverage and shape-set structures are represented in the runtime schema, while conditional requirements and cross-file/hash checks are enforced by runtime code. No blocking schema/code mismatch found within the reviewed diff.

## Current sequence image readback

Reopened `reports/crucible-shaping/sequence.png`. The current pixels visibly include a separate legend reading “UI blue / Store green / Async amber”; the blue, green, and amber role bands are also visible. This records the rendered image only and makes no claim about product implementation or a preferred content-review verdict.

## Scope and readiness

Review stayed within the requested runtime, schema, loop-test, and fixture diffs. No broad or focused tests were run by this reviewer. The updated sequence image was visually re-opened.

**Readiness: HOLD.** The two P1 bypasses mean the same-evidence retry and pre-scoring evidence/selection controls are not yet reliable. The P2 findings also need resolution or explicit disposition before relying on the journal and evidence-classification paths.
