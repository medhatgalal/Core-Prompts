# System design playbook

Use for topology, storage/messaging/caching, scale, availability and operational boundaries. Integrate API and database guidance when the decision crosses those contracts. Start from functional requirements, critical user journeys and constraints, not a default gateway/cache/queue diagram.

## Required system artifacts

- Requirements and workload assumptions, including units and growth uncertainty.
- Context/topology and component responsibility/state/owner map.
- Read/write flow with acknowledgment, persistence and external effect boundaries.
- Capacity and bottleneck model, failure-domain analysis and overload behavior.
- Consistency, storage/messaging/cache lifecycle, security and observability.
- Rollout/rollback/recovery plan and validation criteria.

### System Component Template

| Component | Responsibility / interface | Authoritative state | Scale driver / limit | Failure / degradation | Owner |
| --- | --- | --- | --- | --- | --- |
| Ingest / worker / storage | Name only needed components | Truth or projection | Workload and resource | Detection, containment, recovery | Known or to confirm |

Show control plane versus data plane when relevant. Distinguish logical modules, processes and failure domains. A multi-zone label does not prove failover or independent dependencies. Identify availability/consistency tradeoffs and operator capacity rather than assuming more distributed components improve reliability.

## Capacity as an argument

When scale drives a decision calculate relevant throughput, storage growth, concurrency, backlog, cache working set and job demand. State inputs, units, peak shape, headroom, resource bottleneck and measurements needed. Do not calculate irrelevant quantities simply to fill a template.

Example, under explicit synthetic assumptions: input rate 120 jobs/s, 12 workers, mean service time 0.2 s/job gives nominal capacity 12 / 0.2 = 60 jobs/s. Over a 300-second sustained burst, backlog grows approximately (120 - 60) × 300 = 18,000 jobs. With later input 20 jobs/s, nominal drain time is 18,000 / (60 - 20) = 450 seconds. Retries, service-time variation, scheduling and downstream limits can worsen this estimate. Mean capacity is not proof of a tail-latency or completion SLO.

Define queue depth/age limits, per-tenant fairness, admission limits, degradation/load shedding and overload recovery. Scaling proposals must respect downstream connection/IO/API quotas and startup delay. Explain who rejects work and what clients observe. A queue absorbs a bounded burst; it does not fix a sustained arrival rate above service capacity.

## State and failure paths

For each important write, locate the durable commit and acknowledgment. If database state, object storage and event publication are separate effects, give intermediate states, cleanup/reconciliation and a durable retry mechanism. An outbox or CDC can address a database/event dual-write seam; it does not make arbitrary external effects atomic. Consumers still need a duplicate/replay/ordering policy. Scope any exactly-once claim to its actual mechanism and limits.

Trace crash before/after commit, duplicate/out-of-order messages, dependency timeout, poison input, overload and replay after deletion where relevant. Specify bounded retry/backoff, dead-letter/quarantine ownership, observability and a repair path. Protect against retries multiplying across layers. Distinguish temporary failure, permanent rejection and unknown outcome.

For caches, define source of truth, freshness, invalidation/TTL, capacity/eviction and recovery after loss. For projections, define lag target, rebuild/replay scope, reconciliation and schema evolution. Deletion/retention must propagate safely to copies and replays; identify unresolved retention policy rather than inventing legal requirements.

## Reliability and security

Define user-visible SLIs with measurement location, numerator/denominator or latency threshold, time window and target supplied or proposed. Identify where a metric misses failed requests. For recovery give RPO/RTO objectives or unknowns and the failure scenario they apply to. Name redundancy, failover detection, fencing/state ownership and restore verification where these support the recommendation.

Map trust boundaries, authentication/authorization, tenant isolation, secret/data handling and audit access to mechanisms. Keep observability useful without exposing sensitive payloads. Name the operator/team or the ownership gap for alerts, replay, backups and degraded operation. Compare complexity to team staffing and on-call constraints.

## Validation and evolution

Use a compact sequence or state table for the riskiest flow. Specify load/fault/recovery tests and concrete observations as proposed checks; do not claim they ran. Stage rollout with compatibility and data gates, bounded exposure, abort triggers and ordered recovery. Preserve old/new event and storage compatibility across rollback windows.

Reject unsupported high-availability claims, unexplained microservices, unbounded queues/retries, unowned state, caches without lifecycle, and arithmetic that conflicts with targets. If targets cannot be met under fixed limits, show the conflict and choices; do not silently relax a constraint.

Sources checked 2026-09-10: [Google SRE overload](https://sre.google/sre-book/handling-overload/), [SLO implementation](https://sre.google/workbook/implementing-slos/), [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html). These support mechanisms and questions, not local reliability or performance claims.
