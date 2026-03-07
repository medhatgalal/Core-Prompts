# Phase 9: EXT-01 Deterministic URL Ingestion - Research

**Researched:** 2026-03-06
**Domain:** Canonical URL admission, bounded retrieval, immutable snapshot ingestion
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Phase 9 admits URL inputs only through explicit shared-gate approval plus URL-specific policy approval.
- URL content must be converted to immutable local snapshots before sanitization.
- Rejected URLs must fail closed and never reach sanitize, routing, or execution paths.
- Provenance must be explicit and deterministic in downstream uplift artifacts.
- No authenticated browsing, dynamic rendering, recursive crawl, or execution expansion in this phase.

### Claude's Discretion
- Exact module boundaries for resolver, URL policy, and snapshot store.
- Exact rejection-code taxonomy and fetch implementation details.
- Test file layout and fixture strategy.

### Deferred Ideas (OUT OF SCOPE)
- Authenticated URL profiles
- Browser-rendered content
- Multi-document or recursive ingestion
- Any execution gating or tool/runtime work

</user_constraints>

<research_summary>
## Summary

Phase 9 should preserve the existing deterministic ingestion guarantee by treating URLs as a policy-gated transport that resolves into local immutable snapshots before any existing reader or sanitizer runs. The cleanest fit in this codebase is to keep the shared Phase 8 extension contract unchanged, add a dedicated URL-policy contract for Phase 9 semantics, and make the phase-1 pipeline read only local descriptors regardless of original source type.

The recommended architecture is:

`raw source -> source_resolver -> shared extension gate -> url_policy_validate -> bounded_fetch -> snapshot_store -> read_local_file_text -> sanitize_two_pass -> render_intent_summary`

This architecture keeps the network boundary narrow, makes failure modes typed and testable, and preserves byte-stable outputs because downstream phases consume a pinned local snapshot rather than a live response stream.

**Primary recommendation:** implement `source_resolver.py`, `url_policy.py`, and `url_snapshot_store.py` as dedicated ingestion modules, then wire them through `pipeline.py` and provenance-aware uplift helpers.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `urllib.parse` | Python 3.12 stdlib | Canonical URL parsing and normalization | Matches deterministic, dependency-light repo style |
| `urllib.request` | Python 3.12 stdlib | Bounded URL retrieval and redirect control | Avoids adding new HTTP client dependency in Phase 9 |
| `ipaddress` | Python 3.12 stdlib | Private/special-use IP boundary enforcement | Required for SSRF-style boundary protection |
| `socket` | Python 3.12 stdlib | DNS resolution for resolved-address policy checks | Needed to classify destination addresses deterministically |
| `hashlib`, `pathlib`, `tempfile` | Python 3.12 stdlib | Content-addressed snapshot storage | Aligns with immutable local artifact design |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 8.x | Boundary, determinism, and integration tests | Required for requirement evidence |
| Existing repo contract helpers | current | Canonical serialization and boundary behavior | Reuse instead of inventing ad hoc envelopes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Stdlib fetcher | `httpx` / `requests` | Better ergonomics, but unnecessary dependency expansion for a bounded deterministic phase |
| Separate snapshot DB | SQLite manifest | More queryable, but content-addressed flat files are sufficient and simpler for v1.3 |
| Overloading Phase 8 policy schema | Dedicated Phase 9 URL policy contract | Separate contract keeps source-kind gate semantics distinct from fetch/content constraints |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Resolver before policy
**What:** classify input source kind and canonicalize URL before any admission policy decision.
**When to use:** all ingestion entrypoints.

### Pattern 2: Two-layer admission
**What:** shared extension contract decides whether URL source kind is even allowed; URL policy decides whether the concrete canonical URL and response envelope are allowed.
**When to use:** any URL path in Phase 9.

### Pattern 3: Snapshot-first ingestion
**What:** convert approved live response into a content-addressed local snapshot before existing reader/sanitizer stages.
**When to use:** all approved URL ingestion flows.

### Pattern 4: Provenance as explicit source metadata
**What:** carry normalized source, policy rule, and content hash in the `context.source` envelope.
**When to use:** all URL-backed uplift artifacts.

