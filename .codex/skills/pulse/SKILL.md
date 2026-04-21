---
name: "pulse"
description: "High signal-to-noise comms triage across Gmail and Google Chat. Deterministic priority. Triage is read-only; sweep/act/archive/delete require explicit approval."
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
- `gws gmail users messages modify` — archive email (**only during `/sweep` with user approval**)
- `gws gmail users messages trash` — delete email (**only during `/sweep` with user approval**)
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

**Exception — `/hot` mode** overrides the above: uses simplified columns (`# | Pri | Space / Source | Subject | Age | Action`), omits the source summary footer and all plumbing lines, and prepends an executive summary. See Step 4 for full /hot rules.

---

## Invocation

| Command | What It Does | Default Behavior |
|---------|-------------|-----------------|
| `pulse /help` | Show quick reference | Commands, priority rules, examples |
| `pulse` | Triage both email + chat | 20 unread emails + unread chat msgs across configured spaces |
| `pulse /email` | Email only | 20 unread emails |
| `pulse /chat` | Chat only | Unread msgs across configured spaces |
| `pulse /hot` | High-priority only | 🔴+🟡 only, max 5 items, recency-filtered (12h 🔴 / 24h 🟡), executive summary first |
| `pulse /count` | Counts only, no table | Fastest check: just priority counts per source |
| `pulse /all` | Include read emails | Overrides default `is:unread` to `newer_than:24h` |
| `pulse /from <person>` | Filter by sender | Both sources, match on name or email |
| `pulse /space <name>` | Single chat space | Fuzzy-match against configured space names |
| `pulse /window <time>` | Override time window | `1h`, `6h`, `2d`, `1w` — applies to both sources |
| `pulse /deep` | Read top 5 bodies | Full message text for top 5 priority items |
| `pulse /deep <N>` | Read top N bodies | e.g., `pulse /deep 3` |
| `pulse /thread <N>` | Expand conversation | Show full thread for item #N from the pulse table |
| `pulse /open <N...>` | Open in browser | Open items by number in Gmail/Chat. e.g., `pulse /open 1 3 5` |
| `pulse /delete <N...>` | Quick delete | Trash email items by number. e.g., `pulse /delete 4 6` |
| `pulse /archive <N...>` | Quick archive | Archive email items by number. e.g., `pulse /archive 2 3` |
| `pulse /act` | Step-through actions | Propose actions for 🔴+🟡 items, execute one-by-one with approval |
| `pulse /act <N>` | Act on specific item | Propose action for item #N only |
| `pulse /rate <±N...>` | Rate items | Boost (+) or demote (-) in one shot. e.g., `pulse /rate +3 +4 -1 -2` |
| `pulse /memory` | Show learned signals | Display current boost/demote rules |
| `pulse /memory clear` | Reset memory | Wipe all learned signals |
| `pulse /tune` | Calibration session | Walk through 20 messages, rate each, build memory |
| `pulse /tune <N>` | Shorter session | Walk through N messages. e.g., `pulse /tune 10` |
| `pulse /config` | Configure pulse | Guided setup for spaces, VIPs, direct reports, defaults |
| `pulse /mute <N...>` | Mute items | Hide items from future pulse runs this session. e.g., `pulse /mute 1 4` |
| `pulse /mute <N> <duration>` | Mute with expiry | e.g., `pulse /mute 1 4h`, `pulse /mute 3 2d` |
| `pulse /muted` | Show muted items | List currently muted items with expiry times |
| `pulse /unmute <N...>` | Unmute items | Restore muted items. e.g., `pulse /unmute 1 4` |
| `pulse /unmute all` | Clear all mutes | Remove all mutes |
| `pulse /sweep` | Inbox cleanup | Propose emails to archive or delete based on memory + patterns |
| `pulse /sweep <filter>` | Filtered cleanup | Pre-filter scan. e.g., `pulse /sweep gitlab`, `pulse /sweep older than 2d` |

**Stacking:** all commands compose. `pulse /email /hot /window 2h` = urgent unread emails from last 2 hours.

