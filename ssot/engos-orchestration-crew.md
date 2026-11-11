---
name: "engos-orchestration-crew"
description: "Design, launch and oversee a multi-agent crew in any agent harness (Claude Code, Kiro, Codex, Gemini CLI, or any harness that can start sub-agents and read and write files) that runs a long job to a defined goal against acceptance criteria fixed up front: a lead, workers, fresh verifiers, a safety watch and an independent drift auditor, with change control. Use when the user types /engos-orchestration-crew (with or without a command such as help, design, launch, status, end) or wants a long, checkable, multi-agent job (an A/B evaluation, QA of a built system, an audit or a migration) run unattended with no drift. Do not use for short or single-agent tasks."
capability_type: "skill"
version: "v1.1"
install_target: "global"
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
version: "v1.1"
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

**Check the fit first.** Allow roughly an hour for design and setup. Unattended qualification
adds at least ten hours for 60 consecutive 600-second intervals, before production work. Include
both in the elapsed-time budget. If the job is short, single-agent, or has no observable pass
condition, say so in two lines and recommend doing it directly instead. Go ahead only if the
user still wants it. Omit a safety watch only when the design identifies why nothing in scope or
outside it can be harmed. Record omitted roles and the reason in the plan. Keep fresh verifiers
and an independent drift auditor.

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
     and a version number. Name the operating mode (unattended or attended), the actual harness,
     elapsed deadline, and the owner and evidence for each applicable gate. For attended work,
     specify who resumes which session, the safe pause point, and how the applicable 10/30-minute checks
     will be covered during active work. If attendance or oversight cannot be supplied, hold.
3. Harden both files. Run hostile reviewer sub-agents, each given the files and not your
   reasoning. Then have an independent scorer sub-agent score them 1 to 10. Fix and repeat until
   the score is 9 or more. If the scores stop rising, tell me it is diminishing returns and
   advise, but do not lower the target yourself. Only I change the target.
4. Show me a 150-word summary including the mode, elapsed budget, and any human handbacks.
   Wait for my explicit go-ahead on that plan before freezing it or launching the crew.
5. On my go-ahead, freeze the baseline: copy both files to your scratchpad with SHA256 hashes,
   and start `oversight-log.md` (time, change, reason, approved by).

## The crew

| Role | Started as | Job | Never |
|---|---|---|---|
| Lead | A new session | Runs the loop, applies the rules, keeps `state.json`, `decisions.md` and `ambiguities.md`, writes the final report | Does workers' or verifiers' tasks itself |
| Workers | Sessions started by the lead | Do the work, test their own output, report in the fixed format | Grade their own final verdict |
| Verifiers | Fresh sessions, one per pass | Re-test every criterion independently. Trust no report | Reuse a worker's evidence as proof |
| Safety watch | A read-only session | Every 10 minutes, checks for out-of-scope changes or harm against its before snapshot and returns observations to the designer | Writes files or changes the system |
| Drift auditor | A read-only session that you start | Every 30 minutes, compares the run, and your own edits, with the frozen baseline. Returns findings rated High, Medium or Low to the designer | Writes files, messages the crew or fixes anything |

Give each brief the goal, its inputs, its limits, its output format and a stop condition.
Distinguish observed from concluded everywhere. Both monitors return their numbered, UTC-stamped
observations via the session's read-only output to the designer. The designer records the session,
time, evidence reference and finding in the authorized log (for preflight, `preflight.md`).
Monitor sessions never append status lines, save snapshots, or write timer files. Use a
host-managed wake or an authorized controller to schedule them; verify the return path before work.

## Platform facts. Design around them

Use **Harness adapters** as a starting point. Inventory the tools, permissions, worker capacity
and return channels actually exposed in this session. Use available native workers and their
return channel for foreground design, review and attended work. If exposed and authorized,
use Claude Code's dynamic Workflow, a Kiro workflow, or Codex workers to give each separable
task an owner and return its artifact to a fresh verifier. Check the distinct session and
actual result before recording the review. Use individual foreground workers if the workflow
mechanism is absent. If an independent worker is unavailable, hold that review.
Do not infer an installed
registration, independent session, scheduler or permission boundary from an adapter example.
During preflight, record the actual session IDs, mechanisms used and observations supporting the
selected mode. A foreground worker's completion is evidence only for its foreground task.
For file-based handoff, use the inbox and numbered UTC status format below, with the designer
recording monitor replies.

