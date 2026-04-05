# Changelog

## 1.4.14 - 2026-04-04

- Reworked the docs and policy split so rules stay machine-readable and user docs stay user-facing:
  - moved durable docs workflow, repo workflow, and agent-behavior policy into `.kiro/steering/`
  - updated `AGENTS.md` to route agents to steering instead of treating maintainer docs as the canonical rule source
  - clarified that maintainer docs are guides and checklists, not the governing policy layer
- Deepened the user-facing onboarding path around current installed capabilities:
  - expanded `README.md` to lead with installed skills and advisory agents, richer expected-output guidance, and transcript-style examples
  - expanded `docs/EXAMPLES.md` to cover every currently shipped skill with concrete asks, expected outputs, follow-up asks, and "why this skill first" guidance
  - refreshed `docs/GETTING-STARTED.md`, `docs/UAC-USAGE.md`, and `docs/CLI-REFERENCE.md` so installed capabilities remain first, UAC stays the intake/uplift layer, and repo tooling stays third
- Tightened docs-governance and release-facing clarity:
  - documented Kiro steering inclusion and rule-writing expectations for this repo
  - clarified the role of generated inspection views such as `docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, and `docs/STATUS.md`
  - refreshed docs routing and maintainer hygiene guidance to reduce drift and overlap

## 1.4.13 - 2026-04-04

- Added the `autosearch` capability as a first-class canonical asset:
  - landed `ssot/autosearch.md` with a measurable self-improvement contract, setup guidance, experiment loops, evaluation gates, and promotion criteria
  - generated skill and agent surfaces for Codex, Gemini, Claude, and Kiro
  - bundled capability-owned bootstrap and template resources for goal contracts, scorecards, ledgers, and promotion packets
- Hardened capability intake and emitted metadata fidelity:
  - `uac-import.py` now preserves authored SSOT bodies, frontmatter metadata, and `## Constraints` instead of falling back to flattened summaries
  - repeated judge/apply runs for an existing canonical slug now normalize to safe update behavior instead of self-conflicting
  - generated capability descriptors and bundled `capability.json` resources now carry richer authored constraints and metadata
- Improved deploy and user-facing product surfaces:
  - `scripts/deploy-surfaces.sh` now supports slug-scoped deploys and copies full bundled resource trees instead of only `capability.json`
  - refreshed `README.md` and examples to lead with installed skills and concrete example asks, while keeping `bin/uac` framed as the intake and uplift path
  - added a maintainer hygiene rule to keep README and examples user-facing rather than acronym-first and maintainer-heavy

## 1.4.12 - 2026-04-02

