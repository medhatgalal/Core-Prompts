# Capability Fabric vNext Handoff

## Current Shape
- Layered manifest module exists
- Cross-analysis exists
- UAC shell emits manifest, cross-analysis, handoff payloads
- Apply is implemented and repo-mutating with explicit confirmation
- Canonical landing now writes `ssot/<slug>.md` plus `.meta/capabilities/<slug>.json`
- Build bundles descriptor resources into generated skill and agent surfaces

## Resume Priorities
1. Run the full validation suite after each apply/build change
2. Inspect generated `.meta/manifest.json` and `.meta/capability-handoff.json`
3. Confirm docs and shell help reflect the repo-mutating apply flow
4. Review whether surface rules need additional machine-readable wrapper metadata

## Critical Boundary
Capability Fabric/UAC publish advisory metadata only. Any drift into orchestration or runtime delegation is a bug.
