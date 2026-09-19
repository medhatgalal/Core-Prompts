---
name: "engos-delivery-diagram-contract-artifacts"
description: "Author a surface-agnostic shaped-pitch artifact bundle with Mermaid component, sequence, and data-flow diagrams plus API/contracts and security-owner tables. Use when a shaped solution needs durable visual and contract evidence before review or betting; do not invent component internals or place artifacts on external surfaces."
display_name: "Shaping Artifact Author — Diagrams, Contracts, and Security Ownership"
kind: "workflow"
capability_type: "skill"
version: "v1.1"
---
# Shaping Artifact Author — Diagrams, Contracts, and Security Ownership

## Purpose

Turn an already-shaped solution into a durable, surface-agnostic artifact
bundle that makes the fat-marker solution visible without turning shaping into
implementation. Use this skill after research and scope decisions are available
and before a pitch enters its review or betting gate. It authors Mermaid source,
an API/contract table, and a security-owner matrix from stated evidence. It does
not decide whether the pitch is worth betting, add implementation code, or
silently fill gaps with plausible internals.

## Primary Objective

Produce one inspectable artifact package that can be rendered or embedded on
multiple target surfaces while preserving the same component seams, flow,
contract states, ownership, assumptions, no-gos, and evidence references.

## Invocation Hints

Use when the user asks to make a shaped pitch visual, add architecture
diagrams, define API contracts for a pitch, document security ownership, or
prepare a pitch for a review/betting gate. Use the companion
`engos-delivery-artifact-embed` skill only after the bundle has passed this
skill's completeness checks.

## Required Inputs

- the shaped pitch or solution brief
- appetite, no-gos, and known rabbit holes
- cited research or source references for components and seams
- any stated contract states: `exists_and_works`, `exists_but_broken`,
  `missing`, or `unknown`
- target surface hint, if known; the authoring output remains surface-agnostic

## Required Output

Write or return a bundle with this stable shape:

```text
shaping-artifacts/
  manifest.json
  component.mmd
  sequence.mmd
  data-flow.mmd
  contracts.md
  security-owners.md
  evidence-ledger.md
  no-gos.md
```

`manifest.json` records the pitch identity, appetite, source hashes or links,
diagram inventory, contract row count, security-owner row count, target-neutral
format, and source status for each artifact: `authored` or `blocked`. Store render
and placement observations in separate receipts bound to these source hashes; they
must not mutate the reviewed source inventory. The Markdown tables must include at least:

| Required table | Minimum columns |
| --- | --- |
| API / contracts | Method, endpoint (network only), purpose, direction, interface, producer, consumer, contract state, evidence, owner/action |
| Security ownership | Responsibility, owner, enforcement/control, boundary, evidence, unresolved gap |

Each diagram source must have a caption, diagram type, evidence references, and
an explicit statement of what it does not show. The component diagram shows
named components and seams; the sequence diagram shows a representative
request or event path; the data-flow diagram shows data movement and stores.

## Workflow

1. Read the pitch and evidence ledger before drawing. Extract only components,
   interfaces, stores, owners, and flows that the pitch or cited evidence names.
2. Set the artifact budget from the appetite. Choose the smallest diagram set
   that covers the required seams; if the source cannot support a diagram,
   record `blocked` with the missing evidence rather than guessing.
3. Read resources/references/diagram-style.md and resources/references/bundle.md.
   Author Mermaid first. Prefer LR for flows and TB for hierarchy when legible.
   Apply the team's semantic style palette, keep node
   labels short, and label edges with protocol, port, or contract context.
4. Author the contract table for both provided and required interfaces. Record
   contract state and distinguish observed behavior from assumption.
5. Author the security-owner matrix. Assign responsibility only when the pitch
   or evidence names an owner; otherwise record `unassigned` and a concrete
   decision needed.
6. Run the no-fabrication check: every node, edge, table row, owner, and
   enforcement claim has an evidence reference or is visibly marked assumed.
7. Run the completeness check: component, sequence, data-flow, contracts, and
   security ownership exist; source and evidence status are recorded; no-go and
   appetite constraints are carried forward.
8. Return the bundle and a short judgment. Do not place it on a Google Doc,
   wiki, PR/MR, or chat surface; hand that action to the embed skill.

## Rules

