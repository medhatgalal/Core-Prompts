---
name: "engos-quality-code-review"
description: "Review a staged change, diff, commit, or branch for correctness, scope, simplicity, lifecycle risk, and merge readiness before commit, push, merge, or release. Use for judgment; do not use to apply reviewer feedback."
display_name: "Commit Review — Git Commit Quality Gate"
kind: "skill"
capability_type: "skill"
---
# Commit Review — Git Commit Quality Gate

## Purpose
Use this capability to review staged changes, working-tree diffs, or git commits before commit, push, merge, or release. It is a review gate: it reads the actual diff, finds correctness and scope risks, checks commit-message quality, flags over-engineering, and gives a clear readiness decision.

Use this before you create a commit, before you push a branch, before an MR/PR is merged, or after a fix commit has been prepared. Do not use this capability to modify files or apply reviewer feedback; use `engos-delivery-address-code-review` when the user wants selected PR/MR review comments implemented.

## Primary Objective
Determine whether the diff under review is ready to move forward, blocked by correctness or scope issues, or should be split into smaller focused changes before review continues.

## Choose the Right Review Capability
Use `engos-quality-code-review` when the job is judgment.

| User Intent | Use | Why |
| --- | --- | --- |
| "Review my staged changes before I commit" | `engos-quality-code-review` | pre-commit quality gate; no mutation |
| "Review the latest commit" | `engos-quality-code-review` | commit scope, message quality, and merge readiness |
| "Tell me if this MR is too broad" | `engos-quality-code-review` with `engos-quality-gitops-review` if branch/CI state matters | commit/diff findings first, branch gate second |
| "Fix the comments reviewers left on my MR" | `engos-delivery-address-code-review` | action workflow that reads comments and edits files |
| "After fixes, check the fix commit" | `engos-quality-code-review` | verifies the response commit stayed scoped |

Default to `engos-quality-code-review` for pre-commit or pre-push checks. Switch to `engos-delivery-address-code-review` only when the user explicitly wants to inspect and implement existing PR/MR review comments.

## Output Directory
When file output is requested, default to:
- `reports/code-reviews/<timestamp>-<commit>.md`

## Committed-range Collection (Explicit Only)
When the user requests an immutable committed-range package, read the collection
request guidance in `resources/references/review-targets.md`, then load the additive
`collect` route in `resources/resource-map.json`: `resources/scripts/review_package.py`
and its `resources/schemas/review-package.schema.json` dependency. Read the selected
collector context for the exact command and trust limits, then invoke the helper
with exact recorded base/head commit IDs, task/owner/generation/repository bindings,
and a new absent output leaf under an existing nonsymlink parent. Optional spec and
plan SHA-256 values are caller assertions. Use Python 3.11+ and supported Git/POSIX
primitives; the standalone helper requires only stdlib and Git.

The helper emits `ReviewPackage.v1` committed-range evidence and a manifest-digest
receipt. Exit 0 means complete collection only; exit 2 means incomplete/freeze
failure; exit 3 means invalid/unsupported/unsafe input. Preserve partial output and
use a new leaf rather than overwriting it. Binary evidence remains unreviewed;
changed gitlinks make collection incomplete without traversing submodules.
Collection captures endpoint net changes plus all range commit objects, excluding
staged/dirty edits, intermediate patches and unchanged consumers. Keep the ordinary
`review` route, default `HEAD`, six narrative sections and `Findings.v1` unchanged.
Independently bound consumer verification and actual review remain separate;
collection success cannot produce a review/security/correctness verdict or merge
permission. Read needed unchanged consumers at the exact target before findings.

## Core Principles
- **Scope discipline**: changes must match what the commit message describes
- **Simplicity first**: flag over-engineered solutions and unnecessary spread
- **Evidence-based**: review the actual diff, not assumptions about intent
- **AI-aware**: assume AI-assisted changes can drift outside the requested scope unless proven otherwise
- **Actionable output**: every finding should give the reviewer a concrete next move

