# Model capacity — Stage 3 teaching draft

Status: **review_pending / render_pending**. G0–G2 passed by author inspection under the teaching contract. G3 and G4 have not passed. Source identity: `engos-example-model-capacity/input.md`; every citation below names that case's fixture, not production evidence (`input.md:3-4`).

## Original request

> Include maximum input length in the existing model catalog so our
> builder can prevent requests that are too large. Don't change model selection.

Verbatim source: `input.md:6-7`.

## Problem, use case and business win

Builders learn limits only after submitting, according to the scenario support team (`input.md:11`). The guiding use case is a catalog consumer identifying whether the selected model has a known input-token limit before a request is submitted. A model without a configured limit remains explicitly unknown (`input.md:6-7`, `input.md:12-13`, `input.md:20-22`).

The intended business win is enabling earlier recognition of oversized input while preserving familiar selection and existing consumers. Fewer late failures is an expected benefit, not a measured result or promised reduction. Completion for this slice is the catalog contract, not a new UI or demonstrated prevention in production (`input.md:6-13`).

## Appetite and kill criteria

M1 supplies a hypothetical two engineer-days with one engineer. This is willingness to spend, not an estimate or real staffing commitment (`input.md:9-10`). Abandon the proposed slice if it requires any live provider call or changes existing selection behavior. If preserving known/unknown semantics, compatibility or authorization cannot fit that appetite, return for a new scenario decision; do not relax those guarantees (`input.md:9-13`, `input.md:23-24`).

## Proposed solution and alternatives

Extend the existing ModelCatalog response with optional `inputCapacityTokens`, copying a present positive integer from CatalogConfig for the corresponding model ID. Omit the field when no value is configured. Omission means unknown, never zero, unlimited, or a claim that the model rejects all input. The name and unit come from existing configuration; this response field is **proposed**, not fixture-existing (`input.md:18-22`).

Keep the current catalog operation, existing required model ID/name/provider fields, authorization and config revision binding. Retain config validation before active replacement. No provider lookup, new storage, selection change, or customer text is needed (`input.md:16-28`). Consumers that ignore the optional field retain their current behavior; informed consumers can interpret a present input-token limit. Actual builder prevention remains outside this no-new-UI slice (`input.md:6-13`, `input.md:18-22`).

Alternatives: a required field or zero sentinel would conflict with partial coverage and compatible consumers (`input.md:12-13`, `input.md:18-22`). A nullable field would add a second representation without a supplied need; omission follows the optional-field precedent. Live enrichment violates M1 (`input.md:9-10`). New UI work is unnecessary for the supplied completion condition (`input.md:12-13`).

## In / Out / Later

| Category | Scope and rationale |
| --- | --- |
| In | One optional positive input-token value per configured model; unknown omission; retained required fields, access, config validation and revision binding (`input.md:12-28`) |
| Out | Selection changes and live provider calls (M1); new storage and required UI work are not needed for the fixture outcome (`input.md:9-13`, `input.md:27-28`) |
| Later | Builder experience improvements or additional limit coverage would need separately supplied intent, sources and appetite; neither is a dependency or an approved commitment (`input.md:12-13`, `input.md:20-22`) |

## Ordered cut list

These are proposed cuts if work threatens M1, not claims that extras were requested.

1. Cut optional example polish beyond one known/unknown contract pair; retain the full semantics.
2. Defer any expanded config coverage; preserve honest unknowns for unconfigured models (`input.md:20-22`).
3. Exclude any consumer UI work beyond explaining the response contract; the required outcome does not need a new UI (`input.md:12-13`).
4. Stop and return for a decision if the remaining contract slice exceeds M1. Never cut compatibility, authorization, validation, input-only units or known/unknown distinction to make the budget fit (`input.md:9-13`, `input.md:18-26`).

## Pitch-wide proof slice and workstreams

Proposed first end-to-end proof: read one active catalog revision containing one configured and one unconfigured model through the existing authorized operation. Observe a positive integer for the first and omitted field for the second, unchanged original fields and unchanged legacy selection. A denied session still receives no catalog. This is an acceptance scenario to execute later, not an observed test (`input.md:16-26`).

`ready` below means scoped enough to discuss within this fixture; no work is implemented or independently approved. Every slice inherits the no-gos below.

