# AGENTS.md - Core-Prompts Source of Truth

## Scope and priority

- Canonical source for all surface initialization: `ssot/`.
- Canonical generated outputs: `.codex/`, `.gemini/`, `.claude/`, `.kiro/` in repository root.
- `clis/` is legacy/deprecated and must not be treated as source-of-truth.

## Surface rules

- UAC is advisory and recommends the surface area for each SSOT entry.
- Direct/workflow capabilities emit:
  - `.codex/skills/<slug>/SKILL.md`
  - `.gemini/skills/<slug>/SKILL.md`
  - `.claude/skills/<slug>/SKILL.md`
  - `.kiro/skills/<slug>/SKILL.md`
- Agent capabilities emit:
  - `.codex/agents/<slug>.toml`
  - `.gemini/agents/<slug>.md`
  - `.claude/agents/<slug>.md`
  - `.kiro/agents/<slug>.json`
- `capability_type: both` emits both the direct and agent surfaces above.
- Do not generate command-only or prompt-only artifacts when a skill surface already covers direct exposure.
- Classify invocation styles:
  - `codex`: skill (`$name`) inferred from `.codex/skills/<slug>/SKILL.md`
  - `codex`: sub-agent registration via `.codex/agents/<slug>.toml` and `[agents.<slug>]` in `./.codex/config.toml` for SSOT agent entries
  - `gemini`: skill in `.gemini/skills/<slug>/SKILL.md`
  - `claude`: skill in `.claude/skills/<slug>/SKILL.md`
  - `kiro`: skill in `.kiro/skills/<slug>/SKILL.md` and paired agent in `.kiro/agents/<slug>.json`

## Source-of-truth policy and schema controls

- The canonical rule set is `.meta/surface-rules.json`.
- Canonical machine-readable capability metadata lives under `.meta/capabilities/`.
- Canonical aggregate advisory metadata lives in `.meta/capability-handoff.json` and `.meta/manifest.json`.
- Canonical quality policy lives under `.meta/quality-profiles/`.
- Canonical UAC capability templates live under `.meta/capability-templates/`.
- Generated review evidence and similar run artifacts belong under `reports/`, not under `.meta/`.
- Persisted local source references in canonical metadata must be repo-relative, not absolute machine paths.
- Bundled `capability.json` resources must stay machine-portable; install/deploy must not rely on rewriting metadata paths.
- Generated Codex agent TOMLs must use the current runtime shape: `name`, `description`, `sandbox_mode`, and `developer_instructions`. Do not emit top-level `tools = [...]` arrays.
- Imported capabilities must meet a template-backed benchmark gate before `apply` can land them.
- Capability bodies must be rich enough to justify every emitted surface; do not let metadata claim stronger surfaces than the SSOT body supports.
- Every canonical SSOT entry must carry an explicit contract strong enough for direct and agentic use: `Purpose`, `Primary Objective`, workflow contract, boundaries, invocation hints, required inputs, required output, examples, and an evaluation rubric or scorecard-equivalent.
- Vendor formats are validated against cache snapshots in `.meta/schema-cache/manifest.json`.
- Update schema cache by running `python3 scripts/sync-surface-specs.py` before strict checks when docs changed.
- Preferred active runtime is Python `3.14`; minimum supported runtime is Python `3.11+`.
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
- Do not treat `reports/**` as canonical source-of-truth when rebuilding surfaces or descriptors.

## Steering Files

- Kiro steering lives under `.kiro/steering/`.
- For branch and mutation workflow, consult `.kiro/steering/repo-workflow.md` before making substantial repo changes.
- For documentation hierarchy, docs drift, and generated-doc positioning, consult `.kiro/steering/docs-governance.md` when editing `README.md`, `docs/`, generated user views, or maintainer docs.
- For rule-writing discipline and ask evaluation quality, consult `.kiro/steering/agent-behavior.md` before changing rules, docs policy, or execution posture.
- Treat these steering files as the durable cross-surface policy location. Keep `AGENTS.md` as the short router and stable repo-wide rule summary.

## Maintainer hygiene

- Use `.kiro/steering/docs-governance.md` and `.kiro/steering/repo-workflow.md` as the durable rule set for docs hygiene, docs drift, and repo workflow.
- Use `docs/MAINTAINER-HYGIENE.md` as the human-facing maintainer guide and checklist, not as the canonical rule surface.
- Review docs when commands, paths, setup, naming, metadata contracts, CI, release flow, or generated-surface behavior change materially.
- When a shipped capability changes behavior or discoverability, update the relevant user-facing docs in the same slice. Do not defer README, getting-started, or examples uplift to a later cleanup pass.
- Treat GitHub and GitLab parity as intentional design work; document any platform difference instead of letting drift accumulate silently.
- Prefer deterministic GitHub and GitLab CLIs (`gh`, `glab`) for GitOps work. Treat MCP integrations as optional helpers, not the primary release path.
- Promote a lesson into `AGENTS.md` only when it is stable, repo-wide, and likely to prevent repeated failure for future agents.
- When UAC uplift misses the benchmark bar, improve the SSOT body and the template or judge gate together; do not paper over weak bodies with descriptor-only fixes.
