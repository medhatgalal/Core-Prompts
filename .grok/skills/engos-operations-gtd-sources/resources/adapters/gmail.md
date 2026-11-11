# Source: Gmail

Read-only. Never send, reply, label, archive or mark read.

## Commands

List candidates (returns message ids):

```
gws gmail +triage --max 300 --query 'in:inbox newer_than:4d' --format json
```

Read one candidate:

```
gws gmail +read --id <id>
```

Get the thread id for the source key:

```
gws gmail users messages get --params '{"userId":"me","id":"<id>","format":"minimal"}'
```

## Window

Inbox, last 2 days. On Monday, since Friday 6 AM. The profile may change this.

The query reads back 4 days so a Monday run reaches Friday; drop messages whose header date is outside the window. The command returns at most the number set by `--max`. If it returns exactly that many, the window may be cut off: raise `--max` or page, and say so under "Not checked". Never report "nothing new" from a capped result.

## Becomes a task when

A person is waiting on the user, or a deadline, payment or form is due. Not newsletters, notifications or FYI. Skip anything the user already answered. A candidate in a class the profile lists under `report_only` (for example a system notice that only asks to approve or decline) is not captured: list it under "seen, not captured" with its title and class.

Drive comment notification emails belong to the Drive comments source, not this one.

## Source key

`gmail:<threadId>`

## Tags

The tag for what the next action needs in hand (for example a computer tag if it needs a web form, an email tag only if the action is sending a reply). Add the person tag when sure. Not the source name: an email that needs a form filled is a computer item, not an email item.

## Notes

Verified once, on one dry run. Not re-checked since.
