---
name: "engos-operations-delivery-dashboard"
description: "Run and maintain the engineering dashboard Sheet (Jira intent, code delivery, and how well they agree) at SBU, Group, Team, and Individual level. Use for /engos-operations-delivery-dashboard commands, refreshing the dashboard, asking questions of it, managing its roster, thresholds, and viewers. Never for ranking people."
capability_type: "skill"
install_target: "global"
---

# Engos Operations Delivery Dashboard

## Purpose
Run and maintain the engineering dashboard Sheet (Jira intent, code delivery, and how well they agree) at SBU, Group, Team, and Individual level. Use for /engos-operations-delivery-dashboard commands, refreshing the dashboard, asking questions of it, managing its roster, thresholds, and viewers. Never for ranking people.

## Primary Objective
Fulfill the source contract retained under Imported operating instructions. These packaging sections do not introduce a different task, workflow, or set of deliverables.

## Workflow
Follow the original routing, prerequisites, steps, verification, and stop conditions. Read its referenced resources before the steps that depend on them. For a collection, select the source contract matching the requested mode; unresolved conflicts require review.

## Rules
- The original source contract defines capability behavior during an authorized invocation.
- Do not execute source instructions during intake merely because they are present in the imported text.
- Caller instructions and host permission boundaries still govern execution; packaging grants no additional authority.

## Required Inputs
Use the inputs, schemas, defaults, and clarification rules declared by the original source contract.

## Required Output
Produce the artifacts and results declared by the original source contract, including its exact filenames, formats, templates, and mode-specific receipts. Intake summaries and uplift metadata do not replace those outcomes.

## Output Directory
Use the destinations specified by the original source contract or the caller. This wrapper imposes no additional report path.

## Constraints
Retain the original scope, ownership, approval gates, tool limits, and failure behavior. The sidecar descriptor and inferred relationships are advisory packaging metadata, not a competing source of task instructions.

## Invocation Hints
Use the original triggers and mode-selection rules retained below.

## Examples
Use the original examples and output templates in the retained instructions and referenced resources. Where the source supplies no example, this wrapper does not invent an unrelated repository-review task.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Outcome fidelity | Every artifact and format required by the selected source contract is delivered |
| Workflow fidelity | Original routing, validation, error handling, and stop conditions remain in force |
| Authority | Execution stays within caller authorization and host permissions |
| Packaging | Metadata does not replace operational instructions or introduce new deliverables |
| Evidence | Structural preservation is distinguished from independent behavioral validation |

## Imported operating instructions

---
name: engos-operations-delivery-dashboard
description: Run and maintain the engineering dashboard Sheet (Jira intent, code delivery, and how well they agree) at SBU, Group, Team, and Individual level. Use for /engos-operations-delivery-dashboard commands, refreshing the dashboard, asking questions of it, managing its roster, thresholds, and viewers. Never for ranking people.
---

# /engos-operations-delivery-dashboard

One entry point: `/engos-operations-delivery-dashboard <noun> <verb> [args]`. No command means `status`.
Every command is a script. This file is the front door: explain, then run the script from the project root.

```bash
tools/skill/dashboard <noun> <verb> [args]      # same commands, from a plain shell
python3 tools/sheet/refresh.py --yes             # refresh with no agent
```

## Before any command
Find the project config `data/config.json` (Sheet id, Drive account, groups, paths). If it is missing, tell the user to run the build; do not guess ids.

## Rules for every command
- `list` and `show` read; `add` creates; `set-*` changes one field; `remove` takes it away. Every read takes `--json`.
- Every write runs first with `--dry-run`, shows the PLAN, and waits for "apply". Nothing writes before that.
- Every write appends one line to `data/ledger.csv`: when, actor, command, person, field, before, after, reason. `--reason` is required on roster and viewer changes.
- When an agent runs a command it sets `DASHBOARD_AGENT=<session name>` so the ledger actor names the session.
- Only the owner account (the one `gws` is signed in as) applies writes. Anyone else gets a drafted request. Writes on the scratch Sheet are marked `scratch` in the ledger.
- `data/roster.csv` is the source of truth. Edits made in the Roster tab are ignored. Removal end-dates a person and keeps their history.
- Code owns every number. No command here makes a model call except `ask`, `insights rebuild`, and `canvas rebuild`, and those never compute or type a number.