---

## Help Output

When the user runs `pulse /help`, `pulse -h`, or `pulse --help`, respond with exactly this:

```
📡 Pulse — Comms Triage (triage is read-only; actions require approval)

COMMANDS
  pulse                          What needs my attention right now?
  pulse /help                    This help text
  pulse /email                   Email only
  pulse /chat                    Chat only
  pulse /hot                     Top 5 urgent items, recency-filtered, exec summary first
  pulse /count                   Priority counts only (fastest)
  pulse /all                     Include already-read messages
  pulse /from <person>           Filter by sender/author
  pulse /space <name>            Single chat space (fuzzy match)
  pulse /window <time>           Override time window (1h, 6h, 2d, 1w)
  pulse /deep [N]                Read full body of top N items (default 5)
  pulse /thread <N>              Expand full conversation for item #N
  pulse /open <N...>             Open items in browser (e.g., pulse /open 1 3 5)
  pulse /delete <N...>           Quick delete items (e.g., pulse /delete 4 6)
  pulse /archive <N...>          Quick archive items (e.g., pulse /archive 2 3)
  pulse /act                     Step through actions for 🔴+🟡 items
  pulse /act <N>                 Propose action for item #N only
  pulse /rate <±N...>             Rate items: +N boost, -N demote (e.g., pulse /rate +3 -1 -2)
  pulse /memory                  Show learned boost/demote rules
  pulse /memory clear            Reset all learned signals
  pulse /tune [N]                Calibration session — walk through N messages (default 20)
  pulse /config                  Guided setup for spaces, VIPs, direct reports, defaults
  pulse /sweep                   Propose emails to archive/delete based on memory + patterns
  pulse /mute <N...>             Mute items this session (e.g., pulse /mute 1 4)
  pulse /mute <N> <duration>     Mute with expiry (e.g., pulse /mute 1 4h)
  pulse /muted                   Show currently muted items
  pulse /unmute <N...>           Restore muted items
  pulse /unmute all              Clear all mutes

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
  All config in ~/.kiro/scratch/pulse/config.json
  Memory in ~/.kiro/scratch/pulse/memory.json
  Mutes in ~/.kiro/scratch/pulse/mutes.json
  Run `pulse /config` to set up interactively
```

---

## Configuration

All user-specific config lives in `~/.kiro/scratch/pulse/config.json` — not in this skill file. The skill reads this file on every run. Memory lives alongside it at `~/.kiro/scratch/pulse/memory.json`.

**Schema:**
```json
{
  "version": 1,
  "spaces": [
    {"name": "Space Name", "id": "spaces/XXXX"}
  ],
  "vips": ["vip@example.com"],
  "direct_reports": ["report@example.com"],
  "defaults": {
    "email_max": 20,
    "chat_max_per_space": 10,
    "email_query": "is:unread"
  }
}
```

**If config.json is missing on first run:** auto-discover spaces via `gws chat spaces list` and prompt the user to select. Create `config.json` with the result.

**`pulse /config` reads and writes this file.** The skill itself never changes.

### Chat Spaces

Read `spaces` array from `config.json`. When the user says `pulse /space EGAI`, fuzzy-match against the `name` field. When no `/space` flag is given, check all configured spaces.

### Sender Name Resolution

The Chat API returns `sender.name` as `users/123456` with no display name. Pulse maintains a `user_cache` in `config.json` mapping user IDs to names.

**How the cache is populated:**
- From `argumentText` in @mention annotations (e.g., `@Alice Smith` → `users/100001...` = "Alice Smith")
- From email headers when a chat notification arrives via Gmail
- Manually via `pulse /config`

**When a sender ID is not in the cache:** fall back to the space name as attribution (e.g., "someone in EGAI") — never display "unknown" and never guess or fabricate a name.

**Cache schema in config.json:**
```json
"user_cache": {
  "users/100001234567890123456": "Alice Smith",
  "users/100009876543210987654": "Bob Chen"
}
```

