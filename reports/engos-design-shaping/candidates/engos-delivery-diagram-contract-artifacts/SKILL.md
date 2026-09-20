---
name: engos-delivery-diagram-contract-artifacts
description: Produce the required Shaped-stage diagrams, API contracts and security ownership from a passing frame and research log. Keep Mermaid and complete tables authoritative across surfaces, with rendered inspection and explicit proposed versus existing interfaces.
display_name: Shaped Pitch Artifact Author
kind: workflow
capability_type: skill
---
# Shaped Pitch Artifact Author

## Purpose

Supply the visual and interface evidence required by Stage 3 of full Shape Up
shaping. Preserve this existing Core-Prompts identity as a helper owned by the
shaping conductor. It cannot substitute for Intake, Framed, Research or review.

## Primary Objective

Make the shaped solution understandable at the exemplar's level: boundaries,
component interactions, data movement, interface state, security responsibility
and explicit negative space, all supported by the research and scope decisions.

## Invocation Hints

Use for “make this shaped solution visual,” “show the interfaces and who owns
security,” or the conductor's required Stage 3 output. A request for a vague
problem to become a pitch starts with engos-design-shaping. Direct artifact-only
use is supported, but reports earlier stages unassessed.

## Required Inputs

Passing G1/G2 receipts and their current frame/evidence; the shaped solution
proposal; original constraints; accepted appetite; scope decisions; diagram style;
and the chosen surface's content-width constraints. For artifact-only requests
outside a full shaping run, label upstream stages unassessed and make no
full-pipeline readiness claim.

## Workflow

Read `resources/diagram-style.md` before authoring or rendering diagrams.

1. Verify the frame and research revisions. Every selected-scope open question
   must have an evidence-backed answer. Return needs_spike if any material seam
   remains unresolved; a polished diagram cannot repair that.
2. Inventory named components, interfaces, data stores, owners and boundaries.
   Separate implemented facts from proposed changes. Proposed interfaces may be
   defined at contract level, clearly marked, with current precedents cited.
   Never present a proposed method as an existing method or invent internals.
3. Produce component.mmd, sequence.mmd and data-flow.mmd. Each includes a caption,
   legend, source references and what it intentionally omits. Use Mermaid first.
   Use alternative source only for a documented expressiveness limit. Rendering
   Mermaid to PNG for Google Docs is a target conversion, not a source fallback.
4. Produce contracts.md with the exemplar's Method/Purpose or
   Method/Endpoint/Purpose columns; add producer, consumer, state and evidence.
   Separate in-process calls from network APIs. Capture input/output meaning and
   material errors at boundaries without a production implementation plan.
5. Produce security-owners.md with Responsibility, Owner and How enforced,
   plus evidence/state. Describe negative responsibilities explicitly, including
   which other component owns them. An unassigned required owner blocks G3.
6. Preserve every row and diagram in an immutable source-content manifest: stable
   IDs, paths, source hashes, caption, evidence and proposed/observed state.
   Store render and placement observations in separate receipts keyed to those
   hashes; adding a placement observation does not rewrite reviewed content.
   Hash the actual source bytes; do not put a placeholder in a successful receipt.
7. Render all diagrams locally. Inspect pixels for legibility, clipping, arrows,
   boundaries and fidelity to source. Correct and rerender the weakest view.
   A parser result, SVG count or existence of PNG files is insufficient.
8. Return the bundle to engos-quality-shaping-gate for G3 assessment. Placement
   uses engos-delivery-artifact-embed after G3 passes.

## Required Output

The three Mermaid sources and render evidence; complete contracts and security
tables; captions/negative space; evidence links; and manifest with actual hashes,
row inventories, statuses and unresolved gaps. The package is part of the full
pitch folder, alongside the problem/solution, no-gos and workstream artifacts.

```text
artifact_id: stable pitch identity
source_manifest: paths and SHA256 for source prose, three diagrams and full tables
diagram_inventory: component, sequence, data-flow; captions and evidence references
table_inventory: all contract and security row IDs and counts
render_receipts: source hash, renderer, image path and actual pixel observations
upstream_status: G1/G2 receipt references, or unassessed for artifact-only use
gaps: explicit unresolved items
```

## Rules

Use short node labels, semantic colors for components/data/security, labeled
edges and no more than eight sequence participants unless split with explicit
coverage. Every source claim is cited; every proposal is marked as proposed.
Unknowns stay unknown. Preserve implementation freedom inside boundaries.

The HTML and document representations must retain the same rows and meanings.
Do not manually abbreviate a full contract inventory to a few attractive sample
rows while claiming parity. A summary is allowed only as an explicitly labeled
additional view with the full table still available on the final target.

## Constraints

No Jira tickets, implementation code, invented runtime proof, or betting decision.
The artifact author cannot approve its own independent quality review. A target
render limitation remains an explicit blocker or human step, never silent omission.

## Examples

A library embedded in a host has an in-process contract, not a fabricated REST
endpoint. Its security matrix states which checks the host owns and whether the
library performs any additional checks, based on evidence. A diagram must show
that boundary without adding a nonexistent authentication service.

If twelve contracts are authored, the adapter must retain all twelve. Rendering
four representative rows fails completeness even if the screenshot looks clean.

## Evaluation Rubric

| Check | Pass |
| --- | --- |
| Upstream readiness | Passing current frame and evidence, or explicitly artifact-only |
| Exemplar coverage | Three diagram types, complete contracts and responsibility matrix |
| Evidence fidelity | Existing/proposed/unknown clearly separated |
| Visual quality | Every diagram pixel-inspected and legible at target width |
| Portability | One authoritative source and complete row inventory |
| Gate boundary | Authoring does not claim review or placement completion |
