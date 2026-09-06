---
name: "opex-briefing"
description: "txt | pdf | gdoc | html | md | both"
capability_type: "skill"
install_target: "repo_local"
---

# Opex Briefing

## Purpose
Use this capability when the user needs intent
- *Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.

Constraints
- *Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.

Requested Outcome
- Output destination: `~/Library/CloudStorage/GoogleDrive-*/My Drive/@Reference/Operational-Excellence/YYYYMMDD/`
- Extract per ticket: key, summary, priority, status, assignee, created date, linked tickets, customer impact field

Rejected/Out-of-Scope Signals
- None

## Primary Objective
Intent
- *Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.

Constraints
- *Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.

Requested Outcome
- Output destination: `~/Library/CloudStorage/GoogleDrive-*/My Drive/@Reference/Operational-Excellence/YYYYMMDD/`
- Extract per ticket: key, summary, priority, status, assignee, created date, linked tickets, customer impact field

Rejected/Out-of-Scope Signals
- None

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
## Constraints
- - **Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.
- - **`Executive-Incident-Communication` label** = C-level visibility. Talking points must cite specific data, timelines, and owners — no generalities.
- - If no RCA exists: state `"Root cause: Not yet determined."` — never speculate
- - Per fix ticket: key
- summary
- status
- assignee
- target ship date (or "no date")
- The HTML MUST use a CSS Grid layout:
- | Status tag (orange) | `#fdf2e9` bg, `#e67e22` text | In-progress/no date |
- 1. **All Jira ticket references MUST be clickable links** to `https://appian-eng.atlassian.net/browse/{KEY}`
- 2. **Customer COUNT must be prominent** — bold in the intro paragraph (e.g., `<strong>4 customers impacted.</strong>`) AND shown per-row in the summary table
- - `<h3>` "Recurring Pattern" (ONLY if 2+ prior tickets) → `<table>`
- ### Recurring Pattern Table (Required Columns)
- <tr><td><a href="...">KEY</a></td><td>description</td><td>✅ Confirmed | ⚠️ Likely | ❌ No</td></tr>
- - No speculative root cause appears as confirmed
- 1. **Active voice, no hedging.** "The deploy broke X" not "It appears X may have been impacted."
- 3. **Five Whys: one sentence per level. Factual. No adjectives.**
- 5. **No corporate filler.** Zero tolerance for "synergies," "leverage," "going forward," "learnings."
- - **0 incidents**: Produce a 1-line briefing: "No active Blocker/Critical incidents. No action items."
- - **No RCA yet**: Include the incident. State it. Coaching says: "We need [owner] to start the postmortem."
- | Access denied | 403 on specific ticket | Note "[KEY]: no access" in output. Continue. |
- | All tickets fail | Zero successful fetches | Abort with clear error. Do not produce empty briefing. |
- | GWS unavailable | `gws` timeout or auth error | Skip gdoc output. Fall back to local file only. |
- **Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.
- **`Executive-Incident-Communication` label** = C-level visibility. Talking points must cite specific data, timelines, and owners — no generalities.
- If no RCA exists: state `"Root cause: Not yet determined."` — never speculate
- Per fix ticket: key
- **All Jira ticket references MUST be clickable links** to `https://appian-eng.atlassian.net/browse/{KEY}`
- **Customer COUNT must be prominent** — bold in the intro paragraph (e.g., `<strong>4 customers impacted.</strong>`) AND shown per-row in the summary table
- `<h3>` "Recurring Pattern" (ONLY if 2+ prior tickets) → `<table>`
- No speculative root cause appears as confirmed
- **Active voice, no hedging.** "The deploy broke X" not "It appears X may have been impacted."
- **Five Whys: one sentence per level. Factual. No adjectives.**
- **No corporate filler.** Zero tolerance for "synergies," "leverage," "going forward," "learnings."
- **0 incidents**: Produce a 1-line briefing: "No active Blocker/Critical incidents. No action items."
- **No RCA yet**: Include the incident. State it. Coaching says: "We need [owner] to start the postmortem."

## Invocation Hints
- Intent
- *Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.

Constraints
- *Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.

Requested Outcome
- Output destination: `~/Library/CloudStorage/GoogleDrive-*/My Drive/@Reference/Operational-Excellence/YYYYMMDD/`
- Extract per ticket: key, summary, priority, status, assignee, created date, linked tickets, customer impact field

Rejected/Out-of-Scope Signals
- None


## Examples
### Example Request
> Use `opex-briefing` to inspect a repo change, produce a deterministic recommendation, and make the review timing explicit.

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
