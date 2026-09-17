---
name: engos-delivery-artifact-embed
description: Place a passing Shaped pitch on its selected HTML, PR/MR, chat, Google Doc or wiki surface and verify complete saved content and pixels. Preserve source identity, native tables and every diagram; a human step leaves placement pending.
display_name: Shaped Pitch Surface Adapter
kind: workflow
capability_type: skill
---
# Shaped Pitch Surface Adapter

## Purpose

Complete Stage 4 by placing the full shaped pitch on the requested surface.
Keep this existing helper identity. The source bundle is authoritative; adapters
transform representation without choosing a new solution or dropping content.

## Primary Objective

Return observed target placement for every required surface, with complete
diagrams, tables, prose and source identity. A failed target produces an exact
human/platform step and placement_pending; it cannot make the whole run bet-ready.

## Required Inputs

Current G3 pass and bundle; selected target/account and authorized write scope;
full row/diagram inventory; target style and access capabilities. Read
`resources/surfaces.md` before selecting a placement route. Diagnostic preparation
may happen during preflight, but final placement follows the Shaped gate.

## Workflow

1. Inspect target capabilities and select one adapter. Native Mermaid support
   must be observed or verified in the actual target configuration; chat and wiki
   families do not universally render Mermaid.
2. For a Mermaid-enabled HTML site or PR/MR, emit fences and full Markdown tables
   without hosting images. Build/preview and inspect the rendered result.
3. For Google Docs, render the same Mermaid source to PNG. Prepare a local DOCX
   containing the full pitch, images, captions and native tables using the supplied
   house style. Visually verify it, then import as a native Google Doc through the
   supported host path. The user-requested GWS route uses `--upload` and verified
   schema flags, never the reported blocked `--upload-file` path.
4. For an existing Google Doc, preserve its content and structure, use a fresh
   revision guard, and choose a tested private image-insertion path. Upstream's
   DOCX conversion/image-URI method is a candidate to verify, not a guaranteed
   workaround. Do not make a file public to satisfy an insertion URL requirement.
5. For a wiki, choose supported native Mermaid macro or image attachment and
   native table. For chat without rendering, use a permitted image reference and
   complete inline tables; report if the target cannot preserve required content.
6. Read back the actual saved target. Compare every diagram and table row with
   the bundle; inspect the rendered pixels, including captions, legibility,
   headings, table structure and explicit exclusions. Native Docs tables must
   remain tables rather than pictures of tables.
7. Record target ID/URL, revision or saved timestamp, source hashes, exact row and
   image counts, readback evidence, pixel observations and limitations. Submit to
   G4. An upload acknowledgement does not establish content or visual parity.

## Required Output

One receipt per requested surface with adapter, representation, source identity,
target/revision, content inventory comparison, render/readback evidence and
status. Valid completion states are placed or verified_native_passthrough.
human_step_required and blocked retain placement_pending.

## Rules

Preserve the full pitch, not only its diagrams. Detect content drift before
declaring placement. Reuse authorized access without broadening sharing or
changing OAuth scopes. Name account/destination before writing. Use current
supported UI actions; `app_post` and `sky_click` are historical failure labels,
not portable API requirements. After a click, verify actual UI state; do not
assume an accessibility action worked when the screen is unchanged.

## Constraints

This adapter cannot waive an upstream gate, create a human bet, or execute
implementation. Public image hosting is not a prerequisite. A private upload
or export may initialize existing authentication but does not authorize a new
account, permission scope or sharing change. Preserve unique temporary artifacts
until placement is verified; delete only within authorized cleanup scope.

## Examples

An HTML preview displays three Mermaid diagrams and eight contract rows. A
Google Doc imported from the same bundle must have three inline images and all
eight native-table rows, plus the complete responsibility matrix. If its
conversion drops a row, G4 fails and the adapter repairs that representation.

If only public-URL insertion is available and domain policy blocks sharing,
return the exact manual insertion step and target content to verify. Do not
call that second surface proven or the run bet-ready.

## Evaluation Rubric

| Check | Pass |
| --- | --- |
| Target selection | Actual capability determines the route |
| Fidelity | Full prose, row and diagram inventories survive |
| Privacy | No implicit public sharing or account change |
| Style | Requested typography and visual checks pass |
| Proof | Current saved-target readback and inspected pixels |
| Honest status | Human steps remain pending and prevent G4 passing |
