# v1.3 Feature Scope Research: EXT-01 and EXT-02

## table-stakes
- Cross-cutting deterministic boundary contract (applies to both extensions): fail-closed defaults, closed enums, typed error codes, stable ordering, and byte-stable serialization for identical input + policy.
- Cross-cutting governance contract: every boundary-expanding action must be policy-gated, explicitly versioned, and evidence-linked (no implicit or heuristic-only approvals).
- EXT-01 (URL ingestion) minimum scope:
  - Add explicit URL admission policy (scheme/domain/path/content-type/size/redirect/timeouts) with deterministic allow/deny outcomes.
  - Canonical URL normalization before policy evaluation (same input URL always yields same normalized form and decision).
  - Read-only retrieval behavior only (no auth/session/cookie state, no JS rendering, no mutable remote actions).
  - Typed rejection/acceptance evidence paths integrated into ingestion contracts.
  - Boundary tests proving no bypass of local-file safety rules outside policy-approved URL paths.
- EXT-02 (downstream routing/execution) minimum scope:
  - Keep execution behind explicit approval policy and deterministic gates.
  - Require deterministic pre-execution validation and dry-run trace before any execute-eligible path.
  - Enforce closed tool/capability matrix and explicit deny lists for route profiles.
  - Preserve deterministic fallback to `NEEDS_REVIEW` when any approval, capability, or safety invariant is missing.

## differentiators
- Policy snapshot replayability: same request + same policy version + same inputs produces identical decisions and traces.
- Governance-as-code instead of prose-only governance: versioned policy artifacts with deterministic rule IDs and audit-ready evidence paths.
- Staged execution model: simulate-first and execute-by-exception, rather than direct execution on first pass.
- Boundary-aware determinism: explicit refusal paths are first-class outputs, not runtime surprises.

## anti-features/out-of-scope
- Autonomous/open-ended execution beyond closed, policy-approved capability sets.
- Arbitrary shell/network calls selected dynamically by model output.
- Recursive crawling, authenticated browsing, or browser-style dynamic rendering for EXT-01.
- Runtime policy mutation, hot-patching allowlists, or operator-implicit overrides without traceable policy version change.
- Auto-remediation behaviors that install packages, modify environment state, or silently retry side-effecting actions.
- Any feature that degrades deterministic outcomes (time/randomness-dependent ranking, non-stable output ordering, implicit fallback behavior).

## complexity notes
- EXT-01 complexity: medium-high.
  - Primary risks are URL normalization edge cases, redirect handling, content-type ambiguity, and SSRF-style boundary bypass patterns.
  - Complexity remains manageable if v1.3 constrains retrieval to strict policy-governed read-only ingestion.
- EXT-02 complexity: high.
  - Side-effect governance, idempotency, rollback semantics, and approval propagation create higher coupling and failure-mode surface.
  - Deterministic execution semantics are substantially harder than deterministic routing/validation.
- Recommended v1.3 slicing:
  - Slice A: shared policy/contract hardening for EXT-01 and EXT-02 (no new side effects yet).
  - Slice B: EXT-01 controlled rollout with deterministic URL ingestion gates.
  - Slice C: EXT-02 simulate-first default; execute path remains narrowly gated until deterministic evidence is proven.
- Suggested release gate for each slice: deterministic regression suite pass, boundary tests pass, contradiction scan pass across PROJECT/REQUIREMENTS/ROADMAP language.

## dependencies
- Product/policy dependencies:
  - New requirement IDs for v1.3 that separate policy readiness from runtime enablement (do not collapse governance and implementation into one requirement).
  - Explicit approval model for execution with deny-by-default semantics.
- Code dependencies in current architecture:
  - `src/intent_pipeline/ingestion/policy.py`: extend URI policy from blanket reject to explicit policy-evaluated URL admissions.
  - `src/intent_pipeline/ingestion/reader.py`: add deterministic URL-read path with typed errors while preserving local-file path behavior.
  - `src/intent_pipeline/phase4/contracts.py` and `src/intent_pipeline/phase4/validator.py`: extend policy/capability contracts for execute eligibility gates.
  - `src/intent_pipeline/phase4/mock_executor.py`: keep simulate path canonical and evidence-linked for execute gating.
  - `src/intent_pipeline/phase5/runtime_checks.py` and `src/intent_pipeline/phase5/help.py`: keep preflight/help strictly non-executing and policy-consistent.
- Testing dependencies:
  - New boundary tests for URL policy bypass prevention and deterministic rejection coding.
  - New deterministic cross-run tests for URL normalization and policy evaluation ordering.
  - New execution-gate tests proving fail-closed behavior when approvals/capabilities are incomplete.
- Operational dependencies:
  - Versioned policy artifacts and immutable run-time policy snapshot capture for auditability.
  - Clear rollout mode flags (`governance-only`, `simulate-only`, `execute-gated`) to avoid accidental boundary expansion.
