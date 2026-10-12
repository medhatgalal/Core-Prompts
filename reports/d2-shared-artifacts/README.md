# D2.S2: source-owned shared artifact packaging

`engos-design-specify-change` owns the unchanged SpecContract schema. The existing `engos-design-architecture` skill optionally consumes a supplied contract using its local `spec-contract` route. One finite canonical allowlist pins owner, source, digest and consumer destination. Generated provider copies are delivery artifacts, not separate authored oracles or skills to delete.

Read the evidence in this order:

1. [Independent source/package review](review-final-source-package.json) and [exhaustive source disposition](requirement-review.json): four additive architecture lines; 864 original lines, four curated modes, 32 other capabilities and seven owner files preserved.
2. [Initial code review](review-code-initial.json), [repair verification](review-repair-verification.json) and [metadata finding](review-metadata-finding.json): missing-registry trust downgrade, escaped JSON references and actual UAC/generator mode loss were reproduced, repaired, and rechecked. Earlier failing and interrupted checks remain visible with their limits.
3. [UAC receipt](uac-summary.json): distinguish the first partial write/failed validation, stale-current-source retry, pre-repair mode loss and final serialized validated apply. Repository apply is not installation. Current-source attestation is accepted; historical-baseline binding remains a separate status.
4. [Local validation](LOCAL-VALIDATION.json) and [unaltered CI verification sequence](local-ci/receipt.json): 13 steps, six disjoint pytest groups; focused reruns do not inflate totals.
5. [Independent docs review](review-docs-initial.json), [product seal](product-payload.json), [evidence lineage](EVIDENCE-MANIFEST.json), and [final review](FINAL-REVIEW.json): product identity, source truth, review, hosted CI and behavior are different evidence classes.

This draft is stacked on exact D2.S1 `2f4c16526b75b9df14da8fdedbbb76040878b6cf`, targeting `AI/d2-spec-contract`. Its 33-skill inventory includes the unmerged prerequisite; main remains 32. No new skill identity, registered agent, rename/removal, install, merge, Core version/tag or release is performed. D2.S3 trace checking, additional consumers, oracle sharing, migration and full adoption acceptance remain proposed.

The shared loader is upgraded in all existing resource-backed generated packages. Old loaders reject the new import map; future adoption must refresh the complete package atomically, preserve local customization, and validate recovery before release. The receipt binds provenance and consistency, not approval or package authenticity. JSON `$ref` and `$dynamicRef`, including decoded nested/escaped keys, are unsupported and rejected. No source is fetched or resolved at runtime, no installed sibling is needed, and no model/provider superiority is claimed.

Public evidence normalizes machine-local display paths and trailing blank pytest log whitespace. The compiler log is condensed to status, counts, all artifact hashes and its 23 advisory lint findings across 12 skills; private originals and paired hashes retain lineage. Hosted exact-head results and draft URLs are recorded in the review description and private report after the commit exists. Release remains HOLD until all accepted task dispositions and migration/docs/install/update/usage/before-after/why acceptance are complete.
