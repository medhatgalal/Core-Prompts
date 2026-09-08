# Auto-Research actual local acceptance demonstration

This run executed a Python whitespace-normalization search using the current Auto-Research SSOT and emitted experiment resource package. It is a deterministic fixture demonstration, not formal capability promotion, a cross-model comparison, or a frontier performance benchmark. Independent replay passed for both the three-trial search and the separately labeled controller controls.

## Target Summary and Goal Contract

Normalize a string by trimming boundary whitespace, collapsing internal whitespace (including tabs, newlines, and Unicode whitespace) to one ASCII space, and preserving non-whitespace Unicode text. Empty input remains empty. The complete contract was written and hashed before the baseline run and candidate mutations: `protected/goal-contract.json`.

The search budget was exactly three optimization trials. The objective ranks protected correctness first, with no regression of a formerly passing case; at equivalent correctness, one fewer AST node is a meaningful simplicity improvement. Exact ties retain the incumbent. Runtime observations are recorded but never ranked. Each deterministic candidate ran once during search, with final baseline/incumbent reruns and a required independent replay. Each process has a five-second limit. No external APIs, paid comparison runs, or third-party imports were used.

## Baseline and Protected Evaluation

Original `return value.strip()` passed 6/16 cases with 10 AST nodes. Its immutable reference is `original/normalize.py`. Baseline SHA-256: `9dddc7b60600c6f6e45190da9fe055d16883d9d13c3ec00479245255c2978459`.

The fixed evaluator embeds 16 protected cases for empty input, trimming, ASCII whitespace, tabs/newlines, nonbreaking and em spaces, CJK/Arabic/accented text, emoji, combining characters, and zero-width-character preservation. Evaluator SHA-256 remained `5a4ef4ee317495e126a6e8fbf5d6fc44153622fe579b5540770d0f05ec328fc4`. The evaluator, contract, and baseline are read-only files plus checked hashes; this is integrity protection for a trusted local fixture, not an operating-system sandbox against malicious code. The cases were visible development cases; no held-out generalization claim is made.

## Search Surface and Scorecard

Only the isolated candidate Python module could change, including coordinated import and function-body edits. Every trial began as an exact copy of the current incumbent, and archived candidate bytes remain separately available. The original baseline, incumbent, and active trial were different paths. The package and frozen inputs were hash-checked before and after every actual evaluator process.

| Artifact | Protected cases | AST nodes | Decision | Parent |
| --- | ---: | ---: | --- | --- |
| Original trim-only | 6/16 | 10 | Frozen baseline | — |
| trial-01 | 16/16 | 60 | accepted | original |
| trial-02 | 16/16 | 19 | accepted | trial-01 |
| trial-03 | 16/16 | 14 | accepted | trial-02 |

## Experiment Ledger and Result

`ledger.jsonl` records actual candidate hashes, parent hashes, joint mutation hypotheses, comparisons, decisions, remaining trial counters, and raw evidence paths. The runner appends each decision before updating the incumbent.

The three genuine hypotheses were: a Unicode-aware explicit character scanner to fix normalization; a standard-library regular expression to simplify the accepted scanner; and built-in split/join to remove the regular expression and trim operations. These are plausible alternative implementations of the same task. None was deliberately broken to fabricate a failed search. Trial 1 delivered ten additional passing cases; trials 2 and 3 retained all 16 while reducing syntax-tree complexity from 60 to 19 to 14 nodes.

Final retained candidate (`incumbent/normalize.py`):

```python
def normalize(value):
    return " ".join(value.split())
```

Genuine gain against original: **10 additional cases passed, from 6/16 to 16/16**. The retained implementation has 14 versus the inadequate baseline's 10 AST nodes; it is not claimed to be smaller than the baseline. Simplicity gains apply against the first fully correct incumbent. No speed, memory, or global-optimum claim is made.

Exactly **3 optimization trials** ran and all three were accepted. Search had **0 rejected trials and 0 tied trials**. It continued twice after the first win and stopped because the declared three-trial budget was exhausted.

## Separately Labeled Controls

Controls live in `controls/` and their actual results in `raw/negative-control-*`. They add zero optimization trials and zero claimed gain:

