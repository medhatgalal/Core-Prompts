# Orchestrator Contract

This document teaches external orchestrators how to consume Capability Fabric outputs safely.

## Boundary
Capability Fabric/UAC publish:
- capabilities
- descriptors
- generated surfaces
- quality/evidence metadata
- advisory relationship and overlap hints

Capability Fabric/UAC do not publish:
- routing policy
- delegation order
- workflow execution policy
- SDLC control loops

## Canonical Read Order
1. `.meta/capability-handoff.json`
2. `.meta/capabilities/<slug>.json`
3. `ssot/<slug>.md` only when deeper prompt semantics are needed

## Canonical Capability Types
- `skill`
- `agent`
- `both`
- `manual_review`

Commands, plugins, powers, and extensions are deployment wrappers only.

## Fields to Consume
Use these fields as advisory metadata:
- `slug`
- `display_name`
- `capability_type`
- `summary`
- `role`
- `domain_tags`
- `required_inputs`
- `expected_outputs`
- `tool_policy`
- `install_target`
- `emitted_surfaces`
- `review_status`
- `confidence`
- `quality_status`
- `benchmark_profile`
- `preferred_use_cases`
- `artifact_conventions`
- `invocation_style`
- `requires_human_confirmation`
- `relationship_suggestions`
- `overlap_candidates`
- org-graph advisory fields

## Consumption Rules
- treat descriptors and handoff metadata as a capability directory
- use `relationship_suggestions` and `overlap_candidates` as hints, not routing instructions
- do not infer execution authority from wrapper presence alone
- do not infer orchestration authority from prompt richness alone
- keep runtime routing, delegation, and sequencing outside Capability Fabric/UAC

## Quality and Trust
- `quality_status=ship`: passed the current quality gate
- `quality_status=revise`: not ready for canonical landing
- `quality_status=manual_review`: do not auto-land or auto-trust
- `benchmark_profile`: tells you which bar or benchmark set was used
- `requires_human_confirmation=true`: keep a human approval gate before automated action

## Artifact Conventions
Use `artifact_conventions` as output-path hints only. They do not imply that Capability Fabric/UAC will execute the work itself.
