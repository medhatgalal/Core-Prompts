# Phase 4 Research: Target Validation + Mock Execution + Fallback Degradation

## Scope and Boundary

Phase 4 should consume only Phase 3 `route_spec`-driven artifacts and emit deterministic machine contracts for:
- target capability/policy validation
- mock execution trace (dry-run only)
- fallback degradation outcome

Strictly excluded in this phase:
- real tool/runtime execution
- output/help/assistant text generation
- runtime dependency/environment checks

## Deterministic Implementation Guidance

Recommended deterministic composition (fail-closed):
1. `validate_target(...)` on canonical route + capability matrix.
2. If validation blocks, skip mock execution and run `resolve_fallback(...)` immediately.
3. If validation passes, run `run_mock_execution(...)` (no side effects).
4. If mock trace returns terminal failure, run `resolve_fallback(...)`.
5. Emit one canonical Phase 4 result contract with stable ordering and deterministic enums.

Guidance aligned to Phase 3 patterns (`contracts.py`, `engine.py`, `rosetta.py`, `semantic_router.py`):
- Use frozen `@dataclass(slots=True)` contracts + closed `Enum`s.
- Normalize text fields (`strip`/whitespace collapse) and canonicalize mapping keys.
- Keep rule/error IDs stable constants (no dynamic text-based IDs).
- Preserve byte-stable JSON via `json.dumps(..., sort_keys=True, separators=(",", ":"))`.

## Proposed Phase 4 Requirement IDs

Use these IDs in planning/tests:
- `VAL-01`: Validate route target against typed capability matrix (no freeform capability acceptance).
- `VAL-02`: Validation is fail-closed and deterministic for identical inputs.
- `VAL-03`: Validation failures emit deterministic code + evidence paths.
- `MOCK-01`: Mock execution is dry-run only; no side effects.
- `MOCK-02`: Mock trace is step-level, deterministic, and linked to route/capability evidence.
- `FALLBACK-01`: Fallback degradation follows fixed tier order.
- `FALLBACK-02`: Terminal unresolved outcome is deterministic `NEEDS_REVIEW`.
- `DET-04`: Phase 4 full output is byte-stable across repeated identical runs.
- `BOUND-04`: No real execution, no output/help generation, no runtime dependency checks.

## Typed Contract Recommendations

### 1) Capability Validation Report

```python
@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: ValidationErrorCode
    severity: ValidationSeverity  # BLOCKER | WARNING
    evidence_path: str            # e.g., "route_spec.target.tool_id"
    expected: str | None
    actual: str | None
    message: str                  # deterministic, normalized

@dataclass(frozen=True, slots=True)
class ValidationReport:
    schema_version: str           # "4.0.0"
    route_spec_schema_version: str
    decision: ValidationDecision  # PASS | BLOCK
    target_tool_id: str
    capability_profile_id: str
    checked_capabilities: tuple[str, ...]
    policy_checks: tuple[str, ...]
    issues: tuple[ValidationIssue, ...]
    applied_rule_ids: tuple[str, ...]
```

### 2) Mock Execution Trace

```python
@dataclass(frozen=True, slots=True)
class MockStep:
    step_id: str
    stage: MockStage              # PRECHECK | PLAN | SIMULATE | VERIFY
    action: str
    status: MockStepStatus        # PASS | FAIL | SKIP
    evidence_paths: tuple[str, ...]
    produced_artifacts: tuple[str, ...]
    error_code: MockErrorCode | None

@dataclass(frozen=True, slots=True)
class MockTrace:
    schema_version: str
    decision: MockDecision        # PASS | FAIL
    route_profile: str
    steps: tuple[MockStep, ...]
    applied_rule_ids: tuple[str, ...]
```

### 3) Fallback Outcome

```python
@dataclass(frozen=True, slots=True)
class FallbackOutcome:
    schema_version: str
    decision: FallbackDecision    # DEGRADED | NEEDS_REVIEW
    final_route_profile: str
    chosen_tier: FallbackTier     # TIER_0 | TIER_1 | TIER_2 | TERMINAL
    attempted_tiers: tuple[FallbackAttempt, ...]
    terminal_code: FallbackErrorCode | None
    evidence_paths: tuple[str, ...]
    applied_rule_ids: tuple[str, ...]
```

## Deterministic Error Code Strategy

