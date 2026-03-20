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

## Core Principles
- **Scope discipline**: changes must match what the commit message describes
- **Simplicity first**: flag over-engineered solutions and unnecessary spread
- **Evidence-based**: review the actual diff, not assumptions about intent
- **AI-aware**: assume AI-assisted changes can drift outside the requested scope unless proven otherwise
- **Actionable output**: every finding should give the reviewer a concrete next move

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

## Companion Capability Matrix
Use companion capabilities deliberately instead of flattening every review into one generic answer.

| Situation | Companion Capability | Why |
| --- | --- | --- |
| release readiness, changelog, CI, packaging, or merge gates matter | `gitops-review` | commit quality alone is not enough for release or branch health |
| behavior changed and test confidence is weak | `testing` | test coverage and edge-case discovery need a dedicated pass |
| interface, architecture, or migration risk is material | `architecture` | structural risk needs architectural judgment, not just commit review |
| doc drift or example drift is part of the commit | `docs-review-expert` | keep documentation review explicit and separate |

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
- related issue or ticket context when that exists

### 3. Commit Message Quality Checklist
Check:
- [ ] title describes **what** changed rather than implementation mechanics
- [ ] body explains **why** the change exists
- [ ] body mentions constraints, follow-up work, or migration notes when relevant
- [ ] breaking changes are called out explicitly
- [ ] commit message does not promise more than the diff actually delivers

### 4. Check Scope and Complexity
Look for:
- strict alignment between message and diff
- no unrelated refactors mixed with the stated change
- no unnecessary abstractions, patterns, or file spread
- a diff size proportionate to the stated task

**Scope Alignment Checklist**
- [ ] changes are strictly limited to what the commit message describes
- [ ] no "while I'm here" changes or opportunistic cleanup
- [ ] a bug fix commit fixes the named bug rather than adjacent problems too
- [ ] unrelated improvements are split into separate commits

**Over-Engineering Checklist**
- [ ] solution is as simple as possible for the stated problem
- [ ] no unnecessary abstractions or premature optimization
- [ ] no new patterns or frameworks without clear justification
- [ ] changes stay localized unless there is a defensible reason to spread

**Size vs Scope Checks**
- [ ] large diffs correspond to genuinely large features
- [ ] small bug fixes remain small and targeted
- [ ] if the diff is large but the commit message is simple, treat that as a review risk
- [ ] ask whether the work could have been split into smaller focused commits

**Red Flags**
- commit says "fix typo" but touches many files
- commit says "add validation" but also refactors the module
- new abstractions or helper layers appear for a simple change
- files change that are not implied by the commit description
- refactoring is mixed with behavior changes

**When to Reject**
If the change is over-engineered or out of scope, recommend one or more of:
1. revert to a simpler approach
2. split into smaller focused commits
3. remove unrelated changes before merge

### 5. Check Code Risk
Look for:
- correctness issues, missing edge cases, or unsafe assumptions
- missing or stale tests when behavior changed
- security or secrets handling problems
- debug residue, dead code, or inconsistent conventions

**Correctness Checklist**
- [ ] no syntax errors, typos, or incorrect imports
- [ ] logic is sound and edge cases are handled
- [ ] error handling is explicit enough to debug failures
- [ ] exceptions are not silently swallowed
- [ ] tests were updated if behavior changed

**Security Checklist**
- [ ] no hardcoded secrets or credentials
- [ ] inputs are validated where appropriate
- [ ] sensitive data handling matches repo expectations

**Style and Cleanliness Checklist**
- [ ] naming is clear and consistent
- [ ] project conventions are followed
- [ ] no commented-out code or stray debug statements
- [ ] new dependencies are justified and noted

### 6. Provide Feedback
If issues are found:
- describe each problem clearly
- identify the file and approximate location
- provide a concrete fix or shape of fix
- explain why the fix matters

If no issues are found:
- confirm the commit looks good
- highlight especially strong patterns when useful
- give a clear merge-ready signal

## Examples
### Example Request
> Review the latest commit and tell me whether it is merge-ready or too broad.

### Example Output Shape
- commit under review
- findings with file references
- scope and message assessment
- merge readiness decision

### Usage Examples
```text
/code-review
```
Reviews the most recent commit (`HEAD`).

```text
/code-review <commit-hash>
```
Reviews a specific commit.

```text
/code-review /scope
```
Biases the review toward scope discipline and over-engineering detection.

## Output Format
Structure the review like this:

```text
## Git Commit Review Results

**Commit:** [short hash] - [title]

### Issues Found: [count]

1. **[Severity]** in `path/file.ext` (line ~X)
   - Problem: [description]
   - Fix: [code example or concrete remediation]
   - Why: [explanation]

### Positive Notes
- [strong choices worth keeping]

### Recommendation
[Ready for MR / Needs revision before MR / Split required]
```

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
- Do not rubber-stamp a commit just because tests pass.


Capability resource: `.codex/skills/code-review/resources/capability.json`
