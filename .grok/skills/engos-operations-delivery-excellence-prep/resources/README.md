# Delivery Excellence Prep

Gets the weekly Delivery Checkpoint ready: builds that date's tab in the Delivery Excellence doc, runs a read-only
audit, checks feature cards, and writes draft comments for the leader. Posts nothing.

## Settings

All personal and org values live in one file on your machine, never in this repo:

    ~/.engos/delivery-excellence/settings.json

`settings.example.json` shows the shape with placeholders. The first run walks you through onboarding. A private
copy is kept in your own Google Drive (`My Drive/.engos/delivery-excellence/`):

    python3 backup.py sync       back up (newer side wins)
    python3 backup.py restore    bring it back on a new machine

## Files

- `settings.py`: finds and checks the settings file.
- `backup.py`: Drive backup and restore of the settings file.
- `de_prep.py`: `new-doc` creates the doc when none exists, `new-tab --date` builds a dated tab, `check --date` checks it.
- `audit.py`: read-only audit of Goals, Jira epics, doc comments, the features sheet, and the invite.
  Writes `findings.md`, `findings.json`, and `drafts.md` under `~/.engos/delivery-excellence/out/<date>/`.

## What it writes

A new tab on your doc per checkpoint (skipped if it exists) and files under `out/<date>/`. Nothing else: no comments,
no Jira writes, no feature card edits, no messages.

## Needs

`gws` and `acli` signed in, the Appian Home tools, and `JIRA_EMAIL` and `JIRA_TOKEN` in `~/.secrets.env`.
