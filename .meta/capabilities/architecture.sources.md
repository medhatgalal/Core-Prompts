# architecture source assessment

## Imported Sources
- `https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture`
- `https://raw.githubusercontent.com/Alexanderdunlop/ai-architecture-prompts/main/prompts/claude-code-prompt.md`
- `https://raw.githubusercontent.com/Alexanderdunlop/ai-architecture-prompts/main/prompts/claude-prompt.md`
- `https://raw.githubusercontent.com/Alexanderdunlop/ai-architecture-prompts/main/prompts/cursor-prompt.md`

## Benchmarks
- `ssot/code-review.md`
- `ssot/resolve-conflict.md`

## Benchmark Findings
- Harish architecture files provide useful practical mode decomposition and implementation-facing guidance.
- Alexanderdunlop prompts contribute stronger black-box, replaceability, and maintainability framing.
- `code-review` contributes strict checklist behavior, objective-by-objective review blocks, and explicit decision headings.
- `resolve-conflict` contributes explicit failure-mode thinking, inversion-style checks, and deterministic alternatives handling.
- Combined outcome: deterministic architecture skill with explicit scorecard, failure handling, and migration/rollback requirements.

## Rationale
Preserve the four-mode structure from Harish Garg, then uplift each mode with:
- explicit acceptance criteria
- scorecard requirement
- failure and rollback handling
- benchmark alignment checks against code-review and resolve-conflict behavior templates
