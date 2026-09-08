# Independent state-transition control review

**Verdict: pass for the separately labeled controller controls. Formal promotion: hold.** This follow-up closes the initial review's rejection/tie/disposal/continuation coverage gap for prescribed controls. It adds zero optimization trials and zero optimization gains. The original optimization run remains three accepted trials.

## Scope and implementation identity

I inspected `run_transition_controls.py`, its control contract, seed, all three candidate archives, ledger, captured evaluator and controller outputs, disposal evidence, intermediate states, and summary. The original runner SHA-256 is still `025678cc6651c1235e8c202879c79e192d462b9d6db33bbde9888152d079b94d`, matching the first independent review. The original evaluator remains `5a4ef4ee317495e126a6e8fbf5d6fc44153622fe579b5540770d0f05ec328fc4`.

The new wrapper imports that exact runner and changes only its `ROOT` global to copied control state. Its original repository context, manifest, contract and function implementation remain intact. The controller's event name and local counter still say `optimization_trial`; the separate control contract and directory explicitly classify all three calls as controls, outside the original search budget and gains.

The original host history contains actual successful wrapper execution `37ca1f`. I matched the wrapper bytes from that call to the current file, and matched all three printed events plus summary to the stored control evidence. The exported provenance contains only relevant call/result metadata and hashes.

## Independent execution and result

I used a separate verifier, [independent_transition_replay.py](independent_transition_replay.py), to construct a fresh replica under [transition-replay](transition-replay). The verifier imported the unchanged `run_fixture.py` directly and invoked its actual `trial()` function; it did not substitute independent decision code for the controller. Independent scoring was used to check the real decisions afterward.

Actual replay command: `python3 -I -B reports/frontier-modernization/live-auto-research/verification/independent_transition_replay.py`, execution chunk `c9c942`, exit 0. Four evaluator processes ran: a fresh scanner-seed evaluation, followed by the three same-controller calls. All completed successfully under the original five-second limit, with empty stderr. The three evaluator outputs were byte-identical to the original transition-control outputs, and replay events matched except for timestamps.

**76 checks passed.** The seed was the accepted original scanner, with 16/16 cases and 60 AST nodes.

| Labeled control | Score | Actual decision | Resulting incumbent |
| --- | --- | --- | --- |
| Known lower-quality trim-only candidate | 6/16; 10 AST nodes; ten regressions | Rejected | Original scanner seed |
| Scanner plus comment, changed bytes but identical AST | 16/16; 60 AST nodes | Tied | Original scanner seed |
| Known split/join positive control | 16/16; 14 AST nodes | Accepted | Split/join candidate |

For the rejected and tied calls, the unchanged controller retained the scanner's identity and score while advancing only the replica's local trial counter. The third call began from that same retained scanner and accepted the simpler candidate after the preceding loss and tie. Each call removed its exact active file and retained the immutable candidate archive and raw evidence. Both original-control and verification-replica active directories are empty.

Machine evidence, hashes, state transitions and coverage boundaries are in [independent-transition-review.json](independent-transition-review.json). Supporting raw outputs, state snapshots and disposal records remain under `transition-replay/`.

## Preservation and remaining limits

The original fixture, original transition-control evidence, twelve package identities, protected evaluator/data/contract/baseline, original optimization ledger, and original incumbent all remained unchanged during replay. The initial independent review files and script also remain unchanged. All writes were confined to new verification outputs.

These are prescribed negative, tie and positive controls, not newly discovered optimization hypotheses. They demonstrate the real controller's rejection, tie retention, active-file disposal, archive preservation and later acceptance under this deterministic contract. The first review remains accurate for its original scope; this follow-up supplies the previously missing control evidence.

The controller's invalid-candidate transition, timeout/crash recovery, crash-consistent durability and hostile-code isolation remain untested. Sixteen visible cases and a local AST-size metric do not support held-out generalization, runtime-speed claims, formal capability promotion or a frontier-model benchmark.
