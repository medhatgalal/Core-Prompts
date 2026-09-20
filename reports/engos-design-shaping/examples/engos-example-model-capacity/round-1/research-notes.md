# Model capacity — Stage 2 fixture research

Source identity: `engos-example-model-capacity/input.md`. All 31 lines were opened with line numbers. These are stipulated teaching premises, not code inspection or runtime results (`input.md:3-4`). G1 passed before this file was authored. No spike was needed or executed in this exercise.

## Question dispositions

| ID | Disposition and answer | Evidence / scope | Uncertainty and consequence |
| --- | --- | --- | --- |
| Q1 | answered: CatalogConfig has inputCapacityTokens for some model IDs. Present values are positive integers measuring input tokens only; builder tokenizer uses that unit. Absence means no supplied known value, not zero. | `input.md:20-22`; known/unknown required by `input.md:12-13` | Output encoding is a design proposal, not an existing response fact. No provider accuracy or freshness guarantee is supplied. |
| Q2 | answered: ModelCatalog contains model ID, name and provider; consumers support optional additive fields and required fields must remain. | `input.md:18-19` | This establishes an additive precedent within the fixture; exact HTTP method/path and code symbols are not supplied and will not be invented or changed. |
| Q3 | answered: Catalog API owns existing user/session authorization. CatalogConfig has no credentials/customer text. Config loading rejects invalid candidate values before replacing the active catalog; one revision binds response data. | `input.md:23-26` | Enforcement internals and error codes are unspecified; retain the stated boundary rather than claim an implementation. |
| Q4 | answered: Catalog API serves versioned configuration without per-request provider calls. At 10,000 reads/day and at most 100 rows, the supplied addition is one scalar lookup per row, no new storage or provider request. | `input.md:16-17`, `input.md:27-28` | Derived upper bound: 1,000,000 scalar lookups/day. This is arithmetic on the fixture, not measured latency, cost or capacity. |

All selected-scope questions have fixture answers. Unknown transport names and implementation internals are not new seams: the proposal retains the existing catalog operation unchanged. If later implementation reveals a different contract, this teaching verdict supplies no authority to override it.

## Grounded risks and proposed clearance checks

Owners below are component responsibilities from the fixture, not invented teams. Clearance checks are future acceptance evidence, not executed results.

| ID | Grounded risk | Proposed mitigation / responsible component | Clearance evidence required; stop boundary |
| --- | --- | --- | --- |
| R1 | Some models lack capacity; coercing absence to zero would contradict known/unknown intent (`input.md:12-13`, `input.md:20-22`) | Catalog API maps only present values; catalog consumers interpret absence as unknown | Proposed contract examples show positive value retained and absent value omitted, never zero; reject draft/implementation if absence becomes zero or unlimited |
| R2 | Input-only token unit can be misrepresented as combined capacity (`input.md:21-22`) | Catalog API documents input-token semantics; Builder UI remains responsible for any use of its tokenizer | Proposed comparison checks use the same unit; stop if conversion, output budgeting or a new tokenizer is required |
| R3 | Existing consumers and selection must survive (`input.md:6-7`, `input.md:18-19`) | Catalog API adds optional data only; consumers retain existing selection | Future compatibility comparison preserves required fields and selection; abandon if selection changes become necessary (M1) |
| R4 | Invalid candidate values must not replace active response data (`input.md:25-26`) | Existing config loading retains validation and revision binding | Future invalid-candidate rejection leaves active catalog intact; mixed-revision response blocks acceptance |
| R5 | Existing access and non-sensitive data boundaries must survive (`input.md:23-24`) | Catalog API retains authorization; CatalogConfig remains metadata-only | Future denied-session check exposes no catalog; response contains no credentials or customer text; stop if authority/data scope expands |

No risk is declared eliminated. Supplied decision M1 excludes live-provider lookup and selection changes; it does not grant a new production risk waiver (`input.md:9-10`).

## Proposal carried to Stage 3, subject to G2

Propose one optional response field named `inputCapacityTokens`, reusing the configuration's name and unit; omit it when not configured. This is a proposed response-contract extension, not a claim that ModelCatalog already exposes it (`input.md:18-22`). Retain existing operation, authorization, required fields, validation and revision binding (`input.md:16-26`). Null/zero defaults and live enrichment are unnecessary alternatives, not missing research results.
