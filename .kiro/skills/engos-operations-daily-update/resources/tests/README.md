# daily-update skill tests

These tests re-check the skill after it changes, without a person checking the doc by hand. Leaders do not
need to run them. They write only to new Google Docs whose title starts with "E2E TEST", shared with the
person running them.

## Run

```
sh run_full.sh
```

It creates a fresh test doc, plays two days for every persona (doc owner, leaders, cover, close, send draft),
then prints the rule checks (`../scripts/verify.py`) and reader checks (`../scripts/usability.py`). It never
sends anything: the send step is a draft.

Needs `gws` signed in. The tester's address comes from `DU_TEST_EMAIL`, or the signed-in `gws` user if unset.
Docs listed in `~/.daily-update/protected.json` are never written.

## Files

| File | Purpose |
|---|---|
| `run_full.sh` | The full run described above |
| `exploratory.py` | Creates the doc and plays day one, including traps (vague dates, candidate names, raw links, editing another person's tab) |
| `day_mon_nov9.py` | Day two: add, move, cover, finish, and three refusals |
| `rules_test.py` | Offline: status rules, pre-publish check (warn vs block), stale-date check, Missing a plan, short labels, migration colour mapping |
| `cli_test.py` | Offline: the initiative lifecycle table, who may do what, name matching, validation, source CRUD on a throwaway config, and the noun-verb grammar (every old command name is refused) |
| `feedback_test.py` | Offline: Feedback tab entry lint, format, newest-first insert, first-entry replace, duplicate skip, nothing outside the list touched |
| `backup_test.py` | Drive backup: first backup, no bounce, restore on a clean machine, newer side wins, Drive outage. Uses a throwaway "E2E TEST .engos" folder and trashes it after |

When a skill rule changes, change the matching script and add a check to `verify.py`. Confirm the new check
fails before the change and passes after it.
