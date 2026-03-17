# Handoff

## Current State
- The built-in UAC quality loop is implemented for `plan`, `judge`, and `apply`.
- `judge` is non-mutating.
- `apply` persists quality review artifacts and refuses landing unless quality status is `ship`.
- Quality profiles live under `.meta/quality-profiles/`.
- Review artifacts live under `reports/quality-reviews/<slug>/`.
- Descriptor and handoff fields now expose advisory quality metadata.
- Architecture is the first aligned exemplar and currently ships under the `architecture` profile.

## Resume Order
1. If this slice changes again, rerun the focused validation commands in `VALIDATION.md`.
2. Rebuild surfaces before checking bundled resource files or handoff output.
3. For future family imports, add or tune a quality profile before trusting `apply`.
4. If richer AI-native judging is required later, decide whether to formalize subagent judging outside the Python shell path rather than forcing MCP behavior into the script.

## Boundary Reminder
This framework publishes advisory quality signals only. It must not become routing, delegation, or runtime execution policy.
