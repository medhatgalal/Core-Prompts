# Start and resume

## Start procedure

Verify current runtime/task, project identity, authorized artifact home and access.
Resolve the existing project layout first; otherwise propose `planning/<task-slug>/`
inside an appropriate authorized project. Confidential material belongs in approved
private storage, never a public capability repository. Map logical homes explicitly.
Assign one conductor writer; workers get separate candidate directories.

Preserve the original request in `brief.md`; inventory sources using `sources.md`.
Show understood problem, uncertainty, proposed next step and at most three questions.
Offer AI-led, human-led or hybrid acquisition. Suggest Markdown plus HTML review;
ask target preferences only when needed. Register all required targets, including
Google Docs when requested; draft-only has no implied publication authority.
Use `questions.md` for a short-session/deeper-workshop choice and effort checkpoint.
Existing frames/pitches get a prerequisite audit and reuse of supported material,
not forced rewriting or invented previous receipts.

## Logical storage and authority

| Home | Purpose |
| --- | --- |
| `sources/index.json` | Classification, coverage, revision and permitted source references |
| `candidates/<work-order-id>/` | Unaccepted worker outputs and candidate human events |
| `accepted/<revision>/` | Immutable content manifest, question/uncertainty/decision snapshots and acceptance record |
| `state/run.json` | Sole pointer/version to the accepted snapshot |
| `state/questions.json`, `state/decisions.json` | Derived views only; never independent authority |
| `reviews/<receipt-id>.json` | Attributable review evidence bound to subjects |
| `delivery/<operation-id>.json` | Intent, destination identity, saved result and reconciliation |
| `exports/<revision>/` | Derived HTML/JSON/document representations |

These are logical homes, not invented runtime CLI arguments. At actual invocation
resolve the gate's `runtime` route from the map at
`registry(engos-quality-shaping-gate).resource_root`, read its selected `runtime.md`,
then read the resolved `scripts/shaping_run.py --help`; reconcile storage/schema with this
contract. Conceptual operations are init/status/prepare/seal/accept/reopen and
delivery-intent/delivery-record. The controller integrates exact examples only
after help exists. If required semantics are absent, report the dependency and
use `fallback`; never manually forge helper receipts.

Prepare one immutable revision containing content, source/policy bindings and all
state snapshots before switching the accepted pointer against its expected prior
version. Human replies and worker returns remain candidates until reconciliation
and acceptance. Recheck real input hashes at acceptance. Never update accepted
decision or uncertainty closure separately. Record actual host ownership limits;
an advisory helper is not an access-control boundary.

## Resume procedure

1. Verify run/project identity and accepted pointer plus its acceptance record.
   Read the referenced immutable snapshots and applicable resource revisions.
   Rebuild mismatched derived views; do not trust chat summaries or file timestamps.
2. Reconcile candidate events, current source hashes, human authority and target
   revisions. Increment generation for changed accepted content, decisions,
   relevant sources/policy/resources or authority; reopen only dependent stages.
   Receipt-only additions and unrelated source changes need a dependency check,
   not automatic invalidation. Preserve earlier history and dissent.
3. Bind each unique work order to run, stage, logical request and attempt. Identical
   already-accepted replay returns its existing receipt; a different return for
   that accepted work order is a conflict. Retain stale results without advancing.
   An uncertain/partial transaction is `recovery_pending`, never guessed success.
4. Read delivery intents before retrying writes; uncertain success requires target
   lookup/readback, not duplicate creation. Load `reconcile` for external edits.
5. Orient the user with current stage, settled decisions, changed facts, unresolved
   blockers and next action. Resume at the earliest affected unaccepted stage;
   skip already answered questions unless material evidence changed.

At an effort limit or absent human, finish independent work within the bound and
return a hold with owner/next action. Do not silently extend the budget or poll for
consent. Record actual human effort, elapsed/active time and model cost when available,
including repair; unknown measurements remain unknown.
