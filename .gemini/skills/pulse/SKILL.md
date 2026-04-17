---
name: "pulse"
description: "High signal-to-noise comms triage across Gmail and Google Chat. Read-only. Deterministic priority classification. Quick action recommendations."
---
# Pulse — Comms Triage

## Purpose
Use this capability when you need a fast, high signal-to-noise view of outstanding emails and chat messages across Gmail and Google Chat. It exists to cut through inbox noise and surface what actually needs your attention, with deterministic priority classification and actionable next steps.

## Primary Objective
Classify incoming messages by urgency using deterministic rules (not vibes), present them in a scannable format with clickable links, and optionally step through actions one-by-one with explicit user approval. Learn from user feedback over time via a persistent memory system.

## Workflow Contract
1. Check `gws auth status` — fail fast if auth is expired.
2. Gather data from Gmail (`+triage`) and configured Chat spaces (`spaces messages list`).
3. Fetch email headers (`+read --headers`) for To/CC/List addressing classification.
4. Detect chat @mentions via `annotations` array and unread state via `getSpaceReadState`.
5. Classify each item into 🔴 Urgent / 🟡 Needs Response / 🔵 FYI using deterministic rules.
6. Apply memory adjustments (boost/demote) from `~/.kiro/scratch/pulse/memory.json`.
7. Present results as a structured table with clickable links and proposed actions.
8. On `/act`, step through actions one-by-one with user approval before any write.
9. On `/rate`, extract generalizable patterns and persist to memory.

## Boundaries
- allowed: read Gmail messages and headers, read Chat messages and spaces, read Chat space read state, read/write memory file, present structured output
- forbidden: send, reply, forward, delete, archive, modify, or label any message during triage. Write commands (`+reply`, `+forward`, `+send`) are ONLY permitted during `/act` mode after explicit per-item user approval.
- escalation: if the user asks for a write action outside `/act` mode, stop and confirm before executing

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- check my email / inbox / messages
- what needs my attention
- any urgent messages
- triage my comms / communications
- what's new in chat
- pulse, pulse /hot, pulse /email, pulse /chat

## Required Inputs
- `gws` CLI authenticated (`gws auth status` must pass)
- Configured chat spaces (auto-discovered on first run or manually configured in SKILL.md)

## Required Output
Every pulse run must include:
- Timestamp header
- Priority-classified table with: #, Addr, From, Subject (clickable link), Age, Action
- Source summary footer (Gmail count, Chat spaces/msgs, memory signal count)
- Proposed action list for 🔴 and 🟡 items

## Examples

### Example: Default triage
```
pulse
```
Returns 20 unread emails + unread chat messages across configured spaces, classified into 🔴/🟡/🔵.

### Example: Hot items only
```
pulse /hot
```
Returns only 🔴 and 🟡 items, skipping 🔵 FYI noise.

### Example: Rate items
```
pulse /rate +3 +4 -1 -2
```
Boosts items 3 and 4, demotes items 1 and 2. Extracts generalizable patterns (sender, subject, source app, addressing) and saves to memory.

### Example: Step through actions
```
pulse /act
```
Walks through each 🔴/🟡 item, proposes a response, waits for approval before sending.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Auth check | Fails fast with actionable fix command if auth is expired |
| Classification determinism | Same messages always produce the same priority tier |
| Addressing accuracy | To/CC/List correctly detected from headers, @mentions from annotations |
| Memory persistence | Ratings survive across sessions, strengthen with repetition |
| Safety invariant | No write commands executed without explicit per-item user approval |
| Output scannability | Table is readable in < 10 seconds, links are clickable |


Capability resource: `.gemini/skills/pulse/resources/capability.json`
