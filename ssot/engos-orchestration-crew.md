---
name: "engos-orchestration-crew"
description: "Design, launch and oversee a multi-agent crew in any agent harness (Claude Code, Kiro, Codex, Gemini CLI, or any harness that can start sub-agents and read and write files) that runs a long job to a defined goal against acceptance criteria fixed up front: a lead, workers, fresh verifiers, a safety watch and an independent drift auditor, with change control. Use when the user types /engos-orchestration-crew (with or without a command such as help, design, launch, status, end) or wants a long, checkable, multi-agent job (an A/B evaluation, QA of a built system, an audit or a migration) run unattended with no drift. Do not use for short or single-agent tasks."
capability_type: "skill"
version: "v1.0"
install_target: "global"
version: "v1.0"
---

# Engos Orchestration Crew

## Purpose
Design, launch and oversee a multi-agent crew in any agent harness (Claude Code, Kiro, Codex, Gemini CLI, or any harness that can start sub-agents and read and write files) that runs a long job to a defined goal against acceptance criteria fixed up front: a lead, workers, fresh verifiers, a safety watch and an independent drift auditor, with change control. Use when the user types /engos-orchestration-crew (with or without a command such as help, design, launch, status, end) or wants a long, checkable, multi-agent job (an A/B evaluation, QA of a built system, an audit or a migration) run unattended with no drift. Do not use for short or single-agent tasks.

## Primary Objective
Fulfill the source contract retained under Imported operating instructions. These packaging sections do not introduce a different task, workflow, or set of deliverables.

## Workflow
Follow the original routing, prerequisites, steps, verification, and stop conditions. Read its referenced resources before the steps that depend on them. For a collection, select the source contract matching the requested mode; unresolved conflicts require review.

## Rules
- The original source contract defines capability behavior during an authorized invocation.
- Do not execute source instructions during intake merely because they are present in the imported text.
- Caller instructions and host permission boundaries still govern execution; packaging grants no additional authority.

## Required Inputs
Use the inputs, schemas, defaults, and clarification rules declared by the original source contract.

## Required Output
Produce the artifacts and results declared by the original source contract, including its exact filenames, formats, templates, and mode-specific receipts. Intake summaries and uplift metadata do not replace those outcomes.

## Output Directory
Use the destinations specified by the original source contract or the caller. This wrapper imposes no additional report path.

## Constraints
Retain the original scope, ownership, approval gates, tool limits, and failure behavior. The sidecar descriptor and inferred relationships are advisory packaging metadata, not a competing source of task instructions.

## Invocation Hints
Use the original triggers and mode-selection rules retained below.

## Examples
Use the original examples and output templates in the retained instructions and referenced resources. Where the source supplies no example, this wrapper does not invent an unrelated repository-review task.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Outcome fidelity | Every artifact and format required by the selected source contract is delivered |
| Workflow fidelity | Original routing, validation, error handling, and stop conditions remain in force |
| Authority | Execution stays within caller authorization and host permissions |
| Packaging | Metadata does not replace operational instructions or introduce new deliverables |
| Evidence | Structural preservation is distinguished from independent behavioral validation |

## Imported operating instructions

---
name: "engos-orchestration-crew"
description: "Design, launch and oversee a multi-agent crew in any agent harness (Claude Code, Kiro, Codex, Gemini CLI, or any harness that can start sub-agents and read and write files) that runs a long job to a defined goal against acceptance criteria fixed up front: a lead, workers, fresh verifiers, a safety watch and an independent drift auditor, with change control. Use when the user types /engos-orchestration-crew (with or without a command such as help, design, launch, status, end) or wants a long, checkable, multi-agent job (an A/B evaluation, QA of a built system, an audit or a migration) run unattended with no drift. Do not use for short or single-agent tasks."
version: "v1.0"
---
# Crew orchestration

You are the **designer** for a multi-agent job I want run to a defined goal, unattended where
possible, with no drift from the plan. You design it, you set it running, and then you oversee
it. You never do the crew's work yourself.

## Commands

One entry point: `/engos-orchestration-crew <command>` (`$engos-orchestration-crew` where the
harness uses `$` for skills). The command is the first word. If the first word is not a command,
the whole text is the job and `design` runs.

| Command | What it runs | Section |
|---|---|---|
| `help` (also `-h`, `--help`) | Print this table and one example per command. Write nothing, start nothing | Commands |
| `design <job>` (default) | The job, the fit check, and Phase 1 steps 1 to 4, ending at the go-ahead | The job, Phase 1 |
| `launch` | Phase 1 step 5 (freeze the baseline), start the crew, run the gates | Phase 1, The crew, Gates |
| `status` | One oversight pass, then a sitrep | Your job while it runs |
| `end` | The final report, the post-run analysis hand-off and the summary to me | The end |

