---
name: "pulse"
display_name: "Pulse — Comms Triage"
kind: "skill"
capability_type: "skill"
description: "High signal-to-noise comms triage across Gmail and Google Chat. Read-only. Deterministic priority. Quick action recommendations."
---

# Pulse — Comms Triage

Quick-check your email and chat. See what matters. Ignore what doesn't.

## Purpose
Use this capability when you need a fast, high signal-to-noise view of outstanding emails and chat messages across Gmail and Google Chat. It cuts through inbox noise and surfaces what actually needs your attention, with deterministic priority classification and actionable next steps.

## Primary Objective
Classify incoming messages by urgency using deterministic rules (not vibes), present them in a scannable format with clickable links, and optionally step through actions one-by-one with explicit user approval. Learn from user feedback over time via a persistent memory system.

## Tool Boundaries

This skill is **100% read-only** during triage. It MUST NEVER send, reply, forward, delete, archive, or modify any message during triage.

Allowed gws commands (exhaustive list):
- `gws gmail +triage` — list inbox messages
- `gws gmail +read --id <ID>` — read a specific email body
- `gws gmail +read --id <ID> --headers` — read email with To/CC/From headers
- `gws gmail +reply --id <ID>` — reply to email (**only during `/act` with user approval**)
- `gws gmail +forward --id <ID>` — forward email (**only during `/act` with user approval**)
- `gws gmail users threads get` — read a full email thread
- `gws chat spaces list` — discover user's spaces
- `gws chat spaces messages list` — list recent chat messages
- `gws chat spaces messages get` — read a specific chat message
- `gws chat +send` — send chat message (**only during `/act` with user approval**)
- `gws chat users spaces getSpaceReadState` — get last-read timestamp for a space
- `gws auth status` — check auth health

Write commands (`+reply`, `+forward`, `+send`) are ONLY allowed during `/act` mode and ONLY after explicit user approval for each action. Pulse triage itself (the default) remains 100% read-only.

- forbidden: delegation decisions, orchestration, runtime execution control
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
- Configured chat spaces (auto-discovered on first run or manually configured)

## Required Output
Every pulse run must include:
- Timestamp header
- Priority-classified table with: #, Addr, From, Subject (clickable link), Age, Action
- Source summary footer (Gmail count, Chat spaces/msgs, memory signal count)
- Proposed action list for 🔴 and 🟡 items

---

## Invocation

| Command | What It Does | Default Behavior |
|---------|-------------|-----------------|
| `pulse /help` | Show quick reference | Commands, priority rules, examples |
| `pulse` | Triage both email + chat | 20 unread emails + unread chat msgs across configured spaces |
| `pulse /email` | Email only | 20 unread emails |
| `pulse /chat` | Chat only | Unread msgs across configured spaces |
| `pulse /hot` | High-priority only | Both sources, 🔴 and 🟡 only — skip 🔵 |
| `pulse /count` | Counts only, no table | Fastest check: just priority counts per source |
| `pulse /all` | Include read emails | Overrides default `is:unread` to `newer_than:24h` |
| `pulse /from <person>` | Filter by sender | Both sources, match on name or email |
| `pulse /space <name>` | Single chat space | Fuzzy-match against configured space names |
| `pulse /window <time>` | Override time window | `1h`, `6h`, `2d`, `1w` — applies to both sources |
| `pulse /deep` | Read top 5 bodies | Full message text for top 5 priority items |
| `pulse /deep <N>` | Read top N bodies | e.g., `pulse /deep 3` |
| `pulse /thread <N>` | Expand conversation | Show full thread for item #N from the pulse table |
| `pulse /act` | Step-through actions | Propose actions for 🔴+🟡 items, execute one-by-one with approval |
| `pulse /act <N>` | Act on specific item | Propose action for item #N only |
| `pulse /rate <±N...>` | Rate items | Boost (+) or demote (-) in one shot. e.g., `pulse /rate +3 +4 -1 -2` |
| `pulse /memory` | Show learned signals | Display current boost/demote rules |
| `pulse /memory clear` | Reset memory | Wipe all learned signals |

**Stacking:** all commands compose. `pulse /email /hot /window 2h` = urgent unread emails from last 2 hours.

---

## Help Output

When the user runs `pulse /help`, `pulse -h`, or `pulse --help`, respond with exactly this:

