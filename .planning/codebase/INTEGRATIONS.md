# External Integrations

**Analysis Date:** 2026-03-04

## Integration Overview

This repo mainly integrates with:
- Local AI CLI installations (`codex`, `gemini`, `claude`, `kiro-cli`)
- Remote vendor documentation endpoints for schema/reference checks
- Optional external APIs used by embedded GSD tooling
- GitHub Actions CI runtime
- User home-directory configuration targets

It does **not** integrate with databases, cloud storage, or message brokers.

## 1) Local CLI Integrations (Primary)

### Codex
- Source artifacts generated to:
  - `.codex/skills/<slug>/SKILL.md`
  - `.codex/agents/<slug>.toml` (agent-kind entries only)
- Deployment target paths:
  - `<target>/.codex/skills/<slug>/SKILL.md`
  - `<target>/.codex/agents/<slug>.toml`
  - `<target>/.codex/config.toml`
- Registration mechanism:
  - `scripts/deploy-surfaces.sh` writes a managed block between:
    - `# >>> core-prompts codex agents start >>>`
    - `# <<< core-prompts codex agents end <<<`
  - Adds `[agents.<slug>]` with `config_file = "<target>/.codex/agents/<slug>.toml"`

### Gemini
- Source artifacts generated to:
  - `.gemini/commands/<slug>.toml`
  - `.gemini/skills/<slug>/SKILL.md`
  - `.gemini/agents/<slug>.md`
- Deployment target paths:
  - `<target>/.gemini/commands/<slug>.toml`
  - `<target>/.gemini/skills/<slug>/SKILL.md`
  - `<target>/.gemini/agents/<slug>.md`
- Verification in smoke checks:
  - `gemini --version`
  - `gemini --help`
  - `gemini skills list`

### Claude
- Source artifacts generated to:
  - `.claude/commands/<slug>.md`
  - `.claude/agents/<slug>.md`
- Deployment target paths:
  - `<target>/.claude/commands/<slug>.md`
  - `<target>/.claude/agents/<slug>.md`
- Verification in smoke checks:
  - `claude -v`
  - `claude --help`
  - `claude agents`

### Kiro
- Source artifacts generated to:
  - `.kiro/prompts/<slug>.md`
  - `.kiro/skills/<slug>/SKILL.md`
  - `.kiro/agents/<slug>.json`
- Deployment target paths:
  - `<target>/.kiro/prompts/<slug>.md`
  - `<target>/.kiro/skills/<slug>/SKILL.md`
  - `<target>/.kiro/agents/<slug>.json`
- JSON contract checks:
  - `scripts/validate-surfaces.py` can run `kiro-cli agent validate --path <file>` when `--with-cli` is enabled.
- Resource URI conventions enforced by `.meta/surface-rules.json`:
  - `file://.kiro/prompts/<slug>.md`
  - `skill://.kiro/skills/<slug>/SKILL.md`

## 2) Remote Vendor Documentation / Schema Sources

Remote sources are declared in `.meta/surface-rules.json` and refreshed by `scripts/sync-surface-specs.py`.

### External URLs used
- `https://geminicli.com/docs/cli/commands`
- `https://geminicli.com/docs/cli/custom-commands`
- `https://geminicli.com/docs/cli/skills`
- `https://geminicli.com/docs/core/subagents`
- `https://docs.anthropic.com/en/docs/claude-code/skills`
- `https://docs.anthropic.com/en/docs/claude-code/sub-agents`
- `https://kiro.dev/docs/cli/custom-agents/`
- `https://kiro.dev/docs/cli/custom-agents/configuration-reference/`
- `https://kiro.dev/docs/skills/`

### Sync/cache behavior
- Script: `scripts/sync-surface-specs.py`
- Network call method: Python `urllib.request.urlopen`
- TLS behavior: uses `ssl._create_unverified_context()`
- Cache index written to: `.meta/schema-cache/manifest.json`
- Per-source cache files stored in: `.meta/schema-cache/*.json` (checksum metadata)

## 3) CI/CD Integration

GitHub Actions workflow: `.github/workflows/cli-surfaces-validate.yml`
- Trigger: `push` to `main`, `pull_request`
- Runner: `ubuntu-latest`
- Steps:
  - `actions/checkout@v4`
  - `actions/setup-python@v5` with `python-version: '3.11'`
  - `python3 scripts/sync-surface-specs.py --refresh`
  - `python3 scripts/smoke-clis.py`
  - `python3 scripts/validate-surfaces.py --strict`

