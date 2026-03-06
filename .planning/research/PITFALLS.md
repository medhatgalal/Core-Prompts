# v1.3 EXT-01/EXT-02 Pitfalls Research

## Scope

- Focus area: `EXT-01` (URL ingestion) and `EXT-02` (controlled routing/execution) in a deterministic, boundary-first system.
- Baseline assumption from v1.2 governance: both extensions remain `defer` until explicit policy + verification gates are satisfied.

## Pitfall Matrix (Risk, Anti-Pattern, Prevention, Mitigation)

| ID | Extension | Pitfall + Anti-Pattern | Concrete Risk | Prevention Controls | Mitigation |
| --- | --- | --- | --- | --- | --- |
| P-01 | EXT-01 | Canonicalization drift. Anti-pattern: policy checks raw URL text before canonical normalization. | Allowlist bypass via case, percent-encoding, dot segments, or default-port variants. | Parse-normalize-parse pipeline; compare policy against canonical form only; reject non-stable normalization. | M-01 Canonical URL Gate |
| P-02 | EXT-01 | Scheme-smuggling. Anti-pattern: `startswith("http")` checks or permissive scheme parsing. | Non-approved schemes (`file:`, `data:`, `ssh:`) or malformed scheme strings bypass controls. | Closed scheme enum; strict URI parser; explicit deny list for local/embedded schemes. | M-02 Strict Scheme Contract |
| P-03 | EXT-01 | DNS/IP boundary bypass. Anti-pattern: host allowlist without resolved-address policy. | SSRF to loopback, link-local, RFC1918, metadata endpoints, or rebinding targets. | Resolve and classify all A/AAAA answers; deny private/special ranges; optionally pin resolved address per request. | M-03 Network Boundary Resolver |
| P-04 | EXT-01 | Redirect trust expansion. Anti-pattern: automatic redirect follow with no re-validation. | First URL is allowed, redirected URL is not; policy bypass through redirect chain. | Redirect budget (`max_redirects`), per-hop re-validation, same-policy enforcement for each `Location`. | M-04 Redirect Revalidation |
| P-05 | EXT-01 | Unbounded fetch envelope. Anti-pattern: no hard caps on bytes, duration, or content expansion. | Resource exhaustion, parser hangs, decompression bombs, nondeterministic timeout behavior. | Deterministic caps for connect/read/total time, response bytes, decompressed bytes, and max documents per run. | M-05 Bounded Fetch Envelope |
| P-06 | EXT-01 | Header-trust parsing. Anti-pattern: trust `Content-Type` without payload verification. | Unexpected binary/HTML/script content enters text pipeline and destabilizes sanitization. | MIME allowlist + magic-byte sniffing + charset validation; reject ambiguous or mismatched payloads. | M-06 Typed Payload Admission |
| P-07 | EXT-01 | Time-variant ingestion. Anti-pattern: fetch live pages without immutable capture contract. | Same input URL yields different downstream decisions across runs. | Capture manifest (URL, headers subset, content hash, timestamp, policy version); process by content hash thereafter. | M-07 Snapshot Ingestion Contract |
| P-08 | EXT-01 | Provenance collapse. Anti-pattern: remote and local sources handled as equivalent plain text. | Lost traceability; cannot prove which policy path admitted data. | Mandatory source provenance fields (`source_type`, `origin`, `admission_rule_id`, `content_hash`). | M-08 Provenance Envelope |
| P-09 | EXT-01 | Fail-open rejection paths. Anti-pattern: "best-effort" fallback after policy/parser rejection. | Rejected sources still influence downstream state via partial data. | Fail-closed pipeline contract; no parse/sanitize on rejected sources; typed rejection codes and evidence paths. | M-09 Fail-Closed Admission |
| P-10 | EXT-02 | Dynamic route-to-tool inference. Anti-pattern: tool chosen directly from free-form model output. | Unstable or unauthorized tool selection; nondeterministic execution paths. | Closed `route_profile -> tool_id` mapping in policy contract; reject unmapped profiles. | M-10 Static Route Mapping |
| P-11 | EXT-02 | Capability overgrant. Anti-pattern: wildcard capabilities or coarse "execute-all" profiles. | Privilege escalation and side-effect expansion beyond approved boundary. | Deny-by-default capabilities; per-profile required capabilities; explicit missing-capability block. | M-11 Least-Privilege Capability Matrix |
| P-12 | EXT-02 | Soft-validation execution. Anti-pattern: proceed when validation is degraded or partially failing. | Unsafe execution despite policy/routing contradictions. | Hard gate: execution allowed only when validation decision is PASS and `can_proceed=true`. | M-12 Hard Validation Gate |
| P-13 | EXT-02 | Dry-run side effects. Anti-pattern: mock/simulation imports network/fs/process APIs. | "Simulation" mutates system state, violating no-side-effect guarantee. | Static AST checks for forbidden imports/calls; hermetic test harness; explicit dry-run artifact-only outputs. | M-13 Side-Effect Firewall |
| P-14 | EXT-02 | Non-deterministic precedence. Anti-pattern: unordered policy/rule evaluation and ad hoc tie-breaks. | Same inputs produce different disposition/execution outcomes. | Fixed rule order, conservative tie-break precedence, canonical serialization and repeated-run equality tests. | M-14 Deterministic Decision Engine |
| P-15 | EXT-02 | Non-idempotent retries. Anti-pattern: automatic retry for write/execute actions without idempotency token. | Duplicate external effects on transient failures or race conditions. | Operation classes (`read`, `write`, `execute`), idempotency keys, retry budget by class, explicit replay policy. | M-15 Idempotent Execution Contract |
| P-16 | EXT-02 | Audit gaps. Anti-pattern: logs without policy version, rule IDs, or evidence paths. | Inability to prove why action was permitted/blocked; weak incident forensics. | Immutable execution ledger with input hash, output hash, policy version, rule IDs, decision, and evidence paths. | M-16 Deterministic Audit Ledger |
| P-17 | EXT-02 | Secret boundary bleed. Anti-pattern: passing full environment/context into tools by default. | Credential exposure or secret exfiltration via tool args/output. | Explicit secret scopes per tool, redaction at boundary, deny secret passthrough unless policy-allowed. | M-17 Secret Scope Control |
| P-18 | EXT-02 | Concurrent action races. Anti-pattern: parallel execution on shared targets without serialization rules. | Order-dependent effects and nondeterministic final state. | Deterministic scheduler (stable ordering + per-target lock), single-flight by operation key. | M-18 Deterministic Concurrency Guard |

