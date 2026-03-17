# UAC Capability Model

UAC is the authoritative classifier for imported sources and SSOT entries.

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
- `quality_pass_count`
- `quality_stop_reason`
- `consumption_hints`

These fields describe trust, fit, and usage guidance. They do not grant execution authority.

## Install Target
Supported scopes:
- `global`
- `repo_local`
- `both`

`apply` requires explicit confirmation before writing canonical repo state.

## Related Docs
- [UAC usage](UAC-USAGE.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
