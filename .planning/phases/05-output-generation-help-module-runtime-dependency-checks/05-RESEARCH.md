# Phase 5 Research: Output Generation + Help Module + Runtime Dependency Checks

## Deterministic Implementation Guidance

### 1) Output Generation
- Introduce `src/intent_pipeline/phase5/contracts.py` with a schema-major-gated Phase 5 contract (`5.x`) and typed enums for output status and codes.
- Treat `Phase4Result` as immutable input evidence. Phase 5 must consume `validation`, `mock`, and `fallback` but never mutate Phase 4 decisions or fields.
- Emit two deterministic surfaces:
  - Machine payload: typed, schema-versioned, canonical JSON (`sort_keys=True`, fixed separators).
  - Human text: fixed template and fixed section order.
- Use explicit pipeline ordering in the Phase 5 result contract (same pattern as Phase 4 `pipeline_order`) and enforce equality to a constant tuple.
- Enforce stable ordering for all lists/maps (`issues`, `checks`, `hints`, `evidence_paths`) by deterministic key sorting before serialization.

### 2) Help Module
- Implement a closed help-topic enum (usage, failure_explanation, remediation_hints, boundary_clarification).
- Map typed upstream signals (Phase 4 decision/error codes + runtime check codes) to fixed templates. No freeform persona generation.
- Require each help response to include:
  - `topic`
  - `code`
  - `message` (template derived)
  - `evidence_paths` (sorted)
  - `actions` (non-executing guidance only)
- Keep template selection deterministic:
  - Primary key: terminal/most severe code
  - Tie-break: lexical order of code
- Preserve `NEEDS_REVIEW` semantics: help can explain and guide, but cannot alter terminal outcome.

### 3) Runtime Dependency Checks
- Implement preflight-only checker module (for example `src/intent_pipeline/phase5/runtime_checks.py`) that performs presence/capability inspection only.
- Dependency model:
  - `required`: missing -> blocking status
  - `optional`: missing -> degraded status
- Check methods must be side-effect free:
  - Allowed: static inspection (`importlib.util.find_spec`, `shutil.which`, pure config lookup).
  - Forbidden: execution (`subprocess`, `os.system`, tool invocation), installs/upgrades, network calls.
- Emit typed check entries with deterministic fields:
  - `dependency_id`, `classification`, `status`, `reason_code`, `evidence_paths`, `detail`
- Aggregate outcome rule:
  - Any missing required dependency => `BLOCKING`
  - Else any missing optional dependency => `DEGRADED`
  - Else => `PASS`

### 4) Phase 5 Engine Composition
- Add deterministic orchestrator (`src/intent_pipeline/phase5/engine.py`) with fixed order:
  - `run_runtime_dependency_checks`
  - `generate_output_surfaces`
  - `resolve_help_response`
- Return a single `Phase5Result` contract carrying:
  - `phase4` passthrough snapshot (or references)
  - `runtime_checks`
  - `output`
  - `help`
  - `pipeline_order`
- Enforce fail-closed schema-major checks at all boundaries.

## Proposed Phase 5 Requirement IDs (Replace TBD)

- `OUT-01`: Phase 5 emits a typed schema-versioned machine output payload from `Phase4Result` with canonical deterministic serialization.
- `OUT-02`: Phase 5 emits deterministic human-readable output using fixed section order and fixed templates.
- `OUT-03`: Output generation must preserve upstream Phase 4 terminal semantics (`NEEDS_REVIEW`) without status mutation.
- `HELP-01`: Help module is constrained to closed deterministic topics and typed codes.
- `HELP-02`: Help text is template-driven, roleplay-free, and includes explicit evidence-path references.
- `HELP-03`: Help responses provide non-executing remediation guidance only.
- `RUNTIME-01`: Runtime dependency checks are preflight-only and side-effect free.
- `RUNTIME-02`: Missing required dependencies deterministically produce blocking outcomes with typed reason codes.
- `RUNTIME-03`: Missing optional dependencies deterministically produce degraded outcomes with typed reason codes.
- `RUNTIME-04`: Runtime dependency reports are schema-versioned and stably ordered.
- `DET-05`: Phase 5 artifact serialization is byte-stable across repeated and cross-process identical runs.
- `BOUND-05`: Phase 5 excludes real execution, auto-remediation, package installation, and network-based dependency/help operations.

## Validation Architecture

### Test Strategy
- Contract tests (`tests/test_phase5_contracts.py`):
  - Schema-major validation and typed coercion.
  - Enum/value fail-closed behavior.
  - Deterministic ordering normalization for all collections.
- Engine composition tests (`tests/test_phase5_engine.py`):
  - Assert exact orchestration order and pipeline tuple.
  - Assert Phase 4 outputs are consumed but not mutated.
  - Assert status aggregation rule (`BLOCKING` > `DEGRADED` > `PASS`).
- Boundary tests (`tests/test_phase5_boundary.py`):
  - AST import guard against forbidden layers/modules (`execution`, `subprocess`, `requests`, `httpx`, `socket`, installer tooling).
  - Output payload excludes real-execution fields and remediation side effects.
  - Typed boundary violation codes prefixed `BOUND-05-*` with sorted evidence paths.
- Determinism tests (`tests/test_phase5_determinism.py`):
  - Repeated in-process runs are byte-identical.
  - Cross-process runs with fixed env (`PYTHONHASHSEED=0`, `TZ=UTC`, `LC_ALL=C.UTF-8`, `LANG=C.UTF-8`) are byte-identical.

### Commands
```bash
PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 LANG=C.UTF-8 pytest -q tests/test_phase5_contracts.py tests/test_phase5_engine.py tests/test_phase5_boundary.py tests/test_phase5_determinism.py
```

```bash
PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 LANG=C.UTF-8 pytest -q -k "phase5 and (det or bound)"
```

## Scope Boundary Guardrails

- No real execution: Phase 5 must not call runtime tools, subprocesses, or side-effecting adapters.
- No auto-remediation: no install/upgrade/patch/retry actions for missing dependencies.
- No network dependency/help enrichment: no HTTP fetches or remote introspection.
- No upstream behavior drift: Phase 5 can explain/format outcomes but cannot alter Phase 4 decision semantics.
