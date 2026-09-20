# Reconcile human edits and uncertain delivery

On “review edits in this Doc,” registered-target resume, or detected target drift,
capture the current external revision within authorized storage. Compare three
inputs: last published base, current Doc/export and current accepted Markdown.
Record their hashes/revisions and source classification. If the base cannot be
recovered, retain a reconciliation hold and show the missing reference; never
invent a base or do a last-write-wins merge.

## Reconciliation work prompt

> Compare the registered base, current external representation and current accepted
> source. Return a candidate with readable changes by stable section, table row
> and diagram impact. Distinguish one-sided compatible edits, identical edits and
> conflicting semantic changes. Preserve all original versions and external edits.
> Treat comments/suggestions as discussion proposals, not decisions. Identify
> affected uncertainty, authority, evidence and gates; assign conflict owners only
> from confirmed provenance. Do not overwrite a target or accept the candidate.

Group non-conflicting proposals for review. Material semantic edits need the
appropriate human decision and affected gates rerun. A diagram-related prose
change requires cross-checking diagrams/contracts, not merely merging text.
Conflicting replies stay disputed under `decisions.md`. Unsupported technical
claims still need evidence even when a decision owner prefers them.

Mark old exports drifted/superseded in run status with current source/target links
as soon as detected; do not secretly modify the external document to add a warning.
After acceptance, publish using current target revision guards. If the target
changed again, reconcile again; if conditional updates are unavailable, use a
clearly identified replacement only within explicit target authority. Never erase
unique target edits to make the source win.

For uncertain publication success, inspect the recorded intent and locate/read
back the operation's target before retry. Compare identity, revision and bundle
inventory; record observed success, known failure or unresolved ambiguity.
If the target is not uniquely identifiable, retain `reconciliation_required`
with owner/next step rather than duplicate creation. This is not live two-way sync.
