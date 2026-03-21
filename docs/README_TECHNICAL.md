# Technical Documentation Hub

Use this index when you need operational and implementation detail beyond the root README.

## Start Here

- [Getting Started](GETTING-STARTED.md): first-run setup, common command flow, and troubleshooting.
- [Examples](EXAMPLES.md): full run examples for each prompt.
- [CLI Integration Reference](CLI-REFERENCE.md): per-CLI surfaces, deployment targets, and verification commands.
- [Architecture](ARCHITECTURE.md): SSOT model, generators, validators, manifest, and deployment design.
- [Maintainer Hygiene Rules](MAINTAINER-HYGIENE.md): durable docs and GitOps review timing, parity, and lessons-capture rules.
- [FAQ](FAQ.md): common problems and practical fixes.

## Source of Truth Notes

- Authoritative content originates from `ssot/` and `.meta/surface-rules.json`.
- Generated outputs are in `.codex/`, `.gemini/`, `.claude/`, and `.kiro/`.
- Automation scripts live in `scripts/`.
- Persisted local capability source references must stay repo-relative so packaged and installed artifacts remain machine-portable.

## Typical Technical Workflow

1. Edit SSOT files in `ssot/`.
2. Build surfaces: `bin/capability-fabric build`.
3. Validate artifacts: `bin/capability-fabric validate --strict`.
4. Optionally run CLI smoke checks: `python3 scripts/smoke-clis.py --strict`.
5. Deploy managed files: `bin/capability-fabric deploy --cli all`.

Direct skill exposure is standardized on `skills/<slug>/SKILL.md` across all supported CLIs.
