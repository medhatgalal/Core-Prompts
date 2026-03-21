# Core-Prompts / Capability Fabric

Capability Fabric is the capability-provider direction for Core-Prompts. It publishes reusable skills, agent surfaces, descriptors, and advisory handoff metadata. It does not own orchestration, runtime routing, or delegation.

## Fast Path
Use the repo wrappers first. They select a supported Python runtime automatically and keep the common flows consistent.

```bash
bin/uac --help
bin/capability-fabric --help
```

## What It Ships
- canonical SSOT prompts in `ssot/`
- machine-readable descriptors in `.meta/capabilities/`
- generated surfaces for Codex, Gemini, Claude, and Kiro
- advisory aggregate handoff in `.meta/capability-handoff.json`
- deterministic import and uplift through UAC

## Common Flows
```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
bin/capability-fabric build
bin/capability-fabric validate --strict
scripts/deploy-surfaces.sh --dry-run --cli all
scripts/install-local.sh --dry-run --target "$HOME" --allow-nonlocal-target
```

## Canonical Model
Capability types:
- `skill`
- `agent`
- `both`
- `manual_review`

Commands, plugins, powers, and extensions are deployment wrappers, not peer capability types.

Direct skill exposure is standardized on `skills/<slug>/SKILL.md` across Codex, Gemini, Claude, and Kiro. This repo no longer treats `commands/` or `prompts/` directories as direct deployment targets.

Canonical state:
- `ssot/<slug>.md`
- `.meta/capabilities/<slug>.json`
- `sources/ssot-baselines/<slug>/baseline.md`

Generated surfaces are derived artifacts under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`.

## Apply vs Deploy vs Package
- `apply`: mutates this repo only, rebuilds surfaces, and validates
- `deploy`: copies generated surfaces and bundled resources to a target root
- `install-local.sh`: convenience wrapper for home-targeted copy installs; still copy-only and still explicit
- `package`: produces release archives from the curated runtime/integration boundary

## Documentation
- [Docs hub](docs/README.md)
- [Getting started](docs/GETTING-STARTED.md)
- [CLI reference](docs/CLI-REFERENCE.md)
- [UAC usage](docs/UAC-USAGE.md)
- [Capability model](docs/UAC-CAPABILITY-MODEL.md)
- [Baseline source library](sources/ssot-baselines/README.md)
- [Orchestrator contract](docs/ORCHESTRATOR-CONTRACT.md)
- [Technical docs hub](docs/README_TECHNICAL.md)
- [Release packaging](docs/RELEASE-PACKAGING.md)
