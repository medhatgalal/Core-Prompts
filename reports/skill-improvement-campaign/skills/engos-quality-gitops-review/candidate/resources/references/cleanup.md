# Cleanup and recovery

Cleanup begins with an exact inventory, not a glob. Record each proposed branch/worktree/artifact path, task owner, reason it is no longer needed, unique commits/content, tracked modifications, untracked and relevant ignored files, active operation/session/process or lock, and retained evidence/recovery location. Avoid exposing file contents unnecessarily. A clean Git status, merged label or old timestamp does not establish disposability.

Use read-only commands such as `git worktree list --porcelain`, scoped status/diff/log, and branch inclusion checks. After squash/rebase merging, inspect the recorded merge result/content; absence of source-commit ancestry alone is not proof of unmerged valuable work, and apparent content equivalence alone does not prove recovery copies exist. Unknown ownership or activity means retain pending investigation.

Before any authorized removal, state exact targets and preservation evidence, check for changes since the inventory and satisfy host destructive-action policy. Prefer supported non-forced operations and recoverable cleanup. Do not remove the current active worktree, other tasks' branches, untracked user material or unique evidence as a side effect. Do not use force/remove/reset to get past an unexplained refusal. Do not delete outside the authorized boundary.

Git worktree removal, metadata pruning and repair are different operations. `git worktree remove` normally expects a clean worktree. `prune` removes stale administrative records for missing worktrees; a moved directory or unavailable mounted worktree may need repair or protection instead. A lock may deliberately preserve an offline worktree. Inspect before recommending either operation. Reflogs can aid local recovery but are not permanent backup or proof that untracked files are recoverable.

For authorized execution, verify each resulting branch/worktree/artifact state and preserved recovery material; report retained targets and why. If interrupted or partially successful, preserve receipts and inspect before resuming. A cleanup plan is not completed cleanup.

Source basis checked 2026-09-10: [Git worktree](https://git-scm.com/docs/git-worktree), [Git reflog](https://git-scm.com/docs/git-reflog). Project-specific ownership, active-session and retention rules govern the actual targets.
