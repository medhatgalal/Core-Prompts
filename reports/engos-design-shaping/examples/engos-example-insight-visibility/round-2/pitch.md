# Insight visibility: daily adoption without support requests

Stage 3 teaching draft, **review_pending / render_pending**. Source identity: `engos-example-insight-visibility/input.md` plus I1/I2 in `round-two-clarifications.md`. Checks below are proposed and unexecuted.

## Problem and desired result

> Make insights more useful. We can't tell whether anyone cares.

Original statement, `input.md:5`. Product managers currently request monthly adoption counts from support (`input.md:8`). I1 now selects a specific outcome: permitted product managers see existing viewed/generated daily counts in the existing internal reporting tool without requesting them from support. The business win is direct visibility and less support-mediated reporting, not improved insight quality or a measured productivity gain (`round-two-clarifications.md:20-25`).

## Appetite and proposed approach

The hypothetical appetite is one week with one engineer. Kill the bet if publication needs customer text, new metric computation or a new analytics service (`round-two-clarifications.md:22-24`).

Propose an aggregate-only publication step within InsightService using MetricsPlatform's existing daily intake. Send approved S1 records: pseudonymous account ID, UTC date, viewed count and generated count. Preserve the source counts; do not calculate a new adoption metric. Existing intake replaces the same account/day record idempotently, and the existing product-manager role governs viewing (`input.md:9-12`, `round-two-clarifications.md:27-31`). The publication step is new proposed work, not an existing export claimed to run today.

Continuing monthly support requests misses I1's outcome. A new analytics service violates the kill condition. Ranking or AI changes lack a supported problem and are excluded (`input.md:14`, `round-two-clarifications.md:21-24`).

## Scope and cuts

**In:** activation-forward daily counts and existing reporting access. **Out:** customer text/prompts, new metrics, content/ranking changes and a new service. **Later:** historical publication; it is explicitly not a completeness dependency (`round-two-clarifications.md:20-34`).

Ordered proposed cuts: first optional presentation polish, then optional extra explanatory views beyond the two requested counts. History is already excluded, not a claimed saving. If the remaining core exceeds the appetite, return for a decision. Never trade away field restrictions, access checks, account/day replacement or the two-count outcome.

## Visible slices and clearance

The first proposed end-to-end slice publishes one retained activation-forward account/day record, shows its unchanged counts to a permitted product manager and withholds it from an unauthorized user. Repeat the record to demonstrate replacement rather than double counting. [Full contracts and acceptance](contracts.md) specify the boundary behavior.

| Workstream | Status | Visible first slice |
| --- | --- | --- |
| Aggregate projection | ready for fixture discussion | Only four S1 fields cross, no document text or prompt |
| Existing intake integration | ready for fixture discussion | Same-key repeat leaves one record, corrected counts replace it |
| Reporting and failure visibility | ready for fixture discussion | Authorized counts visible, denied user blocked, failed publication not reported as complete |

Principal risks are content leakage, double counting, access expansion and incomplete publication after quota/retention limits. [Research notes](research-notes.md) and [security owners](security-owners.md) assign mitigation and future clearance. The nominal 1,000 records/day is 10% of the 10,000-record quota, not guaranteed retry headroom. Source retention is 30 days; unavailable data must not become invented zeros (`round-two-clarifications.md:32-34`).

Inspect the [component](component.mmd), [sequence](sequence.mmd) and [data-flow](data-flow.mmd) sources. Controller rendering, pixel inspection and independent review remain pending. The [journal](journal.md) records fresh sequential gates; advancement reflects new fixture inputs, not demonstrated capability improvement.
