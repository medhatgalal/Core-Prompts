# document-visuals recipe

## Selection and inputs
Caller names document-visuals recipe, or clearly requests the donor-specific output set below. Generic docs/release review alone does not select this recipe.

- README.md
- docs/CLI-REFERENCE.md
- docs/ARCHITECTURE.md (if present)
- scripts/build-surfaces.py
- scripts/validate-surfaces.py
- scripts/deploy-surfaces.sh


Missing inputs: Require actual component evidence. docs/ARCHITECTURE.md is optional if absent; use verified source components, otherwise mark insufficient diagram evidence. Screenshot slots remain optional, max3; no screenshot tool requirement.

## Output precedence and authority
Only explicitly selected Docs recipe replaces default seven-section output assembly; all source/boundary/independent-review rules retain their actual triggers.

Docs explicit substantial-rewrite execution uses existing coordinator/writer/reviewer acceptance. Findings-only/ordinary recommendations/narrow formatting remain advisory. No corresponding cycle is added to GitOps.

Drafts, findings and proposed commands grant no overwrite, install, Git mutation or release authority. Read named source evidence; never invent unavailable commands or hosted results.

## Required artifacts, in order
1. visuals_plan.md: Hero concept; Mermaid complete code and each node/edge explanation; optional screenshot slots max3; accessibility notes

## Retained donor-specific obligations
# Prompt D: Visuals and Diagram Guidance

```text
You are creating a visual plan that improves comprehension and trust, not decoration.

## Scope
Produce visuals_plan.md only.

## Locked Strategy
- Mixed visuals:
  1) one hero image concept
  2) one Mermaid architecture diagram
  3) optional screenshot placeholders

## Hard Rules
1) Each visual must teach something specific.
2) Every visual must include precise alt text.
3) Do not add visuals that imply unverified features.
4) Diagram nodes and labels must match real repository components.

## Inputs to Inspect
- README.md
- docs/CLI-REFERENCE.md
- docs/ARCHITECTURE.md (if present)
- scripts/build-surfaces.py
- scripts/validate-surfaces.py
- scripts/deploy-surfaces.sh

## Required visuals_plan.md Structure
1) Hero image concept:
   - objective
   - visual composition
   - caption
   - alt text
2) Mermaid diagram:
   - include complete diagram code block
   - include explanation for each node/edge
3) Screenshot slots (optional, max 3):
   - filename suggestion
   - capture target
   - alt text
   - instructional value
4) Accessibility notes:
   - contrast and readability guidance
   - mobile rendering considerations
```
