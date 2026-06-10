---
name: opex-briefing
description: >
  Generates an executive-ready HTML briefing for Operational Excellence reviews.
  Pulls active incidents from Jira, builds Five Whys causal chains, maps fix status,
  and produces pre-written talking points. Output is a single BRIEFING.html with
  left-nav, actions box, and per-incident drill-downs.
inputs:
  jira_projects:
    description: "Jira project keys to query"
    default: ["EA", "IA"]
  priority_filter:
    description: "Priority levels to include"
    default: ["Blocker", "Critical"]
  output_format:
    description: "html | md | both"
    default: "both"
---

## User Input

The user provides ticket keys (e.g., `EA-6284, EA-5649`) and optionally a meeting date. If ticket keys are provided inline, use those directly. If the user says "prep for next meeting," determine tickets from the tracking doc or active query, then confirm with the user.

Output goes to: `~/Library/CloudStorage/GoogleDrive-scott.parrish@appian.com/My Drive/@Reference/Operational-Excellence/YYYYMMDD/`

## Appian Context (Behavioral Rules)

- **EA** = External/Customer-facing incidents. **IA** = Internal infrastructure.
- **Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.
- **`Executive-Incident-Communication` label** = C-level visibility. Talking points must be extra precise.
- **Root Cause Categories**: Infrastructure, Code Defect, Configuration, Capacity, External Dependency, Process Gap.

## Steps

### 1. Gather Active Incidents
- If ticket keys provided: fetch each directly
- Otherwise query: `project in ({{jira_projects}}) AND status != Closed AND priority in ({{priority_filter}}) ORDER BY priority DESC, created ASC`
- Extract per ticket: key, summary, priority, status, assignee, created date, linked tickets, customer impact field
- **VERIFY**: Confirm each ticket's current status by reading it directly. Do not rely on cached/stale query results.

### 2. Build Root Cause (Five Whys)
- Read all comments and linked postmortem docs on each incident
- Follow child/linked engineering tickets for technical detail
- Construct a 3–5 level causal chain: customer impact → immediate cause → systemic gap
- Each "why" = one factual sentence citing its source (comment author + date, or linked ticket key)
- **MUST end with a Preventive Action statement**: the durable fix that prevents recurrence — not just repair of the current instance. Ask: "What changes so this class of failure cannot happen again?"
- If no RCA exists: state `"Root cause: Not yet determined."` — never speculate

### 3. Map Fix Tickets
- For each incident, collect ALL child/linked remediation tickets (stories, bugs, tasks)
- Per fix ticket: key, summary, status, assignee, target ship date (or "no date")
- **VERIFY**: Open each fix ticket. Confirm status matches today. Flag contradictions (e.g., fix "Done" but incident still open).

### 4. Detect Patterns
- Search for prior incidents with same root cause component or failure mode (last 6 months)
- If 2+ prior tickets exist: state the pattern, list ticket keys, note what was tried before
- **VERIFY**: Pull each cited prior ticket. Confirm it's real and relevant — not just keyword-similar. In the output, state HOW you confirmed relevance (same component? same RCA category? same author grouped them?).

### 5. Write Coaching Sections
- **What to Say**: 3–4 bullets. First person, present tense. As if spoken aloud in the meeting.
- **If They Ask**: Top 3 anticipated follow-up questions with pre-written answers.

### 6. Produce Output
- Generate `BRIEFING.html` (primary) using the template structure below
- Generate `BRIEFING.md` (companion) with equivalent content, flat structure
- Footer: generation timestamp + `opex-briefing` skill attribution

## Output Template (HTML)

```
┌─────────────────────────────────────────────────────┐
│ LEFT NAV              │  MAIN CONTENT               │
│                       │                             │
│ • Summary             │  ┌─ ACTIONS BOX (top) ────┐│
│ • Incident 1          │  │ Decisions needed today  ││
│ • Incident 2          │  │ • action item 1         ││
│ • ...                 │  │ • action item 2         ││
│ • Bottom Line         │  └─────────────────────────┘│
│                       │                             │
│                       │  SUMMARY TABLE              │
│                       │  ticket | status | owner    │
│                       │                             │
│                       │  PER-INCIDENT SECTION:      │
│                       │  ┌─ Facts ────────────────┐ │
│                       │  │ Source-cited fields     │ │
│                       │  └────────────────────────┘ │
│                       │  ┌─ Five Whys ────────────┐ │
│                       │  │ 1. Why → 2. Why → ...  │ │
│                       │  │ Preventive Action: ... │ │
│                       │  └────────────────────────┘ │
│                       │  ┌─ Recurring Pattern ────┐ │
│                       │  │ (if 2+ prior tickets)  │ │
│                       │  │ ticket | same cause?   │ │
│                       │  └────────────────────────┘ │
│                       │  ┌─ Fix Tickets ──────────┐ │
│                       │  │ ticket | status | date  │ │
│                       │  └────────────────────────┘ │
│                       │  ┌─ What to Say (green) ──┐ │
│                       │  │ • bullet               │ │
│                       │  │ • bullet               │ │
│                       │  └────────────────────────┘ │
│                       │  ┌─ If They Ask ──────────┐ │
│                       │  │ Q: ...  A: ...         │ │
│                       │  └────────────────────────┘ │
│                       │                             │
│                       │  BOTTOM LINE (orange box)   │
│                       │  1-sentence overall status  │
└─────────────────────────────────────────────────────┘
```

Per-incident section order is fixed: **Facts → Five Whys (ending with Preventive Action) → Recurring Pattern (if any) → Fix Tickets → What to Say → If They Ask**

## Verification Checklist (Run Before Finalizing)
- Every ticket link resolves to the correct ticket
- Every status claim matches the ticket's status *today*
- Every named owner matches the current Jira assignee
- Every RCA claim cites who confirmed it and where (comment link or ticket key)
- Every Five Whys chain ends with a **Preventive Action** — a durable fix that prevents the class of failure, not just repair of this instance
- Every "pattern" claim lists real prior ticket keys that were individually verified, with stated reason for relevance
- No speculative root cause is presented as confirmed
- Fix tickets are actually linked/children of the incident — not coincidental matches

## Voice (5 Rules)
1. **Active voice, no hedging.** "The deploy broke X" not "It appears X may have been impacted."
2. **Unconfirmed = say so explicitly.** "Not confirmed" or "Investigating" — never guess.
3. **Five Whys: one sentence per level. Factual. No adjectives.**
4. **What to Say: first person, present tense, spoken aloud.** "The fix ships Tuesday."
5. **No corporate filler.** Zero tolerance for "synergies," "leverage," "going forward," "learnings."

## Edge Cases
- **0 incidents**: Produce a 1-line briefing: "No active Blocker/Critical incidents. No action items."
- **>5 incidents**: Top 5 by severity × age in main sections. Remainder in appendix table.
- **No RCA yet**: Include the incident. State it. Coaching says: "We need [owner] to start the postmortem."
- **Conflicting info**: Present both sources with dates. Mark as "Unresolved — needs clarification."

## Definition of Done
1. Every incident has Facts, Five Whys (or explicit "not started"), and verified fix tickets
2. Every incident has "What to Say" coaching (3–4 bullets) and "If They Ask" (3 Q&As)
3. Actions box at top contains every decision or escalation needed *today*
4. Verification checklist passes with zero failures
5. A leader can scan the full briefing in <5 minutes and know what to say and what to ask for