## Workflow
1. Read the complete `review` route in `resources/resource-map.json`: `resources/references/review-targets.md` and its findings schema. Use the existing bundled `resources/scripts/load_module.py --route review` when available, or read both files directly. Missing or unread required resources make the review incomplete.
2. Capture the exact staged diff, working-tree diff, commit, or branch diff under review; bind it and relevant source/consumer reads to the target as specified in that reference.
3. Read the commit message and the actual diff before making any judgment.
4. Check message quality, scope alignment, and implementation complexity.
5. Record findings with stable IDs, severity, precise location, changed-cause evidence, verified consumer evidence for introduced breakage, impact, repair, and disposition.
6. End with ready, blocked, or split required for a complete review; use unverifiable when evidence or review coverage is incomplete. Review judgment grants no repair, publication, merge, or release authority.

## Rules
- Preserve the default target of `HEAD`. An explicit staged request reviews the index; an empty index does not silently change the target.
- Record target kind, resolved base/head where applicable, included change classes, and snapshot digest for mutable or supplied diffs. Recheck bindings before issuing the verdict; drift invalidates affected evidence.
- Read relevant source and actual consumers beyond the diff when the change can break them. Tie each introduced-breakage finding to the changed cause and a verified affected consumer; distinguish unrelated pre-existing defects.
- Missing, malformed, stale, or unread review evidence is incomplete, never a clean result. Collection success, schema validity, or a self-reported read receipt cannot prove actual reading, truthful findings, or permission to merge.

## Tool Boundaries
- allowed: inspect git history, inspect staged, unstaged, branch, or committed diffs, and write review artifacts when asked
- forbidden: applying fixes, modifying files, staging changes, silent approval, hidden execution, or claiming code quality is fine without reading the diff
- escalation: if the change crosses into release risk, test gaps, or architecture risk, recommend `engos-quality-gitops-review`, `engos-quality-testing-review`, or `engos-design-architecture`

## Companion Capability Matrix
Use companion capabilities deliberately instead of flattening every review into one generic answer.

| Situation | Companion Capability | Why |
| --- | --- | --- |
| release readiness, changelog, CI, packaging, or merge gates matter | `engos-quality-gitops-review` | commit quality alone is not enough for release or branch health |
| behavior changed and test confidence is weak | `engos-quality-testing-review` | test coverage and edge-case discovery need a dedicated pass |
| interface, architecture, or migration risk is material | `engos-design-architecture` | structural risk needs architectural judgment, not just commit review |
| resource growth, capacity exhaustion, or missing cleanup is material | `engos-design-architecture` | identify an eviction strategy or explicit lifecycle bounds |
| doc drift or example drift is part of the commit | `engos-quality-docs-review` | keep documentation review explicit and separate |
| reviewer comments need to be implemented | `engos-delivery-address-code-review` | this review gate should not mutate files |

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- review the latest commit
- review my staged changes before I commit
- review this diff before I push
- check whether this diff is too broad
- judge whether AI-generated changes are over-engineered
- tell me if this commit message and change scope are strong enough to merge

## Required Inputs
- commit hash, staged diff, working-tree diff, branch diff, or the default target of `HEAD`
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

Keep these six sections. In `Commit Under Review`, include the bound target and coverage. In `Findings`, use the fields and evidence links in `resources/schemas/findings.schema.json`; an empty findings list supports a clean verdict only after the declared target is fully reviewed. Include `review_status`, `unreviewed`, and the verdict in `Merge Readiness`. Render these fields inline for chat; when a machine-readable review artifact is requested, write a `Findings.v1` JSON record alongside any requested narrative. Do not write files solely because the schema exists.

## Review Process
### 1. Capture the Commit
Default to the most recent commit (`HEAD`), even if the checkout is dirty. Resolve
its full commit ID and the selected parent, or declare a root commit. Inspect the
actual patch and message, then relevant files at that revision. For merge commits,
state the selected parent/comparison; do not silently substitute a combined diff.

