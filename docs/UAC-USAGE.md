# UAC Usage Guide

Preferred shell entrypoints:

```bash
bin/uac --help
bin/capability-fabric --help
```

Direct Python entrypoint still works:

```bash
python3 scripts/uac-import.py --help
```

## Modes
- `import`: inspect sources without mutating repo state
- `audit`: review current SSOT entries and generated surfaces
- `explain`: print rubric and deployment matrix
- `plan`: show the proposed landing shape without writing files
- `judge`: run the quality loop without landing repo state
- `apply`: write canonical SSOT + descriptor state after confirmation or `--yes`, then rebuild and validate

## Typical Flow
```bash
bin/uac import /absolute/path/to/prompt.md
bin/uac plan /absolute/path/to/family-folder
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
bin/uac apply /absolute/path/to/family-folder --yes
```

## Source Kinds
- local file
- local folder
- raw public HTTPS URL
- GitHub repo or folder URL
- multiple `--source` values in one run
- repomix-reduced repo inputs

## What `apply` Does
- writes canonical repo state under:
  - `ssot/<slug>.md`
  - `.meta/capabilities/<slug>.json`
- materializes or preserves the fidelity baseline source under:
  - `sources/ssot-baselines/<slug>/baseline.md`
- may persist quality-review artifacts under `reports/quality-reviews/`
- runs:
  - `bin/capability-fabric build`
  - `bin/capability-fabric validate --strict`
- does not deploy to CLI homes automatically

## What `judge` Does
- selects a quality profile
- resolves the canonical baseline source from `sources/ssot-baselines/`
- evaluates the candidate against benchmark rules
- returns pass/fail evidence and judge reports
- refuses canonical landing until status is `ship`

## Important Boundary
UAC publishes advisory metadata only. It does not decide delegation or runtime routing.

## Direct Surface Outcome
When a capability is classified for direct exposure, the generated direct surface lands in each vendor `skills/<slug>/SKILL.md` path. UAC does not target direct `commands/` or `prompts/` deployment paths in this repo.

## Related Docs
- [Getting started](GETTING-STARTED.md)
- [UAC capability model](UAC-CAPABILITY-MODEL.md)
- [Baseline source library](../sources/ssot-baselines/README.md)
- [Orchestrator contract](ORCHESTRATOR-CONTRACT.md)
- [CLI reference](CLI-REFERENCE.md)