| Workstream | Status | Visible first slice and completion evidence |
| --- | --- | --- |
| W1 — Catalog API response | ready | Proposed known/unknown response pair from one revision retains ID/name/provider and unit meaning; compare required fields before/after. No zero/null fallback, provider call, storage or selection change (`input.md:18-22`, `input.md:26-28`) |
| W2 — Existing consumer compatibility | ready | Proposed legacy consumer comparison ignores the new optional field and preserves selection; informed consumer reads input-token/unknown meaning without a new UI. Evidence is a future comparison, not a fake consumer method (`input.md:6-13`, `input.md:18-22`) |
| W3 — Existing boundary preservation | ready | Proposed invalid config and denied-session cases show active revision retained and unauthorized catalog withheld. No new authorization service or expanded data scope (`input.md:23-26`) |
| W4 — Live enrichment / selection rewrite / new UI | excluded | M1 forbids first two; M2 requires no new UI. No selected slice depends on them (`input.md:9-13`) |

These are coarse responsibilities for one engineer, not separate team commitments or production tickets. No required `needs_spike` work is hidden in the bet; no spike ran.

## Risks and clearance

R1–R5 are grounded and fully mapped in research-notes. Proposed clearance below remains **unexecuted**.

| Risk | Owner / mitigation | Evidence that would clear the slice |
| --- | --- | --- |
| R1 — Missing mistaken for zero or unlimited | Catalog API and catalog consumers; omission contract | Known/unknown pair verifies positive versus absent, never substituted zero (`input.md:12-13`, `input.md:20-22`) |
| R2 — Wrong capacity unit | Catalog API documents input-only tokens; Builder UI owns its tokenizer use | Contract review and future comparison agree on input tokens, not characters or combined budget (`input.md:21-22`) |
| R3 — Consumer / selection regression | Catalog API preserves optional additive pattern; consumers retain behavior | Future legacy compatibility and selection comparisons pass (`input.md:6-7`, `input.md:18-19`) |
| R4 — Invalid or mixed config revision | Existing config loading and Catalog API retain validation/binding | Future invalid candidate rejection retains active catalog and a response uses one revision (`input.md:25-26`) |
| R5 — Access or sensitive-data expansion | Catalog API retains session checks; CatalogConfig remains metadata-only | Future unauthorized case returns no catalog; response inspection finds no customer text/credentials (`input.md:23-24`) |

Rabbit-hole boundary: do not solve incomplete data with live provider discovery or a config-completeness project. Preserve unknown values and walk away if lookup becomes necessary (`input.md:9-10`, `input.md:20-22`). Risk acceptance is bounded by supplied M1–M4; no author-created production waiver exists.

## Load-bearing no-gos

- No live provider calls or selection changes; requirement triggers M1 stop (`input.md:9-10`).
- No removal of required fields, required new response field, zero/null sentinel, or conflation of input-only and combined limits; these undermine M2 and the supplied contract (`input.md:12-13`, `input.md:18-22`). Null exclusion is part of this proposal, not an asserted existing rule.
- No weakened authorization, customer-text/credential inclusion, invalid candidate activation or mixed-revision response (`input.md:23-26`).
- No new storage or provider request; retain one scalar lookup per row. Derived maximum is 10,000 × 100 = 1,000,000 lookups/day, with no measured latency or dollar-cost claim (`input.md:27-28`).

## Artifact trace and handoff

Component source shows Builder UI / Catalog API / CatalogConfig boundaries. Sequence source covers candidate acceptance/rejection and authorized/denied reads. Data-flow source distinguishes existing model fields from the proposed scalar. The files carry captions, legends, omissions and citations; all are **render_pending**. Full contracts C1–C4 are in contracts.md; security/negative responsibility rows S1–S5 are in security-owners.md.

Trace: Q1 → C2/C4, W1/W2, R1/R2; Q2 → C1/C2, W1/W2, R3; Q3 → C1/C3, W3, R4/R5; Q4 → W1 and the no-storage/no-provider boundary. M1–M4 remain the supplied decisions in decisions.md.

Next: independent reviewer checks source content; controller renders and inspects all three diagrams before judging G3. Target intent is a local HTML reference page; the possible later combined Google Doc does not yet exist in this run (`input.md:30-31`). No HTML, cloud placement, G3/G4 pass, live feasibility or reference-ready certification is claimed here.
