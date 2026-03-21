# Contributing

- Edit only SSOT files under `ssot/` for behavioral changes.
- Regenerate all outputs with `bin/capability-fabric build`.
- Never hand-edit generated per-CLI artifacts.
- Run `bin/capability-fabric validate --strict` before pushing.
- Run `python3 scripts/smoke-clis.py --strict` when local CLIs are available.
- Keep PRs scoped to one behavior change and include a brief validation summary.
- Keep `docs/CLI-REFERENCE.md` aligned when changing deployment flags, CLI settings, or discovery behavior.
- Deployment policy is copy-only with symlinks forbidden at destination paths.
- Direct skill exposure is standardized on `skills/<slug>/SKILL.md`; do not add vendor `commands/` or `prompts/` targets for direct surfaces.

## Adding a new prompt

1. Add `ssot/<slug>.md` using existing frontmatter fields (`name` and `description`).
2. Run `python3 scripts/sync-surface-specs.py --refresh`.
3. Run `bin/capability-fabric build`.
4. Run `bin/capability-fabric validate --strict`.
5. Run `python3 scripts/smoke-clis.py --strict` (if local CLIs installed).
6. Optionally run `bin/capability-fabric deploy --dry-run --cli all` to verify copy deployment.
7. For non-home staging tests, use `scripts/deploy-surfaces.sh --dry-run --cli all --target "$HOME/tmp/llm-home" --allow-nonlocal-target`.
8. Optionally build release assets: `scripts/package-surfaces.sh --version vX.Y.Z`.
9. Commit SSOT + regenerated dot-surface files + manifest update.
