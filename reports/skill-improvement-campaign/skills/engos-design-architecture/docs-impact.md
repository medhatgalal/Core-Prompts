# Proposed user documentation for an accepted Architecture candidate

Draft text for coordinator integration. Shared docs are unchanged. Do not publish this as shipped behavior until the same-slug candidate and generated resources are accepted. Preserve existing general examples that remain valid; update them in place rather than adding another overview.

## README orientation

In the current Architecture capability entry, explain the practical addition:

> Architecture turns API, data, module and system questions into one implementation-usable decision: explicit contracts, viable alternatives, failure behavior and migration/recovery. It selects the relevant design guides and can recommend keeping a simple existing design.

No model name, benchmark win or experimental evaluator details belong in the user-facing capability description.

## Getting started

Add or update one first-success request:

> Use `engos-design-architecture` to assess whether our billing module should become a separate service. The invoice and ledger currently share a transaction; clients retry; old clients need seven days of compatibility. Give an inline recommendation with alternatives, state ownership, migration/rollback and the checks needed before implementation. Do not implement it.

Expected result: one coherent recommendation that makes the state/compatibility tradeoff explicit, with a bounded validation handoff. Missing inputs produce stated assumptions or focused questions. An inline request creates no files.

## EXAMPLES Architecture section

Replace the current generic capability-layout example with representative asks and expected artifacts:

| Ask | Useful output |
| --- | --- |
| “Design a tenant-scoped async job API where clients retry after timeout.” | Operation catalog and request/success/error examples; authorization, deduplication/concurrency, compatibility and validation |
| “Introduce tenant-local document IDs while old writers continue.” | Schema/keys, query-index mapping, compatibility matrix, backfill reconciliation and recovery boundary |
| “Providers leak status semantics into callers; avoid adding a service.” | Pattern fit including current design, before/after interface, error/lifecycle ownership and reversible refactor |
| “Can twelve workers handle our burst under a one-minute completion target?” | Explicit capacity/backlog math, feasibility limits, admission/degradation, measurable signals and staged rollout |

Explain that a pure staged-diff review goes to Code Review, test generation to Testing Review and release gates to GitOps. Architecture can hand off acceptance criteria but does not execute the migration or deploy the design.

## Maintainer and generated docs

Regenerate catalog/status/release-delta through the canonical workflow after accepted source/resource integration. Review CLI reference only if exposing resource-loader usage to maintainers; direct users should not need a manual loader to ask a design question. Record changed format applicability and resource selection in the changelog. Preserve scorecard dimensions/thresholds while documenting that self-scoring is not independent proof. Do not advertise token/latency/quality improvements until valid matched evidence exists.

## Integration sequence and shared ownership

Coordinator reviews complete entry plus resources and preservation map, resolves routing overlap and the explicit output-format requirement change, runs same-slug UAC plan/judge/apply with the retained global install target, and promotes candidate resources to `sources/capability-resources/engos-design-architecture/` only in that accepted slice. Regenerate surfaces serially. Update resource-aware Architecture tests, descriptor expected outputs, reviewed Goal Contract/topology and docs together; do not weaken tests just to accept a shorter body.

The initial read-only UAC outputs used default target inference and report repo-local installation despite the unchanged source `install_target: global`; they are diagnostics, not an approved final write set. The full authored resource bundle must participate in the final review. Preserve current curated descriptor lineage and benchmark sources; verify the suspected upstream source-link path drift separately. No owner-side shared metadata or generated surface edits were made.

The initial UAC preview also wraps the submitted file under `Imported operating instructions`, so its rendered SSOT is not byte-identical to the authored experiment entry. Quality-loop checking was explicitly off (`quality_status: null`); no benchmark pass is established. The coordinator must resolve the final same-slug ingestion/write set and evaluate the actual complete emitted treatment if that wrapper will ship. Do not evaluate the raw candidate then silently ship a different wrapper.

Revision note: the initial UAC diagnostics are retained at their original submitted C1 identity; the revised candidate adds explicit caller vendor/framework/portability preservation. Those diagnostic previews do not establish acceptance of the revised source. New public examples test simple retained designs and concrete artifact work; RPC/webhook/event breadth remains unmeasured.
