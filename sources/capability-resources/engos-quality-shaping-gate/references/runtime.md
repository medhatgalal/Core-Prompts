# Bounded shaping runtime

`scripts/shaping_run.py` is a Python 3.11+ standard-library CLI operated by the
controller. It records local consistency, not semantic truth or publication.
Read [gates.md](gates.md) and [rubrics.md](rubrics.md) for actual review policy.
The machine contracts are [runtime.schema.json](../schemas/runtime.schema.json),
with a complete [policy example](../schemas/policy.example.json). The schema's
`definitions/policy`, `prepare`, `review`, `questions`, `decisions`, and
`deliveryRecord` identify the individual input contracts. The executable uses
explicit fail-closed validation, not a JSONSchema dependency. Cross-field/hash
checks in this document are additional to structural schema validation.

## Trust and scope

The host must restrict accepted state, policy, reviewer assignment and this CLI
to the controller. Workers receive their candidate directory only. The runtime
does not launch workers, authenticate a supplied identity string, prove independent
context, authenticate human decisions, open cloud targets, render diagrams, or
check whether evidence says what the reviewer claims. A caller who can edit the
controller store can bypass these rails. Host permissions and attribution are
separate evidence. The local lock is advisory, not a sandbox.

The host must quiesce candidate/source writers during seal and acceptance. The
lock covers cooperating controller transactions, not concurrent editors of input
files. Hash rechecks do not provide an OS snapshot of a changing source tree.

Before dispatch the controller records the author, distinct reviewer, assignment
evidence and context evidence in `prepare`. Assignment/context files must be
actual host observations, including worker identity, initial context, allowed
resources, inherited context, contamination/access checks and limitations. This
is required at every gate, including G3. An author-written label or a test fixture
does not establish independent review. Contamination requires a new assessment.

Semantic reviewers inspect actual source and candidate bytes. They assess every
mandatory predicate with evidence and rationale; headings, keywords, filenames
and `pass` strings are never interpreted as proof of truth. Missing/failing/
unverifiable assessments hold. Tests use explicitly fake semantic receipts and
are mechanical regression evidence only. They are not independent review, a
human pilot, rubric calibration, saved-target visual QA or release acceptance.

## Run layout and commands

Use an authorized artifact home. All input paths in JSON are portable paths
relative to that home; CLI `--run`, `--policy`, `--spec`, `--receipt`, and `--record`
are filesystem paths. `--policy` must be inside the run. Absolute/nested symlink
paths, traversal, backslashes, colons and nonregular files are refused. Prefer
the physical temporary path (`/private/tmp` on macOS, not its `/tmp` symlink).
Source inputs cannot use `state/`, `accepted/`, or `candidates/`.

```text
<run>/sources/                  authorized input/evidence snapshots and policy
<run>/state/run.json            sole committed revision pointer/version
<run>/state/revisions/<hash>.json complete immutable controller journal revisions
<run>/state/controller.lock     OS-backed controller lock
<run>/candidates/<work-order>/  worker output, allocated after prepare
<run>/accepted/<hash>.json      complete immutable accepted snapshot
```

The controller stages the policy example with actual target destinations plus
exact copies of the actual gates/rubric at the paths in `references`. Both policy
bytes and referenced resource bytes are pinned. A policy ID is descriptive, not
proof of those bytes. Copy all materially relevant original sources, constraints,
resource dependencies, decisions/authority records and source index into authorized
`sources/` paths and list them in `inputs`. The helper cannot discover omitted
dependencies or silently track changes to the remote originals of local copies.
Refresh copies when upstream changes; reopen the earliest affected gate.

Frame-only and shaped-draft runs may set delivery_targets to an empty array.
G0–G3 remain available without publication. This never permits empty-target G4
acceptance or an unrequested delivery operation. The example retains HTML and
Google Docs because both remain required for this task's complete pilot acceptance.

