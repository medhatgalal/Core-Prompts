# Phase 7: Extension Governance Decision Pack (`EXT-01`, `EXT-02`) - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Finalize deterministic go/defer/reject governance decisions for deferred extensions `EXT-01` (URL ingestion) and `EXT-02` (downstream routing/execution), and synchronize resulting boundary language across planning artifacts. This phase defines policy and traceability only; it does not implement new runtime capabilities.

</domain>

<decisions>
## Implementation Decisions

### Decision rubric and evidence standard
- Use a deterministic rubric with explicit criteria per extension: boundary safety, determinism impact, policy/control maturity, and verification readiness.
- Each extension decision must include: disposition (`go`, `defer`, or `reject`), rationale, risk statement, and required preconditions for reconsideration.
- Decisions must be evidence-backed using existing project artifacts (requirements, roadmap, archived milestone docs), not ad hoc assumptions.

### `EXT-01` governance framing (URL ingestion)
- Treat URL ingestion as high-boundary-risk until explicit validation and policy controls are fully specified and testable.
- For v1.2 scope, default-safe posture is non-implementation; decision output must clearly state whether `EXT-01` is deferred or rejected and under what conditions it could move to `go`.
- If disposition is not `go`, document concrete gating criteria (policy contract, deterministic validation, boundary tests) required for future phase admission.

### `EXT-02` governance framing (downstream routing/execution)
- Treat downstream execution as a stricter boundary tier than `EXT-01` due side-effect risk and interaction with no-execution guarantees.
- For v1.2 scope, require explicit approval model and deterministic execution governance contract before any `go` outcome is considered.
- Decision output must explicitly preserve current no-execution guarantees unless all required controls are satisfied and approved in a future milestone.

### Cross-document synchronization contract
- Project-level boundary language in `PROJECT.md`, scope/traceability entries in `REQUIREMENTS.md`, and milestone/phase framing in `ROADMAP.md` must remain semantically aligned after decisions are published.
- No mixed signals allowed (for example: one file says `defer`, another implies near-term implementation).
- Update history should remain auditable with requirement IDs `EXTG-01` and `EXTG-02` explicitly referenced.

### Claude's Discretion
- Exact rubric scoring format (table vs structured bullets).
- How to present preconditions and risk statements for readability.
- Whether decision output is captured directly in existing files or with an additional milestone note, as long as canonical docs are synchronized.

</decisions>

<specifics>
## Specific Ideas

- Use a two-level outcome statement per extension: "Decision now" and "Re-entry criteria".
- Keep wording deterministic and policy-like (avoid aspirational or ambiguous language).
- Include explicit statement that Phase 7 produces governance outcomes only, not capability delivery.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/REQUIREMENTS.md`: Contains canonical `EXT-01`, `EXT-02`, `EXTG-01`, and `EXTG-02` anchors for decision mapping.
- `.planning/ROADMAP.md`: Defines Phase 7 goal/success criteria and required scope boundaries.
- `.planning/PROJECT.md`: Contains current milestone goal and out-of-scope boundaries that governance decisions must preserve or explicitly amend.

### Established Patterns
- Prior milestones enforce strict deterministic boundary language and no-execution guarantees.
- Requirement IDs are used as canonical traceability anchors across planning artifacts.
- Milestone hardening work favors explicit parity and auditable evidence over implicit interpretation.

### Integration Points
- Governance decisions must propagate into `PROJECT.md`, `REQUIREMENTS.md`, and `ROADMAP.md` in one consistent pass.
- Any future extension admission criteria should be staged as next-milestone inputs rather than appended as in-phase implementation scope.

</code_context>

<deferred>
## Deferred Ideas

- Designing and implementing full URL policy validators and network safety controls (future implementation phase).
- Designing and implementing an execution authorization model with runtime side-effect governance (future implementation phase).
- Any capability build-out beyond decision artifacts and boundary-language synchronization.

</deferred>

---

*Phase: 07-extension-governance-decision-pack-ext-01-ext-02*
*Context gathered: 2026-03-05*
