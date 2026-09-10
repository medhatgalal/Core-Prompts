# Shared decision and evolution guidance

Use with every selected mode. Keep one framing and decision record for a mixed-mode request. Templates are content aids; instantiate relevant fields without duplicating entire reports.

## Decision record

Record context and the concrete decision, status (`proposed` unless acceptance is evidenced), chosen option, viable rejected options, constraints driving the choice, positive/negative consequences, owner or owner-to-confirm, and revisit condition. Preserve superseded rationale with a replacement reference. An ADR documents a decision; it does not approve or execute it.

| Decision | Options | Recommendation and reason | Cost / risk | Evidence | Revisit when |
| --- | --- | --- | --- | --- | --- |
| Deployment boundary | Existing module / separate service | Choose from observed scale, ownership and release needs | Operations, consistency and compatibility | Current source or stated assumption | Specific workload or ownership change |

## Trace the important contracts

For each critical boundary name caller, owner, input/output, error, authority, state transition and lifecycle. Link material requirements to an enforcing mechanism and a validation observation. Do not write a catalog of every possible risk. Select scenarios that could invalidate this decision and expose unresolved conflicts.

| Invariant or requirement | Mechanism / owner | Adverse scenario | Observable check | Remaining evidence |
| --- | --- | --- | --- | --- |
| One accepted effect per operation | Chosen commit/deduplication boundary | Timeout after commit followed by retry | Effect count plus returned operation identity | Concurrency rehearsal proposed |

A trace is a design argument until executed. Show causal steps, not private internal reasoning or a simulated test receipt.

## Migration and recovery

For meaningful schema, interface or topology changes, give:

1. Preconditions: current versions/data, authority for execution, backup/restore expectations, dependency readiness and compatibility constraints.
2. Expand: introduce compatible readers/writers/interfaces. State what old and new versions can read and write together.
3. Migrate: backfill or replay in bounded batches; state source of truth, concurrent-write handling, checkpoints, reconciliation and failure restart behavior.
4. Cut over: identify routing/read/write switches, observation window and objective abort criteria. Name owner/owner-to-confirm for each gate.
5. Contract: remove compatibility only after consumers and rollback windows are verified. Identify the first irreversible step and its consequences before recommending it.
6. Roll back or recover: reverse compatible steps in dependency order, account for new data/events and external effects, and give a roll-forward/restore/compensation plan where simple reversal is unsafe. Do not promise zero data loss or a recovery time without evidence.

| Phase | Old/new compatibility | Gate and observation window | Stop trigger | Reversal or recovery | Owner |
| --- | --- | --- | --- | --- | --- |
| Expand / migrate / cutover / contract | Reads, writes, stored formats | Observable threshold or unresolved target | Named failure | Ordered action and data consequences | Known or proposed |

For unchanged architecture, say no migration is required and why. For a new design, describe staged adoption and removal/replacement of newly introduced state where meaningful. Do not invent a backfill for an empty system.

## Validation and useful handoff

Give the next engineer a finite list: deliverable/interface, dependency, invariant, acceptance observation, failure control and owner gap. Distinguish proposed checks, static checks actually run, and live behavior not observed. Test plans should name inputs and expected outcomes; deeper test generation and execution belong to separate authorized work.

Use diagrams at the level the audience needs. Label boundaries, protocols and state; distinguish in-process modules from deployed services. A dependency arrow does not establish atomicity or availability. Reuse a small context/component view plus one critical sequence when helpful rather than drawing every level automatically.

Source aids: [C4 diagram selection](https://c4model.com/diagrams), [Nygard decision records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions). Consult platform-specific compatibility documentation when a concrete migration depends on its behavior. These references support practices, not local acceptance evidence.
