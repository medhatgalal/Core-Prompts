# Changelog

## 0.2.5 - 2026-03-03

- Rewrote root `README.md` to be prompt-first and more approachable:
  - stronger product-style intro and value framing
  - quick install path and AI handoff block
  - expanded prompt-centric examples
- Added documentation navigation hub: `docs/README.md`.
- Added full run examples page for each core prompt: `docs/EXAMPLES.md`.
- Updated technical docs routing:
  - `docs/GETTING-STARTED.md` now links to examples
  - `docs/README_TECHNICAL.md` now includes examples in start-here paths

## 0.2.4 - 2026-03-03

- Added Codex true sub-agent generation and registration flow:
  - build now emits `.codex/agents/<slug>.toml` for SSOT entries marked `kind: agent` or `role: agent`
  - deploy now registers managed `[agents.<slug>]` entries in `<target>/.codex/config.toml`
  - validation now enforces `codex_agent` artifacts only for SSOT agent entries
- Marked `mentor`, `converge`, and `supercharge` SSOT entries as `kind: agent`.
- Added docs evolution prompt system under `docs/prompt-pack/`:
  - one master orchestrator prompt
  - modular prompts A-E plus adversarial ship gate prompt F
  - operator guide for together vs modular usage
- Added technical docs structure for progressive disclosure:
  - `docs/README_TECHNICAL.md`
  - `docs/GETTING-STARTED.md`
  - `docs/ARCHITECTURE.md`
  - `docs/FAQ.md`
  - `docs/ASSETS/README.md`
- Updated root and CLI reference docs to surface the new docs architecture and prompt-pack entry points.

## 0.2.3 - 2026-03-03

- Updated `analyze-context` memory location to `.analyze-context-memory/` (project root) in SSOT and all generated surfaces.
- Updated docs to call out the `analyze-context` memory folder convention.

## 0.2.2 - 2026-03-03

- Enforced no-symlink deployment policy in `scripts/deploy-surfaces.sh`:
  - deployment never creates symlinks
  - if destination file is a symlink, the symlink path is unlinked and replaced with a regular file copy
- Converted `scripts/install-local.sh` into a copy-only wrapper around `scripts/deploy-surfaces.sh`.
  - link mode is removed and now errors if requested
- Added explicit deployment policy to `.meta/surface-rules.json` (`deployment_policy`).
- Updated docs (`README.md`, `docs/CLI-REFERENCE.md`) to document symlink replacement behavior.

## 0.2.1 - 2026-03-02

- Normalized generated Kiro agent resource URIs to root-style skill references:
  - `file://.kiro/prompts/<slug>.md`
  - `skill://.kiro/skills/<slug>/SKILL.md`
- Extended deploy script with custom destination root support:
  - `scripts/deploy-surfaces.sh --target /path`
- Added `docs/CLI-REFERENCE.md` with:
  - per-CLI discovery checks
  - required settings and behavior notes
  - Kiro agent field explanations and resource conventions
  - release/deploy validation flow
- Added `scripts/package-surfaces.sh` for deterministic release packaging (`tar.gz` + `zip`).
- Updated `README.md` and `CONTRIBUTING.md` to link CLI reference and packaging workflow.

## 0.2.0 - 2026-03-02

- Added `scripts/deploy-surfaces.sh` for copy-only global deployment to:
  - `gemini`, `claude`, `kiro`, `codex`, or `all`
- Added deployment flags:
  - `--cli gemini|claude|kiro|codex|all`
  - `--target PATH` (custom destination root; default `~`)
  - `--dry-run`
  - `--strict-cli`
- Deployment behavior is now documented as:
  - no deletes
  - no symlink creation
  - overwrite existing files in place (`cp -f`)
- Updated README and CONTRIBUTING to use `deploy-surfaces.sh` as the primary deployment path.

## 0.1.0 - 2026-03-02

- Initial bootstrap from SSOT sources.
- Added root repository docs and Apache-2.0 license.
- Added generated surfaces for:
  - `.codex/skills`
  - `.gemini/commands`
  - `.claude/commands`
  - `.kiro/prompts`
  - `.kiro/agents`
- Added build/validation tooling and CI workflow.
