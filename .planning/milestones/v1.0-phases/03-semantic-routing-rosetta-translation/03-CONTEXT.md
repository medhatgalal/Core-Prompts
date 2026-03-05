# Phase 3: Semantic Routing & Rosetta Translation - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers deterministic semantic routing and Rosetta translation over Phase 2 uplift artifacts.

In scope for Phase 3:
- Derive routing outcomes from uplift context/intent/task/constraint/acceptance artifacts.
- Translate routed intent signals into a canonical route-spec schema (Rosetta layer).
- Preserve deterministic, schema-versioned behavior for identical inputs.

Explicitly out of scope for Phase 3:
- Target tool validation and mock execution.
- Output generation/help rendering.
- Runtime dependency checks.

</domain>

<decisions>
## Implementation Decisions

### Routing Basis and Signal Precedence
- Primary routing basis is intent + constraints, not task graph-first or acceptance-first.
- Cross-layer precedence is fixed: hard constraints > intent > task graph > acceptance.
- Acceptance remains a supporting routing signal, not the primary gate in this phase.

### Rosetta Translation Scope
- Rosetta translation normalizes routed signals into a single deterministic canonical route-spec schema.
- Translation does not rewrite the full uplift contract.
- Translation is contract-preserving and additive to existing Phase 2 artifacts.

### Ambiguity and Missing Evidence Handling
- Ambiguous or incomplete routing evidence must emit deterministic `NEEDS_REVIEW` outcomes.
- `NEEDS_REVIEW` outcomes must include explicit missing-evidence fields, not silent fallback guesses.
- Best-guess routing is disallowed for Phase 3.

### Route Target Taxonomy
- Route targets are represented as a fixed closed enum profile set.
- Freeform dynamic route labels are disallowed for determinism.
- Numeric scoring can exist as secondary diagnostics but not as the sole route output.

### Scope Lock for Phase 3
- Phase 3 produces routing + translation artifacts only.
- No tool validation, no execution, and no output generation logic are introduced in this phase.

### Carried Forward Constraints
- Deterministic and roleplay-free behavior remains mandatory.
- Phase 1 and 2 schema/version and explicit-vs-inferred traceability constraints remain in force.

### Claude's Discretion
- Exact enum member names for the fixed route profile set.
- Canonical route-spec field names and ordering, provided schema-version and determinism guarantees hold.
- Internal helper/module boundaries for routing and translation layers.

</decisions>

<specifics>
## Specific Ideas

- Make route-spec the only Rosetta output artifact consumed by downstream phases.
- Keep route outcomes explainable by including dominant-signal provenance (which layer won precedence).
- Preserve compatibility by keeping the uplift contract intact and attaching route-spec as deterministic adjunct output.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/intent_pipeline/uplift/engine.py`: canonical integration point producing deterministic uplift artifacts suitable as routing input.
- `src/intent_pipeline/uplift/contracts.py`: schema-versioned typed contract patterns reusable for route-spec typing.
- `src/intent_pipeline/uplift/constraints.py`: deterministic hard/soft precedence logic pattern directly reusable in routing precedence.
- `src/intent_pipeline/uplift/intent_layer.py` and `task_decomposition.py`: stable semantic/task signals for route classification and translation mapping.

### Established Patterns
- Deterministic canonical serialization and stable key ordering are enforced by tests and should be preserved.
- Schema-major validation gates are used at layer boundaries and should continue for route-spec evolution.
- Unknown/missing evidence is represented explicitly rather than guessed; Phase 3 should mirror this behavior.

### Integration Points
- Phase 3 should sit immediately after Phase 2 uplift composition (`run_uplift_engine`) and before Phase 4 validation/execution logic.
- Route-spec output should become the primary input contract for Phase 4 target tool validation.
- Routing/translation outputs should be testable via deterministic byte-stability and precedence-conflict matrix tests.

</code_context>

<deferred>
## Deferred Ideas

- Target tool validation + mock execution + fallback degradation (Phase 4).
- Output generation + help module + runtime dependency checks (Phase 5).
- URL ingestion and downstream execution expansion beyond current roadmap boundaries.

</deferred>

---

*Phase: 03-semantic-routing-rosetta-translation*
*Context gathered: 2026-03-04*
