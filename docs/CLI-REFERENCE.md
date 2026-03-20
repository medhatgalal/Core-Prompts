# CLI Reference

This document defines generated surface paths, deploy behavior, and validation commands.

## Canonical Inputs
- SSOT: `ssot/`
- descriptors: `.meta/capabilities/`
- manifest: `.meta/manifest.json`
- handoff contract: `.meta/capability-handoff.json`
- persisted local source references inside canonical metadata and bundled `capability.json` resources must be repo-relative, not absolute machine paths

## Core Commands
```bash
python3 scripts/build-surfaces.py
python3 scripts/validate-surfaces.py --strict
python3 scripts/smoke-clis.py
scripts/deploy-surfaces.sh --dry-run --cli all
```

## Generated Surfaces
### Codex
- `.codex/skills/<slug>/SKILL.md`
- `.codex/skills/<slug>/resources/capability.json`
- `.codex/agents/<slug>.toml`
- `.codex/agents/resources/<slug>/capability.json`

### Gemini
- `.gemini/skills/<slug>/SKILL.md`
- `.gemini/skills/<slug>/resources/capability.json`
- `.gemini/agents/<slug>.md`
- `.gemini/agents/resources/<slug>/capability.json`

### Claude
- `.claude/skills/<slug>/SKILL.md`
- `.claude/skills/<slug>/resources/capability.json`
- `.claude/agents/<slug>.md`
- `.claude/agents/resources/<slug>/capability.json`

### Kiro
- `.kiro/skills/<slug>/SKILL.md`
- `.kiro/skills/<slug>/resources/capability.json`
- `.kiro/agents/<slug>.json`
- `.kiro/agents/resources/<slug>/capability.json`

## Deploy Contract
- `apply` mutates canonical repo state only
- `deploy` copies generated artifacts to a target root
- deployment is copy-only and never creates symlinks
- default target root is the repository root unless `--target` is provided
- install does not rewrite capability metadata paths; portability must already be correct in the built artifacts

## Smoke Checks
- version/help probes run for all configured CLIs
- filesystem checks verify expected generated surfaces per CLI
- discovery checks run only for discovery-backed surfaces:
  - Gemini skills
  - Claude agents
  - Kiro agents

## Related Docs
- [UAC usage](UAC-USAGE.md)
- [Release packaging](RELEASE-PACKAGING.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
