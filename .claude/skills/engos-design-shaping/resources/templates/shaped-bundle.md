# Shaped bundle field template

Create only reached-stage outputs. Preserve stable section, table-row, diagram,
claim and evidence IDs across representations. Markdown is human-editable source;
proposed edits create candidates, never overwrite an accepted immutable revision.
Unknown fields are gaps, not invitations to fill plausible values.

| Artifact | Required fields/content |
| --- | --- |
| `pitch.md` | Title; contributors/authority; problem and why-now; guiding use case/business win; observable success; actual appetite/walk-away and decision IDs; bounded solution/macro flow; alternatives and reasons; dependencies/decoupling; integration evidence; In/Out/Later; ordered safe cuts; risks/mitigations/owners; No-Gos and objective kill criteria |
| `pitch-summary.md` | Same outcome, appetite, solution, key trade-off, uncertainty/readiness and evidence links without new claims |
| `workstreams.md` | Provisional coarse workstreams, responsibilities/non-responsibilities, ready/needs_spike/excluded with evidence or exclusion decision, first observable slice, dependencies and No-Gos; no tickets or invented commitments |
| `traceability.md` | Original requirement/decision -> frame -> research evidence -> solution/diagram/table/slice -> review; explicit unresolved gaps |
| `journal.md` | Attributable actual iterations, decisions, holds, repairs and resource/revision changes; no reconstructed successful history |
| `pitch-report.json` | Machine-readable pointers to source revision, inventories, content/review and per-target delivery status; not an independently edited pitch |
| `no-gos.md` | Load-bearing forbidden paths, rationale/evidence, affected seams/slices, decision authority and stop conditions |
| `evidence-ledger.md` | Claim/evidence ID, source/revision/locator, coverage, fact/proposal/opinion/observation, inspection mode, limitations and unresolved status |
| Source-content manifest | Artifact IDs/paths and actual hashes; full prose sections, row IDs/counts and diagrams/captions; upstream binding; separate render/placement receipts to avoid recursive hashes |

## Required diagram fields

`component.mmd`: components, callers, ownership boundaries and seams.
`sequence.mmd`: representative request/event path with relevant alternative/failure
paths. `data-flow.mmd`: movement, transformations, persistence and trust boundaries.
Each has a caption, legend, evidence refs, existing/proposed/unknown labels and
explicit omissions. Keep negative responsibilities visible. Render receipts bind
source hash, renderer, saved image and observed pixels/limitations; parser success
does not prove legibility.

## Full contract table fields

Stable row ID; Direction (provided/required); Method/Endpoint (or in-process
interface); Purpose; producer; consumer/caller; input/parameter meaning and bounds;
output/response meaning; material errors; timeout/retry/idempotency; consistency
and persistence; trust/access boundary; lifecycle/version expectations where
material; contract state; evidence; owner/action; explicit non-responsibility.
Use reasoned not-applicable for irrelevant semantics, never blank cells concealing
a load-bearing seam. Mark proposed interfaces as proposed with cited precedent;
do not pretend new methods exist. Retain the exemplar Method/Purpose shape.

## Security-owner matrix fields

Stable row ID; Responsibility; Owner; How enforced/control; enforcement location;
trust/data boundary; evidence/state; non-responsibility and actual responsible
component; unresolved gap and next action. Keep unknown owners explicit.

## Proof and betting preparation

Pitch-wide proof slice and each workstream's first slice: outcome to observe,
boundary/seam, evidence required, current evidence versus future acceptance check,
dependencies, effort within appetite and stop condition. A proposed check is not
an executed spike. Do not equate future implementation acceptance with shaping proof.

After G3, `betting-table-prep.md` contains a one-minute pitch, key trade-off,
appetite, review checklist, three evidence-backed hard questions and handoff.
It is a local sidecar unless requested on target. Any new substantive claim
requires content reconciliation and affected review, not a publishing shortcut.
