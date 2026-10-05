# Accepted pitch handover

## Write one handover

Trigger: the person with confirmed authority chooses Accept at the betting table
for the exact, current pitch revision, after engineering frame agreement and team
package acceptance. Write one human-readable source handover in the authorized
artifact home. Record the accept and source/review/decision bindings separately
in the existing agent journal; do not replace immutable accepted snapshots.

Use these short headings and content:

### In this handoff, build these

List every accepted item, each with one proof sentence stating the observable
completion. Copy the agreed scope and proof; do not narrow an item, omit one or
invent proof. If an item has no single proof sentence, return to shaping for
correction or splitting before acceptance. Do not hand an unresolved list to build.

### Named, and not in this handoff

List every deferred item and why it is deferred. State for each: “It needs its own
pitch before anyone builds it.” Naming a deferred item is not build permission.

### Do not build

Carry every forbidden line from the accepted pitch. Keep the three lists distinct;
resolve conflicting entries in shaping before acceptance rather than guessing.

### Shaping finished

Include the agreed frame, existing component, sequence and data-flow diagrams,
data contract and security-owner tables, API decision or no API, and the result
with observations, mocks and limits if a separately authorized skeleton was run.
When none ran, say so; do not create a trial to fill the heading. Keep original
captions, evidence and existing/proposed/unknown meanings. Reuse the package's
diagrams rather than drawing new ones for the handover.

### Shaping did not do

State: “Spec, requirements, design, architecture, plan, tasks.” Write none of those
documents in shaping. Existing fat-marker diagrams, contracts and provisional
workstreams retain their shaping purpose; they are not downstream deliverables.

### Next

State: “A separate build session starts at spec, and only for the build-these
list.” Build may finish every build-these line. It may not drop one or pick up
a deferred or forbidden line. “Proceed and loop” continues the current item;
it does not widen the sheet. A wider job needs a new pitch and a new accept.

### Not done

List everything named and not in this handoff. Deferred and forbidden work stays
unfinished and outside this build session even when every accepted item finishes.

Keep the prose for a person: short headings, the three lists and package diagrams
and tables. Do not dump gate tokens, scores or file paths into the document.
Source hashes, exact package/review identities and output receipts stay in agent
records. Evidence can use readable titles or links without exposing local paths.

## Complete the one source before sealing

For a new handover, include all three Mermaid fences, original captions and full
contract/security tables in the mutable handover candidate before seal. Images
supplement the fences; they never replace editable source. Bind the complete
source inventory and hash to its logical handover identity.

If an existing sealed or accepted source lacks required content, hold the requested
delivery. Preserve accepted bytes, history and the bet. Use the existing candidate/
reconciliation path for authorized completion under the same logical handover
source identity; renew affected source/render hashes, reseal and review affected
gates before delivery. A formatting repair changes no accepted scope or bet.
Reuse that valid resulting source, never author a second prose handover.

## Ask for copies after writing

Print the four plain status lines from ways-of-working.md, then ask with the host
ask-the-user tool when available, otherwise show options and wait:

“HTML, Google Doc, Word, JSON, Markdown, or all of them?”

Choices: HTML; Google Doc; Word; JSON; Markdown; All of them. A host with fewer
menu slots can
accept free text or a staged menu. Wait for the actual selection. Silence, defaults
and an empty tool result leave output choice pending; create no export from them.
All of them means HTML, a native Google Doc, Word (.docx), full document JSON
and the reused Markdown source of this one handover. Ask for missing authorized
destinations only for selected
copies. Create no unselected deliverables. A private intermediate DOCX used by
the existing Google Doc conversion is not a selected Word deliverable.

## Reuse selected Markdown

For Markdown selection, return the existing complete handover file; record its
portable path, source identity and sha256. Verify all three Mermaid fences,
captions, full contract/security columns and every row, accepted decision content
and build/deferred/forbidden lists against the source inventory. Repeated selection
reuses the same file/hash; it creates no duplicate authored prose. Missing source
content uses the candidate/reconciliation hold above, never an in-place edit of
accepted content.

## Reuse the existing output paths

Read the current diagram and embed skills and their selected resources before
conversion. Reuse shaping-artifacts/component.mmd, sequence.mmd (a real
sequenceDiagram), data-flow.mmd, contracts.md and security-owners.md, preserving
all rows, captions and evidence. Reuse source-bound SVG/PNG assets when their
hashes and presentation mapping still match. If mapping or hashes require new
derivatives, use the existing embed helper's documented render command on the
same Mermaid source. Never add a second diagram renderer or redraw the solution.

For HTML and full document JSON, use the embed helper's existing shaped profile
and explicit presentation mapping. That profile requires pitch.md, contracts.md
and security-owners.md. Prepare a scoped conversion inventory where pitch.md is
an exact copy of the source handover, the tables and Mermaid are the accepted
package bytes, and presentation.json anchors each diagram to the handover's
Shaping finished section. This copy is adapter input, not a second authored pitch.
Keep receipts outside it. Read helper help for actual flags; there is no new
handover profile or new renderer. JSON must contain the full handover, lists,
tables and diagram source/captions, not only a status manifest.

