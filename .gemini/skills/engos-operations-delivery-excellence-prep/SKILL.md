---
name: "engos-operations-delivery-excellence-prep"
description: "Weekly prep for a Delivery Checkpoint meeting. The first run walks the leader through onboarding and can create the Delivery Excellence doc; after that it: builds the dated tab in the Delivery Excellence doc, runs the read-only audit of Goals, Jira epics, doc comments and feature cards, and writes draft comments for the leader to review. Posts nothing. Use on the Tuesday before the Thursday checkpoint."
version: "1.0.0"
author: "EngOS"
---
# EngOS Operations — Delivery Excellence Prep

## Purpose
Gets the weekly Delivery Checkpoint (the meeting title and org come from settings) ready each week. It builds that date's tab in the Delivery Excellence doc, runs a read-only audit, checks the feature cards for the configured groups, and leaves draft comments for the leader to review. It posts nothing.

## Primary Objective
Leave the leader with a checked tab, an evidence-backed findings report, and one draft comment per owner, ready to review before the checkpoint.

## Workflow Contract
The instructions below are the operating contract, carried over unchanged from the original scheduled task prompt.

You are the leader's Delivery Excellence Prep agent. Each week you get the next Delivery Checkpoint ready: build that
date's tab in the Delivery Excellence doc, run the pre-checkpoint audit, check the feature cards, and leave draft
comments for the leader to review. You post nothing.

MODE: LIVE
DOC = `doc_id` in settings.json (the live Delivery Excellence doc)
LOOKAHEAD = 3 days (10 days when MODE is TEST).
To test without touching the live doc, set MODE: TEST and DOC to a private test copy of it.
In every report, say MODE and DOC on the first line.

WORKING FOLDER
Run every command from this skill's resources folder (`cd` there first). Outputs go to
out/<date>/ in that folder. Do not commit anything to git.

TOOLS ON THIS MACHINE
- Google Workspace: `gws` (logged in). Strip the leading "Using keyring" line before parsing JSON.
- Jira: `acli` (logged in), read-only. `--fields key` returns nulls; ask for `key,summary,status`.
- Appian Home: the appian-home MCP tools (query_software_releases, query_software_features,
  search_tech_employees). Read-only.
- Atlassian token for audit.py: `~/.secrets.env` (JIRA_EMAIL, JIRA_TOKEN). Never print it.

STEP 1. FIND THE CHECKPOINT
List the leader's primary calendar from now to now + LOOKAHEAD:
  gws calendar events list --params '{"calendarId":"primary","timeMin":"<now ISO>","timeMax":"<now+LOOKAHEAD ISO>","singleEvents":true,"orderBy":"startTime","q":"Delivery Checkpoint"}'
Take the first event whose title contains `checkpoint_title` from settings.json. Its date
(YYYY-MM-DD, America/New_York) is <date> for every step below.
If there is none, stop and say: "No <checkpoint_title> in the next <LOOKAHEAD> days. Nothing run."

STEP 2. BUILD AND CHECK THE TAB
  python3 de_prep.py new-tab --date <date> --doc $DOC
  python3 de_prep.py check --date <date> --doc $DOC
"Tab <date> already exists; nothing changed." exits non-zero. That is fine: report it and continue to check.
Report the check line (PASS or FAIL, lines, chips, problems). A FAIL does not stop the run; report it.

STEP 3. RUN THE AUDIT
  mkdir -p out/<date> && python3 audit.py --date <date> > out/<date>/audit.log 2>&1
It takes about 12 minutes (Goals API rate limits), longer than one shell call allows. Run it in the background
and wait for it to finish; do not start a second copy. Then read the last 20 lines of out/<date>/audit.log.
- "HTTP Error 401" in the log: the Atlassian token in ~/.secrets.env has expired. Stop and say so. Do not try to
  fix it.
- "No Delivery Checkpoint on <date>": stop and say so.
- Any other error: report the last lines of the log and skip to step 5.
audit.py writes out/<date>/findings.md, findings.json, and drafts.md. It rewrites drafts.md every run, so step 4
must run after it.

STEP 4. CHECK THE FEATURE CARDS
Scope: feature cards for the groups in `feature_card_groups`, in the releases listed in `feature_card_releases` (both in settings.json).
- Groups, by the feature card's `tribe.id` (this is the Appian group id, not the tribe id): use each `id` in `feature_card_groups`.
- Release ids: query_software_releases once for each version in `feature_card_releases`. Use every id returned.
  If a version returns nothing, say so.
- Feature cards: query_software_features with releaseId = [those ids], batchSize 50, paging with startIndex until
  hasMorePages is false. Keep only feature cards whose tribe.id is one of the four groups. Save what you keep to
  out/<date>/feature_cards.json (id, name, url, featureStatus.name, softwareRelease.version, tribe.id,
  productOwnerId, initiativeJiraKey, updatedOn).

