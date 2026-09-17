# Security Responsibility Matrix — PM Query Library Architecture Exercise

Source: [Security Interface Contract](https://docs.appian-stratus.io/process-mining/new-arch/#security-interface-contract-lcp--pm-query-lib)

| Responsibility | Owner | Boundary/control | Evidence | Unresolved gap |
| --- | --- | --- | --- | --- |
| User authentication | LCP | Appian session cookie validated before PM code runs | Exemplar Security Interface Contract | None stated in exemplar |
| User authorization | LCP | `ProcessMiningGatingService.resolveAndGate(appianId)` checks access/role | Exemplar Security Interface Contract | Defense-in-depth check is recommended |
| `logUuid` resolution | LCP | Resolve user-facing `appianId`; do not trust user-supplied `logUuid` | Exemplar Security Interface Contract | Must preserve invariant in callers |
| Cross-process isolation | pm-query-lib + ADS | Scope table names with `{logUuid}__`; ADS applies namespace controls | Exemplar Security Interface Contract | Correct scoping remains a critical invariant |
| Cross-tenant isolation | Infrastructure / LCP / ADS | Per-site isolation and namespace/node boundaries | Exemplar Security Interface Contract | Deployment-specific proof is outside this exercise |
| SQL injection prevention | pm-query-lib + ADS | jOOQ DSL escaping plus ADS function blocklisting and AST validation | Exemplar Security Interface Contract | Exact runtime policy is not re-tested here |
| Input validation | pm-query-lib | Validate filters, attributes, ranges, aggregations before SQL generation | Exemplar Security Interface Contract | None stated in exemplar |
| Rate limiting / query complexity | LCP | Caller controls admission and timeouts | Exemplar Security Interface Contract | Thresholds are not specified in exemplar |
| Error message sanitization | LCP | Do not expose raw SQL/table names from library errors | Exemplar Security Interface Contract | Concrete response taxonomy not specified |
| Audit logging | LCP | Log who accessed which mining process | Exemplar Security Interface Contract | Event schema and retention are not specified |

The matrix assigns no responsibility that is absent from the source; gaps remain
visible rather than being converted into implementation claims.
