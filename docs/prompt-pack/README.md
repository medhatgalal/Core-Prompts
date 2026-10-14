# Docs Evolution Prompt Pack

This pack helps you evolve this repository's documentation into a more approachable, marketing-grade experience while staying factual and verifiable.

It supports two operating modes:

1. Together: run one orchestrator prompt for end-to-end output.
2. Separately: run modular prompts A-E in sequence or as needed.

For everyday onboarding, use the [Getting Started fast/safe paths](../GETTING-STARTED.md)
and [conditional skill flows](../SKILL-FLOWS.md). To author that documentation,
request the existing Docs Review `ai-onboarding` recipe, which returns the README
snippet followed by a full Getting Started draft. All seven prompts below remain
callable; the [recipe mapping and fallback](../EXAMPLES.md#seven-retained-prompt-donors)
retains their exact output contracts. No donor retirement or rename is part of
these documentation changes.

## Files

- `prompts/master-orchestrator.md`
- `prompts/prompt-a-readme-story.md`
- `prompts/prompt-b-ai-install-flow.md`
- `prompts/prompt-c-technical-extraction.md`
- `prompts/prompt-d-visuals.md`
- `prompts/prompt-e-factual-gate.md`
- `prompts/prompt-f-evaluate-and-ship-gate.md`

## Defaults (Locked)

- Tone mode: balanced warmth
- Image strategy: mixed visuals
- README remains concise and navigational
- Technical depth lives under `docs/`
- No invented capabilities, flags, or commands

## Use Together (Single-Pass)

Use this when you want a full draft set in one run.

1. Open `prompts/master-orchestrator.md`.
2. Paste into your AI tool.
3. Set `repo_path` to this repository path.
4. Keep defaults unless you have a reason to override audience.

Expected outputs:

- `README_vNext.md`
- `docs/README_TECHNICAL.md`
- `visuals_plan.md`
- `factual_audit.json`

## Use Separately (Modular)

Use this when you want tighter control by phase.

Recommended sequence:

1. Prompt A: README narrative and value framing.
2. Prompt B: "point AI at repo and install" flow.
3. Prompt C: move technical depth to docs.
4. Prompt D: visuals and diagram guidance.
5. Prompt E: factual gate and consistency review.
6. Prompt F (optional): adversarial ship gate for commit/push/tag/package readiness.

## Operator Checklist

Use this before publishing docs updates:

- Purpose is clear in first screenful.
- "Get started in 2 minutes" appears near top.
- README links to exact docs pages for deeper detail.
- Every command appears in repo scripts/docs.
- No unsupported CLIs or fabricated features are mentioned.
- All visuals include meaningful alt text.
- Mermaid diagram reflects actual build/validate/deploy flow.
- Factual audit maps all claims to concrete repo paths.

## Suggested Handoff Snippet

Use this when handing the repo to an AI assistant:

```text
You are working in <repo_path>/Core-Prompts.
Use docs/prompt-pack/prompts/master-orchestrator.md.
Keep tone as balanced warmth, visuals as mixed strategy, and enforce factual claims from local files only.
Output README_vNext.md, docs/README_TECHNICAL.md, visuals_plan.md, and factual_audit.json.
```

## Optional installed-skill recipes

The seven prompt files above remain unchanged and callable. For the same bounded artifact jobs through existing skills, see [documentation recipe examples](../EXAMPLES.md#optional-documentation-recipes). Docs Review provides docs-bundle, readme-authoring, ai-onboarding, information-relocation, document-visuals, factual-audit and adversarial-doc-review. GitOps Review supplies the candidate-bound docs-release-readiness companion. The historical Prompt F tag-before-package/origin-only command text is retained as source history; the additive F recipe uses current verified package-before-tag and dual-remote ordering. No release or installation is performed by selecting a recipe.
