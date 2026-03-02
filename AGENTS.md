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
- Classify invocation styles:
  - `codex`: skill (`$name`) inferred from `.codex/skills/<slug>/SKILL.md`
  - `gemini`: slash command in `.gemini/commands/<slug>.toml`
  - `claude`: slash command in `.claude/commands/<slug>.md`
  - `kiro`: prompt in `.kiro/prompts/<slug>.md` and paired agent in `.kiro/agents/<slug>.json`

## Source-of-truth policy and schema controls

- The canonical rule set is `.meta/surface-rules.json`.
- Vendor formats are validated against cache snapshots in `.meta/schema-cache/manifest.json`.
- Update schema cache by running `python3 scripts/sync-surface-specs.py` before strict checks when docs changed.
- The validator is implemented as a verifier and must match the rule definitions; changes must be made to rules first, then generator/validator.

## Build and validation

- Build with: `python3 scripts/build-surfaces.py`
- Validate with: `python3 scripts/validate-surfaces.py`
- CI runs validation on each push and pull request via `.github/workflows/cli-surfaces-validate.yml`.
- Treat any validation failure as blocking.

## Safe operation

- Keep changes limited to requested surface and generated output.
- Never rely on stale legacy `clis/*` paths as source.
- Preserve user-defined customization for this repo unless explicitly changed through SSOT.