### Chat Unread Detection

Pulse uses time-window filtering as the default proxy for "unread" chat messages. The `getSpaceReadState` API requires the `chat.users.readstate` OAuth scope — if available, pulse will use it for precise unread detection. Otherwise, it falls back to the time window.

**Default behavior:** show chat messages from the last `chat_window` (default: `2h` in config.json). This assumes recent messages are likely unread.

- `/window <time>` overrides the chat window (e.g., `pulse /window 8h` after being away overnight)
- `/all` shows all messages regardless of time
- If `chat.users.readstate` scope is available, pulse uses `getSpaceReadState` for precise filtering instead of the time window

### VIP Senders

Read `vips` array from `config.json`. Messages from VIPs always classify as 🔴 regardless of content. Until configured, treat no one as VIP.

### Direct Reports

Read `direct_reports` array from `config.json`. OOO notices and status updates from direct reports classify as 🟡 (team capacity awareness). Same messages from non-reports classify as 🔵. Until configured, treat all OOO/status messages equally (🔵).

### Defaults

Read `defaults` object from `config.json`. Overridable per-run via `/window`, `/all`, etc.

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
| 🔵 Calendar (max) | 🔵 | • Subject starts with "Updated invitation:", "Invitation:", "Accepted:", "Declined:", "Tentative:" |
|          |       | • From: `calendar-notification@google.com`, `calendar-server.bounces.google.com` |
|          |       | • **Always 🔵 regardless of other rules. Never promoted above 🔵. Excluded from `/hot`.** |

**Chat @mention detection:** Check `annotations` array for `USER_MENTION` with your user ID.
- @mention + urgent keyword → 🔴
- @mention alone → 🟡
- No @mention → classify by content only

After standard rules, apply memory adjustments from `~/.kiro/scratch/pulse/memory.json`.

**Resolution detection (chat threads):** Before finalizing priority, scan chat thread messages for resolution language: "fix merged", "PR submitted", "tested", "deployed", "resolved", "shipped", "LGTM", "merged to main", "all clear", "fixed". If the most recent messages contain resolution language, downgrade the thread to 🔵 regardless of earlier urgency. Resolved threads are noise — the fire is out.

**Executive relevance filter (applies to `/hot` only):** After classification and before presentation, apply a final filter that asks: "Does this require action or a decision from ME specifically, or is it team activity I'm being informed about?"

Downgrade to 🔵 (excluded from `/hot`) if ALL of these are true:
- You are NOT @mentioned or directly addressed
- You are NOT in To: or CC: (email)
- The conversation is between other team members (no question directed at you)
- The thread is operational coordination (build details, commit hashes, PR reviews between ICs, ticket triage between QE and devs)

Keep as 🔴/🟡 (stays in `/hot`) if ANY of these are true:
- You are @mentioned or directly addressed
- A VIP is asking a question (even if not directly to you — you may need to act)
- The topic is a decision that needs your input (architecture proposals, process changes, escalation responses)
- The topic is a blocker or risk to something you own (e.g., keynote demo, team capacity)
- It's from a direct report and signals a problem (not routine status)

