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
- CLI integration reference in `docs/CLI-REFERENCE.md`
- Technical docs hub in `docs/README_TECHNICAL.md`
- Docs evolution prompt pack in `docs/prompt-pack/README.md`

## Key Files

- [CLI integration reference](docs/CLI-REFERENCE.md)
- [Technical docs hub](docs/README_TECHNICAL.md)
- [Getting started](docs/GETTING-STARTED.md)
- [Architecture](docs/ARCHITECTURE.md)
- [FAQ](docs/FAQ.md)
- [Docs evolution prompt pack](docs/prompt-pack/README.md)
- [Deploy script](scripts/deploy-surfaces.sh)
- [Packaging script](scripts/package-surfaces.sh)
- [Surface rules](.meta/surface-rules.json)

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
  - sub-agents via `.codex/agents/<slug>.toml` for SSOT entries marked `kind: agent` or `role: agent`

The `clis/` folder is intentionally removed from this repo and not used as source-of-truth.

## Quick start

- List SSOT files: `ls ssot/*.md`
- Generate all surfaces: `python3 scripts/build-surfaces.py`
- Refresh schema references from vendor docs: `python3 scripts/sync-surface-specs.py`
- Validate outputs: `python3 scripts/validate-surfaces.py`
- Optional smoke checks: `python3 scripts/smoke-clis.py`
- Deploy generated surfaces globally (copy-only): `scripts/deploy-surfaces.sh --cli all`
- Package release artifacts: `scripts/package-surfaces.sh --version vX.Y.Z`

Recommended validation flow:

1. `python3 scripts/sync-surface-specs.py`
2. `python3 scripts/build-surfaces.py`
3. `python3 scripts/validate-surfaces.py --strict`
4. `python3 scripts/smoke-clis.py --strict`
5. `scripts/deploy-surfaces.sh --dry-run --cli all`
6. `scripts/deploy-surfaces.sh --cli all`
7. `scripts/package-surfaces.sh --version vX.Y.Z`

## One-file flow

1. Edit an SSOT source file in `ssot/`.
2. Run `python3 scripts/build-surfaces.py`.
3. Run `python3 scripts/validate-surfaces.py`.
4. Commit generated artifacts.

## Docs Evolution Prompt Pack

If you want to evolve docs with an AI assistant while keeping claims factual:

- Start with [docs/prompt-pack/README.md](docs/prompt-pack/README.md)
- Single-pass mode: use `docs/prompt-pack/prompts/master-orchestrator.md`
- Modular mode: run prompts A-E in order as needed

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
- `scripts/deploy-surfaces.sh --cli all --target /tmp/llm-home`  
  Copies into a custom destination root instead of `~` (for staging/test roots).

Deployment is copy-only and never creates symlinks. If a destination file path is a symlink, deployment unlinks that path and replaces it with a regular file copy. It only touches exact files for SSOT-managed slugs.
For Codex sub-agents, deployment also updates `<target>/.codex/config.toml` under managed `[agents.<slug>]` tables.

## Packaging

- `scripts/package-surfaces.sh --version v0.2.1`  
  Builds `tar.gz` and `zip` assets in `dist/` containing generated surfaces plus deployment/docs metadata.
- `scripts/package-surfaces.sh --version v0.2.1 --output-dir dist`  
  Same behavior with explicit output directory.

## CLI integration details

- See `docs/CLI-REFERENCE.md` for:
  - per-CLI discovery commands
  - required runtime settings
  - Kiro agent field explanations and resource URI conventions
  - release validation/deploy workflow
- `analyze-context` memory files now live in `.analyze-context-memory/` at project root.

Symlink policy verification snippet:

```bash
python3 - <<'PY'
import json
from pathlib import Path
h = Path.home()
root = Path('/Users/medhat.galal/Desktop/Core-Prompts')
slugs = [e['slug'] for e in json.loads((root/'.meta/manifest.json').read_text())['ssot_sources']]
paths = []
for s in slugs:
    paths += [
        h/f'.gemini/skills/{s}/SKILL.md', h/f'.gemini/agents/{s}.md', h/f'.gemini/commands/{s}.toml',
        h/f'.claude/agents/{s}.md', h/f'.claude/commands/{s}.md',
        h/f'.kiro/skills/{s}/SKILL.md', h/f'.kiro/agents/{s}.json', h/f'.kiro/prompts/{s}.md',
        h/f'.codex/skills/{s}/SKILL.md',
    ]
for e in json.loads((root/'.meta/manifest.json').read_text())['ssot_sources']:
    if (e.get('kind') or '').lower() == 'agent':
        paths.append(h/f".codex/agents/{e['slug']}.toml")
syms = [p for p in paths if p.is_symlink()]
print(f'managed={len(paths)} symlinks={len(syms)}')
for p in syms:
    print(p)
PY
```

Legacy compatibility script:
- `scripts/install-local.sh` is a copy-only wrapper over `scripts/deploy-surfaces.sh` (link mode removed).

## Required CLI settings

- Gemini subagents: enable `"experimental.enableAgents": true`.
- Claude command-skills: do not run with `--disable-slash-commands` when testing command surfaces.
- Kiro: keep `kiro-cli` updated for current custom-agent and resource handling.

## Surfaces generated

For each SSOT file:

- `.codex/skills/<slug>/SKILL.md`
- `.codex/agents/<slug>.toml` for SSOT entries with `kind/role: agent`
- `.gemini/skills/<slug>/SKILL.md`
- `.gemini/commands/<slug>.toml`
- `.gemini/agents/<slug>.md`
- `.claude/commands/<slug>.md`
- `.claude/agents/<slug>.md`
- `.kiro/skills/<slug>/SKILL.md`
- `.kiro/prompts/<slug>.md`
- `.kiro/agents/<slug>.json`

See `.meta/manifest.json` for generated mapping.