```
📡 Pulse — Comms Triage (read-only)

COMMANDS
  pulse                          What needs my attention right now?
  pulse /help                    This help text
  pulse /email                   Email only
  pulse /chat                    Chat only
  pulse /hot                     Urgent + needs-response only (skip 🔵)
  pulse /count                   Priority counts only (fastest)
  pulse /all                     Include already-read messages
  pulse /from <person>           Filter by sender/author
  pulse /space <name>            Single chat space (fuzzy match)
  pulse /window <time>           Override time window (1h, 6h, 2d, 1w)
  pulse /deep [N]                Read full body of top N items (default 5)
  pulse /thread <N>              Expand full conversation for item #N
  pulse /act                     Step through actions for 🔴+🟡 items
  pulse /act <N>                 Propose action for item #N only
  pulse /rate <±N...>             Rate items: +N boost, -N demote (e.g., pulse /rate +3 -1 -2)
  pulse /memory                  Show learned boost/demote rules
  pulse /memory clear            Reset all learned signals

STACKING
  All commands compose:
  pulse /email /hot /window 2h   Urgent unread emails, last 2 hours
  pulse /chat /from alice        Alice's chat messages
  pulse /deep 3 /hot             Read top 3 urgent items in full

PRIORITY
  🔴 Urgent         VIP senders, "action required", sole recipient, @mention + urgent
  🟡 Needs Response  @mentions, To:/CC:, questions, review requests, hot threads
  🔵 FYI            Everything else (count only unless ≤5)

MEMORY
  /rate teaches pulse what matters to you over time.
  Learns sender, subject pattern, source app, addressing, and space.
  Repeated signals get stronger (weight 1→2→3).
  Weight 3 demotes hide items entirely.
  Stored at ~/.kiro/scratch/pulse/memory.json

CONFIG
  Edit the skill SKILL.md to configure:
  • Chat spaces to monitor
  • VIP sender list
  • Default limits
```

---

## Configuration

### Chat Spaces

**Auto-discovery (first run or when no spaces configured):**

```bash
gws chat spaces list --params '{"pageSize": 50}' --format json
```

Present the user's spaces and ask which ones to monitor. Save the selection in this config block.

**Configured spaces (after discovery):**

```
SPACES:
- name: "Agent Studio TDMs"
  id: "spaces/AAAAaUiTeeQ"
- name: "AIPCA Code Reviews"
  id: "spaces/AAQADXO1mOo"
- name: "EGAI"
  id: "spaces/AAAA2fLPClU"
```

When the user says `pulse /space EGAI`, fuzzy-match against the `name` field.
When no `/space` flag is given, check all configured spaces.

### Chat Unread Detection

Pulse detects unread chat messages using the Space Read State API:

```bash
gws chat users spaces getSpaceReadState --params '{"name": "users/me/spaces/<SPACE_ID>/spaceReadState"}' --format json
```

This returns `lastReadTime`. Any message with `createTime` after `lastReadTime` is unread.

- Default behavior: show only unread chat messages
- `/all` flag: show all messages in the time window regardless of read state
- If the read state API fails, fall back to time-window filtering

### VIP Senders (User-Configurable)

Messages from VIPs always classify as 🔴 regardless of content.

```
VIPS:
- "manager@example.com"
```

Until configured, treat no one as VIP. Do not guess org charts.

### Defaults

| Setting | Value |
|---------|-------|
| Email max | 20 |
| Chat max per space | 10 |
| Chat filter | Unread (falls back to 24h window if read state unavailable) |
| Email query | `is:unread` |

---

## Workflow Contract

### Step 1: Auth Health Check

```bash
gws auth status
```

If auth is expired: print `⚠️ gws auth expired. Run: gws auth login` and stop.
If a specific source fails, continue with available sources and mark the failed source.

### Step 2: Gather Data

**Email (when email is in scope):**

Phase 1 — Get message list:
```bash
gws gmail +triage --max <MAX> --query '<QUERY>' --format json
```

Phase 2 — Fetch headers for To/CC classification:
```bash
gws gmail +read --id <MESSAGE_ID> --headers --format json
```

This returns `to`, `cc`, and `from` fields. Classify:
- **To: (sole)** → strong 🔴 signal
- **To: (multi)** → 🟡
- **CC:** → weaker, likely 🔵 unless content triggers higher
- **List/BCC** → 🔵

Display as Addr column: `→ To`, `→ To+N`, `→ CC`, `→ List`

**Chat (when chat is in scope):**

1. Get read state: `gws chat users spaces getSpaceReadState`
2. Fetch messages: `gws chat spaces messages list`
3. Filter unread (or all if `/all`)
4. Check `annotations` array for `USER_MENTION` entries

### Step 3: Classify Priority

Apply deterministically. Highest priority wins when multiple rules match.

