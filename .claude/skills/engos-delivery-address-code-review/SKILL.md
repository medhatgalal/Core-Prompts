---
name: "engos-delivery-address-code-review"
description: "Apply selected pull request or merge request feedback with tightly scoped edits, then prepare the fix for re-review. Use only when actionable reviewer comments already exist; use code review for pre-commit or pre-push judgment."
---
# Address Code Review — PR/MR Feedback Resolution

## Purpose
Use this capability when the user wants to address, fix, or resolve actionable review comments left on a pull request or merge request. This is the action counterpart to `engos-quality-code-review`: `engos-quality-code-review` evaluates staged changes, diffs, or commits; `engos-delivery-address-code-review` implements selected reviewer-requested fixes and prepares the branch for re-review.

Use this only after there is an existing PR/MR review thread, inline comment, requested-change discussion, or explicit reviewer note to address. If the user has not received review feedback yet and wants a quality gate before committing or pushing, use `engos-quality-code-review` instead.

## Primary Objective
Read open review comments from a PR/MR, present them to the user, apply the requested changes with minimal scope, and prepare a commit with only the reviewer-requested fixes.

## Choose the Right Review Capability
Use `engos-delivery-address-code-review` when the job is action.

| User Intent | Use | Why |
| --- | --- | --- |
| "Review my staged changes before I commit" | `engos-quality-code-review` | review gate; no mutation |
| "Review this commit for scope and risk" | `engos-quality-code-review` | findings, message quality, and readiness |
| "Read the open MR comments and fix them" | `engos-delivery-address-code-review` | action workflow tied to reviewer feedback |
| "Address only comments 2 and 4" | `engos-delivery-address-code-review` | selected-comment implementation with narrow scope |
| "Check the fix commit after you address comments" | `engos-quality-code-review` | verifies the response stayed scoped |

Do not use `engos-delivery-address-code-review` to proactively improve code, clean up adjacent issues, or review a diff before a reviewer has commented. It should only mutate files that are tied to selected review feedback.

## Tool Boundaries
- allowed: read MR/PR discussions, read source files, apply targeted edits, run git commands for commit and push
- forbidden: modifying code that has no associated review comment, silent bulk refactors, resolving comments without applying the fix
- escalation: if a review comment requests architectural changes or new test coverage, recommend `engos-design-architecture` or `engos-quality-testing-review`

## Companion Capability Matrix

| Situation | Companion Capability | Why |
| --- | --- | --- |
| reviewer requests architectural rework | `engos-design-architecture` | structural decisions need dedicated judgment |
| reviewer requests new tests or coverage | `engos-quality-testing-review` | test design needs a dedicated pass |
| commit readiness after fixes are applied | `engos-quality-code-review` | verify the fix commit is scoped and clean |
| merge/push readiness after addressing feedback | `engos-quality-gitops-review` | branch health and CI checks before merge |
| no reviewer comments exist yet | `engos-quality-code-review` | run the pre-commit or pre-push review gate first |

## Invocation Hints
- address the review comments
- fix the MR feedback
- resolve PR comments
- apply the requested changes from reviewers
- address code review
- address selected reviewer comments
- implement requested changes from MR discussions

## Required Inputs
- an open PR/MR on the current branch (auto-detected) or an explicit PR/MR link
- platform context: GitLab project ID or GitHub owner/repo (detected from git remote)
- which comments to address (all open, or user-selected subset)
- confirmation before editing when comments are ambiguous, broad, or architectural

## Required Output
- `Comments Found` — numbered list of open review comments with author, file, line, and summary
- `User Selection` — which comments the user chose to address
- `Changes Applied` — per-comment summary of what was modified
- `Commit Guidance` — suggested commit message and push instructions
- `Follow-up Review` — whether to run `engos-quality-code-review`, `engos-quality-testing-review`, `engos-design-architecture`, or `engos-quality-gitops-review`

## Workflow

### 1. Find the MR/PR
- Detect platform from `git remote -v` (GitLab vs GitHub).
- **GitLab**: find the project ID, then list open MRs filtered by current branch.
- **GitHub**: find open PRs for the current branch.
- If exactly one open MR/PR is found, use it automatically.
- If none or multiple found, ask the user for the MR/PR link.

### 2. Fetch review comments
- **GitLab**: read MR discussions.
- **GitHub**: read PR review comments.
- Filter out resolved and outdated comments. Focus on open, actionable feedback.

### 3. Present the comments
Show the user a numbered list of open comments with:
- Author
- File and line reference
- The requested change (summarized)

Ask the user which comments to address (all or specific ones).
Do not edit files until the selected comment set is clear.

### 4. Apply changes
For each selected comment:
1. Read the referenced file.
2. Understand the context and the requested change.
3. Apply the fix.
4. If the change is ambiguous or risky, ask the user for clarification before applying.

### 5. Commit and push
- Stage only the files that were modified to address comments.
- Suggest a commit message like: `Address review comments` (with ticket prefix if the branch name contains one).
- Push to the existing remote branch.
- After the fix is ready, recommend `engos-quality-code-review` on the fix commit before asking reviewers to re-check.

## Constraints
- **Only modify code that has an associated review comment.** Do not touch other changed lines in the diff that have no comments.
- If you believe an uncommented change also needs fixing, explain why and ask the user before making any modification.
- Do not resolve/close review threads programmatically — let the reviewer verify.
- Do not mix unrelated changes into the fix commit.

## Examples
### Example Request
> Address the review comments on my current MR.

### Example Non-Goal
> Review my staged changes before I commit.

Use `engos-quality-code-review` for this instead; no reviewer feedback exists yet.

### Example Output Shape
- list of open comments with file references
- user confirmation of which to address
- applied changes per comment
- commit message and push result
- follow-up review recommendation

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Comment coverage | All selected comments are addressed with targeted fixes |
| Scope discipline | Only reviewer-requested changes are made, nothing else |
| User confirmation | Ambiguous changes are confirmed before applying |
| Commit hygiene | Fix commit contains only the review-related changes |

## Review Timing
- commit: when the fix commit is ready for re-review
- pull request: when all comments are addressed and push is complete
- merge: reviewer verifies fixes before approving


Capability resource: `.claude/skills/engos-delivery-address-code-review/resources/capability.json`
