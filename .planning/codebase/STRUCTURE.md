# Core-Prompts Directory Structure

## High-Level Layout
- `ssot/`: canonical prompt/agent source files (one markdown file per slug).
- `scripts/`: operational tooling for build, validation, deployment, smoke checks, packaging.
- `.meta/`: build manifest, artifact rules, and schema-cache snapshots.
- `.codex/`, `.gemini/`, `.claude/`, `.kiro/`: generated per-CLI surfaces.
- `.github/workflows/`: CI automation for validation pipeline.
- `docs/`: user and technical documentation.
- `dist/`: packaged release artifacts (`.tar.gz`, `.zip`).
- `system/uac/`: UAC reference/spec materials.
- `.planning/codebase/`: codebase mapping outputs (this directory).

## Practical Tree (Key Paths)
```text
.
|- ssot/
|  |- analyze-context.md
|  |- converge.md
|  |- mentor.md
|  |- supercharge.md
|  `- threader.md
|- scripts/
|  |- build-surfaces.py
|  |- validate-surfaces.py
|  |- sync-surface-specs.py
|  |- smoke-clis.py
|  |- deploy-surfaces.sh
|  |- install-local.sh
|  `- package-surfaces.sh
|- .meta/
|  |- surface-rules.json
|  |- manifest.json
|  `- schema-cache/
|- .codex/
|  |- skills/<slug>/SKILL.md
|  `- agents/<slug>.toml
|- .gemini/
|  |- commands/<slug>.toml
|  |- skills/<slug>/SKILL.md
|  `- agents/<slug>.md
|- .claude/
|  |- commands/<slug>.md
|  |- agents/<slug>.md
|  |- get-shit-done/
|  `- hooks/
|- .kiro/
|  |- prompts/<slug>.md
|  |- skills/<slug>/SKILL.md
|  `- agents/<slug>.json
|- .github/workflows/
|  `- cli-surfaces-validate.yml
|- docs/
|- dist/
`- system/uac/
```

## Entry-Point Files by Concern
- Content authoring:
- `ssot/*.md`

- Build/generation:
- `scripts/build-surfaces.py`

- Contract/policy definition:
- `.meta/surface-rules.json`

- Validation/provenance:
- `scripts/validate-surfaces.py`
- `.meta/manifest.json`

- External schema/source caching:
- `scripts/sync-surface-specs.py`
- `.meta/schema-cache/manifest.json`

- Runtime smoke verification:
- `scripts/smoke-clis.py`

- Deployment and installation:
- `scripts/deploy-surfaces.sh`
- `scripts/install-local.sh`

- Release packaging:
- `scripts/package-surfaces.sh`
- `dist/`

- CI orchestration:
- `.github/workflows/cli-surfaces-validate.yml`

## Generated Surface Mapping (From One SSOT Slug)
For each `ssot/<slug>.md`, generator output is written to:
- `.codex/skills/<slug>/SKILL.md`
- `.gemini/commands/<slug>.toml`
- `.gemini/skills/<slug>/SKILL.md`
- `.gemini/agents/<slug>.md`
- `.claude/commands/<slug>.md`
- `.claude/agents/<slug>.md`
- `.kiro/prompts/<slug>.md`
- `.kiro/skills/<slug>/SKILL.md`
- `.kiro/agents/<slug>.json`
- Plus `.codex/agents/<slug>.toml` when SSOT frontmatter indicates agent kind.

## Current Repository Characteristics
- Small codebase footprint (`49` tracked files in current checkout).
- Heavy emphasis on generated content in dot-directories.
- Python scripts implement core logic; shell scripts handle deployment/package operations.
- No application runtime service; this repo is a content-transformation and distribution toolchain.
