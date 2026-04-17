---
name: "pulse"
description: "High signal-to-noise comms triage across Gmail and Google Chat. Read-only. Deterministic priority classification. Quick action recommendations."
---
# Pulse — Comms Triage

## Purpose
Use this capability when the user needs intent
- Use this capability when you need a fast, high signal-to-noise view of outstanding emails and chat messages across Gmail and Google Chat. It exists to cut through inbox noise and surface what actually needs your attention, with deterministic priority classification and actionable next steps.
- Classify incoming messages by urgency using deterministic rules (not vibes), present them in a scannable format with clickable links, and optionally step through actions one-by-one with explicit user approval. Learn from user feedback over time via a persistent memory system.

Constraints
- Classify each item into 🔴 Urgent / 🟡 Needs Response / 🔵 FYI using deterministic rules.

Requested Outcome
- allowed: read Gmail messages and headers, read Chat messages and spaces, read Chat space read state, read/write memory file, present structured output

Rejected/Out-of-Scope Signals
- None

## Primary Objective
Use this capability when you need a fast, high signal-to-noise view of outstanding emails and chat messages across Gmail and Google Chat. It exists to cut through inbox noise and surface what actually needs your attention, with deterministic priority classification and actionable next steps.

## Output Directory
- `reports/<slug>/<timestamp>-summary.md` style report paths are the default when file output is requested
- repo-ready artifacts should be named explicitly when the user asks for direct changes

## Workflow
1. Clarify the task, success criteria, and hard constraints.
2. Inspect the relevant repo or source context before making recommendations.
3. Produce deterministic outputs with explicit evidence, boundaries, and target paths or artifacts.
4. Record risks, review timing, and anything that requires manual confirmation.

## Rules
- Keep the capability reusable and deterministic.
- Publish advisory guidance only unless the caller explicitly requests execution.
- Do not claim orchestration, delegation, or runtime-control ownership.

## Required Inputs
- source text
- user intent/context

## Required Output
- deterministic summary
- uplift payload
- capability recommendation
- deployment guidance
- explicit risks and open questions
- target paths, commands, or artifact names when applicable

## Constraints
- - forbidden: send, reply, forward, delete, archive, modify, or label any message during triage. Write commands (`+reply`, `+forward`, `+send`) are ONLY permitted during `/act` mode after explicit per-item user approval.
- ## Required Inputs
- - `gws` CLI authenticated (`gws auth status` must pass)
- ## Required Output
- Every pulse run must include:
- ### Example: Hot items only
- Returns only 🔴 and 🟡 items
- skipping 🔵 FYI noise.
- | Safety invariant | No write commands executed without explicit per-item user approval |
- Classify each item into 🔴 Urgent / 🟡 Needs Response / 🔵 FYI using deterministic rules.
- forbidden: send, reply, forward, delete, archive, modify, or label any message during triage. Write commands (`+reply`, `+forward`, `+send`) are ONLY permitted during `/act` mode after explicit per-item user approval.
- `gws` CLI authenticated (`gws auth status` must pass)

## Invocation Hints
- check my email / inbox / messages
- what needs my attention
- any urgent messages
- triage my comms / communications
- what's new in chat
- pulse, pulse /hot, pulse /email, pulse /chat

## Examples
### Example Request
> Use `pulse` to inspect a repo change, produce a deterministic recommendation, and make the review timing explicit.

### Example Output Shape
- current state summary
- findings or recommendation
- target paths or commands
- risks and review timing

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Intent coverage | The capability states when to use it and what success looks like |
| Output contract | Deliverables are deterministic and reviewable |
| Boundary clarity | The capability says what it will not do |
| Surface usability | The body is strong enough to support every emitted surface |

## Review Timing
- commit: when commands, behavior, or metadata contracts change
- pull request: when repo structure, CI, release flow, or docs drift materially
- merge: when adjacent capability or doc surfaces changed and drift is likely
- release: verify shipped behavior, install flow, and references against the final state

## Advisory Notes
- Relationship and org-graph metadata remain advisory for future orchestrators.
- Use the sidecar descriptor as the canonical machine-readable contract.
- Emit surfaces for: `claude_skill, codex_skill, gemini_skill, kiro_skill`


Capability resource: `.codex/skills/pulse/resources/capability.json`
