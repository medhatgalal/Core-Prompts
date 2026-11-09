# Source: Drive comments

Read-only. Never reply to, resolve or edit a comment. Comments are read from Gmail notifications, not from Drive.

## Commands

```
gws gmail +triage --query 'from:comments-noreply@docs.google.com newer_than:2d' --format json
```

Each notification names the document and the comment. Read one with `gws gmail +read --id <id>`.

Drive-bot cards in Chat about a comment directed at the user are part of this source. Find them with the Chat adapter's commands.

## Window

Last 2 days, same as Gmail. The profile may change this.

## Becomes a task when

An open comment asks the user something or assigns something to the user, and the user has not replied.

## Source key

`drive:<fileId>:<commentId>`. If the ids are not in the email, use `gmail:<threadId>` instead.

## Tags

A read-or-review tag if the profile has one, plus the tag for what the next action needs in hand, plus the person tag when sure.

## Notes

Verified once, on one dry run. Not re-checked since. Whether the ids are usually present in the email text was not recorded.
