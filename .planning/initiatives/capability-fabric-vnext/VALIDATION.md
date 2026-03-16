# Capability Fabric vNext Validation

## Required Commands
- `python3.11 -m pytest -q`
- `python3.11 -m compileall src tests scripts bin`
- `python3.11 scripts/build-surfaces.py`
- `python3.11 scripts/validate-surfaces.py --strict`
- `python3.11 scripts/uac-import.py --mode audit --output table`
- `bin/uac plan https://github.com/harish-garg/gemini-cli-prompt-library`
- `bin/uac apply https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture --yes --benchmark-search off --use-repomix off`
- `bin/uac apply https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/testing --yes --benchmark-search off --use-repomix off`

## Evidence To Capture
- Manifest layering present in import payloads
- Cross-analysis present in import and audit payloads
- Install-target recommendation present in plan payloads
- Handoff contract present in import and audit payloads
- Real `apply` writes SSOT + descriptor and rebuilds surfaces
- Descriptor resources are bundled into generated skill/agent surfaces
- Whole-repo Harish Garg import clusters into family candidates
- No payload claims orchestration ownership

## Actual Results
- `python3.11 -m pytest -q` -> `222 passed`
- `python3.11 -m compileall src tests scripts bin` -> passed
- `python3.11 scripts/build-surfaces.py` -> generated `10` SSOT entries and refreshed `.meta/capability-handoff.json`
- `python3.11 scripts/validate-surfaces.py --strict` -> passed
- `python3.11 scripts/uac-import.py --mode audit --output table` -> SSOT audit rendered with fit analysis for `10` entries
- `bin/uac plan https://github.com/harish-garg/gemini-cli-prompt-library` -> clustered the repo into `architecture`, `code-review`, `debugging`, `docs`, `learning`, `prompts`, and `testing`
- `bin/uac apply .../commands/architecture` -> landed `ssot/architecture.md`, `.meta/capabilities/architecture.json`, and `.meta/capabilities/architecture.sources.md`
- `bin/uac apply .../commands/testing` -> landed `ssot/testing.md`, `.meta/capabilities/testing.json`, and `.meta/capabilities/testing.sources.md`
- architecture family was manually uplifted after apply to replace the raw scaffold with a black-box-oriented family entry
- testing family was manually uplifted after apply to replace the raw scaffold with a framework-aware testing family entry
