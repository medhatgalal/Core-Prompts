# Consume an externally bound committed review package

This route verifies binding, never review quality or authority. Select `verify-package` explicitly; ordinary review remains HEAD/staged/snapshot as requested.

Before dispatch, the controller or authorized direct caller retains task ID, subject implementation owner, actual positive generation, repository identity, exact base, spec/plan hashes and trusted owner source hashes in its own task record. TaskContract has no generation field. Resolve the current candidate independently after implementation; never learn these values from a worker package. Capture actual collector exit and exact stdout, strictly parse its successful receipt and retain result/manifest digests outside the package. Complete ReviewPackageExpectation.v1 outside the package and retain its exact SHA-256 externally. No null identity wildcard or coerced generation is accepted.

Invoke the verified installed code-review owner helper:

```sh
python3 -I <code-review-skill>/resources/scripts/verify_review_package.py --repo <task-worktree> --package <frozen-leaf> --result <exact-collector-stdout-file> --expect <controller-expectation.json> --expect-sha256 <externally-retained-digest>
```

The selected dependencies include `scripts/verify_review_package.py`, the fixed adjacent producer `scripts/review_package.py`, `schemas/review-package-expectation.schema.json` and the producer schema. Python 3.11+, Git and POSIX nofollow descriptors are required; no pip runtime dependency. No network, output writes, package code, staging, checkout, reset or submodule worktree traversal occurs. Missing owner/helper/runtime means unavailable committed binding; do not guess a sibling path. Direct D5 can still use its normal truthful receipt path.

Stdout is one ReviewPackageBinding.v1 JSON line. Exit 0 means matched and `review_status:not_assessed`; exit 2 means rejected evidence or target; exit 3 means invalid expectation/invocation or unavailable context. Absent, malformed or nonzero output is unusable. Never translate matched into ready, approved or clean. Source changes require independently accepted new expected hashes and fresh collection, never renewal from a returned manifest.

Only current clean committed candidates qualify: no staged/unstaged tracked changes or nonignored untracked files; sparse, skip-worktree and assume-unchanged states reject. Keep evidence outputs outside the worktree. Dirty unrelated content stays intact; use a separately hashed dirty snapshot or isolated worktree. Ignored files, submodule worktrees and external state are outside this scope.

After matching, the actual independent reviewer reads the bound diff/source and needed unchanged consumers. Findings.v1 uses target.kind=branch, comparison=range, exact base/head, snapshot_digest=null and included_change_classes=[committed]. The subject owner differs from the reviewer actor/node. Recheck binding before consumption when source, target or evidence changes. Missing findings, unread material or interrupted review remains incomplete/unverifiable. Preserve stable findings and dispositions. Task review never waives final full-branch integration review, hosted CI or GitOps.

Replay uses the trusted producer algorithm, not independent proof of its correctness. Held descriptors and byte rechecks detect observed replacement/tampering; they cannot lock out arbitrary same-UID syscall races or later changes. Matched is not a durable authorization seal.
