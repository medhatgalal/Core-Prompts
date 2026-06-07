---
name: "eng-report"
description: "Engineering progress report for any git repo. Generates a standalone HTML dashboard with velocity, MRs, lines changed, release timeline, code churn, contributor breakdown, and autonomy metrics. Supports fleet mode to run across multiple repos and upload to Google Drive."
---
# Engineering Progress Report

## Dependencies

| Command | Requires |
|---------|---------|
| `run` | `git` only — no external dependencies |
| `sync` | `gws-drive` skill (Google Drive access) |
| `sync-authors` | Appian Home MCP server (`search_tech_employees` tool) |
| `configure` | None |
| `add` | None |

`sync-authors` is the only command that requires Home MCP. It is optional — author lists can be maintained manually in `config.yaml` if Home MCP is unavailable.

## Purpose
Generate a standalone HTML engineering report for any git repository covering the last 2 weeks (or a custom date range). Supports single-repo and fleet (multi-repo) modes. Reports can be saved locally, uploaded to Google Drive in dated directories, and announced via Google Chat or email.

## Usage

```
/eng-report <command> [options]
```

**Commands:**

| Command | Description |
|---------|-------------|
| `run` | Generate reports for all configured repos (or one with `--repo`). Saves to `/tmp/YYYY-MM-DD/` locally and opens in browser. |
| `sync` | Pull latest reports from Google Drive to `~/eng-reports/`. |
| `configure` | Interactive one-time setup (Drive folder, local sync path, notify defaults) |
| `add PATH` | Add a repo to the configured repo list |
| `sync-authors` | Re-resolve group membership via Home MCP and update `authors` lists in config for all scoped repos |

**Options for `run`:**

| Option | Default | Description |
|--------|---------|-------------|
| `--repo PATH` | all configured repos | Limit to one specific repo |
| `--since DATE` | `1 week ago` | Start date — accepts ISO format `YYYY-MM-DD` or relative `N weeks ago` / `N days ago` |
| `--drive` | false | Upload to Google Drive, then auto-sync to `~/eng-reports/` |
| `--open` | false | Open `_index.html` (or single report) in browser after generating |
| `--notify` | false | Send notification via Chat/email |
| `--folder NAME` | config value | Drive folder override for this run |
| `--email ADDR` | config value | Email override for this run |
| `--chat SPACE` | config value | Chat space override for this run |

**Options for `sync`:**

| Option | Default | Description |
|--------|---------|-------------|
| `--open` | false | Open `_index.html` in browser after syncing |
| `--date DATE` | latest | Sync a specific date folder (`2026-05-29`) |
| `--force` | false | Re-download all files even if already local |

**Auto-sync behavior:**
- `run --drive` → generates, uploads, automatically syncs to `~/eng-reports/YYYY-MM-DD/`
- `run` (no `--drive`) → generates to `/tmp/YYYY-MM-DD/` only, opens each report in browser
- `run --drive --open` → generates, uploads, syncs, opens `_index.html`
- `sync` → explicit pull from Drive, no generation

## Configuration

Config lives at `~/.kiro/skills/eng-report/config.yaml`.

There are two types of entries: **repo entries** (single repo) and **group entries** (multiple repos, aggregated).

```yaml
drive:
  folder: "Engineering Reports"
  notify:
    chat_space: ""
    email: "you@company.com"

local:
  sync_path: "~/eng-reports"
  window: "1 week ago"

repos:
  # ── Repo entry: single repo, optional author/path scope ──────────────────
  - name: MyRepo
    path: ~/repo/my-repo         # single path

  - name: AIPlatform-repo
    path: ~/repo/ai-platform    # whole repo, no scope

  # ── Group entry: multiple repos, same author filter, aggregated ──────────
  - name: AIPlatform
    repos:                       # list of repos to query
      - ~/repo/ai-platform
      - ~/repo/ae
    scope:
      business_unit: "Automation"
      tribe: "AI PLATFORM"
      resolved_at: "2026-06-05"
      authors:
        - Alice Johnson
        - Roberto Bisteni
        # ...

  - name: Automation-SBU
    repos:
      - ~/repo/ae
      - ~/repo/ai-platform
      - ~/repo/agent-continuous-learning
      - ~/repo/lcp-mcp-server-service
    scope:
      business_unit: "Automation"
      resolved_at: "2026-06-05"
      authors:
        - Alice Johnson
        # ... all Automation SBU members
```

