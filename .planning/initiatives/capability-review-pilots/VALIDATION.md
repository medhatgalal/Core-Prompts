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
- weak body set for the recovery slice: `supercharge`, `analyze-context`, `converge`
- missing capability set before recovery: `gitops-review`
- `docs-review-expert` needed a full `both` upgrade, not just a skill landing

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
- the external research was not sufficient as a direct import
- land a repo-native `gitops-review` capability with explicit operating contract, companion-skill routing, and release gates

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
- normalize the family into a repo-quality `both` capability candidate instead of applying the raw source directly

### Docs Candidate Judge Dry Run
Command shape used during drafting:
```bash
bin/uac judge --benchmark-search off --source <temp-docs-review-expert-draft>.md
```
Observed outcome:
- accepted as a candidate shape
- initial judge passes flagged missing source-fidelity markers such as `Primary Objective`

Decision:
- use the judge feedback to shape the final SSOT entry with stronger objective, examples, constraints, explicit output contract, and advisory agent contract

### UAC Template and Judge-Gate Hardening
Changes landed:
- added canonical machine-readable templates under `.meta/capability-templates/` for `skill`, `agent`, and `both`
- extended `uac_quality.py` with a `benchmark_readiness` judge
- added scorecard reporting for:
  - title clarity
  - description richness
  - intent coverage
  - boundary clarity
  - output specificity
  - metadata completeness
  - surface usability
- updated `apply` behavior so candidates that fail the benchmark gate remain in review instead of landing into SSOT

Reason:
- the previous slice proved that metadata cleanup alone does not raise weak capability bodies to the benchmark bar
- the quality gate now blocks exactly that failure mode

## Final Decisions
- land `docs-review-expert` as a new SSOT capability with `both` surfaces
- land `gitops-review` as a new SSOT capability with `both` surfaces
- treat maintainer hygiene guidance as durable support material, not the primary GitOps outcome
- keep `.planning/` as the working ledger
- do not adopt Beads or Spec-Kit in this slice
- keep durable lessons in `AGENTS.md` and `docs/MAINTAINER-HYGIENE.md`

## Local Validation Results
### Passed
- `python3 scripts/sync-surface-specs.py --refresh --timeout 60`
  - refreshed all schema-cache sources to healthy snapshots
- `python3 scripts/build-surfaces.py`
  - generated 12 SSOT entries
- `python3 scripts/validate-surfaces.py --strict`
  - passed
- `python3 scripts/smoke-clis.py`
  - completed
  - note: Gemini discovery probe timed out after 15 seconds, but smoke still completed
- `bin/uac audit --output table`
  - `docs-review-expert` and `gitops-review` are aligned as `both`
- `python3 -m pytest -q tests/test_uac_quality.py tests/test_validate_surfaces.py tests/test_capability_recovery.py`
  - `9 passed`
- `python3 -m pytest -q tests/test_uac_quality.py tests/test_validate_surfaces.py tests/test_capability_recovery.py tests/test_uac_manifest.py tests/test_uac_import.py tests/test_uac_ssot.py`
  - `34 passed`
- `python3 -m pytest -q`
  - `246 passed`

### Review Acceptance Evidence
- code review evidence:
  - `reports/code-review/20260318-capability-uplift-recovery.md`
  - outcome: no blocking findings
- docs review evidence:
  - `reports/docs-review/20260318-capability-uplift-recovery.md`
  - outcome: no blocking documentation findings

Decision:
- keep the benchmark gate intact
- proceed to PR/MR, hosted CI, merge, package, release, and install rerun once hosted CI is green
