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
3. In a source checkout, `ssot/<slug>.md` when deeper semantics are needed.
   In an extracted distribution, read the selected provider's bundled
   `skills/<slug>/SKILL.md` and its selected package-local resources instead;
   distributions omit canonical SSOT. An installed standalone package can use
   its `SKILL.md` and `resources/capability.json` when aggregate metadata is absent.

## Selecting from the user's prompt

The host can use the [skill flows](SKILL-FLOWS.md) and
[job map](SKILL-JOB-MAP.md) to identify the requested outcome, existing accepted
work, material uncertainty and allowed scope. Choose the first missing job:
diagnosis for an unexplained failure, specification for unclear behavior,
architecture for a material design decision, planning for a useful breakdown,
or implementation for a clear authorized change. Review-only requests end in
findings. Small changes can bypass planning; Batman requires explicit selection.

These are selection aids for the external router, not installed routing policy.
No universal automatic Core-first router, organization model or replacement harness
is installed. A copyable onboarding request in README is user guidance, not a
new global routing rule. Load the smallest relevant skill and selected resources;
retain the host's permissions, delegation constraints and project-local rules.
If a material ambiguity changes the route or authority, a concise clarification
is needed; otherwise the smallest sufficient route can proceed. Skill discovery
depends on the host. Explicitly loading the exact available skill and resources
is the documented fallback, not proof of native discovery or permission to act.

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
- `quality_status=structural_ready`: passed deterministic UAC gates; this is not behavioral promotion
- legacy `quality_status=ship`: historical structural evidence only; consumers must not reinterpret it as behavioral proof
- `quality_status=revise`: not ready for canonical landing
- `quality_status=manual_review`: do not auto-land or auto-trust
- `benchmark_profile`: tells you which bar or benchmark set was used
- `requires_human_confirmation=true`: keep a human approval gate before automated action

## Artifact Conventions
Use `artifact_conventions` as output-path hints only. They do not imply that Capability Fabric/UAC will execute the work itself.
