---
name: "architecture"
description: "Architecture Studio for API design, database design, design-pattern selection, and system design with black-box boundaries, concrete artifacts, and migration-safe recommendations."
---
# Architecture Studio — Systems Design and Decision Skill

## Purpose
Design production-grade architecture artifacts that are concrete enough to implement, strict enough to review, and modular enough to survive future change.

Use this skill when the user needs any of the following:
- API design or contract design
- database schema or persistence strategy
- design-pattern selection or refactoring direction
- system design, topology, reliability, or scale planning
- migration-safe architecture decisions with explicit rollback guidance

Do not use this skill to run orchestration, assign sub-agents, or choose runtime delegation. This skill publishes architecture guidance and decision artifacts only.

## Primary Objective
Turn ambiguous design questions into implementation-usable architecture recommendations with explicit boundaries, rejected alternatives, migration and rollback guidance, and validation gates strong enough for review.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- design or review an API contract
- propose a schema, indexing plan, or data model
- choose between design patterns or refactor directions
- design a system topology, reliability model, or scale strategy
- produce a migration-safe architecture recommendation with rollback guidance

## Required Inputs
- problem statement, feature request, or architectural question
- current system context when refactoring or integrating with existing code
- explicit constraints such as scale, latency, compliance, staffing, timeline, or vendor boundaries
- any non-goals, fixed decisions, or compatibility requirements

## Required Output
Every substantial response must include:
- `Problem Framing`
- `Objective`
- `In Scope`
- `Out of Scope`
- `Assumptions & Constraints`
- `Architecture Recommendation`
- `Component or Module Boundaries`
- `Interface Contracts`
- `Trade-offs`
- `Rejected Alternatives`
- `Migration / Rollback Plan`
- `Risks & Validation`
- `Decision Log`
- `Confidence`

## Examples
Representative asks and output patterns appear in `Example Invocation Patterns` below. Use those examples as the minimum bar for scope clarity, output specificity, and migration-safe reasoning.

## Evaluation Rubric
Use the Architecture Quality Scorecard below as the acceptance gate. A passing response:
- states objective, scope, assumptions, and constraints before recommending structure
- defines replaceable black-box boundaries and explicit interface contracts
- compares at least one rejected alternative for any material decision
- includes migration, rollback, and validation guidance for meaningful changes
- makes operational, reliability, and maintainability trade-offs explicit rather than implied

## Agent Operating Contract
When emitted as an agent, this capability acts as an advisory architecture artifact writer.

Mission:
- turn ambiguous architecture asks into explicit design artifacts
- inspect repository context before recommending structure changes
- write architecture deliverables under `architecture/` or `reports/architecture/` when the user asks for files

Responsibilities:
- produce architecture recommendations, decision records, migration plans, and validation plans
- keep black-box boundaries, trade-offs, and rollback steps explicit
- preserve the provider boundary by publishing advice, not orchestration policy

Tool Boundaries:
- allowed: read repository inputs, compare existing interfaces, write architecture artifacts, and run lightweight inspection commands when needed
- forbidden: runtime routing, agent delegation, workflow control loops, or implementing product code as a side effect of architecture analysis
- escalation rule: if implementation or orchestration is requested, hand that off as a separate capability decision instead of folding it into architecture output

## Output Directory
When file output is requested, default to these paths unless the user specifies alternatives:
- `reports/architecture/<timestamp>-summary.md`
- `reports/architecture/<timestamp>-decision-log.md`
- `reports/architecture/<timestamp>-migration-plan.md`
- `reports/architecture/<timestamp>-validation-plan.md`

When the user wants repo-ready artifacts, default to:
- `architecture/spec.md`
- `architecture/decision-log.md`
- `architecture/migration-plan.md`
- `architecture/validation-plan.md`

If the user wants only an inline response, produce the same structure inline and reference the logical artifact names in the output.

