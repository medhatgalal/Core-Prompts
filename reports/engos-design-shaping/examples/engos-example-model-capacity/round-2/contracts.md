# Model capacity round 2 — complete scoped contract inventory

Source: `engos-example-model-capacity/input.md`; teaching premises only (`input.md:3-4`). C1–C4 cover the selected boundaries, not a whole-product API inventory. Method names and HTTP paths are not supplied; descriptions below are operations, not invented callable methods. No new endpoint is proposed.

| ID | Method / Endpoint | Purpose | Producer → consumer; kind | Inputs / outputs and material failure semantics | State and evidence |
| --- | --- | --- | --- | --- | --- |
| C1 | Existing catalog read; actual HTTP method/path unspecified and unchanged | Return authorized ModelCatalog | Catalog API → Builder UI / existing catalog consumers; network | Existing user/session context; model ID, name, provider retained; response bound to config revision. Existing authorization remains prerequisite; denied access must not expose catalog. Error codes and revision wire format unspecified and unchanged. | Existing fixture contract; `input.md:16-19`, `input.md:23-26` |
| C2 | Additive field on C1, not a method or endpoint | Expose known input-token capacity | Catalog API → catalog consumers; proposed network payload extension | Per model ID, present configured positive integer maps to optional inputCapacityTokens. Omit when absent; omission = unknown. No zero, null, unlimited or combined-budget representation. Preserve required fields and C1 access/revision semantics. Missing capacity is not an API failure; invalid candidate config follows C3. | Proposed response extension; configuration field and optional additive precedent are fixture-existing, `input.md:12-13`, `input.md:18-26` |
| C3 | Existing config loading; signature unspecified | Validate candidate before active replacement | CatalogConfig → Catalog API's configuration loading; internal data boundary, transport/in-process signature unspecified | Candidate model values positive when present. Reject invalid candidate before replacement; keep active catalog. Response data bound to config revision. Exact exception format/storage internals not given and not changed. | Existing fixture contract; preserving it is a proposal constraint, `input.md:16-17`, `input.md:20-26` |
| C4 | Consumer interpretation of C2; no new callable API | Distinguish known input-token limit from unknown | ModelCatalog → Builder UI / catalog consumers; data interpretation, not a new network call | Present positive integer denotes input tokens using the supplied tokenizer's unit; absent denotes unknown, not zero/unlimited. Legacy consumers may ignore optional field. No automatic selection change or new UI requirement; actual pre-submit enforcement is not delivered here. | Proposed interpretation; tokenizer unit and additive tolerance are existing premises, `input.md:6-13`, `input.md:18-22` |

Proposed acceptance examples: a configured positive value is returned unchanged; an unconfigured model omits the field; invalid candidate values do not replace active data; an unauthorized request yields no catalog. These specify checks, not executed results (`input.md:12-13`, `input.md:20-26`). No sample number is presented as a real model's capacity.

No new timeout, retry, cache, credential exchange, persistence or provider protocol is introduced. The fixture bounds this addition to one scalar lookup per row, at most 100 rows/read and 10,000 reads/day (`input.md:27-28`). Existing unspecified internals remain unspecified. Rendering and independent review are pending.

## Round-two semantic constraints and exact acceptance

M2 protects exact positive input values, absent/unknown, input-only units and valid older callers. Optional presentation polish is the only cut (round-two-clarifications.md:10-16). No fake method name or executed check is implied.

| Check | Given | Required observable result, proposed and unexecuted |
| --- | --- | --- |
| A1 known | Active revision contains positive input-token value v for a model | Response field exists and equals v exactly, original fields from the same revision retained. No output capacity substituted |
| A2 absent | Active revision has no capacity for that model | Response field absent, not null, zero, unlimited or a guessed value. Existing required fields unchanged |
| A3 legacy | Valid older caller sees the response with the optional field | Caller remains valid and its selected model matches the baseline without the field. No mandatory consumer/UI change |
| A4 invalid candidate | Active revision r remains available while a candidate fails existing validation | Candidate not activated. Subsequent response still has r's original fields and r's capacity/absence, not a mixture |
| A5 access | Caller lacks existing session authorization | No ModelCatalog data disclosed, existing failure semantics retained |

A1/A2 cite input.md:20-22 and round-two-clarifications.md:10-13. A3 cites input.md:6-7,18-19 and clarification lines 12-13. A4 cites input.md:25-26; r and v are symbolic acceptance inputs, not actual observations. A5 cites input.md:23. These sharpen independent review's requested proof plan without claiming proof.

## Limited actual schema evidence, separate from A1–A5

Controller supplied and executed the [declared extension schema](../contract-checks/engos-example-capacity.schema.json) against [ten cases](../contract-checks/cases.json), using installed jsonschema. [observed.json](../contract-checks/observed.json) records all ten expectations matched: absence, positive integer, minimum positive and unrelated-field cases accepted; zero, negative, null, string, boolean and fractional values rejected. Author opened all three files and verified the schema/case hashes match the receipt. Author did not rerun the probe.

This is actual controller-reported contract-only validation, not a fixture production fact or spike. The schema has no required properties and allows additional properties: it checks only this optional extension's shape. It does not validate required existing model fields, exact copy/omit mapping, token units, revision consistency, valid older callers, selection, authentication or invalid-config activation. The case named `other-fields-preserved` demonstrates tolerance of an unrelated field, not preservation by an application. A1–A5 therefore remain unexecuted API/consumer checks.

Schema SHA-256: `f02c8c25593be28f32861aa3d6311d2f8f2d475a0a77e708e5b0f731d103ea86`. Cases: `88c8504791e602c78e77bfb5b958fa928e3dccf55474c93bcc43549f3603e862`. Observed receipt: `08c531d0eba3e5e29a936adec36c93fc3d98620774d64c0d435d1337fc8382ca`. These external teaching-probe files are read-only inputs to round two.
