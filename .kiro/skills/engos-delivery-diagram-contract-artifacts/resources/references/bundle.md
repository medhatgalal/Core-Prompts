# Required shaping bundle

In a full shaping run, read the accepted frame, current evidence and decision
snapshots before authoring. Artifact-only mode may use a supplied solution but
must not fabricate upstream gate history. Annotate existing/proposed/unknown seams.

For a full shaping run, the shaper is the producer of pitch.md, pitch-summary.md,
workstreams.md and traceability.md using the conductor's shaped-bundle template.
This helper produces contracts.md, security-owners.md, component.mmd, sequence.mmd
and data-flow.mmd for that same candidate bundle; the controller accepts it and
does not independently reauthor sidecars. `workstreams.md` is the canonical name.

For standalone artifact-only requests, use the supplied solution and produce only
the original shaping-artifacts bundle (manifest, three diagrams, contracts,
security owners, evidence-ledger and no-gos). No conductor, new pitch document or
shaping sidecar is required. Retain partial/blocked results when evidence is missing.
Preserve the supplied appetite, cuts, no-gos and evidence in either mode.
Method/Purpose or Method/Endpoint/Purpose columns retain the exemplar's interface
shape; also keep direction, producer, consumer, state, evidence and owner/action.
Security rows retain Responsibility, Owner, How enforced, boundary and evidence.
State which component explicitly does not own a responsibility and who does.

Every diagram has a caption, source references, legend and intentional omissions.
Cover input/output meaning, material failures, applicable retries/consistency and
persistence, not invented implementation algorithms. If a diagram cannot be
supported, report the exact research gap and do not fill it with plausible internals.

The immutable source inventory binds Markdown, Mermaid and row identities/hashes.
Render and placement receipts are separate references to that inventory. Do not
mutate source hashes when adding observations or recursively hash the receipt.
Render all three diagrams and inspect pixels; repair overflow/contrast/clipping
then rerender changed sources. The delivery skill's local exporter can render
Mermaid using an available trusted CLI; invoking it does not authorize publication.
