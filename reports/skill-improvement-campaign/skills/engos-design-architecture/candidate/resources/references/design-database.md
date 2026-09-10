# Database design playbook

Use for relational/non-relational models, query/index design, transactions, consistency, retention and recovery. Start with domain invariants and access patterns, then choose storage mechanisms. Do not assume the example engine is the user's required database.

## Required database artifacts

- Entity/collection model, ownership, relationships/cardinality and lifecycle.
- Schema outline with keys, integrity/nullability and deletion behavior.
- Query-to-index mapping, read/write frequency assumptions and cost of extra indexes.
- Transaction/consistency boundaries, concurrency and failure behavior.
- Migration/backfill/compatibility gates, retention/privacy and backup/recovery notes.
- Operational risks and concrete validation scenarios.

### Schema and query plan template

| Entity | Key / tenant scope | Relationships / deletion | Integrity and lifecycle | Owner |
| --- | --- | --- | --- | --- |
| Document | Chosen key, tenant rule | Parent scope and delete behavior | Valid states, uniqueness and retention | Domain owner |

| Query | Filter/order and frequency | Proposed index / partition | Why it fits | Write/storage cost | Evidence needed |
| --- | --- | --- | --- | --- | --- |
| Tenant's recent documents | Tenant equality; time and ID tie-break | Key order matching access | Named query path | Measured later | Plan/cardinality on representative data |

Tie every index to a real query. Call out intentional denormalization, update/reconciliation cost and stale reads. Separate transactional truth from projections and analytics. Partition/shard only for an evidenced or explicitly hypothetical trigger.

## Integrity before happy-path SQL

State which invariants are enforced by keys/checks/foreign keys, transactions, application policy or another owner. Tenant-scoped relationships must preserve tenant identity at the boundary; authentication alone is insufficient. A pre-insert query for absence does not, by itself, enforce concurrent uniqueness. Describe enforcement and the conflict/retry contract. For SQL checks, account for nullability and the engine's constraint semantics. Avoid cross-service foreign keys that bypass ownership without justification.

Example of a tenant-scoped relationship in a relational outline:

```sql
CREATE TABLE documents (
  tenant_id UUID NOT NULL,
  document_id UUID NOT NULL,
  created_at TIMESTAMP NOT NULL,
  PRIMARY KEY (tenant_id, document_id)
);
CREATE TABLE annotations (
  tenant_id UUID NOT NULL,
  annotation_id UUID NOT NULL,
  document_id UUID NOT NULL,
  PRIMARY KEY (tenant_id, annotation_id),
  FOREIGN KEY (tenant_id, document_id)
    REFERENCES documents (tenant_id, document_id) ON DELETE RESTRICT
);
CREATE INDEX documents_recent
  ON documents (tenant_id, created_at DESC, document_id DESC);
```

This demonstrates relationship scope and a recent-document access path only. It is not a complete authorization, encryption, retention or production migration plan. Confirm timestamp/timezone and deletion policy for the actual use case.

## Transactions, consistency and recovery

Trace two concurrent operations that stress the important invariant. Name the isolation/locking/conditional-write mechanism and what happens on conflicts, deadlocks or serialization failures. Check actual engine behavior; do not assume that wrapping statements in a transaction makes arbitrary invariants serializable. Where an operation also emits an event, identify the atomic persistence boundary and duplicate/reconciliation strategy.

Specify stale-read tolerance, read-your-write needs and projection lag where relevant. Define recoverable state, RPO/RTO targets or unknowns, backup/restore scope, integrity verification and replay/duplicate handling. A replica is not by itself proof of recoverability. Retention and deletion must consider indexes/projections, caches, backups and replays without inventing a compliance guarantee.

## Migration under live traffic

Apply the shared expand/migrate/cutover/contract sequence. Include old/new readers and writers, source-of-truth changes, concurrency-safe backfill and reconciliation by invariant rather than row count alone. Identify lock/rewrite implications for the chosen engine/version and limits on batch size, lag, duration and abort. For PostgreSQL, a concurrent index build has specific transaction and failure behavior; an invalid index must be detected and handled. Do not call an operation zero-downtime just because its name says concurrent.

Before deleting a column or narrowing uniqueness, verify both consumer compatibility and whether new data can still be represented by the old model. If that cannot hold, give an explicit point after which roll-forward or restore/compensation replaces rollback. Proposed DDL is never executed by this skill.

## Reject or make provisional

Reject indexes without queries, application-only uniqueness under concurrency without a mechanism, undeclared tenant cross-links, unexplained denormalization, unverified backfills and impossible rollback claims. If workload, isolation, retention or recovery constraints are missing, mark the design provisional and prioritize the evidence that would settle the decision.

Sources checked 2026-09-10: [PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [isolation and transaction retries](https://www.postgresql.org/docs/18/transaction-iso.html), [concurrent index creation](https://www.postgresql.org/docs/18/sql-createindex.html). Use version-specific primary documentation for other engines.
