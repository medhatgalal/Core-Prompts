# Observed tool provenance

The primary execution evidence is the calling task's actual `functions.exec`/`exec_command` tool history plus captured subprocess stdout/stderr in `raw/`. This index does not substitute a self-authored receipt for actual execution.

- Initial runtime inspection: command chunk `80362b`; cwd and repository `/Users/medhat.galal/.codex/worktrees/921d/Core-Prompts`, branch `AI/frontier-capability-modernization`, HEAD `c9d6de07b4d1918970a5f70350cf50200a6a0ff4`, Python 3.14.7. The large pre-existing dirty-state list was truncated; no clean-state claim is made.
- Actual experiment-route loader supplied complete resource text: command chunk `0eead6`, exit 0. Bundle manifest `a485f7eaf1c508e21d130f75ab04c44966ac9700c0a4d33f0d9ad8443bad9dc8`; assembled content `8937556551fbcf508d8cd11a21c89a5c0ab7583d123529d242b7e16117015c2b`. A second actual loader execution captured exact stdout/stderr and its argv in `raw/resource-delivery-*`.
- Goal/evaluator/baseline/package freeze: command chunk `c777a4`, exit 0, before any candidate execution.
- Actual baseline execution: command chunk `251dfd`, exit 0; 6/16 cases, 10 AST nodes.
- Actual trial 1: command chunk `538f1b`, exit 0; 16/16 cases, 60 AST nodes.
- Actual trial 2: command chunk `653cc4`, exit 0; 16/16 cases, 19 AST nodes.
- Actual trial 3, separately labeled controls, and final rechecks: command chunk `d516df`, exit 0; third candidate 16/16 cases, 14 AST nodes. Complete per-process commands, exit codes, runtime strings, observed wall times, candidate/evaluator hashes, and raw stdout hashes are in `raw/*.json`.
- First independent reviewer spawn was refused by the real collaboration tool because the active agent limit was reached. No simulated reviewer was substituted.

`protected/manifest.json` freezes twelve current package-file hashes, including SSOT, emitted skill, loader, resource map, experiment guidance, shared guidance, and templates. The report runner checks those bytes on every evaluation. The harness itself is `run_fixture.py`; its final content hash is recorded below after search and before independent review.

Harness SHA-256: `025678cc6651c1235e8c202879c79e192d462b9d6db33bbde9888152d079b94d`.

Host execution task ID (read from `CODEX_THREAD_ID` by actual command chunk `da7eed`): `01a08241-3656-7832-ae51-9d33f361756f`. Exact append-only host history confirmed by chunk `06646e`: `/Users/medhat.galal/.codex/sessions/2026/09/08/rollout-2026-09-08T14-21-47-01a08241-3656-7832-ae51-9d33f361756f.jsonl`. The independent reviewer has read-only access to verify historical tool events directly.

Same-controller transition controls: actual command chunk `37ca1f`, exit 0; wrapper `run_transition_controls.py` imports the unchanged runner and redirects only ROOT to copied labeled state. The three printed decisions were rejected, tied, accepted. Original artifacts and evaluator hashes matched before/after. Independent initial replay chunk `0f7fd4` passed 155 checks; independent transition replay chunk `c9c942` passed 76 checks. Each independent review records its own tool execution and verification-only raw outputs.
