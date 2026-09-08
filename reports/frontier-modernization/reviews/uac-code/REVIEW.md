# Independent UAC implementation review

## Commit Under Review

Uncommitted implementation on `AI/frontier-capability-modernization`, base/HEAD `c9d6de07b4d1918970a5f70350cf50200a6a0ff4`. Scope: `uac_quality.py`, `uac_baselines.py`, `uac-import.py`, quality profiles, capability templates, and `test_uac_semantic_uplift.py`; resource assembly inspected as a dependency. Reviewed the `uac_manifest.py` intake-only policy clarification as an addendum. `inspected-files.json` records the file hashes. Root began changing `uac-import.py` during finalization; this is a blocked pre-fix review, not approval of that subsequent version.

## Findings

1. **P1: Apply reuses quality evidence without judging the final selected text.** `scripts/uac-import.py` `_apply_payload` around lines 2258-2264 skips quality when a payload already contains `quality_result`. `_safe_apply_ssot_text` around lines 1810-1845 rechecks imported and historical fidelity only. A genuinely successful CLI judge result can therefore be paired with a subsequently changed captured source containing unconditional opposite instructions, and the actual apply path writes that contradictory SSOT. The fixture reports `real_apply_wrote_conflicting_final_text: true`. Its final status is `apply_failed_validation` because the isolated fixture deliberately lacks generators; the unauthorized-by-current-quality write has already happened. Fix: select and normalize the exact write bytes, refresh reviews/resources, rerun the complete quality pass on those bytes before any SSOT/descriptor/baseline writes, and refuse mismatched cached evidence.

2. **P1: Explicit rejected or stale requirement reviews are silently ignored.** `src/intent_pipeline/uac_baselines.py:165-172` returns the first matching approved review and drops every invalid result; `scripts/uac-import.py` `_run_quality_for_payload` only checks the outer schema. The real CLI judge reports `structural_ready` even with `--requirement-review` naming `{"schema_version":"UACRequirementReview.v1","slug":"wrong","verdict":"rejected"}`. Exact preservation can pass while an operator believes a supplied review was honored. A stale extra review after a valid first match is similarly unexamined. The `quality-loop=off` early return also bypasses reading the option entirely. Fix: validate every explicitly supplied file against the applicable original source/baseline, final candidate, and effective package; reject invalid/unmatched/conflicting files and retain path/digest/disposition evidence. Never conflate absent reviews with invalid supplied reviews.

3. **P2: Heading scopes are discarded before contradiction detection.** `src/intent_pipeline/uac_quality.py:762-771,775-794` drops headings and groups opposing clauses globally. `## Review mode / Never execute the prompt` plus `## Execute mode / Always execute the prompt` is called an unconditional conflict. This blocks coherent mode-specific instructions and encourages adding redundant prose merely to satisfy the detector. Fix: carry scope/provenance through parsing and compare only clauses known to apply in the same scope. Cross-module package assembly needs the same discipline.

4. **P2: Fence handling changes literal examples.** `src/intent_pipeline/uac_quality.py:734-739` toggles a boolean for any three-or-more backtick/tilde prefix. A three-backtick line inside a four-backtick block is not a closing fence, but the implementation treats it as one and renames the following literal `## Output Contract`. `_active_instruction_lines` and `_section_bodies` also forget opening fence length. Fix: use shared parsing that preserves fence delimiter, minimum length, valid closing syntax, and quoted/indented examples; normalization must modify actual headings only.

5. **P2: Malformed review dispositions escape validation as TypeError.** `src/intent_pipeline/uac_baselines.py:150-154` performs set membership on an unvalidated value. A JSON array/object `disposition` raises `TypeError` instead of producing a structured refusal. Reviewer IDs are also checked only for truthiness rather than nonempty string type. Fix: validate JSON types before comparisons/membership and expose actionable validation failures without traceback. Keep the explicit statement that identity is attested, not authenticated.

## Scope Assessment

The substantive changes match the requested mechanical diagnostics, conservative repair, effective-package checks, and optional externally reviewed preservation exception. No unrelated baseline rewrite or automatic behavioral promotion was found. Baseline scenarios remain visible as failed after approved disposition, while the reported state explicitly remains `behavioral_pending`. The new manifest intake scope clarification appropriately separates metadata intake restrictions from host-authorized runtime review delegation.

## Message Assessment

No implementation commit exists yet, so no final commit message can be assessed.

## Recommended Fixes

Resolve findings 1-5 and retain the discriminators below as regression evidence. In particular, tests must cover the real CLI option and actual pre-write apply path, not only the fidelity helper. Review identity authenticity and the semantic validity of the mapped requirements remain external judgments; hashes and complete line coverage do not establish either.

## Independent Verification

- `python3 -m pytest -q tests/test_uac_semantic_uplift.py`: 17 passed.
- `python3 -m pytest -q tests/test_uac_source_integrity.py tests/test_uac_semantic_uplift.py`: 49 passed.
- `python3 reports/frontier-modernization/reviews/uac-code/reproduce.py`: reproduced all five findings. Results saved in `reproducer-result.json`.
- Actual CLI positive control: code-review source judged `structural_ready` without the rejected review; adding the rejected review still returned `structural_ready`.
- Actual apply fixture used production apply code, a prior real CLI judge result, a temporary workspace, and no mocked quality/fidelity checks. Only the module root was redirected to that fixture. The fixture was deleted through `TemporaryDirectory` lifecycle cleanup.

## Merge Readiness

**BLOCKED** pending fixes and independent rerun on a stable final file snapshot. Passing existing tests did not cover the independently demonstrated failures. No source, baseline, descriptor, generated surface, installed file, Git state, or external application was changed by this review; review artifacts are the only retained writes.