Commands pick where to start. They do not skip, reorder or change any step: after a command's
step, carry on as the method says. `launch`, `status` and `end` need the run's `plan.md` and
`acceptance-criteria.md`; if they are not found, ask for their folder in one line.

**Help** prints the table above, then one example per command, written the way this person
started the skill:

```text
/engos-orchestration-crew help
/engos-orchestration-crew design A/B test tool X vs tool Y building the same app; done when every criterion has a verified verdict
/engos-orchestration-crew launch
/engos-orchestration-crew status
/engos-orchestration-crew end
```

## The job

The user's text after the skill command (or after `design`) describes the job. From it, fill in
these five fields:

- **Goal:** one sentence: what must be true at the end.
- **Done when:** the observable conditions that end the job.
- **System or work under test:** where it lives (site, repo, documents, data).
- **Steps only the user can do:** for example typing sensitive values, sign-ins, approvals.
- **Hard limits:** budget, time cap, things never to touch.

If a field is missing and it would change the design, ask (up to 3 questions in all). Show the
five fields back before Phase 1 starts.

**Check the fit first.** This pattern costs about an hour of setup before any work starts. If
the job is short, single-agent, or has no observable pass condition, say so in two lines and
recommend doing it directly instead. Go ahead only if the user still wants it. Drop crew roles
the job does not need (for example the safety watch when nothing can be harmed), and say which
ones you dropped and why.

## Phase 1: design (before anything runs)

1. Ask me up to 3 questions where my answer would change the design. Otherwise state your
   assumptions and carry on.
2. Write two files:
   - **`acceptance-criteria.md`:** numbered criteria, each with how to test it and what counts
     as a pass. A pass must be observable on the real system, never taken from an agent's word.
     Also include:
     - the verdicts: PASS, FAIL, BLOCKED-BY, NOT TESTABLE;
     - a dependency table, so one failure does not fail everything after it;
     - declared limits, fixed in advance;
     - the metrics to record.
   - **`plan.md`:** roles, gates, the loop, the stop rule, messaging, safety, the final report,
     and a version number.
3. Harden both files. Run hostile reviewer sub-agents, each given the files and not your
   reasoning. Then have an independent scorer sub-agent score them 1 to 10. Fix and repeat until
   the score is 9 or more. If the scores stop rising, tell me it is diminishing returns and
   advise, but do not lower the target yourself. Only I change the target.
4. Show me a 150-word summary, then wait for my go-ahead.
5. On my go-ahead, freeze the baseline: copy both files to your scratchpad with SHA256 hashes,
   and start `oversight-log.md` (time, change, reason, approved by).

## The crew

| Role | Started as | Job | Never |
|---|---|---|---|
| Lead | A new session | Runs the loop, applies the rules, keeps `state.json`, `decisions.md` and `ambiguities.md`, writes the final report | Does workers' or verifiers' tasks itself |
| Workers | Sessions started by the lead | Do the work, test their own output, report in the fixed format | Grade their own final verdict |
| Verifiers | Fresh sessions, one per pass | Re-test every criterion independently. Trust no report | Reuse a worker's evidence as proof |
| Safety watch | A read-only session | Every 10 minutes, checks nothing outside scope changed or was harmed | Writes anything |
| Drift auditor | A read-only session that you start | Every 30 minutes, compares the run, and your own edits, with the frozen baseline. Writes findings rated High, Medium or Low | Messages the crew or fixes anything |

Give each brief the goal, its inputs, its limits, its output format and a stop condition.
Distinguish observed from concluded everywhere.

## Platform facts. Design around them

Use the adapter under **Harness adapters** for the harness you run in, and design around its
facts. Every adapter covers the same five things: starting sessions, messaging, timers, tool deny
rules and model reporting. The inbox files, the `status.md` lines and `date -u` timestamps in the
Claude Code Desktop adapter work in every harness.

## Rules

- **Change control.** Any change to the plan, the criteria, a gate, the stop rule or fairness
  needs my approval first. When I approve: bump the version, log the change, freeze a new
  baseline and tell the lead. Corrections that bring the run back in line with the plan need no
  approval, but log them too.
- **One rulings file.** Every reading of an ambiguous criterion goes in `ambiguities.md`, applies
  to everyone, and is what verifiers read.