Commands below assume the current directory is the resolved resource root
(`<skill>/resources`) and that the
controller has prepared those files. `0`, `1`, `2` illustrate the initial sequence;
always read the actual version after any successful mutation.

```sh
python3 scripts/shaping_run.py init --run /private/tmp/shaping-demo --run-id demo --controller controller-17 --policy /private/tmp/shaping-demo/sources/policy.json
python3 scripts/shaping_run.py status --run /private/tmp/shaping-demo
python3 scripts/shaping_run.py prepare --run /private/tmp/shaping-demo --expected-version 0 --spec /private/tmp/shaping-demo/prepare-G0.json
# Dispatch the author only now. Its writes go to candidates/G0-intake-a1/.
python3 scripts/shaping_run.py seal --run /private/tmp/shaping-demo --expected-version 1 --work-order G0-intake-a1
# The assigned reviewer now inspects the sealed subject and returns ReviewReceipt.
python3 scripts/shaping_run.py accept --run /private/tmp/shaping-demo --expected-version 2 --receipt /private/tmp/shaping-demo/reviews/G0.json
```

All commands have `--help`. The optional read-only `progress` projection and
controller observation inputs are documented in [progress.md](progress.md).
Existing `status` retains its default JSON interface. Every mutation except `init` requires
`--expected-version`. Successful JSON output exits 0; invalid, stale, conflicting
or unmet conditions exit 2 with `status: hold`; unverifiable persistent state exits
3 with `status: recovery_pending`; filesystem/IO failures exit 3 with `status: error`.
Argument syntax errors use argparse's exit 2 and usage text. An error after pointer
commit may have committed: inspect `status` and replay the same request first.

Exact `prepare` input (replace labels and evidence with actual host records):

```json
{
  "schema_version": 1,
  "work_order_id": "G0-intake-a1",
  "gate": "G0",
  "author": "author-worker-17",
  "reviewer": {
    "identity": "reviewer-worker-18",
    "independent": true,
    "assignment_evidence": "sources/reviewer-assignment.json",
    "context_evidence": "sources/reviewer-context.json"
  },
  "inputs": ["sources/original.md", "sources/index.json", "sources/reviewer-assignment.json", "sources/reviewer-context.json"],
  "source_revision": "source-index-revision-1",
  "resource_revision": "shaping-gates.v1+rubric.v2",
  "skill_allowlist": ["engos-design-frame-from-vague"],
  "original_constraints": ["Preserve the supplied problem; do not choose a solution in the frame."],
  "assigned_questions": [],
  "source_access_scope": "Only listed sources and explicitly approved source inspection",
  "effort_bound": "One intake pass; stop at missing decisions",
  "stop_conditions": ["Missing evidence", "Unclear authority", "Source access outside scope"]
}
```

`prepare` adds run ID, generation, controller, assignment version, predecessor
snapshot, actual input/policy/resource hashes, candidate path/write targets,
required outputs/predicates, accepted question/decision snapshots and return schema.
The work-order ID is unique for the entire run; use a fresh attempt ID for repair.
The directory must not exist before assignment. `seal` checks required outputs
and registers and returns `subject` (the cumulative filename/SHA256 inventory)
and `return_hash`. It is idempotent for unchanged bytes; changed sealed candidates
need a new work order. Store reviews outside candidates so they cannot hash themselves.

## Minimum artifacts and predicate mapping

Every candidate contains `questions.json` and `decisions.json`, independently of
prose. Accepted bundles are cumulative. Earlier accepted files remain byte-identical;
later stages may add files but must reopen the owning stage to change earlier prose.
Registers may evolve under the checks below. Policy may add mandatory outputs or
predicates, but cannot remove these minima or lower thresholds.

