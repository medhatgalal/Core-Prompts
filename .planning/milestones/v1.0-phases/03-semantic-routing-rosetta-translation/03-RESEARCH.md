# 03 Research — Semantic Routing & Rosetta Translation

Date: 2026-03-04
Phase: 03-semantic-routing-rosetta-translation
Scope lock: Deterministic semantic routing + Rosetta route-spec translation only.

## Research Outcome

Phase 3 should introduce a deterministic routing layer that consumes Phase 2 uplift artifacts and emits a canonical Rosetta `route_spec` contract. The implementation should remain pure and side-effect free, preserve schema-major gating, and produce identical byte output for identical inputs.

Phase 3 output should be additive, not destructive:
- Preserve the Phase 2 uplift contract unchanged.
- Attach or return a separate Phase 3 route-spec artifact derived from uplift signals.
- Never perform target validation, execution, or output/help generation in Phase 3.

## Inputs Reviewed

- `.planning/phases/03-semantic-routing-rosetta-translation/03-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- `src/intent_pipeline/uplift/engine.py`
- `src/intent_pipeline/uplift/contracts.py`
- `src/intent_pipeline/uplift/constraints.py`
- `src/intent_pipeline/uplift/intent_layer.py`
- `src/intent_pipeline/uplift/task_decomposition.py`
- `tests/test_uplift_engine_pipeline.py`

## Baseline Constraints To Preserve

- Determinism and roleplay-free behavior remain mandatory across all code paths.
- Schema-major validation gates are required at contract boundaries.
- Stable ordering and canonical serialization must be preserved (`sort_keys=True`, deterministic list ordering).
- Unknown or missing evidence must be explicit; no best-guess routing.
- Precedence is fixed: hard constraints > intent > task graph > acceptance.

## Recommended Architecture

## Standard Stack

- Python dataclasses with `frozen=True, slots=True` for contracts and immutability.
- Enum-backed decision and error code types for deterministic branching.
- Pure functional composition pattern matching `run_uplift_engine(...)` style.
- Canonical JSON serialization via `json.dumps(..., sort_keys=True, separators=(",", ":"))`.

## Architecture Patterns

1. Phase 3 entrypoint consumes uplift payload, not raw text.
- Recommended entrypoint signature:
  - `run_semantic_routing(uplift: UpliftContract) -> RoutingContract`
- Keep uplift production in Phase 2 (`run_uplift_engine`) and Phase 3 composition separate.

2. Split routing and translation concerns into separate modules.
- `routing/contracts.py`: Phase 3 schema types and validation.
- `routing/semantic_router.py`: deterministic classification using precedence rules.
- `routing/rosetta.py`: normalize routing decision into canonical `route_spec`.
- `routing/engine.py`: orchestration and schema boundary enforcement.

3. Make route target taxonomy a closed enum.
- Route targets must be fixed enum members.
- Freeform/dynamic route names are disallowed.
- Numeric scores may exist only as diagnostics, never as sole output.

4. Represent ambiguity as first-class output.
- Route decision must support `NEEDS_REVIEW`.
- `NEEDS_REVIEW` requires explicit `missing_evidence` and `ambiguity_reasons` fields.

## Data Contracts

Recommended Phase 3 top-level contract:

```python
@dataclass(frozen=True, slots=True)
class RoutingContract:
    schema_version: str  # 3.x
    uplift_schema_version: str  # expected 2.x input
    route_spec: RosettaRouteSpec
    diagnostics: RoutingDiagnostics
```

Recommended canonical route-spec contract:

```python
@dataclass(frozen=True, slots=True)
class RosettaRouteSpec:
    schema_version: str  # 3.x
    route_profile: RouteProfile  # closed enum
    decision: RouteDecision  # PASS_ROUTE | NEEDS_REVIEW | BLOCKED
    dominant_signal: SignalLayer  # HARD_CONSTRAINT | INTENT | TASK_GRAPH | ACCEPTANCE
    supporting_signals: tuple[SignalReference, ...]
    required_capabilities: tuple[str, ...]
    policy_constraints: tuple[RouteConstraint, ...]
    task_focus_ids: tuple[str, ...]
    acceptance_gate: str  # PASS | FAIL | NEEDS_REVIEW from uplift acceptance
    missing_evidence: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
