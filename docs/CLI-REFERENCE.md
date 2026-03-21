# CLI Reference

This document defines generated surface paths, deploy behavior, and validation commands.

Preferred active runtime: Python `3.14`.
Minimum supported runtime: Python `3.11+`.
Prefer the repo wrappers when possible:
- `bin/capability-fabric` for build, validate, and deploy
- `bin/uac` for import, plan, judge, and apply

If local `python3` resolves to an older interpreter, set `PYTHON_BIN=python3.11` or `PYTHON_BIN=python3.14` before using the wrappers.

## Canonical Inputs
- SSOT: `ssot/`
- descriptors: `.meta/capabilities/`
- manifest: `.meta/manifest.json`
- handoff contract: `.meta/capability-handoff.json`
- persisted local source references inside canonical metadata and bundled `capability.json` resources must be repo-relative, not absolute machine paths
- every SSOT entry must satisfy the canonical contract sections enforced by validation: purpose, primary objective, workflow contract, boundaries, invocation hints, required inputs, required output, examples, and an evaluation rubric or scorecard-equivalent

## Core Commands
```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
bin/capability-fabric deploy --dry-run --cli all
```

## Direct Surface Standard
Direct skill surfaces are standardized on `skills/<slug>/SKILL.md` for every supported CLI. This repo no longer deploys direct exposure into `commands/` or `prompts/` directories.

## Generated Surfaces
| CLI | Direct skill surface | Bundled skill resource | Agent surface | Bundled agent resource |
| --- | --- | --- | --- | --- |
| Codex | `.codex/skills/<slug>/SKILL.md` | `.codex/skills/<slug>/resources/capability.json` | `.codex/agents/<slug>.toml` | `.codex/agents/resources/<slug>/capability.json` |
| Gemini | `.gemini/skills/<slug>/SKILL.md` | `.gemini/skills/<slug>/resources/capability.json` | `.gemini/agents/<slug>.md` | `.gemini/agents/resources/<slug>/capability.json` |
| Claude | `.claude/skills/<slug>/SKILL.md` | `.claude/skills/<slug>/resources/capability.json` | `.claude/agents/<slug>.md` | `.claude/agents/resources/<slug>/capability.json` |
| Kiro | `.kiro/skills/<slug>/SKILL.md` | `.kiro/skills/<slug>/resources/capability.json` | `.kiro/agents/<slug>.json` | `.kiro/agents/resources/<slug>/capability.json` |

## Deploy Contract
- `apply` mutates canonical repo state only
- `deploy` copies generated artifacts to a target root
- deployment is copy-only and never creates symlinks
- default target root is the repository root unless `--target` is provided
- install does not rewrite capability metadata paths; portability must already be correct in the built artifacts
- `install-local.sh` is a compatibility wrapper around deploy and remains copy-only

## Smoke Checks
- version/help probes run for all configured CLIs
- filesystem checks verify expected generated surfaces per CLI
- discovery checks run only for discovery-backed surfaces:
  - Gemini skills
  - Claude agents
  - Kiro agents

## Related Docs
- [Getting started](GETTING-STARTED.md)
- [UAC usage](UAC-USAGE.md)
- [Release packaging](RELEASE-PACKAGING.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
