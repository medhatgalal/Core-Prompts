# Evidence-derived progress

`shaping_run.py progress` reads one committed controller revision and emits the
same versioned projection as JSON (default), Markdown, or HTML. It does not write
run state, contact a target, dispatch work, or monitor continuously. Existing
`status` keeps its default JSON interface; `status: consistent` means storage
consistency only. A missing/corrupt journal produces `unverifiable`, zero verified
gates and exit 3 in every progress format. Source drift produces explicit stale
states, not acceptance. Valid projections exit 0 even when work is blocked.

For an ordinary status read, this reference and the helper's actual help are
sufficient; the progress route does not force an implementation-code read.
Use progress-tools when authoring/validating observation payloads or inspecting
the schema/code. All resources remain bundled; neither route grants write authority.

Run these commands from the installed resource root, replacing the illustrative
run and observation paths with controller-owned inputs:

```sh
python3 scripts/shaping_run.py status --run /private/tmp/shaping-demo
python3 scripts/shaping_run.py progress --run /private/tmp/shaping-demo
python3 scripts/shaping_run.py progress --run /private/tmp/shaping-demo --format markdown
python3 scripts/shaping_run.py progress --run /private/tmp/shaping-demo --format html
python3 scripts/shaping_run.py progress --run /private/tmp/shaping-demo --format json --as-of 2026-09-18T12:00:00Z --activity-max-age-seconds 900
```

Output is stdout; the caller chooses an authorized destination. HTML/Markdown
artifact links are relative to the run root: place a saved view there or resolve
those references against that root in the consuming adapter. The latest accepted
link opens the immutable snapshot containing exact artifact bytes; the draft link
opens its assigned candidate directory. Destination labels are plain text, never
automatically clickable URLs. Paths reject traversal, symlinks, unsafe schemes,
URL delimiters and control characters. Text is escaped, including embedded source
HTML and Markdown link syntax. The static HTML uses no script or external assets.

`--as-of` supplies the observation-age comparison and snapshot label for
reproducibility; it does **not** reconstruct an old revision. Omit it for a current
read. Reads assume the documented runtime's quiescent source-writer boundary.
The 900-second default is an adjustable observation freshness window, never a
worker timeout, ETA, or claim that an unobserved worker is hung.

## Provenance and requested scope

Legacy runs remain readable without migration: evidence mode, activity, requested
stop and unknown timestamps stay unknown. The controller may record missing
context using `progress-context --spec PATH --expected-version N`. Its input is
`progress.schema.json#/definitions/context`, for example:

```json
{
  "name": "Example framing rehearsal",
  "evidence_mode": "simulated",
  "requested_stop": "G1",
  "observed_at": "2026-09-18T10:00:00Z",
  "evidence": "sources/request-and-provenance.json",
  "investment_appetite": "unknown"
}
```

Use actual source evidence and actual observation times, not these sample values.
The command hashes that evidence in the existing immutable journal revision.
Scope or appetite corrections require a fresh expected version and supporting
evidence; old context remains recoverable in prior journal revisions. A run cannot
switch between real and simulated labels. `real` is controller-attributed evidence
provenance, not an authenticated human decision or an actual-live execution claim.
Missing/changed provenance cannot yield a completed requested scope. No change to
this view's requested stop grants authority for work or changes the gate policy.

Gates beyond the requested stop are `outside_scope`: G1 framing completion does
not require G2–G4. An unknown stopping point yields `requested_complete: null` and
no assumed denominator. Counts measure verified gates only. Investment appetite
and the work order's checkpoint `effort_bound` are reported separately.

## Host observations in the existing journal

`observe --record PATH --expected-version N` commits an observation under the
existing controller lock and atomic revision pointer. There is no second tracker.
The input contract is `progress.schema.json#/definitions/observation`:

```json
{
  "event_id": "start-G1-a1",
  "run_id": "demo",
  "version": 4,
  "generation": 0,
  "work_order_id": "G1-a1",
  "kind": "started",
  "observed_at": "2026-09-18T10:15:00Z",
  "actor": "actual-assigned-author",
  "evidence": "sources/host-start-observation.json"
}
```

The controller must supply real host observations including scope and limitations.
The runtime verifies evidence bytes and the assigned actor label, not host identity
or the truth of the observation. The work-order ID is the unique attempt identity;
run, observed version, generation, assigned actor, subject hash (where sealed),
evidence hash and committed version bind each record. Timestamps must be actual UTC,
not future times. Out-of-order events within an attempt, wrong assignments, stale
generations and altered duplicate IDs are refused without mutation. Exact replay
is idempotent, including a crash at pointer commit. Changed/missing observation
evidence is exposed in `invalid_observations` and cannot support current activity.
That invalidation does not erase a known failed assessment or changed/failed
target. Committed negative observations stay applicable to their exact subject or
operation across missing/replaced evidence and unrelated generation changes.
Their original records remain in `observations`; `review_issues` and target
`unresolved_observations` expose why readiness is withheld. Evidence integrity is
reported separately and never becomes good merely because old evidence vanished.

Supported kinds:

- `dispatched`, `started`, `candidate_returned`, `review_requested`, `stopped`:
  observations only. Prepared/dispatched orders are queued; only a fresh started
  observation supports `last_observed_active`. Completed or invalidated attempts
  cannot remain active. Stopped activity does not revoke an accepted gate.
  Current pending attempts take precedence over a late stop from an accepted
  predecessor. Review-return/hold observations end a preceding started indicator;
  historical events remain available without controlling current activity.
  Activity selects the latest relevant committed event before checking its evidence.
  If that event or its attempt dependencies are unverifiable, activity is unknown:
  its time and `last_recorded_kind` remain visible, its actor is not claimed, and an
  older started event cannot become current again. Missing or changed evidence
  cannot imply renewed activity.
