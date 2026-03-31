---
name: "weekly-intel"
description: "Multi-source weekly intelligence gathering, convergence, fact-check audit, and single-document report generation (exec narrative body + technical appendices) for any team, project, or time window."
---
# Weekly Intelligence — Multi-Source Progress Report with Fact-Check Audit

## Purpose
Use this capability when a leader, manager, or IC needs a comprehensive, fact-checked progress report synthesized from multiple data sources (issue trackers, code repositories, chat spaces, meeting notes, documents) for a specific team, project, or time window.

## Primary Objective
Gather raw data from every available source, converge findings into a unified picture, audit every claim against primary evidence, and produce a single report document: an exec-friendly narrative body (no jargon, no ticket numbers) followed by named appendices containing all technical detail, source links, and evidence.

## In Scope
- Gathering data from issue trackers, git repos, code review platforms, chat spaces, and meeting notes
- Cross-referencing and converging findings across sources
- Fact-checking every substantive claim against primary evidence
- Producing a single report with an exec-friendly narrative body and technical appendices
- Declaring confidence levels per claim category

## Out of Scope
- Modifying any source system (tickets, repos, chat, docs)
- Making recommendations about what the team should do next (unless explicitly asked)
- Comparing teams against each other
- Forecasting future delivery dates
- Accessing private or restricted data beyond what the authenticated user can see

## Non-Negotiables
- Every quantitative claim must be re-verified before inclusion
- Self-reported numbers must not be presented as automated measurements
- Numbers must not be rounded in a direction that flatters the result
- The exec narrative must contain zero ticket numbers, MR numbers, or commit hashes
- The internal consistency check between the narrative body and appendices must not be skipped

## Agent Operating Contract
When emitted as an agent, this capability is read-heavy and synthesis-focused.

Mission:
- discover and collect data from all relevant sources within the specified time window
- cross-reference findings across sources to build a unified, non-duplicated picture
- audit every substantive claim before including it in a report
- produce a single report document with exec body and technical appendices

Responsibilities:
- source discovery and data collection across issue trackers, git repos, code review platforms, chat spaces, and meeting notes
- convergence of overlapping or conflicting information
- fact-check audit with confidence ratings per claim category
- single-document report generation (exec body + technical appendices)

## Tool Boundaries
- allowed: read from issue trackers, git repos, code review platforms, chat APIs, document APIs; write report files; run convergence and audit passes
- forbidden: modifying tickets, merging code, sending messages, or taking any action beyond reading and reporting
- escalation: if a claim cannot be verified from primary sources, mark it as unverified rather than asserting it

## Output Directory
When file output is requested, default to:
- `reports/<project>-weekly-report-<date>.md`

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- what happened this week / last week / since Tuesday
- weekly status report for my team
- summarize progress across these chat spaces and repos
- give me something I can share with leadership
- pull together what we accomplished and what's at risk

## Required Inputs
Ask the user for these before starting. If the user provides partial info, auto-detect the rest and confirm.

1. **Team or project name** — what team, project, or product area is this report for?
2. **Time window** — what date range? (default: last 7 business days from today)
3. **Chat spaces** — which Google Chat spaces should be checked? (provide names, or say "search for X")
4. **Git repositories** — which repos? (local paths or remote URLs)
5. **Issue tracker project** — Jira project key(s) and any label/component filters; any teams to exclude
6. **Meeting notes** — any Gemini Notes or Google Docs to check? (provide search terms or doc IDs)
7. **Audience** — who is the primary reader? (exec leadership, engineering management, the team itself)
8. **Known initiatives** — any active initiatives, epics, or goals to track specifically?

## Source Discovery (Hybrid Auto-Detection)

On first run for a project, auto-detect sources and confirm with the user:

- **Git repos:** scan for remotes via `git remote -v` in the working directory
- **Chat spaces:** search by project name via chat space list API
- **Jira project:** infer from commit message prefixes (e.g., `LCP-` → project `LCP`)
- **Meeting notes:** search Drive for docs matching `<project> AND (Huddle OR Notes OR Gemini)` modified in the time window

After confirmation, save the config to `.weekly-intel.json` in the repo root so subsequent runs skip discovery:

```json
{
  "project": "Composer",
  "jira_project": "LCP",
  "jira_exclude": ["smart search"],
  "chat_spaces": ["spaces/AAQAomEIX68", "spaces/AAQAcHm-Bgo"],
  "git_repos": ["/path/to/repo"],
  "gitlab_repos": ["gitlab.example.com/org/repo"],
  "gemini_search_terms": ["Composer Huddle", "Composer Leadership"],
  "audience": "exec"
}
```

