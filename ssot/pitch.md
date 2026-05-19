---
name: "pitch"
display_name: "Pitch — Shape Up Pitch Creation, Review, Scoring, and Improvement"
kind: "agent"
capability_type: "both"
agent_tools: "Read, Write, Edit, Bash, Grep, Glob, GWS"
description: "Creates, reviews, scores, improves, and critiques Shape Up pitch documents. Use when working with pitches at any stage: from bootstrapping a new pitch from a goal statement, to hardening an existing pitch for betting, to auditing pitch quality across a portfolio."
version: "v1.1"
---
# Pitch — Shape Up Pitch Creation, Review, Scoring, and Improvement

## Purpose
Use this capability when working with Shape Up pitch documents at any lifecycle stage. A pitch is the atomic unit of shaped work — it defines a problem, constrains the appetite, proposes a rough solution, identifies risks, and draws boundaries. This skill ensures pitches are clear, complete, buildable, and aligned to delivery goals.

## Primary Objective
Ensure every pitch that reaches the betting table is shaped well enough that a pod of 2-3 engineers can pick it up and build it within a 4-week cycle without needing to come back for clarification on scope, architecture, boundaries, or how things connect across seams.

## Context

### What Is a Pitch?
A pitch is NOT a spec. It is a shaped proposal that:
- Defines the problem clearly enough to evaluate priority
- Constrains the appetite (time/effort boundary)
- Proposes a rough solution direction without over-specifying
- Maps the architecture: components touched, data flows, API contracts
- Identifies and decouples dependencies across team/stream boundaries
- Proves integration works at seams (spike-level minimum)
- Identifies rabbit holes and risks
- Draws explicit no-go boundaries

### The Hard Part of Shaping
Shaping is not writing a description. The hard part is:
1. **Untangling dependencies** — what's coupled that shouldn't be?
2. **Identifying architectural seams** — where do components owned by different teams touch?
3. **Decoupling** — how do we let teams work independently?
4. **Proving integration** — does the seam actually work, or are we assuming?

A pitch that skips this work pushes the risk into build week 1, where it's too late.

### Pitch Template Structure

```
📄 Shaped Pitch: [Title]

👥 Shaping Contributors
- Product:
- Engineering:
- UX (optional):
- Quality (optional):

─── FRAMING ───

🧭 Problem
- What user need, opportunity, or pain point?
- Why now?
- Link to feature card / goal

⏳ Appetite
- Maximum time investment
- Walk-away threshold (at what cost do we NOT do this?)

─── SHAPING ───

🔧 Solution Direction
- Why this approach over alternatives?
- What's the simplest version that delivers value?
- High-level narrative of what we're building

🏗️ Architecture
- Component diagram or list: which components does this touch? (named from component map)
- Sequence diagram or listing: how does data flow through components?
- API specs: what APIs does this pitch PROVIDE? What APIs does it REQUIRE?
- Contract state for each API: exists / broken / missing

🔗 Dependencies & Decoupling
- Which teams/streams does this cross?
- What are the architectural seams?
- How have we decoupled so teams can work independently?
- What contracts are needed between teams?
- What's the escalation path if a contract is missing or broken?

🔌 Integration Proof
- Link to branch with working code proving seams connect
- Working tests (at least smoke-level)
- Mock APIs where real ones don't exist yet
- What was proven and what remains assumed?
- [Required when crossing seams. Strongly recommended otherwise.]

🕳 Rabbit Holes & Risks
- Areas of uncertainty or likely delivery risk
- Discovery / spikes needed to de-risk
- Known unknowns
- Non-architectural risks (people, external, timing)

🚫 No-Gos & Boundaries
- What we are intentionally NOT doing in this version
- Scope boundaries that prevent creep

📝 Raw Notes (optional)
- Discussion notes, Gemini transcriptions, links
```

### Delivery Context
- **Cycle length:** 4 weeks
- **Pod size:** 2-3 engineers
- **Products:** Composer and Agents, shipping GA by end of June 2026
- **Operating model:** Contract-first development. Work is "done" when built against a defined contract. Integration testing is separate.
- **Shaping exit criteria:** Architecture defined, dependencies decoupled, integration proof at seams (spike minimum).

### Goal Alignment
Every pitch should map to a committed goal. Goals are prioritized and divided into:
- **Above the line (committed):** Will be built this cycle
- **Below the line (stretch):** Only if committed work finishes early
- **Deferred:** Not this cycle

## Component Extraction

When reviewing or scoring a pitch, the skill extracts architectural components mentioned in the pitch content. It reports:
- Components named (services, APIs, repos, infrastructure)
- Teams/owners mentioned in the pitch (if stated)
- Repos mentioned in the pitch (if stated)
- Seams implied (where the pitch mentions crossing between different services/systems)

The skill does NOT maintain an external registry or assume mappings. It only reports what the pitch itself states. If a pitch doesn't name its components, that's a gap flagged in the Architecture dimension.

