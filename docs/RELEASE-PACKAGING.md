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
scripts/package-surfaces.sh --version vX.Y.Z
```

## Packaged Boundary
The package should include:
- generated surfaces under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`
- `.meta/manifest.json`
- `.meta/capability-handoff.json`
- `.meta/capabilities/`
- `sources/ssot-baselines/`
- deploy/install scripts
- curated operator/integrator docs
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
4. build the release package from the merged state
5. create the tag and publish the release artifacts