```

Contract rules:
- `schema_version` major must be `3`; reject non-`3.x` output writes.
- Input uplift schema major must be `2`; reject unsupported input major.
- Tuples/lists sorted deterministically before serialization.
- `task_focus_ids` must be subset of uplift task graph node IDs.
- `decision=NEEDS_REVIEW` is mandatory when required evidence is missing or route tie is unresolved.

## Deterministic Routing Flow (Recommended)

1. Validate uplift schema and required fields.
2. Build normalized signal bundle from uplift layers:
- Hard constraints (`constraints.applied_hard`) as top-priority gates.
- Intent signals (`primary_objective`, `in_scope`, `quality_constraints`, `unknowns`).
- Task graph structure (`nodes`, `edges`, dependency density, tagged constraint keys).
- Acceptance state (`decision`, hard criterion failures, missing evidence).
3. Apply precedence engine:
- Hard constraint gate first.
- If not decisive, evaluate intent mapping rules.
- If still unresolved, use task graph pattern rules.
- Acceptance only refines/blocks outcomes; it does not override stronger layers.
4. Resolve ambiguity deterministically:
- If multiple profiles tie after all deterministic tie-breakers, return `NEEDS_REVIEW` with reasons.
5. Translate selected route into canonical Rosetta `route_spec`.
6. Canonicalize and serialize output.

## Algorithm Options

Option A (recommended): Deterministic rule matrix
- Implement explicit decision-table rules with stable rule IDs.
- Pros: Highest explainability, easiest auditability, deterministic by construction.
- Cons: Requires up-front rule maintenance.

Option B: Weighted signals with deterministic tie-breakers
- Compute bounded integer scores per profile then tie-break by fixed lexical/profile order.
- Pros: Flexible for nuanced routing.
- Cons: Harder to reason about than pure decision table.

Option C: Hybrid gate + score
- Hard/intent gates first, weighted scoring only among surviving candidates.
- Pros: Preserves precedence while allowing nuanced secondary ranking.
- Cons: More moving parts and validation burden.

Recommendation:
- Use Option C with strict constraints:
  - Gates decide admissibility.
  - Scoring is secondary diagnostics.
  - Any unresolved tie returns `NEEDS_REVIEW`.

## Don’t Hand-Roll

- Do not introduce probabilistic/LLM-based routing in Phase 3.
- Do not implement dynamic plugin discovery for route profiles.
- Do not infer missing evidence via heuristics that hide uncertainty.
- Do not collapse routing + target validation into one phase path.

## Common Pitfalls

- Treating acceptance as primary router instead of supporting signal.
- Allowing soft constraints to override hard constraints.
- Emitting route profile without explicit evidence provenance.
- Returning default route on missing fields instead of `NEEDS_REVIEW`.
- Introducing non-deterministic ordering via sets/dicts without canonical sort.

## Failure Modes and Deterministic Handling

| Failure Mode | Deterministic Handling | Outcome |
| --- | --- | --- |
| Unsupported uplift schema major | Raise typed boundary error with stable code (`UNSUPPORTED_INPUT_SCHEMA`) | Hard failure |
| Missing required uplift sections (`intent`, `constraints`, etc.) | Emit structured validation error with missing field list sorted | Hard failure |
| Hard constraints imply incompatible routing outcomes | Emit `NEEDS_REVIEW` with `ambiguity_reasons` and winning/losing rule IDs | Soft stop |
| Intent unknowns block profile selection | Emit `NEEDS_REVIEW` + `missing_evidence` | Soft stop |
| Task focus IDs not present in task graph | Reject translation with typed contract violation | Hard failure |
| Canonicalization drift between runs | Determinism test fails on byte mismatch | Test failure |

## Validation Architecture

Validation should be requirement-indexed and split into contract, algorithm, boundary, and determinism suites.

Proposed Phase 3 requirement IDs:
- `ROUTE-CTX-01`: Router accepts only schema-compatible uplift artifacts.
- `ROUTE-PREC-01`: Precedence order is enforced exactly (`hard > intent > task > acceptance`).
- `ROUTE-ENUM-01`: Route profile is always a closed enum member.
- `ROUTE-UNK-01`: Missing/ambiguous evidence yields `NEEDS_REVIEW` with explicit fields.
- `ROSETTA-01`: Rosetta translation emits canonical schema-versioned `route_spec`.
- `ROSETTA-02`: `task_focus_ids` and evidence links are consistent with uplift graph.
- `DET-03`: Repeated runs are byte-stable for identical inputs.
- `BOUND-03`: Phase 3 does not perform target validation, execution, or output generation.

Recommended test modules:
- `tests/test_routing_contracts.py`
- `tests/test_semantic_router_precedence.py`
- `tests/test_semantic_router_ambiguity.py`
- `tests/test_rosetta_translation.py`
- `tests/test_phase3_determinism.py`
- `tests/test_phase3_boundary.py`

Actionable validation strategy for planning:
1. Implement contract tests first (schema-major gates, enum closures, required fields).
2. Add precedence matrix tests using minimal uplift fixtures that isolate each signal layer.
3. Add ambiguity fixtures asserting deterministic `NEEDS_REVIEW` payload shape.
4. Add translation integrity tests asserting task/evidence linkage and canonical field ordering.
5. Add byte-stability harness (multi-run in-process and cross-process).
6. Add explicit boundary tests asserting no imports/calls to Phase 4/5 concerns from Phase 3 engine.

## Code Examples

Precedence selector skeleton:

```python
def select_route(signals: SignalBundle) -> RouteSelection:
    if signals.hard_gate.blocked:
        return RouteSelection.needs_review(
            reason="hard_gate_blocked",
            missing_evidence=signals.hard_gate.missing_evidence,
        )

    for layer in ("intent", "task_graph", "acceptance"):
        candidate = evaluate_layer(layer, signals)
        if candidate.is_decisive:
            return candidate

    return RouteSelection.needs_review(
        reason="no_decisive_route",
        missing_evidence=signals.missing_evidence,
    )
```

Canonical serialization guard:

```python
def to_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
```

## Planner-Ready Implementation Sequence

1. Define Phase 3 contracts and enums with schema-major validation.
2. Implement deterministic signal extraction from uplift payload.
3. Implement precedence-based semantic router with explicit rule IDs.
4. Implement Rosetta translator to canonical `route_spec`.
5. Compose Phase 3 engine and enforce boundary guards.
6. Add full validation suite (contracts, precedence, ambiguity, translation, determinism, boundaries).

## Phase Boundary Enforcement

Phase 3 must not implement:
- Target tool validation.
- Mock execution or execution fallback logic.
- Output/help generation.

If these concerns appear, they should fail boundary checks and be deferred to Phase 4/5.
