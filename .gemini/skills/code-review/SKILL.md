---
name: "code-review"
description: "[ScottP] Git commit review with scope control and over-engineering detection"
---
# Code Review — Git Commit Quality Gate

## Purpose
Review git commits before creating merge requests, focusing on commit message quality, scope alignment, and detecting over-engineering in AI-assisted coding environments.

## Output Directory
All review artifacts should be stored in `reports/code-reviews/` with timestamped filenames.

---

## Core Principles
- **Scope discipline**: Changes must match what the commit message describes
- **Simplicity first**: Flag over-engineered solutions
- **Evidence-based**: Review actual diff output, not assumptions
- **AI-aware**: Recognize that AI-assisted coding can easily introduce scope creep

---

## Review Process

### 1. Capture the Commit
Run this command to capture the commit for review:
```bash
# Create reports directory if needed
mkdir -p reports/code-reviews

# Capture commit for review
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
git show HEAD --no-color 2>&1 > reports/code-reviews/${TIMESTAMP}-${COMMIT_HASH}.md
```

**CRITICAL**: After writing the file, you MUST read it to review both the commit message and all changes.

### 2. Commit Message Quality

Check:
- [ ] Clear, concise title describing **what** the commit does (not how)
- [ ] Description explains **why** the change was made and provides context
- [ ] References related issues or tickets if applicable
- [ ] Breaking changes or migration steps are documented

### 3. Scope & Complexity Review (AI-Assisted Coding Focus)

**CRITICAL**: AI-assisted coding can easily get out of hand. Changes must be strictly scoped.

**Scope Alignment:**
- [ ] Changes are **strictly limited** to what the commit message describes
- [ ] No "while I'm here" changes or scope creep
- [ ] If the commit says "fix bug X", only bug X should be fixed
- [ ] Unrelated improvements or refactors should be separate commits

**Over-Engineering Check:**
- [ ] Solution is as **simple as possible** for the stated problem
- [ ] No unnecessary abstractions or premature optimization
- [ ] No new patterns/frameworks introduced without clear justification
- [ ] Changes are localized - not spreading across multiple modules unnecessarily

**Size vs. Scope:**
- [ ] Large diffs should only exist for genuinely large features
- [ ] Small bug fixes should have small diffs (typically <50 lines)
- [ ] If diff is large but commit message is simple, **FLAG IT** - likely over-engineered
- [ ] Question: "Could this have been a smaller, more targeted change?"

**Red Flags to Call Out:**
- Commit says "fix typo" but touches 10 files
- Commit says "add validation" but refactors entire module
- New abstractions/classes added for simple changes
- Changes to files/modules not mentioned in commit description
- Refactoring mixed with feature work or bug fixes

**When to Reject:**
If the change is over-engineered or out of scope, recommend:
1. Revert to a simpler approach
2. Split into multiple focused commits
3. Remove unrelated changes

### 4. Code Quality

**Correctness:**
- [ ] No syntax errors, typos, or incorrect imports
- [ ] Logic is sound and edge cases are handled
- [ ] Appropriate error handling with clear messages
- [ ] No swallowed exceptions without logging
- [ ] Tests updated if behavior changed

**Security:**
- [ ] No hardcoded secrets or credentials
- [ ] Input validation where appropriate
- [ ] Sensitive data is properly handled

**Style & Cleanliness:**
- [ ] Follows project conventions
- [ ] Clear, consistent naming
- [ ] No commented-out code or debug statements
- [ ] Breaking changes flagged in commit message
- [ ] New dependencies noted if added

### 5. Provide Feedback

**If issues found:**
- Clearly describe each problem
- Specify file and approximate line location
- Provide a concrete fix with code example
- Explain why the fix matters

**If no issues found:**
- Confirm the commit looks good
- Highlight any particularly good patterns
- Give the green light for merge request

---

## Output Format

Structure your review as:

```
## Git Commit Review Results

**Commit:** [short hash] - [title]

### Issues Found: [count]

1. **[Severity]** in `file.py` (line ~X)
   - Problem: [description]
   - Fix: [code example]
   - Why: [explanation]

### Positive Notes:
- [Any good patterns or improvements]

### Recommendation:
[Ready for MR / Needs revision before MR]
```

If no issues: Keep it brief and confirm it's good to go.

---

## Usage Examples

### Basic Review
```
/code-review
```
Reviews the most recent commit (HEAD).

### Review Specific Commit
```
/code-review <commit-hash>
```
Reviews the specified commit.

### Review with Focus
```
/code-review /scope
```
Focus specifically on scope alignment and over-engineering detection.

---

## Hard Constraints

1. **Never skip reading the actual diff** - Always capture and read the full `git show` output
2. **Evidence over assumptions** - Base review on actual changes, not what you think should be there
3. **Scope discipline is non-negotiable** - Flag any scope creep immediately
4. **Simplicity bias** - When in doubt, recommend the simpler approach
5. **No rubber-stamping** - If you can't verify something, say so explicitly
