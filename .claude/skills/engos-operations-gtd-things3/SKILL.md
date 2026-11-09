---
name: "engos-operations-gtd-things3"
description: "Task-system adapter that lets the GTD planning method read and write Things 3 on macOS through a bundled script. Use when the profile lists `things3` under adapters, or when the GTD method needs snapshot, inspect, history, capture, relocate, schedule, annotate or retag against Things 3. Do not use on other platforms, for Things Cloud or iOS, or to run the planning method itself."
---
# GTD Things 3 adapter

## Purpose

Maps the method's abstract verbs onto Things 3 and describes the bridge script that enforces the write rules. The method rules live in `engos-operations-gtd-planning`. This file holds only what is specific to Things.

The bridge is `resources/things.js`. Its header comment is the source of truth. This file summarises them.

## Primary Objective

Read and write Things 3 for the GTD method only through the bridge, so every write rule is enforced by code, and report each result as observed.

## Tool Boundaries

- macOS only. Things must be running.
- Each call takes seconds. A full snapshot may take several.
- Checklists, repeat rules and headings cannot be read by scripts. Never say what a checklist holds. If a change might touch one (rename, split), tell the user you cannot see it.
- A `move` is not proven to keep an item in its heading. Make no such promise until a test shows it.
- "This Evening" is not supported.
- Touch Things only through the bridge. Never open the database, use the `things:///` URL scheme, or write your own AppleScript.

## Required Inputs

- A bridge command from the Commands table.
- Its argument: a JSON value or `@<file>`.
- Whether the run is interactive or unattended (`THINGS_INTERACTIVE`).
- For `move` and `clear-schedule`: the user's yes to the exact change, after a dry run.

## Workflow Contract

Touch Things only through the bridge. Run it as shown, read before writing, and show a dry run before any real `move`.

## Run it

```
osascript -l JavaScript resources/things.js <command> [json | @file] [--dry-run]
```

Arguments are a JSON value on the command line, or `@<file>` to read it from a file. `--dry-run` reports what would happen and changes nothing. Any other flag is an error. `capabilities` (or `--version`) prints the command names and contract version.

## Environment variables

| Variable | Effect |
|---|---|
| `THINGS_INTERACTIVE=1` | Allows `move` and `clear-schedule`. Set only by the interactive entry point. Scheduled or unattended runs never set it. Without it, those commands are refused. |
| `THINGS_TAG_ALLOWLIST` | Comma-separated tags. In an unattended run, `add` accepts only these. Others are dropped. |

The flag stops accidents and misconfiguration. It does not stop a caller who sets it. The hard guard is a host permission rule that denies `move` for the scheduled task.

## Commands

| Command | Verb | Notes |
|---|---|---|
| `snapshot` | snapshot | Open items in Inbox, Today, Upcoming, Anytime, Someday, plus areas, projects (with ids) and tags. Today items also appear under Anytime; count each id once. Notes are cut at 400 characters. Required columns id, name, notes, tags must have equal length or the call aborts; optional columns (area, project) are exempt. Observed once: a live snapshot on one real database showed equal column lengths. Not tested: what a failed column read does, so keep the assert. |
| `get <id>` | inspect | One item in full. Checklists unreadable. |
| `logbook <days>` | history | Items completed in the last N days. |
| `add` | capture | Items `{title, notes, tags, deadline, src}`. Inbox only. Refuses more than 25 at once. Skips a key already present (open items, and completed in the last 30 days). Drops unknown tags. Caps note length. Strips `src:` lines from untrusted text. Reads the key from the last notes line only. |
| `add --dry-run` | capture | Lists what would be added. |
| `move <id>` | relocate, schedule, annotate, retag | Fields: `id`, `projectId` or `area`, `when` (`today` or `YYYY-MM-DD`), `deadline`, `replaceDeadline`, `addTags`, `title`, `notesAppend`. Refused unless `THINGS_INTERACTIVE=1`. |
| `move --dry-run` | | Shows the change. Always show it and get a yes before the real call. |
| `clear-schedule <ids>` | clear-schedule | Takes a JSON array of ids (or `{id}` objects), `@file`, or comma-separated ids. Moves the item to Anytime, which clears its start date (checked on real Things, see the mapping table below). Refused unless `THINGS_INTERACTIVE=1`, even with `--dry-run`. The bridge re-reads the item afterwards and reports a failure if the date is still set. |
| `capabilities`, `--version` | | Command names and contract version. Read-only. |

Method verbs to bridge commands: inspect = `get`, history = `logbook`, capture = `add`, relocate, schedule, annotate and retag = `move` (fields above), clear-schedule = `clear-schedule`, snapshot = `snapshot`.

