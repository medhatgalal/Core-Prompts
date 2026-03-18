# Validation

## Repo Grounding
- confirmed SSOT inventory under `ssot/`
- confirmed docs split under `docs/`
- confirmed current planning model under `.planning/`
- confirmed UAC shell contract via `bin/uac` and `scripts/uac-import.py`

## External and Local Research Inputs
### Docs Review Family
- external sources:
  - `https://github.com/thibaultyou/prompt-library/tree/main/prompts/documentation_specialist_agent`
  - `https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/docs`
  - `https://diataxis.fr/`
  - `https://www.writethedocs.org/`
- local sources:
  - `~/Desktop/ai_repos/codex-settings/prompts/insight-documenter.md`
  - current repo docs hub and technical docs

### GitOps Family
- platform docs:
  - `https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners`
  - `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets`
  - `https://docs.gitlab.com/user/project/codeowners/`
  - `https://docs.gitlab.com/user/project/merge_requests/approvals/rules/`
- local sources:
  - `~/Desktop/ai_repos/gemini-cli/.gemini/skills/pr-creator/SKILL.md`
  - `~/Desktop/ai_repos/codex-settings/prompts/github-pr-reviewer.md`
  - `~/Desktop/ai_repos/gemini-cli/docs/issue-and-pr-automation.md`
  - `~/Desktop/ai_repos/beads/docs/PROTECTED_BRANCHES.md`

## UAC Evidence
### Current Repo Audit
Command:
```bash
bin/uac audit --output table
```
Result:
- benchmark anchors are strong: `architecture`, `code-review`, `resolve-conflict`, `testing`, `uac-import`
- weakest description set for this slice: `supercharge`, `analyze-context`, `converge`

### GitOps Candidate Intake
Command:
```bash
bin/uac plan --benchmark-search off \
  --source ~/Desktop/ai_repos/gemini-cli/.gemini/skills/pr-creator/SKILL.md \
  --source ~/Desktop/ai_repos/codex-settings/prompts/github-pr-reviewer.md
```
Observed outcome:
- accepted as a reusable skill family
- proposed slug from raw UAC grouping was generic (`multi-source-import`)
- useful as evidence that the prompt-like material is reusable
- not good enough as-is for direct landing under the desired GitOps family name

Decision:
- use the research to drive durable maintainer guidance and selective SSOT uplift, not a direct SSOT landing in this slice

### Docs Candidate Intake
Command:
```bash
bin/uac plan --benchmark-search off \
  --source https://raw.githubusercontent.com/thibaultyou/prompt-library/main/prompts/documentation_specialist_agent/prompt.md \
  --source https://raw.githubusercontent.com/harish-garg/gemini-cli-prompt-library/main/commands/docs/write-readme.toml
```
Observed outcome:
- rejected for direct landing
- the external material was too template-heavy / weakly structured for UAC's intent-bearing threshold

Decision:
- normalize the family into a repo-quality skill candidate instead of applying the raw source directly

### Docs Candidate Judge Dry Run
Command shape used during drafting:
```bash
bin/uac judge --benchmark-search off --source <temp-docs-review-expert-draft>.md
```
Observed outcome:
- accepted as a candidate shape
- initial judge passes flagged missing source-fidelity markers such as `Primary Objective`

Decision:
- use the judge feedback to shape the final SSOT entry with stronger objective, examples, constraints, and explicit output contract

## Final Decisions
- land `docs-review-expert` as a new SSOT skill
- land GitOps outcomes as maintainer guidance plus SSOT description uplifts
- keep `.planning/` as the working ledger
- do not adopt Beads or Spec-Kit in this slice

## Local Validation Results
### Passed
- `python3 scripts/build-surfaces.py`
  - generated 11 SSOT entries
- `python3 scripts/validate-surfaces.py --strict`
  - passed
- `python3 scripts/smoke-clis.py`
  - completed
  - note: Gemini discovery probe timed out after 15 seconds, but smoke still completed
- `bin/uac audit --output table`
  - `docs-review-expert` is aligned as `skill`
- `python3 -m pytest -q tests/test_validate_surfaces.py`
  - `2 passed`
- `python3 -m pytest -q tests/test_uac_ssot.py`
  - `7 passed`

### Inconclusive In This Environment
- `python3 -m pytest -q`
  - started and made progress, then stalled without clean completion
- `python3 -m pytest -q tests/test_uac_manifest.py`
  - started and made progress, then stalled without clean completion

Decision:
- treat strict validation, smoke, and targeted passing tests as the current evidence set for this slice
- do not claim full-suite green until the hanging pytest behavior is understood
