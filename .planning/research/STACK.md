# Stack Research

**Domain:** Deterministic intent pipeline extension hardening (`EXT-01` URL ingestion, `EXT-02` controlled execution)
**Researched:** 2026-03-06
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12.x | Primary runtime for deterministic contracts and pipeline orchestration | Existing codebase is Python-first with dataclass contracts and deterministic serialization patterns already established |
| `urllib.parse` + `ipaddress` (stdlib) | Python 3.12 stdlib | Canonical URL parsing/normalization and IP boundary classification | Keeps critical normalization and boundary checks dependency-light and reproducible |
| `dataclasses` + `typing` (stdlib) | Python 3.12 stdlib | Typed contracts for policy, approval, provenance, and execution result envelopes | Aligns with current Phase 2-5 contract style and preserves explicit schema boundaries |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `idna` | 3.10 | Stable IDN hostname normalization before policy evaluation | Use when URL policy must safely handle unicode/punycode hostnames |
| `pytest` | 8.3.x | Deterministic and boundary regression suite | Use for repeated-run equality checks, fail-closed tests, and extension gate assertions |
| `hypothesis` | 6.127.x | Property-based tests for URL canonicalization edge cases | Use for canonicalization drift, redirect-chain, and parser ambiguity coverage |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `ruff` | Lint and import-policy enforcement | Add rules that reject network/process imports in dry-run-only modules |
| `mypy` | Static typing on new extension contracts | Enforce explicit optionality for approval/policy fields to prevent implicit fail-open logic |

## Installation

```bash
# Supporting runtime libs
pip install idna

# Dev dependencies
pip install pytest hypothesis ruff mypy
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Stdlib URL/IP primitives | `rfc3986` | Use if stricter RFC component validation is required beyond stdlib behavior |
| `pytest` + `hypothesis` | Unit tests only (no property tests) | Acceptable only if canonicalization complexity stays very small and bounded |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Headless browser fetching for EXT-01 | Adds non-deterministic rendering/network behavior and broadens boundary risk | Deterministic policy-gated HTTP retrieval to immutable snapshots only |
| Dynamic executor/plugin discovery for EXT-02 | Produces non-closed capability surface and unstable route-to-tool behavior | Static closed registry with explicit capability matrix |
| Runtime policy mutation without version pinning | Breaks replayability and audit determinism | Versioned policy artifacts and immutable policy snapshots |

## Stack Patterns by Variant

**If `EXT-01` remains in governance-only mode:**
- Keep URL logic contract-only (policy parse + normalization + decision enums)
- Because this enables early verification without expanding runtime ingestion behavior

**If `EXT-02` is simulate-first in v1.3:**
- Keep execution contracts and journal scaffolding active while execution adapters remain hard-gated
- Because this preserves no-execution safety while proving deterministic gating behavior

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.12 | `idna` 3.10 | Supports stable IDN processing used during canonical policy checks |
| `pytest` 8.3.x | `hypothesis` 6.127.x | Stable pairing for deterministic + property-based boundary tests |

## Sources

- Local codebase (`src/intent_pipeline/*`) — current contract and determinism patterns
- `.planning/research/FEATURES.md` — feature-level table stakes and complexity slicing
- `.planning/research/ARCHITECTURE.md` — integration points and additive component model
- `.planning/research/PITFALLS.md` — boundary-risk matrix and mitigation controls

---
*Stack research for: deterministic extension re-entry in Local Intent Sanitizer*
*Researched: 2026-03-06*
