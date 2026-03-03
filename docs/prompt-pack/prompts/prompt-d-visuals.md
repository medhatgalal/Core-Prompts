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
