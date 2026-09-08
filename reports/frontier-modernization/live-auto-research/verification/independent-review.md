# Independent local fixture review

**Verdict: pass for this deterministic local fixture. Formal promotion: hold.** The retained candidate is `trial-03`, with SHA-256 `87649224bef74bdb41260e7bb8bd1b393da872a54a41579f7197d20eea857250`. This review establishes neither frontier-model performance nor the revised skill's general effectiveness.

## Target, contract, baseline and search surface

The protected contract requires boundary trimming, internal whitespace collapse to one ASCII space, and preservation of non-whitespace Unicode text. It preregisters correctness without regressions first, then fewer AST nodes at equal correctness; exact ties retain the incumbent. The budget is exactly three optimization trials, with five seconds per evaluator process and separate controls. Only isolated candidate modules are mutable.

I read the current SSOT and loaded the complete `experiment` resource route with the actual emitted helper, recovering the initial truncated combined read before dependent work. I independently inspected the evaluator, contract, manifest, runner, candidate/proposal archives, complete captured results, controls, ledger, state, summary, and disposal records.

## Independent scorecard and decisions

| Artifact | Exact cases passed | AST nodes | Derived decision | Derived parent |
| --- | ---: | ---: | --- | --- |
| Original baseline | 6/16 | 10 | Frozen reference | — |
| trial-01: explicit scanner | 16/16 | 60 | Accept correctness gain | original |
| trial-02: regex collapse | 16/16 | 19 | Accept equivalent correctness and simpler syntax | trial-01 |
| trial-03: split/join | 16/16 | 14 | Accept equivalent correctness and simpler syntax | trial-02 |

No previously passing case regressed. The final gain is ten additional passing cases. The incumbent is four AST nodes larger than the inadequate baseline; simplicity improved against the first fully correct candidate. AST count is a local syntax-size proxy, not a measured readability, maintenance, or performance outcome.

The hypotheses are plausible ways to improve the function and then simplify it. None of the three optimization candidates is a deliberately broken control. They are an illustrative sequence selected by the agent against visible development cases, not evidence of blind discovery or broad search quality. Exactly three optimization trials appear in both the ledger and actual host tool outputs. Search continued twice after its first win and stopped at its stated budget.

## Replay and provenance

The separate verifier [independent_replay.py](independent_replay.py) never imports or invokes the mutating runner. Its actual command was `python3 -I -B reports/frontier-modernization/live-auto-research/verification/independent_replay.py` (execution chunk `0f7fd4`, exit 0). It ran eight evaluator subprocesses: baseline, all three trial archives, final baseline, incumbent, wrong-output control, and syntax-invalid control. Every replayed stdout was byte-identical to the corresponding original raw stdout. All processes exited 0 with empty stderr; the syntax-invalid candidate was correctly reported as invalid within evaluator JSON. The changed-evaluator copy was independently rejected by hash before execution, matching its archived control result.

**155 checks passed.** Scores and regressions were recomputed from individual case results; AST counts were independently parsed. Twelve package hashes and four protected hashes matched before and after replay. Candidate identities, proposal/archive parity, raw stdout hashes, recorded commands/runtime/exit status, state, controls, and all incumbent transitions agree. Full machine evidence is in [independent-review.json](independent-review.json); supporting stdout/stderr are alongside it.

Historical provenance was checked against the original host session `01a08241-3656-7832-ae51-9d33f361756f`, not just the authored provenance index. Relevant actual tool outputs are at lines 28, 57, 64, 71, 76 and 81: resource delivery `0eead6`, freeze `c777a4`, baseline `251dfd`, and trials `538f1b`, `653cc4`, `d516df`. Their linked calls precede their results. Recorded trial events equal the ledger. The runner created in the baseline tool call is byte-identical to the reviewed current runner (`025678cc6651c1235e8c202879c79e192d462b9d6db33bbde9888152d079b94d`). Its trial function appends the decision at line 132 before copying the accepted incumbent at line 134. This establishes the executed code ordering, not crash-consistent transaction durability.

## Controls, preservation and evidence limits

The wrong-output control independently scores 6/16 and regresses against the incumbent. The syntax control is invalid. The evaluator-copy hash control is refused before execution. All three are separately labeled, add zero optimization trials, and contribute zero claimed gains.

**No tied or rejected optimization trial ran.** `controls()` assigns its quality/syntax dispositions directly instead of sending these candidates through `trial()`. Thus the controls verify scoring and evaluator-identity checks, but do not demonstrate the optimization controller's rejected/tied state transitions, disposal after a rejected trial, or continuation after a loss. The declared tie rule is unexercised.

All three exact active trial files are absent; their read-only candidate archives and raw evidence remain. The active directory is empty. Baseline, evaluator, contract, sentinel, incumbent and package hashes agree. Every original fixture file and its permission mode remained unchanged during verification. I wrote only verification artifacts; no source, provider, Git mutation, installation or release action occurred. Concurrent repository work outside this fixture was not audited globally.

The data are sixteen visible deterministic cases, with no sealed evaluation or statistical comparison. Hashes and read-only file modes protect trusted local inputs; executing candidate code with `exec` is not a malicious-code sandbox. Timeout/crash recovery and durable state transactions were not demonstrated. These limits are compatible with this fixture's bounded pass and prevent extending it into formal capability promotion or a frontier benchmark.

## Trace-to-eval follow-up

Retain the ten baseline failures as normalization regressions and keep the three controls separate from optimization results. A separately authorized follow-up should exercise a plausible losing hypothesis and an exact tie through the real controller before claiming those transitions work. No additional optimization trials or fixture mutations were performed for this review.