Resolve the requested ref once and keep that full ID for all subsequent reads:

```bash
REVIEW_HEAD=$(git rev-parse --verify 'HEAD^{commit}') || exit 1
git show --no-patch --format=fuller "$REVIEW_HEAD"
git rev-list --parents -n 1 "$REVIEW_HEAD"
```

For a non-merge commit, including a root commit, inspect its patch:

```bash
git show --no-ext-diff --no-textconv --format=fuller --no-color "$REVIEW_HEAD"
```

For a merge commit, set `REVIEW_PARENT` to the explicitly selected full parent ID
from the parent list above and record that choice. Inspect that parent's patch:

```bash
git diff --no-ext-diff --no-textconv --no-color "$REVIEW_PARENT" "$REVIEW_HEAD"
```

Recheck the requested ref and snapshot bindings before the verdict. Disclose any
drift and renew affected review if the requested target changed; never silently
replace `REVIEW_HEAD` or read a newer checkout as the captured commit.

For an explicit pre-commit staged review, inspect the index first:

```bash
git diff --staged --no-ext-diff --no-textconv --no-color
```

If nothing is staged, say that there is no staged target. Inspect the working-tree
diff only after saying that the review is not a commit-ready staged review; label
that fallback with its own working-tree target and digest. Never stage changes.

Use the target rules in `resources/references/review-targets.md` for working-tree,
branch, root/merge commit, and supplied-diff requests. Bind mutable snapshots to
the exact reviewed bytes, not just to the current `HEAD`. A branch review includes
the declared full range, not only its last commit. If file output was requested,
save the captured material under `reports/code-reviews/` and read it before findings;
an unread capture or failed capture is incomplete. Without a file request, inspect
and report inline. Do not turn artifact capture into permission to change source.

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
- resources are created without cleanup, eviction, retention, or capacity bounds
- runtime configuration is frozen during initialization without an explicit immutability contract
- shared mutable state or non-atomic writes appear in concurrent execution paths
- critical warnings have no machine-consumable monitoring or escalation path
- failure modes are silent, unrecoverable, or diagnosable only after redeployment
- parameters or schema changes appear without downstream compatibility analysis

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

### 6. Check Resource & Lifecycle
Look for resource accumulation, initialization-order hazards, concurrency defects, operational blind spots, and downstream contract changes that can make an otherwise correct diff unsafe in production.

**Resource Management Checklist**
- [ ] files, directories, caches, queues, buffers, connections, tasks, subprocesses, and other resources have explicit growth bounds
- [ ] every newly created resource has a clear owner and lifecycle
- [ ] cleanup runs on success, error, timeout, and cancellation paths
- [ ] accumulation is bounded by TTL, eviction, rotation, quotas, size caps, backpressure, or another explicit mechanism
- [ ] temporary artifacts do not persist without a cleanup mechanism
- [ ] disk writes include retention, capacity, and failure handling
- [ ] early returns and partial failures do not leak resources

**Concurrency and Initialization-Time Checklist**
- [ ] environment, configuration, feature flags, clocks, clients, and mutable dependencies are not frozen during initialization when runtime evaluation is required
- [ ] initialization order cannot leave state stale unless startup-time immutability is an explicit contract
- [ ] shared mutable dictionaries, caches, registries, files, and singleton state have documented ownership and synchronization
- [ ] async and multi-worker paths avoid lost updates, duplicate work, partial writes, and read-modify-write races
- [ ] file replacement and state publication are atomic where inconsistent reads are possible
- [ ] concurrent operations handle cleanup and cancellation safely

**Operational Readiness Checklist**
- [ ] warnings and errors are actionable rather than repetitive noise
- [ ] critical failures produce machine-consumable metrics, traces, events, health signals, or alerts
- [ ] operational signals include stable context for diagnosis and ownership
- [ ] repeated warnings are aggregated or rate-limited when necessary
- [ ] operators can inspect or safely change relevant runtime state without redeployment when the system requires it
- [ ] timeouts, retries, fallbacks, circuit breaking, and partial failures degrade gracefully
- [ ] failures remain observable instead of silently switching behavior

