# Source: Chat

Read-only. Never post, react or mark read.

## Commands

List spaces (prints one JSON document per page, NDJSON; parse with `jq -s`):

```
gws chat spaces list --params '{"pageSize":1000}' --page-all
```

Keep spaces whose `lastActiveTime` is inside the window. Then, per space:

```
gws chat spaces messages list --params '{"parent":"spaces/<id>","filter":"createTime > \"<ISO>\"","pageSize":500}'
```

Fetch spaces in parallel with a small script, not one long `xargs` line. A full run is slow, mostly here.

## Window

Same as Gmail: last 2 days, Monday since Friday 6 AM. The profile may change this.

## Becomes a task when

The message is in a direct message or mentions the user, is not from the user, and is unanswered: no later message from the user in that DM, thread, or (in spaces without threads) space. A direct ask, an unanswered question to the user, or a promise the user made.

Drive-bot cards about a comment directed at the user belong to the Drive comments source.

To tell which messages are from the user, use `<USER_ID>` (format `users/<number>`), looked up from the user's own profile:

```
gws people people get --params '{"resourceName":"people/me","personFields":"metadata"}'
```

The id is in `metadata.sources[].id`; prefix it with `users/`.

## Source key

`chat:<spaceId>:<messageId>`, using the two ids from `spaces/<spaceId>/messages/<messageId>`.

## Tags

The tag for what the next action needs in hand (a chat tag if the answer is a Chat message). Add the person tag when sure.

## Notes

Verified once, on one dry run. Not re-checked since.