## Rules

- **Change control.** Any change to the plan, the criteria, a gate, the stop rule or fairness
  needs my approval first. When I approve: bump the version, log the change, freeze a new
  baseline and tell the lead. Corrections that bring the run back in line with the plan need no
  approval, but log them too.
- **One rulings file.** Every reading of an ambiguous criterion goes in `ambiguities.md`, applies
  to everyone, and is what verifiers read.
- **Same method everywhere.** If there are arms or groups being compared, every check uses the
  same method in each. Exclude human wait from matched-arm active time. The elapsed wall-clock
  cap includes every wait, including waits for the user, qualification and final verification.
- **Never skip a check to save me a step.** Batch everything that needs me into one hand-off
  instead.
- **Hand-offs to me** go in a `user-entry.md` file: exactly what to type, where, and what not to
  click. I type `entered` in that member's session when done.
- **Refusals.** If an agent's own safety rules refuse a step, do not argue it round. Bring me
  options, and treat that step the same everywhere.
- **Never** send mail or chat to people, file tickets, share documents, or delete or damage
  anything outside the job. Draft; I send.

## Gates (preflight, logged in `preflight.md`)

1. Record each member's reported model and its source. Check each barred tool at the effective
   enforcement boundary with a no-effect permission probe or an isolated, inert fixture. Even
   if unexpectedly allowed, a probe must be incapable of sending, publishing, touching a real
   protected target or causing any prohibited side effect. Record the observed refusal. If safe
   proof is unavailable or the call is allowed, block the affected role and its dependent work.
2. Each member signs in where it needs to. Keep user-only steps with the user.
3. Place a uniquely numbered test in every member's inbox, including the lead's, without
   messaging the recipient about it. Verify that each member discovers it, acts on it and returns the number through
   its permitted channel. In attended mode an agreed human resume may start the turn; log it.
4. With a safety watch, it reads the protected state and returns the before snapshot; the designer
   records it before work. If the approved plan omitted the watch because nothing can be harmed,
   the designer records gate 4 as inapplicable with the scope and rationale. An absent required
   watch, snapshot or read-only return path blocks work.
5. **Unattended:** qualify the actual lead session and timer on this run. Record each of 60
   consecutive 600-second wakes from arming, with a UTC time and a lead response from that
   session to a new inbox item or a numbered heartbeat. An authorized scheduler may send the
   planned automatic resume at each interval. Require no human nudge. A scheduler exit,
   synthetic receipt or worker completion does not count. A missed wake or manual nudge from
   a human or operator breaks the streak; hold if a fresh full streak will not fit the deadline.
   **Attended:** mark the 60-wake test inapplicable to this mode and demonstrate one
   real handback and resume at the agreed checkpoint. Record who resumed, what state the next
   turn read and the returns from the applicable monitors. Do not claim unattended operation.

Only start work after the approved mode's applicable gates pass within its limits. A missing
timer, broken wake or exhausted budget does not switch modes. Pause at the safe point and report
the blocker. If an attended plan is feasible, obtain my explicit approval of the change, log it,
version and freeze the revised baseline, brief the lead and check its applicable gates before
resuming. An exhausted hard limit still holds unless the user changes it.

## Your job while it runs

- Every 30 minutes during active work, on your own verified timer for unattended work or the
  approved attended schedule:
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

Pick the one for the harness you run in. The imported method described its November 2026
adapter references as help and documentation, and reported an end-to-end crew on Claude Code
Desktop only. That report covers the imported method. For this revision verify all mechanisms
on the actual host. In particular, check items marked *(unconfirmed)* in
the applicable preflight gate before relying on them. The gate evidence and read-only monitor
rules above apply to every adapter. Observe the actual session returning at the planned interval
before relying on its timer.

### Claude Code Desktop

- **Sessions start only on a turn I typed.** Start every session the job will need, standby
  verifiers included, on my first go-ahead turn. Use native foreground workers for bounded passes. Persistent roles require the applicable preflight evidence.