**Entry type rules:**
- `path` (single string) → repo entry, one repo
- `repos` (list) → group entry, multiple repos aggregated into one report
- Group entries with `scope.authors` apply the same author filter to every repo in the list
- Group entries with no `scope` aggregate all commits across all listed repos (no author filter)

**Scope rules (apply to both entry types):**
- `scope.authors` → `git log --author` filter applied per repo, results aggregated
- `scope.paths` → `git log -- path` filter (useful when group shares a subdirectory naming convention)
- `scope.tribe`, `scope.team`, `scope.business_unit` → display labels + drive `sync-authors` resolution
- `resolved_at` → date author list was last resolved; triggers staleness warning if window predates it by >30 days

**Org hierarchy available from Home MCP:**
```
business_unit  →  "Automation", "Appian Foundations", etc.
group         →  "AGENTIC AI", "AI COPILOT", "AI PLATFORM", etc.
team           →  "Agent Studio Enabling Team", "AI Platform Core APIs", etc.
```

**`sync-authors` behavior for group entries:**
Queries authors across ALL repos in the `repos` list (90-day window each), merges the unique set, resolves each against Home MCP, filters by the declared org level.

Set once with `configure`, override per-run with `--folder`, `--email`, `--chat`.

## Workflow

### For `sync-authors`

Re-resolves group/team/business_unit membership from Home MCP for all scoped repos in config.

1. For each repo entry with a `scope` block that has `tribe` (group), `team`, or `business_unit` set:
   a. Get all git authors active in the repo in the last 90 days: `git log --since='90 days ago' --format='%aN' | sort -u`
   b. For each human author (skip bots: `Appian CI`, `*-ops`, `*-automation`, `root`, `hudson-*`):
      - Call `search_tech_employees` with `isFullDetail=true` and the author's display name
      - Extract `etbEngineeringTribe.name`, `etbEngineeringTeam.name`, `etbEngineeringTribe.businessUnit.name`
   c. Filter to authors whose org level matches the scope:
      - `scope.business_unit` → match `businessUnit.name`
      - `scope.tribe` → match `etbEngineeringTribe.name`
      - `scope.team` → match `etbEngineeringTeam.name` (most specific)
   d. Update `scope.authors` list in config.yaml with resolved names
   e. Set `scope.resolved_at` to today's date (`YYYY-MM-DD`)
2. Save updated config.yaml
3. Print summary: for each scoped repo, show old author count → new author count and any additions/removals

### For `configure`

Interactive first-time setup. Reads current `config.yaml` if it exists.

1. **Drive folder** — "Where should reports be saved in Google Drive?" (default: `Engineering Reports`)
2. **Local sync path** — "Where should reports be synced locally?" (default: `~/eng-reports`)
3. **Notifications** — "Email address for weekly summary? (leave blank to skip)"
4. **Chat** — "Google Chat space ID? (leave blank to skip)"
5. **Repos** — For each repo the user wants to add:
   a. "Repo name (display label, e.g. AI Platform):"
   b. "Local path (e.g. ~/repo/ai-platform) — leave blank if not cloned:"
   c. If no local path: "Remote git URL (e.g. git@github.com:appian/ae.git):" — script will auto-clone on first run
   d. "Is this a large monorepo like ae? (y/n)" — if yes, offer scope setup:
      - "Filter by org unit? Enter tribe/group name or leave blank for whole repo:"
      - If tribe entered: call `sync-authors` immediately to resolve members from Home MCP
   e. Repeat until user enters blank for repo name
6. Write `config.yaml`
7. Offer to run `sync-authors` now to resolve all org memberships: "Resolve team memberships from Home MCP now? (y/n)"
   - If yes: run `sync-authors` workflow for all scoped entries
8. Validate git access: for each `remote:` URL, run `git ls-remote <url> HEAD` — warn if unreachable
9. Confirm: "Configuration saved. {N} repos configured. Run `eng-report run` to generate your first reports."

### For `add PATH`

1. Resolve the path to absolute. Verify it contains a `.git` directory — abort with error if not a git repo.
2. Derive the repo name from the directory basename (e.g., `/Users/x/repo/my-repo` → `my-repo`)
3. Append to `repos:` list in `config.yaml`. If path already exists in list, skip and print "Already configured."
4. Confirm: "Added <name> to repo list."

### For `run`

**This command delegates all git data gathering to `scripts/eng-report.py`.** Do not run git commands manually — use the script.

#### Pass 1 — Gather metrics (deterministic)

