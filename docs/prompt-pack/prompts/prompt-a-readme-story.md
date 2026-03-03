# Prompt A: README Story + Value Framing

```text
You are rewriting README.md for clarity and approachability while preserving factual accuracy.

## Scope
Produce only README_vNext.md content.

## Tone
- Balanced warmth: clear, inviting, practical.
- No fluff or over-claiming.

## Non-Negotiable Rules
1) Do not invent capabilities or outcomes.
2) Keep README concise and navigational.
3) Link deeper details to docs pages instead of embedding everything.
4) Keep commands minimal and verifiable.

## Required README Sections
1) Hero: what this repo does and who it is for.
2) Get started in 2 minutes.
3) Use this with AI (copy-paste handoff).
4) What you get.
5) Where technical details live.
6) Next steps.

## Inputs to Inspect
- README.md
- docs/CLI-REFERENCE.md
- AGENTS.md
- scripts/build-surfaces.py
- scripts/validate-surfaces.py
- scripts/deploy-surfaces.sh

## Output Format
- Return only Markdown for README_vNext.md.
- At end, append a short "Claim Notes" list mapping major claims to file paths.
```
