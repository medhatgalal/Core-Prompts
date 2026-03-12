---
description: "Import one external prompt/spec source into the deterministic UAC uplift and packaging flow."
---

# UAC Import

## Purpose
Take one external source and turn it into a deterministic UAC assessment.

Supported inputs:
- local file path
- raw public HTTPS URL

For the given source, perform this workflow in order:
1. Ingest the source through the existing deterministic pipeline.
2. Produce the clean intent summary.
3. Run uplift to extract objective, scope, and constraints.
4. Run semantic routing.
5. Classify the source as skill-like, agent-like, config-like, or manual-review.
6. Recommend the best target surface for Codex, Gemini, Claude, and Kiro.
7. Propose modernization focus areas so the source can be uplifted, reorganized, and packaged cleanly.

## Rules
- Prefer existing pipeline code over ad-hoc parsing.
- Keep results deterministic and roleplay-free.
- Fail closed for unsuitable URL content.
- Do not claim folder-level grouping unless multiple files were explicitly provided.
- If the source is config-only, say so and require manual review instead of pretending it is a prompt.
- If the source is already an agent definition, preserve its control-plane boundaries.

## Required Output
Return a concise structured result with these sections:
- Source
- Summary
- Uplift
- Routing
- UAC Classification
- Recommended Surface
- Modernization Focus
- Next Actions

## Good Outcome
A good result tells the user:
- what the source is
- whether it should become a skill or an agent
- which target systems are appropriate
- what to preserve while uplifting it
- what needs manual review before packaging

## Constraints
- No hidden execution.
- No packaging claims without evidence.
- No generated surface edits unless the user explicitly asks for them.
- If given a local directory instead of a file, ask for the exact file or explain that multi-file grouping is a separate workflow.
