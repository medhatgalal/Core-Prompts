# Select state-failure probes

Use when persistence or an unresolved operation could change what the person believes happened or what they can safely do next. Select only the relevant probe; static content and changes with no affected state may need none. These probes extend [API and state guidance](api-and-state-design.md), without requiring a new workflow or backend capability.

Use the actual state contract and an authorized test environment. A mock can expose design gaps but cannot establish service behavior. Adapt the failure mechanism to available test controls; report a missing check when access cannot support it. Inspect both the visible claim and the state owner, keeping test records and recovery within scope.

## Persisted state and page-only work

**Select when:** the experience saves local or remote state, or reload, relaunch, or navigation can replace current work.

**Invariant:** draft, page-only state, and durably saved state retain distinct meanings. A failed write cannot silently advance the saved baseline. The person can understand which version will return and what can be recovered before leaving the current work.

**Observed check:** establish a saved version at the actual owner, attempt a changed save with persistence unavailable, and compare the owner's retained value with the current display. Reload or relaunch and inspect the restored version and available recovery. Record whether draft preservation and status match the real contract. For example, a page-only change may coexist with an older saved version; inspect whether the interface explains that the older version will return. Do not invent durable recovery if the product supports only temporary work.

## A reply lost after commitment

**Select when:** a mutation can commit at its owner even if the client receives no reply.

**Invariant:** an absent reply leaves the outcome unresolved until evidence establishes it. Preserve the original operation's identity and intent while reconciling what happened. A replay follows the service's actual duplicate-prevention or reconciliation semantics; visible confirmation accounts for the committed result.

**Observed check:** in the test environment, let the owner commit while withholding the reply from the client. Compare the resulting record or operation status with the interface's claim and next actions. Follow the offered recovery and inspect the owner again for additional effects, as well as the final confirmation. A successful ordinary error retry does not cover this case. If the contract offers no safe way to establish the outcome, make that uncertainty and the available next step truthful; do not invent a lookup or promise that retry is safe.

## Editing or retrying while an operation is unresolved

**Select when:** the person can change input, selection, navigate away, cancel, or retry while a prior operation is pending or its outcome is unknown.

**Invariant:** the submitted intent remains distinguishable from later draft changes. A response belongs to the operation that produced it, even if the visible draft has changed. A retry of that intent and a new operation have distinct consequences; neither can erase an unresolved or committed effect from the visible account.

**Observed check:** hold an operation unresolved and exercise the transitions the interface offers, including a changed draft where supported. Release or reconcile the original outcome, then inspect how the interface associates it with its original intent and how any subsequent action affects the owner. Check preserved input, action meaning, and the final account of effects. Editing may stay available through a separate draft or another coherent treatment; disabling all editing is not a universal requirement. Cancellation means what the service supports, rather than an assumed reversal of commitment.

## Keep the evidence proportional

Record the selected transition, the observed owner state, the visible result, and any mismatch or untested limit in existing checks or handoff notes. Inspect the final working state after the last edit, including relevant focus, status access, and return behavior. Preserve useful composition and meaningful choices; these invariants prescribe no fixed layout. Renew checks when their dependencies or new evidence warrant it, and leave unrelated probes unloaded.
