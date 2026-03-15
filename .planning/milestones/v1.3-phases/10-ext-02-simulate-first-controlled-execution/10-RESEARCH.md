# Phase 10: EXT-02 Simulate-First Controlled Execution - Research

**Researched:** 2026-03-09
**Domain:** Simulate-first execution authorization, closed executor registry, deterministic journal evidence
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase 10 adds a new post-Phase-5 execution control plane; Phases 4 and 5 remain non-executing.
- Execute-eligible flow is allowed only when validation passes, fallback is `USE_PRIMARY`, Phase 5 terminal status is `USE_PRIMARY`, and an explicit approval contract matches the route/tool/capability facts.
- Default behavior remains simulate-first; missing approval, mismatched capabilities, and unsupported mappings fail closed as typed `NEEDS_REVIEW` outcomes.
- Route-profile to executor resolution must be closed/static with no dynamic discovery or environment-driven overrides.
- Every blocked, simulated, or execute-approved attempt must emit deterministic journal evidence with idempotency keys.
- Dry-run/simulation logic must remain side-effect free; any allowed write path is limited to deterministic journal persistence.

### Claude's Discretion
- Exact Phase 6 module boundaries beyond the required control-plane surfaces.
- Exact decision-code taxonomy as long as it is closed, typed, and deterministic.
- Exact on-disk journal file layout provided it stays append-only, replay-safe, and canonically serialized.

### Deferred Ideas (OUT OF SCOPE)
- Authenticated executor adapters or secret passthrough.
- Dynamic tool selection, plugin loading, or model-selected execution.
- Automatic retries, rollback orchestration, or concurrent execution scheduling.
- Broader side-effecting adapters beyond a hermetic proof adapter and journal writes.

</user_constraints>

<research_summary>
## Summary

Phase 10 should be implemented as a new `phase6` package that consumes typed Phase 4 and Phase 5 outputs, plus an explicit approval contract, and then applies three deterministic gates in fixed order:

`approval_contract -> execute_eligibility_authorizer -> closed_executor_registry -> simulation_or_execute -> append_only_journal`

The cleanest fit is to keep earlier phases behaviorally stable and introduce the new execution layer as a narrow additive surface. Existing Phase 4 validation already carries the decisive route profile, dominant rule, tool mapping, and capability facts needed to authorize execution. Existing Phase 5 output already exposes the terminal status boundary that must remain non-executing. Phase 10 therefore does not need to re-decide routing or validation; it only needs to bind those existing facts to an approval contract, a closed executor registry, and deterministic evidence emission.

**Primary recommendation:** create `src/intent_pipeline/phase6/contracts.py`, `authorizer.py`, `executor_registry.py`, `journal.py`, and `engine.py`; prove correctness with deterministic contract tests, simulate-first authorizer tests, journal/idempotency tests, and AST-based boundary enforcement that keeps execution logic from leaking into Phases 4 and 5.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `dataclasses`, `enum`, `json` | Python 3.12 stdlib | Typed contracts, closed decision enums, canonical serialization | Matches existing phase contract style |
| `pathlib` | Python 3.12 stdlib | Deterministic journal paths and append-only evidence files | Keeps filesystem writes bounded and explicit |
| `hashlib` | Python 3.12 stdlib | Stable envelope hashing for idempotency and evidence | Required for replay-safe identity |
| `datetime` | Python 3.12 stdlib | Approval expiry parsing and deterministic timestamp handling | Needed for approval validity checks |
| Existing phase4/phase5 contract helpers | current | Reuse route/tool/capability/fallback/output semantics | Avoids duplicating validation logic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 8.x | Unit, integration, determinism, and boundary tests | Required for `EXT2-*` verification evidence |
| `ast` | Python 3.12 stdlib | Static no-side-effect boundary tests | Reuse established repo boundary style |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Static executor registry | Dynamic plugin discovery | Easier expansion later, but violates closed deterministic boundary |
| File-backed append-only journal | SQLite event log | More queryable, but unnecessary complexity and higher mutation surface for v1.3 |
| Broad live adapters | Hermetic proof adapter only | Narrower feature set, but aligns with simulate-first and side-effect constraints |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Post-Phase-5 control plane
**What:** run execution authorization only after Phase 5 has already produced terminal status and human/machine outputs.
**When to use:** all Phase 10 flows.

### Pattern 2: Approval binds upstream facts
**What:** approval contract must match route profile, target tool, dominant rule, policy version, and required capabilities already emitted upstream.
**When to use:** every non-local execution decision.

### Pattern 3: Closed registry resolution
**What:** resolve `(route_profile, target_tool_id)` only through a static registry payload with explicit adapter capabilities and support flags.
**When to use:** simulation and execute-approved adapter selection.

### Pattern 4: Journal every decision
**What:** blocked attempts, simulations, and execute-approved paths all emit deterministic journal entries using the same canonical envelope.
**When to use:** every Phase 10 terminal outcome.

