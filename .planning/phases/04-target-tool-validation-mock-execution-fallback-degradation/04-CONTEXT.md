# Phase 4: Target Tool Validation + Mock Execution + Fallback Degradation - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers deterministic target-tool validation, deterministic mock execution (no side effects), and deterministic fallback degradation over Phase 3 routing outputs.

In scope for Phase 4:
- Validate route-spec targets against typed capability and policy contracts.
- Produce structured dry-run mock execution traces from validated routes.
- Apply fixed fallback degradation tiers when validation/mock paths fail.

Explicitly out of scope for Phase 4:
- User-facing output/help generation.
- Runtime dependency checks.
- Real tool execution or side-effecting actions.

</domain>

<decisions>
## Implementation Decisions

### Target Validation Gate
- Validation mode is **fail-closed** before mock execution.
- Invalid target capabilities/policies produce deterministic blocking validation outcomes.
- Validation outcomes must be machine-verifiable and deterministic for identical inputs.

### Capability Contract Model
- Target capabilities are represented as a **typed capability matrix**.
- Freeform capability metadata is disallowed for core validation paths.
- Capability contract fields must remain schema-versioned and deterministically ordered.

### Mock Execution Semantics
- Mock execution style is **structured dry-run** only.
- Mock outputs must include deterministic step-level simulation details without side effects.
- High-level-only summaries are insufficient for Phase 4 acceptance.

### Mismatch/Error Signaling
- Capability mismatches and policy failures use deterministic machine-readable error codes.
- Error payloads must include explicit evidence paths to offending route/capability fields.
- Human-readable text may supplement but cannot replace stable codes.

### Fallback Degradation Policy
- Fallback strategy is deterministic **tiered degradation**.
- Degradation must follow a fixed ordered ladder, not dynamic best-effort branching.
- Terminal unresolved state must be explicit and deterministic (e.g., `NEEDS_REVIEW`).

### Scope Lock (Phase 4)
- No real execution or external side effects in this phase.
- No output/help rendering logic.
- No runtime dependency check logic.

### Carried Forward Constraints
- Deterministic and roleplay-free behavior remains mandatory.
- Schema-major boundary enforcement from prior phases remains mandatory.
- Missing evidence and ambiguity must remain explicit; no best-guess execution paths.

### Claude's Discretion
- Exact fallback tier labels and internal transition function names.
- Internal module partitioning between validation, dry-run simulator, and fallback resolver.
- Diagnostic payload field naming as long as deterministic code/evidence requirements are preserved.

</decisions>

<specifics>
## Specific Ideas

- Introduce a deterministic `validation_report` artifact before any mock step generation.
- Bind every mock step to route-spec and capability IDs for full traceability.
- Keep fallback ladder auditable by emitting attempted tiers and rejection reasons in order.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/intent_pipeline/routing/contracts.py`: schema-major validation and typed boundary patterns reusable for target capability contracts.
- `src/intent_pipeline/routing/engine.py`: deterministic orchestration pattern reusable for validation -> mock -> fallback pipeline composition.
- `src/intent_pipeline/routing/semantic_router.py`: fixed precedence and explicit ambiguity handling patterns reusable for fallback tier resolution.
- `src/intent_pipeline/routing/rosetta.py`: canonical contract translation patterns reusable for validation/mock artifacts.

### Established Patterns
- Deterministic canonical serialization with stable key ordering and repeated-run byte stability tests.
- Typed error classes with deterministic error codes and structured evidence payloads.
- Strict phase boundary enforcement through dedicated boundary tests.

### Integration Points
- Phase 4 should consume Phase 3 `route_spec` artifacts as its primary input.
- Phase 4 outputs (validation report + mock trace + fallback outcome) should become the primary input contract for Phase 5 output generation.
- Phase 4 must not depend on external tool runtimes; all execution remains simulated.

</code_context>

<deferred>
## Deferred Ideas

- Output generation/help formatting and user-facing response assembly (Phase 5).
- Runtime dependency checks and environment verification (Phase 5).
- Real execution against target tools (future capability, beyond current phase boundary).

</deferred>

---

*Phase: 04-target-tool-validation-mock-execution-fallback-degradation*
*Context gathered: 2026-03-04*
