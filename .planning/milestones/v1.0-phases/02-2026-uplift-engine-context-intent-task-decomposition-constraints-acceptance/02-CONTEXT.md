# Phase 2: 2026 Uplift Engine (Context/Intent/Task Decomposition/Constraints/Acceptance) - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the uplift engine that transforms sanitized input into a structured context/intent model, decomposed task graph, explicit constraints model, and deterministic acceptance output.

This phase clarifies HOW to implement this engine. It does not add unrelated capabilities beyond the phase boundary.

In scope for Phase 2 only:
- Context Layer
- Intent Layer
- Task Decomposition
- Constraint Architecture
- Acceptance Criteria

Explicitly out of scope for Phase 2:
- Rosetta translation
- Target tool validation
- Output generation

</domain>

<decisions>
## Implementation Decisions

### Context and Intent Representation
- Primary internal representation is a **structured JSON schema**.
- Extraction mode is **explicit + inferred with flags** (inferred items must be marked, not merged silently).
- Context shape is a **layered object** with separated sections (source, normalized, inferred, constraints, acceptance).
- Representation must include a mandatory **`schema_version`** field with major-version validation behavior.

### Task Decomposition
- Decomposition depth is capped at **two levels max**.
- Output shape is a **dependency-aware DAG** with deterministic serialized order.
- Ordering must use **rule-based canonical sort** with deterministic tie-breakers.
- Granularity target is **atomic + testable** tasks.

### Constraint Handling
- Constraints are classified into **hard** and **soft**.
- Conflicts are resolved with **deterministic precedence rules** and explicit conflict reporting.
- Hard-constraint violations must **fail with structured error payloads**.
- Constraint specification format is **typed structured fields** (not freeform prose).

### Acceptance and Evaluation
- Acceptance model is **hybrid**: pass/fail gate plus scored diagnostic detail.
- Thresholding uses **fixed deterministic thresholds**.
- Acceptance output must include **criterion-by-criterion evidence** with rationale and links to task IDs.
- Ambiguous/incomplete evaluation returns **`NEEDS_REVIEW`** (not pass).

### Scope Locks (Phase 2)
- Do not implement Rosetta translation in this phase.
- Do not implement target tool validation in this phase.
- Do not implement output generation in this phase.

### Carried Forward from Prior Phase
- Output behavior must remain deterministic and roleplay-free where applicable.
- Phase 1 scope exclusions remain valid for this phase context: avoid introducing URL ingestion and downstream execution expansion outside scoped phase goals.

### Claude's Discretion
- Exact field naming conventions and module boundaries inside the schema implementation.
- Specific deterministic tie-breaker key order once category priorities are fixed.
- Internal scoring formula details as long as fixed-threshold and criterion-evidence decisions are preserved.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/intent_pipeline/ingestion/policy.py`: deterministic typed validation and rejection pattern reusable for hard-constraint checks.
- `src/intent_pipeline/sanitization/pipeline.py`: clear pure-function staged pipeline pattern reusable for uplift stages.
- `src/intent_pipeline/summary/renderer.py`: deterministic output normalization/ordering pattern reusable for acceptance report serialization.
- `tests/test_*`: requirement-indexed, deterministic test style already established and should be preserved.

### Established Patterns
- Deterministic, explicit transformations with no probabilistic behavior in core pipeline paths.
- Strong emphasis on typed errors/reasons and stable output ordering.
- Verification via focused pytest modules with repeated-run determinism tests.

### Integration Points
- New uplift engine should connect after sanitization output and before any later routing phases.
- Phase 2 artifacts should feed Phase 3 routing inputs without requiring shape reinterpretation.
- Acceptance evidence should align with traceable requirement/task identifiers for future phases.

</code_context>

<specifics>
## Specific Ideas

- Use one canonical engine contract object containing:
  - `context`
  - `intent`
  - `task_graph`
  - `constraints`
  - `acceptance`
- Include explicit provenance markers (`source`, `inferred`, `confidence`) in inferred fields.
- Serialize DAG deterministically (stable node ordering plus explicit dependency lists).
- Return structured `NEEDS_REVIEW` with missing-evidence keys when acceptance cannot be confidently computed.

</specifics>

<deferred>
## Deferred Ideas

- Rosetta translation (planned for later phase).
- Target tool validation (planned for later phase).
- Output generation (planned for later phase).

</deferred>

---

*Phase: 02-2026-uplift-engine-context-intent-task-decomposition-constraints-acceptance*
*Context gathered: 2026-03-04*
