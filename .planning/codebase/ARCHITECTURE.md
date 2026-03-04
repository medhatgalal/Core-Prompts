# Core-Prompts Architecture Map

## System Type
`Core-Prompts` is an SSOT-driven surface generator. It transforms prompt definitions in `ssot/` into CLI-specific artifacts under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`, then validates and deploys them.

## Concrete Entry Points
- Build: `scripts/build-surfaces.py`
- Validate: `scripts/validate-surfaces.py`
- Sync vendor schema/source snapshots: `scripts/sync-surface-specs.py`
- CLI smoke checks: `scripts/smoke-clis.py`
- Deploy to user CLI homes (copy-only): `scripts/deploy-surfaces.sh`
- Backward-compatible deploy wrapper: `scripts/install-local.sh`
- Package release archives: `scripts/package-surfaces.sh`
- CI pipeline trigger: `.github/workflows/cli-surfaces-validate.yml`

## Layering (Top to Bottom)
1. Content Layer
- Canonical authoring source: `ssot/*.md`
- Frontmatter controls slug/description and agent mode (`kind: agent` or `role: agent`).

2. Policy Layer
- Artifact rules and required formats: `.meta/surface-rules.json`
- Cached remote documentation/schemas: `.meta/schema-cache/manifest.json` and `.meta/schema-cache/*.json`

3. Transformation Layer
- `scripts/build-surfaces.py` reads each SSOT file, parses frontmatter/body, and emits generated files to:
- `.codex/skills/<slug>/SKILL.md`
- `.codex/agents/<slug>.toml` (only when SSOT entry is agent-kind)
- `.gemini/commands/<slug>.toml`, `.gemini/skills/<slug>/SKILL.md`, `.gemini/agents/<slug>.md`
- `.claude/commands/<slug>.md`, `.claude/agents/<slug>.md`
- `.kiro/prompts/<slug>.md`, `.kiro/skills/<slug>/SKILL.md`, `.kiro/agents/<slug>.json`
- Build also writes the artifact index/provenance base: `.meta/manifest.json`.

4. Verification Layer
- `scripts/validate-surfaces.py` enforces artifact presence/shape against `.meta/surface-rules.json`, checks SSOT↔manifest consistency, checks schema-cache freshness, and writes validation provenance back into `.meta/manifest.json`.
- `scripts/smoke-clis.py` probes installed CLIs and checks surface discoverability using commands like `gemini skills list`, `claude agents`, and `kiro-cli agent list`.
- CI (`.github/workflows/cli-surfaces-validate.yml`) runs `sync-surface-specs.py`, `smoke-clis.py`, and strict validation.

5. Distribution Layer
- `scripts/deploy-surfaces.sh` copies generated files into `<target>/.codex`, `<target>/.gemini`, `<target>/.claude`, `<target>/.kiro`.
- Deployment is explicitly copy-only and symlink-hostile (symlink destinations are replaced with regular files).
- For Codex agents, deploy updates `<target>/.codex/config.toml` with managed `[agents.<slug>]` blocks.
- `scripts/package-surfaces.sh` bundles distributable artifacts into `dist/*.tar.gz` and `dist/*.zip`.

## Runtime Flow
1. Author/update prompt definitions in `ssot/*.md`.
2. Run `python3 scripts/build-surfaces.py` to generate all CLI surfaces and refresh `.meta/manifest.json`.
3. Run `python3 scripts/validate-surfaces.py --strict` to enforce policy.
4. Optionally run `python3 scripts/smoke-clis.py --strict` when CLIs are installed.
5. Deploy using `scripts/deploy-surfaces.sh --cli all` (or a scoped CLI target).
6. Package with `scripts/package-surfaces.sh --version vX.Y.Z` for release output in `dist/`.

## Architectural Boundaries
- Source of truth boundary: edit `ssot/` for behavior changes; generated surfaces are outputs.
- Policy boundary: update `.meta/surface-rules.json` first when changing required artifact contracts.
- Generated artifact boundary: `.codex/`, `.gemini/`, `.claude/`, `.kiro/` are build products.
- Supplemental subsystem: `.claude/get-shit-done/` and `system/uac/` provide auxiliary workflow/framework material, not the primary SSOT generation pipeline.
