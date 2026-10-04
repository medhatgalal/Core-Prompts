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

## Ask for copies after writing

Print the four plain status lines from ways-of-working.md, then ask with the host
ask-the-user tool when available, otherwise show options and wait:

“Which outputs do you want: HTML, Google Doc, Word, JSON, or all four?”

Choices: HTML; Google Doc; Word; JSON; All four. A host with fewer menu slots can
accept free text or a staged menu. Wait for the actual selection. Silence, defaults
and an empty tool result leave output choice pending; create no export from them.
All four means HTML, a native Google Doc, Word (.docx), and full document JSON
of this one handover. Ask for missing authorized destinations only for selected
copies. Create no unselected deliverables. A private intermediate DOCX used by
the existing Google Doc conversion is not a selected Word deliverable.

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
native editable tables, inline images and saved-target verification. Do not make
images public or treat an upload response as a saved Doc. For selected Word,
resolve and read the existing host Word/document skill, use its approved runtime
and document workflow to author this handover with the same prose, native tables
and existing diagram images, then render and inspect every page. Do not extend
Word output to frames or pitches. If that skill or runtime is unavailable, report
the selected copy pending with a concrete unblock; do not silently substitute.

Check saved HTML pixels and all content; saved Google Doc revision, native tables
and pixels; reopened Word text/table/image inventory and every rendered page;
and parsed JSON with full source/list/row/diagram parity. Missing access or a save
failure holds only the affected delivery and preserves the accept. Reconcile
uncertain writes before retrying. Stop after the one handover and selected copies;
start no spec, requirements, design, architecture, plan, tasks or build work.
