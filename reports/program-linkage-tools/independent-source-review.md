# Production linkage independent source review

## Commit Under Review

Source candidate `e627bd1c9c83fb8507f77bd57fee78d61bb6cb72`, committed range from `3782da241e7c4fdb973d9f96f5592926c28e07a4`. Reviewed full graph/trace scripts and bounded schema interpreter, both result schemas, actual production schema identities, source candidates, proposed maps/registry, narrow shared-reference policy/verifier diff, focused tests and source receipt. Source acceptance precedes controller composition/UAC/generation/hosted checks.

## Findings

**LNK-SRC-001 — high — supplied null test artifact is silently treated as absent.** `trace_check.py:290` passes decoded `null` as `None`, which `check_trace` interprets as omitted tests. Independent CLI invocation with `--tests tests.json` containing `null` returned exit 0, `mechanical_passed: true`, `tests_status: not_supplied`, `test_link_validation: not_supplied`, no errors, while recording a tests input hash. A selected invalid TestDesign must fail production shape and must never remove the requested test-coverage gate. The isolated copied-script/schema fixture remains `/private/var/folders/42/sm0kpcrx151_t0cqygfwb3f80000gp/T/linkage-independent-trace-khly14gd`.

**LNK-SRC-002 — medium — escaped unpaired Unicode surrogate breaks the result protocol.** The shared `decode` accepts an ASCII JSON escape for an unpaired surrogate in a task ID; the schema treats it as a string. `emit` uses `ensure_ascii=False` and ordinary UTF-8 stdout, raising UnicodeEncodeError. Independent graph CLI returned exit 1, empty stdout and traceback for a task ID formed as T plus escaped U+D800. The duplicated trace decoder/emitter has the same exposure in returned IDs/pointers/matrix. The fixture remains `/private/var/folders/42/sm0kpcrx151_t0cqygfwb3f80000gp/T/linkage-independent-unicode-7pa1r64k`. No recursive cleanup was performed.

## Scope Assessment

The explicit TaskPlan sibling exception remains tightly limited by exact owner/source/destination/ref and paired binding/direct edges. Canonical owner admission and detached consumer consistency/authenticity are accurately separated; no general URL/schema resolver or new receipt format was introduced. Source-receipt resource/code hashes match. Graph readiness and null observations, trace optional modes and production-schema parity have meaningful focused checks. Candidate SSOT changes are additive. Proposed trace registry/map are correctly not installed yet.

Independent selected checks: **12 passed in 0.91s**, covering schema parity, graph/null/large-cycle behavior, actual mechanical positive/near-miss and canonical/detached reference rules. The worker's 275-source-test pass is recorded evidence, not a quality score. Its two broader generated-state failures remain pending composition/generation, not waived.

## Message Assessment

Reviewed source behavior is a coherent linkage-helper slice with an explicit narrow shared-schema infrastructure amendment. No build, native behavior, main landing or release claim is accepted from the source commit.

## Recommended Fixes

1. Preserve whether `--tests` was supplied independently of decoded value. Explicit JSON null must produce structured TestDesign shape failure (exit 1), empty matrix and supplied/not-assessed test state, with its input hash retained. Keep actual omission not_supplied. Add CLI negative tests for null and other invalid selected top-level values; do not silently coerce them or expand the public API without need.
2. Handle unsupported Unicode deterministically in both scripts before result emission: either reject unpaired surrogates in decoded keys/values with a stable structured input error, or adopt an explicitly reviewed safe escaped serialization policy. Preserve valid non-ASCII/astral text and exact identifiers; do not normalize/drop characters. Add CLI cases for lone high/low surrogates, valid surrogate pairs/non-ASCII, and both success/error result paths. Every handled input must retain one valid JSON result and declared exit behavior instead of traceback.

## Merge Readiness

`review_status: complete` for this source scope; **blocked with two open findings**. Separate `semantic-review.json` records actual independent rejection of the near-miss against exact fixture hash: R1 only permits authorized rows, but T1 and TEST1 require forbidden rows. The actual checker mechanically passed it while leaving semantics/behavior not_assessed. This satisfies the bounded negative semantic observation, not overall source acceptance or a comparative-quality claim.

No Core source/product edit, build, UAC, registry installation, shared-metadata generation, Git mutation, new agent or publication was performed. Final composition, detached generated packages, CI wiring/local/hosted checks and main parity remain separate gates. Same author repairs these findings; same reviewer rechecks exact new bytes.
