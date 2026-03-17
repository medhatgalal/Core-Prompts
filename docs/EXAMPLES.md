# Examples

## UAC Import an External Prompt
```bash
bin/uac import /absolute/path/to/prompt.md
```
Expected result:
- summary
- uplift
- capability recommendation
- install-target recommendation
- advisory handoff preview

## UAC Plan a Family Landing
```bash
bin/uac plan https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture
```
Expected result:
- clustered family recommendation
- descriptor/SSOT landing plan
- overlap/conflict analysis
- benchmark hints

## UAC Judge Without Landing
```bash
bin/uac judge /absolute/path/to/family-folder --quality-profile architecture
```
Expected result:
- quality status
- judge reports
- blockers or ship decision
- no canonical repo mutation

## Audit Current SSOT
```bash
bin/uac audit --output table
```
Expected result:
- one row per SSOT entry
- declared vs inferred capability
- surface alignment status

## Release Validation Loop
```bash
python3 scripts/build-surfaces.py
python3 scripts/validate-surfaces.py --strict
python3 scripts/smoke-clis.py
scripts/deploy-surfaces.sh --dry-run --cli all
```
