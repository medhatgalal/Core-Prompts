# Contributing

- Edit only SSOT files under `ssot/` for behavioral changes.
- Regenerate all outputs with `python3 scripts/build-surfaces.py`.
- Never hand-edit generated per-CLI artifacts.
- Run `python3 scripts/validate-surfaces.py` before pushing.
- Run `python3 scripts/smoke-clis.py --strict` when local CLIs are available.
- Keep PRs scoped to one behavior change and include a brief validation summary.
- Keep `docs/CLI-REFERENCE.md` aligned when changing deployment flags, CLI settings, or discovery behavior.
- Deployment policy is copy-only with symlinks forbidden at destination paths.

## Adding a new prompt

1. Add `ssot/<slug>.md` using existing frontmatter fields (`name` and `description`).
2. Run `python3 scripts/sync-surface-specs.py --refresh`.
3. Run `python3 scripts/build-surfaces.py`.
4. Run `python3 scripts/validate-surfaces.py --strict`.
5. Run `python3 scripts/smoke-clis.py --strict` (if local CLIs installed).
6. Optionally run `scripts/deploy-surfaces.sh --dry-run --cli all` to verify global copy deployment.
7. For non-home staging tests, use `scripts/deploy-surfaces.sh --dry-run --cli all --target "$HOME/tmp/llm-home"`.
8. Optionally build release assets: `scripts/package-surfaces.sh --version vX.Y.Z`.
9. Commit SSOT + regenerated dot-surface files + manifest update.