**API Contract Checklist**
- [ ] changes to parameters, return values, defaults, ordering, serialization, and error behavior preserve existing callers
- [ ] defaults retain established behavior rather than merely preventing a syntax error
- [ ] generated schemas, clients, descriptors, documentation, and reflection-based interfaces are reviewed for contract changes
- [ ] optional parameters do not become visible to downstream consumers without compatibility analysis
- [ ] tool-calling and schema-driven consumers can interpret the new contract safely
- [ ] versioning, migration, deprecation, and compatibility tests are added when required

### 7. Provide Feedback
If issues are found:
- describe each problem clearly
- identify the exact target-relative file, line, and side; for a deleted cause use the base side, and for a commit-message issue label the message location
- provide a concrete fix or shape of fix
- explain why the fix matters
- retain a stable finding ID and disposition on re-review; mark resolved only after verifying the repair against the new bound target

If no issues are found and the declared target is fully reviewed:
- report an empty findings list and the reviewed coverage
- highlight especially strong patterns when useful
- give a clear advisory readiness signal

If coverage, target binding, source reads, or requested output is missing or malformed, retain any confirmed findings, list what remains unreviewed, and report incomplete/unverifiable. Never translate a failed or empty review return into ready.

## Examples
### Example Request
> Review the latest commit and tell me whether it is merge-ready or too broad.

### Example Pre-Commit Request
> Use `engos-quality-code-review` to review my staged changes before I commit.

### Example Output Shape
- commit under review
- findings with file references
- scope and message assessment
- merge readiness decision

### Usage Examples
```text
/engos-quality-code-review
```
Reviews the most recent commit (`HEAD`).

```text
/engos-quality-code-review staged
```
Reviews staged changes before commit.

```text
/engos-quality-code-review <commit-hash>
```
Reviews a specific commit.

```text
/engos-quality-code-review /scope
```
Biases the review toward scope discipline and over-engineering detection.

## Output Format
Use the six required sections with a brief overall assessment, findings ordered by
impact, scope and message judgments, concrete repairs, and a final advisory verdict.
A finding uses this shape; the complete machine contract and applicability rules
are in `resources/schemas/findings.schema.json` and the review-target reference:

```text
Finding F-001 | high | introduced_breakage | open
Location: src/api.py:42 (head)
Changed cause: removed the legacy keyword [E-diff]
Affected consumer: jobs/nightly.py:18 still supplies that keyword [E-caller]
Impact: the nightly job fails before processing records
Repair: retain compatibility or update and verify the affected consumer
Disposition reason: verified caller remains incompatible at the reviewed revision
```

`Recommended Fixes` may describe a patch without applying it. Include useful
positive notes without weakening an open blocker. `Merge Readiness` states
`review_status`, unreviewed items, and `ready`, `blocked`, `split_required`, or
`unverifiable`; hosted CI and actual merge authorization remain separate gates.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Commit message quality | The message explains what changed and why clearly enough to review |
| Scope discipline | The diff stays tightly aligned to the stated goal |
| Simplicity | The implementation avoids unnecessary abstraction or spread |
| Evidence quality | Findings bind to the actual target and specific changed causes; introduced breakage includes a verified affected consumer |
| Merge guidance | A complete review ends with ready / blocked / split; missing evidence stays incomplete and unverifiable |
| Resource & lifecycle | No unbounded growth, no incorrectly frozen initialization state, and failure modes are observable and recoverable |

## Constraints
- Never skip reading the actual diff.
- Base findings on evidence, not assumptions.
- Flag scope creep immediately.
- Prefer the simpler valid implementation when alternatives exist.
- If something cannot be verified, say so explicitly.
- Do not rubber-stamp a commit just because tests pass.