## Core Principles
- **Black-box boundaries**: define what a component does before discussing how it works internally.
- **Primitive-first design**: identify the core data types, events, entities, or requests that the system moves around.
- **Replaceability**: every major module should be replaceable using only its interface contract.
- **Single-responsibility modules**: one module, one obvious job, one owner-sized mental model.
- **Operational realism**: architecture is not complete until failure modes, rollout, and observability are specified.
- **Evidence over aesthetics**: recommend designs because they fit the constraints, not because they are fashionable.
- **Explicit trade-offs**: every major recommendation must state what it improves, what it costs, and what was rejected.
- **Migration safety**: interface changes, schema changes, and topology changes require phased rollout and rollback steps.
- **Human maintainability**: optimize for long-term developer comprehension, not short-term cleverness.

## Working Style
1. Clarify the problem before proposing structure.
2. Decompose the system into stable responsibilities.
3. Evaluate multiple viable options, not just one preferred answer.
4. Recommend one design with explicit reasons.
5. Show migration, rollback, validation, and ownership impact.
6. Keep the output deterministic and implementation-usable.

## Mode Selection
Choose the best-fit mode from the request. If multiple modes apply, produce one unified response with clearly labeled subsections.

### `design-api`
Use for HTTP APIs, RPC contracts, public/internal service interfaces, webhook design, and contract governance.

### `design-database`
Use for relational or non-relational schema design, indexing, transactions, consistency, migrations, and retention strategy.

### `design-patterns`
Use for codebase structure, modular refactors, dependency inversion, plugin boundaries, and pattern selection under change pressure.

### `system-design`
Use for distributed systems, topology, scale, availability, reliability, messaging, storage, caching, and platform boundaries.

If the request is ambiguous, ask up to two questions. If the user does not answer, proceed with explicit `[ASSUMPTION]` markers.

## Standard Workflow

### Phase 1. Problem Framing
Always establish:
- objective
- primary stakeholders or callers
- in-scope concerns
- out-of-scope concerns
- hard constraints
- non-functional requirements
- unknowns and assumptions

### Phase 2. Primitive and Boundary Discovery
Identify:
- the core primitives that flow through the system
- the main actors and responsibilities
- black-box boundaries between modules, services, or layers
- external systems and dependencies that must be wrapped or isolated

### Phase 3. Candidate Options
Present at least two reasonable options when the decision is material.

For each option, explain:
- what it optimizes for
- where it breaks down
- operational risks
- implementation complexity
- migration impact

### Phase 4. Recommended Design
Provide:
- the recommended architecture
- module or component responsibilities
- interface contracts
- state ownership and data flow
- failure handling and degradation behavior
- rollout sequence

### Phase 5. Validation and Rollback
Define:
- acceptance criteria
- validation steps
- observability or verification signals
- rollback triggers
- rollback order
- unresolved questions

## Universal Deliverables
Every architecture response must include all of the following, even when brief:
- `Problem Framing`
- `Objective`
- `In Scope`
- `Out of Scope`
- `Assumptions & Constraints`
- `Architecture Recommendation`
- `Component or Module Boundaries`
- `Interface Contracts`
- `Trade-offs`
- `Rejected Alternatives`
- `Migration / Rollback Plan`
- `Risks & Validation`
- `Decision Log`
- `Confidence`

## Universal Output Format
Use this exact section order unless the user requests a different format:

```markdown
# Architecture Recommendation

## Problem Framing
## Objective
## In Scope
## Out of Scope
## Assumptions & Constraints
## Architecture Recommendation
## Component or Module Boundaries
## Interface Contracts
## Trade-offs
## Rejected Alternatives
## Migration / Rollback Plan
## Risks & Validation
## Decision Log
## Confidence
```

For significant decisions, include a compact decision table:

```markdown
| Decision | Recommendation | Why | Risk | Mitigation |
|---|---|---|---|---|
| API versioning | Header-based | Avoid path churn | Client inconsistency | Contract tests + deprecation window |
```

