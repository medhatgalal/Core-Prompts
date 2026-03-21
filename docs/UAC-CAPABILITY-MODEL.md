# UAC Capability Model

UAC is the authoritative classifier for imported sources and SSOT entries.

## Template-Backed Landing Rule
Before `apply` lands a new or uplifted capability, UAC must judge it against:
- a capability template from `.meta/capability-templates/`
- the active quality profile from `.meta/quality-profiles/`
- the current benchmark bar represented by strong local capabilities such as `architecture`, `code-review`, `testing`, and `uac-import`

The goal is to prevent weak SSOT bodies from landing with strong metadata or overly broad emitted surfaces.

## Baseline Source Library
Prompt-body fidelity baselines must be maintained as repo-resident source artifacts under `sources/ssot-baselines/`, not selected operationally by git SHA.

Required behavior:
- `sources/ssot-baselines/index.json` is the canonical baseline catalog
- `sources/ssot-baselines/<slug>/baseline.md` is the canonical prompt-body fidelity oracle for that capability
- historical commit SHAs may appear only as lineage evidence in `historical_proof`
- `judge` and `apply` must resolve baseline source files first, so workspace copies without `.git` still have deterministic fidelity oracles
- new capabilities landed through UAC should materialize a baseline source snapshot before or during `apply`

## Canonical Capability Types
| Type | Meaning | Auto-deployable |
| --- | --- | --- |
| `skill` | reusable prompt/workflow with bounded outputs | yes |
| `agent` | delegated specialist with explicit agent semantics | yes |
| `both` | one canonical source that emits workflow and agent surfaces | yes |
| `manual_review` | conflicting or weakly structured content | no |

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

For repo-local SSOT capabilities, persisted `resources` and `source_provenance.normalized_source` must use repo-relative paths such as `ssot/architecture.md`. Canonical metadata and bundled capability resources must not persist machine-specific absolute filesystem paths.

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