```bash
eng-report run --json-only > /tmp/metrics.json
# For a single entry:
eng-report run --name MyRepo-Repo --json-only > /tmp/metrics.json
```

The script handles: git fetch, all git log commands, author filtering, multi-repo aggregation, Jira prefix detection, contributor counting, release tagging, file churn, and daily velocity. Output is structured JSON per entry.

#### Pass 2 — Generate AI narrative

Read `/tmp/metrics.json`. For each entry with `commits > 0`, generate:

- **`summary`**: 3–4 sentence arc of the period. Team-framing only — never single out individuals negatively.
- **`themes`**: `<ul>` HTML with 4 `<li>` items. Each must cite a specific file, metric, or pattern from the JSON as evidence.
- **`architecture`**: 4 `<div>` cards (use exact format from AI Narrative Integration section). Synthesized from top files and commit subjects.
- **`work_areas`**: For Jira-prefixed repos only. Cluster commit subjects (strip ticket prefix) into 5–7 plain-English work areas. Render as horizontal bar HTML (see AI Narrative Integration section).

Write to `/tmp/narrative.json`: `{"entry-name": {"summary": "...", "themes": "...", "architecture": "...", "work_areas": "..."}}`

For entries with `commits == 0`: skip narrative — the script renders "No activity this period" automatically.

#### Pass 3 — Render HTML (deterministic)

```bash
eng-report run --narrative-file /tmp/narrative.json
# With Drive upload:
eng-report run --narrative-file /tmp/narrative.json --drive --open
```

`_index.html` is always generated, grouped by: Repos → SBU → Groups → Teams → Individuals.
### Index Page (`_index.html`)

A summary page generated whenever ≥2 repos are processed. Uses same design tokens and dark theme.

**Structure:**
- Header: "Engineering Reports — YYYY-MM-DD"
- Cross-repo comparison table with these exact columns:

| Repo | Commits | MRs | Net Lines | Releases | Top Contributor |
|------|---------|-----|-----------|----------|-----------------|

- **Data source:** Each cell comes from that repo's Step 2 computed metrics. "Top Contributor" = author with highest commit count from `git shortlog` output, formatted as "Name (N%)".
- Each repo name is a relative hyperlink to `<RepoName>.html` (works locally and in Drive)
- Footer: "Generated: YYYY-MM-DD HH:MM" timestamp

### Drive Upload (`--drive`)

Uses `gws-drive-upload` skill tools:

1. Search for the top-level folder by name from config (e.g., `"Engineering Reports"`). If not found, create it.
2. Within that folder, search for a subfolder named today's date (`YYYY-MM-DD`). If not found, create it.
3. Upload `_index.html` first, then each `<RepoName>.html` in alphabetical order
4. Print the Drive folder URL to console
5. **Auto-sync**: download all uploaded files to `local.sync_path/YYYY-MM-DD/` so they're immediately browsable locally. Create the local directory if it doesn't exist.

### For `sync`

1. Read `local.sync_path` and `drive.folder` from config. Abort with error if either is missing.
2. List dated subfolders in the Drive folder (pattern: `YYYY-MM-DD`)
3. If `--date` specified: sync only that folder. If folder not found in Drive, abort with error.
4. If no `--date`: sync the most recent dated folder (sorted lexicographically descending, take first).
5. For each `.html` file in the folder: download to `local.sync_path/YYYY-MM-DD/<filename>`. Skip if file already exists locally AND `--force` is not set.
6. Print: "Synced N files to ~/eng-reports/YYYY-MM-DD/"
7. If `--open`: open `local.sync_path/YYYY-MM-DD/_index.html` in browser

### Notifications (`--notify`)

After fleet run completes (and Drive upload if applicable):

**Google Chat** (if `chat_space` configured or `--chat` provided):
Post exactly this format:
```
📊 Engineering Reports — YYYY-MM-DD

N repos analyzed:
• RepoName: X commits, Y MRs, Z releases
[repeat for each repo]

Reports saved to: <folder_name>/YYYY-MM-DD/
[If --drive was used, append: "Drive: <folder_url>"]
```
Use `gws-chat-send` skill.

**Email** (if `email` configured or `--email` provided):
Send with subject "Engineering Reports — YYYY-MM-DD" and same body content as Chat message.
Use `gws-gmail-send` skill.

**If neither chat nor email is configured and `--notify` is passed:** Print warning "No notification targets configured. Use `configure` or pass --email/--chat."

## Output Quality Standards

