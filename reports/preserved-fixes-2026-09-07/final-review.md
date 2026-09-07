# Independent final code and docs review

## Superseding review: runtime packaging and corrected examples

The renewed review supersedes the initial blocked docs verdict below. **Code ready; docs ready**, subject to required final local/hosted checks and refreshed generated health evidence. No blocking finding remains in the inspected implementation. The initial findings remain below as the review ledger, not current blockers.

- Both metrics/rendering command pairs now retain the same `--since "2 weeks ago"`.
- Single-entry index behavior now matches the executable; default-config compatibility remains explicit.
- Configure targets `~/.local/bin/eng-report`, resolves the exact installed runtime helper, preserves custom launcher content through comparison, and no longer searches home for a random checkout or invokes unsupported `eng-report configure`.
- `scripts/eng-report.py` is now included by package-surfaces, install_bundle ROOTS, and the legacy standalone copy inventory. The legacy launcher resolves the target installed runtime (`$TARGET_ROOT/.core-prompts-updater/scripts/eng-report.py`) rather than the source checkout. This closes the observed release/install omission without changing selected skill-scope membership or moving canonical implementation.
- The focused deployment test verifies installed helper bytes equal canonical source, rejects a checkout path in launcher text, asserts the exact installed helper path, and executes `run --help` with cwd outside the checkout. The package-boundary test requires the helper in the archive. These assertions meaningfully exercise delivery; this reviewer inspected them without duplicating the parent’s running suite.
- Current STATUS at renewed inspection reports zero validation errors and zero smoke failures. Final regeneration remains tied to the parent’s last serial checks.
- The saved profile installation still requires the explicitly reviewed existing-launcher refresh: profile deployment does not itself migrate a previous checkout-bound launcher. Do not infer live migration from the legacy install test.

Nonblocking editorial suggestion: rename the residual Notifications heading containing `--notify` to “Notifications (explicit integration request)”; its body already enforces the correct explicit request/recipient boundary.

Renewed reviewed SHA-256 identities:


- `scripts/eng-report.py`: `4aed5dd288ba3e48e710c0fddc986f5e330368251a22bca9f79c46f55bdb26b6`
- `scripts/deploy-surfaces.sh`: `6ef69e5c62869164a33d388f43115fa4cd8439dab94bfed9645227969e2582da`
- `scripts/install_bundle.py`: `fa4700a980e775f1d071c06eab581e4367b3302635ccec26b155e4293d1164ab`
- `scripts/package-surfaces.sh`: `735c3b6cade2611bce9ff810d9b738d84984c07d52eccb16798773f62ea15139`
- `tests/test_deploy_surfaces.py`: `5e2ac6aa2a09c541bdbfd32d5d8fe97d922006b7155c63ddb09f50e5b42439c2`
- `tests/test_package_surfaces.py`: `1ba8e0628f4a153ef1c47e7d9b814d4174fd5a4857bdce6bddc93fc844f0aa2c`
- `tests/test_eng_report_json.py`: `83dd09c74a2ebf01b6e14a27b3d606b8759f723163292c6ea8998a41cb54c404`
- `ssot/engos-audit-engineering-progress.md`: `c89b815c182161cde0f17ea686e5ffb9c12d405dceb9ccffbdb90c5e63023b29`
- `docs/EXAMPLES.md`: `e90982e1daaed8e3c785aa5b597ef3bb5601a33db417a73e7242a0891911cb85`

## Initial review ledger
## Commit Under Review

Working-tree diff against `97adb7ad0e56ae6e07efc43b085a549194fc1b33`, branch `AI/preserved-fixes-release`, worktree `/Users/medhat.galal/.codex/worktrees/0397/Core-Prompts`. This is an unstaged working-tree review, not a staged commit/message approval. The reviewer changed only this report. Same-slug UAC completion is caller-reported; its generated descriptor was inspected. Full local validation is concurrently owned by the delivery agent and is not claimed complete here.

Reviewed identities (SHA-256):

- `scripts/eng-report.py`: `4aed5dd288ba3e48e710c0fddc986f5e330368251a22bca9f79c46f55bdb26b6`
- `tests/test_eng_report_json.py`: `83dd09c74a2ebf01b6e14a27b3d606b8759f723163292c6ea8998a41cb54c404`
- `ssot/engos-audit-engineering-progress.md`: `488c130cc5d95b20d026ffcd49d89483c733682552118ff0fc61600970f32c8c`
- `docs/EXAMPLES.md`: `d4ad1a2cb978b8a6f29ee36f5bb6e183a7e535871425087c2286e615bd367994`

## Findings

**[P2] Keep the same reporting window during the rendering pass.** `docs/EXAMPLES.md:597` and `ssot/engos-audit-engineering-progress.md:141` omit `--since "2 weeks ago"` supplied by the preceding metrics command. The script independently resolves each invocation to `args.since` or configuration/default one week (`scripts/eng-report.py:1465`). Following the new example with defaults writes a two-week narrative into a one-week metrics report. Add the same window to the second command and regenerate current surfaces. This blocks docs readiness until corrected.

