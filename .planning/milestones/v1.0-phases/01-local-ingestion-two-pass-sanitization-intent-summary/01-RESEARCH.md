# 01 Research — Local Ingestion + Two-Pass Sanitization + Intent Summary

Date: 2026-03-04
Phase: 01-local-ingestion-two-pass-sanitization-intent-summary
Scope lock: Local files only, mandatory two-pass sanitization, deterministic roleplay-free intent summary, no routing/execution.

## Research Outcome

Phase 1 should be planned as a strictly bounded, deterministic text pipeline with three isolated components:
1. Local path ingestion gate
2. Two-pass sanitization engine
3. Deterministic summary renderer

This keeps requirement traceability clear and prevents accidental drift into URL ingestion, agentic behavior, or downstream execution.

## Standard Stack

- Runtime: Python 3.11+ (aligned with existing repository script usage)
- Parsing/IO: `pathlib`, `os`, `stat`, `io`, `unicodedata`, `re`
- Determinism helpers: stable sort, fixed template rendering, normalized whitespace/newlines
- Testing: `pytest` with fixture files + snapshot/golden tests
- Optional safety hardening (if needed in Plan 01-01): MIME sniffing via stdlib only; avoid new dependencies unless required

## Architecture Patterns

### 1) Ingestion Boundary Adapter

Use a dedicated `IngestionPolicy` gate before any read:
- Accept only local file paths
- Reject URL/URI schemes (`http://`, `https://`, `ftp://`, `file://`, `ssh://`, `data:`)
- Reject path strings containing network-style markers when ambiguous
- Resolve to absolute path and enforce `is_file()`

Output contract:
- `IngestionResult { source_path, raw_text, metadata }`
- Fail fast with typed errors (`INVALID_SOURCE`, `NON_LOCAL_INPUT`, `READ_FAILURE`)

### 2) Mandatory Two-Pass Sanitization Pipeline

Enforce composition as code, not convention:
- `pass1(raw_text) -> intermediate_text`
- `pass2(intermediate_text) -> sanitized_text`
- Summary renderer must only accept `sanitized_text`

Pass responsibilities:
- Pass 1 (structural cleanup): encoding normalization, newline normalization, null/control character stripping, fence trimming, obvious markup flattening
- Pass 2 (behavioral cleanup): remove roleplay/system-instruction phrasing, command-like imperatives, persona framing, and execution hints while preserving intent facts

Invariant to enforce in code/tests:
- Pass 2 input is byte-for-byte output of Pass 1
- No bypass path from raw input to summary renderer

### 3) Deterministic Summary Renderer

Use template-driven rendering with fixed section order and no model sampling:
- Section order fixed at compile-time
- Deterministic line wrapping/whitespace policy
- Stable ordering for extracted intent points
- No timestamps/random IDs in output

Recommended summary format:
1. `Intent`
2. `Constraints`
3. `Requested Outcome`
4. `Rejected/Out-of-Scope Signals` (if any)

## Don’t Hand-Roll

- Do not implement URL parsing heuristics from scratch; use `urllib.parse` for initial scheme checks and explicit allow/deny rules.
- Do not use LLM generation for summary in Phase 1; deterministic templates are required for SUM-03.
- Do not conflate sanitization with intent extraction; keep sanitization pure and testable.
- Do not add routing hooks, tool invocation stubs, or "future-ready" execution branches in this phase.

## Common Pitfalls

- Hidden non-determinism from unordered sets/dicts in rendering.
- Sanitization that over-deletes and removes user intent with adversarial-like text.
- URL rejection implemented only at UI/CLI layer but not in core pipeline.
- Roleplay filtering that misses subtle phrasing (e.g., "as your assistant", "I will execute").
- Tests that validate outputs loosely (substring checks) instead of exact deterministic expectations.

## Validation Architecture

Validation must be requirement-indexed and layered so each failure points to one requirement ID.

### A) Unit Validation (fast, requirement-atomic)

- `INGEST-01`: accepts canonical local files (`/tmp/x.txt`, relative local path resolved to abs)
- `INGEST-02`: rejects scheme-prefixed inputs and network-like paths
- `SAN-01`: pass1 transforms raw input deterministically (golden output)
- `SAN-02`: pass2 consumes pass1 output only (assert call graph / explicit pipeline object)
- `SUM-01`: summary generated only from sanitized content
- `SUM-02`: roleplay markers removed from final summary (exact negative assertions)
- `SUM-03`: N repeated runs with same input/config produce byte-identical output
- `BOUND-01/02`: no routing/execution symbols invoked; pipeline terminates at summary artifact

### B) Integration Validation (pipeline behavior)

Use fixture corpus with 3 categories:
- Clean intent files
- Noisy/roleplay-heavy files
- Invalid/non-local source attempts

For each fixture, validate:
- expected acceptance/rejection status
- pass1 output snapshot
- pass2 output snapshot
- final summary exact snapshot

### C) Determinism Harness (critical gate)

For each accepted fixture:
- run pipeline 50 times in same process, then 50 times across fresh processes
- compare SHA-256 of final summary (all hashes must match)
- enforce normalized environment in tests (`TZ=UTC`, fixed locale)

### D) Boundary/Negative Validation

- Verify URL/URI inputs fail before file read attempt
- Verify summary stage cannot receive raw or pass1 text type (type/state guard)
- Verify no downstream handler interface is imported or called in Phase 1 path

### E) CI Gate Policy

Phase 1 merge gates should require:
- all requirement-mapped tests passing
- determinism harness passing
- snapshot updates reviewed explicitly (no auto-accept)

## Requirement-to-Plan Guidance

Plan 01-01 (Ingestion Boundary):
- Build `IngestionPolicy` + typed rejection reasons
- Add unit tests for local acceptance and URL rejection

Plan 01-02 (Two-Pass Sanitization):
- Implement strict pass chaining object
- Build fixture snapshots for pass1 and pass2 outputs

Plan 01-03 (Deterministic Summary):
- Implement fixed template renderer with stable ordering
- Add repeatability harness and roleplay-free assertions

## Code Examples (Planning-Level)

```python
sanitized_1 = pass1(raw_text)
sanitized_2 = pass2(sanitized_1)
summary = render_intent_summary(sanitized_2)
```

```python
assert is_local_file(source)
assert not is_uri(source)
```

```python
first = run_pipeline(path)
for _ in range(99):
    assert run_pipeline(path) == first
```

## Open Decisions for Planner

- Exact roleplay phrase blocklist vs pattern-based classifier in pass2.
- Whether summary should include a confidence field (deterministic if rule-based, optional).
- File size cap for Phase 1 safety (recommended: define explicit max bytes and test it).

## Exit Criteria for Phase Completion

Phase 1 is complete only when:
- All 9 v1 requirements have direct passing tests.
- Determinism harness is green with zero output drift.
- No network/URL ingestion path exists in production code path.
- No routing/execution behavior exists beyond summary output.