- Added a thin consumer shell generated from canonical metadata:
  - `scripts/build-surfaces.py` now emits `dist/consumer-shell/capability-catalog.json`, `dist/consumer-shell/release-delta.json`, and `dist/consumer-shell/status.json`
  - generated user-facing docs now include `docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, and `docs/STATUS.md`
  - release packaging now includes the generated consumer-shell bundle and docs
- Improved contributor visibility in UAC without weakening the canonical landing path:
  - `uac-import.py` now emits rendered SSOT preview, descriptor preview and delta, overlap preview, user-visible impact, and contributor guidance for `plan` and `judge`
  - imported capability metadata now carries additive `version`, `author`, `compatibility`, `supported_agents`, and invocation hints through manifest and generated surfaces
- Hardened validation and operational reporting:
  - added prompt and metadata linting for advisory-only policy boundaries and secret-like literals
  - `smoke-clis.py` now persists report artifacts under `reports/smoke-clis/`
  - strict validation now warns instead of hard-failing when a remote schema refresh is unhealthy but a cached artifact is already available
- Refreshed docs and tests for the new consumer-facing model:
  - updated `README.md`, docs hub, getting-started, CLI reference, and release packaging docs to explain the upstream-plus-consumer-shell split
  - added regression coverage for consumer shell generation, richer UAC previews, validation linting, and smoke-report persistence

## 1.4.11 - 2026-03-22

- Made the canonical manifest content-stable:
  - removed volatile build timestamps from `.meta/manifest.json`
  - removed validation provenance from the tracked manifest so repeated no-op `build` and `validate` runs no longer dirty git
  - kept `.meta/manifest.json` focused on canonical SSOT inventory and generated artifact mapping
- Moved volatile run evidence into ignored reports:
  - `scripts/build-surfaces.py` now writes build provenance under `reports/build-surfaces/`
  - `scripts/validate-surfaces.py` now writes validation provenance under `reports/validation/`
  - no-op manifest writes are skipped when canonical content has not changed
- Added regression coverage and updated docs:
  - added a manifest stability test proving repeated build/validate runs keep the tracked manifest byte-stable
  - updated architecture and CLI reference docs to explain the manifest/report split

## 1.4.10 - 2026-03-22

- Hardened Codex agent registration during install and deploy:
  - taught `scripts/deploy-surfaces.sh` to remove stale duplicate managed `[agents.<slug>]` stanzas anywhere in `config.toml` before writing the canonical Core-Prompts managed block
  - made repeat installs idempotent so managed agent registration stays singular instead of accumulating duplicate entries over time
  - preserved unrelated custom agent registrations while cleaning only the managed Core-Prompts agent set
- Added regression coverage for installer hygiene:
  - verified repeated Codex deploy/install runs do not duplicate managed agent stanzas
  - verified legacy duplicate managed stanzas are cleaned up while unmanaged custom config remains intact

## 1.4.9 - 2026-03-21

- Clarified the default usage model for Core-Prompts:
  - updated `README.md` to state that the primary way to use Core-Prompts is through the skills already deployed into the CLI
  - repositioned repo, UAC, and Capability Fabric flows as the advanced maintainer and authoring layer rather than the default entrypoint
  - updated `docs/README.md` and `docs/GETTING-STARTED.md` so the first path is using deployed Core-Prompts, with repo build and release workflows clearly presented as secondary

## 1.4.8 - 2026-03-21

- Reworked the top-layer documentation to explain the user value more clearly:
  - rewrote `README.md` around prompt drift, prompt weakening, trust loss, and reusable capability value instead of leading with internal architecture terms
  - updated `docs/README.md` to route readers by intent and audience instead of only by doc category
  - upgraded `docs/GETTING-STARTED.md` to explain what success looks like, why the workflow is worth doing, and where to go next for exact technical depth
- Preserved technical and maintainer depth while improving onboarding:
  - kept the deeper developer and maintainer docs in-repo and linked them more clearly
  - kept the skills-only direct-surface model and baseline-source model consistent across the edited docs

## 1.4.7 - 2026-03-21

- Shipped the historical-baseline and skills-only standardization slice:
  - moved the fidelity baseline oracle from commit-only references into repo-resident baseline sources under `sources/ssot-baselines/`
  - taught UAC quality and descriptor generation to persist historical baseline metadata and validation matrices across canonical descriptors and bundled capability resources
  - removed the remaining generator compatibility logic for direct `commands/` and `prompts/` targets so direct exposure stays standardized on `skills/<slug>/SKILL.md`
- Tightened deploy and validation guarantees:
  - added regression coverage proving deploy/install do not create `.gemini/commands`, `.claude/commands`, `.codex/prompts`, `.kiro/prompts`, or `.agents/*` direct-surface paths
  - kept deploy/install copy-only and verified the generated surface set remains skill-first for all supported CLIs
- Reworked operator and maintainer docs to match the current repo state:
  - promoted the `bin/uac` and `bin/capability-fabric` wrappers as the preferred entrypoints
  - clarified the direct-surface standard, baseline-source model, and release order across `README.md`, `docs/README.md`, `docs/CLI-REFERENCE.md`, `docs/UAC-USAGE.md`, `docs/CAPABILITY-FABRIC.md`, and `docs/RELEASE-PACKAGING.md`
  - aligned contributing guidance with the current build, validate, deploy, and packaging workflow

## 1.4.6 - 2026-03-20

- Raised the SSOT contract bar across the full catalog:
  - enforced a repo-wide contract requiring purpose, primary objective, workflow contract, boundaries, invocation hints, required inputs, required output, examples, and an evaluation rubric or scorecard-equivalent for every canonical SSOT entry
  - strengthened `architecture`, `mentor`, `threader`, and `resolve-conflict` to meet that contract without stripping their specialized operating instructions
  - added clearer companion-capability routing so direct skills and advisory agents hand off cleanly instead of overreaching
- Hardened prompt and orchestration quality after the `v1.4.5` release:
  - restored and strengthened the rich operational sections in `code-review` and `resolve-conflict`
  - added stronger contract and routing layers for `analyze-context`, `uac-import`, `threader`, and `mentor`
  - rebuilt generated skill and agent surfaces across Codex, Gemini, Claude, and Kiro to match the stronger SSOT bodies
- Improved validation reliability and future quality gates:
  - extended canonical-source validation from a benchmark subset to all SSOT entries
  - taught the validator to recognize workflow and example equivalents such as `Workflow Contract`, `Resolution Process`, `Example Invocation Patterns`, and `Usage Examples`
  - fixed the metadata walk in `validate-surfaces.py` so transient filesystem races no longer cause flaky strict-validation failures
  - added regression coverage for the validator fallback path

## 1.4.4 - 2026-03-18

- Shipped the capability uplift recovery slice:
  - reworked `docs-review-expert` into a true `both` capability with skill and advisory agent surfaces
  - added `gitops-review` as a new `both` capability for repo hygiene, CI, merge, packaging, tag, and release gates
  - rewrote the weak SSOT bodies for `supercharge`, `analyze-context`, and `converge` to match the benchmark-grade contract used by `architecture`, `code-review`, `testing`, and `uac-import`
- Hardened UAC landing quality:
  - added machine-readable capability templates for `skill`, `agent`, and `both`
  - added benchmark-readiness scoring, scorecards, and apply-block behavior for weak candidates
  - added validator coverage for malformed multi-frontmatter SSOT files
- Hardened schema-cache refresh behavior:
  - strict validation now tolerates transient upstream doc timeouts when a previously healthy cache snapshot is available
  - refreshed the schema cache and verified strict validation, smoke checks, and full pytest coverage before release

## 1.4.2 - 2026-03-18

- Fixed portable capability metadata for repo-local SSOT sources:
  - canonical descriptors and `.meta/manifest.json` now persist repo-relative source refs like `ssot/architecture.md`
  - bundled `capability.json` resources no longer embed build-machine absolute SSOT paths
- Added guardrails so the regression fails fast:
  - strict validation now rejects absolute local source refs in persisted capability metadata
  - source-reference portability is now documented in repo policy and technical docs
- Rebuilt generated surfaces and reran home install so installed CLI resources match the portable metadata policy

## 1.4.0 - 2026-03-17

- Shipped the Capability Fabric broad release slice:
  - added UAC quality-loop documentation and clarified `judge`, `apply`, `deploy`, and `package` boundaries
  - promoted `architecture` to a dual-surface capability with advisory artifact-writer agent surfaces
  - normalized descriptor display names, summaries, and high-priority consumption hints
  - added orchestrator-facing contract and release-packaging docs
  - tightened smoke-test semantics around surface-aware discovery

## 1.3.1 - 2026-03-13

- Hardened install/deploy behavior for partial CLI environments:
  - removed the Bash 4+ `mapfile` dependency from `scripts/deploy-surfaces.sh`
  - verified copy-only deployment works under macOS system Bash
  - kept non-strict mode as a safe no-op when selected CLIs are unavailable
- Added deployment/install integration coverage for:
  - no-CLI, partial-CLI, and strict missing-CLI scenarios
  - Codex agent registration boundaries
  - wrapper parity between `scripts/install-local.sh` and `scripts/deploy-surfaces.sh`
- Updated docs to ship and explain the new SSOT skills:
  - `code-review`
  - `resolve-conflict`
  - clarified that both remain skill-only surfaces and are not Codex sub-agents

## 1.3 - 2026-03-11

- Shipped controlled extension re-entry for the Local Intent Sanitizer milestone:
  - shared fail-closed extension contracts and boundary gates
  - deterministic URL ingestion with canonical normalization, explicit URL policy, immutable snapshots, and provenance propagation
  - simulate-first controlled execution with exact approval contracts, closed executor registry mapping, deterministic journal evidence, idempotency replay, and hermetic adapter behavior
- Added real public source validation coverage:
  - accepted prompt/spec-style raw URL path through Phase 6
  - rejected non-intent-bearing raw URL path before execution surfaces
- Added `scripts/run-url-e2e.py` so one URL can be run through ingest, summary, uplift, routing, Phase 4, Phase 5, and Phase 6.

## 0.2.6 - 2026-03-03

- Anonymized local/private absolute paths in docs and prompts:
  - replaced user-specific paths with `<repo_path>/Core-Prompts` placeholders
  - replaced `/tmp/llm-home` examples with `$HOME/tmp/llm-home`
  - normalized AGENTS source path to `ssot/`
- Reworked root `README.md` structure:
  - value-first opening statement
  - full examples with expected outputs for each core skill
  - installation section after examples
  - additional links section at the end
- Reduced repository-structure detail in `README.md` to keep the page user-facing and outcome-focused.

## 0.2.5 - 2026-03-03

- Rewrote root `README.md` to be prompt-first and more approachable:
  - stronger product-style intro and value framing
  - quick install path and AI handoff block
  - expanded prompt-centric examples
- Added documentation navigation hub: `docs/README.md`.
- Added full run examples page for each core prompt: `docs/EXAMPLES.md`.
- Updated technical docs routing:
  - `docs/GETTING-STARTED.md` now links to examples
  - `docs/README_TECHNICAL.md` now includes examples in start-here paths

## 0.2.4 - 2026-03-03

- Added Codex true sub-agent generation and registration flow:
  - build now emits `.codex/agents/<slug>.toml` for SSOT entries marked `kind: agent` or `role: agent`
  - deploy now registers managed `[agents.<slug>]` entries in `<target>/.codex/config.toml`
  - validation now enforces `codex_agent` artifacts only for SSOT agent entries
- Marked `mentor`, `converge`, and `supercharge` SSOT entries as `kind: agent`.
- Added docs evolution prompt system under `docs/prompt-pack/`:
  - one master orchestrator prompt
  - modular prompts A-E plus adversarial ship gate prompt F
  - operator guide for together vs modular usage
- Added technical docs structure for progressive disclosure:
  - `docs/README_TECHNICAL.md`
  - `docs/GETTING-STARTED.md`
  - `docs/ARCHITECTURE.md`
  - `docs/FAQ.md`
  - `docs/ASSETS/README.md`
- Updated root and CLI reference docs to surface the new docs architecture and prompt-pack entry points.

## 0.2.3 - 2026-03-03

- Updated `analyze-context` memory location to `.analyze-context-memory/` (project root) in SSOT and all generated surfaces.
- Updated docs to call out the `analyze-context` memory folder convention.

## 0.2.2 - 2026-03-03

- Enforced no-symlink deployment policy in `scripts/deploy-surfaces.sh`:
  - deployment never creates symlinks
  - if destination file is a symlink, the symlink path is unlinked and replaced with a regular file copy
- Converted `scripts/install-local.sh` into a copy-only wrapper around `scripts/deploy-surfaces.sh`.
  - link mode is removed and now errors if requested
- Added explicit deployment policy to `.meta/surface-rules.json` (`deployment_policy`).
- Updated docs (`README.md`, `docs/CLI-REFERENCE.md`) to document symlink replacement behavior.

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
