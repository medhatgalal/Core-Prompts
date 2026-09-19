# Model capacity — round 2 frame

Source: `engos-example-model-capacity/input.md` and model M2 in `round-two-clarifications.md`. Original statement is retained in intake.

**People/problem/why now:** Builders learn limits only after submission, per the scenario support report (`input.md:6-7`, `input.md:11`).

**Desired outcome:** Consumers distinguish an exact known positive input-token limit from unknown. Older callers remain valid, model selection stays unchanged and no output-token limit is substituted. No new UI is required (`input.md:12-13`, `round-two-clarifications.md:10-13`).

**Appetite and walk-away:** Two engineer-days with one engineer; walk away if live provider calls or selection changes are necessary. Only optional presentation polish may be cut (`input.md:9-10`, `round-two-clarifications.md:14-15`). These are hypothetical decisions, not an estimate.

**Boundaries:** Include honest known/unknown information and compatibility. Exclude invented defaults, unlimited interpretations and output-capacity substitution. Preserve existing access and non-sensitive catalog data (`input.md:23-24`, `round-two-clarifications.md:10-14`).

| Question | Evidence required before choosing a solution |
| --- | --- |
| Q1 — Which values and units exist, and what does absence mean? | Fixture data definitions plus M2 semantics |
| Q2 — Can information be added without breaking older callers? | Existing consumer contract |
| Q3 — What owns access, validation and response consistency? | Existing boundary responsibilities |
| Q4 — What workload fits without provider calls or new storage? | Fixture volume and serving pattern |

No selected response shape, endpoint or build steps. Existing boundaries and desired semantics constrain research rather than prescribe implementation.
