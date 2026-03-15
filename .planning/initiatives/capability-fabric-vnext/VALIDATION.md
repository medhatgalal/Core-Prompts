# Capability Fabric vNext Validation

## Required Commands
- `python3.11 -m pytest -q`
- `python3.11 -m compileall src tests scripts`
- `python3.11 scripts/build-surfaces.py`
- `python3.11 scripts/validate-surfaces.py --strict`
- `python3.11 scripts/uac-import.py --mode audit --output table`
- `python3.11 scripts/uac-import.py --mode plan --source <fileA> --source <fileB>`

## Evidence To Capture
- Manifest layering present in import payloads
- Cross-analysis present in import and audit payloads
- Install-target recommendation present in plan payloads
- Handoff contract present in import and audit payloads
- No payload claims orchestration ownership

## Actual Results
- `python3.11 -m pytest -q` -> `218 passed`
- `python3.11 -m compileall src tests scripts` -> passed
- `python3.11 scripts/build-surfaces.py` -> generated 8 SSOT entries and refreshed `.meta/capability-handoff.json`
- `python3.11 scripts/validate-surfaces.py --strict` -> passed
- `python3.11 scripts/uac-import.py --mode audit --output table` -> SSOT audit rendered with fit analysis
- Harish Garg architecture family recorded as `skill_family` / `architecture`
- Alexanderdunlop architecture repo recorded as `skill_family` / `ai-architecture-prompts`
