# information-relocation recipe

## Selection and inputs
Caller names information-relocation recipe, or clearly requests the donor-specific output set below. Generic docs/release review alone does not select this recipe.

- README.md
- docs/CLI-REFERENCE.md
- AGENTS.md
- .meta/surface-rules.json
- .meta/manifest.json
- scripts/build-surfaces.py
- scripts/validate-surfaces.py
- scripts/deploy-surfaces.sh


Missing inputs: Require current README and available referenced source truth. Missing new target pages are output targets, not input failure. Preserve every essential fact or record unresolved relocation; do not claim completed relocation with missing source text.

## Output precedence and authority
Only explicitly selected Docs recipe replaces default seven-section output assembly; all source/boundary/independent-review rules retain their actual triggers.

Docs explicit substantial-rewrite execution uses existing coordinator/writer/reviewer acceptance. Findings-only/ordinary recommendations/narrow formatting remain advisory. No corresponding cycle is added to GitOps.

Drafts, findings and proposed commands grant no overwrite, install, Git mutation or release authority. Read named source evidence; never invent unavailable commands or hosted results.

## Required artifacts, in order
1. docs/README_TECHNICAL.md Markdown
2. docs/ARCHITECTURE.md Markdown
3. docs/FAQ.md Markdown
4. relocation table: README topic | New docs location | Reason | Source path(s)

## Retained donor-specific obligations
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