| Gate | Required new artifacts | Mandatory semantic IDs mapped to gates.md |
| --- | --- | --- |
| G0 | `brief.md`, `intake.md` | `original_preserved`; `source_coverage`; `fact_classification`; `no_selected_solution` |
| G1 | `framed.md` | `problem_frame` (people/problem/why-now/outcome); `confirmed_appetite_walkaway`; `boundaries_uncertainties`; `no_selected_solution` |
| G2 | `research-notes.md` | `uncertainties_resolved`; `evidence_sufficiency` (including actual spikes/private-review limitations); `grounded_risks` |
| G3 | `pitch.md`, `pitch-summary.md`, `workstreams.md`, `traceability.md`, `contracts.md`, `security-owners.md`, `component.mmd`, `sequence.mmd`, `data-flow.mmd` | `coherent_bounded_solution`; `exemplar_coverage` (scope/cuts/no-gos/mitigations); `diagrams_visual`; `contracts_security`; `workstreams_proof`; `constraints_traceability`; `author_audit`; `independent_review`; `rubric_assessment` |
| G4 | `betting-table-prep.md` | `saved_target_parity` (all text/rows/diagrams/style); `target_revision_pixels` (revision plus representation-appropriate verification); `faithful_betting_prep`; `no_delivery_discrepancy` |

Predecessor/current-generation/input hash checks are mechanical, in addition to
these semantic assessments. No schema proves the table rows are substantively
complete. G3 reviewers evaluate contracts/security coverage in gates.md, inspect
each of the three rendered diagrams, and apply the source-specific rubric anchors.

## ReviewReceipt

Use `definitions/review`. Copy the following bindings from the emitted order:
`run_id`, `gate`, `work_order_id`, `generation`, `policy_hash`, `resource_revision`,
`predecessor`. Copy `subject` and `return_hash` from `seal` exactly. `schema_version`
is integer `1`. `reviewer` must match the assigned identity. For acceptance,
`authored_candidate` is false, `independence_confirmed` true, `verdict` is `pass`,
`next_state` equals this gate, and `unresolved_blockers` is an empty array.
`findings` is an array of nonempty strings (empty permitted).

`evidence` maps IDs such as `E1` to files in the sealed cumulative subject; include
actual observation files/render artifacts in the candidate before sealing.
`assessments` has exactly one entry for every required predicate:

```json
{
  "original_preserved": {
    "outcome": "pass",
    "evidence_ids": ["E1"],
    "explanation": "REPLACE with the actual comparison and its limitations"
  }
}
```

This fragment illustrates shape only; it is not a review or a usable full receipt.
Fail/unverifiable are valid reported outcomes that cannot advance. Each claimed
pass needs nonempty evidence IDs resolving to nonempty hashed files and an actual
reviewer's explanation. The runtime can check existence/binding, not whether the
observation is authentic or sufficient.

For G3, `scores` contains `dimensions`, `team_mean`, `pitch_mean`, `overall`.
Every dimension is `{ "score": 4, "rationale": "actual basis", "evidence_ids": ["E1"] }`.
The seven team keys are `simplicity`, `testability`, `security`, `architecture`,
`cost`, `feasibility`, `confidence`. The five pitch keys are `problem_clarity`,
`appetite_fit`, `solution_sharpness`, `contract_quality`, `boundary_discipline`.
Use all twelve, finite scores 1–5, each >=3. Overall is `sum(all twelve scores)/12`
and must be >=4; category means are reporting only. Supply means without display rounding
(absolute comparison tolerance 1e-9). Rationale follows each dimension's source
anchor, not a generic rule that every 5 requires finished implementation.

G3 also requires `render_evidence` with all three keys `component.mmd`,
`sequence.mmd`, `data-flow.mmd`, each a nonempty evidence-ID array. A single
inspection report may cover all three, but its real coverage is a semantic review
obligation. Outside G3 use `scores: null` and `render_evidence: {}`.
Outside G4 use `targets: []`; the G4 contract is below. G3 always requires actual
local diagram pixel inspection, even for a JSON-only delivery request.

## Questions and decisions

Empty registers are `[]`, not empty files. An uncertainty entry has:

