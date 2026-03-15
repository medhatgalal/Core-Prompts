# UAC Usage Guide

Primary shell entrypoint:

```bash
python3.11 scripts/uac-import.py --help
```

## Modes

### `import`
Import one file, folder, raw URL, or GitHub tree and return a deterministic UAC result.

```bash
python3.11 scripts/uac-import.py --mode import --source /absolute/path/to/prompt.md
python3.11 scripts/uac-import.py --mode import --source https://raw.githubusercontent.com/org/repo/main/file.md
python3.11 scripts/uac-import.py --mode import --source https://github.com/org/repo/tree/main/prompts --show-rubric
```

### `audit`
Audit existing SSOT entries and compare declared capability vs inferred capability vs generated surfaces.

```bash
python3.11 scripts/uac-import.py --mode audit --source ssot
python3.11 scripts/uac-import.py --mode audit --output table
```

### `explain`
Print the capability rubric and deployment matrix.

```bash
python3.11 scripts/uac-import.py --mode explain
python3.11 scripts/uac-import.py --mode explain --output table
```

### `plan`
Show how a source would land in SSOT without writing files.

```bash
python3.11 scripts/uac-import.py --mode plan --source /absolute/path/to/folder
```

### `apply`
Reserved for future mutation flow. For now it returns a planned-only result and does not write files.

```bash
python3.11 scripts/uac-import.py --mode apply --source /absolute/path/to/prompt.md
```

## Accepted Source Types

- local file path
- local folder path
- raw public HTTPS URL
- GitHub repo or folder URL
- `ssot` path for audit mode

## What the Output Tells You

For imports:
- normalized source provenance
- clean summary
- uplifted objective/scope
- routing result
- capability type and rationale
- emitted surfaces by CLI
- modernization focus
- next actions

For audits:
- declared capability
- inferred capability
- expected surfaces
- actual surfaces
- alignment status and issues

## When UAC Refuses Automatic Deployment

UAC holds the source in `manual_review` when it cannot classify safely.

Common reasons:
- config-only wrapper without a strong prompt body
- missing objective/scope structure
- conflicting signals that would make deployment ambiguous
