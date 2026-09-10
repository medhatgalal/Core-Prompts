# Public Architecture controls

Seventeen author-visible synthetic tasks cover four modes, mixed service split, missing evidence, routing/authority, parameter/constraint variants and an ordinary artifact-producing catalog design. They are not held-out validation. Expectations are in `../public-expectations.json`; keep them out of candidate runtime input.

SYS-01 deliberately repeats the guide’s worked arithmetic and PAT-01/DB-01 closely resemble teaching examples. Keep them as instructional controls, never transfer evidence. SYS-03 changes workload and queue/latency constraints; SYS-04 is feasible and favors retaining a simple system. PAT-03 and DB-03 change domain/constraints. ART-01 supplies actual SQL/API/requirements files and requests OpenAPI plus a decision record. Candidate producers receive only their task and declared context_files, not all cases/expectations.

Structured JSON workload data is the numeric authority for SYS-01/03/04 and is loaded by the checker; arithmetic is calculated from those fields. `uniqueness_scenario.json` is an explicit finite old/new compatibility witness. These are illustrative public oracle calculations, not model output scoring or proof of SQL engine behavior. The checker rejects altered numbers that disagree with public expected outcomes, but semantic prompt/expectation drift still needs review.

`service_split_request.md` remains a newly authored replacement proposal for the absent AR-PUB-001 input; it does not reconstruct historical bytes or alter original evals. RPC, webhook and event-contract breadth remains unmeasured; these new cases do not close it.
