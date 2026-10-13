# ai-onboarding recipe

## Selection and inputs
Caller names ai-onboarding recipe, or clearly requests the donor-specific output set below. Generic docs/release review alone does not select this recipe.

- README.md
- docs/CLI-REFERENCE.md
- CONTRIBUTING.md
- scripts/deploy-surfaces.sh
- scripts/install-local.sh
- scripts/validate-surfaces.py


Missing inputs: Require actual install/deploy/validation docs/scripts. A missing obsolete path may be mapped to a verified current path with an explicit difference; if first-run commands cannot be verified, return blocked drafting with exact missing facts, not guessed tools.

## Output precedence and authority
Only explicitly selected Docs recipe replaces default seven-section output assembly; all source/boundary/independent-review rules retain their actual triggers.

Docs explicit substantial-rewrite execution uses existing coordinator/writer/reviewer acceptance. Findings-only/ordinary recommendations/narrow formatting remain advisory. No corresponding cycle is added to GitOps.

Drafts, findings and proposed commands grant no overwrite, install, Git mutation or release authority. Read named source evidence; never invent unavailable commands or hosted results.

## Required artifacts, in order
1. Section 1: README Use this with AI snippet only
2. Section 2: full docs/GETTING-STARTED.md Markdown

## Retained donor-specific obligations
# Prompt B: AI Install and Onboarding Flow

```text
You are optimizing the onboarding path so someone can point an AI at this repo and get started safely and correctly.

## Scope
Produce two artifacts:
1) README section: "Use this with AI"
2) docs/GETTING-STARTED.md draft

## Goals
- Minimize setup friction.
- Keep steps deterministic.
- Make AI handoff explicit and reusable.

## Hard Rules
1) Only include commands that exist in repo docs/scripts.
2) Do not assume global tools beyond what is documented.
3) Keep first-run path to 2-5 steps.
4) Add failure recovery hints for missing binaries and validation errors.

## Inputs to Inspect
- README.md
- docs/CLI-REFERENCE.md
- CONTRIBUTING.md
- scripts/deploy-surfaces.sh
- scripts/install-local.sh
- scripts/validate-surfaces.py

## Required Output Details
- A copy-paste AI handoff block.
- A "Fast path" and a "Safe path" flow.
- One troubleshooting mini-table (symptom, likely cause, action).
- A clear "what success looks like" checklist.

## Output Format
- Section 1: README snippet only.
- Section 2: full docs/GETTING-STARTED.md Markdown.
```