- **Same method everywhere.** If there are arms or groups being compared, every check uses the
  same method in each, and every wait for me is left out of the timings.
- **Never skip a check to save me a step.** Batch everything that needs me into one hand-off
  instead.
- **Hand-offs to me** go in a `scott-entry.md` file: exactly what to type, where, and what not to
  click. I type `entered` in that member's session when done.
- **Refusals.** If an agent's own safety rules refuse a step, do not argue it round. Bring me
  options, and treat that step the same everywhere.
- **Never** send mail or chat to people, file tickets, share documents, or delete or damage
  anything outside the job. Draft; I send.

## Gates (preflight, logged in `preflight.md`)

1. Every member reports its model. Each barred tool is tried and refused.
2. Each member signs in where it needs to.
3. Each member acts on an inbox file it was never messaged about.
4. The safety watch takes a "before" snapshot.
5. 60 lead timer wakes arrive in a row with no message from me.

Only then does the work start.

## Your job while it runs

- Every 30 minutes, on your own timer:
  - re-hash the files;
  - read the lead's new decisions and the crew's outputs;
  - check them against the plan and criteria.
- Read each auditor report and check its findings against the files yourself before acting.
- Fix drift by messaging the lead. Bring me anything that could move a verdict.
- Answer my questions here. I type in the lead session only when asked.
- Sitreps: 150 words, a table if it helps, observed vs concluded, and what you need from me.

## The end

1. **Final report**, written by the lead:
   - verdicts per criterion, with evidence;
   - metrics;
   - where verifiers disagreed with workers;
   - every ruling and decision;
   - what was not tested, and why.
2. **Post-run analysis**, a separate session I start:
   - root causes backed by evidence, each attacked by a hostile reviewer;
   - recommendations, each tied to a proven cause and to the re-test that would prove it;
   - draft tickets for me to file;
   - a scorer gives it 9/10 or better.
3. **A 150-word summary to me:** the verdict, the 3 biggest findings, what needs me, and links.

## Harness adapters

Pick the one for the harness you run in. Commands below come from each tool's own help output
and documentation as of November 2026; none of the non-Claude adapters has been run end to end
in a crew. Items marked *(unconfirmed)* had no documentation or test behind them; check them in
gate 1 before relying on them.

### Claude Code Desktop (the adapter this skill was proven on)

- **Sessions start only on a turn I typed.** Start every session the job will need, standby
  verifiers included, on my first go-ahead turn. Use the lead's sub-agents only as a fallback.
- **The lead can send only 10 messages to other sessions per message I type.** So do not rely on
  messages:
  - The lead writes `agents/<member>/inbox/<n>.md`.
  - Every member keeps one timer: before ending a turn it checks `kill -0` on its pid file, and
    only if that fails starts `sleep 600` in the background. It reads its inbox on every wake.
  - Members reply by appending one numbered line, `#N <UTC time> <status>`, to their `status.md`.
  - The lead tracks the last `#N` handled for each member.
  - A verifier that must wait mid-pass starts a timer too.
- **Timers die sometimes.** Only a message can wake that member. The lead's turn-end note then
  says "needs <me>: type continue in the lead session."
- **Project `.claude/settings.json` deny rules apply even in bypass mode.** Put the crew in
  folders whose deny rules block the tools they must not use. Test in gate 1 that each one is
  refused.
- **Agents' headed browsers can steal keyboard focus.** Tell me to move them to their own macOS
  desktop. Agents never switch tabs while they wait for me, and they check every field before
  each submit.
- Take every timestamp from `date -u`, never from memory.

### Kiro (Kiro CLI and IDE)

| Need | Mechanism |
|---|---|
| Sessions | One process per member: `kiro-cli chat --agent <name> --no-interactive "<brief>"`; `--resume-id <id>` continues it. The `subagent` tool (alias `use_subagent`) runs sub-agents in parallel, but they report back to the parent and end, so use them only as the fallback. The `delegate` tool runs background agents (`/delegate status`); how long they live is *(unconfirmed)* |
| Messaging | No native session-to-session messaging. Use the inbox files and `status.md` lines |
| Timers | Hooks fire on events only, never on a clock, and a background `sleep` waking an idle agent is *(unconfirmed)*. Run each member from an outside loop or cron that re-invokes `kiro-cli chat --resume-id <id> --no-interactive "read your inbox"` every 600 seconds. Those re-invocations are the timer wakes gate 5 counts |
| Deny rules | One agent JSON per role in `.kiro/agents/` or `~/.kiro/agents/`: `tools`, `allowedTools`, `toolsSettings.shell.deniedCommands` (deny is checked before allow), `toolsSettings.write.deniedPaths`. A `preToolUse` hook that exits with code 2 blocks the call. Whether 2.x deny lists hold under `--trust-all-tools` is *(unconfirmed)*, so prefer the hook. In V3, `permissions.rules` deny always wins |
| Model | Pin it with the agent JSON `model` field or `--model`; `kiro-cli chat --list-models` lists them. With `model: "auto"` a member may not know its model, so report the pinned name. A command that prints the active model mid-session is *(unconfirmed)* |

