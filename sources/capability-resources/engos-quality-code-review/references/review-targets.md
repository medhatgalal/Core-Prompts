# Review target and findings contract

Read this reference and `resources/schemas/findings.schema.json` completely before
review. The one `review` route loads both through the existing resource loader;
assembly proves content identity, not model consumption. Keep the entry skill's
message, scope, simplicity, correctness, security, lifecycle, concurrency,
operational and API checks. This reference narrows target/evidence semantics.

## Select and bind the target

Record `target.kind`, full resolved `base` and `head` commit IDs when applicable,
`comparison`, `included_change_classes`, and `snapshot_digest`. Never infer a
staged request from a dirty checkout. No argument still means latest commit HEAD.

| Request | Target and boundary | Included changes |
| --- | --- | --- |
| Latest/specific commit | `commit`; resolved head and selected parent base; `parent`, `merge_parent`, or `root` comparison | That commit's patch and message; exclude staged/unstaged/untracked checkout edits |
| Explicit staged | `staged`; base=head=checkout HEAD when it exists, `staged` comparison, index snapshot digest | Index only; read changed source and unchanged consumers from the index, not unstaged files |
| Working tree | `working_tree`; declare `unstaged` (index to worktree) or `combined` (HEAD to worktree), head/base=checkout HEAD when it exists, snapshot digest | Declare staged/unstaged inclusion accurately; list untracked paths explicitly if included; never imply they appear in git diff |
| Branch/range | `branch`; full head and actual comparison base; `merge_base` for branch contribution or `range` for explicitly selected endpoints | Full declared range and commit list, including messages; do not substitute HEAD~1 for a multi-commit task |
| Supplied patch | `diff`; `supplied_diff` comparison and digest; keep unknown base/head null | Exact supplied bytes; do not claim repository context or consumer coverage that was not obtained |

For a root commit use `base: null` and compare against the empty tree. For an
unborn index/working tree use null commit IDs and bind all included bytes through
the snapshot. A merge commit needs a named parent or explicit comparison choice;
if intent is unresolved, report incomplete rather than choosing silently. An
empty staged index means no staged target; disclose any working-tree fallback
before inspecting it and report it as a separate target. An empty/no-change target
is a no-op observation, not evidence of a completed code review.

Capture status, included classes, exact patch and source identities at the start.
For snapshots, retain a manifest of repository-relative paths, presence/deletion,
file mode and content SHA-256 for every included file and context file used, plus
the exact patch SHA-256 and comparison/index identity. Hash the UTF-8 JSON manifest
with sorted keys and compact separators, preserving its exact bytes; put that
SHA-256 in `snapshot_digest`. Include content hashes for binary files; disclose
unreviewable binaries rather than treating an empty textual diff as review. Check
status and all relevant identities again at the end; drift requires recapture and
renewed review of affected evidence. A mutable workspace's commit ID alone cannot
bind a staged or working-tree review. Do not invoke write-tree, stage, reset, or
rewrite source merely to collect review evidence.

Resolve committed source reads from the selected Git objects, even when a newer
checkout exists. For branch reviews record how the base was selected; an explicit
task baseline must include all task commits. Keep rename/deletion old and new paths
and base/head sides distinct. Findings on removed lines use the base-side location;
do not invent a new-side line for an inline publisher. This skill does not publish.

## Verify the changed cause and consumer

Read the actual diff and relevant full files, types, call sites and tests at the
bound revision/snapshot. An introduced-breakage finding must connect a changed
line or deleted/renamed contract to a consumer or execution path actually inspected
at that target. Search results alone are leads, not verified caller evidence.
Inspect outside-diff consumers when a changed interface, symbol, default, gate or
lifecycle can affect them. Record what the consumer does and why the change breaks
it; do not treat an imagined caller or an unrelated pre-existing defect as proof.

A consumer may be in the same file, an unchanged caller, configuration, generated
client or test. Record its actual location and evidence IDs. For a brand-new entry
point, the inspected input-to-failure execution path can be the consumer evidence.
If a material consumer cannot be inspected, list the coverage gap in `unreviewed`;
keep the conclusion unverifiable instead of presenting a speculative bug as fact.
An intended API change does not erase a verified unintended downstream breakage.

Scope, message and nonblocking suggestion findings need no invented runtime
consumer. Use their category, `affected_consumer: null`, and explain applicability
in `disposition_reason`. Still identify the changed cause and evidence (including
commit metadata where appropriate). Use message location side `message` with a
null line when no source line applies.

## Structured findings and evidence

Use `Findings.v1` fields in chat or a requested JSON artifact. Preserve the six
entry sections; structured fields augment them. Each finding has a stable ID,
severity (`critical`, `high`, `medium`, `low`), category, location, changed cause,
evidence IDs, affected consumer where applicable, impact, concrete repair and
disposition (`open`, `resolved`, `accepted_risk`, `not_actionable`) with rationale.
Critical/high/medium open findings block ready; low severity is optional follow-up.
Do not downgrade a blocker to obtain ready. Accepted risk needs attributable
acceptance evidence from an authorized decision maker, not the reviewer's choice.
Resolved findings need inspected repair evidence at the current target. Preserve
prior IDs/history on re-review; a disposition is not permission to apply a fix.

Evidence entries identify path, kind (`diff`, `source`, `consumer`, `message`,
`test`, `decision`), target side (`base`, `head`, `snapshot`, `external`), immutable
Git blob/commit ID or SHA-256, applicable line bounds, and `read_status`. Record
external decision evidence by content hash and attribution. Every evidence ID must
be unique and referenced IDs must resolve to entries actually read. Use exact
base/head/snapshot identities; resolving a reference merely to a current path is
insufficient. A model's assertion that it read a file is not independent evidence
of tool delivery or semantic correctness.

`review_status: complete` requires the actual selected diff, source and material
consumer context to have been read and all declared coverage to be reviewed.
`unreviewed` is empty only then. `ready` additionally needs no unresolved blocking
finding. Use `blocked` for confirmed blockers and `split_required` for a complete
scope review that requires splitting. Missing/unread/stale evidence, malformed or
absent requested output, unresolved targets or interrupted review means
`review_status: incomplete`, `verdict: unverifiable`; retain confirmed findings and
specific unreviewed items. A valid empty findings list after a complete review is
allowed; a missing report or an unparsed empty string is not an empty findings list.

JSON Schema checks field shape and some status consistency. It cannot verify
reference identity/uniqueness by ID, line meaning, actual reads, intended scope,
truth, consumer applicability, severity or acceptance authority. The reviewer and
consuming operator must check those semantics against actual evidence before
using the verdict. A successful capture or collection is not review completion.
No verdict grants repair, posting, approval, merge, installation or release rights.

## Optional collection request

Ordinary review loads only the review route and keeps the default HEAD target.
When immutable committed-range evidence is explicitly requested, select the
separate collect route. Supply exact full recorded ancestor base/candidate IDs,
task ID, owner, positive generation, repository identity and a new task-owned
output leaf; optional spec/plan digests remain caller assertions. The selected
collect context contains the command and full coverage/trust limits. Collection
completion remains separate from actual review, unchanged-consumer reads and
Findings.v1 judgment. Staged/dirty requests retain the review snapshot contract.
