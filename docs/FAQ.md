# FAQ

## What should I edit when I want behavior changes?
Edit `ssot/`. Generated surfaces and most descriptor details are derived.

## What is the difference between `apply`, `deploy`, and `package`?
- `apply`: writes canonical repo state and rebuilds surfaces
- `deploy`: copies generated surfaces to a target root
- `package`: creates release archives from the curated runtime/integration boundary

## What does `judge` do?
`judge` runs the quality loop without landing canonical repo state. It is the safest way to see whether a candidate is ready for `apply`.

## Do I need all CLI binaries installed?
No. They are only required for local smoke checks and target-specific deploy validation.

## Where should a future orchestrator start?
Read [ORCHESTRATOR-CONTRACT.md](ORCHESTRATOR-CONTRACT.md), then `.meta/capability-handoff.json`, then the per-capability descriptor files.

## Does Capability Fabric decide which capability should run?
No. Capability Fabric/UAC publish advisory metadata only. Routing and delegation stay outside.