**Stale event reframing:** When a chat thread contains a time-specific event that has already passed (e.g., "huddle at 9:50" and it's now 11:30), the executive summary bullet should focus on the underlying issue, not the expired event. Reframe: instead of "pulling leaders for 9:50 huddle" → "demo site broken since yesterday — investigation needed". The table row can reference the huddle, but the bullet should describe the live problem.

**Jira notification relevance:** Jira ticket notifications are informational by default (🔵) unless:
- The ticket is tagged as blocking a key event or a customer escalation you own
- You are assigned, mentioned, or watching the ticket
- A direct report filed it and flagged it as a blocker

For `/hot`, collapse Jira notifications into a single awareness line in the stale footer rather than a table row, unless the above exceptions apply. Format: `📋 N new Jira tickets today (PROJ-1234, PROJ-5678, ...) — run pulse for details`

**Mute filtering:** After classification, load `~/.kiro/scratch/pulse/mutes.json`. Remove expired mutes. For each remaining mute, suppress matching items:
- Email: match by message ID
- Chat: match by message `name` OR by `thread_id` (thread muting catches new replies)

Muted items are excluded from the table entirely. Add a footer note: `🔇 N muted items hidden (pulse /muted to review)`

**Chat-while-away email suppression:** When both email and chat are in scope (default `pulse`, `pulse /hot`), automatically hide any email from `chat-noreply@google.com`. The chat space scan already covers these messages — showing them as email is pure duplication. Count suppressed items in the footer: `📧 N chat-notification emails suppressed (already in chat scan)`. This does NOT apply when running `pulse /email` alone (no chat scan to cover them).

**Self-message hiding:** Never show items where the sender is you (matching your email or chat user ID), UNLESS:
- Someone replied after your message in the same thread (new activity you haven't seen)
- The item is a thread where the latest message is from someone else

Your own messages with no subsequent replies are noise — you know what you said.

**Thread collapsing:** Group emails sharing the same thread subject or thread ID into a single row with a count badge. Display as: `Project Status Update (×3)` instead of 3 separate rows. For the collapsed row:
- Use the most recent message's date for the Age column
- Use the most recent sender for the From column
- Priority = highest priority among grouped messages
- The item number refers to the group; actions (`/archive`, `/delete`, `/mute`) apply to ALL messages in the group

Similarly for chat: if multiple messages are in the same thread, collapse to one row showing the thread topic + count.

### Step 4: Present Results

**Subject / Preview column = clickable hyperlink:**
- Gmail: `https://mail.google.com/mail/u/0/#inbox/<MESSAGE_ID>`
- Chat: `https://chat.google.com/room/<SPACE_ID>/<THREAD_NAME>`

**Presentation rules:**
- 🔴, 🟡, and 🔵 always show full numbered table (numbers are continuous across all tiers)
- If `/hot`:
  - **Executive summary first:** Before the table, output 3-5 bullet points summarizing the key actionable items. Format: `[🔴|🟡] [person/topic]: [what needs your attention] — [recommended action]`. No age in bullets — age lives in the table only. This is the primary output — the table is the detail view.
  - **Empty state:** If zero items pass all filters, output: `✅ Nothing hot — inbox is clean. Run full pulse to check lower-priority items.`
  - **Max-age filter:** Only show 🔴 items ≤ 12h old and 🟡 items ≤ 24h old. Older items drop to a stale footer: `⏰ N stale items (>12h/24h) — run full pulse to see`
  - **Cap at 5 items.** If more than 5 items pass the age filter, show top 5 sorted by priority then recency. Footer: `📋 N more items in full pulse`
  - **Simplified table columns:** Use `| # | Pri | Space / Source | Subject | Age | Action |`. Chat items show the space name (e.g., "EGAI"). Email items show the sender category (e.g., "Jira", "Announcement", "Alice Smith"). No separate Src and From columns.
  - **No plumbing lines.** Omit all meta/stats lines: no "N emails auto-filtered", no "N chat-notification emails suppressed", no memory/signal counts, no source summary footer, no mute count footer. The only footer lines allowed are: stale count, overflow count, and Jira awareness line (if Jira tickets were downgraded).
  - **Calendar exclusion:** Items classified as 🔵 Calendar (invites, updates, accepts, declines) are always excluded from `/hot` output.
  - **Resolution exclusion:** Chat threads containing resolution language ("fix merged", "PR submitted", "tested", "deployed", "resolved", "shipped", "LGTM", "merged to main") are downgraded to 🔵 and excluded from `/hot`.
  - Omit 🔵 entirely
  - **No separate action list.** The Action column in the table is sufficient for /hot. Do not append the detailed proposed action list — it's redundant at this item count.
- If `/count`, show counts only (no table)
- Append proposed action list for 🔴+🟡 items

### Step 4b: Open in Browser (when `/open` is active)

Look up the item numbers from the most recent pulse/sweep table and open their URLs:

- Gmail: `open "https://mail.google.com/mail/u/0/#inbox/<MESSAGE_ID>"`
- Chat: `open "https://chat.google.com/room/<SPACE_ID>/<THREAD_NAME>"`

Multiple items open in separate tabs: `pulse /open 1 3 5` opens three tabs.

### Step 4c: Quick Delete / Archive (when `/delete` or `/archive` is active)

Immediately act on email items by number from the most recent table. No sweep workflow needed.

- `pulse /delete 4 6` → trash those emails, confirm after: `✅ Deleted 2 items`
- `pulse /archive 2 3` → remove from inbox, confirm after: `✅ Archived 2 items`

**Safety:**
- Only works on email items (chat messages can't be deleted/archived via API)
- Single item: execute immediately
- Multiple items: list what will be affected, then execute on `y`
- Learns from the action (saves to memory like sweep does)

Works after any command that produces a numbered table (`pulse`, `pulse /hot`, `pulse /sweep`, etc.).

### Step 4d: Mute / Unmute (when `/mute`, `/muted`, or `/unmute` is active)

Muting hides items from future pulse runs without modifying the underlying message. Works on both email and chat items.

**Storage:** `~/.kiro/scratch/pulse/mutes.json`

**Schema:**
```json
{
  "version": 1,
  "muted": [
    {
      "id": "19d9ce456700b006",
      "type": "email",
      "from": "admin@demo-site.example.com",
      "subject": "Error in Task: Update dates",
      "muted_at": "2026-04-17T16:30:00Z",
      "expires_at": "2026-04-17T20:30:00Z",
      "reason": "user muted #1"
    },
    {
      "id": "spaces/XXXX1234/messages/abc123.def456",
      "type": "chat",
      "thread_id": "spaces/XXXX1234/threads/abc123",
      "from": "Alice Smith",
      "preview": "@Bob Chen - are we good on the VPN thing...",
      "muted_at": "2026-04-17T16:30:00Z",
      "expires_at": null,
      "reason": "user muted #2"
    }
  ]
}
```

**`/mute <N...>` behavior:**

1. Look up item numbers from the most recent pulse table.
2. For each item, record its unique ID:
   - Email: Gmail message ID
   - Chat: message `name` (e.g., `spaces/XXX/messages/YYY.ZZZ`) AND `thread_id`
3. Default expiry: **end of calendar day** (midnight local time). Override with duration: `pulse /mute 1 4h` = 4 hours from now.
4. Save to `mutes.json`.
5. Confirm: `🔇 Muted 2 items (expires: end of day)`

**Duration parsing:**
- `1h`, `2h`, `4h` — hours
- `1d`, `2d` — days
- `eod` — end of current calendar day (default)
- `forever` — no expiry (until manually unmuted)

**Chat thread muting:** When a chat message is muted, the entire thread is muted (by `thread_id`). New messages in the same thread stay hidden. This prevents the same conversation from resurfacing with each new reply.

**`/muted` behavior:**

Show all currently active mutes:
```
🔇 Muted Items (3 active)

| # | Type | From | Preview | Muted | Expires |
|---|------|------|---------|-------|---------|
| 1 | 💬   | You  | @Bob Chen - VPN thing... | 16:30 | end of day |
| 2 | 💬   | Alice | Quick Update: ...noon milestone | 16:30 | end of day |
| 3 | 📧   | Carol Davis | messaged you on Chat... | 16:31 | 20:31 |

Unmute: `pulse /unmute 1 3` or `pulse /unmute all`
```

**`/unmute <N...>` behavior:**

1. Look up item numbers from the `/muted` table (not the pulse table).
2. Remove matching entries from `mutes.json`.
3. Confirm: `🔊 Unmuted 2 items — will appear in next pulse`

**`/unmute all` behavior:**

Clear all mutes. Confirm: `🔊 All mutes cleared`

**Expiry cleanup:** On every pulse run, remove expired mutes from `mutes.json` before filtering.

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
   | `not_mentioned` | Conditional: only match when you're NOT @mentioned |
   | `no_direct_question` | Conditional: only match when no question is directed at you |
   | `classification_override` | Force a tier ("fyi", "needs_response", "urgent") instead of shifting |

   Conditional matches enable nuanced rules like: "this space is 🔵 unless I'm @mentioned" — same space can be 🟡 when tagged and 🔵 when not.

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

### Step 8: Tune Session (when `/tune` is active)

`/tune` walks through a diverse sample of messages to teach pulse your preferences.

**Phase 1 — Gather a diverse sample:**

Fetch messages from all sources, aiming for variety:
- 50% email, 50% chat (adjusted if `/tune /email` or `/tune /chat`)
- Mix of: automated notifications, human messages, mailing lists, @mentions, doc comments, calendar items
- Include items from different senders, spaces, and time ranges
- Default: 20 messages. Override with `pulse /tune <N>`.

**Phase 2 — Walk through each message:**

For each message, show the full content and context:

```
━━━ Tune [1/20] ━━━

Source: 📧 Email
From: Gemini <gemini-notes@google.com>
Addr: → To
Subject: [Notes: "Leadership Huddle"](https://mail.google.com/mail/u/0/#inbox/<ID>)

> [full message body]

Is this the kind of message you want to see?

  👍 yes — I want to see these
  👎 no — hide or deprioritize these
  🤷 skip — no opinion on this one

Why? (optional — helps pulse learn better patterns):
```

**Phase 3 — Capture response and extract pattern:**

For each rated message:
1. Record the user's yes/no/skip + their reason
2. Extract the best generalizable pattern (same logic as `/rate`):
   - Automated sender → `source_app` + `subject_pattern`
   - Human → `sender`
   - Category → `subject_pattern` or `addr`
3. Show the proposed rule:
   ```
   Got it — demoting: Gemini meeting notes (pattern: "Notes: .*")
   Reason: "I read these in the doc directly, don't need email copies"
   ```
4. Save to memory. No confirmation needed per-item during tune (the whole session is the confirmation).

**Phase 4 — Summary:**

After all messages:
```
📡 Tune Complete — 20 messages reviewed

  👍 Boosted (6):
    • alice@example.com — "important collaborator"
    • bob@example.com — "project updates matter"
    • Google Docs comments on "Project Command Center" — "active doc I own"
    • @mentions in Team Chat — "my team"
    • Direct questions in any space — "people waiting on me"
    • Emails where I'm sole To: recipient — "direct asks"

  👎 Demoted (8):
    • Gemini meeting notes — "read in doc directly"
    • Calendar declines — "noise"
    • Site notifications — "automated"
    • GitLab access grants — "automated"
    • Jira escalation blasts to mailing list — "not on-call"
    • ...

  🤷 Skipped (6)

Memory: 14 signals saved. Run `pulse /memory` to review.
Next `pulse` will use these preferences.
```

**Tune stacks with source filters:**
- `pulse /tune /email` — only email messages
- `pulse /tune /chat` — only chat messages
- `pulse /tune 10 /email` — 10 email messages

---

### Step 9: Config (when `/config` is active)

`/config` walks through each configurable property interactively.

**Storage:** Config lives in the SKILL.md itself (the SPACES, VIPS, DIRECT_REPORTS, and Defaults blocks). The agent reads the current values, walks through each, and rewrites the config blocks in place.

**Flow for each property:**

1. **Chat Spaces:**
   - Auto-discover via `gws chat spaces list`
   - Show current configured spaces (if any)
   - Present full list of user's spaces with checkboxes
   - If already configured, ask: "Append to existing list, overwrite, or keep as-is?"
   - Save selection

2. **VIP Senders:**
   - Show current VIPs (if any)
   - Ask: "Who are your VIP senders? (emails, comma or space separated)"
   - If already configured, ask: "Append to existing list, overwrite, or keep as-is?"
   - Save

3. **Direct Reports:**
   - Show current direct reports (if any)
   - Ask: "Who are your direct reports? (emails, comma or space separated)"
   - If already configured, ask: "Append to existing list, overwrite, or keep as-is?"
   - Save

4. **Defaults:**
   - Show current defaults (email max, chat max, time window, query)
   - For each, ask: "Keep current value or change?"
   - Only update values the user wants to change

**Example session:**

```
📡 Pulse Config

━━━ Chat Spaces ━━━
Current: Agent Studio TDMs, AIPCA Code Reviews, EGAI

Found 12 spaces on your account:
  1. ✅ Agent Studio TDMs
  2. ✅ AIPCA Code Reviews
  3. ✅ EGAI
  4.    Design Reviews
  5.    Platform Engineering
  ...

Append, overwrite, or keep as-is? (a/o/k): k
→ Keeping current 3 spaces.

━━━ VIP Senders ━━━
Current: (none configured)

Who are your VIP senders? (emails, or "skip"):
> vp@example.com, director@example.com
→ Saved 2 VIPs.

━━━ Direct Reports ━━━
Current: (none configured)

Who are your direct reports? (emails, or "skip"):
> alice@example.com, bob@example.com
→ Saved 2 direct reports.

━━━ Defaults ━━━
  Email max:     20  — keep? (y/n): y
  Chat max/space: 10 — keep? (y/n): y

✅ Config saved.
```

**Config is non-destructive by default:** every property with existing values asks append/overwrite/keep before changing anything.

---

### Step 10: Sweep (when `/sweep` is active)

`/sweep` scans your inbox for cleanup candidates and proposes archive or delete actions.

**Phase 1 — Scan for cleanup candidates:**

Fetch a larger batch of emails (up to 50):
```bash
gws gmail +triage --max 50 --query 'in:inbox' --format json
```

Sweep scans the entire inbox regardless of read status — read emails cluttering the inbox are just as much noise as unread ones.

For each message, classify as a sweep candidate if it matches ANY of:
- **Memory demotes (weight ≥ 2):** messages matching strongly demoted patterns
- **Automated notifications:** GitLab pipelines, site provisioning alerts, process error emails
- **Calendar noise:** declines, accepts, OOO auto-replies, Gemini meeting notes
- **Stale threads:** messages older than 7 days that were never 🔴 or 🟡
- **Duplicate notifications:** multiple emails about the same event/ticket

**Phase 2 — Present candidates in a single numbered table:**

```
📡 Sweep — 35 candidates from 50 scanned

| #  | Action  | From | Subject | Age |
|----|---------|------|---------|-----|
|  1 | archive | Dana Lee | Declined: Leadership Huddle... | 12h |
|  2 | archive | Sam Patel | Declined: Leadership Huddle... | 12h |
|  3 | archive | Chris Wong | Declined: Leadership Huddle... | 12h |
|  4 | archive | Pat Rivera | Declined: Leadership Huddle... | 14h |
|  5 | archive | Jordan Kim | Declined: Leadership Huddle... | 14h |
|  6 | archive | Sam Patel | Out of office Re: Leadership... | 10h |
|  7 | archive | admin@demo-site.example.com | Error in Task: Create/Link | 8h |
|  8 | archive | admin@demo.example.com | Error in Task: Write Cat | 14h |
|  9 | archive | admin@demo.example.com | Error in Task: Write Cat | 15h |
| 10 | archive | Site Mgmt | Your Site is ready | 5h |
| 11 | archive | Site Mgmt | Your Site is ready | 12h |
| 12 | archive | GitLab | Fixed pipeline for feature-branch | 9h |
| 13 | archive | Datadog | Your Daily Digest | 14h |
| 14 | delete  | Vendor | Try Product X with 50% off | 14h |
| ...

Kept: 15 emails (VIP, 🔴, 🟡 — not touched)
```

**Response format — simple and flexible:**

- `all` — execute every proposed action as shown
- `none` — cancel, touch nothing
- `1-14` — execute items 1 through 14
- `1 3 5 7-12` — mix of individual items and ranges
- `all -4 -6` — all except items 4 and 6
- `flip 14` — change item 14's action (archive↔delete)
- `drop 3 5` — remove items from the list entirely (won't be touched)
- `only <criteria>` — filter the list by natural language (e.g., `only calendar`, `only datadog`, `only older than 1d`)

**Pre-filter with `/sweep <filter>`:**

`pulse /sweep` accepts natural language that pulse translates into the best Gmail query:

```
pulse /sweep gitlab              → from:gitlab subject:pipeline
pulse /sweep calendar declines   → subject:(Declined OR "Out of office")
pulse /sweep older than 2d       → older_than:2d
pulse /sweep announcements       → from:no-reply-announcements OR from:no-reply
pulse /sweep datadog             → from:datadog OR from:dtdg
pulse /sweep process errors      → from:admin subject:"Error in Task"
pulse /sweep everything from last week → older_than:7d
```

The agent interprets intent and constructs the query dynamically — these examples are illustrative, not a fixed mapping. Any natural language filter works.

**In-session filtering with `only`:**

After the table is shown, `only` re-filters without re-fetching:

```
> only calendar
  Showing 7 of 35 (filtered to calendar items)
  [table with just items 1-7]

> all
  Executing: archive 7. Proceed? (y/n)
```

Examples:
```
> only gitlab              # just GitLab items
> only older than 12h      # just items older than 12 hours
> only siteops datadog    # Site ops + Datadog items
> only delete              # just items proposed for delete
> all                      # show full list again (reset filter)
```

After the user responds, confirm before executing:
```
Executing: archive 13, delete 1

Proceed? (y/n)
```

**Phase 3 — Execute with approval:**

For each batch the user approves:
- **Archive:** `gws gmail users messages modify --params '{"userId": "me", "id": "<ID>"}' --json '{"removeLabelIds": ["INBOX"]}'`
- **Delete:** `gws gmail users messages trash --params '{"userId": "me", "id": "<ID>"}'`

After each batch, confirm: `✅ Archived 7 calendar emails.`

**Phase 4 — Summary:**

```
📡 Sweep Complete — 14 actions taken

  ✅ Archived: 13
  🗑️ Deleted: 1
  ⏭️ Skipped: 21

  Inbox: ~201 → ~187 unread
```

**Safety rules for `/sweep`:**
- NEVER auto-execute. Every batch requires explicit approval.
- Confirmation prompt:
  - Mixed batch (archive + delete): `Proceed? (y/n)`
  - All-delete batch: `Type "delete" to confirm, or n to cancel` (extra friction for destructive-only operations)
- Default to archive, not delete. Only propose delete for vendor marketing, exact duplicates, or obvious spam.
- NEVER propose archiving/deleting messages from VIPs or direct reports.
- NEVER propose archiving/deleting messages classified as 🔴 or 🟡.

**Learning from sweep actions:**

After each sweep execution, pulse saves the user's chosen action into memory signals with a `sweep_action` field:

```json
{
  "type": "demote",
  "match": {"sender_pattern": "no-reply@dtdg\\.co"},
  "reason": "sweep: deleted Datadog digests",
  "weight": 2,
  "sweep_action": "delete",
  "created": "2026-04-17"
}
```

**How `sweep_action` drives future recommendations:**

| User action | `sweep_action` | Next sweep proposes | Weight change |
|-------------|---------------|-------------------|---------------|
| Deleted | `"delete"` | delete | +1 |
| Archived | `"archive"` | archive | +0.5 (rounds up on repeat) |
| Flipped archive→delete | `"delete"` | delete (stronger signal) | +1 |
| Dropped (kept) | none | won't propose next time | no change |

When sweep encounters a message matching a signal with `sweep_action`, it uses that action as the default proposal. No `sweep_action` = default to archive.

This means:
- Datadog digests you deleted → auto-propose delete next time
- Gemini notes you archived → auto-propose archive next time
- Patterns you consistently keep won't be proposed again

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


Capability resource: `.codex/skills/pulse/resources/capability.json`
