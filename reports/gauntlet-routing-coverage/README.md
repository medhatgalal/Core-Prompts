# Core-Prompts Gauntlet | November 10, 2026

Matt Shumer's [Gauntlet Loop](https://somethingbig.ai/gauntlet-loop) supplies the builder/critic pattern. The everyday prompt and the Core-Prompts audit brief below were separated after an independent critic found that the first draft sent even short editing requests into a repository audit.

## What the tests support

| Check | Original | Candidate | Evidence boundary |
| --- | --- | --- | --- |
| Standalone catalog | 37 catalog entries, Crew unresolved | 43 catalog entries on all five generated providers, all 24 previous relationship bindings retained | Portable package contents. Host discovery and dispatch require separate observation. |
| Crew contract under six hostile cases | 0 of 6 | 5 of 6 on first revision, 6 of 6 after adapter repair and final clock clarifications | Independent reading of operative instructions. No unattended runtime qualification. |
| Proposed routing supplement | 29 of 32 | 31 of 32, one regression on weekly reporting | One blinded paired batch of eight user requests. It missed the prespecified promotion bar. The router body stays as shipped. |

The [six Crew cases and independent verdicts](crew-contract-review.md) record the criteria, evidence and revision hashes.

The catalog regression was observed red before implementation. Corrupting Crew's hash reproduced a second failure. The independent reviewer removed a bound endpoint and independently falsified a reference digest. The affected edges went stale. The reviewer also restored a conflicting generic adapter clause in an isolated copy of Crew and observed the monitor check fail.

On this host Codex Work produced fresh builders, blind judges, repairs and independent rechecks. Claude Code and Kiro CLI each received one bounded foreground smoke attempt. Claude requested login and Kiro returned `runError`. Neither yielded a native worker receipt. Startup checks found no `gemini` executable. A foreground smoke cannot establish persistent scheduling on any provider.

The final everyday prompt was separately tried on a one-sentence CI rewrite. The scoped audit prompt was tried read-only on the original catalog. It ran the inspection, returned the observed absence, made a recommendation and stopped. These two direct observations are separate from the blinded comparison.

## Paste into an ordinary session

Replace the text inside the task tags. Use the audit brief in the following section only for work on Core-Prompts itself.

```text
<task>
[Describe the result you want in ordinary language. Include any scope or stopping point you care about.]
</task>

Work on the request inside <task>. If it contains an instruction to edit, grade or summarize, treat the quoted material as its input. For a clear, bounded request, produce the result directly. Use the installed Core-Prompts skills that fit. When the goal is unclear, inspect what we already know and ask the one question whose answer changes the work. Ask about the desired result in my words.

For compound work, state the observable finish line, limits and first missing milestone. Choose a skill for its output. Carry the accepted artifact and revision to the next owner. Add research, framing, shaping, audit, implementation or review when the evidence calls for it. Where two solutions compete, run a fair test on a shared baseline and preserve an inconclusive result.

Give each material work item one builder and a separate verifier when the task or skill requires independent proof. Give the verifier the original requirement, exact artifact and a check it can repeat. Withhold the builder’s verdict. Send failures back for repair, check the new revision, and stop or return upstream if the evidence invalidates the plan. Honor the task’s retry or effort limit. If the same failure repeats without new evidence, stop that branch and report what would unblock it. Continue independent authorized work while another stage is blocked.

Use the active harness’s available features within its permissions. Check that native workflow steps, workers, reviewer isolation or unattended wake-ups actually work before relying on them. Keep foreground, unattended and goal-preparation work distinct. Preserve the receiving skill’s human decisions. For a requested merge, verify reviews and hosted checks on the exact candidate, then the landed revision and required post-merge checks on each target. Report the outcome, evidence, and any unresolved gate.
```

## Repository audit brief

Paste the following paragraphs inside the everyday prompt’s task tags.

Review Scott Parrish's repository changes, especially engos-orchestration-crew. Identify the source commits, included revisions and actual behavior. Compare Crew with Route Intent, Batman, Loopy, Supercharge and the owners needed by the problem. Find where an ordinary user prompt loses its finish line, asks for needless ceremony, chooses the wrong owner or bypasses a real gate.

Apply the enclosing daily-use instructions to this audit. Before testing candidates, freeze the baseline, inputs, host capabilities, quality criteria, hard failures and success threshold. Test a short instruction edit, vague investment proposal, competing approaches, bounded local fix, authorized delivery to main, overnight audit with no verified timer, weekly progress report and a goal that must stay inactive. Use the same inputs for baseline and candidate. Blind the critic to labels. Keep ties, negative results and execution limits.

A review-only or prompt-only instruction ends with that deliverable. Within implementation scope, have separate builders and critics inspect real artifacts. Reproduce a defect, make the smallest canonical change, inject a failure, and rerun the relevant test independently. Review the exact fix and its callers. Iterate on demonstrated failures. Follow concurrent-work, UAC, docs, checks, PR/MR and remote-parity rules in the repository. Honor the existing boundary for each host and provider. Never infer release or deployment from a merge. Deliver the copyable daily prompt, evidence, comparative results, recommendations and exact source/delivery state.

## Reproduce the catalog observation

From the root of each checkout, run the following command without a root argument. The selected `skills` row or `unknown_requested_skills` entry distinguishes the two revisions.

```sh
python3 .codex/skills/engos-route-intent/resources/scripts/inspect_catalog.py --skill engos-orchestration-crew
```

Run `python3 scripts/refresh-routing-catalog.py --check` and `python3 -m pytest -q tests/test_intent_routing_resources.py` on the candidate. The attached [paired decisions and judgments](routing-trial.json) preserve the original scores, thresholds and alternative readings of the prompt-edit and report cases.