```json
{
  "id": "U1",
  "blocking": true,
  "in_scope": true,
  "status": "deferred",
  "evidence_standard": "Current inspected interface behavior with source revision and relevant scope",
  "evidence": [],
  "decision_id": null,
  "dependency_evidence": [],
  "details": {
    "question": "What freshness does the user action require?",
    "source_gap": "The supplied request has no freshness constraint",
    "why_it_matters": "Changes feasibility and scope",
    "respondent": "owner_unassigned",
    "history": [],
    "answer_provenance": null
  }
}
```

Statuses: proposed, accepted-for-investigation, answered, disputed, deferred,
excluded. Rejected wording stays in `details.history`; it does not remove the
uncertainty. IDs cannot disappear or downgrade `blocking`. G2–G4 reject in-scope
blocking entries unless answered with existing evidence. `evidence_standard` is
mandatory; the reviewer must assess whether evidence meets it. `evidence` and
`dependency_evidence` are paths in the sealed subject or enumerated hashed inputs,
not reviewer evidence IDs.

After G2, adding a blocking uncertainty or changing its resolution, evidence
standard or scope requires reopening G2. Accepted prose/evidence filenames are
immutable across later gates; use unique stage-specific names for new observations.

Scope exclusion requires `in_scope: false`, `status: excluded`, a `decision_id`
pointing to a confirmed decision, and nonempty dependency evidence. A decision is
`{ "id": "D1", "status": "confirmed", "authority": "actual designated human",
"reason": "actual decision and reason", "evidence": ["sources/decision-D1.json"] }`.
Statuses may also be proposed or disputed. Optional `details` preserves provenance,
dissent and other context. An accepted decision cannot silently change or disappear;
reopen its owning stage. A confirmation string is not authentication or evidence
that the named human actually made it. Review checks this separately.

## Atomic acceptance, replay and recovery

One immutable accepted JSON snapshot contains all cumulative artifact bytes as
base64 plus their SHA256 hashes, separate parsed question/decision arrays, complete
work order, transitive input/policy/resource bindings, full parsed receipt AND its
exact original bytes, predecessor and acceptance version. G4 also snapshots delivery
records. Original JSON/prose bytes remain available without reserialization. This
single-file representation avoids a partially copied multi-file accepted bundle.
Consumers can decode `files[name].base64`; these are source bytes, not a second
authoritative prose model. No separately mutable question/decision caches exist.

A nonblocking OS lock serializes cooperating writers (POSIX flock / Windows byte
lock). The runtime writes and fsyncs the immutable snapshot, then a complete state
revision, then atomically replaces `state/run.json` under the expected-version
check. POSIX parent directories are fsynced. Orphan objects before the pointer
commit are unaccepted; replay may reuse them. After commit, the identical original
receipt bytes return the existing acceptance without a second write, even if the
caller supplies its pre-crash version. Different bytes for that accepted work-order
ID conflict. Reopened receipts remain historical and cannot be replayed as current.

`status` verifies the pointer, referenced revision, historical snapshot hashes and
current predecessor chain. Missing/corrupt referenced state yields recovery_pending;
it never reconstructs acceptance by guessing from orphan objects. Preserve the
store and restore a known verified pointer/backup under controller supervision.
Unreferenced interrupted writes are not authority and are never auto-promoted.
State is logically immutable/hash-checked, not protected against a hostile writer.
Local filesystems with atomic replace and working locks are assumed; network
filesystem semantics and Windows power-loss durability have not been proven here.

Late results hold without state mutation. Retain their candidate/receipt files
outside committed state for inspection. `status` reports local source/resource
drift and withholds content-ready/verified-delivery flags until resolved; it cannot
observe edits to remote originals or targets without a fresh readback.

Pinned policy, work-order and predecessor inputs are checked independently even
when they name the same path; an ordinary input hash cannot replace a policy pin.
Content readiness uses G3's dependency set, while delivery readiness additionally
checks G4 and saved-target evidence. G4-only readback drift must not revoke unchanged
G3 content. The aggregate dependency_drift list can therefore be nonempty while
content_ready remains true and delivery_state is pending.

