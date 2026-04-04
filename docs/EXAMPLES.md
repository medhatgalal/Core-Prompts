# Examples

Use this page to see the product surface first, then the maintainer and ingestion flows.

## Installed Skill Examples

### Improve a system with `autosearch`
Use the deployed skill when you want measurable improvement rather than one-shot edits.

Example request:
> Use `autosearch` to improve our review prompt so it catches more behavioral regressions without increasing review noise.

Expected result:
- a clarified goal contract
- baseline and evaluation criteria
- bounded experiment plan
- promotion-ready guidance only after a verified winner exists

### Harden a plan with `supercharge`
Use the deployed skill when a request is underspecified, risky, or likely to produce weak execution.

Example request:
> Use `supercharge` to turn this rough idea into a concrete implementation plan with tradeoffs and failure modes.

Expected result:
- sharper problem framing
- decomposed plan
- clearer constraints and acceptance criteria
- a stronger execution-ready brief

### Converge competing options with `converge`
Use the deployed skill when multiple proposals or sources need one coherent recommendation.

Example request:
> Use `converge` to compare these three approaches and recommend one final architecture with rationale.

Expected result:
- conflicts surfaced explicitly
- tradeoffs compared on common criteria
- one recommendation with open risks

### Review documentation with `docs-review-expert`
Use the deployed skill when docs feel bloated, duplicated, or unclear.

Example request:
> Use `docs-review-expert` to tell me what belongs in `README.md` versus `docs/`, what drifted, and what to fix first.

Expected result:
- file-placement decisions
- drift findings
- section-level rewrite guidance
- review timing recommendations

## Maintainer / Repo Examples

These are for changing canonical capability source, descriptors, generated surfaces, or release state.

### Import an external prompt family
```bash
bin/uac import /absolute/path/to/prompt.md
```

Expected result:
- summary
- uplift
- capability recommendation
- install-target recommendation
- advisory handoff preview

### Plan a landing before writing repo state
```bash
bin/uac plan https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture
```

Expected result:
- clustered family recommendation
- descriptor and SSOT landing plan
- overlap and conflict analysis
- benchmark hints

### Judge before apply
```bash
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
```

Expected result:
- quality status
- judge reports
- blockers or ship decision
- no canonical repo mutation

### Audit current canonical state
```bash
bin/uac audit --output table
```

Expected result:
- one row per SSOT entry
- declared vs inferred capability
- surface alignment status

### Build, validate, and deploy after review
```bash
bin/capability-fabric build
bin/capability-fabric validate --strict
scripts/deploy-surfaces.sh --cli all --slug autosearch --target "$HOME" --allow-nonlocal-target --dry-run
```

Expected result:
- regenerated surfaces
- strict validation pass
- an explicit copy plan for the selected capability
