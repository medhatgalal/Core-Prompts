# Core-Prompts Surface Registry

This repository is the source-of-truth for SSOT-driven prompt/skill/agent surfaces across Codex, Gemini, Claude, and Kiro.

## What this repo owns

- SSOT prompt definitions in `ssot/`
- Canonical generated outputs under:
  - `.codex/`
  - `.gemini/`
  - `.claude/`
  - `.kiro/`
- Validation and CI checks in `scripts/`

## Invocation map

- Gemini:
  - skills via `.gemini/skills/<slug>/SKILL.md`
  - custom commands via `.gemini/commands/<slug>.toml`
  - subagents via `.gemini/agents/<slug>.md`
- Claude:
  - command-skills via `.claude/commands/<slug>.md`
  - subagents via `.claude/agents/<slug>.md`
- Kiro:
  - skills via `.kiro/skills/<slug>/SKILL.md`
  - prompts via `.kiro/prompts/<slug>.md`
  - agents via `.kiro/agents/<slug>.json`
- Codex:
  - skills via `.codex/skills/<slug>/SKILL.md`

The `clis/` folder is intentionally removed from this repo and not used as source-of-truth.

## Quick start

- List SSOT files: `ls ssot/*.md`
- Generate all surfaces: `python3 scripts/build-surfaces.py`
- Refresh schema references from vendor docs: `python3 scripts/sync-surface-specs.py`
- Validate outputs: `python3 scripts/validate-surfaces.py`
- Optional smoke checks: `python3 scripts/smoke-clis.py`
- Deploy generated surfaces globally (copy-only): `scripts/deploy-surfaces.sh --cli all`

Recommended validation flow:

1. `python3 scripts/sync-surface-specs.py`
2. `python3 scripts/build-surfaces.py`
3. `python3 scripts/validate-surfaces.py --strict`
4. `python3 scripts/smoke-clis.py --strict`
5. `scripts/deploy-surfaces.sh --dry-run --cli all`
6. `scripts/deploy-surfaces.sh --cli all`

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
- `python3 scripts/smoke-clis.py --strict`  
  Verifies expected SSOT slugs are discoverable in local Gemini/Claude/Kiro CLIs.

## Local deploy options

- `scripts/deploy-surfaces.sh --cli all`  
  Copy-only deployment for all available CLIs; overwrites existing files in place.
- `scripts/deploy-surfaces.sh --cli kiro`  
  Copy-only deployment for one CLI target.
- `scripts/deploy-surfaces.sh --dry-run --cli all`  
  Shows planned operations without writing anything.
- `scripts/deploy-surfaces.sh --cli all --strict-cli`  
  Fails if a selected/required CLI binary is unavailable.

Deployment is non-destructive for path entries: no deletes and no symlink creation. It only touches exact files for SSOT-managed slugs.

Legacy compatibility script:
- `scripts/install-local.sh` still exists for explicit link/copy mode workflows.

## Required CLI settings

- Gemini subagents: enable `"experimental.enableAgents": true`.
- Claude command-skills: do not run with `--disable-slash-commands` when testing command surfaces.
- Kiro: keep `kiro-cli` updated for current custom-agent and resource handling.

## Surfaces generated

For each SSOT file:

- `.codex/skills/<slug>/SKILL.md`
- `.gemini/skills/<slug>/SKILL.md`
- `.gemini/commands/<slug>.toml`
- `.gemini/agents/<slug>.md`
- `.claude/commands/<slug>.md`
- `.claude/agents/<slug>.md`
- `.kiro/skills/<slug>/SKILL.md`
- `.kiro/prompts/<slug>.md`
- `.kiro/agents/<slug>.json`

See `.meta/manifest.json` for generated mapping.
