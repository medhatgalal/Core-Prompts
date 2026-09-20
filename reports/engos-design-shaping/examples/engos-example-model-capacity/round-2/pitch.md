# Model capacity: expose an honest input limit

Stage 3 teaching draft, **review_pending / render_pending**. Source identity: `engos-example-model-capacity/input.md` plus M2 in `round-two-clarifications.md`. API and consumer acceptance checks remain unexecuted.

## Problem and payoff

> Include maximum input length in the existing model catalog so our
> builder can prevent requests that are too large. Don't change model selection.

Original request, `input.md:6-7`. Builders currently learn limits after submission (`input.md:11`). The guiding use case is a consumer recognizing a known input limit before submission while treating missing information honestly. The intended business win is earlier recognition of oversized requests without disrupting selection. This slice delivers catalog information, not a new UI or a measured reduction in failures (`input.md:12-13`).

## Appetite and proposal

Spend at most two engineer-days with one engineer. Walk away if live provider calls or selection changes become necessary (`input.md:9-10`).

Propose optional `inputCapacityTokens` in ModelCatalog. Copy the configured positive input-token value exactly; omit the field when absent. Unknown is never zero, unlimited, null or a guessed default. Do not substitute output capacity. This is a proposed response extension using the existing configuration field and optional-additive consumer precedent (`input.md:18-22`, `round-two-clarifications.md:10-13`).

Retain original required fields, authorization, validation and revision binding. A response's capacity and original fields must belong to the same active revision (`input.md:18-26`). A mandatory new field or default limit would break the requested semantics; live enrichment violates the walk-away. A separate endpoint adds no required outcome and is not selected.

## Scope, cuts and no-gos

**In:** exact known/unknown input-limit information through the existing catalog. **Out:** selection changes, provider lookups, new storage and required UI work. **Later:** any richer builder presentation needs another decision (`input.md:9-13`, `input.md:27-28`).

There is no meaningful safe feature cut in this core. Ordered cuts are (1) optional decorative presentation and (2) optional explanatory example polish. Neither removes the known/absent acceptance pair or supporting contracts. If the core cannot fit, return for a decision. Do not cut semantics, backward compatibility or security (`round-two-clarifications.md:14-16`).

## Proof slice, workstreams and risks

The first proposed end-to-end slice returns one known and one absent limit from an authorized catalog read. Then compare a legacy caller and reject an invalid config candidate. [Exact acceptance expectations and complete contracts](contracts.md) define unchanged values, omitted fields, unchanged selection and retention of the previous revision. No hidden UI work is required.

Limited actual evidence: the controller's [schema-only probe](../contract-checks/observed.json) records all ten declared valid/invalid cases matching expectations. It validates positive-integer-or-absent shape only. It does not test exact data mapping, older callers, selection, authorization or config activation; allowing an unrelated field is not proof that an application preserves it.

| Workstream | Status | Visible first slice |
| --- | --- | --- |
| Response projection | ready for fixture discussion | Positive value copied exactly, missing field omitted, one revision retained |
| Consumer compatibility | ready for fixture discussion | Older caller remains valid and chooses the same model |
| Existing boundaries | ready for fixture discussion | Invalid candidate preserves active data, denied session exposes no catalog |

All inherit the no-gos. Missing-as-zero, mixed revisions, broken callers and widened access are the principal risks. Their owners, mitigations and unexecuted clearance checks are in [research notes](research-notes.md) and [security responsibilities](security-owners.md). One scalar lookup per row stays within the supplied workload; no measured latency claim is made (`input.md:27-28`).

Review the [component](component.mmd), [sequence](sequence.mmd) and [data-flow](data-flow.mmd) sources alongside those tables. The sequence text is repaired, but all three need controller rendering and pixel inspection. [The journal](journal.md) records actual gates and review changes; no G3/G4 pass is claimed.
