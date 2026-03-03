# Getting Started

This guide is the fastest safe path to generate, validate, and optionally deploy surfaces from SSOT.

## Prerequisites

- Python 3.11+
- Repository checked out locally
- Optional CLI binaries if you plan to run smoke checks or targeted deployment:
  - `codex`
  - `gemini`
  - `claude`
  - `kiro-cli`

## Fast Path (2-5 minutes)

1. Enter repo root:

```bash
cd /Users/medhat.galal/Desktop/Core-Prompts
```

2. Build generated outputs:

```bash
python3 scripts/build-surfaces.py
```

3. Validate generated artifacts:

```bash
python3 scripts/validate-surfaces.py --strict
```

4. Optional smoke checks (requires installed CLIs):

```bash
python3 scripts/smoke-clis.py --strict
```

5. Optional dry-run deployment:

```bash
scripts/deploy-surfaces.sh --dry-run --cli all
```

## Safe Path (with explicit schema refresh)

Use this when vendor schema snapshots may be stale:

```bash
python3 scripts/sync-surface-specs.py --refresh
python3 scripts/build-surfaces.py
python3 scripts/validate-surfaces.py --strict --with-cli
python3 scripts/smoke-clis.py --strict
scripts/deploy-surfaces.sh --dry-run --cli all
```

## AI Handoff Snippet

Paste this into your AI tool when you want guided repo operation:

```text
You are working in /Users/medhat.galal/Desktop/Core-Prompts.
Treat ssot/ as source of truth and generated outputs under .codex/, .gemini/, .claude/, .kiro/ as derived artifacts.
When making behavior changes, edit ssot files first, then run build and validate.
Do not hand-edit generated surfaces.
```

## Success Checklist

- `python3 scripts/build-surfaces.py` completes without errors.
- `python3 scripts/validate-surfaces.py --strict` passes.
- If smoke checks run, expected slugs are discoverable in local CLIs.
- Dry-run deployment shows the intended managed file copies.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `No SSOT files found in ssot/` | wrong working directory | run commands from repo root |
| `Python 3.11+ required` | older interpreter in PATH | use Python 3.11+ explicitly |
| validation fails for missing artifacts | build step not run or partial outputs | run `python3 scripts/build-surfaces.py` then validate again |
| `missing CLI binary` warnings | local CLI not installed | install the CLI or run without strict CLI checks |
