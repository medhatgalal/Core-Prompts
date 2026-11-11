# Freshness v2 / upstream conflict recommendation

## Inversion Analysis

Failure would mean dropping freshness v2's evidence/verdict separation or gates, losing incoming Feedback/GTD behavior, treating stale generated files as the union, or presenting fixture and transport checks as semantic confidence. Preserve both canonical changes, release provenance and uncertainty, then require build and independent readback evidence.

## Conflict Summary

Inspection found five unresolved paths: `.meta/install-bundle.json`, `.meta/skill-job-map.json`, `CHANGELOG.md`, `docs/RELEASE-DELTA.md` and `docs/STATUS.md`. Only CHANGELOG is handwritten; the other four are generated. No freshness SSOT/resource path appears in the unresolved list.

Actual inspected HEAD is `44622bad`; actual MERGE_HEAD is `1fe63876`, whose VERSION is `v1.22.2`. The dispatch named `3a173691`/v1.22.1, so this recommendation follows the actual conflict and explicitly preserves its additional v1.22.2 history. It does not establish upstream pipeline state or claim resolution has been executed.

## Content Comparison

| Area | HEAD | Actual incoming | Relationship |
| --- | --- | --- | --- |
| Changelog opening | Unreleased Changed (freshness v2) and Added (freshness sweep/gates) | Full v1.22.2 GTD and v1.22.1 Feedback sections, then v1.22.0 history | Additive chronological history |
| Freshness canonical content | Sweep, specify-change, plan-implementation and shaping, with bundled resources | Incoming lacks these branch additions | Preserve HEAD additions; a parent-to-parent deletion is not a resolution instruction |
| Daily update | Prior body/resources | Feedback commands, nested tab, publish-linked entries and independent review notes | Preserve incoming canonical body/resources |
| GTD | Prior planning and source rules | Capture signal test, report_only, source interview and Gmail window/cap edits | Preserve incoming canonical bodies/resources |
| Generated metadata/docs | Freshness-derived | Upstream-derived | Rebuild union; neither parent alone is sufficient |

The direct source diff confirms incoming edits to `ssot/engos-operations-daily-update.md`, `ssot/engos-operations-gtd-planning.md`, daily-update scripts/tests, and the GTD Gmail adapter. These edits are orthogonal to freshness. The controller reports README auto-merges at 46 skills; verification must confirm that count and identity set.

## Resolution Strategy

Keep the complete HEAD Unreleased section, including both Changed and Added, followed by complete incoming v1.22.2, v1.22.1, v1.22.0 and older history. Keep actual incoming VERSION v1.22.2 and incoming daily-update/GTD canonical changes unchanged. Preserve all four freshness sources and effective bundled content unchanged relative to HEAD.

Reseed only the four generated conflict paths from incoming as readable build inputs; regenerate their lasting content from the union. After building, refresh router descriptor summaries/hashes, retaining all 24 relationship semantics and the complete 46-identity catalog. If snapshot refresh changes a build input, rebuild or propagate through the repository's supported process and confirm final provider bundles agree. No hand-edited generated content is a substitute for regeneration.

## Resolution Plan

1. Continue the existing merge; confirm the inspected parents before mutation.
2. Resolve CHANGELOG additively in the order above. Preserve automatically merged README and canonical additions.
3. Reseed the four generated conflict files, build serially, and refresh router summaries/hashes as above. Keep existing relationship semantics and inventory identities.
4. Inspect changes against both parents; verify VERSION follows the actual accepted incoming ref. Incoming main contains 45 capability identities; add exactly HEAD's one freshness skill to obtain the 46-identity union.
5. Run focused and package checks, then obtain independent readback of the resolved patch before any task-branch merge commit.
6. Stop at the authorized task-branch boundary. The user's choice between the freshness work/dependency graph and the entire connected graph remains pending; retain current strict traversal until answered. Main merge, installation and release are outside this recommendation.

## Verification Steps

- Compare all four freshness SSOT source hashes and their effective resource hashes against HEAD; require equality. Confirm sweep and each gate remain present.
- Compare incoming daily-update and GTD canonical bodies/resources against actual MERGE_HEAD; require preservation, including Feedback and report_only behavior and corresponding tests/assets.
- Check canonical router catalog and each detached provider router catalog by direct set equality against all 46 descriptor identities, not only dynamic-root discovery. Confirm 24 relationship semantics remain unchanged and descriptor summaries/hashes match final content.
- Verify incoming main's 45 identities plus exactly the one freshness identity produce the union of 46. Confirm README, STATUS, canonical/provider router catalogs, other generated catalogs and package counts all agree at 46.
- Run strict surface checks and focused source, package and documentation checks required by the repository. Record commands, exits and limitations; upstream green pipelines are not proof of this union's correctness.
- Run `git diff --check`, scan for conflict markers, and require an empty unresolved-path list after staging. Independently review the actual readback and parent comparisons before committing.

## Open Decisions or Risks

The dispatch/actual-ref discrepancy must be acknowledged by the controller before execution: actual incoming contains v1.22.2, so retaining v1.22.1 VERSION would contradict the inspected source. No incompatible instruction body was exposed by the conflict list or inspected source differences. Counts, hashes, generated consistency and checks remain expected acceptance conditions, not completed evidence. The choice between the freshness work/dependency graph and the entire connected graph remains user pending; current strict traversal must remain until answered. This artifact alone grants no merge-to-main, installation or release authority.
