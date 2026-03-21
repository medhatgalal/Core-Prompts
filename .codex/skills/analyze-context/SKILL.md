---
name: "analyze-context"
description: "Iterative Analysis Workflow for multi-file, multi-source repo analysis with canonical memory files, anti-sprawl controls, and compaction-safe progress tracking."
---
# Analyze Context — Iterative Multi-File Analysis Workflow

## Purpose
Use this capability for multi-file or multi-source analysis that must preserve context, findings, and progress across long sessions, memory compaction, or multi-turn review work.

## Primary Objective
Turn broad analysis into one deterministic working set: one canonical context file, one canonical todo file, one canonical insights file, and a repeatable workflow that survives session loss without scattering notes across the repo.

## Workflow
1. Check the current branch before starting any long-running analysis work.
2. Establish the analysis goal, success criteria, scope, and exclusion rules.
3. Create or reuse one canonical memory set under `.analyze-context-memory/`.
4. Process one item at a time and update the canonical files before moving on.
5. Restore state from those files first after compaction or interruption.
6. End with a complete insights summary and no dangling analysis state.

## Tool Boundaries
- allowed: create and maintain canonical memory files, inspect source material, summarize findings, and keep durable progress state
- forbidden: pretending analysis is implementation, silently changing unrelated repo state, or replacing canonical source documents with temporary notes
- escalation: if the work becomes design, review, testing, or decision synthesis, route to the companion capability instead of overextending this one

## Rules
- One initiative gets one active memory set.
- Do not fork versioned analysis memory files for the same initiative.
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
| The user wants a durable transcript or full thread export | `threader` | target thread scope, fidelity expectations, file or inline export preference |
| The analysis identifies a testing or verification gap | `testing` | changed area, risk hotspots, existing test stack, missing scenarios |
| The analysis identifies implementation quality or review risk | `code-review` | diff or commit scope, review goals, suspected regressions or over-engineering risks |

## Constraints
- Do not start long-running analysis directly on `main` or `master`.
- Do not create multiple competing memory sets for the same initiative.
- Do not let insights remain only in the todo file.
- Do not archive mid-initiative.

## Safety Check
Before proceeding, you MUST check the current branch.

```bash
git status --short --branch
```

If the current branch is `main` or `master`, stop and request a dedicated branch before starting long-running analysis work.

## Canonical Memory Files
Create these files in `.analyze-context-memory/` at the project root.

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
1. read the context file to restore the goal
2. read the todo file to restore progress position
3. read the insights file to restore accumulated knowledge
4. continue from the recorded next item instead of restarting from memory

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
