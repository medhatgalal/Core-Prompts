# Model capacity — Stage 1 frame

Source identity: `engos-example-model-capacity/input.md`; teaching premises only (`input.md:3-4`). Original statement remains verbatim in intake.

**Problem and people.** Builders discover input limits after submitting. They need advance knowledge without changing how a model is selected (`input.md:6-7`, `input.md:11`).

**Why now.** The scenario support team reports this late discovery; no incident rate or financial loss is supplied (`input.md:11`).

**Desired outcome.** Catalog consumers can distinguish a known limit from an unknown one and existing consumers keep working. This enables the builder's stated prevention use case; delivering a new UI is not required (`input.md:6-7`, `input.md:12-13`).

**Appetite.** M1 is a hypothetical willingness to spend two engineer-days with one engineer, not an estimate or a real team commitment (`input.md:9-10`).

**Walk away.** Stop if the outcome needs live provider calls or changes to existing selection behavior (`input.md:9-10`). Do not silently expand the supplied appetite.

**Boundaries.** Include advance input-limit knowledge and backward-compatible consumer behavior. Exclude selection changes and any requirement for a new UI (`input.md:6-13`). Existing authorization and exclusion of credentials/customer text from catalog configuration are system constraints, not proposed mechanisms (`input.md:23-24`).

## Research questions

| ID | Question | Evidence needed |
| --- | --- | --- |
| Q1 | What capacity data exists, what does it measure, and what does absence mean? | Fixture data and unit definitions |
| Q2 | Can consumers receive additional information without breaking the existing contract? | Fixture consumer compatibility constraints |
| Q3 | Who controls access and keeps invalid source values from becoming active? | Fixture authorization, validation and revision responsibilities |
| Q4 | Can the bounded outcome avoid live lookups and new storage at the stated workload? | Fixture serving pattern, volume and per-row work |

No response field, endpoint, algorithm, component design or implementation step is selected in this frame.
