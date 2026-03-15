# Phase 10: EXT-02 Simulate-First Controlled Execution - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 10 adds a new post-Phase-5 controlled-execution control plane that remains simulate-first by default, fails closed on any missing approval or capability invariant, and emits deterministic evidence for every blocked, simulated, or execute-approved decision.

In scope for Phase 10:
- Define explicit execution-approval contracts and deterministic validation of approval payloads.
- Add a closed executor registry keyed by approved route/tool combinations only.
- Add a Phase 6 style execution authorizer after Phase 5; Phases 4 and 5 remain non-executing.
- Add deterministic decision reporting and journal evidence with idempotency keys.
- Enforce simulate-first default and side-effect-safe dry-run/mock behavior with boundary tests.

Explicitly out of scope for Phase 10:
- Dynamic executor discovery or model-selected tool invocation.
- Authenticated secret passthrough, operator shell access, or open-ended environment execution.
- Runtime mutation of policy, capability matrix, or approval artifacts.
- Any changes to URL ingestion behavior beyond consuming Phase 9 provenance and policy outputs.
- Automatic retries, rollback orchestration, or concurrent multi-target execution.

</domain>

<decisions>
## Implementation Decisions

### Execution stage placement and upstream contract posture
- Keep Phases 4 and 5 unchanged as non-executing control surfaces.
- Introduce a new `phase6` execution stage after `run_phase5`, not inside Phase 4 or Phase 5.
- Phase 6 consumes typed upstream artifacts, not raw text:
  - `Phase4Result`
  - `Phase5Result`
  - `ExecutionApprovalContract`
  - optional journal root / registry payload inputs
- Phase 6 must preserve Phase 4 and Phase 5 terminal semantics; it may only add an execution disposition layer on top.

### Execute-eligible definition
- `execute_eligible=true` is allowed only when all of the following are true:
  - Phase 4 validation decision is `PASS`
  - Phase 4 fallback decision is `USE_PRIMARY`
  - Phase 5 output terminal status is `USE_PRIMARY`
  - route profile and target tool resolve through the closed registry
  - approval contract is present, schema-valid, unexpired, and capability-matching
- `DEGRADED` and `NEEDS_REVIEW` upstream states are never execute-eligible.
- Any mismatch between approval contract and upstream route/validation facts terminates as deterministic `NEEDS_REVIEW`.

### Approval contract shape
- Add a dedicated Phase 6 approval contract module rather than overloading Phase 4 policy contracts.
- Approval contract must be versioned and fully explicit. Minimum fields:
  - `schema_version`
  - `approval_mode` with closed enum: `SIMULATE_ONLY`, `EXECUTE_APPROVED`
  - `approval_id`
  - `approved_by`
  - `approved_at`
  - `expires_at`
  - `idempotency_key`
  - `route_profile`
  - `target_tool_id`
  - `dominant_rule_id`
  - `required_capabilities`
  - `policy_schema_version`
  - `policy_rule_ids`
- Approval contracts are deny-by-default: missing artifact, malformed fields, expired approval, or schema/version mismatch all fail closed.

### Closed executor registry and adapter model
- Use a closed static registry keyed by `(route_profile, target_tool_id)`.
- Registry entries declare:
  - `adapter_id`
  - `route_profile`
  - `target_tool_id`
  - `capabilities`
  - `supports_simulation`
  - `supports_execution`
  - stable `rule_id`
- No dynamic plugin loading, reflection-based discovery, environment-driven override, or free-form adapter path selection.
- Ambiguous mappings, duplicate registry keys, or unsupported route/tool pairs deterministically block execution.

### Simulate-first default
- Default Phase 10 posture is `SIMULATE_ONLY` even when routing and validation succeed.
- `approval_mode=SIMULATE_ONLY` may produce a successful simulation result and journal evidence, but never side effects.
- `approval_mode=EXECUTE_APPROVED` is required before any non-simulated adapter path can be considered.
- Missing approval does not silently downgrade to simulation; it returns `NEEDS_REVIEW` with explicit evidence.

### Phase 10 delivery scope for live execution
- Phase 10 should implement the control plane and registry boundary completely, but keep the shipped adapter set hermetic by default.
- The registry may include a deterministic no-side-effect adapter that proves execute-path orchestration and journaling contracts without external mutation.
- Any adapter that would touch network/process/file mutation beyond the journal path remains out of scope unless explicitly guarded and covered by boundary tests.
- This keeps the milestone aligned with simulate-first while still delivering `EXT2-*` gating, approval, registry, and evidence semantics.

### Journal and idempotency evidence
- Add an append-only deterministic journal module under `src/intent_pipeline/phase6/`.
- Journal identity is based on explicit `idempotency_key`; duplicate keys must not re-run an already-recorded approved attempt.
- Canonical evidence for every blocked, simulated, or execute-approved attempt includes:
  - `schema_version`
  - `decision`
  - `decision_code`
  - `approval_mode`
  - `approval_id`
  - `idempotency_key`
  - `policy_schema_version`
  - `policy_rule_ids`
  - `route_profile`
  - `target_tool_id`
  - `dominant_rule_id`
  - ordered `evidence_paths`
  - deterministic content hash of the execution request envelope