For a selected Google Doc, keep the embed adapter's supported private conversion,
native editable tables, inline images and saved-target verification. Read back
the current saved revision, inventory every table row and inline image/diagram,
and inspect saved-target pixels; source screenshots are insufficient. Do not make
images public or treat an upload response as a saved Doc. For selected Word,
resolve and read the existing host Word/document skill, use its approved runtime
and document workflow to author this handover with the same prose, native tables
and existing diagram images, then render and inspect every page. Do not extend
Word output to frames or pitches. If that skill or runtime is unavailable, report
the selected copy pending with a concrete unblock; do not silently substitute.

Check saved HTML pixels and full content; saved Google Doc revision, native
editable tables with all rows, full inline-image/diagram inventory and pixels;
reopened Word text/table/image inventory and every rendered page;
and parsed JSON with full source/list/row/diagram/caption/contract/security and
accepted-decision parity. Verify Markdown reuse and complete content separately.
Missing access or a save
failure holds only the affected delivery and preserves the accept. Reconcile
uncertain writes before retrying. Stop after the one handover and selected copies;
start no spec, requirements, design, architecture, plan, tasks or build work.

## Read-only selection and reuse helper

Load the `handover-tools` route and read `scripts/handover_outputs.py --help` from
this package's resolved resource root before invocation. The helper reads only:

```text
python3 scripts/handover_outputs.py --source HANDOVER.md --inventory ACCEPTED_INVENTORY.json --choice Markdown
```

Repeat `--choice` for explicit selections; `all` or `all of them` expands to five.
An absent, empty or unsupported choice holds; private conversion DOCX is not a
choice. The helper neither writes nor copies source, converts, renders or publishes.
`ready` is a selection/source-reuse plan; actual delivery remains pending.
Markdown returns the supplied path/hash without resolving a substitute or following
a symlink. Missing content, drift, incorrect spans or inventory gaps hold for the
candidate/reconciliation path; no accepted bytes are overwritten.

The controller supplies a trusted `HandoverSourceInventory.v1` JSON bound to its
accepted handover: `source_id`, `source_sha256`, `diagrams` and `tables`. Diagram
entries, ordered as in source, have exactly the IDs `component`, `sequence` and
`data-flow`, their complete Mermaid-fenced `markdown`, inclusive `locator` (`N:M`),
exact `caption` and `caption_locator`. Contract/security entries have exactly IDs
`contracts` and `security`, complete table `markdown` and `locator`, full `columns`
and every `rows` cell. Retain all fields/rows from the accepted inventory, not a
small test fixture or keyword summary. A table span cannot stop before its last
row. Source SHA binds all prose, decisions and lists, not only inventoried elements.
The helper verifies exact bytes/spans and structure; acceptance authenticity,
semantic completeness, caption meaning and visual quality remain independent checks.
Do not mint a replacement accepted inventory from a deficient source to evade review.

Optional `--evidence ADAPTER_EVIDENCE.json` maps only selected format IDs (`html`,
`google-doc`, `word`, `json`, `markdown`) to independently observed adapter records.
All records bind `source_sha256`, `content_sha256`, exact full `tables` (id/columns/
rows), `diagrams` (id/markdown/caption) and `host_observation_ref`. Visual formats
also name `target_id`. `content_sha256` and `text_inventory_sha256` mean canonical
normalized full-content digests reconstructed from independent saved-target
readback, not raw DOCX/HTML or cloud-object hashes. They must preserve the entire
source inventory and accepted decisions. The adapter must supply real readback;
copying the source digest into a record proves none occurred.

Word/Google Doc records require `native_editable_tables: true`, `image_inventory`
with all three diagram IDs and `text_inventory_sha256`. Word additionally requires
`reopened_saved_file: true`, positive `page_count`, ordered `inspected_pages` from
1 through that count, and one nonempty `saved_page_pixels` observation reference
per page. Google Docs requires current `saved_revision == readback_revision` and
nonempty `saved_target_pixels` references. HTML requires saved-target pixels; JSON
requires `parsed: true` and full content/inventory parity; Markdown requires
`reused_source: true`. Source screenshots, sampled Word pages, stale Doc readback,
non-native tables or partial image/row inventories hold the adapter evidence.

An `evidence_consistent` result checks declared evidence consistency only. It
cannot authenticate host observations, perform the JSON parse on a remote target,
reconstruct adapter content or inspect pixels. The controller must observe those
operations and independent semantic/visual results before recording delivery as
verified. The helper leaves delivery pending even when declarations are consistent.
Exit 0 means a valid plan (and consistent records if supplied); exit 2 means a hold.
Missing selected evidence remains pending; unselected evidence cannot create a copy.
