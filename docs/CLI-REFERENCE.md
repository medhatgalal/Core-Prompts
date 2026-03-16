# CLI Integration Reference

This document defines the generated surfaces, resource bundling, deployment behavior, verification commands, and required runtime settings for each supported CLI.

## Local References
- Surface rules: `.meta/surface-rules.json`
- Generated mapping: `.meta/manifest.json`
- Capability descriptors: `.meta/capabilities/`
- Advisory handoff contract: `.meta/capability-handoff.json`
- Build: `scripts/build-surfaces.py`
- Validate: `scripts/validate-surfaces.py`
- Deploy (copy-only): `scripts/deploy-surfaces.sh`
- Shell wrappers: `bin/uac`, `bin/capability-fabric`

## Deployment Contract
- `apply` mutates repo-local canonical sources only
- `deploy` copies generated surfaces plus bundled resources into CLI home directories
- deployment never classifies sources or mutates SSOT
- deployment remains copy-only and never creates symlinks

## Generated Surfaces By CLI

### Gemini
Source paths:
- `.gemini/commands/<slug>.toml`
- `.gemini/skills/<slug>/SKILL.md`
- `.gemini/skills/<slug>/resources/capability.json`
- `.gemini/agents/<slug>.md`
- `.gemini/agents/resources/<slug>/capability.json`

Commands stay thin. Skills and agents reference bundled descriptor resources.

### Claude
Source paths:
- `.claude/commands/<slug>.md`
- `.claude/agents/<slug>.md`
- `.claude/agents/resources/<slug>/capability.json`

Commands stay thin. Agent files reference bundled descriptor resources.

### Kiro
Source paths:
- `.kiro/prompts/<slug>.md`
- `.kiro/skills/<slug>/SKILL.md`
- `.kiro/skills/<slug>/resources/capability.json`
- `.kiro/agents/<slug>.json`
- `.kiro/agents/resources/<slug>/capability.json`

Canonical generated Kiro resource URIs:
- `file://.kiro/prompts/<slug>.md`
- `skill://.kiro/skills/<slug>/SKILL.md`
- `file://.kiro/agents/resources/<slug>/capability.json`
- `file://.kiro/skills/<slug>/resources/capability.json`

### Codex
Source paths:
- `.codex/skills/<slug>/SKILL.md`
- `.codex/skills/<slug>/resources/capability.json`
- `.codex/agents/<slug>.toml`
- `.codex/agents/resources/<slug>/capability.json`

Codex skills remain the primary reusable surface. Agent registrations stay thin and reference bundled descriptor resources.

## UAC Surface
Primary intake surface:
- `uac-import`

Capability model:
- `skill`
- `agent`
- `both`
- `manual_review`

Shell modes:
- `import`
- `audit`
- `explain`
- `plan`
- `apply`

Install target model:
- `--install-target auto|global|repo_local|both`
- `apply` still requires confirmation unless `--yes` is supplied

Important boundary:
- Capability Fabric/UAC publish manifests, descriptors, and advisory handoff only
- orchestration, routing, and delegation remain external concerns

## Validation and Release Flow
1. `bin/capability-fabric build`
2. `bin/capability-fabric validate --strict`
3. `scripts/smoke-clis.py` when local CLIs are installed
4. `scripts/deploy-surfaces.sh --dry-run --cli all --target "$HOME/tmp/llm-home"`
5. `scripts/package-surfaces.sh --version vX.Y.Z`
