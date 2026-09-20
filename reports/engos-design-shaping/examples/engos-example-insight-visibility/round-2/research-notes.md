# Insight visibility — round 2 fixture research

Opened original input lines 1–19 and clarification lines 18–34. G1 now passes on new supplied decisions; no runtime or spike was executed. Existing facts below are fixture premises, proposed behavior is labeled separately.

| ID | Disposition / answer | Evidence / uncertainty |
| --- | --- | --- |
| RQ1 | answered: InsightService already records viewed/generated account/day aggregates. Approved S1 contains pseudonymous account ID, UTC date and those two counts; no document text/prompts may cross | `input.md:9-10`, `round-two-clarifications.md:27-31`; use existing schema, no new pseudonymization or metric formula asserted |
| RQ2 | answered: existing MetricsPlatform daily intake accepts S1 and idempotently replaces the same account/day record | `input.md:11-12`, `round-two-clarifications.md:28-29`; exact callable method/path and failure codes unspecified, no new endpoint required |
| RQ3 | answered: metric reads use the existing service credential and product managers use the existing platform role | `round-two-clarifications.md:29-31`; no new credentials/scopes or content access granted |
| RQ4 | answered: 1,000 accounts/day, platform quota 10,000 records/day, source retention 30 days, activation forward only, history Later | `round-two-clarifications.md:32-34`; nominal one-record/account/day load is 10% of quota, not observed capacity or guaranteed retry headroom |

Selected seams have supplied contract premises. No live feasibility is established. Proposal: an aggregate-only publication step within InsightService uses the existing daily intake; MetricsPlatform presents the accepted records to its existing product-manager role. This is new use of existing contracts, not an existing implemented export or a new analytics service (`input.md:9-12`, `round-two-clarifications.md:20-34`).

## Risks, owners and future clearance

| Risk | Proposed mitigation / responsible component | Required clearance evidence, not executed |
| --- | --- | --- |
| R1 — Content leakage because counts and customer content coexist (`input.md:9-10`) | InsightService publication step allowlists exactly S1 fields; platform retains approved-schema boundary | Inspect submitted record: only pseudonymous ID, UTC date, viewed count, generated count; a content-bearing candidate is withheld (`round-two-clarifications.md:27-31`) |
| R2 — Duplicate day counted twice (`round-two-clarifications.md:28-29`) | MetricsPlatform retains replacement semantics; proposed publisher sends current account/day record, not increments | Repeat identical account/day payload: one record with unchanged counts, not a sum; corrected payload replaces that key. No exactly-once claim |
| R3 — Read or reporting access expands (`round-two-clarifications.md:29-30`) | InsightService uses existing metric-read credential; MetricsPlatform checks existing PM role | Denied metric read produces no publication; unauthorized reporting user sees no records; no credential in payload |
| R4 — Quota exhaustion, stale replay or retention loss (`round-two-clarifications.md:32-34`) | Proposed InsightService step serializes submissions for a key, stops on failure or quota denial and reconciles the latest source value before a bounded rerun | Verify current-account/day replacement and total submissions within approved available quota; do not assume unlimited retries. After data expires, flag unavailable rather than fabricate zeros/history |

R4 mitigation is proposed failure behavior, not an assertion of existing retries, transactional delivery, backfill or platform quota allocation. Detailed scheduling/recovery internals remain builder choices inside these boundaries. Failure handling must expose incomplete publication rather than report success. No new metric computation, customer text or analytics service may become a dependency; otherwise I1 kills this bet (`round-two-clarifications.md:23-24`).

History is explicitly excluded from selected work, with I2 provenance (`round-two-clarifications.md:33-34`). Correcting a retained activation-forward account/day record is replacement of the selected data, not a promise to backfill pre-activation history. No missing row is interpreted as a zero count; that is a proposed reporting integrity rule, not an added source fact.
