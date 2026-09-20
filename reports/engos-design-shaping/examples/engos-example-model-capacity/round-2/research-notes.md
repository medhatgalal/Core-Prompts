# Model capacity — round 2 fixture research

Opened original input lines 1–31 and clarification lines 1–16. Premises only, no code or spike execution. G1 passed before this artifact.

| ID | Disposition / answer | Evidence and remaining limit |
| --- | --- | --- |
| Q1 | answered: configured capacities are positive input-token integers and may be absent; exact positives and unknown absence are mandatory | `input.md:20-22`, `round-two-clarifications.md:10-13`; no provider freshness claim |
| Q2 | answered: optional additive fields supported, existing required fields retained; valid older callers must continue working | `input.md:18-19`, `round-two-clarifications.md:12-13`; HTTP method/path unspecified and unchanged |
| Q3 | answered: Catalog API owns session access; config loading rejects invalid candidates before replacing active data; revision binds response | `input.md:23-26`; internal signatures remain unspecified |
| Q4 | answered: configuration-backed reads without provider calls; 10,000 reads/day, at most 100 rows, one scalar lookup per row, no new storage | `input.md:16-17`, `input.md:27-28`; at most 1,000,000 lookups/day is derived arithmetic, not measured cost |

No unresolved selected-scope dependency in this teaching fixture. Proposal for Stage 3: optional response `inputCapacityTokens`, copy exact configured value, otherwise omit. This adapts the existing config field and additive precedent; it is not already exposed in the fixture (`input.md:18-22`).

## Risks and clearance requirements

All checks below are proposed and unexecuted. They address the independent review's request for sharper acceptance without pretending to raise confidence through prose.

| Risk / owner | Mitigation and exact future clearance | Grounding |
| --- | --- | --- |
| R1 — False known limit / Catalog API and consumers | Known positive `v` returns exactly `v`; absent config has no response field, not zero/null/default/unlimited; output capacity is never substituted | `input.md:20-22`, `round-two-clarifications.md:10-13` |
| R2 — Compatibility or selection regression / Catalog API and Builder UI | Compare original required fields and legacy caller selection with/without optional field; equality required, no new UI dependency | `input.md:6-13`, `input.md:18-19` |
| R3 — Invalid activation or mixed revisions / existing config loading and Catalog API | Invalid candidate is rejected, subsequent read retains previous active revision's original fields and capacity together; no mixed revision | `input.md:25-26` |
| R4 — Access/data scope expansion / Catalog API and CatalogConfig | Denied session sees no catalog; source/response inspection has no credentials or customer text | `input.md:23-24` |

Scope discipline: no material safe feature cut exists in this selected core. Only optional presentation polish can go; if core exceeds M1, return for a decision instead of weakening semantics (`round-two-clarifications.md:14-16`).

Review follow-up: sequence messages will use plain text/commas instead of semicolons. This is a source repair, not render proof; controller must rerender all three sources (`round-one-render-observations.md:3-11`, `round-one-render-observations.md:20-22`).
