# v1.3 Architecture Integration Research: `EXT-01` / `EXT-02`

Date: 2026-03-06  
Scope: integrate deferred extensions into the current deterministic pipeline without regressing existing boundary contracts.

## Deterministic Design Goal

`EXT-01` (URL ingestion) and `EXT-02` (downstream execution) should be integrated as additive, fail-closed layers. Existing deterministic behavior remains the default path, and extension paths must require explicit policy + approval artifacts.

## Integration Points with Existing Pipeline

### Existing baseline

Current runtime path is split into deterministic phases:

1. Phase 1: `run_phase1_pipeline`  
   `read_local_file_text -> sanitize_two_pass -> render_intent_summary`
2. Phase 2: `run_uplift_engine`
3. Phase 3: `run_semantic_routing`
4. Phase 4: `run_phase4` (validate + mock + fallback, no execution)
5. Phase 5: `run_phase5` (runtime preflight + output + help, no execution)

### `EXT-01` integration points

- Insert a source-resolution stage before current ingestion policy/read:
  - `source input -> source resolver -> local file path (existing reader path)`
- Keep `read_local_file_text` deterministic by reading only local materialized files.
- Propagate source provenance (`source_kind`, `normalized_source`, `content_sha256`) into Phase 2 context payload so later phases can enforce policy traces.

### `EXT-02` integration points

- Keep Phases 4 and 5 unchanged as non-executing deterministic gates.
- Add a new post-Phase-5 execution stage (Phase 6 style extension):
  - Input: `Phase4Result`, `Phase5Output`, explicit `ExecutionApprovalContract`
  - Output: typed `ExecutionResult` with deterministic evidence and replay-safe metadata
- Execution is allowed only when fallback and policy gates explicitly permit it.

## New vs Modified Components

### New components

- `src/intent_pipeline/ingestion/source_resolver.py`  
  Deterministic source classification (`LOCAL_FILE`, `URL`) and canonical normalization.
- `src/intent_pipeline/ingestion/url_policy.py`  
  URL allow/deny policy contract and normalization rules.
- `src/intent_pipeline/ingestion/url_snapshot_store.py`  
  Content-addressed materialization of approved URL payloads to local immutable snapshots.
- `src/intent_pipeline/phase6/contracts.py`  
  `ExecutionApprovalContract`, `ExecutionRequest`, `ExecutionResult`, typed error codes.
- `src/intent_pipeline/phase6/authorizer.py`  
  Deterministic approval/policy gate (fail closed).
- `src/intent_pipeline/phase6/executor_registry.py`  
  Closed mapping from approved route/tool to executor adapter.
- `src/intent_pipeline/phase6/journal.py`  
  Append-only execution evidence ledger with idempotency keys.

### Modified components

- `src/intent_pipeline/ingestion/policy.py`  
  Add extension-aware source validation entrypoint while preserving local-only default.
- `src/intent_pipeline/ingestion/reader.py`  
  Accept resolved local snapshot descriptors (still reads local files only).
- `src/intent_pipeline/uplift/context_layer.py`  
  Include source provenance fields in deterministic context payload.
- `src/intent_pipeline/phase4/contracts.py` (optional additive)  
  Add execution-intent metadata fields only if needed for downstream policy binding; keep current schema semantics stable.
- `src/intent_pipeline/phase5/*`  
  No behavior expansion; only optional references to downstream execution eligibility flags (advisory, non-executing).

## Data/Control Flow Updates

### Flow A: default deterministic (no extension activation)

`local source -> existing Phase1..Phase5 -> terminal output/help`  
No network operations, no execution, same behavior as current shipped pipeline.

### Flow B: `EXT-01` deterministic URL ingestion

`URL source -> source_resolver -> url_policy_validate -> snapshot_lookup/materialize -> read_local_file_text -> sanitize -> Phase2..Phase5`

Rules:
- URL payload is processed only after policy approval.
- Pipeline consumes immutable local snapshot artifact, not live response streams.
- Snapshot hash becomes canonical provenance input for downstream artifacts.

### Flow C: `EXT-02` controlled downstream execution

`Phase3 route_spec -> Phase4 validation/mock/fallback -> Phase5 output/help -> Phase6 authorizer -> executor_registry -> execution_journal`

Rules:
- Execution path is unreachable without explicit approval contract.
- Routing/validation/fallback remain the deciding control plane.
- Execution result is typed and auditable, with deterministic evidence ordering.

## Build Order

1. Add typed extension contracts and feature flags (default disabled, fail closed).
2. Implement `EXT-01` source resolver + URL policy + snapshot store without changing existing local-path behavior.
3. Wire ingestion to consume resolver output and preserve `read_local_file_text` local-read semantics.
4. Extend Phase 2 context provenance for deterministic traceability of resolved source artifacts.
5. Add Phase 6 authorization contracts and gate engine (no executor side effects yet).
6. Implement closed executor registry + adapters behind explicit approval checks.
7. Add execution journal/idempotency layer and replay-safe verification.
8. Add end-to-end deterministic and boundary tests across local-only, URL-enabled, and execution-approved paths.

## Boundary Guardrails (Determinism-Centered)

- Default behavior remains current no-network/no-execution path unless extension flags and approval artifacts are present.
- Unknown source types, unknown route profiles, unknown executors, or missing approvals must terminate as deterministic `NEEDS_REVIEW`/block codes.
- URL ingestion must use canonical normalization and policy allowlist checks before any materialization.
- URL content must be pinned to deterministic snapshot hashes; live fetch variance must not leak into core pipeline outputs.
- Execution must require:
  - `route_spec.decision == PASS_ROUTE`
  - Phase4 validation pass and eligible fallback state
  - valid `ExecutionApprovalContract` matching tool/profile/capability scope
  - idempotency key check against execution journal
- Keep Phase 4 and Phase 5 boundary contracts intact: no side-effect execution imports or mutation logic added there.
- Preserve canonical serialization (`sort_keys=True`, deterministic ordering) for all new extension contracts and reports.
- All extension code paths must emit explicit evidence paths and typed error codes for auditability.
