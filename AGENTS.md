# AGENTS.md — Core-Prompts Source of Truth

## Scope and priority

- Canonical source for all surface initialization: `/Users/medhat.galal/Desktop/Core-Prompts/ssot`.
- Canonical generated outputs: `.codex/`, `.gemini/`, `.claude/`, `.kiro/` in repository root.
- `clis/` is legacy/deprecated and must not be treated as source-of-truth.

## Surface rules

- Every SSOT file must produce artifacts for all required surfaces.
- For each SSOT entry:
  - `.codex/skills/<slug>/SKILL.md` (primary surface for Codex)
  - `.gemini/commands/<slug>.toml`
  - `.claude/commands/<slug>.md`
  - `.kiro/prompts/<slug>.md`
  - `.kiro/agents/<slug>.json`
- Do not create ad-hoc prompt artifacts for Codex when a skill surface exists and is authoritative.

## Build and validation

- Build with: `python3 scripts/build-surfaces.py`
- Validate with: `python3 scripts/validate-surfaces.py`
- CI runs validation on each push and pull request via `.github/workflows/cli-surfaces-validate.yml`.
- Treat any validation failure as blocking.

## Safe operation

- Keep changes limited to requested surface and generated output.
- Never rely on stale legacy `clis/*` paths as source.
- Preserve user-defined customization for this repo unless explicitly changed through SSOT.
