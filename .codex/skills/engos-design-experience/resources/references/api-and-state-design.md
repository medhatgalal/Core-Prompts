# Design with data, APIs, and states

Use for service-backed or stateful experiences. A static report may only need accurate provenance and freshness; it does not need a fabricated service architecture.

## Establish what the interface can truthfully do

Inspect relevant specifications, existing clients, implementation, and representative responses when available. Resolve contradictions rather than assuming a specification proves current behavior. Record the source and version where they affect a decision. Use current official API documentation for unfamiliar contracts; OpenAPI is one possible format, not a requirement.

Map important actions at the depth needed to design them:

| User action | Data and operation | Permission | Pending behavior | Success | Failure and recovery |
| --- | --- | --- | --- | --- | --- |
| The user's intended action | Actual operation, or explicitly proposed contract | Relevant role or permission | What remains usable and whether work can be cancelled | What confirms the result | Relevant error, preserved context, and next action |

This is a thinking and handoff aid, not a mandatory table in every answer. The same information may be embodied in a prototype or specification.

Separate **supported now**, **requires a system change**, and **unverified or mocked** behavior. When contracts are missing, propose the smallest useful assumption and label it. Do not present proposed endpoints, latency guarantees, permission rules, or calls as existing or verified. A desired experience can justify a backend recommendation; it cannot make that capability exist.

## Let real semantics shape the interaction

- **Search and collections:** Distinguish searching visible items from the full collection. Match sorting, filters, counts, and pagination to service support. Do not imply complete results from a partial page.
- **Mutations:** Establish when a change is committed. Use optimistic feedback only when error recovery and rollback are credible. Pending is not success.
- **Bulk actions:** Represent partial outcomes when the service does not guarantee atomicity. Preserve failed items and avoid inviting duplicate submission of successful ones.
- **Delayed work:** Reflect the actual job states and known progress. Do not turn unknown duration into invented percentages. Cancellation and retry depend on supported semantics.
- **Permissions:** Present meaningful unavailable states and explain them when appropriate. UI visibility is not authorization enforcement.
- **Conflicts and interrupted work:** Handle stale edits, lost connection, or expired sessions where consequential to the task. Preserve work and provide a credible recovery path when supported.

In a recovery state, distinguish actions by their effect. If "Retry" and the unchanged primary action perform the same operation, prefer one clear next action rather than competing equivalents. Preserve genuinely different choices, such as retrying the operation, changing the input, or abandoning it. Do not remove confirmation or review that a real consequence or product rule requires.

For AI-assisted features, consider whether the user needs sources, uncertainty, review before action, correction, or reversal. Show the real status of generated or automated work. Do not invent confidence scores to create trust.

## Build useful prototypes honestly

Use representative synthetic or approved data. Keep mocks identifiable in the artifact or handoff as appropriate; do not expose real sensitive data merely to make a demonstration convincing. Include a meaningful failure or permission scenario when it tests an important design choice.

A proposed API contract is a design output. A successful mock is prototype evidence. A verified operation against the actual service is integration evidence. Report those levels accurately and only perform live operations within the user's authorization.

Product APIs govern the experience. Agent tool APIs govern inspection, generation, and validation. Availability of a browser or drawing tool does not establish access to the product's backend, or authority to modify it.
