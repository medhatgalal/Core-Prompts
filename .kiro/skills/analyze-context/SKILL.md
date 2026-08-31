---
name: "analyze-context"
description: "Maintains repository-scoped durable state for long-running multi-file investigations. Use when evidence and progress must survive compaction, new sessions, branch changes, or worktree removal."
---
# Analyze Context — Durable Multi-File Investigation

## Purpose
Use this capability when a multi-file or multi-source investigation must preserve its goal, evidence, findings, and progress across long sessions, compaction, session replacement, branch changes, or worktree removal.

Large context windows and conversation compaction reduce recovery frequency. They do not replace durable state on disk.

Do not use this capability when the main job is to make a final decision, harden a prompt or plan, import a capability, design a system, or prove one variant performs better than another.

## Primary Objective
Maintain one canonical context/todo/insights set per task under `~/.analyze-context/`. Keep it until the work is complete without turning temporary analysis state into branch content or worktree residue.

## Workflow
1. Establish a stable task ID, goal, success criteria, scope, and exclusions.
2. Resolve the task directory and recover its three files, or migrate the matching legacy set before writing.
3. Record the current branch and worktree as metadata; process one item at a time.
4. Update the three files after meaningful progress and before likely context loss or worktree cleanup.
5. Mark the task complete only after every TODO is checked and the insights file contains the final summary.

## Storage Contract
Store each task outside the repository in one human-readable project/task directory:

```bash
ACTIVE_WORKTREE_ROOT="$(git rev-parse --show-toplevel)"
REPO_COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"
PROJECT_ID="$(basename "$ACTIVE_WORKTREE_ROOT")"
STATE_HOME="${ANALYZE_CONTEXT_STATE_HOME:-$HOME/.analyze-context}"
TASK_ID="<stable-task-id>"
TASK_DIR="$STATE_HOME/$PROJECT_ID/$TASK_ID"
CURRENT_BRANCH="$(git branch --show-current)"
```

- `ANALYZE_CONTEXT_STATE_HOME` may override the default, but it must remain outside every worktree. If policy blocks the location, request permission or another external path; never fall back silently.
- If two repositories have the same `PROJECT_ID`, append a short hash of `REPO_COMMON_DIR` to distinguish them.
- Branch and worktree names belong in the context file as metadata. They do not determine the task directory.
- The store is machine-local. Use a reviewed export or `threader` for cross-machine handoff; never commit scratch state automatically.

## Tool Boundaries
- allowed: create and maintain the external canonical state set, inspect source material, summarize findings, migrate legacy state, and keep durable progress state
- forbidden: pretending analysis is implementation, silently changing unrelated repo state, treating provider-native memory as canonical, or replacing canonical source documents with temporary notes
- escalation: if the work becomes design, review, testing, or decision synthesis, route to the companion capability instead of overextending this one

## Rules
- One task gets one context/todo/insights set.
- Do not fork versioned analysis files for the same task.
- Never write canonical analysis state inside a branch, linked worktree, or main checkout.
- Do not treat session end, compaction, branch removal, or worktree removal as completion or cleanup authority.
- Use a distinct task ID for each concurrent task. Read only the exact task selected for the current work.
- Treat legacy `.analyze-context-memory/` directories as read-only migration sources. They must remain gitignored and untracked until migrated.
- Do not keep important findings only in chat history.
- Update the canonical set before likely context loss and merge scattered notes into it immediately.
- Mark a task complete only when every TODO checkbox is checked and `insights` contains the final summary.
- Completed files may remain on disk. Cleanup is optional, later, and user-approved; hooks must never delete them.
- Do not store secrets, credentials, or unrestricted sensitive source content in analysis state.

## Trigger and Checkpoint Rule
Invoke `analyze-context` when work spans several files or turns, the user asks to preserve or resume analysis, or the task may outlive its current session, branch, or worktree.

When the skill is active:

- recover the exact task set before new analysis
- update context, todo, and insights after meaningful progress
- checkpoint all three before likely compaction, session end, or worktree cleanup
- report the three paths, progress, findings, and next action in substantial responses

