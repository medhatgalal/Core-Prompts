# Getting Started

This is the shortest safe path to build, validate, and inspect Capability Fabric outputs.

## Prerequisites
- Python `3.14` preferred, Python `3.11+` supported
- repository checked out locally
- optional CLI binaries if you want smoke checks or deploy dry-runs

Preferred entrypoints:
- `bin/capability-fabric` for build, validate, and deploy
- `bin/uac` for import, plan, judge, and apply

These wrappers choose the highest available supported Python runtime automatically. If you need to pin one explicitly, set `PYTHON_BIN=python3.11` or `PYTHON_BIN=python3.14`.

## Fast Path
```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
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
bin/capability-fabric deploy --dry-run --cli all
```

Home-targeted dry run:
```bash
scripts/install-local.sh --dry-run --target "$HOME" --allow-nonlocal-target
```

## Direct Surface Standard
Direct exposure is skill-only for all supported CLIs:
- `.codex/skills/<slug>/SKILL.md`
- `.gemini/skills/<slug>/SKILL.md`
- `.claude/skills/<slug>/SKILL.md`
- `.kiro/skills/<slug>/SKILL.md`

This repo does not deploy direct surfaces to vendor `commands/` or `prompts/` directories.

## Next Docs
- [Examples](EXAMPLES.md)
- [FAQ](FAQ.md)
- [CLI reference](CLI-REFERENCE.md)
