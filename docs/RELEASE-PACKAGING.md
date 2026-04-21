# Release Packaging

This document defines the local release path for packaged Capability Fabric artifacts.

Preferred release runtime: Python `3.14`.
Minimum supported runtime: Python `3.11+`.

Prefer the repo wrappers for build and validate so the runtime selection stays consistent.

## Local Release Gate
```bash
python3 -m pytest -q
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

## Build and Dry-Run
```bash
bin/capability-fabric build
bin/capability-fabric deploy --dry-run --cli all
```

## Package
```bash
scripts/package-surfaces.sh --version "$(tr -d '[:space:]' < VERSION)"
```

`VERSION` is the canonical shipped release version. Packaging fails if `--version` does not match `VERSION` or if the top `CHANGELOG.md` entry does not match `VERSION`.

## Packaged Boundary
The package should include:
- generated surfaces under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`
- `.meta/manifest.json`
- `.meta/capability-handoff.json`
- `.meta/capabilities/`
- `dist/consumer-shell/`
- `sources/ssot-baselines/`
- deploy/install scripts
- release-watch updater scripts, `VERSION`, and `RELEASE_SOURCE.env`
- curated operator/integrator docs
- generated consumer-shell docs (`docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, `docs/STATUS.md`)
- `README.md`
- `CHANGELOG.md`

The package should not include:
- `.planning/`
- `reports/quality-reviews/`
- stray local artifacts such as `.DS_Store`

## Remote CI
Do not call the repo release-green until the hosted CI surface is green after push.

- GitHub Actions:
  - runs on pushes to `main` and `AI/**`
  - runs on `pull_request`
- GitLab CI:
  - runs on branch pushes
  - runs on merge request pipelines

## Recommended Release Order
1. run the local release gate
2. push the branch and wait for GitHub Actions and GitLab CI to go green
3. merge only after the hosted checks are green
4. verify `VERSION`, `CHANGELOG.md`, docs, and updater help all describe the same shipped version and release-watch contract
5. build the release package from the merged state
6. create the tag and publish the release artifacts

## Installed Release Watch Contract

Initial install writes the installed version and release-source metadata into the standalone bundle so future checks do not depend on any local source checkout path:

- `~/.core-prompts-updater/VERSION`
- `~/.core-prompts-updater/RELEASE_SOURCE.env`
- `~/update_core_prompts.sh`

Daily scheduled updater runs execute `~/update_core_prompts.sh --check-release` before normal update sync. `--check-release` checks only, fetches release tags, syncs a dedicated clean mirror, persists release-watch state, and never auto-installs. `--accept-release` is the explicit install/apply step that refreshes from the synced mirror after confirmation.

If a newer release is pending, normal updater runs show a warning banner but do not silently mutate the user system or block normal package/tool/prompt updates.