## Mitigation Catalog

| Mitigation | Summary |
| --- | --- |
| M-01 Canonical URL Gate | Normalize URL to canonical form before any policy decision; reject if canonicalization is ambiguous or unstable. |
| M-02 Strict Scheme Contract | Only permit explicit schemes; reject all local, embedded, or unknown schemes. |
| M-03 Network Boundary Resolver | Resolve host and enforce IP boundary policy (deny loopback/local/private/special-use). |
| M-04 Redirect Revalidation | Re-apply full policy checks on each redirect hop with strict hop limits. |
| M-05 Bounded Fetch Envelope | Enforce deterministic caps on time, bytes, decompression, and fan-out. |
| M-06 Typed Payload Admission | Admit only validated MIME/charset/payload signatures compatible with the sanitizer pipeline. |
| M-07 Snapshot Ingestion Contract | Convert live URL fetch to immutable content-hash snapshot for deterministic downstream processing. |
| M-08 Provenance Envelope | Carry source provenance and policy admission metadata through all phases. |
| M-09 Fail-Closed Admission | Rejection ends processing; no silent fallback path for invalid/unapproved sources. |
| M-10 Static Route Mapping | Enforce route profile to tool mapping as static policy data, never model-improvised at runtime. |
| M-11 Least-Privilege Capability Matrix | Bind each route to minimal capabilities; block any missing or extra-required capabilities. |
| M-12 Hard Validation Gate | Allow controlled execution only when typed validation contract passes fully. |
| M-13 Side-Effect Firewall | Guarantee dry-run/mock code paths are side-effect-free by static and runtime controls. |
| M-14 Deterministic Decision Engine | Fix evaluation order and tie-breaks; require reproducible outputs for identical inputs. |
| M-15 Idempotent Execution Contract | Require idempotency semantics and replay-safe behavior before allowing retries. |
| M-16 Deterministic Audit Ledger | Persist machine-auditable evidence for every decision and attempted action. |
| M-17 Secret Scope Control | Minimize secret exposure with explicit scoped injection and mandatory redaction. |
| M-18 Deterministic Concurrency Guard | Serialize conflicting actions with deterministic ordering and lock strategy. |

## Minimum v1.3 Admission Controls (Go/No-Go)

1. `EXT-01` should remain non-go unless M-01 through M-09 are implemented and backed by deterministic pass/fail tests.
2. `EXT-02` should remain non-go unless M-10 through M-18 are implemented with fail-closed execution gates.
3. Any partial implementation that weakens no-side-effect guarantees or deterministic replay should default to `defer` (or `reject` if boundary safety is violated).
