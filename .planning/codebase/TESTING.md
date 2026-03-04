# Testing Practices

## Current Testing Model
- This repo uses script-based validation and smoke checks instead of a dedicated unit-test framework.
- No `tests/` or `test_*.py` suite is present; quality gates are implemented in executable scripts and CI.

## Primary Test/Validation Entry Points
1. Build generated artifacts:
   - `python3 scripts/build-surfaces.py`
   - Produces surfaces and updates `.meta/manifest.json`.
2. Structural validation:
   - `python3 scripts/validate-surfaces.py --strict`
   - Validates generated artifacts against `.meta/surface-rules.json` (TOML/frontmatter/JSON checks, expected/missing/extra file checks, manifest consistency, schema-cache health, CLI probe behavior).
3. CLI smoke/discovery checks:
   - `python3 scripts/smoke-clis.py --strict`
   - Probes configured CLIs from `.meta/surface-rules.json` (`codex`, `gemini`, `claude`, `kiro-cli`) and verifies generated slug discovery commands.
4. Schema cache refresh (pre-validation support):
   - `python3 scripts/sync-surface-specs.py --refresh`
   - Refreshes `.meta/schema-cache/manifest.json` entries used by strict validation.

## CI Test Layout
- Workflow: `.github/workflows/cli-surfaces-validate.yml`.
- Trigger: `push` to `main` and all `pull_request` events.
- Job sequence:
  1. `python3 scripts/sync-surface-specs.py --refresh` (non-blocking sync step)
  2. `python3 scripts/smoke-clis.py`
  3. `python3 scripts/validate-surfaces.py --strict`

## Where Assertions Live
- `scripts/validate-surfaces.py`:
  - Format/required-field checks (`validate_toml`, `validate_frontmatter`, `validate_json`).
  - Artifact set completeness and no-extras checks (`collect_actual`, expected-vs-actual diffing).
  - Schema-cache TTL and health checks (`check_schema_cache`).
  - Optional CLI binary/version probing (`cli_probe_warnings`, `collect_cli_versions`).
- `scripts/smoke-clis.py`:
  - CLI executable existence and probe checks (`run_probe`).
  - Discovery assertions for expected slugs (`assert_discovery`).
- `scripts/sync-surface-specs.py`:
  - External schema/doc fetch health and cache metadata updates.

## Coverage Notes (What Is and Is Not Covered)
- Covered well:
  - Generated artifact presence and schema shape under `.codex/`, `.gemini/`, `.claude/`, `.kiro/`.
  - SSOT-to-manifest consistency (`ssot/*.md` vs `.meta/manifest.json`).
  - CLI startup/discovery sanity checks when binaries are installed.
  - Schema reference freshness via `.meta/schema-cache/manifest.json`.
- Partially covered:
  - Deploy behavior in `scripts/deploy-surfaces.sh` is mostly verified via dry-run/manual checks rather than automated assertions.
- Not covered by an automated unit suite:
  - Parser edge cases in `scripts/build-surfaces.py`/`scripts/validate-surfaces.py`.
  - End-to-end packaging checks for `scripts/package-surfaces.sh`.
  - Numeric code coverage reporting (no coverage tool config despite `coverage/` ignore entry in `.gitignore`).

## Practical Local Test Workflow
1. `python3 scripts/sync-surface-specs.py --refresh`
2. `python3 scripts/build-surfaces.py`
3. `python3 scripts/validate-surfaces.py --strict`
4. `python3 scripts/smoke-clis.py --strict` (if CLI binaries are installed)
5. `scripts/deploy-surfaces.sh --dry-run --cli all --target "$HOME/tmp/llm-home"`

## Test Failure Diagnostics
- Validation failures print explicit missing/extra/invalid artifact messages from `scripts/validate-surfaces.py`.
- Smoke failures print per-tool command failures and missing slugs from `scripts/smoke-clis.py`.
- Validation provenance and tool versions are written into `.meta/manifest.json` under `validation` for audit/debug context.
