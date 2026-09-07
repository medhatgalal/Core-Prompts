---
name: opex-briefing
description: >
  Generates an executive-ready HTML briefing for Operational Excellence reviews.
  Pulls active incidents from Jira, builds Five Whys causal chains, maps fix status,
  and produces pre-written talking points. Outputs a single BRIEFING.html with
  left-nav, actions box, and per-incident drill-downs.
inputs:
  jira_projects:
    description: "Jira project keys to query"
    default: ["EA", "IA"]
  priority_filter:
    description: "Priority levels to include"
    default: ["Blocker", "Critical"]
  output_format:
    description: "txt | pdf | gdoc | html | md | both"
    default: "both"
---

## User Input

The user provides ticket keys (e.g., `EA-6284, EA-5649`) and optionally a meeting date. Use inline ticket keys directly. If the user says "prep for next meeting," pull tickets from the tracking doc or active query, then confirm with the user.

Output destination: `~/Library/CloudStorage/GoogleDrive-*/My Drive/@Reference/Operational-Excellence/YYYYMMDD/`

## Appian Context (Behavioral Rules)

- **EA** = External/Customer-facing incidents. **IA** = Internal infrastructure.
- **Postmortem SLA**: P1/P2 require postmortem within 5 business days of resolution. Flag violations.
- **`Executive-Incident-Communication` label** = C-level visibility. Talking points must cite specific data, timelines, and owners — no generalities.
- **Root Cause Categories**: Infrastructure, Code Defect, Configuration, Capacity, External Dependency, Process Gap.

## Steps

### 1. Gather Active Incidents
- If ticket keys provided: fetch each directly
  ```
  acli jira workitem view EA-1234 --fields '*all' --json
  ```
- Otherwise query: `project in ({{jira_projects}}) AND status != Closed AND priority in ({{priority_filter}}) ORDER BY priority DESC, created ASC`
- Extract per ticket: key, summary, priority, status, assignee, created date, linked tickets, customer impact field
- **Critical custom fields**: `customfield_10663` (customer impact), `customfield_10666` (affected customers), `customfield_10253` (immediate fix), `customfield_10673` (postmortem link), all `labels`, all `issuelinks`
- **VERIFY**: Read each ticket directly to confirm current status. Never use cached or stale query results.

### 2. Build Root Cause (Five Whys)
- Read all comments and linked postmortem docs on each incident
- **Comment keywords to search**: `root cause`, `RCA`, `caused by`, `postmortem`, `customer notified`, `resolved at`
- Follow child/linked engineering tickets for technical detail
- Build a 3–5 level causal chain: customer impact → immediate cause → systemic gap
- Each "why" = one factual sentence citing its source (comment author + date, or linked ticket key)
- **End with a Preventive Action statement**: the durable fix that blocks recurrence of this failure class. Ask: "What changes so this class of failure cannot happen again?"
- If no RCA exists: state `"Root cause: Not yet determined."` — never speculate

### 3. Map Fix Tickets
- Collect ALL child/linked remediation tickets (stories, bugs, tasks) for each incident
- Per fix ticket: key, summary, status, assignee, target ship date (or "no date")
- **VERIFY**: Open each fix ticket. Confirm status matches today. Flag contradictions (e.g., fix "Done" but incident still open).

### 4. Detect Patterns
- Search for prior incidents sharing the same root cause component or failure mode (last 6 months)
- If 2+ prior tickets exist: state the pattern, list ticket keys, note prior remediation attempts
- **VERIFY**: Open each cited prior ticket. Confirm relevance — not just keyword similarity. State HOW you confirmed relevance (same component? same RCA category? same author grouped them?).

### 5. Write Coaching Sections
- **What to Say**: 3–4 bullets. First person, present tense. As if spoken aloud in the meeting.
- **If They Ask**: Top 3 anticipated follow-up questions with pre-written answers.

### 6. Produce Output
- Generate `BRIEFING.html` (primary) using the template structure below
- Generate `BRIEFING.md` (companion) with equivalent content, flat structure
- Footer: generation timestamp + `opex-briefing` skill attribution

| Format | File | Method |
|--------|------|--------|
| html | `BRIEFING.html` | Direct write |
| md | `BRIEFING.md` | Direct write |
| txt | `BRIEFING.txt` | Strip HTML tags, plain text |
| pdf | `BRIEFING.pdf` | `pandoc BRIEFING.html -o BRIEFING.pdf` |
| gdoc | Google Doc | `gws docs +write --title "OpEx Briefing YYYYMMDD"` |

## Output Template (HTML)

### Layout & CSS (Mandatory)

The HTML MUST use a CSS Grid layout:
```css
body { display: grid; grid-template-columns: 200px 1fr; min-height: 100vh; }
```

### Color Scheme (Exact Values)

