# engos-design-presentation-progress-plan

Status: preserved reviewed plan, contract v1 retained. Implementation and local
visual checks now exist; see engos-quality-presentation-progress-verification.md
for current evidence and remaining gates. This plan is not itself a completion
receipt. Extends the reviewed full-shaping plan without replacing its gates.
Source baseline 75a1b1f164f6eedd589818cc8ea4ac84aa436f78 in the existing isolated
AI/engos-full-shaping-design worktree. Main remains read-only.

## Approach Decision

Improve two separable concerns: reference-matched document presentation and an
evidence-derived flow progress view. Reuse the conductor, gate runtime and embed
adapter. No new agent product, tracker, dashboard service or always-running swarm.
User requested how to improve, execute, verify and expose status/progress; this
document defines that next slice, not a claim that it has already shipped.

## Complexity Diagnosis

The exporter currently prints a broad Markdown subset into a minimal HTML shell;
the pilot's 13-column contract table wrapped into unreadable fragments. Rich source
coverage did not establish a rich reading experience. Source reference comparison
mostly covered content/structure, not matched rendered pages. Runtime status already
reports accepted stage, version/generation, drift, content readiness, deliveries
and work orders, but not a friendly current-action/owner/next-step view. A visually
green document can be confused with a passed gate or a fresh observation.

## Decomplect Plan

1. Preserve canonical meaning and stable section/row/diagram IDs separately from
   layouts. Keep audit/register detail available without making it the reader's
   primary experience. Do not turn tables into bitmap text.
2. Derive progress from current accepted receipts, pending work orders, unresolved
   questions/decisions and separately recorded host observations. Do not hand-edit
   an independent progress file as a second truth.
3. Keep content acceptance, presentation acceptance, target placement, actual human
   betting authority and code/release delivery distinct.

## Refactored Artifact

### Presentation

First render the actual reference Docs/site and the current candidate side by side
within approved private storage. Establish a visual acceptance sheet covering
heading hierarchy, density, color roles, section rhythm, figure placement, caption
and legend treatment, compact contract/security tables and negative space. Preserve
which references were supplied and which were discovered; do not assert an
unconfirmed pair is the exact intended sample.

Framed template: clear problem/scenario, why-now, appetite/walk-away, In/Out/Later,
decisions and open questions, no proposed architecture. Shaped template: concise
decision summary, cohesive narrative, diagrams beside the explanations they support,
readable primary tables, detailed contract fields linked by stable row ID in
supporting sections, explicit risks/no-gos and readiness/decision panel. Preserve
all required fields and meaning; fewer primary columns must not discard evidence.

Maintain Mermaid as editable source where appropriate. Produce durable SVG and
high-resolution PNG derivatives with source hashes. Use SVG in HTML with accessible
captions and full-size viewing; PNG inline in Google Docs with native editable
tables. Retain house Docs Title18/H113/H211.5 and semantic colors. Local SVG/PNG
assets can avoid a mandatory runtime CDN fetch; generation must report renderer
availability and failure honestly. No raster screenshot of tables as a substitute.

### Progress view

One compact status card in conversation, a generated Markdown/HTML view and a
machine-readable JSON projection from the same run record. Show:

- run name/ID, revision, real versus simulated evidence, requested stopping point;
- Intake → Framed → Research → Shaped → Bet-ready, with each gate's current state;
- current work/action, responsible role and actual assigned actor if available;
- reason for any hold, precise resource/answer needed, expected respondent and
  next permitted action; unassigned owners remain unassigned;
- links to latest draft and latest accepted artifact, clearly distinguished;
- content review, visual review and every requested target's placement separately;
- decisions/uncertainties resolved versus still blocking, plus evidence links;
- investment appetite separately from interview/checkpoint effort;
- snapshot time, last verified source/target revision and last observed activity.

