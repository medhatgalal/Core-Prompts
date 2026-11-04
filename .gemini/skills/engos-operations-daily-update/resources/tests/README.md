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

When a skill rule changes, change the matching script and add a check to `verify.py`. Confirm the new check
fails before the change and passes after it.
