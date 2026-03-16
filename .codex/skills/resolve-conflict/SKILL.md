---
name: "resolve-conflict"
description: "[ScottP] Structured merge conflict resolution with Charlie Munger inversion analysis"
---
# Resolve Conflict — Structured Merge Conflict Resolution

## Purpose
Analyze and resolve git merge conflicts using structured reasoning, Charlie Munger-style inversion, and logical document structure principles.

## Output Directory
All conflict analysis artifacts should be stored in `reports/merge-conflicts/` with descriptive filenames.

---

## Core Principles
- **Inversion first**: Ask "what would make this merge catastrophically wrong?" before solving
- **Keep all valuable content**: Default to additive resolution, not deletion
- **Logical structure**: Order sections by principle → pattern → implementation
- **No contradictions**: Ensure merged content is internally consistent
- **Evidence-based**: Work from actual conflict markers and diffs

---

## Resolution Process

### Phase 1: Inversion Analysis (Charlie Munger Style)

**Invert the problem**: Instead of asking "how do I merge this?", ask "what would make this merge catastrophically wrong?"

#### Ways to Fail:
1. **Lose important content** - Drop valuable sections from either branch
2. **Create duplicates** - End up with redundant guidance that conflicts
3. **Break logical flow** - Insert sections in wrong order, making the doc hard to follow
4. **Introduce inconsistency** - Have content in one place contradict content elsewhere
5. **Merge incompatible concepts** - Force together ideas that shouldn't coexist

#### Therefore, Success Means:
- **Keep ALL valuable content** from both branches
- **Logical ordering** that builds from general principles to specific patterns
- **No contradictions** between sections
- **Clear hierarchy** of concerns
- **Explicit trade-offs** when choices must be made

---

### Phase 2: Conflict Analysis

#### 2.1 Identify the Conflict
- **File(s)**: List all files with conflicts
- **Location**: Where in each file (section, line range)
- **Branch context**: What each branch was trying to accomplish

#### 2.2 Content Analysis

For each conflicting section:

**Our Branch (current) Adds:**
```
[Paste the content from our branch]
```
**Purpose:** [What problem does this solve? What value does it add?]

**Their Branch (incoming) Adds:**
```
[Paste the content from their branch]
```
**Purpose:** [What problem does this solve? What value does it add?]

#### 2.3 Relationship Analysis

Determine the relationship between the conflicting changes:
- **Orthogonal**: Different concerns, can coexist (most common)
- **Overlapping**: Similar concerns, need to merge or choose
- **Contradictory**: Incompatible approaches, must choose one
- **Complementary**: Work together, should both be kept

---

### Phase 3: Resolution Strategy

#### 3.1 Determine Logical Structure

For documentation/specification files, order by:
1. **Meta-principles** - How to make decisions
2. **Core principles** - Fundamental rules
3. **Naming/terminology** - What to call things
4. **Structure/patterns** - How to organize things
5. **Implementation details** - Specific how-to guidance
6. **Boundaries/scope** - What's in/out of scope

For code files, order by:
1. **Imports/dependencies**
2. **Constants/configuration**
3. **Type definitions**
4. **Core logic**
5. **Helper functions**
6. **Exports**

#### 3.2 Check for Contradictions

Review merged content for:
- Terminology conflicts (same thing called different names)
- Pattern conflicts (different approaches to same problem)
- Constraint conflicts (rules that contradict each other)
- Scope conflicts (overlapping or contradictory boundaries)

If contradictions exist:
- **Document the conflict explicitly**
- **Present options to the user**
- **Recommend a choice with clear rationale**
- **Do not silently choose** - get user input

---

### Phase 4: Resolution Plan

Create a step-by-step plan:

1. **Merge command**: `git merge <branch>` or `git rebase <branch>`
2. **Conflict resolution approach**:
   - Keep all sections in logical order: [list order]
   - Remove duplicates: [list what to remove]
   - Resolve contradictions: [list how]
3. **Verification steps**:
   - Check for remaining conflict markers
   - Validate file syntax/structure
   - Run tests if applicable
4. **Commit message**: `[branch]: Resolve merge conflict - [brief description]`
5. **Review before push**: [what to check]

---

### Phase 5: Expected Outcome

