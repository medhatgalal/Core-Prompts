# Getting Started

This is the shortest safe path to build, validate, and inspect Capability Fabric outputs.

## Prerequisites
- Python `3.14` preferred, Python `3.11+` supported
- repository checked out locally
- optional CLI binaries if you want smoke checks or deploy dry-runs

If `python3` on your machine is older than `3.11`, run the commands below with `python3.14` instead.

## Fast Path
```bash
python3 scripts/build-surfaces.py
python3 scripts/validate-surfaces.py --strict
python3 scripts/smoke-clis.py
```

## UAC Fast Path
```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
```

Use `apply` only when you want canonical repo state to change:
```bash
bin/uac apply /absolute/path/to/family-folder --yes
```

## Success Checklist
- build completes
- strict validation passes
- smoke checks pass when local CLIs are installed
- dry-run deploy shows the intended copies

## Deploy Modes
Repo-local dry run:
```bash
scripts/deploy-surfaces.sh --dry-run --cli all
```

Home-targeted dry run:
```bash
scripts/install-local.sh --dry-run --target "$HOME" --allow-nonlocal-target
```

## Next Docs
- [Examples](EXAMPLES.md)
- [FAQ](FAQ.md)
- [CLI reference](CLI-REFERENCE.md)