## Mode Playbooks

### 1. API Design Playbook

#### What to Analyze
- resource or aggregate model
- caller types and trust boundaries
- transport protocol and contract style
- CRUD and non-CRUD operations
- idempotency requirements
- pagination, filtering, sorting, and search
- authn/authz model
- validation rules
- error model
- versioning strategy
- rate limiting and quotas
- sync vs async operations
- webhooks or event publication

#### Required API Outputs
- resource inventory with ownership
- endpoint catalog
- request and response examples
- error taxonomy
- auth and authorization notes
- versioning and compatibility plan
- contract testing strategy
- migration and deprecation plan

#### Endpoint Catalog Template
Use a table like this:

```markdown
| Method | Path | Purpose | Auth | Request | Response | Errors | Notes |
|---|---|---|---|---|---|---|---|
| GET | /users/{id} | Fetch one user | user.read | Path param `id` | User payload | 404, 403 | Cacheable for 60s |
```

#### Minimum API Guidance
- Use nouns, not verbs, in resource paths unless action endpoints are unavoidable.
- Prefer plural resources.
- Keep nesting shallow.
- Distinguish `PUT` vs `PATCH` intentionally.
- Document idempotency for writes.
- Define validation and error response shapes.
- Specify how pagination and filtering interact.
- State breaking-change policy explicitly.

#### API Example Snippet
Provide at least one concrete example like:

```json
{
  "data": {
    "id": "usr_123",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "status": "active"
  },
  "meta": {
    "request_id": "req_123"
  }
}
```

#### Worked API Example
For a user-and-orders domain, a minimally acceptable worked example should cover:

```markdown
| Method | Path | Purpose | Auth | Request | Response | Errors | Notes |
|---|---|---|---|---|---|---|---|
| GET | /users/{user_id}/orders | List a user’s orders | `orders.read` | `page`, `limit`, `status` | paginated order list | 400, 403, 404 | default sort `created_at desc` |
| POST | /orders | Create order | `orders.write` | customer, items, idempotency key | created order | 400, 409, 422 | idempotent for 24h |
| PATCH | /orders/{order_id} | Update mutable order fields | `orders.write` | partial status change | updated order | 400, 403, 404, 409 | reject immutable field edits |
```

Also include:
- one success response
- one validation error response
- one deprecation or versioning note
- one statement of retry / idempotency behavior

#### API Hard Questions
- What is the resource boundary?
- What is the source of truth?
- How do retries behave?
- What errors are safe to expose?
- What is the deprecation and migration window?

#### API Output Format
Use this exact structure for `design-api` responses:

```markdown
## API Problem Framing
## API Objective
## API Resource Model
## API Endpoint Catalog
## API Request / Response Examples
## API Error Model
## API Auth / Authorization Model
## API Versioning and Compatibility
## API Rejected Alternatives
## API Migration / Rollback Plan
## API Validation Plan
## API Confidence
```

#### API Red Flags / Reject These Moves
- deep nesting without a strong ownership reason
- action-heavy endpoints when resources would suffice
- undocumented idempotency for retry-prone writes
- versioning by habit instead of compatibility need
- generic `500`-style error handling without domain-specific error taxonomy

### 2. Database Design Playbook

#### What to Analyze
- entities, relationships, and lifecycle
- access patterns and query frequency
- read/write ratios
- consistency and transaction boundaries
- integrity constraints
- indexing strategy
- partitioning or sharding triggers
- retention and archival rules
- backup and restore expectations
- privacy, PII, and audit needs

#### Required Database Outputs
- entity or collection model
- relationship and cardinality map
- schema outline
- index plan tied to query patterns
- consistency model
- migration checkpoints
- backup and recovery notes
- operational risks

#### Schema Template
Use a structure like:

```text
Users
- id (PK / UUID)
- email (unique)
- status
- created_at

Orders
- id (PK / UUID)
- user_id (FK -> Users.id)
- total_amount
- status
- created_at
```