- `held`: supply `hold_type` (`prerequisite` or `decision`), `reason`, `needed`,
  `respondent` (null for unassigned) and `next_action`. Holds persist through later
  activity; `released` requires the controller actor and `resolves` event IDs plus
  evidence. A new attempt does not inherit an old attempt's observational hold.
- `review_returned`: the evidence file must be a full runtime ReviewReceipt for
  the sealed subject and assigned independent reviewer. Failed/unverifiable
  receipts can be recorded but never accepted by this command. Conflicting
  assessments stay visible; a new subject/attempt and review resolve them, not
  last-writer wins. Acceptance still uses the existing `accept` command.
  Progress uses that command's full review validation, including all score floors,
  aggregate score, unresolved blockers and target requirements. Pass labels alone
  are insufficient. Differing outcome/score/blocker assessments conflict; different
  explanatory wording alone does not. A conflicting accepted receipt is retained
  while the gate and current content-review summary withhold verified status.
- `accepted` and `reopened`: record host observation of an already committed
  acceptance or invalidation. These labels cannot create either transition.
- `delivery_result`: requires a G4 order, `operation_id`, `result`
  (`changed`, `failed`, `unchanged`), and `target_revision`. It binds the current
  operation's saved record hash. `unchanged` must match the saved verified
  revision; it means observed unchanged at that time, never unchanged now.
  A changed target requires reconciliation; a failed attempt blocks placement.

All labels and evidence are untrusted text. Controller-store permissions and host
attribution remain the trust boundary documented in [runtime.md](runtime.md).
Invalid API submissions return `hold`/exit 2 and the rejection reason to the caller;
they are not appended to the accepted journal as if they were valid observations.

## Projection interpretation

Accepted artifacts and pending candidates have separate objects, hashes, states
and links. An optional candidate cannot repaint unchanged acceptance. Multiple
outstanding attempts are exposed as a selection conflict rather than picking a
winner. An incompatible review of the same accepted subject is shown as a review
conflict while preserving the accepted receipt as historical fact.

Applicable attempt precedence is stale dependencies, review conflicts/failures,
confirmed prerequisite holds, unanswered required decisions, sealed review pending,
accepted receipt, fresh observed activity, queued assignment, not reached.
Blocking unanswered questions propagate from the accepted predecessor; candidate
questions come only from a sealed register, never loose files. Holds show the
resource/answer needed, respondent and next action. An unassigned respondent stays
unassigned. `current.assignment` links the claimed author/reviewer to the
controller work order and its assignment evidence/version.
For a pending candidate, its validated sealed register supersedes the inherited
questions in that attempt's blocker display. An evidenced answer becomes review
pending, not accepted; the original accepted register remains historical.

Readiness summaries are derived together from projected gate states and verified
request context, never independently from historical acceptance. Content and local
diagram readiness are conservatively bounded by G3's current state, including
conflicts, stale evidence, pending review, and outside-requested-scope gates.
When G3 is verified but request provenance is missing or changed, current readiness
summaries are unknown; the accepted receipts remain available as history. Detailed
predicate receipts can still distinguish individual review outcomes.

`current.label` and its finish action announce completion only when
`requested_complete` is true. If all requested gates have receipts but scope or
provenance needs revalidation, the current label is `context revalidation` and the
next action requests that revalidation. JSON, Markdown and HTML use these same
fields. Regression invariants cover summary/gate alignment at each stopping point,
withheld completion under context drift, and no revival of activity after a later
observation becomes unverifiable.

Policy rebinding and source invalidation follow the authoritative runtime. Old
accepted snapshots remain historical with stale state after reopen or dependency
drift. Local G3 content and diagram review, document presentation review, and each
requested target's placement are distinct. There is currently no journal contract
for document-layout approval, so `visual_review.document_presentation` is unknown;
do not infer it from HTML generation. G3's local-diagram predicate does not prove
the document's layout was independently reviewed.

Each target separates `local_integrity`, saved `target_revision`, actual
`last_read_at`, `observed_target_revision`, and `remote_freshness`. The existing
`delivery-record` accepts optional actual `observed_at` for verified readbacks;
older records have unknown read times. Local unchanged evidence is not remote
freshness. An observation can show changed/failed or observed unchanged at a
recorded time. A negative target observation clears only through a later intact
`unchanged` observation bound to the saved record, or an intact verified
`delivery-record` committed later with an actual `observed_at` at least as recent
as the negative observation. Updating a record without that readback timestamp,
changing generations, or losing observation evidence cannot silently clear it.
The journal records the reconciliation version; legacy records lacking that
version do not retroactively prove resolution. `observation_integrity` separately
reports whether the evidence supporting the displayed observation is intact.
Target-only problems preserve unchanged G3 content. Source changes and target
changes have distinct fields and next actions. No rendered view waives gates,
authorizes publishing, confirms a human bet, or implies implementation/release.

Both human formats show a compact card and gate table with the complete identical
JSON projection available under evidence details. `registers` identifies its
accepted snapshot and lists original question/decision records with evidence.
The current stage, next action and needed respondent lead the view; technical
revision hashes and the full projection are retained under expandable details.
HTML uses text-labelled stage indicators, not color-only progress or an effort
percentage. Accepted links are explicitly evidence snapshots, not rendered pitch
documents; the conductor supplies separate reader-document links when available.
Mechanical tests in `tests/test_shaping_progress.py` cover the projection and
transaction boundaries. They use simulated receipts; they do not establish
real-human comprehension, visual acceptance, remote target truth or release proof.