States: not reached, active, awaiting input, blocked, review pending, changes
requested, verified, stale or stopped. These are a presentation vocabulary, not
new ways to waive gates. No state is inferred from file existence, an author flag,
elapsed time, job title or silence. An old verified stage remains historical but
loses current green status when a dependency changes. Missing/corrupt state is
unverifiable, not a green empty dashboard.

Host activity is observational, never acceptance authority: dispatched, started,
candidate returned, review requested, accepted, held, reopened and delivery result
must bind run/version/generation/work-order/attempt and actual host observation.
Use the existing controller-owned versioned state/event mechanism; do not make a
parallel mutable database. Older runs without activity events show activity unknown.
Out-of-order/duplicate/late observations cannot alter acceptance or revive stale
attempts. Absence of a recent event means activity unknown/stale, not proof a worker
is hung. Phase acceptance and task liveness are different indicators.

Refresh on recorded workflow events, explicit status requests or resume. A generated
HTML file is an as-of snapshot, not a continuously monitored live service. No new
scheduled monitoring, public hosting or automatic Google Doc updates are implied.
If an external status copy is requested later, preserve target authority, revision
checks and external edits. Show counts such as 2/5 gates verified, never imply 40%
of effort or invent completion times.

## Inversion Analysis

Failure modes to test: polished unsupported content; truncated tables; tiny/clipped
figures; stale approval remaining green; simulated decisions displayed as real;
an unavailable agent displayed as running forever; a failed upload displayed as
complete; mismatched snapshots mixing generations; unsafe source HTML/links; host
restrictions accidentally reclassified as user product requirements.

## Dogs Not Barking

No browser error does not mean readable. No recent activity does not prove failure.
No disagreement does not establish approval. A compact history API can omit actual
tool output (observed in the role pilot); resolve disputed coverage with raw events.
An existing PDF/image does not prove it corresponds to the latest approved source.

## Guarded Forward Solution / execution order

A. Capture visual reference baseline; freeze the visual checklist and representative
short/long/wide-table/large-diagram fixtures before repair.
B. Repair artifact formatting and export paths with failing-then-passing tests;
keep source semantics unchanged. Fix the identified renderer-launch test spy.
C. Add the read-only progress projection and narrowly required controller activity
observations, preserving existing default JSON CLI behavior and old-run compatibility.
D. Update relevant canonical skill/resources through same-slug UAC; regenerate
provider bundles. Make entry, stopping conditions, event ownership and status
commands discoverable in the runbook/examples.
E. Exercise positive and failing cases; independent code and visual reviewers,
then a fresh bounded six-role rerun focused on changed behavior. Do not reuse old
scores or the prior Doc's placement as proof for a new bundle.
All B/C edits begin in canonical source/resources, never generated or installed
surfaces. D is the dependent regeneration/documentation checkpoint, not permission
to postpone canonical ownership. F. Carry only a passing candidate through existing full regression/strict checks,
GitHub PR and GitLab MR exact-head checks, main parity and scoped cleanup. Release,
installation, external publication and real team betting remain separately scoped.

## Contract Spec v1

[CONTEXT] User's visual-quality correction and request for understandable flow
progress; original gated-shaping acceptance remains authoritative. Existing runtime
status and role-pilot observations are implementation evidence, not completion.
[INTENT] A person can read a useful, reference-quality document and tell what is
accepted, what is happening, what they owe, and why advancement stopped.
[SPEC] R1 reference-matched typography/layout; R2 durable SVG/PNG; R3 full readable
native tables; R4 trustworthy stage/activity/owner/action projection; R5 freshness,
reopen and simulation distinctions; R6 demonstrated checks and documented delivery.
[CONSTRAINTS] No invented evidence/owners/percentages; no second state authority;
no removed required content, solution in framing, implicit sharing/hosting or new
native agents. Escape untrusted text and validate output links/paths. Keep private
reference content and pilot records out of public source reports.
[ACCEPTANCE]
- R1–R3: compare actual reference/candidate screenshots, not extracted counts.
  Inspect all pages in representative PDF/Docs outputs and all diagram/table regions
  at narrow and wide HTML sizes. No clipped labels, broken word columns or missing
  rows; native tables retained; derived files match original source identities.
