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
- local source checkout metadata, when a home install is performed from a durable checkout
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

Initial install writes the installed version, release-source metadata, and local source checkout metadata into the standalone bundle:

- `~/.core-prompts-updater/VERSION`
- `~/.core-prompts-updater/RELEASE_SOURCE.env`
- `~/.core-prompts-updater/LOCAL_REPO.env`
- `~/update_core_prompts.sh`

Daily scheduled updater runs execute `~/update_core_prompts.sh --check-release` before normal update sync. `--check-release` checks only, fetches release tags, syncs a dedicated clean mirror, persists release-watch state, and never auto-installs when run directly. Scheduled runs auto-accept valid releases by default after the release check; `--schedule-daily HH:MM --notify-only` preserves check-only scheduling. `--accept-release` is the explicit install/apply step for manual acceptance. Accepted releases fast-forward the recorded source checkout and run its installer when the checkout is clean and can fast-forward to the accepted tag; otherwise they fall back to the clean release mirror.

Every accepted release writes a rollback snapshot under `~/.core-prompts-state/snapshots/` before installing. Older snapshots are pruned so the latest 2 are retained by default; use `--snapshot-retention N` to override that. `--list-snapshots` shows rollback points, and `--rollback previous` restores the latest pre-release snapshot.
