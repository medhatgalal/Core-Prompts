# Core-Prompts Surface Registry

This repository is the source-of-truth for CLI surface prompts/commands across Codex, Gemini, Claude, and Kiro.

## What this repo owns

- SSOT prompt definitions in `ssot/`
- Canonical generated outputs under:
  - `.codex/`
  - `.gemini/`
  - `.claude/`
  - `.kiro/`
- Validation and CI checks in `scripts/`

## Invocation map

- Gemini: slash commands via `/.gemini/commands`
- Claude: slash commands via `/.claude/commands`
- Kiro: prompts/agents in `/.kiro/prompts` and `/.kiro/agents`
- Codex: skills under `/.codex/skills`

The `clis/` folder is intentionally removed from this repo and not used as source-of-truth.

## Quick start

- List SSOT files: `ls ssot/*.md`
- Generate all surfaces: `python3 scripts/build-surfaces.py`
- Refresh schema references from vendor docs: `python3 scripts/sync-surface-specs.py`
- Validate outputs: `python3 scripts/validate-surfaces.py`
- Optional smoke checks: `python3 scripts/smoke-clis.py`

Recommended validation flow:

1. `python3 scripts/sync-surface-specs.py`
2. `python3 scripts/build-surfaces.py`
3. `python3 scripts/validate-surfaces.py --strict`
4. `python3 scripts/smoke-clis.py`

## One-file flow

1. Edit an SSOT source file in `ssot/`.
2. Run `python3 scripts/build-surfaces.py`.
3. Run `python3 scripts/validate-surfaces.py`.
4. Commit generated artifacts.

## Validation commands

- `python3 scripts/validate-surfaces.py --with-cli`  
  Runs CLI-backed artifact validation where declared.
- `python3 scripts/validate-surfaces.py --strict --with-cli`  
  Fails on optional checks and CLI artifacts validation issues.
- `python3 scripts/validate-surfaces.py --skip-schema`  
  Skips schema cache freshness checks when offline.

## Surfaces generated

For each SSOT file:

- `.codex/skills/<slug>/SKILL.md`
- `.gemini/commands/<slug>.toml`
- `.claude/commands/<slug>.md`
- `.kiro/prompts/<slug>.md`
- `.kiro/agents/<slug>.json`

See `.meta/manifest.json` for generated mapping.
