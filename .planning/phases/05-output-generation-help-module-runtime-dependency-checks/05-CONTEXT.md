# Phase 5: Output Generation + Help Module + Runtime Dependency Checks - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 delivers deterministic user-facing output generation, deterministic help-module responses, and deterministic runtime dependency checks over Phase 4 artifacts.

In scope for Phase 5:
- Generate canonical output artifacts from `Phase4Result` (`validation`, `mock`, `fallback`) with stable ordering.
- Provide deterministic help responses for usage, troubleshooting, and boundary guidance.
- Run runtime dependency preflight checks and emit typed pass/fail/degraded outcomes.

Explicitly out of scope for Phase 5:
- Real tool/action execution and side-effecting runtime operations.
- New routing/validation/fallback logic beyond consuming Phase 4 contracts.
- URL ingestion or network-fetch based dependency remediation.

</domain>

<decisions>
## Implementation Decisions

### Output Surface Contract
- Phase 5 output must provide two deterministic surfaces:
  - machine contract payload (typed, schema-versioned)
  - human-readable rendered text (fixed section order)
- Output renderer consumes Phase 4 artifacts as immutable evidence inputs.
- Output remains strictly roleplay-free and deterministic for identical inputs/config.

### Help Module Behavior
- Help module uses deterministic intent categories:
  - usage guidance
  - failure explanation
  - remediation hints
  - boundary clarification
- Help content is generated from fixed templates and typed codes, not freeform persona text.
- Help responses must explicitly reference evidence/code paths when available.

### Runtime Dependency Check Policy
- Dependency checks are preflight-only and side-effect free.
- Dependencies are classified as:
  - required (missing => blocking)
  - optional (missing => degraded)
- Check outputs must be typed, deterministic, and schema-versioned with stable ordering.

### Failure and Degradation Semantics
- Missing required dependency yields deterministic blocking output code and explicit check evidence.
- Missing optional dependency yields deterministic degraded status with actionable but non-executing guidance.
- Output/help modules must preserve Phase 4 terminal states (`NEEDS_REVIEW`) without auto-upgrading outcomes.

### Scope Lock (Phase 5)
- No runtime auto-install, patching, or external tool invocation.
- No new execution engine behavior in this phase.
- No non-deterministic response synthesis.

### Carried Forward Constraints
- Deterministic canonical serialization and byte-stability remain mandatory.
- Typed code + evidence-path diagnostics remain mandatory.
- Explicit ambiguity and missing-evidence handling remains mandatory; no best-guess completion.

### Claude's Discretion
- Exact output section labels and human-text phrasing within deterministic template constraints.
- Internal module boundaries between output renderer, help resolver, and dependency checker.
- Check-group naming and tie-break ordering where semantics remain deterministic.

</decisions>

<specifics>
## Specific Ideas

- Introduce a canonical Phase 5 aggregate result contract containing:
  - output payload/text
  - help payload/text
  - dependency-check report
- Map Phase 4 typed codes to help-topic templates for deterministic remediation messaging.
- Keep dependency-check evidence explicit (dependency ID, scope, status, reason code).

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/intent_pipeline/summary/renderer.py`: deterministic fixed-template rendering pattern reusable for human-readable output/help sections.
- `src/intent_pipeline/phase4/contracts.py`: typed schema-versioned contract and deterministic ordering patterns reusable for Phase 5 contracts.
- `src/intent_pipeline/phase4/engine.py`: strict ordered orchestration pattern reusable for Phase 5 pipeline composition.
- `tests/test_phase4_determinism.py`: repeated-run and cross-process byte-stability strategy reusable for Phase 5 determinism checks.

### Established Patterns
- Dataclass + Enum typed contracts with schema-major validation at boundaries.
- Canonical JSON serialization (`sort_keys=True`, fixed separators) for deterministic payloads.
- Dedicated boundary tests to prevent cross-phase leakage and forbidden imports/calls.

### Integration Points
- Phase 5 should consume `run_phase4(...)` output contract directly as primary upstream input.
- Output/help runtime-check artifacts should become final user-facing surfaces for current milestone scope.
- Dependency-check status should integrate with Phase 4 `decision`/`fallback` outcomes without mutating them.

</code_context>

<deferred>
## Deferred Ideas

- Auto-remediation or package installation for missing dependencies.
- Real tool execution after dependency pass.
- External service/network-backed help enrichment.

</deferred>

---

*Phase: 05-output-generation-help-module-runtime-dependency-checks*
*Context gathered: 2026-03-05*
