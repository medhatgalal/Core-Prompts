# Core-Prompts / Capability Fabric

Capability Fabric is the capability-provider direction for Core-Prompts. It publishes reusable skills, agent surfaces, descriptors, and advisory handoff metadata. It does not own orchestration, runtime routing, or delegation.

## What It Ships
- canonical SSOT prompts in `ssot/`
- machine-readable descriptors in `.meta/capabilities/`
- generated surfaces for Codex, Gemini, Claude, and Kiro
- advisory aggregate handoff in `.meta/capability-handoff.json`
- deterministic import and uplift through UAC

## Primary Entry Points
```bash
bin/uac --help
bin/capability-fabric --help
```

Common flows:
```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
bin/capability-fabric build
bin/capability-fabric validate --strict
scripts/deploy-surfaces.sh --dry-run --cli all
```

## Canonical Model
Capability types:
- `skill`
- `agent`
- `both`
- `manual_review`

Commands, plugins, powers, and extensions are deployment wrappers, not peer capability types.

Canonical state:
- `ssot/<slug>.md`
- `.meta/capabilities/<slug>.json`

Generated surfaces are derived artifacts under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`.

## Apply vs Deploy vs Package
- `apply`: mutates this repo only, rebuilds surfaces, and validates
- `deploy`: copies generated surfaces and bundled resources to a target root
- `package`: produces release archives from the curated runtime/integration boundary

## Documentation
- [Docs hub](docs/README.md)
- [Getting started](docs/GETTING-STARTED.md)
- [UAC usage](docs/UAC-USAGE.md)
- [Capability model](docs/UAC-CAPABILITY-MODEL.md)
- [Orchestrator contract](docs/ORCHESTRATOR-CONTRACT.md)
- [CLI reference](docs/CLI-REFERENCE.md)
- [Release packaging](docs/RELEASE-PACKAGING.md)
