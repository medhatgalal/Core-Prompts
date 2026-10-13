# D6.S2 independent source review

## Commit Under Review

Committed source candidate `31b6635c1ec2712918093e54779e5392d17a4659`, range from `3782da241e7c4fdb973d9f96f5592926c28e07a4`. The reviewed worktree was clean before review outputs. Full collector, schema, resource map, candidate addition, review reference, tests, docs diff, source-evidence hashes and fixture XML were inspected. This is source acceptance before UAC/generation/hosted integration.

## Findings

**D6SRC-001 — high — default review route is broken.** `review-targets.md:114` now references `resources/scripts/review_package.py` and its schema, but the unchanged review route closure loads only the reference and Findings schema. Independent `load_resource_bundle(owner, 'review')` raises `ResourceContractError: references/review-targets.md references undeclared or unloaded resource: scripts/review_package.py`. The collect route succeeds with two resources. Ordinary HEAD/staged review therefore fails before review; this is present in canonical sources, not merely missing generated output.

**D6SRC-002 — high — publication can return a false complete receipt.** `review_package.py:410-424` closes the exclusive partial file, then links whatever currently occupies that path. It verifies the partial and final names against each other, not against the written file's retained identity/bytes. There is no final manifest content/digest check. An isolated actual-collector probe changed `manifest.partial` immediately after the real Output.write returned. The collector returned exit 0, status complete, while published `manifest.json` contained `{"injected":true}` and its SHA-256 differed from the returned receipt. Directory/source checks and the two-link/one-link tests did not catch it. The fixture remains at `/private/var/folders/42/sm0kpcrx151_t0cqygfwb3f80000gp/T/d6-independent-manifest-cnf5z59z`; no recursive cleanup was performed.

## Scope Assessment

Exact accepted embedded ReviewPackage schema equals shipped schema; all source-evidence file hashes match current bytes. The candidate preserves ordinary reviewer body and explicit-only collector authority. Git range/object framing, source-side raw bytes, caller-assertion limitations and no-verdict boundaries are explicit. Actual source fixture XML records 82 passed and one APFS non-UTF8-path skip; the skip is unverified coverage, not a pass. Generated provider package closure and hosted Linux raw-path acceptance remain pending.

## Message Assessment

Current head message, `Preserve raw collector test logs with clean diagnostic rendering`, accurately describes the narrow follow-up; broader source implementation is in its predecessor. No release/install/merge result is inferred.

## Recommended Fixes

1. Preserve the existing ordinary review closure without unconditionally loading the collector. Move collector-only resource references/guidance into a selected collect reference or the declared entry/canonical public docs, or otherwise use the existing supported conditional routing contract. Add actual review-route and collect-route assembly checks; do not hide this by adding collector code to every ordinary review or weakening unloaded-reference validation.
2. Keep and verify the collector-created manifest file identity and exact bytes through publication. Before emitting a receipt, verify the final marker is the owned expected inode with expected regular-file/link properties and exact canonical bytes/digest. Unlink only the verified owned partial link; on mismatch preserve output and return exit 2 without a receipt. Add discriminating same-inode tamper and replacement-path tests before link/cleanup and after publication, keeping existing no-overwrite/hardlink/fsync tests. Do not claim protection against arbitrary later privileged mutation; retained receipt verification remains necessary.

## Merge Readiness

`review_status: complete` for this source scope; **blocked with two open high findings**. Independent selected existing tests: 14 passed in 10.68s (`test_rp09_output_faults` and `test_rp16_hostile_initialized_submodule`). The additional publication probe failed the promised acceptance despite these passes. No authoritative build, UAC, shared-file mutation, Git staging/commit, hosted CI or release/install action was performed. Same author must repair; same reviewer will verify changed exact bytes before source acceptance. Final UAC, generated route/package checks, required CI, main parity and remaining documentation integration are downstream gates.
