# Changelog

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