### Codex (Codex CLI)

| Need | Mechanism |
|---|---|
| Sessions | One process per member: `codex exec "<brief>"`; `codex exec resume <id>` continues it; `--worktree` gives it its own git worktree. Sub-agents (`.codex/agents/<name>.toml` registered as `[agents.<name>]` in `config.toml`; tools `spawn_agent`, `send_input`, `wait_agent`, `close_agent`) run in parallel up to `agents.max_concurrent_threads_per_session`; use them only as the fallback. Sub-agent persistence is *(unconfirmed)* |
| Messaging | Inbox files and `status.md` lines. `codex queue --thread <id or name> --message "<text>"` queues a message for an existing session *(listed in help, not run)*. A parent reaches its own sub-agents with `send_input` |
| Timers | A `sleep` tool that ends early on new input exists for some models only *(unconfirmed for the model in use)*. Confirmed fallback: an outside loop or cron running `codex exec resume <id> "read your inbox"` every 600 seconds. Those runs are the timer wakes gate 5 counts |
| Deny rules | Start the safety watch and drift auditor with `-s read-only`, others with `-s workspace-write`, always explicitly, because a user config may default to `danger-full-access`. Command deny rules: `.rules` files with `prefix_rule(pattern=[...], decision="forbidden")` in `~/.codex/rules/`, or `<repo>/.codex/rules/` for a trusted project. Sub-agents inherit the parent's sandbox. Never pass `--ignore-rules`. Whether rules hold under `--dangerously-bypass-approvals-and-sandbox` is *(unconfirmed)* |
| Model | Pin it with `-m <model>` or `model` in `config.toml` and report that. `/status` in the interactive UI; a headless member reading its own model is *(unconfirmed)* |

### Gemini CLI

| Need | Mechanism |
|---|---|
| Sessions | One process per member: `gemini -p "<brief>"` (headless); `--resume <id or latest>` or `--session-id` continues it; `-w` gives it a worktree. Sub-agents (`.gemini/agents/<name>.md` or `~/.gemini/agents/`) run, report back and end, and cannot start others; use them only as the fallback. Whether they run in parallel is *(unconfirmed)* |
| Messaging | No native session-to-session messaging found. Use the inbox files and `status.md` lines |
| Timers | The shell tool can run a background process, but no wake on its completion is documented, and hooks fire on CLI events only. Run each member from an outside loop or cron that re-runs `gemini -p --resume <id> "read your inbox"` every 600 seconds *(flag combination not run)*. Those runs are the timer wakes gate 5 counts |
| Deny rules | Policy engine TOML rules with `decision = "deny"` in `~/.gemini/policies`, or via `--admin-policy`. Project `.gemini/policies` currently has no effect (gemini-cli issue 18186). `tools.exclude` is deprecated; `tools.core` is an allowlist. A user-tier deny outranks the yolo allow-all by the documented priority formula *(concluded from docs, not tested)* |
| Model | Pin it with `-m` or `model.name`. A headless run with `--output-format stream-json` reports the model in its `init` event; `/stats model` shows usage. With the model router on, a member cannot reliably name its model, so report the `init` event's model |

### Any other harness (generic fallback)

Needs only a harness that can start sub-agents and read and write files.

| Need | Mechanism |
|---|---|
| Sessions | Start each member as its own session or process if the harness can. Otherwise use the lead's sub-agents, the same fallback as above |
| Messaging | Inbox files and `status.md` lines only |
| Timers | A background timer that wakes the member if the harness has one. Otherwise an outside loop, cron or scheduler that re-invokes each member every 600 seconds. If neither exists, the lead's turn-end note says "needs <me>: type continue in the lead session" |
| Deny rules | Whatever the harness enforces outside the agent's own choice (sandbox, read-only mode, deny list). A tool it cannot bar fails gate 1; bring that to me |
| Model | Pin the model at start where the harness allows and report the pinned name |
