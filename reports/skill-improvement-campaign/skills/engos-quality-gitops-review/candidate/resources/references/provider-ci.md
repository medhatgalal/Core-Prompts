# Provider and CI evidence

Use only providers required by the repository contract. Confirm host/project identity and installed CLI support; prefer `gh` for GitHub and `glab` for GitLab, with explicit repository/project and immutable identifiers. Redact sensitive logs and never print credentials. Provider docs vary by version/tier; inspect actual policy rather than assuming every feature exists.

## Evidence record
For each relevant requirement capture: provider/repository, PR/MR and current source/base, tested commit and its relationship to source/base, event/pipeline type, required job/check and source application where relevant, run/job/attempt ID, raw status/conclusion, observed time and URL. Keep complete relevant pagination and child/downstream job dependencies. Record access failures or omitted pages as gaps. Do not replace a failed observation with a guessed success.

GitHub head checks, test-merge checks and merge-queue checks can legitimately target different SHAs. Determine the required subject from the current PR/protection/queue state. A green head run does not prove a queue result. A different synthetic merge SHA is not automatically a failure if its lineage and required context match. Required checks can be tied to a source GitHub App; matching only a display name is insufficient.

GitLab branch, merge-request, merged-results and merge-train pipelines serve different subjects. Merged-results uses an integrated source/target result; a train includes earlier queued changes. Identify which current pipeline the merge requirement uses. A canceled obsolete train is historical, not proof the replacement train passed or failed. Source updates, target updates and train reorderings may invalidate earlier evidence.

## Interpret results before judging
- GitHub may accept `success`, `skipped` and `neutral` for required checks. A skipped job did not execute validation; a filtered workflow may leave an expected check pending. Apply the actual requirement: policy acceptance alone does not satisfy a separate requirement that tests executed. Do not block a deliberately optional skip.
- GitLab `allow_failure` can leave a pipeline successful despite a failed job. Manual jobs may be optional or blocking depending on effective rules. Inspect the job requirement and configuration; do not classify every manual job as a failure or every green pipeline as complete execution.
- Distinguish running/pending, canceled/replaced, failed, inaccessible and absent results. Inspect the relevant attempt and job log before attributing cause. A runner outage, timeout, configuration problem, flaky symptom and deterministic product failure need different next actions. Evidence of one failure is not proof of a flaky test.
- Report precise observed error and next diagnostic. A rerun is a mutation requiring execution scope, not a way to hide a failed attempt. Retain prior attempt history where it affects confidence.

## Review and merge
Read current draft/conflict/review/discussion/protection state and bind applicable review receipts to the revision under repository policy. Do not invent approvals from a clean diff. If execution is authorized, refresh source/base and required evidence immediately before the protected merge/queue operation; use expected-head controls where supported. If state moved, stop that mutation and reassess affected requirements.

After a merge, verify actual resulting target commit, inclusion of the reviewed change and required post-merge runs. Squash/rebase changes commit identity: establish inclusion with the provider merge result and the reviewed resulting content, not source-commit ancestry alone. For a two-provider contract, determine whether exact commit parity or a documented content mapping is required. Equal trees do not prove identical history. If one provider succeeds and the other does not, preserve both results and propose a scoped reconciliation; never force-push or re-merge blindly.

## Source basis
Checked 2026-09-10: [GitHub required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), [GitLab merge trains](https://docs.gitlab.com/ci/pipelines/merge_trains/), [GitLab CI YAML](https://docs.gitlab.com/ci/yaml/). Recheck current official help/docs when version-sensitive behavior is material.