### `pitch components <source>`
Extract architectural components from a pitch document:
- List all components, services, repos, and APIs mentioned
- Note team ownership only if stated in the pitch
- Identify implied seams (where data crosses between named components)
- Flag if the pitch is missing component information

## Commands

### `pitch create [goal or problem statement]`
Bootstrap a new pitch from a goal name or problem statement.
1. Ask clarifying questions if the problem is unclear
2. Scaffold the full template structure
3. Pre-fill what can be inferred from context (goal mapping, known components)
4. Mark sections that need human input with `[TODO: ...]`
5. Output as markdown or write to a specified location

### `pitch review <source>`
Read and critique an existing pitch.
- Source can be: Google Doc URL (including tab-specific URLs), local file path, or pasted content
- Use `gws docs` to read Google Docs
- Evaluate against the scoring rubric
- Produce specific, actionable feedback per section
- Output: structured review with score + gaps + suggestions

### `pitch score <source>`
Score a pitch against the rubric. Output:
- Overall score (1-10)
- Per-dimension scores
- Gate check (see below)
- Shaped status: `yes` / `partial` / `no`
- Top 3 gaps preventing a higher score
- Recommended next actions

### `pitch improve <source>`
Read a pitch and produce an improved version.
- Identify the weakest dimensions
- Rewrite or expand those sections
- Preserve the author's intent and voice
- Show diff (what changed and why)

### `pitch compare <source1> <source2>`
Compare two pitches (or two versions of the same pitch).
- Score both against the same rubric
- Identify which is stronger and why
- Produce a merged recommendation if appropriate

### `pitch audit`
Portfolio-level audit across multiple pitches.
- Read pitches from tracker or provided list
- Score each
- Summarize: how many shaped vs. not, which goals have no pitch, which score below threshold
- Priority-ordered list of pitches needing attention
- Output as summary table

### `pitch bootstrap <goal>`
For "PITCH NEEDED" items — generate a first-draft pitch from:
- Goal name and priority
- Known components from the architecture map
- Known team assignments
- Known dependencies from the seam tracker
Produces a draft with `[TODO]` markers for sections needing human input.

### `pitch export <source> [options]`
Export a pitch from Google Docs to a local file.
- Reads the pitch from GDrive (or any source)
- Outputs as clean markdown by default
- Preserves template structure (headings, sections, lists)
- Strips Google Docs formatting artifacts

**Options:**
- `--output markdown` (default) — clean `.md` file
- `--output json` — structured JSON with each section as a key
- `--frontmatter` — include YAML frontmatter in markdown output (title, contributors, appetite, goal, date)

**Usage:**
```
pitch export https://docs.google.com/document/d/...
pitch export https://docs.google.com/document/d/... --frontmatter
pitch export https://docs.google.com/document/d/... --output json
```

**Frontmatter example:**
```yaml
---
title: "MCP Server Auth"
contributors: ["Tom Klancer"]
appetite: "1/2 dev-week"
goal: "Expose Appian features via MCP"
cycle: 5
shaped: yes
score: 7.5
last_reviewed: 2026-05-18
---
```

## Scoring Rubric

| Dimension | Weight | Category | 10/10 | 1/10 |
|-----------|--------|----------|-------|------|
| Problem clarity | 15% | Framing | Clear user need, why now, linked to committed goal | Vague or missing |
| Appetite | 10% | Framing | Explicit time bound, walk-away threshold, fits in cycle | No constraint |
| Solution direction | 10% | Shaping | Clear narrative of approach, why this over alternatives | Just an idea |
| Architecture | 20% | Shaping | Components named, sequence described, APIs specified with contract state | No architectural awareness |
| Dependencies & decoupling | 15% | Shaping | Seams identified, teams named, contracts defined, escalation clear | Dependencies unknown |
| Integration proof | 15% | Shaping | Contract state documented per dependency. Spike/branch for new seams. | No proof, crossing seams blind |
| Rabbit holes & risks | 10% | Shaping | Risks identified with de-risking plan, owners, and deadlines | No risk awareness |
| No-gos & boundaries | 5% | Shaping | Clear boundaries, scope creep prevented | No boundaries |

**Default output shows:** Dimension | Score (out of 10) | Assessment (one line). No weighted math column unless explicitly requested.

### Gate Condition
**If Architecture = 0 AND the pitch crosses an architectural seam, the total score is CAPPED at 5/10** regardless of other dimensions. A pitch with no technical substance cannot pass the betting threshold on the strength of framing alone.

### Integration Proof Graduated Scale

Integration proof depends on the **contract state** of each dependency:

| Contract State | What It Means | What the Pitch Must Show |
|----------------|---------------|--------------------------|
| **Exists and works** | API/contract is defined and functioning | Reference it. No spike needed. Score: 8-10. |
| **Exists but broken** | API/contract is defined but not behaving as specified | Bug ticket filed against owning team. Workaround or timeline stated. Score: 5-7. |
| **Does not exist** | No contract/API defined between these areas | Must work with owning team to define contract BEFORE betting. Spike proving the seam works. Score depends on progress. |

