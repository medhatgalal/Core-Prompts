# Deploy cost definitions while preserving target edits

Stage 3 teaching draft, **review_pending / render_pending**. Source identity: `engos-example-config-deployment/input.md`; added scenario decisions C2–C4 are hypothetical. G0–G2 author checks are recorded in [journal.md](journal.md). No production behavior or test execution is certified.

## Problem and bet

The customer re-enters cost settings after every deployment. The guiding use case is deploying a process with its currency/activity definitions while preserving target-local choices and older packages. The business win is avoiding repeated entry, without a quantified savings claim (`input.md:6-13`). The original statement remains verbatim in [intake.md](intake.md).

Appetite is one week with two engineers. Stop if target override protection cannot hold (`input.md:9-12`). The protected core is indivisible: removing either definition type, compatibility or preservation would break the request. Existing deployment boundaries make this a bounded proposal, not a proven delivery estimate.

## Proposed flow

PackageExporter adds an optional cost-definition section using CostConfigStore's stable process UUID association. A failed source read aborts export; it must not become absence. PackageImporter retains existing deployment authorization and encrypted transport (`input.md:16-23`, `input.md:32-33`, `round-two-clarifications.md:59-60`).

Absent configuration preserves currency and activities. An empty activity list preserves activities; valid currency-only input updates currency alone. Nonempty definitions apply after compatibility, authorization and override checks. Zero and positive activity costs are valid; negative values and unsupported currencies fail validation. Deletion stays out (`round-two-clarifications.md:38-48`, `round-two-clarifications.md:57-62`).

The existing transaction compares revisions at commit and rolls back all package changes on conflict. Specifically, an edit after validation must cause visible conflict, retaining that target edit. Explicit target-admin force is a separate decision, never a blanket bypass for subsequent edits; the proposed interaction requires a fresh authorized attempt after conflict. No lock or API method is invented (`input.md:11-12`, `input.md:19-21`, `round-two-clarifications.md:41-46`).

C4 bounds the complete package: 20,000 activity records, 100 proposed currency records and 4,000 other records total 24,100 against the existing 25,000 capacity. Larger packages are rejected intact under this new scenario requirement, never split. This is C4 evidence, not original-input or runtime proof (`input.md:31`, `round-two-clarifications.md:51-62`). RunningAnalysis reads committed settings on its next normal run (`input.md:28-29`).

## Choices, scope and stops

Manual re-entry leaves the pain unchanged. Always-overwrite violates preservation. A separate cost transaction loses all-or-nothing behavior. Immediate recomputation violates the supplied boundary (`input.md:13`, `input.md:19-29`).

**In:** additive currency/activity deployment within C4, existing explicit force, compatibility and atomic preservation. **Out:** deletion, oversized packages, results/customer transactions, unrelated configuration, new roles/credentials/transport and reload/history recomputation. **Later:** no additional product feature committed; review/rendering are validation work, not product scope (`input.md:10-12`, `input.md:23`, `input.md:28-33`, `round-two-clarifications.md:38-62`).

Ordered cuts: first optional presentation polish, then extra walkthrough examples beyond required proof coverage. There is no authorized functional cut to the protected core; if it cannot fit the week, stop and reshape. Kill on silent concurrent overwrite, absence/empty deleting data, read failure disguised as absence, invalid partial application, or silent package splitting. Detailed risk owners and clearance checks are in [research-notes.md](research-notes.md), P1–P7; none has run.

## Visible first slices and handoff

W1, export: distinguish valid empty/currency-only input from read failure. W2, import: demonstrate one-process success, preservation cases and the validation/edit/commit conflict interleaving. W3, boundaries: demonstrate C4 maximum/oversize outcomes and ordinary next-run analysis. All are ready for teaching design, not implementation acceptance; proof criteria are P1–P7.

Complete supporting sources: [contracts.md](contracts.md), [security-owners.md](security-owners.md), [component.mmd](component.mmd), [sequence.mmd](sequence.mmd), [data-flow.mmd](data-flow.mmd). Controller must rerender all three and inspect pixels; independent review is pending. No G3/G4 pass or placement is claimed.
