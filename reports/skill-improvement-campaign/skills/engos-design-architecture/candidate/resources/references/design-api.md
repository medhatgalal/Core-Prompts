# API design playbook

Use for HTTP, RPC, public/internal interfaces and webhooks. Respect the existing protocol and compatibility contract. Resource naming conventions are HTTP design aids, not rules to impose on RPC. Choose the smallest artifact that makes the interface implementable: a precise catalog and examples, or a machine-readable contract when requested/useful.

## Inspect and decide

Identify resources, aggregates, lifecycle, callers, ownership, tenant/trust boundaries and authoritative state. Inspect current contracts and clients before changing wire behavior. Define operations, validation, authorization, errors, retry behavior, pagination/filter/sort interactions, quotas, synchronous/asynchronous completion, and event/webhook obligations that apply.

For HTTP, use resource nouns and shallow nesting where ownership permits; action endpoints can be justified by domain operations. Distinguish PUT replacement from PATCH partial change. Choose versioning from client compatibility needs; neither path nor header versioning is a universal default.

## Required API artifacts

- Resource/operation inventory with state owner and allowed transitions.
- Endpoint or RPC catalog and concrete request, success and validation/error examples.
- Authentication plus object/action/tenant authorization; define what errors may reveal.
- Compatibility/deprecation and client migration plan, including old/new coexistence.
- Contract validation plan and failure/retry scenarios.

### Endpoint Catalog Template

| Method / operation | Path / interface | Caller and authorization | Input / validation | Success / errors | Retry / concurrency | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| POST / submit | `/jobs` | Authenticated tenant principal, submit right | Input object; request identity | Accepted job identity or documented error | Defined key scope and conflict policy | Polling contract when asynchronous |

### Concrete retry contract

For retry-prone writes define the operation identity, scope (including tenant and operation), request equivalence, retention horizon and behavior after expiry. Specify concurrent same-key requests, a reused key with a different request, timeout after the effect committed, in-progress response, stored result/recovery, and the boundary that atomically owns the effect. An idempotency header alone does not prevent duplicate effects. If a downstream system cannot deduplicate or reveal completion, state that uncertainty and a reconciliation path instead of promising exactly-once execution.

Separate HTTP method idempotence from business deduplication. Bound retries and identify which errors are retryable; do not let layered retries multiply load without a budget. If updates compete, select a conditional write/version check or other concrete concurrency mechanism and its failure response.

For list APIs specify deterministic ordering/tie-breaker, page/cursor semantics under mutation, bounds and how authorization/filtering affect the result. For events/webhooks specify event identity, schema version, authentication, replay window, duplicates, ordering scope, delivery retries, quarantine and subscriber migration where applicable.

### Example: accepted asynchronous operation

```json
{"job_id":"job_7","status":"queued","status_url":"/jobs/job_7"}
```

```json
{"type":"https://example.test/problems/request-conflict","title":"Request conflict","status":409,"detail":"The request identity was reused with different input."}
```

These are illustrative payloads, not complete security or persistence designs. Accompany them with actual request fields, auth, response codes and a validation example for the requested domain. Do not leak tokens, stack traces, internal queries or other tenants' identifiers in errors.

## Machine-readable contracts and checks

When OpenAPI is appropriate, use the project's supported specification/dialect and validator. OpenAPI security alternatives and combined requirements have different semantics; inspect them instead of assuming a security declaration enforces tenant ownership. Define required/nullable fields and examples coherently. An OpenAPI diff can identify wire-contract changes; it cannot prove business compatibility, deployed enforcement or semantic equivalence. Do not install or call remote validators as a side effect of analysis. Propose their use or run only already-authorized lightweight local checks.

For event-first interfaces, consider AsyncAPI if it matches existing tooling; specify application delivery semantics outside what the schema can prove. Do not require both OpenAPI and AsyncAPI for every task.

## Adverse cases and rejection criteria

Trace timeout-before-commit and timeout-after-commit, concurrent duplicate requests, cross-tenant resource access, invalid input, lost updates, rate-limit behavior and old-client compatibility as applicable. Reject undocumented retry-prone writes, leaked errors, unexplained breaking changes and contradictions between examples and contract. Retain a safe existing API when changing it would add no justified value.

Sources checked 2026-09-10: [HTTP semantics, sections 9 and 13](https://www.rfc-editor.org/rfc/rfc9110.html), [Problem Details security and format](https://www.rfc-editor.org/rfc/rfc9457.html), [OpenAPI 3.2 specification](https://spec.openapis.org/oas/v3.2.0.html), [AsyncAPI 3.0 specification](https://www.asyncapi.com/docs/reference/specification/v3.0.0), [oasdiff project](https://github.com/oasdiff/oasdiff). Version choice still follows the user's toolchain; current publication is not proof that a particular tool supports it.
