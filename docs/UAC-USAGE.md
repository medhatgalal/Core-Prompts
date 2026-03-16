# UAC Usage Guide

Preferred shell entrypoints:

```bash
bin/uac --help
bin/capability-fabric --help
```

Direct Python entrypoint still works:

```bash
python3.11 scripts/uac-import.py --help
```

## Modes
- `import`: inspect one or more sources and emit summary, uplift, routing, manifest, fit analysis, and benchmark hints
- `audit`: inspect existing SSOT entries and compare declared vs inferred capability and generated surfaces
- `explain`: print rubric and deployment matrix
- `plan`: show proposed SSOT landing, descriptor path, install target, and cross-analysis without writing files
- `apply`: write canonical SSOT + descriptor into this repo after confirmation or `--yes`, then rebuild and validate surfaces

## Source Kinds
- local file
- local folder
- raw public HTTPS URL
- GitHub repo or folder URL
- multiple `--source` values in one run
- repomix-reduced repo inputs when `repomix` is available

## Examples

### Single source analysis
```bash
bin/uac import /absolute/path/to/prompt.md
```

### Multi-source convergence plan
```bash
bin/uac plan /absolute/path/to/a.md https://github.com/org/repo/tree/main/prompts
```

### Real apply into SSOT + descriptor
```bash
bin/uac apply /absolute/path/to/family-folder --yes
```

### Audit current library
```bash
bin/uac audit --output table
```

### Explain rubric and wrappers
```bash
bin/uac explain --output table
```

## What Apply Does
- writes canonical repo state under:
  - `ssot/<slug>.md`
  - `.meta/capabilities/<slug>.json`
- optionally writes a source-assessment note for external imports
- runs:
  - `python3.11 scripts/build-surfaces.py`
  - `python3.11 scripts/validate-surfaces.py --strict`
- does not deploy to CLI home directories automatically

## Descriptor Model
Canonical landing uses:
- human-readable SSOT markdown in `ssot/`
- machine-readable descriptor JSON in `.meta/capabilities/`

Generated CLI surfaces stay thin. Rich metadata is bundled as a resource where the surface can use it.

## Whole-Repo Behavior
Whole repos are clustered into candidate families before any landing recommendation. Mixed repos should be narrowed to one family before `apply`.

## External Benchmark Search
Default behavior:
- analyze the provided source first
- search GitHub / Google / X only when the family is generic or fit confidence is weak
- use those results as advisory uplift inputs, not as automatic replacement authority

Control flags:
- `--benchmark-search auto|always|off`
- `--use-repomix auto|always|off`

## Important Boundary
Capability Fabric/UAC publish advisory metadata only. They do not decide delegation or runtime routing.
