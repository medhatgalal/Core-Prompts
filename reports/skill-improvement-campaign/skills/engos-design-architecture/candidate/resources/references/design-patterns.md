# Design patterns playbook

Use for modular structure, dependency inversion, plugin boundaries and refactoring under real change pressure. Diagnose the responsibility or variation that is painful before naming a pattern. A stable small conditional may be the right design.

## Inspect

Read the relevant callers, dependencies, tests and available change history. Identify duplicated rules, tight coupling, unclear state/lifecycle ownership, hidden globals, creation complexity, leaky external semantics and concrete extension pressure. Unknown pain is grounds for a provisional diagnosis, not a new abstraction by default.

## Required pattern artifacts

- Diagnosis with evidence and scope.
- Pattern/approach fit matrix with viable alternatives, including no change or local simplification when appropriate.
- Recommended boundary and before/after responsibilities/dependencies.
- Public contract including error, identity, state and lifecycle obligations where relevant.
- Testability/replacement impact and a reversible refactor sequence.

### Pattern Fit Matrix Template

| Approach | Actual pressure it addresses | Fit and cost | Testability / ownership | Keep or reject and why |
| --- | --- | --- | --- | --- |
| Current conditional | Small stable variation | Lowest moving parts | Explicit owner | Retain if evidence supports it |
| Adapter / facade | External semantics leak into callers | Translation maintenance | Boundary conformance tests | Choose only for the observed mismatch |
| Factory / builder | Creation variation / staged construction | Indirection and validation cost | Explicit construction ownership | Match actual complexity |

Prefer composition and dependency inversion when they simplify the real model. Inheritance needs an explicit substitutability case. Treat Singleton skeptically because global access often hides state/lifecycle and test dependencies; do not mechanically reject an already appropriate shared immutable object. Plugin architectures require a stable extension contract and actual independent variation. Avoid introducing builders for trivial construction.

### Before/after boundary example

```text
Before: InvoiceService -> ProviderA SDK types and ProviderB error codes
After:  InvoiceService -> PaymentPort -> Provider adapter(s)
```

A useful port states caller obligations, operation identity and typed outcomes:

```text
PaymentPort.submit(operation_id, amount_minor, currency)
  -> Accepted(provider_reference)
   | Rejected(reason_code)
   | OutcomeUnknown(reconciliation_reference)
```

Define which owner retries, deduplicates, allocates/closes clients, maps errors and reconciles unknown outcomes. Do not hide all failures behind a string return or retry ambiguous external effects inside every layer. The interface may be in-process; it does not require another deployed service. Use the actual language/types when concrete code artifacts are requested, labeled as proposed design.

## Sequence and validation

Establish observable current behavior, extract one seam, keep a compatibility adapter, migrate callers incrementally, verify contract conformance and remove old paths only after the observation window. State how to restore the old call path and what state/resources must survive. Validate representative success, error, unknown outcome, initialization and shutdown behavior where these can change. Do not run the refactor or suite merely to make the recommendation.

Use a decision record for the tradeoff and reconsideration trigger. If no material pressure warrants a pattern, say so and give a specific trigger for revisiting it. An appropriate no-change recommendation is useful output.

Source aid checked 2026-09-10: [Microsoft anti-corruption layer](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer) describes semantic translation, operational costs, in-process or service deployment and when the pattern is unnecessary. The port example here is an illustrative local design, not vendor SDK code or a measured best practice.
