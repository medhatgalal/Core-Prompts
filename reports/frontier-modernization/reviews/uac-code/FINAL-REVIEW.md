# Final independent UAC implementation review

## Commit Under Review

Staged candidate on `AI/frontier-capability-modernization`, HEAD/base `c9d6de07b4d1918970a5f70350cf50200a6a0ff4`. Scope: UAC quality, baselines, apply, manifest intake policy, quality profiles, capability templates, and their tests; resource assembly inspected as a dependency. `final-files-before.json` and `final-files-after.json` bind the inspected files. All hashes remained unchanged through final verification.

Key SHA256 bindings:

- `src/intent_pipeline/uac_quality.py`: `1eea50dc7ff3a8422d60071899dc7c8ce7391f79f26b45a6b4f74ba1644c94c1`
- `src/intent_pipeline/uac_baselines.py`: `af192ef0b8050391a78354c2f349b0ffb9c93db530d46ff9c46a0cb75ae0ba64`
- `scripts/uac-import.py`: `8db76da1de5aac9b76a6fd99d6ea52125318965e09a92e90aa615aee9325d4af`

## Findings

**No remaining blocking finding in the reviewed UAC slice.** All five original findings and both second-pass findings were independently rechecked and resolved:

| Finding | Final independent observation |
| --- | --- |
| Final selected text can bypass previous quality | Actual apply now refuses subsequently contradictory source before its SSOT write. Final and fallback selection paths both call the complete quality loop. |
| Invalid supplied review can be ignored | All 15 stale/rejected ordering variations block, including invalid extras after a valid review. Conflicting approved mappings also block. |
| Distinct mode headings become one contradiction scope | Separate modes/modules do not conflict; opposite clauses in the same mode still produce a finding. |
| Shorter or mismatched fence edits literal examples | Five fenced/quoted/indented variations remain byte-identical. |
| Malformed review disposition raises TypeError | All 24 malformed requirement-field variations return refusal without an exception. |
| Review revoked after judgment remains cached authority | All 14 lifecycle variations across quality-loop on/off return `stale_evidence` before any fixture writes. These include revocation inside confirmation, bytes-only changes, deletion, malformed JSON, a replacement path, and use of captured paths when CLI paths are omitted. |
| Literal TODO output convention is rejected | The real pitch CLI judge now passes. Literal uncertainty-marker/schema conventions pass while standalone unresolved output slots remain below threshold. |

The apply lifecycle probe uses a real successful CLI judge payload and production `_apply_payload`. For confirmation-time revocation, its only interaction substitution is `input()`, which changes the file and returns `yes`; quality, fidelity, file binding, and writes are production code. The unchanged-review positive control writes the exact source into an isolated fixture. Fixture build failure afterward is expected because generators are deliberately absent; the positive control demonstrates that the gate is not merely rejecting every apply.

## Scope Assessment

Implementation stays within the requested structural assessment and preservation controls. Automatic repair remains limited to heading normalization; absent meaning is reported as unresolved. Effective package checks bind resource content but do not claim model consumption. Requirement review checks bind original/candidate/effective hashes and complete source coverage while explicitly declining to authenticate reviewer identity or certify semantics. Baseline files remain unchanged, and requirement disposition remains separate from behavioral promotion. The manifest's intake-only policy clarification does not prohibit host-authorized runtime review delegation.

The two updated Supercharge baseline tests now assert rejection without required independent review. Their passes demonstrate conservative default behavior, not successful modernization or behavioral efficacy.

## Message Assessment

No implementation commit message exists yet; this is approval of the bound staged code slice, not a commit-message or hosted merge review.

## Independent Verification

Reproducible artifacts:

- `reproduce.py` → `final-original-probes.json`: all original defect controls pass.
- `recheck-variations.py` → `final-variations-result.json`: stale ordering, conflicting maps, malformed fields, scopes, literal fences, real CLI, and revoked-review apply controls pass.
- `final-lifecycle.py` → `final-lifecycle-result.json`: 14 changed-review refusals plus an unchanged-review positive control pass.

Broader command independently executed:

```text
python3 -m pytest -q tests/test_uac_semantic_uplift.py tests/test_uac_source_integrity.py tests/test_uac_quality.py tests/test_uac_baselines.py tests/test_uac_import.py tests/test_uac_promotion_apply.py
```

**All 138 selected tests verified:** the initial run passed 127; 11 failed during fixture setup because another review's temporary directories under `reports/` contained dangling symlinks that `copytree(ROOT)` attempted to copy. The fixture owner confirmed those trees were disposable, root removed them, and all 11 affected tests then passed in 46.33 seconds. The failure log is preserved in `final-tests.txt`, exact retry IDs in `final-fixture-failure-tests.json`, and retry output in `final-affected-tests-rerun.txt`. No code changed between those runs.

## Recommended Fixes

None outstanding for this UAC code slice. Preserve these independent failure/repair records alongside the final hashes. Broader feature delivery, hosted CI, installation, and behavioral evaluation remain separate evidence owned by the parent task.

## Merge Readiness

**READY for the reviewed UAC implementation slice at the bound hashes.** This is structural code and executed regression evidence, not a behavioral promotion verdict. The earlier blocked reports and results are preserved. Reviewer retained writes are confined to review artifacts; production source and Git state were not changed by this review.