Use fixed namespaces and never generate codes dynamically:
- Validation: `VAL-*` (e.g., `VAL-001-UNKNOWN_TOOL`, `VAL-002-CAPABILITY_MISSING`, `VAL-003-POLICY_BLOCKED`, `VAL-004-SCHEMA_MISMATCH`)
- Mock: `MOCK-*` (e.g., `MOCK-001-NO_SIMULATION_PLAN`, `MOCK-002-UNSUPPORTED_STEP`, `MOCK-003-INVARIANT_BROKEN`)
- Fallback: `FB-*` (e.g., `FB-001-NO_ELIGIBLE_TIER`, `FB-002-DEGRADATION_EXHAUSTED`)
- Boundary: `BOUND-04-*` (e.g., `BOUND-04-EXECUTION_ATTEMPT`, `BOUND-04-OUTPUT_LAYER_CALL`, `BOUND-04-RUNTIME_CHECK_CALL`)

Rules:
- Every blocking outcome must include `code`, `dominant_rule_id`, and at least one `evidence_path`.
- Keep human-readable `message` supplemental; tests should assert on codes and evidence paths.
- Canonicalize issue/attempt ordering by `(code, evidence_path)` or deterministic tier index.

## Evidence Path Linking

Use dot-path format bound to canonical contracts:
- route spec: `route_spec.<field>`
- validation matrix: `capability_matrix.<tool_id>.<capability_key>`
- mock trace: `mock_trace.steps[<i>].<field>`
- fallback: `fallback.attempted_tiers[<i>].<field>`

Minimum evidence linkage requirements:
- Validation blockers must reference both route field and capability/policy field.
- Mock failures must reference failed step and originating route/capability evidence.
- Fallback terminal outcome must include full attempted tier evidence chain.

## Guardrails (Strict)

Hard boundaries for Phase 4 modules:
- Must not import or call real execution adapters/tool clients.
- Must not import output/help rendering modules.
- Must not import runtime dependency or environment check modules.
- If such calls are attempted, raise typed boundary errors with `BOUND-04-*` codes.

Recommended enforcement style (matching Phase 3 boundary tests):
- AST import boundary tests for forbidden fragments.
- Entry-point signature checks to ensure only contract inputs accepted.
- Composition-order tests to ensure `validate -> mock -> fallback` only.

## Validation Architecture

Proposed module seams:
- `phase4/contracts.py`: enums, dataclasses, schema validation, canonicalization helpers.
- `phase4/validator.py`: capability/policy checks, emits `ValidationReport`.
- `phase4/mock_executor.py`: dry-run simulation, emits `MockTrace`.
- `phase4/fallback.py`: deterministic tier resolver, emits `FallbackOutcome`.
- `phase4/engine.py`: orchestration and final aggregate output contract.

Actionable Phase 4 test strategy mapped to requirement IDs:
1. `test_val_01_typed_matrix_rejects_freeform_capabilities` (`VAL-01`, `VAL-03`)
2. `test_val_02_fail_closed_blocks_mock_on_validation_block` (`VAL-02`, `MOCK-01`)
3. `test_val_03_validation_errors_include_code_and_evidence_paths` (`VAL-03`)
4. `test_mock_01_dry_run_has_no_side_effect_hooks_or_clients` (`MOCK-01`, `BOUND-04`)
5. `test_mock_02_step_trace_is_deterministic_and_evidence_linked` (`MOCK-02`, `DET-04`)
6. `test_fallback_01_degradation_follows_fixed_tier_order` (`FALLBACK-01`)
7. `test_fallback_02_terminal_state_is_needs_review_when_exhausted` (`FALLBACK-02`)
8. `test_det_04_engine_output_is_byte_stable_over_20_runs` (`DET-04`)
9. `test_bound_04_phase4_modules_do_not_import_execution_output_or_runtime_layers` (`BOUND-04`)
10. `test_bound_04_engine_composition_calls_only_validate_mock_fallback` (`BOUND-04`)

## Integration Notes from Existing Code

Patterns to carry forward directly:
- Schema major gating + typed boundary errors from `src/intent_pipeline/routing/contracts.py`.
- Deterministic orchestrator composition from `src/intent_pipeline/routing/engine.py`.
- Canonical evidence linkage style from `src/intent_pipeline/routing/rosetta.py`.
- Fixed precedence and stable rule IDs from `src/intent_pipeline/routing/semantic_router.py`.
- Boundary + byte-stability test style from `tests/test_phase3_boundary.py` and `tests/test_rosetta_translation.py`.

Phase 4 should mirror these patterns to preserve deterministic behavior and clean phase boundaries.
