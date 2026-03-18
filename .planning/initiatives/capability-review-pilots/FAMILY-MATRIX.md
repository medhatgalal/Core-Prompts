# Family Matrix

| Family | Primary Need | Strongest External Inputs | Strongest Local Inputs | UAC Intake Outcome | Landing Decision |
| --- | --- | --- | --- | --- | --- |
| docs-review-expert | docs IA, readability, anti-drift review, file placement, review timing | `documentation_specialist_agent/prompt.md`, Gemini docs-writing prompts, Diataxis | `insight-documenter`, current docs hub, README structure | raw external prompt is too weakly structured for direct landing; normalized draft is a viable skill candidate | land as new SSOT skill |
| gitops-design-hygiene | review timing, protected-branch hygiene, CI/release gates, GitHub/GitLab parity | GitHub CODEOWNERS/rulesets docs, GitLab Code Owners/approval rules docs | `pr-creator`, `github-pr-reviewer`, `issue-and-pr-automation.md`, Beads protected-branch guidance | prompt-like sources are reusable, but the highest-value output for this repo is durable maintainer guidance | land as maintainer rules + selective SSOT uplift |