- R4–R5: deterministic cases for every displayed state; invalid/missing/corrupt
  evidence cannot yield verified. Changed frame/source/policy invalidates exactly
  applicable status; delivery-only failure does not discard valid content approval.
  Crash/resume, duplicate/late results, missing liveness, external edits and mixed
  generations display honest state. Real and simulated runs cannot be conflated.
- R6: isolated reviewers inspect actual outputs and tests; six-role follow-up checks
  that participants identify current stage, blocker, owner and next step without
  interpreting operational JSON. Record limits; structural/source tests do not prove
  real-human usability or all-provider behavior. Exact new external targets require
  their own write authority and saved-target readback.

## Why This Is Simpler

The same accepted content can change layout without reopening framing; one status
projection can change appearance without changing acceptance. A failed target
upload affects placement, not unrelated product decisions. No additional agent
roster or always-on status service is needed.

## Trade-offs / Residual Risk

Progress is only as fresh as observed events and target readback; show timestamps
and unknowns. Automated layout checks cannot replace visual judgment. Shared-model
role tests remain simulation. Exact reference matching must preserve accessibility,
source meaning and surface constraints, rather than copying defects in an exemplar.

## Examples (illustrative, not current run receipts)

1. Intake verified; Framed awaiting product input: appetite missing, owner unassigned,
   next step identify the investment decision-maker. Research not reached. No ETA.
2. Shaped content verified at revision 4; HTML verified; Google Doc blocked on target
   permission. Overall Bet-ready pending. If only target access changes, do not
   restart framing. If the source contracts change, mark dependent review stale.

## QA Evaluation JSON

Independent reviewer 01a0b3e5-6ea2-7791-8d34-2ecdb405a6d3 returned 83/100 for plan
coherence, no critical escalation, with concrete prerequisites rather than runtime
approval. The exact response is preserved in the companion
engos-quality-presentation-progress-plan-review.json. These clarifications respond
to that review; they do not retroactively change its score or imply re-review.

## Clarifications after the independent review

### Reference and visual acceptance sheet (required before renderer edits)

Record exact source Docs revisions and docs-site commit, plus approved private
render captures. Label discovered references separately from supplied references.
Required fixtures: solution-free frame, short shaped pitch, long shaped pitch,
the actual 13-column failure, long labels/sequence and missing/mismatched assets.
Proposed engineering test viewports: 375, 1280 and 1920 CSS pixels; print and Docs
at recorded paper size and 100% view. These are test defaults, not user mandates.
Judge legibility at normal size, repeat table headers across pages, prevent
broken-word columns and unreachable content; allow clearly signposted full-size
figures/detail views rather than shrinking text to force a fit. Keep native tables.
Accessibility checks use semantic headings, text alternatives, keyboard-reachable
figure/detail links and at least 4.5:1 ordinary text / 3:1 large-text contrast as
proposed test thresholds. Preserve house Docs heading sizes. If a reference would
violate readability/accessibility, document the deviation for independent visual
review; unresolved conflicts go to the user, not hidden style drift.

### Asset and table contracts

Each figure has a stable diagram ID and explicit document-section anchor; missing
anchors fail validation rather than silently putting all diagrams at the end.
The asset manifest binds Mermaid/source hash, renderer version/config, SVG/PNG
hashes/dimensions, caption, alternative text and owning section. Use locally bound
assets for a self-contained export where generated; require a successful offline
load test before calling that export self-contained. This is an adapter option,
not a new offline requirement imposed on every product pitch.