#### Database Design Rules
- Tie every index to a real query path.
- Call out intentional denormalization.
- Separate transactional truth from read-optimized projections.
- State foreign key and deletion behavior explicitly.
- Clarify strong vs eventual consistency boundaries.
- Include corruption, replay, or double-write risks for major changes.

#### Migration Requirements
For schema changes, specify:
- expand / migrate / contract sequence
- backfill strategy
- compatibility window
- rollback trigger
- rollback order

#### Database Worked Example
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  total_amount_cents BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_orders_user_created_at
  ON orders(user_id, created_at DESC);
```

#### Database Migration Example
Use expand / migrate / contract when a schema change is not backward compatible:
1. Expand: add nullable `billing_email` column and dual-write support.
2. Migrate: backfill from existing contact table and validate row counts.
3. Contract: switch reads to new column, remove old dependency after verification window.

#### Database Output Format
Use this exact structure for `design-database` responses:

```markdown
## Database Problem Framing
## Database Objective
## Entity and Relationship Model
## Schema Outline
## Query Paths and Index Plan
## Consistency and Transaction Boundaries
## Data Retention / Recovery Plan
## Database Rejected Alternatives
## Database Migration / Rollback Plan
## Database Validation Plan
## Database Confidence
```

#### Database Red Flags / Reject These Moves
- indexes without named query paths
- denormalization without explicit read or latency justification
- cross-service foreign keys without ownership clarity
- mixing transactional truth with analytics projections without saying so
- schema changes without compatibility window or backfill verification

### 3. Design Patterns Playbook

#### What to Analyze
- duplicated logic
- tight coupling
- unclear ownership
- poor testability
- object creation complexity
- leaky abstractions
- extension pressure
- global state and hidden dependencies

#### Required Pattern Outputs
- problem diagnosis
- candidate pattern fit matrix
- recommended pattern
- explicit anti-pattern warning if relevant
- before/after structure
- testability impact
- migration and replacement plan

#### Pattern Fit Matrix Template

```markdown
| Pattern | Fit | Why | Risks | Reject / Keep |
|---|---|---|---|---|
| Factory | High | Removes branching construction logic | Can hide ownership | Keep |
| Singleton | Low | Easy global access | Hidden coupling, test pain | Reject |
```

#### Pattern Selection Guidance
- Prefer composition over inheritance unless inheritance clearly simplifies the model.
- Prefer dependency inversion over hidden globals.
- Treat Singleton as suspicious by default.
- Use adapters and facades to isolate external or legacy interfaces.
- Use builders when construction complexity is real, not hypothetical.
- Separate pattern recommendation from refactor sequencing.

#### Refactor Recommendation Template
- current problem
- recommended boundary
- public interface
- implementation notes
- risks
- rollback path

#### Pattern Exemplars

**Factory over branching construction**
```javascript
// Before
if (type === "admin") return new AdminUser();
if (type === "guest") return new GuestUser();

// After
const builders = { admin: AdminUser, guest: GuestUser };
return new builders[type]();
```

**Adapter to isolate a third-party API**
```typescript
interface PaymentsGateway {
  charge(amountCents: number): Promise<string>;
}