Release packaging integration (local/manual):
- `scripts/package-surfaces.sh` outputs tar/zip bundles to `dist/`.

## 4) External API Integrations in Embedded GSD Runtime

These integrations live under `.claude/get-shit-done/` and `.claude/hooks/`.

### Brave Search API (optional)
- Call site: `.claude/get-shit-done/bin/lib/commands.cjs` (`cmdWebsearch`)
- Endpoint: `https://api.search.brave.com/res/v1/web/search`
- Auth header: `X-Subscription-Token: <BRAVE_API_KEY>`
- Env var: `BRAVE_API_KEY`
- Behavior when missing key: returns `{ available: false, reason: 'BRAVE_API_KEY not set' }`

### npm registry version check (optional)
- Call site: `.claude/hooks/gsd-check-update.js`
- Command executed: `npm view get-shit-done-cc version`
- Purpose: detect update availability for bundled GSD tooling
- Cache written to: `<configDir>/cache/gsd-update-check.json`

## 5) Local OS / Filesystem Integrations

### Home directory writes (deployment)
- Script: `scripts/deploy-surfaces.sh`
- Default target: `$HOME` (or `--target` override)
- Copy policy: copy-only (`cp -f`), no symlink creation, destination symlink replacement
- Managed roots:
  - `<target>/.codex/`
  - `<target>/.gemini/`
  - `<target>/.claude/`
  - `<target>/.kiro/`

### Temp-file bridge for Claude hooks
- Statusline writes context metrics to:
  - `/tmp/claude-ctx-<session_id>.json`
- Context monitor reads that file and may write debounce marker:
  - `/tmp/claude-ctx-<session_id>-warned.json`
- Files referenced in:
  - `.claude/hooks/gsd-statusline.js`
  - `.claude/hooks/gsd-context-monitor.js`

### Config directory discovery
- Hook files inspect one of:
  - `CLAUDE_CONFIG_DIR`
  - `~/.config/opencode`
  - `~/.opencode`
  - `~/.gemini`
  - `~/.claude`
- Detection implemented in `.claude/hooks/gsd-check-update.js`

## 6) Git and CLI Process Integrations

### Git command integration
- Wrapped in `.claude/get-shit-done/bin/lib/core.cjs` via `execSync('git ...')`
- Used for ignore checks and git operations in GSD workflows.

### CLI binary presence checks
- `scripts/deploy-surfaces.sh` gates deployment with `command -v` checks for:
  - `codex`, `gemini`, `claude`, `kiro-cli`
- `scripts/validate-surfaces.py` and `scripts/smoke-clis.py` use `shutil.which(...)` similarly.

## 7) Environment Variables and Secret Surfaces

Variables actively read by code:
- `BRAVE_API_KEY`
  - Used for Brave web search API in `.claude/get-shit-done/bin/lib/commands.cjs`
  - Also used as a feature toggle signal in `.claude/get-shit-done/bin/lib/config.cjs`
- `CLAUDE_CONFIG_DIR`
  - Overrides default config directory in `.claude/hooks/gsd-check-update.js` and `.claude/hooks/gsd-statusline.js`
- `GEMINI_API_KEY`
  - Used in `.claude/hooks/gsd-context-monitor.js` to set hook event name (`AfterTool` vs `PostToolUse`)
- `SURFACE_VALIDATE_STRICT`, `SURFACE_VALIDATE_WITH_CLI`
  - Parsed in `scripts/validate-surfaces.py` to control validation behavior

File-based secret/config signals:
- `~/.gsd/brave_api_key` (checked in `.claude/get-shit-done/bin/lib/config.cjs`)
- `~/.gsd/defaults.json` (optional defaults in `.claude/get-shit-done/bin/lib/config.cjs`)

## 8) Optional Workflow Hook Integrations

Kiro generated agents include an `agentSpawn` shell hook in `.kiro/agents/*.json`:
- Command attempts to run one of:
  - `./scripts/engos prime`
  - `./engos context prime`
- This is best-effort (`|| true`) and non-fatal.

## Integration Risk Notes (Operational)

- Remote schema syncing depends on external docs availability and network; failures are tolerated unless strict mode requires failure (`scripts/sync-surface-specs.py --strict`).
- TLS verification is explicitly relaxed in schema sync (`ssl._create_unverified_context()`), which should be treated as a trust tradeoff.
- Deployment modifies user home CLI config locations; use `--dry-run` for preview.
- CLI-backed validation/smoke depth depends on local binaries being installed.

---
*Integration map derived from executable scripts, workflow files, and generated surface contracts on 2026-03-04.*
