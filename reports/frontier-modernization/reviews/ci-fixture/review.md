# CI fixture repair independent review

**Decision: PASS. No blocking findings.**

## Commit Under Review

Working-tree diff on `AI/frontier-capability-modernization`, based on `f5e92c92e74282707fc42b8bb447d4e9b954bbaa`. No staged change or proposed repair commit message existed at review time. Test file SHA-256: `9304f346c3f30defff0b04b4dbfcea412d0f92eccd130c8f7772bd2ddc25b74a`. Final readback confirmed the same HEAD and file bytes.

## Findings

No correctness or coverage regression found.

- `tests/test_uac_promotion_apply.py:96-112` still provides the all-zero, nonexistent candidate commit and requires the exact `ContractError` message `candidate_revision is not a repository commit`.
- `scripts/uac-import.py:1579-1580` resolves the baseline before the candidate. `_git_commit` at lines 1525-1542 checks real Git commit existence and raises the asserted error. Baseline `HEAD` is available in a shallow clone; the old historical revision was unnecessary to the intended guard.
- Production guard code is unchanged. Candidate rejection occurs before hash and ancestry checks, exactly as before the patch. The test name now states the behavior it has always asserted.
- Independent real ancestry coverage remains unchanged: `tests/test_uac_promotion_apply.py:156-198` creates divergent branches and asserts `candidate_revision is not an ancestor of HEAD`. The valid ancestry path at lines 54-93 also remains. Both tests passed in each full-file run.

## Scope Assessment

Exactly one test file changed: three insertions and three deletions. The mutation changes the test name, replaces the historical baseline revision with `HEAD`, and binds its baseline hash to current canonical SSOT. No production, surface, CI configuration, or ancestry-test edits were needed.

## Message Assessment

Repair commit not yet created. Suggested subject: `test: make nonexistent promotion candidate fixture shallow-safe`.

## Verification

1. Current checkout: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/test_uac_promotion_apply.py -q` — **14 passed in 16.28s**.
2. Created local `file://` clone with `--depth 1 --single-branch --no-tags --branch AI/frontier-capability-modernization`. Verified `--is-shallow-repository=true`, reachable commit count `1`, and HEAD `f5e92c92e74282707fc42b8bb447d4e9b954bbaa`. No network or remote write used.
3. Before overlay, the original single test failed at `git rev-parse 22654fb`, exit 128; pytest returned 1 (**1 failed in 0.52s**), reproducing the unavailable historical fixture.
4. Overlaid only the current `tests/test_uac_promotion_apply.py`. The full file passed: **14 passed in 11.27s**. Clone diff confirmed the same one-file, three-insertion/three-deletion change.

Logs and commands are in `shallow-evidence.json`, `before-repair.log`, `after-repair.log`, and `reviewed.diff` beside this report. Disposable clone retained at `/private/tmp/core-prompts-ci-fixture-nv5bjy1c/shallow` for controller-owned cleanup.

## Recommended Fixes

None.

## Merge Readiness

The fixture repair is ready to commit and submit to hosted checks. This independent local review does not establish renewed GitHub/GitLab CI, merge, release, or installation success.