- Journal records must be canonically serialized with sorted keys and stable sequence ordering.

### Side-effect firewall and boundary enforcement
- Phase 4 and Phase 5 boundary contracts remain intact and must not import execution/network/process modules.
- Simulation modules and authorizer/registry logic must stay side-effect free.
- Boundary tests should explicitly reject network/process/file-mutation imports or calls in dry-run/simulation paths.
- If a hermetic adapter is introduced, its only allowed write path is the deterministic journal location.

### Auto defaults selected for `--auto`
- Use a new `src/intent_pipeline/phase6/` package for all Phase 10 execution control-plane code.
- Treat `USE_PRIMARY` as the only execute-eligible fallback state.
- Require exact approval-to-route matching; no wildcard approvals.
- Keep one static registry payload fixture in tests to drive deterministic allow/block branches.
- Prefer typed `NEEDS_REVIEW` outcomes over exceptions for policy/approval mismatches once inputs parse successfully.

### Claude's Discretion
- Exact Phase 6 module names beyond `contracts`, `authorizer`, `executor_registry`, and `journal`.
- Exact enum/type names for decision codes as long as they stay closed and deterministic.
- Exact on-disk journal layout as long as the journal remains append-only, replay-safe, and canonically serialized.

</decisions>

<specifics>
## Specific Ideas

- Model the Phase 10 control flow as:
  - `Phase4Result -> Phase5Result -> approval_contract -> authorizer -> executor_registry -> simulation_or_execute_decision -> journal_entry`
- Keep approval validation and registry resolution separate so tests can prove which gate blocked.
- Make blocked attempts journaled as first-class evidence, not incidental logs.
- Reuse the existing `NEEDS_REVIEW` semantics and deterministic evidence ordering conventions already present in Phases 4 and 5.
- Keep execute-approved behavior narrowly scoped around a hermetic adapter path unless planning proves a broader adapter is still boundary-safe.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/intent_pipeline/extensions/contracts.py`: versioned contract parsing, stable rule-ID enforcement, and fail-closed policy coercion patterns.
- `src/intent_pipeline/extensions/gates.py`: deterministic gate precedence, typed `ALLOW/BLOCK/NEEDS_REVIEW` outcomes, and ordered evidence paths.
- `src/intent_pipeline/routing/contracts.py` and `src/intent_pipeline/routing/rosetta.py`: closed route profile taxonomy and static route-spec translation rules suitable for approval binding.
- `src/intent_pipeline/phase4/contracts.py`: typed validation, mock, fallback, and boundary violation contracts.
- `src/intent_pipeline/phase4/validator.py`: closed route-profile to tool validation and capability-matrix checks already cover part of `EXT2-02`.
- `src/intent_pipeline/phase4/mock_executor.py`: deterministic, side-effect-free simulation staging pattern to reuse as the Phase 10 simulation baseline.
- `src/intent_pipeline/phase4/fallback.py`: fixed-tier fallback and terminal `NEEDS_REVIEW` behavior that should define execute-eligibility boundaries.
- `src/intent_pipeline/phase5/contracts.py` and `src/intent_pipeline/phase5/engine.py`: typed terminal status preservation and pipeline-order invariants.
- `tests/test_phase4_boundary.py`, `tests/test_phase5_boundary.py`, `tests/test_mock_execution.py`: established AST-based no-side-effect boundary harnesses to extend for Phase 10.

### Established Patterns
- Dataclass + enum contracts with schema-major validation.
- Canonical JSON serialization using `sort_keys=True` and stable tuple/list ordering.
- Cross-process determinism tests for byte-identical outputs on repeated runs.
- Boundary tests that scan for forbidden imports/calls rather than relying on convention.
- Closed registries and closed enums instead of heuristic or model-improvised routing.

### Integration Points
- Add `src/intent_pipeline/phase6/contracts.py` for approval, request, result, and journal envelopes.
- Add `src/intent_pipeline/phase6/authorizer.py` for execute-eligibility evaluation against Phase 4, Phase 5, and approval contract facts.
- Add `src/intent_pipeline/phase6/executor_registry.py` for static registry parsing and adapter resolution.
- Add `src/intent_pipeline/phase6/journal.py` for deterministic append-only evidence persistence and idempotency checks.
- Optionally add `src/intent_pipeline/phase6/engine.py` to orchestrate authorizer -> registry -> journal in one fixed order.
- Keep `src/intent_pipeline/phase4/*` and `src/intent_pipeline/phase5/*` behaviorally stable; only Phase 10 tests should prove that no execution logic leaked backward.

</code_context>

<deferred>
## Deferred Ideas

- Secret-scope injection and authenticated executor adapters.
- Automatic retry policies for write/execute classes.
- Concurrent execution scheduling and locking across shared targets.
- Rollback orchestration or compensating actions.
- Any executor that mutates arbitrary external state without a stronger approval and rollback story.

</deferred>

---

*Phase: 10-ext-02-simulate-first-controlled-execution*
*Context gathered: 2026-03-08*