| Priority | Emoji | Rules (any match triggers) |
|----------|-------|---------------------------|
| 🔴 Urgent | 🔴 | • From a configured VIP sender |
|          |       | • Contains: "urgent", "ASAP", "blocking", "blocked", "action required", "EOD", "critical" |
|          |       | • You are the sole To: recipient |
|          |       | • Chat @mention with urgent keywords |
| 🟡 Needs Response | 🟡 | • You are in To: or CC: (email) |
|          |       | • Chat @mention (even without urgent keywords) |
|          |       | • Contains a question directed at you |
|          |       | • Contains: "review", "approve", "feedback", "sign off", "PTAL" |
|          |       | • Thread has ≥ 3 replies in window (hot thread) |
| 🔵 FYI | 🔵 | • Everything else |

**Chat @mention detection:** Check `annotations` array for `USER_MENTION` with your user ID.
- @mention + urgent keyword → 🔴
- @mention alone → 🟡
- No @mention → classify by content only

After standard rules, apply memory adjustments from `~/.kiro/scratch/pulse/memory.json`.

### Step 4: Present Results

**Subject / Preview column = clickable hyperlink:**
- Gmail: `https://mail.google.com/mail/u/0/#inbox/<MESSAGE_ID>`
- Chat: `https://chat.google.com/room/<SPACE_ID>/<THREAD_NAME>`

**Presentation rules:**
- 🔴 and 🟡 always show full table
- 🔵 shows count if > 5 items; full table if ≤ 5
- If `/hot`, omit 🔵 entirely
- Append proposed action list for 🔴+🟡 items

### Step 5: Deep Read (when `/deep` is active)

Fetch full body for top N priority items via `gws gmail +read --id <ID>`.

### Step 6: Thread Expand (when `/thread <N>` is active)

Fetch full thread via `gws gmail users threads get` or chat thread messages.

### Memory System (`/rate` Learning)

**Storage:** `~/.kiro/scratch/pulse/memory.json`

**When the user rates items:**

1. For each rated item, extract all recognizable signals:

   | Signal Type | Extracted From |
   |-------------|---------------|
   | `sender` | From address / chat user ID |
   | `subject_pattern` | Generalized regex from subject |
   | `source_app` | Originating service (Jira, Gemini, GitLab, etc.) |
   | `addr` | How you were addressed (List, CC) |
   | `space` | Chat space ID |
   | `thread_pattern` | Thread topic keywords |

2. Pick the most useful combination based on item type:
   - Automated notifications → `source_app` + `subject_pattern`
   - Calendar noise → `subject_pattern` alone
   - Human messages → `sender`
   - Mailing list blasts → `addr: List` + `sender`
   - Chat space noise → `space` + `thread_pattern`

3. Present all proposed rules at once for confirmation.

**Weight system:**
- Weight 1: shift one tier
- Weight 2: always 🔵 (demote) or always 🟡+ (boost)
- Weight 3: hidden entirely (demote) or always 🔴 (boost)

### Step 7: Action Step-Through (when `/act` is active)

Phase 1 — Present numbered action list for all 🔴+🟡 items.
Phase 2 — For each: read full message → propose response → wait for approval (send/edit/skip/stop).
Phase 3 — Print summary of actions taken vs skipped.

**Safety:** NEVER auto-send. Every response requires explicit approval. NEVER fabricate information.

---

## What Pulse Does NOT Do

- Triage mode (default) is 100% read-only — it never sends, modifies, or deletes anything.
- `/act` mode can send replies/messages, but ONLY with explicit per-item user approval.
- It never auto-sends, auto-archives, or auto-deletes. Ever.
- It does not mark messages as read.
- It does not create tasks or calendar events (use other skills for that).
- It does not guess — if it can't fetch data, it says so explicitly.
- It does not infer org charts or VIPs — configure them or it won't assume.
- It does not fabricate response content — if it doesn't have enough context, it asks you.

## Taking Action After Pulse

After reviewing pulse output, the user may want to act. Pulse surfaces the ID and suggests the command but **never auto-executes**:

- "Reply to #1" → `gws gmail +reply --id <ID>` (confirm first)
- "Forward #3 to team" → `gws gmail +forward --id <ID> --to <email>` (confirm first)
- "Reply in chat" → `gws chat +send --space <SPACE> --text '...'` (confirm first)

Always present the command with the real ID from the table. Always wait for explicit approval.

## Examples

### Example: Default triage
```
pulse
```
Returns 20 unread emails + unread chat messages, classified into 🔴/🟡/🔵.

### Example: Hot items only
```
pulse /hot
```
Returns only 🔴 and 🟡 items, skipping 🔵 FYI noise.

### Example: Rate items
```
pulse /rate +3 +4 -1 -2
```
Boosts items 3 and 4, demotes items 1 and 2. Extracts generalizable patterns and saves to memory.

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