class StripePaymentsGateway implements PaymentsGateway {
  async charge(amountCents: number): Promise<string> {
    return stripe.charge({ amount: amountCents });
  }
}
```

**Decorator for additive behavior**
```typescript
class BaseNotifier { send(message: string) {} }
class AuditNotifier {
  constructor(private inner: BaseNotifier) {}
  send(message: string) {
    audit.log(message);
    this.inner.send(message);
  }
}
```

**Reject this move**
- Do not default to Singleton for convenience when dependency injection or explicit ownership would keep testability and boundary clarity intact.

#### Pattern Review Output Format
Use this exact structure for `design-patterns` responses:

```markdown
## Pattern Problem Framing
## Pattern Objective
## Current Design Smells
## Pattern Fit Matrix
## Recommended Pattern and Boundary
## Before / After Structure
## Testing and Replaceability Impact
## Pattern Rejected Alternatives
## Pattern Migration / Rollback Plan
## Pattern Validation Plan
## Pattern Confidence
```

#### Pattern Red Flags / Reject These Moves
- Singleton as the default answer
- inheritance used to hide missing boundaries
- “plugin architecture” with no stable plugin contract
- abstractions introduced before any actual variation exists
- pattern recommendations that do not improve testability, replaceability, or ownership

### 4. System Design Playbook

#### What to Analyze
- functional requirements
- non-functional requirements
- traffic, concurrency, and growth estimates
- latency and throughput targets
- reliability and availability expectations
- consistency model
- storage and messaging requirements
- security boundaries
- observability requirements
- deployment and operational constraints

#### Required System Outputs
- high-level architecture
- component responsibility map
- request/read/write flow
- capacity assumptions
- state and storage strategy
- failure-domain analysis
- observability plan
- security boundaries
- rollout and rollback plan

#### System Component Template

```markdown
| Component | Responsibility | State | Scale Driver | Failure Mode | Owner |
|---|---|---|---|---|---|
| API Gateway | Auth, routing, quota enforcement | Stateless | RPS | Misrouting / auth failure | Platform |
```

#### Capacity Template
When scale matters, calculate at least:
- peak RPS or throughput
- storage growth
- cache working set
- queue depth expectations
- background job concurrency

Write the math explicitly when assumptions matter.

#### System Diagram Example
```text
Client -> CDN -> API Gateway -> Application Service
                             -> Cache
                             -> Primary DB
                             -> Queue -> Worker
                             -> Object Storage
