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

## Mutation Order

1. inspect current branch and worktree state
2. create or switch to the working branch
3. verify the canonical source and generated outputs you are about to touch
4. make the smallest coherent set of edits
5. validate the relevant surfaces before proposing merge or release

## Scope Rules

- Keep commits and branches logically scoped.
- Do not hide unrelated cleanup inside docs, release, or surface-generation changes.
- If a task crosses docs, generated artifacts, and scripts, call out the dependency chain explicitly.

## Verification Expectations

- When command examples or release behavior change, verify them against current wrapper help or script behavior.
- When generated-surface paths change, verify them against the actual emitted directories.
- Treat validation failures as blocking until explained or fixed.