## Workflow

### Phase 1: Data Collection

For each source type, gather raw data within the specified time window.

**Issue Tracker:**
- Tickets closed in window (with status transition verification)
- Tickets currently in progress
- Open bugs by priority
- Active initiatives and epics
- Categorize closed tickets: product features vs infrastructure/test fixes vs shared platform

**Git Repositories:**
- Commit log with ticket references (non-merge commits)
- Total commit count (including merges)

**Code Review Platform:**
- Merged merge requests / pull requests in the window
- MR titles and linked tickets

**Chat Spaces:**
- Messages within the time window from each target space
- Extract: topics discussed, decisions made, blockers raised, bugs reported, links shared

**Meeting Notes / Documents:**
- Search for docs matching project name modified in the window
- Extract: decisions, action items, key discussion points, attendee context

### Phase 2: Convergence

Cross-reference findings across all sources:

1. Map tickets to MRs to commits — verify closed tickets have corresponding merged code
2. Map chat discussions to tickets — verify issues raised in chat are tracked
3. Identify work not in the issue tracker — MRs or chat discussions with no ticket
4. Identify tickets with no activity — marked "In Progress" with no commits or MRs
5. Categorize all closed tickets — separate product work from infrastructure; report both with context
6. Build initiative status map — for each known initiative/epic: what shipped, what's in progress, what's blocked

### Phase 3: Fact-Check Audit

Audit depth auto-scales based on audience:
- **Audience = exec/leadership/stakeholders:** Full audit (mandatory)
- **Audience = team/self:** Skip audit, produce appendices only (no exec body)

For each substantive claim, verify:
- **Quantitative claims** (ticket counts, MR counts, scores) — re-run the query and confirm; note methodology caveats (e.g., broad JQL, created-after vs merged-after)
- **Qualitative claims** ("X is fixed", "Y is done") — find the primary source (chat message, ticket transition, MR merge) and cite it
- **Quotes and numbers from chat** — verify they are exact, not paraphrased in a way that changes meaning
- **Attribution** — verify the person who said something is correctly identified

Flag anything that:
- Cannot be verified → mark as "unverified" or remove
- Is directionally correct but imprecise → qualify with hedging
- Comes from a single source → note the single-source caveat
- Could be more positive or negative than evidence supports → rewrite to match evidence

### Phase 4: Report Generation

Produce a single document (`<project>-weekly-report-<date>.md`) with an exec-friendly body followed by technical appendices.

**Document Structure:**

**Main Body** (exec-readable, no jargon, no ticket numbers):
1. **The Short Version** — 2–3 sentences: where we were, where we are, what's at risk
2. **What We Can Do Now That We Couldn't Before** — capabilities delivered, plain language
3. **What's Not Working Yet** — honest, specific, with severity context
4. **What We Need** — decisions or support required from leadership
5. **By the Numbers** — table with metrics, each with a Notes column for caveats

**Appendices** (ordered by reader intent after the exec body):
- **Appendix A: Work Stream Detail** — per-initiative breakdown with inline links to tickets, MRs, chat threads, and docs (the narrative evidence behind the exec body)
- **Appendix B: Risks & Mitigations** — risk table with severity, status, and recommended actions
- **Appendix C: Jira Detail** — closed tickets table, in-progress tickets, open bugs by priority, initiative/epic status; every row links to the Jira ticket
- **Appendix D: Code Changes** — GitLab MR table with links, git commit summary, repo activity metrics
- **Appendix E: Chat & Meeting Intelligence** — key decisions, blockers, and quotes from chat spaces and Gemini meeting notes; each item links to the source space or doc
- **Appendix F: Sources & Confidence** — table rating each source (High/Medium/Low) with methodology notes

Writing rules for the main body:
- Zero ticket numbers, MR numbers, or commit hashes
- No jargon without explanation
- Every claim must be traceable to an appendix entry
- Quantitative claims must include methodology caveats where relevant
- Do not present self-reported numbers as automated measurements
- Do not round numbers in a direction that flatters the result
- Frame percentages in terms of what they mean
- Distinguish between "code is merged" and "feature works on a real site"

Writing rules for appendices:
- Every row must have an inline link to its primary source
- Tables preferred over prose for scannability
- Group by work stream or initiative, not by source type

