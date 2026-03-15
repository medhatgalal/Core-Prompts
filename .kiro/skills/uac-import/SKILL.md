---
name: "uac-import"
description: "Import one external prompt/spec source into the deterministic UAC uplift and packaging flow."
---
# UAC Import

## Purpose
Take one external source or the existing `ssot/` directory and turn it into a deterministic UAC assessment.

Supported inputs:
- local file path
- local folder path
- raw public HTTPS URL
- GitHub repo or folder URL
- existing `ssot/` directory for audit mode

Supported modes:
- `import`
- `audit`
- `explain`
- `plan`
- `apply` (planned-only until a safe mutation flow is added)

For the given source, perform this workflow in order:
1. Ingest the source through the existing deterministic pipeline.
2. Produce the clean intent summary.
3. Run uplift to extract objective, scope, and constraints.
4. Run semantic routing.
5. If the source is a folder or repo subtree, inventory prompt-like files and classify them one by one.
6. Aggregate the collection into a skill-family, agent-family, or manual-review recommendation.
7. Classify each accepted source as `skill`, `agent`, `both`, or `manual_review`.
8. Derive emitted surfaces for Codex, Gemini, Claude, and Kiro from that capability type.
9. Propose modernization focus areas so the source can be uplifted, reorganized, and packaged cleanly.
10. For `audit`, compare declared SSOT capability, inferred capability, and generated surfaces.

## Rules
- Prefer existing pipeline code over ad-hoc parsing.
- Keep results deterministic and roleplay-free.
- Fail closed for unsuitable URL content.
- For folders or repo trees, only group files that were actually inventoried.
- If the source is config-only, say so and require manual review instead of pretending it is a prompt.
- If the source is already an agent definition, preserve its control-plane boundaries.
- Expose the classification rubric and scorecard when the user asks how the decision was made.

## Required Output
Return a concise structured result with these sections:
- Source
- Summary
- Uplift
- Routing
- UAC Classification
- Collection Recommendation
- Recommended Surface
- Modernization Focus
- Next Actions

## Good Outcome
A good result tells the user:
- what the source is
- whether it should become a skill, an agent, or both
- which target systems are appropriate
- what to preserve while uplifting it
- what needs manual review before packaging

## Constraints
- No hidden execution.
- No packaging claims without evidence.
- No generated surface edits unless the user explicitly asks for them.
- For local folders or GitHub folders, inventory the files first and then justify whether they belong under one roof.
