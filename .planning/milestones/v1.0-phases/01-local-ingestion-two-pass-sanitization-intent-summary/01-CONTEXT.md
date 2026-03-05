# Phase 1: Local Ingestion + Two-Pass Sanitization + Intent Summary - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning
**Source:** Direct user scope lock

<domain>
## Phase Boundary

Phase 1 is strictly limited to local-file ingestion, two-pass sanitization, and clean intent summary output.

This phase explicitly excludes:
- URL or any network-based ingestion
- Downstream routing, tool invocation, or execution

</domain>

<decisions>
## Implementation Decisions

### Input Boundary (Locked)
- Ingestion accepts local filesystem files only.
- URL/URI inputs must be rejected.

### Sanitization Pipeline (Locked)
- A mandatory two-pass sanitization pipeline must run before summary generation.
- Pass 2 must consume pass-1 output, never raw input.

### Output Contract (Locked)
- Output is a clean intent summary only.
- Output must be roleplay-free.
- Output must be deterministic for identical inputs and configuration.

### Execution Boundary (Locked)
- No downstream routing/execution in this phase.
- Summary emission is the terminal action.

### Claude's Discretion
- Exact implementation structure (modules, interfaces, and test layout)
- Specific sanitization heuristics as long as two-pass invariant holds
- Determinism strategy details (normalization, stable ordering, fixed templates)

</decisions>

<specifics>
## Specific Ideas

- Add strict input validator that rejects URL-like prefixes (`http://`, `https://`, `ftp://`, `file://`).
- Emit deterministic summary using fixed section ordering and stable normalization.
- Add tests for identical-input repeatability and roleplay-content rejection.

</specifics>

<deferred>
## Deferred Ideas

- URL ingestion and fetch pipeline
- Intent routing/execution integrations

</deferred>

---

*Phase: 01-local-ingestion-two-pass-sanitization-intent-summary*
*Context gathered: 2026-03-04 via direct scope lock*
