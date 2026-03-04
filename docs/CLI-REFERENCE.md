# CLI Integration Reference

This document defines the generated surfaces, deployment behavior, verification commands, and required runtime settings for each supported CLI.

## Local References

- Surface rules: `.meta/surface-rules.json`
- Generated mapping: `.meta/manifest.json`
- Technical docs index: `docs/README_TECHNICAL.md`
- Onboarding guide: `docs/GETTING-STARTED.md`
- Architecture notes: `docs/ARCHITECTURE.md`
- FAQ: `docs/FAQ.md`
- Build: `scripts/build-surfaces.py`
- Validate: `scripts/validate-surfaces.py`
- Smoke checks: `scripts/smoke-clis.py`
- Deploy (copy-only): `scripts/deploy-surfaces.sh`
- Package release artifacts: `scripts/package-surfaces.sh`

## Deploy Script Contract

- Script: `scripts/deploy-surfaces.sh`
- Modes: copy-only, overwrite existing files in place, no symlink creation
- Symlink handling: if destination file is a symlink, deployment unlinks that path and writes a regular file
- Flags:
  - `--cli gemini|claude|kiro|codex|all` (default: `all`)
  - `--target PATH` (default: `~`)
  - `--dry-run`
  - `--strict-cli`

Examples:
- Deploy all to home root: `scripts/deploy-surfaces.sh --cli all`
- Deploy only Kiro to a staging root: `scripts/deploy-surfaces.sh --cli kiro --target "$HOME/tmp/llm-home"`
- Verify planned writes only: `scripts/deploy-surfaces.sh --dry-run --cli all --target "$HOME/tmp/llm-home"`
- Verify managed deployment targets are not symlinks:
  - `python3 - <<'PY' ...` (see README verification snippet)

## Generated Surfaces By CLI

### Gemini

Source paths:
- `.gemini/skills/<slug>/SKILL.md`
- `.gemini/agents/<slug>.md`
- `.gemini/commands/<slug>.toml`

Home deployment targets under `--target` root:
- `<target>/.gemini/skills/<slug>/SKILL.md`
- `<target>/.gemini/agents/<slug>.md`
- `<target>/.gemini/commands/<slug>.toml`

Verify discovery:
- `gemini skills list`
- For command and subagent behavior, verify via manual invocation in an interactive session.

Required setting for subagents:
- Enable `"experimental.enableAgents": true`.

### Claude

Source paths:
- `.claude/commands/<slug>.md`
- `.claude/agents/<slug>.md`

Home deployment targets under `--target` root:
- `<target>/.claude/commands/<slug>.md`
- `<target>/.claude/agents/<slug>.md`

Verify discovery:
- `claude agents`

Requirement:
- Do not run with `--disable-slash-commands` when validating command-skills.

### Kiro

Source paths:
- `.kiro/skills/<slug>/SKILL.md`
- `.kiro/prompts/<slug>.md`
- `.kiro/agents/<slug>.json`

Home deployment targets under `--target` root:
- `<target>/.kiro/skills/<slug>/SKILL.md`
- `<target>/.kiro/prompts/<slug>.md`
- `<target>/.kiro/agents/<slug>.json`

Verify discovery and config validity:
- `kiro-cli agent list`
- `kiro-cli agent validate --path .kiro/agents/<slug>.json`

Canonical generated Kiro resource URIs:
- `file://.kiro/prompts/<slug>.md`
- `skill://.kiro/skills/<slug>/SKILL.md`

#### Kiro Agent Config Fields (Operational Meaning)

Core generated fields:
- `name`: unique agent identifier.
- `description`: listing/selection description.
- `prompt`: inline prompt body.
- `resources`: preloaded files/skills used during execution.
- `hooks`: lifecycle commands (for example, `agentSpawn`).
- `tools`: tool allowlist (`["*"]` allows all).

Additional supported fields you can adopt later:
- `allowedTools`: explicit allowlist for tighter tool restrictions.
- `toolAliases`: custom aliases for tool names.
- `toolsSettings`: per-tool execution settings.
- `mcpServers`: MCP server definitions for the agent.
- `includeMcpJson`: include workspace MCP config automatically.
- `model`: per-agent model override.
- `knowledgeBase`: knowledge base resources/config (when enabled by CLI schema).
- Additional hook phases depending on CLI version (for example `preTool`, `postTool`, `sessionStart`, `userPromptSubmit`).

### Codex

Source paths:
- `.codex/skills/<slug>/SKILL.md`
- `.codex/agents/<slug>.toml` (only for SSOT entries marked `kind/role: agent`)

Home deployment targets under `--target` root:
- `<target>/.codex/skills/<slug>/SKILL.md`
- `<target>/.codex/agents/<slug>.toml`
- `<target>/.codex/config.toml` (managed `[agents.<slug>]` registration block)

Verify discovery:
- `codex --help` and invoke skill by name in a session.
- For sub-agents, verify `~/.codex/config.toml` includes `[agents.<slug>]` entries with `config_file` paths.

## Skill-specific Memory Convention

- `analyze-context` stores canonical memory files in `.analyze-context-memory/` at the project root.

## Validation and Release Flow

1. `python3 scripts/sync-surface-specs.py`
2. `python3 scripts/build-surfaces.py`
3. `python3 scripts/validate-surfaces.py --strict --with-cli`
4. `python3 scripts/smoke-clis.py --strict`
5. `scripts/deploy-surfaces.sh --dry-run --cli all --target "$HOME/tmp/llm-home"`
6. `scripts/package-surfaces.sh --version vX.Y.Z`

## Vendor Documentation

- Gemini commands: https://geminicli.com/docs/cli/commands
- Gemini skills: https://geminicli.com/docs/cli/skills
- Gemini sub-agents: https://geminicli.com/docs/cli/sub-agents
- Claude skills: https://docs.anthropic.com/en/docs/claude-code/skills
- Claude sub-agents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Kiro custom agents: https://kiro.dev/docs/cli/custom-agents/
- Kiro configuration reference: https://kiro.dev/docs/cli/custom-agents/configuration-reference/
- Kiro skills: https://kiro.dev/docs/skills/