### Anti-Patterns to Avoid
- Recomputing route validation inside Phase 10 instead of consuming typed Phase 4 outputs.
- Treating missing approval as implicit consent to simulation or execution.
- Letting runtime environment variables alter registry mappings or approval semantics.
- Hiding blocked attempts in logs instead of first-class journal evidence.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Approval matching | Free-form dict checks scattered through engine | Typed approval contract parser + exact-match helper | Keeps `EXT2-01` deterministic and auditable |
| Executor selection | Ad hoc `if/else` against route profile strings | Static registry contract keyed by `(route_profile, target_tool_id)` | Satisfies `EXT2-02` without dynamic inference |
| Simulation evidence | Print/log strings only | Typed result payload + canonical journal record | Gives replay-safe proof for `EXT2-03` and `EXT2-04` |
| Idempotency | Best-effort duplicate suppression | Content-hash request envelope + explicit `idempotency_key` index | Prevents duplicate approved attempts |

**Key insight:** Phase 10 remains deterministic only if authorization, registry resolution, and journaling all consume explicit typed inputs and preserve a single fixed evaluation order.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Approval drift from upstream facts
**What goes wrong:** approval artifact references a route/tool/capability combination that does not match the actual validated route.
**How to avoid:** exact-match validation against Phase 4/5 facts with typed `NEEDS_REVIEW` outcomes.

### Pitfall 2: Registry ambiguity
**What goes wrong:** multiple adapters match the same `(route_profile, target_tool_id)` or registry metadata is incomplete.
**How to avoid:** closed schema, unique-key enforcement, and deterministic hard block on duplicates or unsupported entries.

### Pitfall 3: Simulation becomes soft execution
**What goes wrong:** simulate-first path imports or invokes process/network/file mutation APIs.
**How to avoid:** AST-based boundary tests plus hermetic adapter design that permits only journal writes.

### Pitfall 4: Non-journaled blocked attempts
**What goes wrong:** denials are observable only in transient logs, breaking auditability.
**How to avoid:** blocked, simulated, and execute-approved outcomes all emit the same canonical journal envelope.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

Phase 10 needs tests across four lanes:
- **Contract tests:** approval contract parsing, schema-major validation, expiry handling, and exact-match approval semantics.
- **Authorizer/registry tests:** execute-eligible gating, closed registry resolution, ambiguous mapping blocks, and simulate-first defaults.
- **Journal/idempotency tests:** append-only evidence layout, duplicate idempotency-key handling, canonical serialization, and blocked-attempt journaling.
- **Boundary/determinism tests:** AST scans for forbidden imports/calls in dry-run/execution control paths plus repeated-run and cross-process byte stability.

Required pass criteria:
1. `EXT2-01` through `EXT2-05` each map to at least one automated test.
2. Missing approval, capability mismatch, and unsupported mapping all terminate as typed `NEEDS_REVIEW` without side effects.
3. Duplicate idempotency keys never rerun approved attempts and journal output remains byte-stable across identical runs.
</validation_architecture>

<open_questions>
## Open Questions

1. **Should execute-approved behavior ship with any side-effecting adapter in v1.3?**
   - What we know: the context keeps the shipped adapter set hermetic by default.
   - Recommendation: ship one deterministic no-side-effect adapter to prove execute-path orchestration and journaling without widening the mutation boundary.

2. **What is the journal root default?**
   - What we know: writes must be deterministic and append-only.
   - Recommendation: allow caller override, but default to a dedicated local phase6 journal directory with canonical filenames derived from `idempotency_key` and envelope hash.

3. **Should approval timestamps be wall-clock compared directly in tests?**
   - What we know: expiry validation is required and determinism matters.
   - Recommendation: inject `now` into approval validation helpers so tests remain deterministic and do not depend on ambient time.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/phases/10-ext-02-simulate-first-controlled-execution/10-CONTEXT.md` — locked scope and decisions
- `.planning/research/ARCHITECTURE.md` — Phase 6 integration point and build order
- `.planning/research/PITFALLS.md` — execution-specific boundary and idempotency risks
- `.planning/research/SUMMARY.md` — milestone sequencing and risk posture
- `src/intent_pipeline/phase4/contracts.py`, `validator.py`, `mock_executor.py`, `fallback.py` — existing validation/fallback/simulation primitives
- `src/intent_pipeline/phase5/contracts.py`, `engine.py` — terminal-status and non-executing output boundaries
- `tests/test_mock_execution.py`, `tests/test_phase4_boundary.py`, `tests/test_phase5_boundary.py` — reusable deterministic and side-effect boundary test patterns

</sources>

---
*Phase: 10-ext-02-simulate-first-controlled-execution*
*Research completed: 2026-03-09*
*Ready for planning: yes*