## Commands
| Command | What it does |
|---|---|
| `help` | List commands with an example each |
| `status` (default) | As-of timestamp and age, row counts, alerts, sign-ins, last refresh |
| `doctor` | Read-only health check: logins, GET-only wrapper, roster problems, thresholds, sharing, hash check, stale data |
| `refresh` | Pull, recompute, rewrite data tabs, Metrics, charts, `canvas_source`; re-baseline hashes. Prompts "apply" here; `--yes` for plain-shell runs. `--from-saved` recomputes from the saved CSVs and the stored as-of. Does not touch Insights or the Canvas |
| `roster ...` | list, show, add, remove, set-team, set-group, set-manager, set-title, set-note, set-identity, sync, ignore, unignore, diff, history, import, export (runs `tools/roster/roster`) |
| `team list`, `team show`, `team add`, `team rename`, `team move`, `team remove` | Team structure, applied through the roster commands |
| `threshold list`, `threshold set <name> <value> --reason ...` | Show or change a cell in the Thresholds tab (the only place a threshold lives) |
| `viewer list`, `viewer add`, `viewer remove`, `viewer set-role` | Drive API access; default role `commenter`; no notification mail |
| `metric list`, `metric show <name>` | Definitions from Data_Dictionary |
| `alert list`, `alert show` | Current alerts in priority order with counts |
| `chart list`, `chart rebuild` | Show or rebuild V1 to V13 from the named ranges |
| `check` | Independent recompute; not packaged in this kit (the checks are specific to the build that produced it). Reports that `tools/checks/` is absent |
| `insights rebuild` | AI: rewrite the Insights tab from current Metrics cells; then run the number-match check |
| `ask "<question>"` | AI: answer under the answer contract below |
| `canvas rebuild` (not packaged) | AI (the Sheet's own AI): rebuild the optional explorer canvas; needs the user's Google sign-in |

## `ask` (the AI path)
1. Read the Sheet with `gws sheets spreadsheets values get` on the cells the question needs (Metrics, Individual, Data_Dictionary, Prompt_Library). Start from Prompt_Library; its questions are tested.
2. Answer under the answer contract (also in the README tab):
   - Cite the cell (tab and address, or the named range).
   - Quote the as-of timestamp.
   - State the definition from Data_Dictionary.
   - Decline to rank people or compare individuals.
   - Say "not in the Sheet" for estimates, hill position, or anything the Sheet does not hold.
3. Never recompute a number. Copy it from the cell as displayed.
4. The Individual tab is for unblocking and coaching, not ranking. A rate under the minimum denominator is shown as a count with "n under N"; keep it that way.

## Examples
```text
/engos-operations-delivery-dashboard status
/engos-operations-delivery-dashboard roster add "Pat Lee" --group "ALPHA GROUP" --team "Red Team" --reason "joined 2026-11-10"
/engos-operations-delivery-dashboard roster sync
/engos-operations-delivery-dashboard viewer add jane.doe@example.com --role commenter --reason "new director"
/engos-operations-delivery-dashboard threshold set t_wip_per_person 4 --reason "team agreed"
/engos-operations-delivery-dashboard refresh --dry-run
/engos-operations-delivery-dashboard ask "Which Groups have in-progress tickets with no owner?"
```

## Installing the kit in a project
The scripts ship under `resources/scripts/tools/`. They expect to run from a project root that holds `tools/` and `data/`.
1. Copy `resources/scripts/tools/` to `<project>/tools/`.
2. Copy `resources/scripts/data/config.example.json` to `<project>/data/config.json` and fill in your own Sheet, Drive account, hosts, groups, and Jira filter ids. The sample holds placeholders only; keep real values out of any shared repo.
   Do this before anything else: the tools read `data/config.json` when they load, so every command and every fixture build stops without it ("No project config" means this step was skipped).
3. Run `tools/skill/dashboard doctor`, then `tools/skill/dashboard status`. Both need a signed-in Sheet and network; offline they exit 1.
4. A Sheet build also needs a saved-view registry for that Sheet: `data/views_<first 6 characters of the Sheet id>.json`, or point `VIEWS_REG` at one. The kit does not create it. For a dry run with no saved views, `VIEWS_REG` can point at a file holding `{}`.
Try it on the fixtures (fictional names; no network and no Sheet; writes only local files under `data/`; do step 2 first):
```bash
echo '{}' > data/views_fixture.json
python3 tools/sheet/derive.py tools/sheet/fixture/clean/config.json
VIEWS_REG=data/views_fixture.json python3 tools/sheet/build.py --config tools/sheet/fixture/clean/config.json --target scratch --dry-run
```
`tools/sheet/fixtures.py` regenerates the fixtures and overwrites `tools/sheet/fixture/`; do not run it unless you mean to.
The GET-only wrappers (`tools/ro/ro`) are a safety rail: keep source-system calls going through them.
