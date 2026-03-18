# Capability Fabric vNext Requirements

## Required
- UAC publishes layered manifests and never exposes orchestration decisions.
- Every import/plan/apply run performs anti-complecting analysis against current SSOT.
- UAC supports multiple sources in one run.
- Install scope is explicit: global, repo_local, or both.
- Apply remains non-mutating until explicit target confirmation exists.
- Handoff contract is machine-readable and advisory only.
- Architecture source assessments are recorded and preserved.

## Acceptance
- Single-source and multi-source runs emit manifest, cross-analysis, and handoff payloads.
- SSOT audit includes fit analysis.
- Existing build/validate/deploy flow remains green.
- Docs describe capability fabric, install scope, and wrapper surfaces clearly for humans and AI.
