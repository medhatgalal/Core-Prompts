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
