# Prompt C: Technical Detail Extraction into docs/

```text
You are restructuring documentation by moving technical depth out of README into docs/ while keeping cross-links precise.

## Scope
Produce:
1) docs/README_TECHNICAL.md
2) docs/ARCHITECTURE.md
3) docs/FAQ.md
4) A relocation table showing what moved from README to docs

## Information Architecture Targets
- docs/GETTING-STARTED.md: onboarding and practical use
- docs/CLI-REFERENCE.md: CLI specifics and commands
- docs/ARCHITECTURE.md: SSOT, generation, validation, deployment internals
- docs/FAQ.md: common issues and fixes

## Hard Rules
1) Keep README high-level and task-oriented.
2) Move dense operational detail into docs pages.
3) Preserve all essential technical facts.
4) Every docs section must have an owner path to source truth (file references).

## Inputs to Inspect
- README.md
- docs/CLI-REFERENCE.md
- AGENTS.md
- .meta/surface-rules.json
- .meta/manifest.json
- scripts/build-surfaces.py
- scripts/validate-surfaces.py
- scripts/deploy-surfaces.sh

## Output Format
1) Markdown for each target file.
2) Relocation table with columns:
   - "README topic"
   - "New docs location"
   - "Reason"
   - "Source path(s)"
```
