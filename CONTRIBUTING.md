# Contributing

- Edit only SSOT files under `ssot/` for behavioral changes.
- Regenerate all outputs with `python3 scripts/build-surfaces.py`.
- Never hand-edit generated per-CLI artifacts.
- Run `python3 scripts/validate-surfaces.py` before pushing.
- Keep PRs scoped to one behavior change and include a brief validation summary.

## Adding a new prompt

1. Add `ssot/<slug>.md` using existing frontmatter fields (`name` and `description`).
2. Run the build + validate commands.
3. Commit SSOT + regenerated dot-surface files + manifest update.