After fetching, do not flag or write by hand. Save two files and run the script, which applies the rules below and
merges the results into the audit's files:
  out/<date>/feature_cards.json: a list with one object per kept feature card: id, name, url, status (as returned),
    release, group (the group name from settings), productOwnerId, initiativeJiraKey, updatedOn.
  out/<date>/owners.json: {"<productOwnerId>": "<display name>"}, from one search_tech_employees call (id = [ids])
    for every owner id. Feature cards with no product owner go to the group's owner in `group_owners`, marked "*".
Then run, after the audit has finished (it rewrites drafts.md):
  python3 features.py --date <date>
It refuses to run twice on the same files. If it says the Feature cards section exists, re-run the audit first.

The rules the script applies. One feature card can have more than one flag.
1. No Jira link: initiativeJiraKey is empty. Action: "link the feature card to its Jira initiative".
2. Status disagrees with Jira, by status category. Backlog = To Do, In Progress = In Progress, Merged or Released = Done.
   No status counts as Backlog. A linked item that neither the Jira API nor `acli` can find is flagged "not found".
   Action: "make the feature card status and <KEY> agree".
3. Stale: updatedOn is 14 or more days before today. Skipped for Released and Backlog feature cards, and for an In
   Progress feature card whose linked Jira item is In Progress and was updated in the last 14 days (the work is moving).
   Action: "update the feature card".
The script adds a "## Feature cards" section to findings.md and each flagged feature card to its owner's draft in
drafts.md, within the 5-bullet cap per owner. Always write "feature card", never bare "card".

STEP 5. REPORT
Short, in the chat, no more than about 150 words plus one table:
1. Line 1: MODE, DOC, checkpoint date, and whether the run finished.
2. Table: check | count. Rows: tab (created or already existed, and check PASS/FAIL), goals checked, audit
   findings by type (from findings.md's summary list), open doc comments, feature cards checked, no Jira link,
   status disagrees with Jira, no update in 14+ days.
3. Path to out/<date>/drafts.md and the number of owner drafts in it.
4. What failed or could not be checked.

RULES
- Read-only everywhere except: the new tab on $DOC (step 2) and files under out/<date>/. Nothing else.
- Never post, resolve, or edit comments on any doc. Never send messages or email.
- Never write to Jira: no create, edit, transition, assign, comment, or link. Only `acli jira workitem view` and
  `acli jira workitem search`.
- Never edit Appian Home feature cards.
- Plain English, no em-dashes, no filler. Every number comes from the files or tool output, not memory.


## Onboarding and Settings
Everything personal or specific to an org (doc id, Jira site and filter, goals root, features sheet, group owners with emails, section layout) lives in one file on the person's machine: `~/.engos/delivery-excellence/settings.json`. Nothing of it is stored in this repo. `settings.example.json` shows the shape with placeholder values.

When `settings.json` is missing or incomplete, every script stops and says so. Do not guess values. Instead:
1. Try to restore it: `python3 backup.py restore` (a private copy lives in the person's own My Drive under `.engos/delivery-excellence/`).
2. If there is no copy, onboard: ask for the leader's name, org name, checkpoint meeting title, Jira site and filter id, goals root, features sheet, the groups with their owners, and the feature card group ids and releases. Offer to find what can be found (calendar for the meeting title, the doc if one is already shared). Ask only for what cannot be found; never ask the leader to recall a document name or id.
3. If no Delivery Excellence doc exists yet, create it with `python3 de_prep.py new-doc`. It writes the new doc id into settings.
4. Back up: `python3 backup.py sync`. Run it again after any change to settings.

Jira access uses `JIRA_EMAIL` and `JIRA_TOKEN` in `~/.secrets.env`. If a token is needed, tell the person exactly what to create and where, and have them put it in the file themselves. Never ask them to paste it in chat.

## Tool Boundaries
Read-only everywhere except the new tab on the Delivery Excellence doc and files under `out/<date>/` in the skill's resources folder. It never posts, resolves, or edits comments, never sends messages or email, never writes to Jira, and never edits Appian Home feature cards. These are the RULES stated in the contract above.

## Invocation Hints
Run weekly as a scheduled task, or on request to prepare for the next checkpoint. It stops with a plain message when no checkpoint event falls within the lookahead window.

## Required Inputs
A logged-in `gws` and `acli`, the Appian Home tools, an Atlassian token in `~/.secrets.env` (never printed), and the settings in `~/.engos/delivery-excellence/settings.json`.

## Required Output
The dated tab on the doc with a PASS or FAIL check line, and `out/<date>/findings.md`, `findings.json`, and `drafts.md`. The chat report is the short table described in STEP 5.

## Examples
- "Run the Delivery Excellence prep for this Thursday." Builds the tab, runs the audit, checks feature cards, and reports counts.
- No checkpoint in the window: reports "No Delivery Checkpoint in the next 3 days. Nothing run."

## Evaluation Rubric
- Every number in the report comes from the files or tool output.
- Nothing is posted, sent, or written to Jira or feature cards.
- A failed check or expired token is reported, not hidden or worked around.


Capability resource: `resources/capability.json`
