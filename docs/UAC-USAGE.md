# UAC Usage Guide

Primary shell entrypoint:

```bash
python3.11 scripts/uac-import.py --help
```

## Modes
- `import`: inspect one or more sources and emit summary, uplift, routing, manifest, and fit analysis
- `audit`: inspect existing SSOT entries and compare declared vs inferred capability and generated surfaces
- `explain`: print rubric and deployment matrix
- `plan`: show proposed SSOT landing, install target, and cross-analysis without writing files
- `apply`: planned-only for now; does not mutate files

## Source Kinds
- local file
- local folder
- raw public HTTPS URL
- GitHub repo or folder URL
- multiple `--source` values in one run

## Examples

### Single source
```bash
python3.11 scripts/uac-import.py --mode import --source /absolute/path/to/prompt.md
```

### Multi-source convergence plan
```bash
python3.11 scripts/uac-import.py --mode plan \
  --source /absolute/path/to/a.md \
  --source https://github.com/org/repo/tree/main/prompts
```

### Audit SSOT
```bash
python3.11 scripts/uac-import.py --mode audit --output table
```

### Explain rubric and wrappers
```bash
python3.11 scripts/uac-import.py --mode explain --output table
```

## What the Output Includes
- source provenance
- deterministic summary
- uplifted objective/scope/constraints
- semantic routing result
- capability classification
- layered manifest
- anti-complecting cross-analysis
- install target recommendation
- advisory orchestrator handoff contract

## Important Boundary
Capability Fabric/UAC publish advisory metadata only. They do not decide delegation or runtime routing.
