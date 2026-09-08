# Independent resource delivery and evaluator review

## Commit Under Review

Working-tree changes relative to `c9d6de07b4d1918970a5f70350cf50200a6a0ff4`, branch `AI/frontier-capability-modernization`, Python 3.14.7, at `/Users/medhat.galal/.codex/worktrees/921d/Core-Prompts`. This is an unstaged review, not an assessment of a proposed commit message. The 32 assigned implementation and canonical resource files are bound in `inspected-start.json` and `inspected-end.json`; none changed during this review. Emitted helper bytes are separately bound in `packaged-helpers-result.json`.

## Findings

1. **P2: An absent manifest silently downgrades an explicitly resource-backed entry, including existing reviewed topology evidence.** `src/intent_pipeline/capability_resources.py:161` returns the entry unchanged whenever the manifest is absent. `src/core_prompts_eval/topology.py:113` likewise skips assembly unless the manifest is a regular file. Its overlay comparison at line 48 checks resource identity only when the newly compiled topology has a bundle. Deleting the map therefore drops resources and their identity from static evaluation. In a valid reviewed fixture whose resource contains no normative-marker clauses, the old `human_reviewed` overlay is accepted despite its previously bound resource bundle disappearing. The entry expressly requires `resources/resource-map.json`, so this is not a legacy self-contained entry.

   Reproduce: `PYTHONDONTWRITEBYTECODE=1 python3 reports/frontier-modernization/reviews/resources-final/reproduce_missing_manifest.py`. Observed result: effective text is entry-only; topology is accepted with `review_status=human_reviewed` and no `resource_bundle_sha256`. See `missing-manifest-result.json`. Detect explicitly resource-backed entries before allowing legacy fallback; fail on missing/nonfile/broken maps; compare prior and current overlay bundle identities symmetrically.

2. **P2: Topology assembly does not validate entry-to-manifest references.** `src/core_prompts_eval/topology.py:114` calls `load_resource_bundle(resource_root)` without `entry_text`. With a valid map and an entry requiring `resources/absent.md`, `effective_capability_text` correctly rejects the missing declaration, but `compile_topology` accepts the same fixture. This permits topology/goal evidence to describe an incomplete resource contract.

   Reproduce: `PYTHONDONTWRITEBYTECODE=1 python3 reports/frontier-modernization/reviews/resources-final/reproduce_topology_entry_reference.py`. See `topology-entry-reference-result.json`. Supply the complete entry to the loader during topology assembly, preserving the intended distinction between router declarations and selected resource closure.

## Executed verification

- **62 passed:** `tests/test_capability_resources.py`, `tests/test_resource_delivery.py`, and `tests/test_frontier_eval_integration.py`, with cache and bytecode writes disabled and fixture state under this review directory. Exact output: `focused-tests.log`. Covered confined paths and symlinks, manifest duplication/schema, nested dependencies, cycles, inactive missing files, unresolved active references, per-route and raw-byte hash changes, historical/candidate separation, binding validation, preflight-to-dispatch resource drift, actual adapter request fields, trace hashes, canonical outcome/ambiguity aliases, resource clauses, and changed-resource overlay rejection.
- **225 successful actual helper invocations across 18 emitted packages:** all declared routes plus `all`, for both skills on five skill surfaces and four agent surfaces. Every stdout JSON exactly equals the canonical source bundle, including complete content, ordered paths, resource hashes, manifest hash, and selected-route hash. All 18 helpers reject an unknown route with exit 2 and empty stdout. `run_packaged_helpers.py` and `packaged-helpers-result.json` retain the command logic and output identities. Supercharge `details` supplies shared rules and the eleven modules; Auto-Research `experiment` supplies shared delivery guidance, loop guidance, and the three declared template dependencies.
- **Four actual subprocess requests captured:** `run_real_pipe_capture.py` observes the exact stdin passed through the real `subprocess.Popen.communicate` operation to the existing fixture adapter. It does not replace `execute_adapter` or generate a simulated adapter response. Assertions verify CRLF/Unicode module content, separate historical and candidate payloads, complete shared content through the existing binding fixture, delivered-artifact hashes, request hashes, trace resource bindings, and the real adapter's deterministic response. Full observed requests and stdout are in `real-pipe-observations.json`; immutable run artifacts are under `real-pipe-fixture/reports/`. Zero paid model calls.
- The two additional reproducers above exercise negative cases missing from the passing suite. Their results block approval.

## Requirement disposition and evidence limits

| Requirement | Finding |
| --- | --- |
| S17 | Declared/present/assembled route closure is exercised on every emitted helper. Actual evaluator subprocess delivery is exercised with distinct arm fixtures. No model comprehension, ordinary host automatic loading, or independently scored module behavior is claimed. |
| S18 | Help/examples/details package assembly preserves exact canonical content and route order. This proves assembled payload, not a model's terminal-only response or exact final formatting. |
| U01 | Nested dependency, path, file, cycle and active-reference checks pass while the manifest is present. Missing-map fallback remains a blocker. |
| U07 | Canonical aliases, resource clause extraction, raw resource identity, changed-resource overlay rejection, preregistered per-arm delivery and trace binding pass their scoped checks. Missing-map/overlay fallback and unchecked entry references remain blockers. |

The `capability.json` infrastructure exemption is reasonable for the generated discovery footer: it is descriptor metadata rather than reasoning-module content. Its exemption must not be described as delivery of that descriptor. The loader's explicit assembly claim and the runner's supplied-in-request claim correctly disclaim consumption. A model-authored read receipt is not used as proof anywhere in this review.

## Scope Assessment

The assigned resource/evaluator changes form a coherent resource-delivery slice. No source files were modified by this review; only this report directory contains new tests, fixtures, and evidence. The parent was changing unrelated tests/docs concurrently, which this review does not approve. All 18 emitted helper hashes currently differ from the inspected canonical helper because the parent has not yet regenerated the final `capability.json` exemption change. Their active-route contents nevertheless match canonical resource assembly. Final generation and renewed helper hash parity are required before final approval.

## Message Assessment

No proposed commit message was provided; not assessed.

## Recommended Fixes

Address both concrete findings, add regression checks for missing/nonfile maps and stale overlay resource removal, regenerate emitted helper copies, then rerun the affected tests and packaged-helper parity check. Keep behavioral promotion pending unless independent resource-dependent model execution is separately performed.

## Merge Readiness

**Blocked for this slice** on the two reproducible static-evidence gaps. The passing tests and transport captures establish their stated scope only; they do not override those findings or establish behavioral promotion.
