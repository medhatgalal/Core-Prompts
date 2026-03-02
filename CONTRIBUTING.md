# Contributing

- Edit only SSOT files under `ssot/` for behavioral changes.
- Regenerate all outputs with `python3 scripts/build-surfaces.py`.
- Never hand-edit generated per-CLI artifacts.
- Run `python3 scripts/validate-surfaces.py` before pushing.
- Run `python3 scripts/smoke-clis.py --strict` when local CLIs are available.
- Keep PRs scoped to one behavior change and include a brief validation summary.

## Adding a new prompt

1. Add `ssot/<slug>.md` using existing frontmatter fields (`name` and `description`).
2. Run `python3 scripts/sync-surface-specs.py --refresh`.
3. Run `python3 scripts/build-surfaces.py`.
4. Run `python3 scripts/validate-surfaces.py --strict`.
5. Run `python3 scripts/smoke-clis.py --strict` (if local CLIs installed).
6. Optionally run `scripts/install-local.sh --dry-run --mode link` to verify global sync changes.
7. Commit SSOT + regenerated dot-surface files + manifest update.
