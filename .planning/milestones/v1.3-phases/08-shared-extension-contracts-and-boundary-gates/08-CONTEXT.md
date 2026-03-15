# Phase 8: Shared Extension Contracts and Boundary Gates - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 establishes the shared deterministic policy contracts and fail-closed boundary gates that all extension paths must satisfy before any URL ingestion (Phase 9) or controlled execution (Phase 10) behavior is enabled.

In scope for Phase 8:
- Define versioned extension policy artifacts with stable rule identifiers.
- Define deterministic decision/evidence contracts used by extension gates.
- Enforce default-disabled extension behavior and fail-closed gate semantics.
- Add boundary and determinism regression checks for extension-disabled and extension-enabled decision paths.

Explicitly out of scope for Phase 8:
- Implementing live URL ingestion behavior (`EXT1-*` delivery remains Phase 9).
- Implementing execution adapters or side-effecting execution (`EXT2-*` delivery remains Phase 10).
- Expanding capability surface beyond closed contract definitions.

</domain>

<decisions>
## Implementation Decisions

### Policy artifact contract and versioning
- Introduce a dedicated extension-policy contract schema with explicit version string and stable `rule_id` fields.
- Policy evaluation uses canonical, deterministic ordering (`rule_priority`, then `rule_id`) with conservative tie-breakers.
- Any missing/invalid policy artifact is a blocking gate outcome, never an implicit fallback to permissive behavior.

### Extension mode defaults and gate posture
- Extension mode defaults to disabled/fail-closed unless explicitly enabled by validated policy artifacts.
- Phase-8 gate outcomes are typed and deterministic, with explicit terminal outcomes (`BLOCK`, `NEEDS_REVIEW`, `ALLOW`) plus evidence paths.
- Unknown mode values, unknown route profiles, or unknown capabilities are treated as hard-block conditions.

### Determinism and evidence contract
- Extension gate outputs must be byte-stable for identical input and policy versions.
- Every gate decision includes: policy version, matched rule IDs, deterministic decision code, and ordered evidence references.
- Canonical serialization remains `sort_keys=True` with stable sequence ordering for list fields.

### Boundary compatibility and non-regression
- Existing local-file pipeline behavior must remain unchanged when extensions are disabled.
- Phase 8 introduces no side-effecting paths: no network I/O, no process execution, no runtime mutation.
- All new gates integrate as additive preconditions to existing Phase 4/5 contracts, not replacements.

### Claude's Discretion
- Exact module names for new shared extension contracts/gate helpers.
- Exact typed enum names for gate outcomes and reason codes.
- Test fixture layout as long as deterministic and boundary coverage criteria are met.

</decisions>

<specifics>
## Specific Ideas

- Keep gate outputs intentionally compact and audit-friendly: one canonical decision block plus ordered evidence array.
- Use a single shared contract primitive for both Phase 9 and Phase 10 to avoid divergent policy semantics.
- Preserve language consistency with v1.2 governance artifacts (`defer/defer` baseline, re-entry by explicit criteria only).

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/intent_pipeline/ingestion/policy.py`: existing local-source policy structures can host extension-aware admission preconditions.
- `src/intent_pipeline/routing/contracts.py`: schema-version validation and deterministic contract serialization patterns.
- `src/intent_pipeline/phase4/contracts.py` and `src/intent_pipeline/phase4/validator.py`: typed validation and fail-closed gating primitives.
- `src/intent_pipeline/phase4/fallback.py`: deterministic terminal-state and evidence-path conventions (`NEEDS_REVIEW`).
- `src/intent_pipeline/phase5/contracts.py`: typed output/report envelope patterns reusable for extension decision reporting.
- `tests/test_phase4_boundary.py`, `tests/test_phase5_boundary.py`, `tests/test_phase4_determinism.py`, `tests/test_phase5_determinism.py`: existing boundary and determinism harnesses to extend.

### Established Patterns
- Dataclass + enum contracts with schema-major validation at boundaries.
- Canonical payload serialization for reproducibility.
- Strict phase boundary tests that ban side-effecting imports/operations in dry-run/non-execution paths.
- Explicit, typed error/reason code patterns with evidence references.

### Integration Points
- Add shared extension contract definitions under `src/intent_pipeline/` where both Phase 9 ingestion and Phase 10 execution flows can import them.
- Insert shared gate evaluation before extension-specific behavior branches are allowed.
- Ensure gate decision payloads flow into downstream phase artifacts without mutating existing Phase 4/5 semantics.

</code_context>

<deferred>
## Deferred Ideas

- URL canonicalization edge implementation details and snapshot materialization mechanics (Phase 9).
- Execution approval adapter behavior, idempotency ledger implementation, and execute-eligible orchestration (Phase 10).
- Authenticated retrieval profiles and write-capable execution modes (future milestone scope).

</deferred>

---

*Phase: 08-shared-extension-contracts-and-boundary-gates*
*Context gathered: 2026-03-06*
