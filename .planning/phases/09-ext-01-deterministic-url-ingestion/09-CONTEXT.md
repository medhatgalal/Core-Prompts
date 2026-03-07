# Phase 9: EXT-01 Deterministic URL Ingestion - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning and execution

<domain>
## Phase Boundary

Phase 9 introduces policy-admitted URL ingestion as a bounded, deterministic extension of the existing local-file pipeline. URL inputs are permitted only when they survive shared Phase 8 extension gates, URL-specific admission policy checks, and immutable snapshot materialization.

In scope for Phase 9:
- Canonical source resolution that classifies local paths vs URLs deterministically.
- URL admission policy with explicit allow/deny dimensions and typed rejection codes.
- Immutable local snapshot materialization for approved URL payloads before sanitization.
- Provenance-safe propagation of URL source metadata into downstream uplift artifacts.
- Deterministic and boundary regression coverage for allow, reject, and fail-closed paths.

Explicitly out of scope for Phase 9:
- Rosetta translation changes beyond preserving existing routing inputs.
- Target tool validation or execution behavior.
- Browser rendering, authenticated browsing, recursive crawl, or multi-document fan-out.
- Dynamic policy mutation or open-ended runtime capability expansion.

</domain>

<decisions>
## Implementation Decisions

### Source classification and normalization
- Add a dedicated source resolver ahead of ingestion policy/read so raw input is classified as `LOCAL_FILE` or `URL` before any read path is chosen.
- Canonicalize URLs before policy evaluation using a strict parse-normalize-serialize flow:
  - lowercase scheme and host
  - punycode hostname via IDNA encoding when needed
  - remove default ports for `http` and `https`
  - normalize empty path to `/`
  - preserve query ordering as supplied after whitespace trimming
- Reject unsupported or unstable URL forms rather than attempting permissive repair.

### URL admission policy and rejection semantics
- Keep Phase 8 shared extension contract as the first gate, then run a Phase 9 URL-specific policy contract.
- URL policy must be explicit about:
  - allowed schemes
  - allowed hosts and/or suffix domains
  - optional path prefixes
  - content-type allowlist
  - max response bytes
  - redirect budget
  - timeout budget
- Rejections must be typed and deterministic, and rejected URLs must terminate before snapshot creation or sanitization.
- Policy parsing remains fail closed: missing or malformed URL-policy artifacts become deterministic `NEEDS_REVIEW`/block outcomes with evidence paths.

### Snapshot ingestion and deterministic retrieval
- Approved URL content is retrieved only through a bounded fetch routine with fixed timeout, redirect, and byte limits.
- The live response is converted immediately into an immutable local snapshot identified by content hash.
- Downstream pipeline stages continue to read from the local filesystem only; they never process a live network stream.
- Snapshot metadata must record canonical source, content hash, selected policy rule, content type, byte count, and retrieval evidence.

### Provenance propagation
- Extend the uplift context `source` block to carry deterministic provenance for URL-backed inputs:
  - `source_type`
  - `normalized_source`
  - `policy_rule_id`
  - `content_sha256`
- Local-file baseline fields remain stable so existing local-only callers are not broken.
- Provenance values are treated as input metadata, not inferred content facts.

### Boundary and non-regression posture
- Local-file ingestion remains unchanged when `extension_mode=DISABLED`.
- No URL path is reachable without shared extension gate approval and URL-policy approval.
- Phase 9 permits bounded network reads for approved URL ingestion only; no cookies, auth headers, JavaScript execution, form submission, or arbitrary header passthrough.
- Unknown schemes, unresolved policy gaps, redirect overflow, content-type mismatch, oversize payloads, and private/special-use IP destinations all fail closed.

### Auto defaults selected for `--auto`
- Use a single deterministic fetch implementation built on Python stdlib primitives rather than adding a new HTTP client dependency in this phase.
- Keep snapshot storage inside the repo-local temp/test space or caller-provided directory, with content-addressed filenames.
- Keep URL policy as a dedicated Phase 9 contract module rather than overloading the shared Phase 8 extension policy schema.

</decisions>

<specifics>
## Specific Ideas

- Model the ingestion chain as: `resolve -> shared gate -> url policy -> snapshot -> local read -> sanitize -> summary`.
- Keep redirect handling explicit and conservative: each hop must re-pass URL policy validation.
- Use deterministic evidence paths that distinguish shared gate failures from URL policy failures and fetch/snapshot failures.
- Preserve the current one-file/one-summary terminal behavior; URL ingestion only changes how the initial source text is obtained.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/intent_pipeline/extensions/contracts.py`: shared extension contract and fail-closed policy parsing from Phase 8.
- `src/intent_pipeline/extensions/gates.py`: deterministic shared gate evaluation already blocks unknown modes, profiles, and capabilities.
- `src/intent_pipeline/ingestion/policy.py`: current local-only admission layer; natural integration point for source resolution and URL policy handoff.
- `src/intent_pipeline/ingestion/reader.py`: preserves the invariant that sanitization reads from local files only.
- `src/intent_pipeline/pipeline.py`: current phase-1 entrypoint and best place to branch between local and URL ingestion paths.
- `src/intent_pipeline/uplift/context_layer.py`: existing deterministic source metadata block that can be extended with provenance fields.
- `tests/test_ingestion_boundary.py`, `tests/test_extension_gate_boundary.py`, `tests/test_extension_gate_contracts.py`, `tests/test_extension_gate_determinism.py`: existing fail-closed and deterministic coverage patterns to extend.

### Established Patterns
- Dataclass/enum contracts with schema-major validation.
- Canonical JSON serialization using `sort_keys=True` and stable list ordering.
- Fail-closed boundary tests that reject unknown or malformed inputs before deeper phases execute.
- Cross-process determinism checks for byte-stable outputs.

### Integration Points
- Add `src/intent_pipeline/ingestion/source_resolver.py` for source-kind classification and URL normalization.
- Add `src/intent_pipeline/ingestion/url_policy.py` for typed URL-policy contracts and deterministic rejection reasons.
- Add `src/intent_pipeline/ingestion/url_snapshot_store.py` for bounded retrieval and immutable content-addressed snapshots.
- Modify `src/intent_pipeline/ingestion/policy.py` to orchestrate shared extension gate + URL policy for URL sources.
- Modify `src/intent_pipeline/pipeline.py` to allow approved URL sources into the existing sanitize/summary flow.
- Modify `src/intent_pipeline/uplift/context_layer.py` and `src/intent_pipeline/uplift/engine.py` so source provenance survives into downstream phases.

</code_context>

<deferred>
## Deferred Ideas

- Authenticated or session-aware URL retrieval profiles.
- Browser-rendered or JavaScript-evaluated ingestion.
- Multi-document URL collection, crawling, or recursive discovery.
- Any execution path or tool invocation based on URL-derived content.

</deferred>

---

*Phase: 09-ext-01-deterministic-url-ingestion*
*Context gathered: 2026-03-06*
