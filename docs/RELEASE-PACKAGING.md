# Release Packaging

This document defines the local release path for packaged Capability Fabric artifacts.

Preferred release runtime: Python `3.14`.
Minimum supported runtime: Python `3.11+`.

Prefer the repo wrappers for build and validate so the runtime selection stays consistent.

## Local Release Gate

First verify the comparison baseline and run the release build described below. The full test suite includes archive tests that require the generated `dist/consumer-shell` views. On a clean committed checkout, validate the checked-in surfaces before that build, as CI does.

```bash
python3 -m pytest -q
bin/capability-fabric validate --strict
python3 scripts/smoke-clis.py
```

## Release comparison baseline

Before the release build, fetch and verify the previous published tag, then set `PREVIOUS_RELEASE_TAG` to that exact tag:

```bash
CORE_PROMPTS_RELEASE_BASE_REF="${PREVIOUS_RELEASE_TAG:?Set the verified previous release tag}" bin/capability-fabric build
```

The generator supports an explicit baseline
and otherwise selects the latest distinct ancestor tag available locally. Fetch
and verify the intended baseline; do not let missing local tags silently turn a
patch-release review into an older cumulative comparison. Check the recorded
comparison basis in `docs/RELEASE-DELTA.md` before packaging. Regenerate this view;
do not hand-edit its capability counts or alter historical published release notes.

## Optional deployment dry-run

After the release build above, preview deployment only when installation is in scope. This uses the already-built bundle and preserves the explicit release-comparison baseline.

```bash
bin/capability-fabric deploy --target "$HOME" --allow-nonlocal-target --dry-run --cli all
```

For a bounded repair or rollout, use `--surface-only` with at least one `--slug`. Review the exact copy set before the real command; surface-only deploy skips updater, launcher, and local-binary refresh.

## Package
```bash
scripts/package-surfaces.sh --version "$(tr -d '[:space:]' < VERSION)"
```

`VERSION` is the canonical shipped release version. Packaging fails if `--version` does not match `VERSION` or if the top `CHANGELOG.md` entry does not match `VERSION`.

## Packaged Boundary
The package should include:
- generated surfaces under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`, `.grok/`
- `.meta/manifest.json`
- `.meta/capability-handoff.json`
- `.meta/capabilities/`
- `.meta/install-bundle.json` and `.meta/install-profiles/`
- evaluation, clarity, descriptor, and plain-English job-map policy under `.meta/`
- `dist/consumer-shell/`
- `sources/ssot-baselines/`
- deploy/install scripts and `scripts/eng-report.py`; installed launchers resolve the standalone runtime copy, independently of the source checkout
- release-watch updater scripts, `VERSION`, and `RELEASE_SOURCE.env`
- local source checkout metadata, when a home install is performed from a durable checkout
- curated operator/integrator docs
- generated consumer-shell docs (`docs/CAPABILITY-CATALOG.md`, `docs/RELEASE-DELTA.md`, `docs/STATUS.md`)
- capability-evaluation and Skill Job Map documentation
- `README.md`
- `CHANGELOG.md`

The package should not include:
- `.codex/config.toml`: generated local agent registrations can contain absolute checkout paths; keep this ignored local file and regenerate registrations at the installation target
- `.planning/`
- `reports/quality-reviews/`
- stray local artifacts such as `.DS_Store`

Both archive formats and standalone runtime inventories/copies exclude local Codex registration configuration. A runtime inventory claiming this local file is rejected; agent registration still generates configuration at the installation target. ZIP creation uses a fresh temporary archive before replacing the output, so excluded or retired members cannot survive from an earlier package with the same filename.

## Remote CI
Do not call the repo release-green until the hosted CI surface is green after push.

The GitLab Python container explicitly installs `zip` for the archive tests; GitHub's hosted Ubuntu runner already provides it.
GitLab also disables the Docker runner's permissive checkout umask and builds with `umask 022`, so recorded file modes survive safe TAR extraction. See [GitLab runner feature flags](https://docs.gitlab.com/runner/configuration/feature-flags/). Installer byte and mode verification remains strict.

- GitHub Actions:
  - runs on pushes to `main` and `AI/**`
  - runs on `pull_request`
  - refreshes external CLI schema/docs references as a non-blocking drift signal
  - validates generated repo surfaces with strict local checks while skipping live schema cache enforcement
- GitLab CI:
  - runs on branch pushes
  - runs on merge request pipelines

Both providers validate the checked-in surfaces before building the distribution views required by the archive tests. This preserves drift detection on fresh checkouts.

Local release gates retain `bin/capability-fabric validate --strict`, including schema cache checks, so transient hosted network or vendor-doc failures do not mask local schema drift review.

When using `validate --with-cli`, native validator results also honor error-output patterns declared in `.meta/surface-rules.json`. Kiro CLI 2.21.1 can print an `Error:` diagnostic while returning zero; this is a failure, including when ANSI color codes surround the diagnostic. The Kiro reference set includes the current configuration page and the versioned CLI 2.x reference; it does not imply that a CLI 3.x migration was performed.

## Recommended Release Order
1. run the local release gate
2. push the branch and wait for GitHub Actions and GitLab CI to go green
3. merge only after the hosted checks are green
4. verify `VERSION`, `CHANGELOG.md`, docs, and updater help all describe the same shipped version and release-watch contract
5. build the release package from the merged state
6. create the tag and push the same tag object to GitHub and GitLab
7. publish the release artifacts and checksums on both remotes
8. accept or install the released version, then verify installed `VERSION`, surface parity, release-watch state, and rollback metadata separately from repository release evidence

## Installed Release Watch Contract

Initial install writes the installed version, release-source metadata, and local source checkout metadata into the standalone bundle:

- `~/.core-prompts-updater/VERSION`
- `~/.core-prompts-updater/RELEASE_SOURCE.env`
- `~/.core-prompts-updater/LOCAL_REPO.env`
- `~/update_core_prompts.sh`

Daily scheduled updater runs execute `~/update_core_prompts.sh --check-release` before normal update sync. `--check-release` checks only, fetches release tags, syncs a dedicated clean mirror, persists release-watch state, and never auto-installs when run directly. Scheduled runs use a deterministic PATH, treat existing managed CLI surface directories as durable update targets when binaries are unavailable to cron, and auto-accept valid releases by default after the release check; `--schedule-daily HH:MM --notify-only` preserves check-only scheduling. Bundled self-refresh is idempotent when the installed updater is both source and destination. `--accept-release` is the explicit install/apply step for manual acceptance. Legacy installs without a saved profile fast-forward the recorded source checkout and run its installer when it is clean and can fast-forward to the accepted tag; otherwise they fall back to the clean release mirror.

Saved-profile release acceptance uses a verified release mirror and its own recoverable transaction; it does not update the development checkout. The installed version and local checkout may therefore differ. See [Installation Profiles](INSTALL-PROFILES.md).

Legacy accepted releases write a rollback snapshot under `~/.core-prompts-state/snapshots/` before installing. Older snapshots are pruned so the latest 2 are retained by default; use `--snapshot-retention N` to override that. `--list-snapshots` shows rollback points, and `--rollback previous` restores the latest pre-release snapshot.


Saved-profile acceptance records rollback metadata and uses profile transactions; the legacy two-snapshot pruning policy and `--snapshot-retention` setting are not applied on that path. Preserve profile recovery data unless separately reviewed for cleanup.
