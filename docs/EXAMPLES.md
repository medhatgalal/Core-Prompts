# Full Run Examples

This page provides full run patterns for each core prompt in this repository.

## Notes Before You Run

- Command prefix differs by tool (`$name`, `/name`, or plain command form).
- Examples focus on workflow shape and expected outcomes.
- For implementation changes, keep SSOT-first workflow: edit `ssot/`, then build and validate.

## 1) Supercharge: Prompt Hardening Run

### Scenario

You have a weak prompt and want a robust execution-ready version.

### Input

```text
supercharge /ult /realism Improve this prompt:
"Create our release plan."
```

### What a good run includes

- A stronger prompt with constraints and acceptance criteria.
- Immediate execution output from the improved prompt.
- Explicit assumptions when context is missing.

### Success signal

You can copy the generated prompt and get repeatable quality with fewer retries.

## 2) Converge: Multi-Source Synthesis Run

### Scenario

You have several competing drafts and need one final recommendation.

### Input

```text
converge intent: "Choose one go-to-market strategy."
source A: <paste>
source B: <paste>
source C: <paste>
```

### What a good run includes

- One integrated proposal.
- Trade-off analysis and decision rationale.
- Open questions separated from final recommendations.

### Success signal

Team can act on one coherent plan without re-debating fundamentals.

## 3) Mentor: Engineering Guidance Run

### Scenario

Your repo workflow broke and you need reliable next actions.

### Input

```text
/mentor I changed SSOT files and now strict validation fails. Output: <paste>
```

### What a good run includes

- Root-cause candidates in priority order.
- Recovery sequence with minimal-risk steps.
- Clear stop conditions before proceeding.

### Success signal

You get back to a clean, validated state without blind fixes.

## 4) Analyze-Context: Iterative Audit Run

### Scenario

You need a structured audit across many files and don’t want to lose context.

### Input

```text
Use analyze-context to audit all ssot/*.md for duplicated constraints and prompt drift.
```

### What a good run includes

- Memory files under `.analyze-context-memory/`.
- Trackable todo progression across files.
- Consolidated findings with recommended edits.

### Success signal

Audit remains coherent over long runs and survives context resets.

## 5) Threader: Context Export Run

### Scenario

You want to continue work in another AI/session without losing thread context.

### Input

```text
/threader export
```

### What a good run includes

- Transcript export as file when supported.
- Correct fallback when file export is unavailable.
- Preserved chronology and decisions.

### Success signal

Another model/session can resume work with minimal drift.

## 6) UAC Import: External Prompt Intake Run

### Scenario

You found prompt/spec material outside the repo and want a deterministic answer about how it should be packaged.

### Input

```text
Use uac-import on `/absolute/path/to/prompt.md`.
```

```text
Use uac-import on `https://github.com/harish-garg/gemini-cli-prompt-library/tree/main/commands/architecture`.
```

### What a good run includes

- Clean summary of each imported source.
- Uplifted objective/scope extraction.
- Skill vs agent vs both recommendation with explicit rationale.
- Collection-level recommendation when multiple files belong under one roof.
- Clear target-system packaging guidance.
- When auditing SSOT, a table that shows declared capability, inferred capability, and surface alignment status.

### Success signal

You know whether to ship the source as a skill, agent, or manual-review item before editing any generated surfaces.

### Audit existing SSOT

```bash
python3.11 scripts/uac-import.py --mode audit --output table
```

What a good run includes:
- one row per SSOT entry
- declared capability vs inferred capability
- alignment status like `aligned`, `frontmatter_mismatch`, or `over-generated`
- enough evidence to decide whether the entry should be skill, agent, or both

## 7) Code Review: Commit Quality Gate Run

### Scenario

You want a pre-merge review that checks whether a commit is correct, scoped properly, and not over-engineered.

### Input

```text
/code-review
```

### What a good run includes

- Findings tied directly to the captured `git show` output.
- Scope and simplicity checks, not just style comments.
- A clear recommendation to merge or revise.

### Success signal

You know whether the commit is safe to ship without relying on vague approval language.

## 8) Resolve-Conflict: Merge Conflict Planning Run

### Scenario

You have a merge conflict or want to preview one before merging and need a disciplined resolution plan.

### Input

```text
/resolve-conflict --preview main
```

### What a good run includes

- Failure modes identified before proposing the merge strategy.
- A branch-by-branch content analysis with explicit trade-offs.
- A resolution order plus verification steps before commit/push.

### Success signal

You can resolve the conflict without dropping valuable content or silently choosing between incompatible approaches.

## Optional Validation Loop

After major prompt/session updates:

```bash
python3 scripts/build-surfaces.py
python3 scripts/validate-surfaces.py --strict
python3 scripts/smoke-clis.py
scripts/deploy-surfaces.sh --dry-run --cli all --target "$HOME/tmp/llm-home"
```