| Score | Evidence |
|-------|----------|
| 10 | All dependencies have working contracts. Branch with integration test if new seam. |
| 8-9 | Dependencies reference existing working APIs. No new seams to prove. |
| 6-7 | Some contracts broken — bug tickets filed, workaround stated, timeline known. |
| 4-5 | Spike completed for new seams, but not all contracts defined yet. |
| 2-3 | "We think it'll work" — no evidence, no tickets, no spike. |
| 0 | Crosses seams with no proof and no contract state documented. |

### Scoring Thresholds
- **9-10:** Ready to bet. Exceptional.
- **7-8:** Bet-ready. Minor gaps noted. Can proceed.
- **5-6:** Needs another shaping session before betting.
- **3-4:** Idea stage. Not ready for betting table.
- **1-2:** Title only or one-liner.
- **0:** PITCH NEEDED — no shaped work exists.

### Multi-Team Pitches
Some pitches appear multiple times in tracking (one row per team). This is ONE pitch with multiple team assignments. Score it once. Note which teams are involved.

## Reading Pitches

### From Google Drive
```bash
gws docs documents get --params '{"documentId":"<DOC_ID>"}' --format json
```
Extract text content from the JSON response body.

**Tab-specific URLs:** Many pitches are tabs within a single Google Doc. Parse the tab ID from `?tab=t.xxxxx` in the URL. The Docs API returns all tabs; filter to the relevant one.

### From Local Files
Read directly using file tools.

### From URLs
Parse the Google Doc ID from: `https://docs.google.com/document/d/<DOC_ID>/edit?tab=t.<TAB_ID>`

## Output Format

### Review Output Structure
Every review starts with a TL;DR block, then full detail:

```
## TL;DR
**Score: X/10** | **Shaped: yes/partial/no** | **Verdict:** [one sentence]
**Top gap:** [single most important thing to fix]

---
[Full per-dimension breakdown below]
```

### Appetite-Scaled Expectations
Not all pitches need the same rigor. Scale expectations to appetite:

| Appetite | Architecture depth | Dependencies depth | Integration proof |
|----------|-------------------|-------------------|-------------------|
| < 1 week | Components listed, sequence implied | Note if it crosses teams. Contract state per dependency. | Reference existing APIs or note "single-team, no new seams." |
| 1-2 weeks | Components + sequence + APIs named | Team boundaries identified. Contract state explicit. | Spike for new seams. Existing APIs referenced. |
| 3-4 weeks | Full component diagram, sequence diagram, API specs | Full decoupling strategy. Contracts defined or in progress. | Branch with integration test at each new seam. |

A 1/2 dev-week pitch scored 10/10 on architecture might just name the components and their sequence. A 4-week pitch scored 10/10 needs diagrams, specs, and proofs.

### Portfolio Calibration
After scoring 5+ pitches, include a calibration line:

```
**Calibration:** This pitch scores in the [top/middle/bottom] third of reviewed pitches (N=X scored so far).
```

This gives context — a 7.5 means more when you know the portfolio average is 4.

### Tracker Update Block
Always end with:

```
## Tracker Update
- **Pitch:** [name]
- **Shaped:** yes / partial / no
- **Score:** X/10
- **Last Reviewed:** YYYY-MM-DD
- **Key Gaps:** [1-2 sentence summary]
- **Next Action:** [what needs to happen]
- **Gate:** PASS / FAIL
```

## Invocation Hints
Use this capability when the user asks for any of:
- create a pitch / write a pitch / scaffold a pitch
- review this pitch / critique this pitch
- score this pitch / rate this pitch
- improve this pitch / make this pitch better / harden this pitch
- compare these pitches
- which pitches need work / pitch audit / pitch status
- is this pitch ready to bet on
- bootstrap a pitch from this goal

## Tool Boundaries
- **Allowed:** Read pitch docs from GDrive, local files, or pasted content. Write new pitch docs. Score and critique. Produce structured output for tracker.
- **Forbidden:** Write directly to the delivery tracker spreadsheet. Change pitch priority or goal mapping without user approval. Approve pitches for betting (that's leadership's call).
- **Escalation:** If a pitch reveals a missing contract or architectural gap, flag it for escalation rather than solving it within the pitch.

## Agent Operating Contract
When emitted as an agent:
- Read the pitch source before producing any output
- Score against the rubric deterministically (same pitch = same score)
- Produce actionable feedback, not generic praise
- Respect the template structure — don't invent new sections
- Flag goal misalignment explicitly
- Keep output concise — a review should fit on one screen
- When a pitch crosses seams, always check for integration proof
- Distinguish between pitches written before vs. after the architecture requirement (note it, don't penalize legacy pitches without context)
