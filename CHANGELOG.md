# Changelog

## 0.2.0 - 2026-03-02

- Added `scripts/deploy-surfaces.sh` for copy-only global deployment to:
  - `gemini`, `claude`, `kiro`, `codex`, or `all`
- Added deployment flags:
  - `--cli gemini|claude|kiro|codex|all`
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