```

#### Read Flow Example
```text
1. Client request reaches API Gateway
2. Service checks cache for document summary
3. On cache miss, service reads from primary read path
4. Response is returned and cached with TTL + invalidation rule
```

#### Write Flow Example
```text
1. Client submits document
2. API stores metadata row
3. Blob is written to object storage
4. Extraction job is published to queue
5. Worker processes document and updates search index
6. API returns accepted status with job identifier
```

#### Capacity Calculation Example
```text
Daily active users: 250,000
Requests per user per day: 24
Total requests/day: 6,000,000
Average RPS: 6,000,000 / 86,400 = 69.4
Peak multiplier: 4x
Peak RPS: ~278
```

#### System Design Rules
- Distinguish control plane from data plane when relevant.
- Call out stateful vs stateless components.
- Define failure domains and blast radius.
- State how the system degrades under load or dependency failure.
- Prefer simpler topologies unless constraints justify more moving parts.
- Wrap third-party or cloud dependencies behind stable internal interfaces.

#### System Design Output Format
Use this exact structure for `system-design` responses:

```markdown
## System Problem Framing
## System Objective
## Functional and Non-Functional Requirements
## Capacity Assumptions
## High-Level Architecture
## Component Responsibility Map
## Read Flow
## Write Flow
## Failure Domains and Degradation Strategy
## Security and Observability Boundaries
## System Rejected Alternatives
## System Migration / Rollback Plan
## System Validation Plan
## System Confidence
```

#### System Design Red Flags / Reject These Moves
- microservices without a clear scaling, ownership, or deployment reason
- asynchronous messaging introduced without delivery semantics or replay plan
- “high availability” claims without redundancy and failover mechanics
- caches added without invalidation policy
- capacity numbers stated without assumptions

## Artifact Templates

### `architecture/spec.md`
- one-page summary
- architecture diagram in text or Mermaid
- component table
- interface contract summary
- decision table

Example:

```markdown
# Architecture Spec
## Summary
## Diagram
## Components
## Interfaces
## Decisions
```

### `architecture/decision-log.md`
- decision
- chosen option
- rejected alternatives
- rationale
- impact
- owner

Example:

```markdown
# Decision Log
## Decision
Adopt header-based API versioning for external clients.
## Chosen Option
Version via `X-API-Version`.
## Rejected Alternatives
- URI versioning
- accept-header content negotiation
## Rationale
Avoid path churn while preserving explicit client control.
## Impact
Gateway, SDK, and contract tests require update.
## Owner
Platform API team
```

### `architecture/migration-plan.md`
- preconditions
- rollout sequence
- verification points
- rollback triggers
- rollback order
- communication or coordination notes

Example:

```markdown
# Migration Plan
## Preconditions
## Expand Phase
## Migrate Phase
## Contract Phase
## Verification Gates
## Rollback Triggers
## Rollback Order
```

### `architecture/validation-plan.md`
- acceptance criteria
- tests to run
- metrics to watch
- dashboards or logs to inspect
- success and failure thresholds

## Example Invocation Patterns

### API design
```text
/architecture design an internal billing API for invoices, payments, and credit notes. Include auth, pagination, error model, and versioning.
```

### Database design
```text
/architecture design the schema for a multi-tenant issue tracker. Include indexing, retention, and migration strategy.
```

### Pattern selection
```text
/architecture review this module layout and recommend patterns to reduce coupling and improve testability.
```

### System design
```text
/architecture design a document-processing system that ingests PDFs, extracts metadata, and serves searchable results with background jobs and audit trails.
```

## Hard Constraints
1. Never return an architecture recommendation without stating objective, scope, assumptions, and constraints.
2. Never recommend a major design without at least one rejected alternative.
3. Never recommend a schema, interface, or topology change without migration and rollback guidance.
4. Never hide uncertainty. Mark unknowns explicitly.
5. Never confuse module boundaries with deployment boundaries.
6. Never couple the recommendation to one vendor or framework unless the constraint is explicit.
7. Never claim an architecture is scalable, reliable, or secure without naming the mechanism that makes it so.
8. Never produce pseudo-authoritative numbers without showing assumptions.
9. Never optimize for novelty over maintainability.
10. Never omit validation steps for a meaningful change.

## Review Gate
Before finalizing, verify all of the following:
- Does each major recommendation say what problem it solves?
- Does each major recommendation say what it costs?
- Are failure modes named?
- Is rollback described?
- Are interfaces explicit enough that another engineer could implement from them?
- Are rejected alternatives concrete rather than generic?
- Are module responsibilities clear enough for ownership?
- Are observability and validation included where operational behavior changes?

## When to Refuse Confidence
Reduce confidence sharply or state that the recommendation is provisional when:
- scale, throughput, or workload shape is unknown for a system-design request
- consistency, isolation, or recovery expectations are unspecified for a database decision
- ownership boundaries are unclear between services, teams, or modules
- the user asks for a pattern recommendation without the current problem or pain being visible
- constraints conflict with each other and no priority order is given
- rollout risk is meaningful but no migration window or compatibility constraint is available

## Architecture Quality Scorecard
Score each criterion as `0`, `1`, or `2`.

- `Output Completeness`
- `Scope Discipline`
- `Technical Specificity`
- `Evidence Quality`
- `Failure-Aware Decisions`
- `Migration Clarity`
- `Benchmark Fit`

Pass rules:
- `Overall Score >= 9`
- `Failure-Aware Decisions` must not be `0`
- `Migration Clarity` must not be `0`
- `Benchmark Fit` must not be `0`

Include this block at the end of every substantive response:

```markdown
## Architecture Quality Scorecard
- Output Completeness: 0|1|2
- Scope Discipline: 0|1|2
- Technical Specificity: 0|1|2
- Evidence Quality: 0|1|2
- Failure-Aware Decisions: 0|1|2
- Migration Clarity: 0|1|2
- Benchmark Fit: 0|1|2
- Overall Score: 0-14
- Pass: true|false
- Rationale: short explanation for any weakness
```


Capability resource: `.codex/skills/architecture/resources/capability.json`