Describe the final state:
- **File structure**: What sections will exist and in what order
- **Content coverage**: What concerns are addressed
- **Consistency**: How contradictions were resolved
- **Completeness**: What's included from each branch

---

## Output Format

Structure your analysis as:

```markdown
# Merge Conflict Analysis - [Branch/Feature Name]

## Charlie Munger Inversion: What Would Make This Merge Fail?

### Ways to Fail:
1. [Failure mode 1]
2. [Failure mode 2]
...

### Therefore, Success Means:
- [Success criterion 1]
- [Success criterion 2]
...

---

## The Conflict

**File:** [path]

**Branch [ours] (current):** [What was added/changed]

**Branch [theirs] (incoming):** [What was added/changed]

**Conflict location:** [Where the conflict occurs]

---

## Content Analysis

### Our Branch Adds:
[Content and purpose]

### Their Branch Adds:
[Content and purpose]

---

## Resolution Strategy

### Logical Document Structure:
1. [Section 1] - [Purpose]
2. [Section 2] - [Purpose]
...

**Rationale:**
[Why this order makes sense]

### No Conflicts Between Sections:
[Explain why sections are orthogonal/complementary]

---

## Resolution Plan

1. [Step 1]
2. [Step 2]
...

---

## Expected Outcome

[Description of final merged state]
```

---

## Usage Examples

### Basic Conflict Resolution
```bash
# Create reports directory if needed
mkdir -p reports/merge-conflicts

# Save conflict analysis
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
# Save your analysis to: reports/merge-conflicts/${TIMESTAMP}-${BRANCH_NAME}.md

/resolve-conflict
```
Analyzes current merge conflicts and provides resolution strategy.

### Analyze Specific File
```
/resolve-conflict path/to/file.md
```
Focuses on conflicts in a specific file.

### Preview Merge
```
/resolve-conflict --preview <branch>
```
Analyzes potential conflicts before merging.

---

## Hard Constraints

1. **Always start with inversion** - Identify failure modes before solving
2. **Never silently drop content** - If content must be removed, explain why
3. **Document contradictions** - Don't hide incompatibilities
4. **Get user input for choices** - Don't make taste/judgment calls alone
5. **Verify logical structure** - Ensure merged content flows logically
6. **Check for consistency** - Scan for contradictions in merged result

---

## Integration with Git Workflow

### Pre-merge Analysis
Before merging a branch, run:
```bash
git merge --no-commit --no-ff <branch>
# If conflicts, run: /resolve-conflict
```

### During Rebase
When rebase conflicts occur:
```bash
# Conflicts appear
/resolve-conflict
# Follow resolution plan
git add <resolved-files>
git rebase --continue
```

### Post-resolution Verification
After resolving conflicts:
```bash
# Check for remaining markers
git diff --check
# Validate syntax
# Run tests
# Review changes
git diff HEAD
```

---

## Common Conflict Patterns

### Documentation Conflicts
- **Pattern**: Both branches add new sections after the same location
- **Resolution**: Order sections logically (principle → pattern → implementation)
- **Check**: Ensure no terminology or pattern contradictions

### Code Conflicts
- **Pattern**: Both branches modify the same function/class
- **Resolution**: Merge logic if orthogonal, choose one if contradictory
- **Check**: Run tests, verify behavior

### Configuration Conflicts
- **Pattern**: Both branches change the same config values
- **Resolution**: Understand intent of each change, choose or merge
- **Check**: Validate config syntax, test with new values

### Dependency Conflicts
- **Pattern**: Both branches add/update dependencies
- **Resolution**: Keep both if compatible, resolve version conflicts
- **Check**: Run dependency resolution, test builds

---

## Example: Documentation Conflict

**Scenario**: Both branches add content after "Error Handling" section.

**Our branch adds**: "Terminology Guidelines"
**Their branch adds**: "API Response Patterns" + "Security Principles"

**Resolution**:
1. Keep all three sections
2. Order: Terminology → Response Patterns → Security
3. Rationale: Name things before structuring them, security is cross-cutting
4. Verify: No terminology conflicts between sections

**Result**: Clean merge with logical flow, all content preserved.


Capability resource: `.codex/skills/resolve-conflict/resources/capability.json`
