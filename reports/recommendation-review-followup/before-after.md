# Recommendation review: before and after

This is a source-contract comparison between baseline `99c380b` and independently reviewed text. Apply, checks and mainline delivery are tracked separately in the PR/MR and check receipts. It does not claim observed behavior, better outcomes or measured savings. Exact original and candidate hashes, clause deltas and authority details are in [before-after.json](before-after.json).

| Skill / scoped route | Before | After | Preserved |
|---|---|---|---|
| `engos-audit-code-health` / `substantial_authored_artifact` | Author runs structural measurements, assembles report and checks metric/output rubric; no independent acceptance of the resulting substantial recommendation. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Target read-only and no test execution; language/exclude boundaries; metric thresholds; conservative dead-code confidence; prior finding remeasurement; drift logic; report frontmatter; scoped cruft preview/digest safeguards. |
| `engos-audit-feature-status` / `substantial_authored_artifact` | Human confirms extracted scope; author assesses statuses/gaps/priorities and final report rubric. Scope confirmation precedes analysis but does not independently accept the completed report. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Scope documents and human confirmation before proof collection; actual file/test-body evidence; OAS/HLD fidelity; completion states with no false greens; gaps and P0-P3 priorities; no implicit code or test execution. |
| `engos-audit-opex-incident-review` / `substantial_authored_artifact` | Author runs the Verification workflow before reporting success; its source/date/count/render checks are not a separate reviewer of the completed report. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Help no access; source query/pagination completeness; frozen snapshots and comparison R1-R8; incident drop-off and DPA obligations; postmortem-body evidence; attribution; count/date reconciliation; complete drill-down; renderer and explicitly authorized output/export boundaries. |
| `engos-audit-weekly-intel` / `substantial_authored_artifact` | Author fact-checks according to audience, generates report and checks internal consistency/confidence before delivery; no separate artifact acceptance participant. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Specified source/time coverage; source convergence; audience-specific fact-check branch; plain executive body and six appendices; source links/confidence; self-reported versus automated measures; body/appendix agreement; read-only source systems. |
| `engos-browser-demo-recorder` / `substantial_authored_artifact` | Author writes plan and complete script, provides execution guidance and judges runnable/narrative/auth/pacing/UI fit with the existing rubric; no separate artifact acceptance. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Complete plan/script without placeholders; feature/auth/URL scope; environment-only credential references; realistic pacing; video configuration; explicit prerequisites; no script execution/service startup/secret-store access; no test or deployment expansion. |
| `engos-content-dynamic-html-presentations` / `substantial_authored_artifact` | Author writes the deck, validates DOM and exports, reads it end-to-end as a presentation, then closes its Completion Checklist; no independent final artifact acceptance. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Output choice; narrative-first design; standalone or approved asset package; 16:9 target geometry; one active slide; interaction/accessibility; images/provenance/crops/load checks; requested-only PNG/PPTX chain; one rendering process; external upload approval; overwrite notice and portability/privacy boundaries. |
| `engos-delivery-resolve-conflict` / `substantial_authored_artifact` | Author compares both sides, resolves human decisions, writes recommendation/plan and checks preservation/logical structure/verification with its rubric; no separate final artifact reviewer. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Actual-conflict scope; inversion; preservation/explicit rejection; both-side content evidence; incompatibility and human decisions; logical order; concrete post-resolution verification; advisory companion boundaries and no hidden implementation authority. |
| `engos-design-plan-to-goal` / `substantial_authored_artifact` | Author drafts packet and verifier, fixes deterministic lint and synthetic-tree findings, seals and checks its own packet; independent no-goal-needed audit and verification-trust rules exist but do not independently accept authored packet semantics. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Research-first source/host preflight; exact bounded anchor/population exclusions; size/adapter limits; verifier trust; condition-present/absent flips; untouched/fake rejection; judge amendment disclosure; authorized durable storage; lint/seal/hash/drift checks; no implicit goal launch or implementation; execution budgets/terminal states intact. |
| `engos-quality-docs-review` / `explicit_documentation_execution` | For explicit execution, author edits documentation after source/placement analysis and assesses its own accuracy/IA rubric; findings-only inspection is external-artifact review and excluded. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Execution-only authored rewrite scope; one canonical home; audience/placement/source behavior/links; exact target scope; no broad rewrites or duplicate docs; source-of-truth and lifecycle review timing; advisory inspection remains independent findings-only work. |
| `engos-quality-testing-review` / `authored_test_plans_or_artifacts` | Author produces framework-aware test plan/set/gap recommendations then checks risk coverage/actionability with its rubric; source reading cannot independently accept its designed tests. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Authored plans/artifacts only; existing framework/layout; generation separated from execution; clear assertions; happy/error/boundary cases; risk priorities; no invented coverage metrics or silent test execution; readiness review belongs to separate route. |
| `engos-reconciliation-converge` / `substantial_authored_artifact` | Author compares sources, scores alternatives and writes one internally consistent final proposal; its own quality rubric checks final completeness without separate source-based artifact acceptance. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Actual source set/criteria; transparent alternative scores and sensitivity; conflict visibility; human taste/ownership/policy choices; no Frankenstein merge; final rationale and muted/rejected ideas; risks/next experiments; synthesis-only authority. |
| `loopy` / `craft_only` | Craft author interviews, designs a loop, privately traces one cycle and checks grounded design before compact delivery; independent verification is conditional on risk rather than required for every substantial crafted artifact. | Persistent coordinator/writer/separate reviewer; sourced current findings; zero-open exit; no review round cap; user-final reopened wontfix. | Exact original operating-body containment excluding package frontmatter; immutable intake package/provenance/license and resource bytes; same native identity with no alias; focused Craft interview; source-grounded unknowns; smallest feedback cycle; observable checks; bounded execution and no-progress/user stops; compact private-design output; separate run/publication authority; every non-Craft route unchanged. |