A 10/10 report MUST satisfy ALL of the following. Treat each as a gate — if any fails, fix before outputting:

- [ ] All 7 metric cards present with values from git commands — no placeholders, no invented values
- [ ] Daily chart: exactly WINDOW_DAYS bars (one per calendar day), zero-commit days show as 2px bars, peak day highlighted with orange→red gradient
- [ ] Category bars: only conventional prefixes (lowercase words before `:`, `(`, `!`). No Jira keys (e.g., `LCP-123`) appear as categories.
- [ ] Architecture Evolution: 4–6 cards, each citing specific file paths AND their add/delete line counts from numstat output. No files referenced that are not in numstat.
- [ ] Release timeline: only git tags or explicit version-bump commits — merge commits NEVER appear here
- [ ] Code churn: top 10 files from numstat, green bar (additions) + red bar (deletions) with numeric labels
- [ ] Executive summary: 3–4 sentences synthesizing patterns, NOT listing commits. References specific modules/directories visible in the data.
- [ ] Key themes: 4 cards, each citing a specific metric (percentage, count, or ratio) as evidence
- [ ] No individual commit SHAs anywhere in the visible report
- [ ] Fully standalone HTML — zero `<link>`, `<script src=`, or `url()` references to external resources
- [ ] Every number in the report is traceable to a specific git command output from Step 1
- [ ] HTML file opens correctly in browser with no console errors

## AI Narrative Integration

Reports are rendered in two passes to ensure data integrity:

**Pass 1 — Deterministic data (script):**
```bash
eng-report run --json-only > /tmp/metrics.json
```
Outputs: `[{"name": "AgenticAI-Group", "commits": 16, "net": 2210, ...}, ...]`

**Pass 2 — AI narrative (skill/AI):**
Read metrics.json. For each entry, generate:
- `summary`: 3–4 sentences synthesizing the arc of the period. Team-framing only.
- `themes`: `<ul>` HTML, 4 `<li>` items each citing a specific file or metric as evidence.
- `architecture`: 4 `<div>` cards — `<div style="background:rgba(30,35,44,0.9);border:1px solid rgba(48,54,61,0.7);border-radius:10px;padding:16px">` with title (blue), description, and file evidence.
- `work_areas`: `<div>` bars HTML for Jira-prefixed repos — cluster commit subjects (stripped of ticket prefix) into 5–7 plain-English work areas with commit counts as horizontal bars.

Write to `/tmp/narrative.json`: `{"AgenticAI-Group": {"summary": "...", "themes": "...", "architecture": "...", "work_areas": "..."}}`

**Pass 3 — Final render (script):**
```bash
eng-report run --narrative-file /tmp/narrative.json
```

`_index.html` is always generated, grouped by: Repos → SBU → Groups → Teams → Individuals.

## /help

```
eng-report — Engineering progress report for any git repo

COMMANDS:
  run                              Generate reports for all configured repos, open in browser
  run --repo ~/repo/my-repo         Generate for one specific repo
  run --since 2026-05-01          Custom start date (also: '2 weeks ago', '30 days ago') (ISO date or "N weeks ago")
  run --narrative-file FILE       JSON file with AI narratives per entry (see workflow)
  run --json-only                 Output metrics JSON only, no HTML (pipe to AI for narrative generation)
  run --author "Jane Smith"       Generate report for a single person across all repos
  run --drive                     Generate + upload to Drive + auto-sync locally
  run --drive --open              Generate + upload + sync + open _index.html
  run --drive --folder "Q2"       Upload to a specific Drive folder
  run --notify                    Notify via Chat/email (uses config)
  run --notify --email a@b.com    Override notification email for this run
  run --drive --notify            Upload + sync + notify

  sync                            Pull latest reports from Drive to ~/eng-reports/
  sync --open                     Pull + open _index.html in browser
  sync --date 2026-05-29          Sync a specific date folder
  sync --force                    Re-download all files

  configure                       Interactive setup (Drive folder, sync path, notify, repos)
  add ~/repo/MyRepo               Add a repo to the configured repo list

LOCAL OUTPUT:
  run (no --drive):  /tmp/YYYY-MM-DD/            temporary, opens in browser
  run --drive:       ~/eng-reports/YYYY-MM-DD/   persistent after auto-sync

DRIVE STRUCTURE:
  Engineering Reports/
    2026-06-05/
      _index.html   ← summary + links to each repo report
      MyRepo.html
      Composer.html

CONFIG: ~/.kiro/skills/eng-report/config.yaml
```
