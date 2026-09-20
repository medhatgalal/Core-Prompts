# Configuration deployment — Research

G1 passed before this artifact. Source identity: `engos-example-config-deployment/input.md`, all 36 lines opened. Evidence class throughout: teaching-fixture premise, never production observation (`input.md:3-4`). Decisions C1 and its constraints are unchanged. No runtime tests or spikes executed.

| Question | Disposition and answer | Opened evidence | Bound / mitigation |
| --- | --- | --- | --- |
| C-Q1 | answered: Importer checks deployment permission and base/current revision; target edits increment revision. Mismatch produces a visible no-write conflict unless authorized admin explicitly forces. | `input.md:16-21`, `input.md:11-12` | Preserve existing protection for cost definitions; force cannot become a default or authorization bypass. |
| C-Q2 | answered: CostConfigStore uses stable process UUID for currency/activity costs. Results/transactions are separate. Old packages omit the section; absence means leave unchanged, never delete. | `input.md:22-25` | Carry only scoped definitions with their identity; preserve absent-section semantics. |
| C-Q3 | answered: Existing transaction validates all included configuration before atomic commit; validation failure retains prior state. | `input.md:26-27` | Extend that contract to included costs; no partial update path. This is fixture support, not a concurrency or rollback test. |
| C-Q4 | answered: RunningAnalysis reads configuration at the start of its next scheduled run. No reload or historical recomputation is allowed. | `input.md:28-29` | Let the normal next run consume committed values; no deployment-triggered computation. |
| C-Q5 | answered for fixture scale: at most 100 × 200 = 20,000 activity entries. Proposed representation budgets one currency record per process: 100 more, totaling 20,100 cost records against the stated 25,000 configuration capacity. | `input.md:22`, `input.md:30-31` | 4,900 records remain for other included configuration; count the entire proposed import and reject over capacity before writes. No assumption that existing process metadata uses zero records. No throughput/latency claim. |
| C-Q6 | answered: Importer owns deployment-permission checks; existing encrypted deployment channel/authorization apply. Analysis library owns no deployment auth; target admin owns explicit force choice. | `input.md:11-12`, `input.md:16-21`, `input.md:32-33` | No new roles, credentials, transport or auth responsibility delegated to analysis. |

## Grounded risks and clearance

These are design hazards derived from fixture obligations; none is a discovered production defect. Clearance below is proposed future acceptance evidence, not completed tests.

| Risk | Basis | Mitigation / responsible fixture component or role | Clearance needed / stop boundary |
| --- | --- | --- | --- |
| R1 Local edit lost through stale import | Revision/conflict rule, `input.md:19-21` | PackageImporter retains guarded atomic application; target admin alone selects force | Stale-base example yields conflict and zero writes; authorized explicit force is separate; stop if protection cannot hold |
| R2 Old-package absence erases costs | Absence semantics, `input.md:24-25` | PackageImporter treats absent cost section as no cost change | Old package preserves target costs; stop any deletion-on-absence design |
| R3 Invalid cost or UUID association causes partial/wrong-process write | UUID store and atomic validation, `input.md:22`, `input.md:26-27` | PackageImporter validates included definitions and their association before commit | Invalid/ambiguous association or invalid included definition leaves all prior state; stop if all-or-nothing cannot be retained |
| R4 Work exceeds configuration capacity | Scale/capacity, `input.md:30-31` | PackageImporter counts total included configuration; PackageExporter bounds cost payload | Boundary examples for accepted total and rejected excess; stop rather than silently split the transaction or omit definitions |
| R5 Deployment accidentally broadens data/auth/analysis effects | Exclusions and timing/security, `input.md:10-12`, `input.md:23`, `input.md:28-33` | PackageExporter excludes results/transaction data; PackageImporter enforces authorization; RunningAnalysis retains schedule | Contract review and later checks show no new credentials, roles, reload or historical recomputation; stop on boundary violation |

## Research conclusion

All six questions are answered within fixture scope. Q5's record representation and reject-over-capacity policy are explicit author proposals using the supplied bound, not invented current behavior. The fixture provides enough existing boundary behavior to draft a contract-level extension; it supplies no actual API signatures, numeric cost validation rules, performance measurements or implementation proof. Do not invent them. Builders would bind the proposed semantic contracts to actual signatures and existing validation rules under separate implementation authority. No unresolved fixture dependency requires a spike for this teaching draft. G2 is awaiting the author gate observation in journal.md.
