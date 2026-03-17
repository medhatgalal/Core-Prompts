# Release Packaging

This document defines the local release path for packaged Capability Fabric artifacts.

## Local Release Gate
```bash
python3 -m pytest -q
python3 scripts/validate-surfaces.py --strict
python3 scripts/smoke-clis.py
```

## Build and Dry-Run
```bash
python3 scripts/build-surfaces.py
scripts/deploy-surfaces.sh --dry-run --cli all
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
- deploy/install scripts
- curated operator/integrator docs
- `README.md`
- `CHANGELOG.md`

The package should not include:
- `.planning/`
- `reports/quality-reviews/`
- stray local artifacts such as `.DS_Store`

## Remote CI
Do not call the repo release-green until the remote GitHub Actions run is green after push.
