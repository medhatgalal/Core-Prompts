# D7.S1 final code/package review

## Commit Under Review

Pre-commit review of the actual working tree and staged diff against `5a6503b65fa28586437965ea6a01540b955fd953`, branch `AI/d7-test-oracles`. This is not a reviewed commit yet. Reviewer `/root/d7_final_review_astra` used the actual `engos-quality-code-review` contract and Core AGENTS/steering. Product reads only; this reviewer authored no product changes.

Assessed source SHA-256: `10c8c23ea06fd358d8bcefcd08d4f6f6b625b7ac67477e8033618c86addfa74a`; effective source/resource binding: `fda56648c638406be64f028ad6a2dd74b2aa2d8758a18c2e15f4fafec2561d1c`. Updated author seal: `78ecaa83f9995100d1b12284575021897cfe948590d13552323d655564653359`. Every file hash in that seal was freshly checked and matched. Final controller product seal and complete CI evidence are pending.

## Findings

### D7-F1 — P2 — Preserve curated mode contracts when adding routed resources

**Status: open.** Location: `.meta/capabilities/engos-quality-testing-review.json:199-205`, repeated in all four modes, all five provider `resources/capability.json` packages and `.meta/manifest.json`.

The actual diff replaces each existing mode's specific `mode_summary`, `required_inputs`, `expected_outputs`, `examples` and `uplift_notes` with a generic heading description and empty arrays. For example, Generate Unit Tests previously declared code/framework/behavior inputs and test-file/fixtures/coverage-note outputs; the applied descriptor now declares none of them. The four mode identities and their SSOT prose remain intact, but descriptor consumers lose their per-mode contract.

The existing build branch at `scripts/build-surfaces.py:572-574` chooses heading-only `extract_capability_modes` whenever a resource map exists. D7.S1 introduces that map, making this a newly exposed package regression. `src/intent_pipeline/uac_modes.py:38-53` supplies the empty fields. `src/intent_pipeline/consumer_shell.py:317-324` treats mode changes as contract-facing; the generated `docs/RELEASE-DELTA.md` independently records this material change. Repo Workflow step 3 requires preserving curated metadata; the frozen D7 scope requires preservation of modes/contracts.

**Concrete repair:** retain source-derived mode identity and current source references while preserving verified descriptive fields for matching current modes through the canonical generation path. Add a focused regression proving a same-slug resource-backed update retains those fields across canonical and bundled descriptors. Do not hand-patch emitted packages or restore removed identities from stale metadata. Renew package validation and the final seal after repair.

## Scope Assessment

Canonical source changes are narrow: command provenance, discriminating observable oracles, and explicit resource/interchange guidance. All four source modes, four global input classes, six human artifact sections and the complete current three-role review protocol remain intact; the review section was compared byte-for-byte with captured current source. No source rename, new agent registration, shared import or D5/D2 consumer is present in the actual change inventory.

The new reference correctly distinguishes outcome discrimination from fake mock choreography while permitting instrumentation at a contractual effect boundary. The expiry equality and pre-expiry observations distinguish both a greater-than mutant and an always-reject implementation. Redeemed-token rejection also observes grant state; the notification example explicitly limits a delivery-boundary observation to attempted delivery. These are inspected design examples, not executed behavioral tests or evidence of model improvement.

TestDesign.v1 has the frozen top-level and per-test field shape, constant `not_run`, optional machine interchange, and coverage-only empty-test support. Required source and runner uncertainties remain explicit. The schema intentionally cannot prove semantic oracle quality, traceability or coverage; the prose and added tests say so. No new runtime validation dependency, invented default runner, blanket full-suite mandate, code-deletion prescription, production implementation or automatic skill handoff is introduced.

Five provider skill bodies contain the full canonical body, all four authored resource files are byte-identical to canonical resources, each bundled descriptor equals the canonical descriptor, and bundled loaders equal the existing standard-library loader. Display name, description, global install guidance, quality matrix, historical baseline and consumption hints compare equal to the captured descriptor. The mode-field loss above is distinct from these passing checks.

The five public docs now describe the applied skill accurately without the stale not-yet-applied wording. Their exact final hashes match the updated author seal. Generated status and release-delta files remain subject to final validation/readback. The actual diff contains no unrelated product changes; its bulk comes from generated packages and copied existing loader bytes.

## Message Assessment

No implementation commit exists yet; HEAD remains the base merge. A future commit message should describe strengthening test-design oracles under the current name, optional design-only interchange, and resource packaging without claiming executed production tests or behavioral promotion.

## Recommended Fixes

Resolve D7-F1 through the author/controller and return the final generated package plus controller validation/product seal to this same reviewer. Final required checks are not waived by source acceptance or package byte equality.

## Merge Readiness

**Blocked for a zero-findings draft-ready acceptance: one open finding, D7-F1.** The source design is acceptable within this review; final package acceptance is not complete. Complete CI and final product binding remain pending. This review never authorizes merge, install, release, rename, D7.S2/S3 or behavioral promotion.
