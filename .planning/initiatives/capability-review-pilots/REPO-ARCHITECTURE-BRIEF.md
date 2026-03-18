# Repo Architecture Brief

## Capability Fabric Flow
1. `ssot/<slug>.md` is the human-readable source of truth.
2. `.meta/capabilities/<slug>.json` is the canonical machine-readable descriptor.
3. `.meta/manifest.json` and `.meta/capability-handoff.json` publish aggregate advisory metadata.
4. `python3 scripts/build-surfaces.py` emits derived surfaces under `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`.
5. `python3 scripts/validate-surfaces.py --strict` enforces schema, metadata, and portability rules.
6. `python3 scripts/smoke-clis.py` checks surface-aware CLI discovery and generated artifact presence.
7. `scripts/deploy-surfaces.sh` and `scripts/install-local.sh` copy generated artifacts to a target root; install does not rewrite canonical metadata.

## UAC Responsibilities
- `import`: inspect source without mutation
- `plan`: inspect plus landing recommendation and family grouping
- `judge`: run quality-loop evidence without landing repo state
- `apply`: write canonical SSOT + descriptors, then rebuild and validate

UAC boundaries:
- advisory metadata only
- no orchestration or runtime delegation
- deploy remains separate from apply

## Documentation Information Architecture
Current durable docs split cleanly into:
- product/operator docs in `README.md` and `docs/GETTING-STARTED.md`, `docs/EXAMPLES.md`, `docs/FAQ.md`
- reference docs in `docs/CAPABILITY-FABRIC.md`, `docs/UAC-USAGE.md`, `docs/UAC-CAPABILITY-MODEL.md`, `docs/CLI-REFERENCE.md`, `docs/ORCHESTRATOR-CONTRACT.md`
- maintainer docs in `docs/README_TECHNICAL.md`, `docs/ARCHITECTURE.md`, `docs/RELEASE-PACKAGING.md`
- research/authoring material in `docs/prompt-pack/` and source assessment docs

## Planning System
Current planning already has the right shape for this initiative:
- top-level project/roadmap/state in `.planning/`
- initiative packages in `.planning/initiatives/`
- research and milestone history in `.planning/research/` and `.planning/milestones/`

Decision: keep `.planning/` as the working ledger for this slice and evaluate Beads / Spec-Kit as alternatives, not defaults.