```sh
python3 scripts/shaping_run.py reopen --run /private/tmp/shaping-demo --expected-version 12 --gate G2 --reason "New load-bearing compatibility question"
```

Reopen removes the selected gate and descendants from the current pointer, keeps
history, and increments generation. New outcome/appetite/scope reopens G1;
solution uncertainty reopens G2. Reopen the earliest stage that depends on changed
input bytes. Policy/resource changes conservatively require G0 reopen with
`--policy <current-policy-path>` to rebind all policy dependencies. Target-scope
changes are policy changes; they cannot retroactively satisfy previous G4 scope.

## Delivery intent and saved-target records

Content approval at G3 and delivery-pending are separate. The helper does no
external work and grants no sharing/create authority. The publisher separately
obtains the required target permissions and emits local evidence.

```sh
python3 scripts/shaping_run.py delivery-intent --run /private/tmp/shaping-demo --expected-version 12 --surface html --destination /approved/pitch.html
python3 scripts/shaping_run.py delivery-record --run /private/tmp/shaping-demo --expected-version 13 --operation OPERATION_HASH --record /private/tmp/shaping-demo/delivery-readback.json
```

Operation identity binds run ID, accepted G3 bundle hash, surface and destination.
The first persisted intent returns `may_create: true` as a bookkeeping signal;
it is not permission. A repeat pending/uncertain intent returns
`reconciliation_required` (exit 2), including after a bundle change. Locate the
already-created target and read it back before recording a result. Do not create
another when identity is uncertain. A verified repeat returns `may_create: false`.
There is no exactly-once guarantee across an external API.

```json
{
  "status": "verified",
  "target_id": "actual-saved-target-id",
  "revision": "actual-readback-revision",
  "evidence": {
    "readback": "sources/target-readback.json",
    "pixels": "sources/target-screen.png",
    "inventory": "sources/target-inventory.json"
  },
  "note": "Actual observer, scope, saved revision, parity findings and limitations"
}
```

If success is uncertain record `{ "status": "uncertain", "note": "actual uncertainty" }`.
A verified record needs a nonempty target ID/revision and all representation-specific
existing, nonempty hashed evidence files. A repeated identical record is idempotent;
conflicting verified records hold unless G4 was explicitly reopened in a later
generation. Reconciliation history is preserved, including old bundle operations.

For G4, include byte-identical copies of the target evidence files in the candidate
before sealing. The receipt `targets` contains one entry for every requested target:
`{ "operation_id": "actual hash", "readback": ["E_readback"], "pixels": ["E_pixels"],
"inventory": ["E_inventory"] }`. These IDs resolve through receipt `evidence`.
The runtime requires exact nonempty target coverage, verified operations bound to
current G3, unchanged delivery evidence and matching subject hashes. For visual
targets the reviewer inspects saved content, all table rows, diagrams, style and pixels;
recording an upload response alone is not sufficient. External target drift cannot
be polled by this local helper; detection requires fresh publisher/reviewer evidence.

Representation-specific evidence: use exact surface ID `json` for a structured
JSON export. Its record and target review use `readback`, `structured`, `inventory`,
with no `pixels` field. The runtime parses the actual readback bytes and requires a
nonempty JSON object/array. `structured` contains the actual source-to-export parity
assessment; `inventory` covers source sections, every table row and diagram. Parse
success alone cannot prove fidelity: the reviewer assesses exact structured parity
under `saved_target_parity`. The `target_revision_pixels` predicate retains its ID
for schema stability and means revision plus representation-appropriate verification.
For HTML, Google Docs and every other visual surface, `pixels` remains mandatory
and cannot be substituted with `structured`. JSON-only runs can reach G4 with these
checks, while G3 still requires all three local rendered-diagram pixel inspections.
The original pilot requires both HTML AND Google Doc; the supplied policy example
preserves both. JSON export cannot replace either without an explicit scope change.