### Phase 5: Internal Consistency Check

Before delivering, verify the document is internally consistent:

1. Every number in the main body must match the corresponding appendix data
2. Every claim in the body must have supporting evidence in an appendix
3. Initiative/epic counts in the body must match Appendix A
4. The By the Numbers table must match Appendix C and D totals
5. Fix any discrepancies before delivering

### Phase 6: Confidence Declaration

End every report with a confidence assessment:

| Claim Category | Confidence | Method |
|---------------|------------|--------|
| Ticket counts | High/Medium/Low | How queried, caveats |
| MR counts | High/Medium/Low | How queried, caveats |
| Feature status | High/Medium/Low | Single source vs corroborated |
| Bug status | High/Medium/Low | Tracker vs chat vs verified |
| Qualitative assessments | High/Medium/Low | Evidence basis |

## Rules
- This capability is advisory only. It reads and reports but does not modify source systems.
- Keep all reports deterministic and evidence-based.
- Do not claim orchestration, delegation, or runtime-control authority.
- Prefer concrete evidence over narrative interpretation.
- Use the sidecar descriptor as the canonical machine-readable contract for this capability.
- Relationship and org-graph metadata remain advisory for future orchestrators.

## Constraints
- Do not modify any source system (tickets, repos, chat). Read only.
- Do not assert a bug is "fixed" based on a single chat message without corroboration from the tracker or code.
- Do not inflate ticket counts by including unrelated teams' work without disclosure.
- Do not present created-after queries as merged-after without noting the caveat.
- Do not skip the internal consistency check between body and appendices.
- Do not use the word "impressive" or "amazing" in the main body. Let the numbers speak.

## Anti-Patterns to Avoid
- **Inflated counts:** counting shared platform or CI fixes as team-specific product work without disclosure
- **Precision theater:** presenting rough estimates as exact measurements
- **Single-source claims:** asserting something is "fixed" based only on one person's chat message
- **Jargon creep:** the exec summary must be readable by someone outside the team
- **Optimism bias:** if something failed in testing, say so
- **Alarm bias:** if something failed once in one test run, don't present it as a systematic failure rate
- **Frankenstein merge:** mashing all sources together without resolving conflicts

## Companion Capability Matrix

| If the report reveals this need | Route to | Handoff |
| --- | --- | --- |
| Body claims don't match appendix data | `converge` | the document, the specific inconsistencies |
| The main body needs quality hardening | `supercharge` | the draft body, audience, quality bar |
| The data collection spans multiple sessions or is interrupted | `analyze-context` | the canonical memory files, progress state |
| The report surfaces code quality or review concerns | `code-review` | the specific commits or MRs in question |


## Required Output
Every substantial response must include:
- a single report document with exec-friendly body and technical appendices (A through F)
- a confidence assessment in Appendix F rating each source (High/Medium/Low) with methodology notes
- an internal consistency check confirming body numbers match appendix data

## Examples

### Example Request
> Run a weekly intel report for the Composer team, last 7 business days. Check the Composer Acceleration and Composer v2 Launch Team chat spaces, the composer repo, Jira project LCP (exclude smart search), and any Composer leadership huddle Gemini notes. Audience is exec leadership.

### Example Output Shape
- single report: `reports/composer-weekly-report-2026-03-31.md`
  - Main body: The Short Version, What We Can Do Now, What's Not Working, What We Need, By the Numbers
  - Appendix A: Work Stream Detail (per-initiative breakdown with links)
  - Appendix B: Risks & Mitigations
  - Appendix C: Jira Detail (closed tickets, in-progress, bugs)
  - Appendix D: Code Changes (MR table, commit summary)
  - Appendix E: Chat & Meeting Intelligence (decisions, blockers, quotes with links)
  - Appendix F: Sources & Confidence

## Evaluation Rubric

| Check | What Passing Looks Like |
| --- | --- |
| Source coverage | All specified sources were queried; none were skipped without explanation |
| Fact-check rigor | Every quantitative claim was re-verified; caveats are explicit |
| Internal consistency | Numbers in the body match appendix data; every claim has appendix evidence |
| Audience calibration | Main body has zero jargon; appendices have full source links |
| Confidence transparency | Appendix F is honest about what was queried directly vs secondhand |
| Convergence quality | No conflicts between sources were hidden; discrepancies are surfaced |


Capability resource: `.gemini/skills/weekly-intel/resources/capability.json`
