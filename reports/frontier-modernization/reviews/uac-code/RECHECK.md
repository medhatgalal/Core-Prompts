# Independent UAC recheck

## Commit Under Review

Uncommitted candidate on `AI/frontier-capability-modernization`, HEAD `c9d6de07b4d1918970a5f70350cf50200a6a0ff4`. Hashes are in `recheck-files-before.json` and `recheck-files-after.json`. This recheck preserves `REVIEW.md` and its initial reproducer results.

## Findings

The five **original examples** now behave correctly: final contradictory text is refused before its SSOT write; explicitly rejected supplied reviews block; mode headings retain scope; literal fences remain unchanged; malformed review fields return failures instead of raising `TypeError`.

Two remaining blocking findings were independently demonstrated:

1. **P1 — Review files are not refreshed when apply begins.** `scripts/uac-import.py:938-943` reads reviews during initial quality; `_apply_payload` around `2273-2275` skips that operation once `quality_result` exists, and `_safe_apply_ssot_text` uses cached `payload['requirement_reviews']`. A real successful CLI judge with an approved review was followed by replacing that same file's verdict with `rejected`. Calling production apply with the original result and the same explicit review path still wrote SSOT. This models a review changed while interactive apply is waiting for confirmation. `recheck-variations-result.json` records `review_changed_after_judge_ssot_written: true`. Fresh `--quality-loop off` invocation correctly refuses the rejected file; the remaining gap is the transition to apply. Reload every explicitly named review, or compare its captured exact digest and fail if changed, after confirmation and before final checks/writes. Preserve review path/digest provenance so cached in-memory approvals cannot silently outlive their files.

2. **P2 — Literal TODO output requirements are mistaken for missing contract content.** `_output_specificity_score` in `src/intent_pipeline/uac_quality.py` returns 4 when it sees any `TODO`, `TBD`, or similar word anywhere in the extracted contract. The unchanged pitch skill explicitly requires a full template with unfinished sections marked `[TODO]` at `ssot/engos-audit-pitch-review.md:432`. Its actual CLI judge now returns `manual_review` with `benchmark category below target: output_specificity (4/10)`. This is a concrete counterproductive prompt requirement: a meaningful output convention must be removed to appease a keyword gate. Distinguish a standalone unresolved authoring placeholder from an explicit output marker, schema value, or uncertainty convention. Add the existing pitch contract as a positive control and retain empty/placeholder-only contracts as negative controls.

## Scope Assessment

The four worker-owned repairs match the original recommendations and retain their structural-only evidence boundary. The `uac_manifest.py` intake-only scope statement continues to introduce no finding. No baseline rewrite or behavioral promotion was performed by this review.

## Message Assessment

No implementation commit has been created; final commit-message assessment remains unavailable.

## Independent Verification

- Original `reproduce.py` rerun: all five original defects are absent. Saved as `recheck-original-probes.json`.
- Additional `recheck-variations.py`: all 15 stale/rejected review ordering cases block, conflicting approved maps block, all 24 malformed requirement-field cases refuse without exception, same-mode contradictions remain detected, separate module headings do not falsely conflict, and all five fenced/quoted/indented literal variants remain intact.
- Actual CLI approved-review positive control: `structural_ready`.
- Actual CLI rejected review plus `--quality-loop off`: `manual_review`.
- Actual apply after review-file rejection: SSOT was written in the temporary fixture. Fixture generation then failed because generators are deliberately absent; that does not undo the observed pre-validation write.
- Broader independently executed test command: `python3 -m pytest -q tests/test_uac_semantic_uplift.py tests/test_uac_source_integrity.py tests/test_uac_quality.py tests/test_uac_baselines.py tests/test_uac_import.py tests/test_uac_promotion_apply.py`.
- Result: **119 passed, 3 failed in 47.15 seconds**. Pitch failure reproduces finding 2. The other two are `test_recovered_supercharge_is_additive_against_historical_baseline` and `test_registry_fallback_works_without_git_history`; both still expect entry-only `additive` despite modularized semantic changes now requiring effective-package assessment and explicit independent requirement disposition. Their expected evidence contract must be updated without weakening default preservation.

## Recommended Fixes

Resolve the apply-time review lifecycle and legitimate TODO false positive, update the two obsolete baseline test expectations with explicit preservation/review semantics, then repeat these exact independent probes and the affected tests. Do not treat current passing counts as approval of the remaining failures.

## Merge Readiness

**BLOCKED.** The original remediation is confirmed, but the demonstrated apply-time review change and output-contract false positive remain unresolved. No canonical source, generated surface, baseline, descriptor, installed state, Git state, or external application was changed by the reviewer; retained writes are review artifacts only.
