# Google Doc Surface Receipt

Artifact: `pm-query-lib-architecture-2026-09-17`

Adapter: `render-upload-insert-readback`

Status: `human_step_required`

This is the dry-run placement packet for the same source bundle used by the
HTML surface. It proves adapter selection and preserves the exact blocker; it
does not mutate an external Google Doc.

## Planned representation

1. Render `component.mmd`, `sequence.mmd`, and `data-flow.mmd` at the adapter
   boundary to PNG/SVG; keep the Mermaid files as the durable source.
2. Upload the derived images through the supported Drive upload form used by
   this environment (`--upload`, not the blocked `--upload-file` form).
3. Insert the private image into the target Doc and create native Docs tables
   from `contracts.md` and `security-owners.md`.
4. Read back the saved document revision and confirm the image/table rows are
   present. Record the source hash in the document or adjacent receipt.

## Current blocker and human step

The known environment path where `insertInlineImage` fetches only a public URL
cannot be used when corporate Drive sharing rejects public publication. The
remaining human/platform step is to provide or approve a private, supported
image-insertion path (or manually insert the rendered image) and then perform
the saved-revision readback. The adapter must not make the file public or claim
`placed` from an upload alone.

```text
source_hash: same source bundle as html-surface.md
representation: rendered_image_plus_native_table
placement_status: human_step_required
verified_by: dry-run plan; no external write performed
changed_meaning: false
blockers:
  - private image insertion path unavailable in this environment
  - live external write and readback not authorized for this repository task
```