- Mermaid source is the durable artifact. Rendered SVG/PNG is a derived view;
  use SVG-to-PNG when PNG is explicitly requested or the target surface cannot
  accept Mermaid or SVG, and record the reason. A native-Mermaid-only request
  does not require unnecessary derived images.
- Never invent methods, classes, endpoints, internal algorithms, retries,
  owners, security controls, or data stores. Unknowns become explicit gaps.
- A diagram is not complete merely because it parses. It must cover the named
  seams and have evidence references.
- Keep fat-marker scope: show what connects and what contract state exists, not
  a production implementation plan.
- Treat an unresolved rabbit hole as a mitigation or blocker, never as a
  resolved fact.
- Preserve the same artifact identity across all surfaces; adapters may change
  representation, not meaning.
- Fail loudly when the appetite cannot support the requested artifact set.
- Contracts and interfaces only; do not produce implementation code or Jira
  tickets.

## Surface Contract

The output is intentionally target-neutral. HTML docs sites, PR/MR
descriptions, and chat can consume the Mermaid fences and Markdown tables
directly. Google Docs and wiki adapters may render the same Mermaid source and
place an image, but they must retain a link or hash to the source bundle and
must report placement evidence separately.

## Constraints

- This skill does not score or approve the pitch; `engos-audit-pitch-review`
  owns the betting judgment.
- This skill does not choose a native agent surface or delegate work.
- This skill does not upload, share, publish, or edit external documents.
- It must work from pasted content, a local file, or a read-only source export.
- If evidence is insufficient, return a partial bundle with explicit blockers;
  never return a polished but unsupported diagram.

## Examples

### Example Request

> Use `engos-delivery-diagram-contract-artifacts` on this shaped pitch. Make
> the component and request flow visible, list provided and required
> contracts, assign security ownership from the evidence, and flag anything
> you cannot prove.

### Example Output Shape

- bundle manifest with `authored`/`blocked` statuses
- component, sequence, and data-flow Mermaid sources
- API/contracts table with contract states
- security-owner matrix with evidence and gaps
- no-go list and evidence ledger
- completeness judgment and blockers

## Evaluation Rubric

| Check | What Passing Looks Like |
| --- | --- |
| Surface neutrality | One source bundle can feed Markdown-native and rendered-image adapters without semantic edits |
| Diagram completeness | Component, sequence, and data-flow diagrams cover the pitch's named seams |
| Contract completeness | Provided/required interfaces have state, owner/action, and evidence |
| Security ownership | Each stated security responsibility has an owner/control, or an explicit unresolved gap |
| No fabrication | Every claim is cited or marked assumed; no invented internals appear |
| Shape Up fit | Appetite, rabbit holes, and no-gos remain visible and the output stays fat-marker |
| Gate readiness | Manifest and statuses let the pitch reviewer fail closed on missing artifacts |

## Full Shaping Handoff

For full runs, require the conductor's current accepted frame/evidence before
Stage 3 authoring; direct artifact requests can remain artifact-only with upstream
status unassessed. Follow the bundle resource for complete contracts and explicit
negative security responsibilities. Keep existing/proposed/unknown contracts distinct.

Render component, sequence and data-flow sources and inspect all pixels for labels,
arrows, boundaries, contrast and evidence fidelity. Syntax success is insufficient.
The embed helper may perform local conversion without permission to publish; actual
placement occurs only after full-run G3 passes. Return complete row/diagram inventory,
source hashes and separate render observations to engos-quality-shaping-gate.

Blast radius: all users of this shared authoring helper gain explicit rendering,
source-bound receipts and exemplar contract coverage; no upstream source repository
or installed native agent configuration is changed by using it.

## Reference-Matched Visual Authoring

Read resources/references/presentation.md with the author route when composing a
shaped bundle. Give every figure an explicit owning section, visible title/caption,
legend and state labels; match rendered samples, not just file inventories. Use
Mermaid-first editable source and the derivatives requested by the selected rich
presentation profile; native-Mermaid-only requests need no extra image step. A curated SVG may
address a documented layout limitation only with preserved source identity and a
semantic cross-check; it may not invent components or hide unknowns.

Keep primary tables readable and retain all richer contract/security fields in
stable-ID supporting detail where needed. The embed adapter owns representation,
asset validation and placement; the author owns coherent source meaning. Complete
source, successful parsing, visual quality and saved-target proof are distinct.

Blast radius: existing artifact authoring gains explicit visual composition and
field-preserving table guidance; stage and external-write authority are unchanged.
