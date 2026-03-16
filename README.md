# Core-Prompts / Capability Fabric

Better prompts, better outcomes, with deterministic capability publishing.

Core-Prompts is evolving into Capability Fabric: a capability-provider layer for prompt workflows, skill surfaces, agent surfaces, and importable external prompt families. It classifies and packages capabilities, but it does not orchestrate them.

## What It Does
- publish reusable skills, commands, prompts, and agent surfaces from canonical SSOT
- import external files, folders, repos, and URLs through deterministic UAC analysis
- write canonical repo state as:
  - `ssot/<slug>.md`
  - `.meta/capabilities/<slug>.json`
- generate thin vendor surfaces with bundled descriptor resources
- validate the generated outputs before deployment
- publish an advisory handoff contract for future orchestrators

## Primary Shell Entry Points
```bash
bin/uac --help
bin/capability-fabric --help
```

### Common flows
```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac apply /absolute/path/to/family-folder --yes
bin/uac audit --output table
bin/capability-fabric build
bin/capability-fabric validate --strict
```

## Capability Model
UAC classifies each source as:
- `skill`
- `agent`
- `both`
- `manual_review`

Commands, plugins, powers, and extensions are deployment wrappers, not peer capability types.

## Apply vs Deploy
- `apply` mutates this repo only:
  - writes SSOT markdown
  - writes descriptor JSON
  - rebuilds surfaces
  - validates
- `deploy` is separate:
  - copies generated surfaces and bundled resources into CLI home directories

## Current Direction
- product direction: `Capability Fabric`
- subsystem: `UAC`
- next pilot families: `architecture` and `testing`

## Docs
- [Capability Fabric overview](docs/CAPABILITY-FABRIC.md)
- [UAC usage guide](docs/UAC-USAGE.md)
- [CLI integration reference](docs/CLI-REFERENCE.md)
- [Architecture source assessment](docs/ARCHITECTURE-SOURCE-ASSESSMENT.md)