## Examples of the pattern

### `engos-audit-code-health`

One example of the pattern: a remediation report calls a public entrypoint dead although its source evidence shows dynamic callers. Previously the author checked its own classification; afterward a separate reviewer opens a sourced artifact defect and the same writer repairs the classification without editing target code.

### `engos-audit-feature-status`

One example of the pattern: a completed status omits a required error path shown in the supplied specification. Scope approval still happens first; afterward the reviewer checks the authored status against that source and keeps the repair open until the same writer corrects it.

### `engos-audit-opex-incident-review`

One example of the pattern: a digest counts a recovered old action link as new progress. Existing comparison rules still govern; the independent reviewer cites the prior/current source mismatch and requires a correction without changing the source system.

### `engos-audit-weekly-intel`

One example of the pattern: the body says a feature shipped while its appendix establishes only merged code. Existing audience formatting remains; the separate reviewer cites the actual evidence and the same writer narrows the claim.

### `engos-browser-demo-recorder`

One example of the pattern: a generated script selects a control absent from the supplied interface evidence. The reviewer opens a source-grounded defect and the same writer repairs the script; neither runs it or claims a recording was observed.

### `engos-content-dynamic-html-presentations`

One example of the pattern: a slide presents illustrative values as measured facts. Existing rendered-view checks remain prerequisites; the independent reviewer checks the source/label, and the same writer repairs the deck and affected exports.

### `engos-delivery-resolve-conflict`

One example of the pattern: a resolution plan silently drops one side's safety exception. The independent reviewer compares both original sides and the same writer restores or explicitly resolves it under the existing human-choice boundary.

### `engos-design-plan-to-goal`

One example of the pattern: a syntactically valid packet verifier checks a proxy instead of the stated outcome. Existing synthetic-tree and sealing checks remain; the reviewer checks the complete source-plan contract and the same writer repairs semantics plus affected deterministic evidence before readiness.

### `engos-quality-docs-review`

One example of the pattern: an explicitly requested documentation rewrite breaks a source-backed link. The writer owns the rewrite; the separate reviewer checks the saved artifact and source path. A findings-only docs review still receives no new authoring loop.

### `engos-quality-testing-review`

One example of the pattern: an authored retry test plan omits a duplicate-delivery branch visible in source. The reviewer cites it and the same writer repairs the plan. This acceptance proves neither test execution nor measured coverage.

### `engos-reconciliation-converge`

One example of the pattern: a final proposal claims a source supports an alternative it rejects. Existing comparison scores remain decision evidence; the reviewer checks source fidelity and the same writer repairs the proposal rather than treating its score as acceptance.

### `loopy`

One example of the pattern: a newly crafted loop assumes a daily schedule the user never supplied. The independent internal reviewer opens the unsupported assumption; the same writer repairs it using the source-grounding rule. The compact public prompt remains intact and no loop is executed.

## Preserved package and host boundaries

Canonical source is reviewed before UAC apply. Structural intake scores remain packaging evidence, separate from runtime artifact acceptance. Existing reports retain their domain findings and formats; reviewer defects are not a new target-domain report. Current descriptors express the scoped artifact contract only, and their intake-only tool policy grants no runtime authority.

The existing generator preserves curated expanded descriptor fields (scripts/build-surfaces.py, resolve_descriptor); these twelve slugs have no scorecard override. No generator or global default-quality-profile change is needed. No out-of-scope skill gains the loop.

The local Craft extension changes only canonical wrapper precedence and adds independent internal artifact acceptance. The complete original operating body, excluding package frontmatter, remains contained byte-for-byte within the candidate body. The full immutable intake source file and pinned companion resources remain unchanged, along with provenance, license, native identity and installed ownership.

Excluded existing review protocols, host identity/path/capped returns, narrow routes and external write/approval gates remain unchanged. No release, version change, installation or application behavior is included.