No code correctness finding in the reviewed JSON change. `render_html=False` gates `render_report`, report HTML writes and modal-JavaScript writes, while `main` skips directory creation and returns before index generation in JSON mode. Default `render_html=True` preserves existing direct callers and ordinary CLI rendering. Metrics, fetch, aggregation, author selection and narrative logic stay intact. This promises no report artifacts, not globally write-free or offline execution; existing remote fallback may create a Git cache.

## Scope Assessment

The code change is local and proportionate. Focused subprocess tests exercise real local Git history without a configured network remote, parse stdout as JSON, preserve sentinel HTML/JavaScript/index bytes, assert absent output directories remain absent, and verify ordinary HTML/index/JavaScript output. Tests are meaningful failure/fix coverage rather than implementation-mirroring assertions. Full tests should be run by the delivery agent after final regeneration; no redundant parallel test run was started by this reviewer.

Only Engineering Progress canonical SSOT changes. No old `eng-report`, `supercharge` or `pulse` skill/evaluation paths are restored. The legacy `~/.kiro/skills/eng-report/config.yaml` path documented here matches the actual `DEFAULT_CONFIG`; it is existing executable configuration compatibility, not a restored skill selector. No Supercharge, OpEx or Loopy source changes occur. No global help gate, template mutation or UAC flattening patch is introduced.

All five generated Engineering Progress skill files are byte-identical (`f3f7225590306c5d841066833157282c1a89f0a1f5b9aefde2002d7e248ab759`). Each bundled descriptor equals canonical metadata. Eval edits preserve current names and substitute the JSON artifact boundary and explicit notification authority for obsolete auto-open/flag claims. Draft evaluation status and structural readiness do not imply behavioral promotion.

## Message Assessment

No proposed commit message exists for this working-tree review. A suitable message should describe the JSON artifact fix and matching CLI guidance. VERSION and CHANGELOG agree on `v1.13.1`; version availability, hosted tags and release publication are outside this review and remain separate delivery gates. Changelog correctly avoids behavioral-promotion claims.

## Recommended Fixes

1. Add the same `--since` to both second-pass examples and regenerate from canonical SSOT.
2. Refresh generated `docs/STATUS.md` after serial validation/smoke: the reviewed snapshot currently says health error, seven validation errors and no smoke report. Do not package stale failing evidence as the final health snapshot.
3. Complete local validation and exact-candidate hosted gates, then reassess any moving-main or release changes separately.

## Merge Readiness

- Code review: **ready**, subject to required execution/CI gates; no blocking implementation finding.
- Docs review: **blocked** by the reporting-window example mismatch and pending final health-snapshot regeneration.
- Merge/release/install: **not assessed as complete** by this review.

## Current State

The changed docs correctly distinguish the single executable `run` subcommand from skill-guided configuration, uploads, browser opening and explicitly authorized communications. Real flags were compared with `python3 scripts/eng-report.py run --help` and parser source. Unsupported flags are described as unsupported rather than presented as executable examples. The JSON caveat correctly states that Git fetching can occur and shell redirection itself creates the metrics JSON file.

## What Belongs Where

README provides discovery and links to the worked example; getting started provides the first invocation; CLI reference gives exact executable boundaries; EXAMPLES supplies the concrete metrics/narrative/render sequence. Canonical SSOT owns help and integration workflow behavior. Changelog records the release slice. Generated status remains a snapshot rather than onboarding authority. This follows current docs-governance steering without introducing new global policy.

## Drift Findings

The new inconsistent window is the actionable user-facing drift. The stale error snapshot is pending known serial checks. The broader pre-existing skill describes an index for at least two repositories while the actual CLI and its new regression produce an index even for one configured entry; the changed exception text correctly captures `--no-index`, `--name` and `--author`, and can be made fully exact while touching this section. This single-entry mismatch predates the repair and is not an implementation regression.

## Examples of Good Output

Use identical config, repository name and window in both passes. For example, the rendering command in EXAMPLES should read:

```bash
eng-report run --config /path/to/config.yaml --name Core-Prompts --since "2 weeks ago" --narrative-file /tmp/narrative.json --output /tmp/progress-report
```

## Review Timing

Recheck the two corrected examples and current generated snapshot before commit. Repeat affected checks if main moves. At release, verify packaged files and installation separately; this review does not claim hosted success, publication or installed parity.

## Open Risks

Skill help is an authored terminal contract, not measured host behavior. Current UAC metadata remains structural evidence only. The implementation intentionally continues existing Git-fetch, remote-cache and explicitly selected AI behavior during JSON collection; no broader no-write guarantee should be added. No changes were requested to those behaviors.
