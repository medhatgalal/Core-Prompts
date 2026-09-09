---
inclusion: always
---

# Repo Workflow Steering

## Purpose

Keep repository changes reviewable, reversible, and easy to isolate.

## Scope

- This file is the canonical rule surface for branch workflow and repo mutation sequencing.
- Do not place branch-governance policy only inside human docs.

## Delivery Workflow

Use this sequence for implementation, including capability updates requested through an installed path, documentation, `AGENTS.md`, and steering. Honor an explicit review-only, draft-only, or no-merge instruction. For an implementation request without such a limit, complete the PR/MR, mainline verification, and task-owned cleanup sequence; do not stop at a local patch or home installation.

1. Verify runtime/task identity, cwd, branch/HEAD, dirty state, and both remotes. Fetch main and reconcile remote differences before choosing a base. Preserve all unrelated work.
2. Create a dedicated `AI/` branch in a linked worktree from verified main. Keep primary checkouts read-only. Do not substitute a copied dirty checkout or silently include another task's pending migration. Resolve an installed name to its current canonical slug before editing.
3. For a capability addition or behavior change, prepare a candidate (start an existing-skill update from current `ssot/<slug>.md`), then run `bin/uac plan`, `bin/uac judge`, and `bin/uac apply <candidate> --yes` after reviewing the exact passing candidate and write set. Use the existing slug for updates; preserve baseline lineage and curated metadata. An authorized implementation already authorizes its scoped apply; do not ask again merely because the helper supports confirmation. Pure regeneration or unrelated docs/rules edits do not require fabricated capability intake.
4. Edit helper resources under `sources/capability-resources/<slug>/`; regenerate emitted bundles through UAC apply or `bin/capability-fabric build`. Review SSOT and descriptor readback against the candidate. Never patch emitted or installed files as the source fix.
5. Update affected user docs and changelog in the same slice. For steering changes, keep policy in steering, the router in `AGENTS.md`, and explanatory guidance in maintainer docs. Remove contradictory or duplicated rules when replacing them.
6. Run focused tests, contract/topology checks, surface validation, and the required local CI checks serially after generation. Refresh schema docs before strict checks. Review code and docs against the final diff; `structural_ready` does not establish behavioral promotion.
7. Commit a coherent change, push the same candidate to both remotes, and create a GitHub PR and GitLab MR. Verify required hosted checks and review requirements on that exact candidate. Resolve failures before merging; a local pass cannot substitute for hosted evidence.
8. Land the reviewed candidate using a merge sequence that preserves GitHub/GitLab main parity and respects branch protections. Verify both main refs, inclusion of the intended changes, and post-merge checks. If upstream moves, integrate it and renew affected evidence before landing.
9. When installation is in scope, deploy the merged generated bundle separately after an exact dry-run and installed-state comparison; verify installed parity. When a versioned release is in scope, complete its documented package/tag/publish checks separately. Do not infer either result from merge alone.
10. Preserve the useful evidence in the PR/MR or durable repo artifacts, then remove task-owned remote/local branches, linked worktrees, candidates, logs, and temporary exports after verifying they contain no unique or active work. Use recoverable cleanup where applicable and retain anything still needed for recovery. Never clean another task's work or leave a patch-only handoff as the completed deliverable. Report main commit, PR/MR links, checks, deployment/release status when applicable, and cleanup outcome.

## Source-of-Truth Rule

- When a repo uses canonical source plus generated outputs, edit the canonical source first and regenerate emitted artifacts instead of hand-patching generated files.
- Only edit generated outputs directly when the generator is broken and the direct edit is part of fixing that generator path.
- Release notes and reviews should describe the canonical change first and the regenerated outputs second.

## Scope Rules

- When compiling an approved plan or attachment into an execution brief, retain its source reference and carry forward deliverables, limits, prerequisites, sequencing, and verification obligations, including those in surrounding prose. Reconcile completion against that source and later authorized changes, not only the derived checklist. Keep this accounting proportional to the work.
- Use stable task-specific paths and Git history for maintained artifacts. Distinguish required release/run identities from duplicate drafts; keep disposable variants in scoped scratch. At handoff or closure, update working status or label it as a historical checkpoint and point to later delivery evidence.
- Before closing a Core-Prompts development slice with a reusable finding, link its evidence and record the owning rule, documentation or regression location and whether prevention is implemented, pending or deliberately not adopted. Use existing task records; do not add standing rules from untested hypotheses.
- Keep commits and branches logically scoped.
- Do not hide unrelated cleanup inside docs, release, or surface-generation changes.
- If a task crosses docs, generated artifacts, and scripts, call out the dependency chain explicitly.

## Verification Expectations

- Bind completion claims to the assessed artifact/revision and the evidence actually obtained. Source inspection, package identity, content delivery, observed behavior, comparative benefit, and delivery/install state are distinct; report unverified gates and protocol deviations explicitly.
- For release publication, verify downloaded assets from each provider against reviewed package digests and the intended archive/source boundary. A zero exit code, successful transfer, or file extension is insufficient evidence of correct content.
- Before installation, verify the reviewed write set and the current state of protected surfaces. Record pre-existing changes separately from installation effects; refreshing a preservation baseline does not authorize overwriting changed owned files or expanding the approved profile.
- When command examples or release behavior change, verify them against current wrapper help or script behavior.
- When generated-surface paths change, verify them against the actual emitted directories.
- Treat validation failures as blocking until explained or fixed.
- Run build-dependent validation serially unless the tooling is known to be race-safe. Do not trust failures caused by validating or smoking half-generated outputs.
- When a change will overwrite installed local surfaces, run a dry-run deploy and compare the generated result against the currently installed state before the real install step.