- **The lead can send only 10 messages to other sessions per message I type.** So do not rely on
  messages:
  - The lead writes `agents/<member>/inbox/<n>.md`.
  - In unattended mode each file-writing member keeps one timer: before ending a turn it checks `kill -0` on its pid file, and
    only if that fails starts `sleep 600` in the background. It reads its inbox on every wake.
  - File-writing members reply by appending one numbered line, `#N <UTC time> <status>`, to their `status.md`.
  - The lead tracks the last `#N` handled for each file-writing member. Monitors return their
    numbered observations to the designer in read-only session output. Hold if a required
    monitor cannot return without writing.
  - In unattended mode a verifier that must wait mid-pass starts a timer too.
- **Timers die sometimes.** Only a message can wake that member. The lead's turn-end note then
  requests a human handback. A human resume is attended and follows the mode-change rule above.
- **Project `.claude/settings.json` deny rules apply even in bypass mode.** Put the crew in
  folders whose deny rules block the tools they must not use. Use the safe gate 1 probes to verify refusal.
- **Agents' headed browsers can steal keyboard focus.** Tell me to move them to their own macOS
  desktop. Agents never switch tabs while they wait for me, and they check every field before
  each submit.
- Take every timestamp from `date -u`, never from memory.

### Kiro (Kiro CLI and IDE)

| Need | Mechanism |
|---|---|
| Sessions | One process per member: `kiro-cli chat --agent <name> --no-interactive "<brief>"`; `--resume-id <id>` continues it. The `subagent` tool (alias `use_subagent`) runs sub-agents in parallel, and returns results to the parent. Use them for foreground tasks; test persistence separately for unattended roles. The `delegate` tool runs background agents (`/delegate status`); how long they live is *(unconfirmed)* |
| Messaging | Use inbox files for assignments. File-writing members append `status.md` lines. Monitors return read-only session output to the designer; block if unavailable |
| Timers | Hooks fire on events only, never on a clock, and a background `sleep` waking an idle agent is *(unconfirmed)*. Run each member from an outside loop or cron that re-invokes `kiro-cli chat --resume-id <id> --no-interactive "read your inbox"` every 600 seconds. Count only observed lead wakes meeting gate 5 |
| Deny rules | One agent JSON per role in `.kiro/agents/` or `~/.kiro/agents/`: `tools`, `allowedTools`, `toolsSettings.shell.deniedCommands` (deny is checked before allow), `toolsSettings.write.deniedPaths`. A `preToolUse` hook that exits with code 2 blocks the call. Whether 2.x deny lists hold under `--trust-all-tools` is *(unconfirmed)*, so prefer the hook. In V3, `permissions.rules` deny always wins |
| Model | Pin it with the agent JSON `model` field or `--model`; `kiro-cli chat --list-models` lists them. With `model: "auto"` a member may not know its model, so report the pinned name. A command that prints the active model mid-session is *(unconfirmed)* |

### Kiro Crew (the KiroCrew app)

From the app's bundled docs and code; not yet run in a crew.

| Need | Mechanism |
|---|---|
| Sessions | One `session_create(agent=<name>, model=<model>, message="<brief>")` per member. Each opens a sidebar tab that lasts until it is closed. Invoke this skill in a message as `$engos-orchestration-crew`. `spawn_run` sub-agents run in parallel but answer and exit, and have no session key, so use them for foreground tasks that need neither a timer nor session tools |
| Messaging | Use inbox files for assignments. File-writing members append `status.md` lines. Monitors return read-only session output to the designer; block if unavailable. `session_send(target, message)` can nudge a member and `session_read_message` reads one back. The stock `kirocrew-team-lead` agent allows `session_create`, `session_read_message` and `session_status`, but not `session_send`. `send_message` goes to the user (Slack, DM, dashboard), never to crew members |
| Timers | Where permitted for that role, use the host-managed `monitor_start(message="read your inbox", interval_secs=600, ...)`. It wakes in the same conversation, one loop per session, 24 cycles by default and 1000 at most, so set `max_cycles` or `max_runtime_secs` to cover the run. It is refused in cron, webhook and sub-agent sessions. `cron_add` and `HEARTBEAT.md` run in sessions of their own, so they cannot wake a member |
| Deny rules | A custom agent JSON per role with `toolsSettings` (`shell.denyByDefault`, `deniedCommands`, `write.fallbackAction: "deny"`), enforced at Kiro Crew's pre-tool-use gate. The stock `kirocrew--readonly` agent is for side turns only and cannot be started as a member |
| Model | Pin it with `model` on `session_create`. The lead reads each member's model and effort with `session_read_message`. A member reading its own model is *(unconfirmed)* |

