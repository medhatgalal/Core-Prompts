# Capability Fabric vNext Handoff

## Current Shape
- Layered manifest module exists
- Cross-analysis exists
- UAC shell emits manifest, cross-analysis, handoff payloads
- Apply remains planned-only and non-mutating

## Resume Priorities
1. Run the full validation suite
2. Inspect generated `.meta/manifest.json` and `.meta/capability-handoff.json`
3. Confirm docs and shell help reflect the new boundary
4. Review whether surface rules need additional machine-readable wrapper metadata

## Critical Boundary
Capability Fabric/UAC publish advisory metadata only. Any drift into orchestration or runtime delegation is a bug.
