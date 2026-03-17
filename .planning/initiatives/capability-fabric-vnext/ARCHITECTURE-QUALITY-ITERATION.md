# Architecture Quality Iteration Plan

## Goal
Raise the architecture capability to a quality bar that is at least as strict as `code-review` and `resolve-conflict` while preserving the Harish/Garg mode structure and Alexanderdunlop quality principles.

## Current Status
- Completed on: 2026-03-17
- Architecture output mode now uses deterministic sections, explicit scorecard logic, rollback discipline, and benchmark-linked alternatives.
- Latest rating: `Architecture output quality = 11 / 14`
- Barrier assessment: pass criteria met (no zero in Failure-Aware, Migration Clarity, Benchmark Fit; overall >= 9).

## Questions to Resolve
1. What level of deterministic scoring detail is required before marking a candidate as `ready`?
2. Which benchmark artifacts must be attached to architecture output for traceability?
3. When should a source candidate be rejected as `manual_review` for architectural overlap/ambiguity?
4. Do we want a separate capability name (`system-architecture`) while keeping slug `architecture`?

## Current Resolution Summary
1. Deterministic scoring detail is standardized as the per-invocation `Architecture Quality Scorecard` with weighted hard-gates.
2. Benchmark artifacts are attached as:
   - raw links in `.meta/capabilities/architecture.sources.md`
   - benchmark/source notes in `.meta/capabilities/architecture.json`
   - explicit `evidence` and `benchmark` fields in `.meta/capability-handoff.json`
3. `manual_review` is required when any of these apply:
   - unresolved overlap with existing SSOT (same family + contradictory contract)
   - missing non-negotiable sections
   - hard-gate quality failure in scorecard (Failure-Aware/Migration Clarity/Benchmark Fit = 0)
4. A richer public presentation name is adopted while preserving slug: `Architecture Studio`.

## Multi-Pass Improvement Process

### Pass 1 — Source Parity
- Compare against:
  - Harish Garg architecture modes
  - Alexanderdunlop architecture prompts
  - `code-review`
  - `resolve-conflict`
- Record all structural deltas in:
  - `ssot/architecture.md`
  - `.meta/capabilities/architecture.sources.md`
- Required output: `Cross-Source Quality Baseline` section updated.

### Pass 2 — Contract Hardening
- Define strict section contract and scorecard in SSOT.
- Add explicit acceptance rules per mode.
- Add fallback and rollback requirements for any persistence/interface change.

### Pass 3 — Descriptor Enrichment
- Reflect family scorecard rules in:
  - `.meta/capabilities/architecture.json`
- Add alias/name clarity and benchmark fit gates.
- Ensure resources include benchmark and source links, including local quality templates.

### Pass 4 — Surface Regeneration
- Run:
  - `python3 scripts/build-surfaces.py`
  - `python3 scripts/validate-surfaces.py --strict`
- Ensure generated surfaces reference `.meta/capabilities/architecture.json` via `resources/capability.json`.

### Pass 5 — Regression Checks
- Add/extend tests for:
  - SSOT architecture scorecard schema
  - mode mandatory sections
  - descriptor quality gates and benchmark links
  - source-note lineage

### Pass 6 — Capability Rating
- Score this capability using its own criteria:
  - Score 0–14 total.
  - Target `>= 9` and mandatory non-zero in:
    - Failure-Aware Decisions
    - Migration Clarity
    - Benchmark Fit
- Keep a rolling score note in `VALIDATION.md` under this initiative.

## Definition of Done
- SSOT is stricter than current baseline and includes deterministic structure + scorecard.
- Descriptor includes explicit quality gates and benchmark fit checks.
- `build-surfaces` + `validate-surfaces --strict` are green.
- Architecture family surfaces are regenerated and diff-only to architecture artifacts.
- New/updated tests protect the quality bar.
