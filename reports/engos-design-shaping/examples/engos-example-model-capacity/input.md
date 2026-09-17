# Model capacity scenario

Constructed teaching fixture. Every fact below is a scenario premise, not live
code or production evidence. Cite this file by line for fixture facts.

Raw input: "Include maximum input length in the existing model catalog so our
builder can prevent requests that are too large. Don't change model selection."

Scenario decision M1: willing to spend two engineer-days with one engineer. Walk
away if it requires live provider calls or changes to existing selection behavior.
Why now: the scenario support team reports builders learn limits only after submit.
Done: catalog consumers can distinguish a known limit from an unknown one and
existing consumers keep working. No new UI is required.

System facts:
- Builder UI calls the existing authenticated Catalog API; that API serves a
  versioned catalog assembled from configuration. It does not call providers per request.
- ModelCatalog currently returns model ID, name and provider. Optional additive
  fields are supported by its consumers; required fields cannot be removed.
- CatalogConfig already has inputCapacityTokens for some model IDs, but not all.
  Values are positive integers when present. It measures input tokens only, not
  combined input/output capacity, and the builder's tokenizer produces that unit.
- Access remains with the Catalog API's existing user/session authorization.
  CatalogConfig contains no credentials or customer text.
- Config loading validates positive values and fails the candidate config before
  replacing the active catalog. A config revision binds the response data.
- Scenario volume: 10,000 catalog reads/day, at most 100 model rows per response.
  One optional scalar lookup per row; no new storage or provider request.

Target for this exercise: a local HTML reference page. A separate combined
Google Doc may be used later to test placement; no writer may claim it already exists.
