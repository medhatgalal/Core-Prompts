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
| `shape-set.json` | Current-policy selected piece IDs, walk-away item if empty, existing/proposed-extension claims, load-bearing flag and exact opened evidence/basis claim references; no-selection holds before scoring |
| `journal.md` | Attributable actual iterations, decisions, holds, repairs and resource/revision changes; no reconstructed successful history |
| `pitch-report.json` | Machine-readable pointers to source revision, inventories, content/review and per-target delivery status; not an independently edited pitch |
| `no-gos.md` | Load-bearing forbidden paths, rationale/evidence, affected seams/slices, decision authority and stop conditions |
| `evidence-ledger.md` | Claim/evidence ID, source/revision/locator, coverage, fact/proposal/opinion/observation, inspection mode, limitations and unresolved status |
| Source-content manifest | Artifact IDs/paths and actual hashes; full prose sections, row IDs/counts and diagrams/captions; upstream binding; separate render/placement receipts to avoid recursive hashes |

## Architecture-fit decision

For material technical capabilities/seams, pitch.md includes the architecture-fit
decision from architecture-fit.md: existing evidence IDs, credible options,
disposition and rationale, relevant constraints, and applicable evolution/validation
boundaries. Reuse, justified new work and intentional separation are valid outcomes.
Keep these decisions consistent with diagram roles and contract ownership; no
second inventory or exhaustive option matrix is required.

## Conditional layer sizing

Only when the team already sizes by layer, include its existing names and scale
in pitch.md or workstreams.md. Record each layer's owner, size and evidence or
attributable estimate, or the explicit non-involvement decision. A blank size is
unknown and remains a gap. Do not invent a layer taxonomy, capacity formula or
staffing commitment; omit this section for teams that do not use layer sizing.

## Required diagram fields

`component.mmd`: components, callers, ownership boundaries and seams.
`sequence.mmd`: real sequenceDiagram for representative request/event and stop,
with separate failure sequences as needed for the limited renderer (no alt/else).
`data-flow.mmd`: movement, transformations, persistence and trust boundaries.
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
a load-bearing seam. The interface entry is a cited network interface, an identified
in-process interface, or the exact token no API. Network methods and endpoints need
source evidence. For a no API interaction, the full data contract remains required.
Use no API only for an interaction without an API. An unknown or uninspected
interface remains a research gap.
Input meaning, output meaning, producer, consumer, state, evidence and owner remain
required. Mark proposed behavior as proposed with its supporting evidence; never
invent a method, path or schema or present a proposed interface as observed.
Retain Method/Purpose where applicable. Compare every material row with its matching
diagram interaction; unexplained differences are gaps, not builder discretion.

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

Before the table, prepare the proposed build/deferred/forbidden lists, including
one proof sentence per in-item and a reason plus separate-pitch requirement for
every deferred item. This is shaping scope, not a spec, requirements document,
design, architecture document, plan or tasks. After a table Accept, write exactly
one handover using handover.md and ask for its selected outputs. A split creates
smaller pitch candidates and no build handover until one is accepted.

The agent record names the exact package revision and source inventory, accepted G3
receipt (or pending review), requested delivery status, attributable human bet
decision (or pending decision), appetite/scope, no-gos, unresolved gaps and next
permitted action. Carry conditional layer sizing only where used by this team.
Keep skeleton observations, mocks and limits separate from planned integration
checks and from design/build authority. A document link or a person's yes cannot
substitute for these records; handoff preparation starts no downstream work.