### Codex (Codex CLI)

| Need | Mechanism |
|---|---|
| Sessions | One process per member: `codex exec "<brief>"`; `codex exec resume <id>` continues it; `--worktree` gives it its own git worktree. Sub-agents (`.codex/agents/<name>.toml` registered as `[agents.<name>]` in `config.toml`; tools `spawn_agent`, `send_input`, `wait_agent`, `close_agent`) run in parallel up to `agents.max_concurrent_threads_per_session`; use available workers for foreground tasks. Sub-agent persistence is *(unconfirmed)* |
| Messaging | Use inbox files for assignments. File-writing members append `status.md` lines. Monitors return read-only session output to the designer; block if unavailable. `codex queue --thread <id or name> --message "<text>"` queues a message for an existing session *(listed in help, not run)*. A parent reaches its own sub-agents with `send_input` |
| Timers | A `sleep` tool that ends early on new input exists for some models only *(unconfirmed for the model in use)*. Another candidate is an authorized outside loop or cron running `codex exec resume <id> "read your inbox"` every 600 seconds. Count only observed lead wakes meeting gate 5 |
| Deny rules | Start the safety watch and drift auditor with `-s read-only`, others with `-s workspace-write`, always explicitly, because a user config may default to `danger-full-access`. Command deny rules: `.rules` files with `prefix_rule(pattern=[...], decision="forbidden")` in `~/.codex/rules/`, or `<repo>/.codex/rules/` for a trusted project. Sub-agents inherit the parent's sandbox. Never pass `--ignore-rules`. Whether rules hold under `--dangerously-bypass-approvals-and-sandbox` is *(unconfirmed)* |
| Model | Pin it with `-m <model>` or `model` in `config.toml` and report that. `/status` in the interactive UI; a headless member reading its own model is *(unconfirmed)* |

### Gemini CLI

| Need | Mechanism |
|---|---|
| Sessions | One process per member: `gemini -p "<brief>"` (headless); `--resume <id or latest>` or `--session-id` continues it; `-w` gives it a worktree. Sub-agents (`.gemini/agents/<name>.md` or `~/.gemini/agents/`) run, report back and end, and cannot start others; use them for tasks that finish in the foreground. Whether they run in parallel is *(unconfirmed)* |
| Messaging | Use inbox files for assignments. File-writing members append `status.md` lines. Monitors return read-only session output to the designer; block if unavailable |
| Timers | The shell tool can run a background process, but no wake on its completion is documented, and hooks fire on CLI events only. Run each member from an outside loop or cron that re-runs `gemini -p --resume <id> "read your inbox"` every 600 seconds *(flag combination not run)*. Count only observed lead wakes meeting gate 5 |
| Deny rules | Policy engine TOML rules with `decision = "deny"` in `~/.gemini/policies`, or via `--admin-policy`. Project `.gemini/policies` currently has no effect (gemini-cli issue 18186). `tools.exclude` is deprecated; `tools.core` is an allowlist. A user-tier deny outranks the yolo allow-all by the documented priority formula *(concluded from docs, not tested)* |
| Model | Pin it with `-m` or `model.name`. A headless run with `--output-format stream-json` reports the model in its `init` event; `/stats model` shows usage. With the model router on, a member cannot reliably name its model, so report the `init` event's model |

### Any other harness (generic fallback)

Use the generic adapter if the harness can start workers and exchange the required evidence within role permissions.

| Need | Mechanism |
|---|---|
| Sessions | Start each member as its own session or process if the harness can. Otherwise use the lead's sub-agents, the same fallback as above |
| Messaging | Use inbox files for assignments. File-writing members append `status.md` lines. Monitors return read-only session output to the designer. If no read-only result path exists, hold work that needs the monitor |
| Timers | A background timer that wakes the member if the harness has one. Otherwise an outside loop, cron or scheduler that re-invokes each member every 600 seconds. If neither exists, hold unattended work and use the attended handback only under the approved plan |
| Deny rules | Whatever the harness enforces outside the agent's own choice (sandbox, read-only mode, deny list). A tool it cannot bar fails gate 1; bring that to me |
| Model | Pin the model at start where the harness allows and report the pinned name |
