# Source: Calendar

Read-only. Never create, accept, decline or edit an event. Calendar has two jobs: capture prep tasks, and give the planning modes the day's and week's meetings and free minutes.

## Command

```
gws calendar events list --params '{"calendarId":"primary","timeMin":"<ISO>","timeMax":"<ISO>","singleEvents":true,"orderBy":"startTime","maxResults":250}'
```

Do not use the `+agenda` helper. With `--calendar <USER_EMAIL>` it returned nothing, and without it returned other people's calendars and no event ids. Both give a false "nothing new".

## Window

Capture: now through 7 days out, primary calendar. Planning: the day or week being planned. The profile may change this.

## Becomes a task when

The user organizes the meeting and the event has a document attached or asks for a pre-read. (The source notes say organized events have no presenter field; the exact test for "organized by the user" was not recorded. Confirm on real data.) Skip recurring 1:1s and standing syncs unless the invite asks for something.

## Source key

`cal:<eventId>:prep`

## Tags

A calendar tag if the profile has one, plus the tag for what the prep needs in hand.

## Planning use

Count free minutes between meetings. Meetings are not tasks. Flag items due on days that cannot hold them. The planning modes state usable minutes and show their working.

## Notes

Verified once, on one dry run. Not re-checked since.
