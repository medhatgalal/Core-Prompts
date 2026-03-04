# Technology Stack

**Analysis Date:** 2026-03-04

## Stack Snapshot

This repository is a **prompt-surface generator and validator** built around SSOT markdown inputs in `ssot/` and generated outputs in `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`.

Execution entrypoints are script-driven:
- Build: `python3 scripts/build-surfaces.py`
- Validate: `python3 scripts/validate-surfaces.py --strict`
- Smoke checks: `python3 scripts/smoke-clis.py --strict`
- Schema refresh: `python3 scripts/sync-surface-specs.py --refresh`
- Deploy: `scripts/deploy-surfaces.sh --cli all`

## Languages

**Primary**
- Python 3.11+ for generation, validation, schema sync, and smoke checks.
  - Entrypoints: `scripts/build-surfaces.py`, `scripts/validate-surfaces.py`, `scripts/sync-surface-specs.py`, `scripts/smoke-clis.py`
  - Version gate: `if sys.version_info < (3, 11)` in `scripts/validate-surfaces.py`

**Secondary**
- Bash for deployment/packaging wrappers.
  - Entrypoints: `scripts/deploy-surfaces.sh`, `scripts/package-surfaces.sh`, `scripts/install-local.sh`
- JavaScript (Node, CommonJS) for embedded GSD utility runtime under Claude surfaces.
  - Entrypoints: `.claude/get-shit-done/bin/gsd-tools.cjs`, `.claude/hooks/gsd-statusline.js`, `.claude/hooks/gsd-context-monitor.js`, `.claude/hooks/gsd-check-update.js`
- Markdown/TOML/JSON/YAML as first-class data/config formats.
  - SSOT source: `ssot/*.md`
  - Rules and manifests: `.meta/surface-rules.json`, `.meta/manifest.json`
  - Generated artifacts: `*.md`, `*.toml`, `*.json` in dot-surface directories
  - Auxiliary matrix: `system/uac/cli_tool_matrix.yaml`

## Runtime Environment

**Python runtime**
- Required: Python 3.11+ (documented in `docs/GETTING-STARTED.md` and enforced in `scripts/validate-surfaces.py`).
- Dependency model: stdlib only (`argparse`, `json`, `pathlib`, `subprocess`, `urllib`, `tomllib`, etc.).

**Node runtime**
- Required for GSD helper/hook scripts shipped in `.claude/`.
- Module type: CommonJS (`.claude/package.json` contains `{ "type": "commonjs" }`).
- Dependency model: no third-party npm modules in-repo; scripts use Node built-ins (`fs`, `path`, `os`, `child_process`).

**Shell/runtime tools**
- Bash-compatible shell required for deploy/package scripts.
- External binaries invoked by scripts include `git`, `tar`, `zip`, and optional CLI binaries (`codex`, `gemini`, `claude`, `kiro-cli`).

## Build and Generation Pipeline

Source-of-truth and generation flow:
1. Read SSOT files from `ssot/*.md`.
2. Parse metadata/body in `scripts/build-surfaces.py`.
3. Generate per-surface artifacts under:
   - `.codex/skills/<slug>/SKILL.md`
   - `.codex/agents/<slug>.toml` (agent-only)
   - `.gemini/commands/<slug>.toml`
   - `.gemini/skills/<slug>/SKILL.md`
   - `.gemini/agents/<slug>.md`
   - `.claude/commands/<slug>.md`
   - `.claude/agents/<slug>.md`
   - `.kiro/prompts/<slug>.md`
   - `.kiro/skills/<slug>/SKILL.md`
   - `.kiro/agents/<slug>.json`
4. Emit artifact index and provenance to `.meta/manifest.json`.

Concrete generated examples currently present:
- `.codex/skills/supercharge/SKILL.md`
- `.codex/agents/supercharge.toml`
- `.gemini/commands/supercharge.toml`
- `.claude/commands/supercharge.md`
- `.kiro/agents/supercharge.json`

## Validation and Quality Gates

Validation logic is rules-driven by `.meta/surface-rules.json`:
- Structural validation: TOML/frontmatter/JSON fields in `scripts/validate-surfaces.py`
- Schema source cache verification against `.meta/schema-cache/manifest.json`
- Optional CLI-backed validators (for example `kiro-cli agent validate --path`)
- Manifest consistency check between `ssot/` and `.meta/manifest.json`

Smoke verification (`scripts/smoke-clis.py`) probes:
- Version and help commands for configured CLIs
- Discovery commands:
  - Gemini: `gemini skills list`
  - Claude: `claude agents`
  - Kiro: `kiro-cli agent list`

## Packaging and Distribution

Release artifact script: `scripts/package-surfaces.sh`
- Creates archives under `dist/`:
  - `core-prompts-<version>-surfaces.tar.gz`
  - `core-prompts-<version>-surfaces.zip`
- Includes generated dot-surface folders and metadata/docs.

Observed packaged outputs include:
- `dist/core-prompts-v0.2.6-surfaces.tar.gz`
- `dist/core-prompts-v0.2.6-surfaces.zip`

## Configuration Surfaces

Core config/rule files:
- `.meta/surface-rules.json` (artifact contracts + tooling definitions)
- `.meta/manifest.json` (generated mapping + validation provenance)
- `.meta/schema-cache/manifest.json` (remote schema/doc cache index)

User/system config hooks:
- Deployment target root defaults to `$HOME` in `scripts/deploy-surfaces.sh`
- Codex agent registration writes managed blocks in `<target>/.codex/config.toml`
- Claude hook scripts read `CLAUDE_CONFIG_DIR` when set

## Dependencies and Libraries (Practical View)

**In-repo code dependencies**
- Python: standard library + `tomllib` (built-in for 3.11+)
- Node: built-in modules only; no package-lock/pnpm/yarn workspace at repo root

**Tooling dependencies (external binaries, optional by mode)**
- Required for full strict validation/deploy/smoke paths:
  - `codex`, `gemini`, `claude`, `kiro-cli`
- Required for packaging/deployment workflows:
  - `tar`, `zip`, `git`, `cp`

## What This Stack Is Not

- No application server runtime (no web API/service in this repo).
- No database or ORM layer.
- No frontend framework build chain.
- No container orchestration files (`Dockerfile`, `docker-compose.yml`) in current tree.

## Operational Baseline

Minimum practical baseline to run core workflows:
- Python 3.11+
- Bash shell + standard Unix utilities
- Git working tree
- Optional local CLI binaries for multi-CLI smoke/deploy coverage

---
*Stack mapped from executable sources and repo docs on 2026-03-04.*
