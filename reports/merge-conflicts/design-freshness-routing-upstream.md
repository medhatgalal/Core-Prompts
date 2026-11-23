# Freshness / routing upstream merge recommendation

## Inversion Analysis

This integration would fail if it discarded incoming router or Crew behavior, restored an old catalog over incoming curation, lost freshness gates, conflated inventory hashes with reviewed relationship evidence, or claimed coverage or user scope approval from mechanical checks. Preserve canonical behavior from both sides and regenerate derived artifacts; verify identity, content and handoff semantics separately.

## Conflict Summary

The actual unresolved list contains 18 paths, rather than the dispatch's 19: five providers' router `resources/capability.json` and `resources/routing-relations.json` pairs; `.meta/capabilities/engos-route-intent.json`, `.meta/install-bundle.json`, `.meta/manifest.json`, `.meta/skill-job-map.json`; `CHANGELOG.md`; `docs/STATUS.md`; `evals/topologies/engos-route-intent.json`; and the canonical `sources/capability-resources/engos-route-intent/routing-relations.json`.

The requested immutable parents are HEAD `d583684a` and incoming `953130dc10c374b6c67ad07cd494509886a16883`. No freshness source conflict appears in the unresolved list. This is a recommendation, not evidence that resolution has executed. The controller reports incoming MR184 pre-merge pipeline 7387999 green and main pipeline still running; neither establishes the union's result.

## Content Comparison

| Area | HEAD contribution | Incoming contribution | Treatment |
| --- | --- | --- | --- |
| Changelog | Freshness v2 Changed and sweep/gates Added bullets | Router catalog/drift check and Crew clarification bullets | Preserve both groups under one Unreleased header |
| Router descriptor | Relative to `1fe63876`, only effective, resource and mapping hash changes | Accepted router metadata/behavior | Retain incoming behavior, rebuild hashes from union |
| Canonical table | Freshness inventory/bindings | Refreshed catalog and accepted relationships/curation | Start from incoming semantics; add union inventory and reviewed freshness endpoint hashes |
| Crew | Earlier body | Attended/unattended preflight, elapsed qualification and monitor evidence clarification | Preserve incoming body |
| Tests/tooling | Freshness tests | Router drift tests and native refresh script | Preserve both auto-merged test sets and incoming script |

The inspected incoming source diff from `1fe63876` adds `scripts/refresh-routing-catalog.py`, changes the canonical router table, Crew SSOT and router resource tests. The native script refreshes inventory summaries/descriptor hashes only, uses a self-routing exception for the router, and explicitly does not refresh relationship endpoint hashes.

## Resolution Strategy

Use incoming canonical routing relationships and curation as the semantic baseline. Preserve incoming router and Crew behavior and the native refresh script unchanged. Refresh the inventory with that script against the union descriptors: all incoming 45 identities plus exactly the freshness skill, totaling 46.

Separately check all 12 corresponding handoff clauses across 11 relationships, then rebind only their `source_ref` descriptor hash fields: five for shaping, four for specify-change and three for plan-implementation. Preserve all 24 incoming relationships and their semantics. The standalone freshness skill is only a catalog entry, not a relationship endpoint, and remains in the 46-entry inventory. An inventory refresh alone cannot authorize those evidence bindings. Rebuild the router descriptor on the resulting union table; do not retain stale HEAD or incoming derived hashes as the final result.

Keep one Unreleased header containing both branches' bullet groups, followed by unchanged incoming v1.22.2 and older history. Treat all generated conflict versions as temporary readable build inputs, then regenerate them through the supported build process. Preserve both automatically merged test sets.

## Resolution Plan

1. Confirm exact parents match the immutable hashes above and continue the existing merge.
2. Resolve CHANGELOG additively and take incoming canonical routing semantics/curation and router behavior as the baseline.
3. Preserve freshness canonical sources/resources and incoming Crew/script/tests; refresh union inventory using `scripts/refresh-routing-catalog.py`.
4. Verify all 12 corresponding handoff clauses across 11 relationships against the final shaping, specify-change and plan-implementation bodies/resources, then rebind only their 12 `source_ref` descriptor hashes (five, four and three respectively). Preserve all 24 incoming relationships, their semantics and every other binding; keep the standalone freshness skill in inventory only.
5. Rebuild the router descriptor and all generated conflicts from union canonical inputs. Repeat the supported refresh/build sequence only as needed to make final inventory and descriptor hashes consistent.
6. Run the checks below and independent readback of the actual resolved patch before a task-branch commit. Do not infer authority for main merge, installation, release, live coverage or scope expansion.

## Verification Steps

- Require direct set equality between all 46 descriptor identities, canonical router catalog, and every detached provider router catalog; confirm README, STATUS and package inventories agree at 46.
- Run the native refresh script's `--check` against final descriptors. Confirm the router self-reference remains the script's documented exception and generated provider pairs match canonical outputs.
- Compare all 24 relationship/curation semantics against incoming. Permit only the 12 reviewed `source_ref` descriptor hash rebindings across 11 relationships for shaping (five), specify-change (four) and plan-implementation (three). Check all 12 corresponding handoff clauses against final endpoint content and record readback evidence. Confirm the standalone freshness skill remains a catalog entry and gains no relationship endpoint.
- Compare freshness source/effective resource hashes against HEAD and incoming Crew/router behavior and native script against incoming; investigate any change beyond the stated derived metadata integration.
- Preserve and run focused freshness and incoming router test coverage, strict surface validation and relevant package checks. Record exact commands, exits and limitations. Check the still-running incoming main pipeline independently before relying on its result.
- Run `git diff --check`, scan for conflict markers and require no unresolved paths after staging. Independently inspect the final union against both immutable parents before committing.

## Open Decisions or Risks

The observed conflict count is 18; any nineteenth target must be identified rather than guessed. Reviewed endpoint hashes and inventory hashes serve different purposes, so hash agreement alone does not prove handoff validity. Live provider coverage remains unestablished by this merge. The user's choice between freshness work/dependency graph and entire connected graph remains pending; retain current strict traversal until answered. No scope approval or main/install/release authority is supplied by this artifact.