| Element | Color | Usage |
|---------|-------|-------|
| Nav background | `#2c3e50` | Sticky left sidebar |
| Nav title | `#e67e22` | Orange, bold, top of nav |
| h2 headings | `#a93226` | Red text + 4px left border |
| Table headers | `#2c3e50` | Dark blue background, white text |
| Summary table headers | `#a93226` | Red background, white text |
| Say-box | `#eaf7ea` bg, `#27ae60` left-border | Green coaching box |
| Five Whys box | `#fafafa` bg, `#a93226` left-border | Red-bordered analysis |
| Bottom-line / Actions box | `#fdf2e9` bg, `#e67e22` 3px border | Orange decision box |
| Status tag (red) | `#fdecea` bg, `#c0392b` text | Active/unstarted fixes |
| Status tag (orange) | `#fdf2e9` bg, `#e67e22` text | In-progress/no date |
| Status tag (green) | `#eaf7ea` bg, `#27ae60` text | Completed/shipped |

### Mandatory Rendering Rules

1. **All Jira ticket references MUST be clickable links** to `https://appian-eng.atlassian.net/browse/{KEY}`
2. **Customer COUNT must be prominent** — bold in the intro paragraph (e.g., `<strong>4 customers impacted.</strong>`) AND shown per-row in the summary table
3. **Nav includes sub-items per incident**: Facts, Five Whys, Pattern (if present), Fix Tickets, What to Say, If They Ask
4. **Print stylesheet**: hides nav, removes backgrounds, uses `page-break-inside: avoid` on key sections
5. **Responsive**: at ≤768px, collapse nav off-screen

### Structure (Top to Bottom)

**Left Nav** (sticky, 200px): nav-title (orange) → ⚡ Actions → 📋 Summary → per-ticket links (each with sub-items: Facts, Five Whys, Fix Tickets, What to Say, If They Ask).

**Main Content** (top to bottom):
1. `<h1>` title + date
2. Intro paragraph with `<strong>` customer count
3. **Actions Box** (`.bottom-line` orange border) — `<h2>` + `<ol>` of today's decisions/escalations
4. **Summary Table** (red headers) — columns: #, Ticket, What Broke, Who's Affected, Owner, Fix Status
5. `<hr>` separator
6. **Per-Incident Sections** (repeat per incident):
   - `<h2>` "KEY — Title"
   - `<h3>` "The Facts" → `<dl class="facts">` with dt/dd pairs
   - `<h3>` "Five Whys" → `<div class="five-whys">` (see format below)
   - `<h3>` "Recurring Pattern" (ONLY if 2+ prior tickets) → `<table>`
   - `<h3>` "Fix Tickets" → `<table>` (Ticket | What | Status)
   - `<h3>` "What You Say" → `<div class="say-box">` with `<ul>` bullets
   - `<h3>` "If They Ask" → `<table>` (Question | Answer)
7. `<footer>` with generation timestamp + skill attribution

### Five Whys Format

Each why is a `<p>` with `<strong>N. Why ...?</strong><br>` followed by the factual answer. After all whys, a separator line (`border-top`) and then:
```html
<p><strong>Preventive action:</strong> [durable fix statement]</p>
```

### Recurring Pattern Table (Required Columns)

When 2+ prior tickets share the same root cause:
```html
<table>
<tr><th>Ticket</th><th>Summary</th><th>Same root cause?</th></tr>
<tr><td><a href="...">KEY</a></td><td>description</td><td>✅ Confirmed | ⚠️ Likely | ❌ No</td></tr>
</table>
```

## Verification Checklist (Run Before Finalizing)
- Every ticket link resolves to the correct ticket
- Every status claim matches the ticket's status *today*
- Every named owner matches the current Jira assignee
- Every RCA claim cites who confirmed it and where (comment link or ticket key)
- Every Five Whys chain ends with a **Preventive Action** — a durable fix that blocks the failure class, not just this instance
- Every "pattern" claim lists verified prior ticket keys with stated relevance reason
- No speculative root cause appears as confirmed
- Fix tickets link directly to the incident as children or linked issues — not coincidental matches

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

## Error Handling

| Error | Detect | Action |
|-------|--------|--------|
| Auth failure | `acli` returns 401/403 | Abort. Print "Re-authenticate: `acli auth login`" |
| Ticket not found | 404 or empty response | Skip ticket. Warn in output footer. |
| Access denied | 403 on specific ticket | Note "[KEY]: no access" in output. Continue. |
| All tickets fail | Zero successful fetches | Abort with clear error. Do not produce empty briefing. |
| GWS unavailable | `gws` timeout or auth error | Skip gdoc output. Fall back to local file only. |
| Duplicate input | Same key listed twice | Deduplicate silently. Fetch once. |

## Definition of Done
1. Every incident has Facts, Five Whys (or explicit "not started"), and verified fix tickets
2. Every incident has "What to Say" coaching (3–4 bullets) and "If They Ask" (3 Q&As)
3. Actions box at top lists every decision or escalation needed *today*
4. Verification checklist passes with zero failures
5. A leader scans the full briefing in <5 minutes and knows what to say and what to ask for
