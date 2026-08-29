---
name: "analyze-context"
description: "Maintains durable analysis state for long-running multi-file investigations. Use when repo analysis must survive compaction or interruption, not for design, imports, or behavioral comparison."
---
# Analyze Context — Iterative Multi-File Analysis Workflow

## Purpose
Use this capability for multi-file or multi-source analysis that must preserve context, findings, and progress across long sessions, memory compaction, or multi-turn review work.

Do not use this capability when the main job is to make a final decision, harden a prompt or plan, import a capability, design a system, or prove one variant performs better than another.

## Primary Objective
Turn broad analysis into one deterministic working set: one canonical context file, one canonical todo file, one canonical insights file, and a repeatable workflow that survives session loss without scattering notes across the repo.

## Workflow
1. Resolve the active worktree root, the main checkout root, and the current branch before starting any long-running analysis work.
2. Establish the analysis goal, success criteria, scope, and exclusion rules.
3. Look for an existing canonical memory set in the main checkout first for backward compatibility and cross-session continuity, but treat it as read-only.
4. Create or reuse one canonical memory set under `.analyze-context-memory/` in the active non-main worktree.
5. Process one item at a time and update the canonical files before moving on.
6. Restore state from those files first after compaction or interruption.
7. End with a complete insights summary and no dangling analysis state.

## Tool Boundaries
- allowed: create and maintain canonical memory files, inspect source material, summarize findings, and keep durable progress state
- forbidden: pretending analysis is implementation, silently changing unrelated repo state, or replacing canonical source documents with temporary notes
- escalation: if the work becomes design, review, testing, or decision synthesis, route to the companion capability instead of overextending this one

## Rules
- One initiative gets one active memory set.
- Do not fork versioned analysis memory files for the same initiative.
- Never write analysis memory to the main checkout.
- `.analyze-context-memory/` must be gitignored; if it is tracked, untrack it before starting.
- Do not keep important findings only in chat history.
- Update memory files before any likely context loss.
- Merge scattered analysis notes back into the canonical set immediately.
- Archive only when the initiative is complete.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- analyze several files or transcripts over a long session
- keep durable analysis notes that survive context loss
- process a broad repo investigation one item at a time
- recover and continue a previously interrupted analysis
- preserve progress across a long research or audit workflow before a later recommendation step

## Required Inputs
- a task slug or clear initiative name
- the analysis goal and success criteria
- the set of files, transcripts, or items to process
- any extraction criteria, constraints, or stop conditions

## Required Output
Every substantial response must include:
- the canonical memory file set in use
- current progress state
- key findings accumulated so far
- next item or next analysis action

## Companion Capability Matrix
| If the analysis reveals this need | Route to | Required handoff |
| --- | --- | --- |
| The user now needs one final recommendation from several competing findings | `converge` | option set, trade-offs, blocking uncertainties, recommendation criteria |
| The analysis turns into architecture or system design | `architecture` | constraints, candidate patterns, affected components, unresolved decisions |
| The analysis turns into prompt, plan, or workflow hardening | `supercharge` | draft artifact, weak sections, improvement goal, constraints |
| The analysis needs behavioral proof that one variant beats baseline | `auto-research` | baseline artifact, candidate artifact or variants, representative tasks, desired pass/fail bar |
| The user wants a durable transcript or full thread export | `threader` | target thread scope, fidelity expectations, file or inline export preference |
| The analysis identifies a testing or verification gap | `testing` | changed area, risk hotspots, existing test stack, missing scenarios |
| The analysis identifies implementation quality or review risk | `code-review` | diff or commit scope, review goals, suspected regressions or over-engineering risks |

## Constraints
- Reading an existing canonical set from the main checkout is allowed.
- Writing analysis memory requires a non-main linked worktree.
- Do not create multiple competing memory sets for the same initiative.
- Do not let insights remain only in the todo file.
- Do not archive mid-initiative.

## Safety Check
Before proceeding, you MUST resolve the active worktree, main checkout, and current branch.

```bash
ACTIVE_WORKTREE_ROOT="$(git rev-parse --show-toplevel)"
MAIN_CHECKOUT_ROOT="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
CURRENT_BRANCH="$(git branch --show-current)"
git status --short --branch
```

Reading a canonical set from the main checkout is allowed. Before writing, stop and request a dedicated linked worktree if `CURRENT_BRANCH` is `main` or `master`, or if `ACTIVE_WORKTREE_ROOT` equals `MAIN_CHECKOUT_ROOT`. Confirm that `.analyze-context-memory/` is gitignored in the active worktree. If Git already tracks the directory, untrack it with an index-only operation that preserves the local files before starting.

## Canonical Memory Files
Use an explicit read/write split:

- **READ:** On initial discovery, inspect the matching set under `MAIN_CHECKOUT_ROOT/.analyze-context-memory/` first for backward compatibility and cross-session continuity. Never modify that set in place. If an active-worktree set already exists, it remains the current working state; the main-checkout set is read-only background, not a competing write target.
- **WRITE:** Always create and update the set under `ACTIVE_WORKTREE_ROOT/.analyze-context-memory/`, where `ACTIVE_WORKTREE_ROOT` is resolved with `git rev-parse --show-toplevel`. If only a main-checkout set exists, initialize the active-worktree set from it before recording new progress.

Analysis state is then born and dies with the slice it belongs to: concurrent agents cannot overwrite one another's memory, and removing the worktree disposes of the state automatically.

### `<task>-context.md`
Contains:
- goal of the analysis
- success criteria
- scope and exclusions
- definitions or extraction criteria
- constraints and rules

### `<task>-todo.md`
Contains:
- the full item list
- per-item checkbox state
- brief notes per item
- current status and next item

### `<task>-insights.md`
Contains:
- accumulated findings
- patterns across items
- notable evidence, quotes, or examples
- the growing summary and final conclusion

## Recovery Procedure
After interruption or compaction:
1. check the active worktree for the initiative's canonical set first
2. if no active-worktree set exists, fall back to the read-only set in the main checkout and initialize the active-worktree set before recording new progress
3. read the context file to restore the goal
4. read the todo file to restore progress position
5. read the insights file to restore accumulated knowledge
6. continue from the recorded next item instead of restarting from memory

## Examples
### Example Request
> Analyze this repo’s build, validation, and release scripts across several files and keep the findings durable across a long session.

### Example Output Shape
- canonical memory file paths
- current progress and next item
- findings added this pass
- updated risks or hypotheses

### Failure Mode To Avoid
- creating scattered scratch files and then losing the real state when the session compacts

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Canonical memory discipline | One context/todo/insights set exists for the initiative |
| Progress recoverability | Another engineer can resume the analysis from disk alone |
| Anti-sprawl | Findings are consolidated rather than scattered |
| Output discipline | Progress, findings, and next steps are explicit each pass |
| Boundary clarity | The capability stays analysis-focused and does not pretend to own unrelated execution |


Capability resource: `.codex/skills/analyze-context/resources/capability.json`