Only trusted renderer output with validated SVG is embedded: reject active scripts,
event handlers, external resource references and unsafe URL schemes. Configure a
supported safe text-label path, or report unsupported content; do not silently
embed arbitrary supplied SVG. Verify asset path containment and source/hash match.

Primary contract view groups ID/interface/purpose/state/owner; supporting sections
retain each remaining producer/consumer/input/output/error/retry/consistency/security/
evidence field keyed by the same ID. The conversion must enumerate and compare every
original cell/field; reject unrecognized fields instead of dropping them. Security
summary retains Responsibility/Owner/How-enforced, with all remaining fields linked.
Cross-links, row IDs and native Docs table cells are checked after placement.

### One deterministic status projection

Overall `status: consistent` from the current helper means storage consistency,
not readiness. All human views consume one versioned projection, never reinterpret
that string independently. Snapshot integrity failure yields unverifiable first.
Requested stopping point determines applicable gates: after a framing-only finish,
G2–G4 are outside requested scope, not failed or incomplete requested work.

For each applicable gate, priority is: stale dependency → current failed review
(changes requested) → unresolved confirmed prerequisite/access failure (blocked)
→ unanswered required decision (awaiting input) → sealed candidate with pending
review (review pending) → current verified receipt (verified) → observed current
attempt activity (last observed active) → dispatched order (queued) → not reached.
The implementation must reconcile conflict cases against actual receipts and
current work-order generations; observational events cannot revoke or grant an
acceptance. Stopped activity is a separate indicator and does not erase a valid
completed gate. Display a claimed actor only with controller assignment provenance;
otherwise owner/actor unknown. Always show the observation time, not an invented
continuous-liveness guarantee. Invalid observations are rejected and exposed.

Compute latest accepted artifact state separately from pending draft/activity state.
The precedence above applies only to events/requirements bound to the relevant
current gate attempt and subject; an optional new draft or its failed review must
not repaint an unchanged accepted revision as unapproved. Display both when useful:
"revision 4 accepted; revision 5 draft needs changes." Conflicting assessments of
the same subject are review conflicts to resolve, not arbitrary last-writer wins.

Use the gate runtime's authoritative invalidation, including conservative policy
rebinding; no narrower policy override is introduced by the view. Source-contract
changes invalidate dependent content/visual/target results. Layout-only outputs
invalidate their visual/placement receipts without changing canonical prose.
Target-only access/failed placement cannot revoke unchanged G3 content. Distinguish
local evidence integrity from remote freshness: 'verified at target revision X,
last read Y' is not 'remote unchanged now'. Changed source and changed target show
separate causes and next actions. Test old runs, partial receipts and conflicting
events before mapping anything to a green status.

### Obligation-to-evidence mapping

| ID | Source obligation | Independent acceptance owner | Required evidence |
| --- | --- | --- | --- |
| R1 | User's samples/formatting correction | Visual reviewer | Versioned reference/candidate screenshots and visual checklist |
| R2 | User's PNG/SVG request; original editable-source constraint | Visual and code reviewers | Source/asset manifest, safe-SVG tests, full-size and offline-option render observations |
| R3 | Original exemplar tables; observed wrapping failure | Visual reviewer plus parity checker | Every-field mapping, 13-column regression, saved native-cell/row readback |
| R4 | User asks status/progress for any given flow | Runtime/code reviewer | Deterministic projection cases, owner/action provenance, matched Markdown/HTML/JSON |
| R5 | Original gates and no invented advancement | Runtime reviewer | Drift/reopen/late-event/partial-run/remote-freshness negative controls |
| R6 | User asks execution and verification, original main delivery | Independent reviewers and controller | Exact candidate identity, test/render/role receipts, docs, hosted checks and remote parity |

New Docs validation requires an expressly approved exact private payload/target.
The prior teaching Doc approval does not authorize a different upload or overwrite.
Until such authority exists, complete local checks and retain saved-Docs proof as
pending; no public sharing, alternate upload route or fabricated target evidence.
