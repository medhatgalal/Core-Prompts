# FAQ

## What should I edit when I want behavior changes?

Edit files in `ssot/`. Generated surfaces are derived artifacts and should not be hand-edited.

## How do I regenerate everything?

Run:

```bash
python3 scripts/build-surfaces.py
python3 scripts/validate-surfaces.py --strict
```

## Why did validation fail with missing artifacts?

Most often the build step was not run after SSOT changes. Re-run build, then validate again.

## Do I need all CLI binaries installed?

No. CLI binaries are only required for local smoke checks and strict CLI validation/deployment scenarios.

## What does deploy do?

`scripts/deploy-surfaces.sh` performs copy-only deployment of managed files to a target root (default `~`). It does not create symlinks.

## How do Codex sub-agents get registered?

For SSOT entries marked as agent (`kind: agent` or `role: agent`), deployment writes managed `[agents.<slug>]` entries in `<target>/.codex/config.toml` with `config_file` paths to generated `.codex/agents/<slug>.toml`.

## Where can I find technical details?

Use:

- `docs/GETTING-STARTED.md`
- `docs/CLI-REFERENCE.md`
- `docs/ARCHITECTURE.md`
- `docs/prompt-pack/README.md`