- Wrong-output control: original trim-only behavior scores 6/16 and is rejected as a quality regression from the retained candidate.
- Invalid-candidate control: syntactically invalid Python is classified invalid with `SyntaxError` and rejected.
- Evaluator-mutation control: a separately changed evaluator copy has a different hash and is refused before execution. The protected evaluator itself is unchanged.

The initial control helper assigns wrong-output and syntax-control dispositions directly. Those checks establish scoring and evaluator-identity behavior; by themselves they do not exercise the main `trial()` rejection/tie transitions. All initial controls leave the original incumbent hash unchanged.

A subsequent authorized control replay closes that state-transition gap through the **same unchanged `trial()` implementation**, in separately copied state under `transition-controls/`. It seeds the actually accepted scanner, then executes a known lower-quality candidate, a byte-changed but AST-equivalent tie, and the already-tested split/join candidate. Actual decisions are **rejected → tied → accepted**. The seed is retained across loss/tie; exact active control files are disposed while code archives remain; the subsequent accepted candidate advances the control incumbent.

These three prescribed state-transition controls add **zero optimization trials and zero optimization gain**. Their reused inner event name is `optimization_trial` for implementation fidelity, but their isolated directory and `control-contract.json` explicitly classify them as controls. Original ledger, state, retained function, evaluator, baseline, and runner hashes stayed unchanged. This proves the evaluated controller transitions for these controls, not arbitrary hostile-candidate isolation.

## Verification and Disposal

The baseline and incumbent were actually re-executed after all search trials and controls, again scoring 6/16 and 16/16. All frozen and package hashes matched. Final retained SHA-256: `87649224bef74bdb41260e7bb8bd1b393da872a54a41579f7197d20eea857250`.

After every trial, the exact task-owned active candidate was removed; its archived code and raw outputs were preserved. `active/` is empty. The neighboring preservation sentinel, original baseline, protected evaluator, and current incumbent remain intact. Every `trials/trial-*/disposal.json` records that check. Only this report directory was written; no source, Git/provider, installation, or release action was performed. Concurrent agents' worktree changes are outside this fixture's custody and are not claimed to have been audited globally.

Independent verification: **pass within this deterministic fixture scope**. `verification/independent-review.md` records 155 passing checks and eight actual evaluator replays with byte-identical raw output, including original host-tool provenance. `verification/independent-transition-review.md` records 76 passing checks and four evaluator processes replaying the fresh scanner seed and the same-function rejection/tie/acceptance sequence. Both reviews are from a real independent subagent; the initial assignment withheld a preferred result. The initial review is preserved unchanged, and the follow-up explicitly closes its controller-control coverage limitation.

The original `summary.json` and `transition-controls/summary.json` remain historical pre-review snapshots so their audited hashes stay intact. **`final-status.json` records the completed verification state.**

## Promotion Decision

**hold** for formal promotion, which is neither requested nor established by this fixture. The best local candidate is retained for the demonstrated contract only. This run demonstrates executed search, baseline/incumbent distinction, protected evaluation, continuation after wins, measured simplicity gains, and separate same-controller rejection/tie/continuation controls. It does not establish that the rewritten skill improves frontier-model performance or generalizes across task families.

## Trace-to-Eval Follow-up

The ten failing baseline cases and their expected results are retained in the immutable evaluator and exact raw output. They can be replayed as normalization regression cases. The negative controls can be replayed as fixture-integrity probes; keep their results separate from task-quality gains. The same-controller controls now preserve regression, tie, disposal, and later-acceptance traces. Further acceptance work should target real-task transfer and the still-untested invalid-candidate controller transition, timeout/crash recovery, and durable state transactions when those claims are in scope.

## Risks and Limits

The dataset is small and visible, implementations were human-readable choices of the invoking agent, and the function is deterministic. The controller's invalid-candidate transition, timeout/crash recovery, crash-consistent durability, and hostile-code isolation remain untested. AST count is a preregistered local syntax-size proxy, not a general readability or maintainability metric. External model calls and paid comparisons were not run, although the invoking and independent-review agents themselves are model executions. Raw measured wall times are provenance only. Resource delivery shows full content was supplied through a real tool, not comprehension by itself.