Do not invoke this skill for a quick one-file answer, ordinary code review, or short-lived lookup.

## Hook Reminders
Hooks are optional reminders; the trigger and checkpoint rule is the portable contract.

- On `SessionStart`, remind the model to recover the matching task set after the task is known.
- On `PreCompact` or `PreCompress`, remind the model to update context, todo, and insights before compaction. If the host event is advisory, do not treat it as the only checkpoint guarantee.
- If a host lacks either event, continue with the skill rule; do not emulate it with noisy per-tool hooks.
- Hooks may read paths, validate freshness, or add a reminder. They must not invent findings, mark completion, move files, or delete state.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- analyze several files or transcripts over a long session
- keep durable analysis notes that survive context loss
- continue an investigation after its branch or worktree was removed
- process a broad repo investigation one item at a time
- recover and continue a previously interrupted analysis
- preserve progress across a long research or audit workflow before a later recommendation step

## Required Inputs
- a stable task ID or clear task name
- the analysis goal and success criteria
- the set of files, transcripts, or items to process
- any extraction criteria, constraints, or stop conditions

## Required Output
Every substantial response must include:
- the canonical external state paths in use
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
- Canonical state must live outside every Git working tree and survive session, branch, or worktree removal.
- Branch and worktree paths are execution metadata, not task identity.
- Do not create multiple competing sets for one task.
- Do not let insights remain only in the todo file.
- Do not clean up an incomplete task.

## Safety Check
Before the first write:

1. Print the resolved `TASK_DIR`, branch, and worktree.
2. Verify `TASK_DIR` is outside every worktree returned by `git worktree list --porcelain`.
3. Verify no tracked path or symlink redirects it into a worktree.
4. If legacy state is tracked, untrack it with an index-only operation that preserves local files before migration.

## Canonical Memory Files
Store exactly three files under `TASK_DIR`:

- `<task-id>-context.md`: task ID, status (`active`, `paused`, or `complete`), `updated_at`, repository common directory, current worktree and branch, goal, success criteria, scope, constraints, and next action
- `<task-id>-todo.md`: full item list, checkbox state, brief per-item notes, current status, and next item
- `<task-id>-insights.md`: accumulated findings, cross-item patterns, evidence references, and the growing summary or final conclusion

## Recovery Procedure
After interruption or compaction:
1. Resolve `TASK_DIR` and select the exact task ID. Never infer the current task from the newest timestamp alone.
2. If no canonical set exists, inspect legacy `.analyze-context-memory/` locations read-only and copy the matching set into `TASK_DIR` before any update.
3. Read all three files; verify status, freshness, checked TODOs, blockers, and next action.
4. Update worktree and branch metadata if execution moved, then continue from the recorded next action without moving the task directory.

## Completion and Cleanup
A task is complete only when every checkbox in `<task-id>-todo.md` is checked, `<task-id>-insights.md` contains the final summary and evidence, and `<task-id>-context.md` is marked `complete`. Leave completed files in place unless the user later approves cleanup. Cleanup must target the exact completed task directory and should use a recoverable operation such as Trash.

## Examples
### Example Request
> Analyze this repo’s build, validation, and release scripts across several files and keep the findings durable across a long session.

### Example Output Shape
- canonical external state paths
- current progress and next item
- findings added this pass
- updated risks or hypotheses

### Failure Mode To Avoid
- tying authoritative state to a worktree, deleting that worktree, and then reconstructing the initiative from stale chat or unrelated repository memory

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Canonical memory discipline | One context/todo/insights set exists for the task |
| Lifecycle durability | State survives compaction, session replacement, branch changes, and linked-worktree removal |
| Progress recoverability | Another engineer can resume the exact task from disk alone |
| Collision safety | Concurrent tasks use distinct task IDs |
| Stale-state prevention | Only the selected task is loaded; unrelated sets are not presented as current |
| Anti-sprawl | Findings are consolidated rather than scattered |
| Output discipline | Progress, findings, and next steps are explicit each pass |
| Boundary clarity | The capability stays analysis-focused and does not pretend to own unrelated execution |


Capability resource: `.kiro/skills/analyze-context/resources/capability.json`
