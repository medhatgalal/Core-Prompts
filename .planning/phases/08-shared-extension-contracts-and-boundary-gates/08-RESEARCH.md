# Phase 8: Shared Extension Contracts and Boundary Gates - Research

**Researched:** 2026-03-06
**Domain:** Deterministic policy contracts and fail-closed extension gate architecture
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase 8 is contract-and-gates only; no live URL ingestion or execution side effects in this phase.
- Extension behavior defaults to disabled/fail-closed unless explicitly enabled by validated policy artifacts.
- Decision outputs must be deterministic, typed, and evidence-linked with stable ordering and canonical serialization.
- Existing local-file baseline behavior must remain unchanged when extensions are disabled.

### Claude's Discretion
- Exact module/file boundaries for shared contracts and gate evaluators.
- Exact enum names and reason-code taxonomy.
- Test fixture arrangement and naming.

### Deferred Ideas (OUT OF SCOPE)
- URL canonicalization/snapshot implementation details (Phase 9).
- Execution adapter and idempotency-journal implementation details (Phase 10).
- Authenticated retrieval and write-capable execution profiles (future milestone).

</user_constraints>

<research_summary>
## Summary

Phase 8 should establish one shared extension policy contract that both ingestion and execution paths consume, then enforce a deterministic gate evaluator ahead of any extension-specific logic. The most stable approach in this codebase is to reuse existing dataclass/enum contract conventions, schema-major validation helpers, and canonical payload serialization already used by routing, phase4, and phase5 modules.

The recommended architecture is: `policy_contract -> gate_evaluator -> typed_gate_result`. Gate evaluation must be conservative and deterministic: unknown mode/profile/capability blocks by default, missing policy artifacts block by default, and every outcome emits structured evidence paths and rule IDs.

**Primary recommendation:** Build a shared `extensions/contracts.py` + `extensions/gates.py` layer and wire non-regression tests before touching Phase 9/10 feature behavior.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python dataclasses/enums | 3.12 stdlib | Typed policy and gate result contracts | Matches existing deterministic contract style in this repo |
| `json` canonical serialization | 3.12 stdlib | Byte-stable payload rendering | Already used across uplift/routing/phase4/phase5 |
| `typing` (`Literal`, `Final`, `Mapping`) | 3.12 stdlib | Closed-mode/value modeling | Prevents fail-open implicit behavior |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 8.x | Determinism and boundary regression verification | Required for phase-level acceptance and Nyquist checks |
| Existing repo test fixtures | current | Reuse phase4/phase5 boundary harnesses | For non-regression and forbidden-side-effect assertions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Dataclass contracts | Pydantic models | Strong validation features, but adds dependency and diverges from current contract pattern |
| Shared gate layer | Duplicate gate logic per phase | Faster initially, but creates drift and inconsistent decision semantics |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Contract-first shared gate primitives
**What:** Centralize extension policy schema + gate evaluator in shared module consumed by phases 9 and 10.
**When to use:** Anytime behavior depends on extension mode/policy eligibility.

### Pattern 2: Deterministic fail-closed decision pipeline
**What:** Evaluate policy in fixed order and return typed decisions (`ALLOW`, `BLOCK`, `NEEDS_REVIEW`) with rule/evidence context.
**When to use:** Any extension eligibility check where unknowns or mismatches appear.

### Pattern 3: Additive integration
**What:** Inject gate checks before extension branches while preserving existing local-only paths.
**When to use:** Backward-compatible rollout from v1.2 defer/defer baseline.

### Anti-Patterns to Avoid
- Splitting gate semantics across ingestion/execution modules with independent decision code lists.
- Permissive defaults when policy fields are absent/invalid.
- Non-canonical evidence ordering that breaks reproducibility checks.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Policy/version validation | Ad hoc dict checks in each caller | Shared validator contract with typed normalization | Prevents inconsistent acceptance/rejection logic |
| Determinism checks | Manual spot assertions | Existing repeated-run byte-stability test pattern | Catches ordering/serialization drift reliably |
| Boundary enforcement | One-off import checks per file | Reuse existing phase boundary test scaffolding | Keeps no-side-effect checks systematic |

**Key insight:** Consistency is the primary risk reducer; shared gate primitives matter more than per-feature optimization in this phase.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Gate drift across phases
**What goes wrong:** Phase 9 and 10 interpret the same policy fields differently.
**How to avoid:** One shared contract/evaluator module and common reason-code enum.

### Pitfall 2: Silent permissive fallback
**What goes wrong:** Missing policy fields accidentally pass extension checks.
**How to avoid:** Fail-closed required-field validation and explicit block reason codes.

### Pitfall 3: Non-deterministic evidence ordering
**What goes wrong:** Identical runs produce different evidence arrays.
**How to avoid:** Stable sort order and canonical serialization assertions in tests.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

Phase 8 must add/extend tests in three lanes:
- **Contract tests:** policy schema/version validation, required fields, enum closure.
- **Gate behavior tests:** unknown modes/profiles/capabilities block deterministically.
- **Non-regression tests:** extension-disabled mode preserves current local-only pipeline outputs.

Required pass criteria:
1. Byte-stable gate payload outputs across repeated and cross-process runs.
2. Boundary tests prove no side-effect-enabling imports or execution behavior introduced in Phase 8.
3. All phase requirement IDs (`XDET-01`, `XDET-02`, `XBND-01`, `XBND-02`) have explicit test mapping.
</validation_architecture>

<open_questions>
## Open Questions

1. **Policy artifact storage path and load lifecycle**
   - What we know: Must be versioned, stable, and audited.
   - What's unclear: Whether to keep policy inline in config or in separate artifact files.
   - Recommendation: Choose one canonical source in Plan 08-01 and enforce it globally.

2. **Decision enum naming compatibility with existing phases**
   - What we know: Existing phases already use `NEEDS_REVIEW` semantics.
   - What's unclear: Whether to expose new gate enum values directly or map into existing status envelopes.
   - Recommendation: Keep explicit gate-level enums but provide deterministic mapping helper for downstream phases.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/phases/08-shared-extension-contracts-and-boundary-gates/08-CONTEXT.md` — locked decisions and scope constraints
- `.planning/research/ARCHITECTURE.md` — integration points and build order
- `.planning/research/PITFALLS.md` — extension-specific failure modes and mitigations
- `src/intent_pipeline/{routing,phase4,phase5}/*.py` — existing contract/gate/determinism patterns
- `tests/test_phase4_boundary.py`, `tests/test_phase5_boundary.py`, `tests/test_phase4_determinism.py`, `tests/test_phase5_determinism.py` — baseline verification patterns
</sources>

---
*Phase: 08-shared-extension-contracts-and-boundary-gates*
*Research completed: 2026-03-06*
*Ready for planning: yes*
