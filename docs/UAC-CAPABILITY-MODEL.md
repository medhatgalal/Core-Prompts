# UAC Capability Model

UAC recommends packaging for imported sources and preserves explicit canonical declarations. Classification does not establish runtime benefit. The canonical policy lives in [surface rules](../.meta/surface-rules.json).

## Template-Backed Landing Rule
Before `apply` lands a new or uplifted capability, UAC must judge it against:
- a capability template from `.meta/capability-templates/`
- the active quality profile from `.meta/quality-profiles/`
- the current benchmark bar represented by strong local capabilities such as `engos-design-architecture`, `engos-quality-code-review`, `engos-quality-testing-review`, and `engos-meta-uac-import`

The goal is to prevent weak SSOT bodies from landing with strong metadata or overly broad emitted surfaces.

## Baseline Source Library
Prompt-body fidelity baselines must be maintained as repo-resident source artifacts under `sources/ssot-baselines/`, not selected operationally by git SHA.

Required behavior:
- `sources/ssot-baselines/index.json` is the canonical baseline catalog
- `sources/ssot-baselines/<slug>/baseline.md` is the canonical prompt-body fidelity oracle for that capability
- historical commit SHAs may appear only as lineage evidence in `historical_proof`
- `judge` and `apply` must resolve baseline source files first, so workspace copies without `.git` still have deterministic fidelity oracles
- a new behavioral baseline may be materialized only after an independent promotion verdict; structurally ready advisory applies remain `behavioral_pending` and preserve historical baseline lineage

## Canonical Capability Types
| Type | Meaning | Auto-deployable |
| --- | --- | --- |
| `skill` | reusable prompt/workflow with bounded outputs | yes |
| `agent` | explicitly declared native worker configuration | only with reviewed execution need for new emission |
| `both` | one canonical source with a skill and optional native execution adapters | only with reviewed execution need for new agent emission |
| `manual_review` | conflicting or weakly structured content | no |

## Skill-first classification

Reusable workflow content defaults to `skill`. Headings such as Mission and Responsibilities, quoted agent examples, and requests for independent reviewers do not establish a need for a named agent. Undeclared native-agent configuration requires packaging review. Existing explicit declarations retain their surfaces.

New or expanded agent emission uses the existing hash-bound `UACRequirementReview.v1` record. Its optional `agent_execution_needs` list identifies each added provider, the necessary `execution_need`, `why_generic_worker_insufficient`, and an exact `candidate_excerpt`. The review must satisfy the existing independent-review and source/candidate/effective-content bindings. This records reviewed intent, not authenticated reviewer identity or behavioral superiority. UAC apply enforces this admission even when its general quality loop is disabled. Generation and validation also check additions before publishing surfaces, using Git release history or the validated installer catalog's latest pinned release. The current generated manifest cannot authorize its own expansion. Persisted reviews contain hashes and scoped attestations, not original source snapshots; build checks final content binding without claiming to replay original-source fidelity.

Adding a missing declaration to an otherwise unchanged released source is a narrow preservation operation: the body and other fields must match the verified released source and the complete emitted surface set must remain identical. UAC records `preserved_existing_contract`, not a newly passing agent template or behavioral promotion. Content, configuration, or surface changes use the normal quality gates.

## Not Capability Types
These are deployment wrappers, not peer capability classes:
- commands
- plugins
- powers
- extensions

## Manifest Layers
### Minimal
- `capability_type`
- `summary`
- `role`
- `domain_tags`
- `required_inputs`
- `expected_outputs`
- `tool_policy`
- `resources`
- `packaging_profile`
- `install_target`
- `emitted_surfaces`
- `source_provenance`
- `confidence`
- `rationale`
- `review_status`
- `display_name`

For repo-local SSOT capabilities, persisted `resources` and `source_provenance.normalized_source` must use repo-relative paths such as `ssot/engos-design-architecture.md`. Canonical metadata and bundled capability resources must not persist machine-specific absolute filesystem paths.

### Expanded
- `relationship_suggestions`
- `capability_dependencies`
- `overlap_candidates`
- `migration_notes`
- `adjustment_recommendations`

### Org Graph
- `org_role`
- `reports_to_suggestions`
- `delegates_to_suggestions`
- `collaborates_with_suggestions`
- `authority_tier`
- `work_graph_impact`

All expanded and org-graph fields are advisory only.

## Quality Metadata
Descriptor and handoff metadata may also publish:
- `quality_profile`
- `quality_status`
- `judge_reports`
- `quality_scorecard`
- `quality_pass_count`
- `quality_stop_reason`
- `historical_baseline`
- `quality_validation_matrix`
- `consumption_hints`

These fields describe trust, fit, and usage guidance. They do not grant execution authority.

## Benchmark Readiness
The quality loop must score whether a candidate is structurally ready to land. The benchmark scorecard evaluates:
- title clarity
- description richness
- intent coverage
- boundary clarity
- output specificity
- metadata completeness
- surface usability

If a candidate fails the benchmark-readiness gate, `apply` must refuse landing until the SSOT body or template fit is improved.

## Install Target
Supported scopes:
- `global`
- `repo_local`
- `both`

`apply` requires explicit confirmation before writing canonical repo state.

## Related Docs
- [UAC usage](UAC-USAGE.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