### Anti-Patterns to Avoid
- Evaluating URL policy on raw user input before normalization.
- Letting reader/sanitizer operate on network streams or partially fetched responses.
- Trusting response `Content-Type` without payload- and charset-level validation.
- Following redirects without re-validating each hop.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL parsing | Regex-only URL classification | `urllib.parse` parse-normalize-serialize flow | Avoids scheme/host/path edge-case drift |
| Address safety | String-prefix host checks | `socket.getaddrinfo` + `ipaddress` classification | Blocks loopback/private/special-use bypasses reliably |
| Snapshot identity | Timestamp-based filenames | SHA-256 content-addressed snapshot path | Makes replay and determinism checks straightforward |
| Provenance transport | Ad hoc extra fields in tests only | Stable `context.source` envelope extension | Ensures later phases and tests consume the same contract |

**Key insight:** the determinism boundary is preserved only if the live network boundary ends before the existing local reader path begins.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Canonicalization drift
**What goes wrong:** different string forms of the same URL evaluate differently.
**How to avoid:** one canonical normalization routine and tests for case/default-port/path normalization.

### Pitfall 2: Redirect policy bypass
**What goes wrong:** initial URL is allowed, redirect target is not.
**How to avoid:** re-run URL policy and address boundary checks on every redirect hop.

### Pitfall 3: Provenance collapse
**What goes wrong:** URL-derived content looks identical to local content downstream.
**How to avoid:** stable `source_type`, `normalized_source`, `policy_rule_id`, and `content_sha256` fields in uplift context.

### Pitfall 4: Fail-open fetch errors
**What goes wrong:** partial or malformed responses fall back into sanitize path.
**How to avoid:** every network/policy/content failure terminates before snapshot read and returns typed deterministic evidence.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

Phase 9 needs tests across four lanes:
- **Resolver tests:** local-vs-URL classification, canonical URL output, invalid/unsupported URL rejection.
- **Policy tests:** scheme/host/path/content-type/size/redirect/timeout rules and typed fail-closed parsing.
- **Snapshot tests:** immutable local materialization, content-hash identity, redirect revalidation, private-address blocking.
- **Integration tests:** approved URL path reaches sanitize/summary through local snapshot only; rejected URL path never reaches sanitizer; uplift context preserves provenance deterministically.

Required pass criteria:
1. Canonical URL decisions are byte-stable across repeated and cross-process runs.
2. Shared disabled-mode local-only behavior remains unchanged.
3. Requirement IDs `EXT1-01` through `EXT1-05` each map to at least one deterministic automated test.
</validation_architecture>

<open_questions>
## Open Questions

1. **How strict should path-prefix policy be?**
   - What we know: policy needs explicit path dimension support.
   - Recommendation: treat missing path prefixes as allow-all within the admitted host/domain and keep matching prefix-based, not glob-based, for v1.3.

2. **Where should snapshot files live by default?**
   - What we know: they must be immutable local files before sanitization.
   - Recommendation: allow caller override, but default to deterministic content-addressed files under a local snapshot root managed by the snapshot store.

3. **How should URL provenance enter uplift code without breaking tests?**
   - What we know: `build_context_layer` currently takes only sanitized text.
   - Recommendation: add optional `source_metadata` input with stable defaults for current callers.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/phases/09-ext-01-deterministic-url-ingestion/09-CONTEXT.md` — locked scope and decisions
- `.planning/research/ARCHITECTURE.md` — integration points and component split
- `.planning/research/PITFALLS.md` — URL-ingestion risks and required mitigations
- `.planning/research/SUMMARY.md` — milestone-level rationale and sequencing
- `src/intent_pipeline/ingestion/policy.py`, `reader.py`, `pipeline.py` — current local-only boundaries
- `src/intent_pipeline/uplift/context_layer.py`, `engine.py` — provenance propagation entrypoints
- `tests/test_ingestion_boundary.py`, `tests/test_extension_gate_boundary.py`, `tests/test_extension_gate_determinism.py` — reusable deterministic test patterns

</sources>

---
*Phase: 09-ext-01-deterministic-url-ingestion*
*Research completed: 2026-03-06*
*Ready for planning: yes*
