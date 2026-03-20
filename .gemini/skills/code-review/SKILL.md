---
name: "code-review"
description: "Commit Review for git commit quality gates, scope control, and over-engineering detection."
---
# Commit Review — Git Commit Quality Gate

## Purpose
Use this capability to review a git commit before merge, with emphasis on scope discipline, message quality, evidence-based findings, and over-engineering risk in AI-assisted coding workflows.

## Primary Objective
Determine whether a commit is ready to move forward, blocked by correctness or scope issues, or should be split into smaller focused changes before review continues.

## Output Directory
When file output is requested, default to:
- `reports/code-reviews/<timestamp>-<commit>.md`

## Workflow
1. Capture the exact commit or diff under review.
2. Read the commit message and the actual diff before making any judgment.
3. Check message quality, scope alignment, and implementation complexity.
4. Record findings with file references, concrete fixes, and merge guidance.
5. End with a clear readiness decision: ready, blocked, or split required.

## Tool Boundaries
- allowed: inspect git history, inspect staged or committed diffs, and write review artifacts when asked
- forbidden: silent approval, hidden execution, or claiming code quality is fine without reading the diff
- escalation: if the change crosses into release risk, test gaps, or architecture risk, recommend `gitops-review`, `testing`, or `architecture`

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- review the latest commit
- check whether this diff is too broad
- judge whether AI-generated changes are over-engineered
- tell me if this commit message and change scope are strong enough to merge

## Required Inputs
- commit hash, staged diff, or the default target of `HEAD`
- repository context when the commit depends on surrounding conventions
- any specific review focus such as scope, message quality, or simplicity

## Required Output
Every substantial response must include:
- `Commit Under Review`
- `Findings`
- `Scope Assessment`
- `Message Assessment`
- `Recommended Fixes`
- `Merge Readiness`

## Review Process
### 1. Capture the Commit
Run:

```bash
mkdir -p reports/code-reviews
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
git show HEAD --no-color 2>&1 > reports/code-reviews/${TIMESTAMP}-${COMMIT_HASH}.md
```

After writing the file, read it before producing findings.

### 2. Check the Commit Message
Look for:
- clear summary of what changed
- enough context to explain why the change exists
- note of breaking change or migration risk when relevant

### 3. Check Scope and Complexity
Look for:
- strict alignment between message and diff
- no unrelated refactors mixed with the stated change
- no unnecessary abstractions, patterns, or file spread
- a diff size proportionate to the stated task

### 4. Check Code Risk
Look for:
- correctness issues, missing edge cases, or unsafe assumptions
- missing or stale tests when behavior changed
- security or secrets handling problems
- debug residue, dead code, or inconsistent conventions

## Examples
### Example Request
> Review the latest commit and tell me whether it is merge-ready or too broad.

### Example Output Shape
- commit under review
- findings with file references
- scope and message assessment
- merge readiness decision

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Commit message quality | The message explains what changed and why clearly enough to review |
| Scope discipline | The diff stays tightly aligned to the stated goal |
| Simplicity | The implementation avoids unnecessary abstraction or spread |
| Evidence quality | Findings are based on the actual diff and reference specific files |
| Merge guidance | The response ends with a clear ready / blocked / split recommendation |

## Hard Constraints
- Never skip reading the actual diff.
- Base findings on evidence, not assumptions.
- Flag scope creep immediately.
- Prefer the simpler valid implementation when alternatives exist.
- If something cannot be verified, say so explicitly.


Capability resource: `.gemini/skills/code-review/resources/capability.json`