Use projects by `projectId`, never by name; names repeat.

## Rules the bridge enforces

- No delete, complete, cancel or move-to-Someday command exists.
- `move` adds tags, never removes. Appends to notes without trimming, re-reads before writing, and checks the old notes are a prefix of the new. A new title keeps the old one in notes ("Original title: ..."). A deadline is replaced only with `replaceDeadline: true`, and the old one goes to notes ("Deadline was: ...").
- `add` writes to the Inbox only. Never creates areas, projects or tags.
- Source key goes on the last non-empty line of notes as `src: <key>` (colon, one space, key). The key itself looks like `<source>:<ids>`, no whitespace.

The bridge cannot verify a user's yes. That part is a convention.

## Edit format

Follow the item's own pattern. If its notes have a first line, bullets, an `Action:` line or links, leave them and add below in the same style. Do not move an item out of its project or heading unless asked.

New items: verb-first title, notes `Action: <one line>`, then the source link, then the `src: <key>` line last.

## GTD to Things mapping

| GTD | Things 3 | Caveat |
|---|---|---|
| In | Inbox | |
| Next actions | Anytime, tagged by context | Anytime also holds later steps of sequential projects. A project is stalled when it has no open item in Today, Anytime or Upcoming. A project whose real next action is hidden by sequencing cannot be detected from a snapshot; the weekly review asks the user. |
| Projects | Projects; outcome in title or first note line | |
| Areas of focus | Areas | |
| Tickler | Start date (Upcoming) | `clear-schedule` removes it. Verified on real Things 2026-11-08 on two items. One in an area with no project: start date cleared, area and notes kept, item left only in Anytime. One inside a project under a heading, with a tag: start date cleared, project and tag kept, and the user confirmed on screen it stayed under its heading. Headings cannot be read by scripts, so this was a visual check |
| Hard deadline | Deadline | Upcoming also shows start dates. Report the two separately. |
| Waiting For | Waiting tag, person tag, first note line `Waiting since: YYYY-MM-DD` | Convention in free text. Fragile. |
| Someday/Maybe | Someday | The user moves it. |
| Commitments | Today | Today also holds items that landed there by start date or deadline. Flag them so the user sees what was chosen and what arrived. |
| Calendar | Not in Things | Read from the calendar source. |
| Reference | Outside Things | The profile says where. |

## Waiting For encoding

Tags: the waiting tag from the profile plus the person's tag. First notes line: `Waiting since: YYYY-MM-DD`. The adapter parses this line to compute age. A person tag is added only when sure it is the same person.

## Settings

Adapter settings (bridge path, tag allowlist, area and tag names) live in this adapter's own config, not the method profile.

## Required Output

The bridge's JSON result for each command, reported with what was observed and what was not checked. For a dry run, what would change and nothing else. Failures, refusals and skipped keys are reported by name.

## Invocation Hints

- Use for `snapshot`, `get`, `logbook`, `add`, `move`, `clear-schedule` against Things 3 on macOS.
- Use only when the profile lists `things3` under adapters.
- Run `capabilities` first if the contract version is in doubt.

## Examples

| Need | Command |
|---|---|
| Open items for the method's first step | `osascript -l JavaScript resources/things.js snapshot` |
| Add new items to the Inbox, check first | `osascript -l JavaScript resources/things.js add @items.json --dry-run` |
| Move an item after a yes (interactive only) | `THINGS_INTERACTIVE=1 osascript -l JavaScript resources/things.js move @move.json` |

## What was tested
The bridge logic is covered by 36 automated tests against a fake Things object. On real Things, read commands (`snapshot`, `get`, `logbook`, `--version`, `capabilities`) and `--dry-run` runs were checked, and `move` (start date) and `clear-schedule` were each run on throwaway items, including one inside a project under a heading with a tag. Not tested on real Things: `add`, `move` into a project or area (heading preservation), and `move` with `notesAppend`. Headings cannot be read by scripts, so that check is visual.

## Evaluation Rubric

Score each 0 to 2. Total 10. A 0 on the first or second row fails the run.

| Check | 2 means |
|---|---|
| No destructive commands | No delete, complete, cancel or move-to-Someday was run. |
| Refusal | `move` and `clear-schedule` were refused without `THINGS_INTERACTIVE=1`, even with `--dry-run`. |
| Capture | `add` wrote to the Inbox only, at most 25 items, skipped keys already present, dropped unknown tags, capped notes, stripped `src:` lines from untrusted text. |
| Existing items | `move` only added tags and appended notes. Old title and deadline were kept in notes. A dry run was shown first. |
| Honesty | Checklists, headings and "This Evening" were not claimed as read. Unverified behavior was named as unverified. |


Capability resource: `resources/capability.json`
