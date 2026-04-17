---
inclusion: always
---

# Repo Workflow Steering

## Purpose

Keep repository changes reviewable, reversible, and easy to isolate.

## Scope

- This file is the canonical rule surface for branch workflow and repo mutation sequencing.
- Do not place branch-governance policy only inside human docs.

## Branch Rules

- Do not make substantial repo changes directly on `main`.
- Create or switch to a dedicated branch before multi-file edits, workflow changes, docs rewrites, release work, or canonical SSOT changes.
- Prefer branch names that describe the work clearly.
- If the worktree already contains unrelated user changes, preserve them and avoid mixing them into the branch scope.
- When several independent change streams are active, prefer separate `git worktree` checkouts rooted at dedicated branches instead of stacking unrelated edits into one checkout.
- Keep one worktree per coherent branch scope when UAC engine work and docs or prompt artifacts are moving concurrently.

## Mutation Order

1. inspect current branch and worktree state
2. create or switch to the working branch
3. verify the canonical source and generated outputs you are about to touch
4. make the smallest coherent set of edits
5. validate the relevant surfaces before proposing merge or release

## Source-of-Truth Rule

- When a repo uses canonical source plus generated outputs, edit the canonical source first and regenerate emitted artifacts instead of hand-patching generated files.
- Only edit generated outputs directly when the generator is broken and the direct edit is part of fixing that generator path.
- Release notes and reviews should describe the canonical change first and the regenerated outputs second.

## Scope Rules

- Keep commits and branches logically scoped.
- Do not hide unrelated cleanup inside docs, release, or surface-generation changes.
- If a task crosses docs, generated artifacts, and scripts, call out the dependency chain explicitly.

## Verification Expectations

- When command examples or release behavior change, verify them against current wrapper help or script behavior.
- When generated-surface paths change, verify them against the actual emitted directories.
- Treat validation failures as blocking until explained or fixed.
- Run build-dependent validation serially unless the tooling is known to be race-safe. Do not trust failures caused by validating or smoking half-generated outputs.
- When a change will overwrite installed local surfaces, run a dry-run deploy and compare the generated result against the currently installed state before the real install step.
