# D1.S1 independent pre-commit review

## Commit Under Review

- Reviewer: `/root/d1_final_review_astra`, independent of the candidate author and prior requirement reviewer.
- Review began against the actual **unstaged working-tree diff**, including every new untracked product resource. At final seal, the controller had staged precisely those 80 product paths for the index-dependent packaging retry. Independent readback verified the same payload digest and no unstaged product changes. This remains a pre-commit source review; no commit existed at seal.
- Branch: `AI/d1-authoring-contracts`.
- Base/HEAD: `5a6503b65fa28586437965ea6a01540b955fd953`.
- Proposed title: `feat(skills): add proportionate authoring and preservation contracts`.
- Authority: D1.S1 under existing names; draft PR/MR for human review. No merge, installation, release, new named agents, renames or D1.S2 work.
- Reviewed product payload: 80 paths, SHA-256 `c9b04205784cea34c86f8b05fc2c024d98d49c4c062d857d69c08504c6b8635f`.
- Payload binding: sorted union of `git diff --name-only HEAD` and `git ls-files --others --exclude-standard`, excluding `reports/`; SHA-256 of UTF-8 JSON array of `{path, sha256}` records, serialized with sorted keys and compact separators. Each file hash covers its exact bytes. Review artifacts are excluded to avoid self-reference.

| Canonical candidate | SHA-256 |
| --- | --- |
| `ssot/engos-meta-uac-import.md` | `65be626e073f50d28be83b488817c326a853dc92937d5d0a8c0478b1f1c6eb00` |
| `ssot/engos-meta-instruction-editor.md` | `664a802ed009e967b598da307a40bcfef3bc01fbf199132eca8452a4b3687c86` |

Both source files match the independently reviewed candidate bytes. Current-source and historical UAC review attestations bind the source, candidate and effective resources; editor current and historical source bytes are identical. These attestations are source-level review evidence, not model efficacy evidence.

## Findings

No blocking defect found in the canonical instructions, owned resources, generated packages or public command examples. The following observations retain their initial state and resolution status.

1. **P2, verification process — resolved.** `tests/test_package_surfaces.py:198` and `tests/test_package_surfaces.py:247`, as recorded in `local-ci/packaging-profiles.log`, fail because release-fixture construction and the inventory assertion use `git ls-files`. The reviewed resource files are still untracked in this unstaged review. One fixture filters them out of the archive, producing a missing `resources/resource-map.json` error; the other reports the same new files absent from the tracked inventory. The batch reports **253 passed, 2 failed, 16 subtests passed**. Correction performed by the controller: staged precisely the reviewed 80 product paths, then reran these two checks. Both passed in **20.86 seconds**, exit zero, with no source or test changes. `LOCAL-VALIDATION.json` preserves the original failure and recovery; the reviewer independently recomputed the unchanged payload digest and verified all 80 product paths were staged with no unstaged product changes. The reviewer has not staged files.
2. **P2, generated status — resolved.** Initial `docs/STATUS.md` reported seven validation errors and no smoke report from the earlier failed apply. The controller's serial validation/smoke/build refreshed it: zero validation errors and warnings, zero smoke failures, one Gemini discovery timeout warning. Current status is truthfully `warn`, not a fabricated clean host probe. Verified against `local-ci/smoke.log` and `local-ci/strict-surfaces.log`.
3. **P3, retained evidence wording — resolved.** `D1-S1.md` previously retained present-tense pre-apply statements, while `review-packet.json` still said review was pending. The earlier state is now explicitly labeled a historical checkpoint with links to subsequent authentic review/apply evidence. Frozen bindings and initial failure records are preserved.

## Scope Assessment

The source change is limited to two existing skills. UAC gains the reuse/harvest/combine/new decision, one receiving owner, conditional source-admission detail and a preservation/displacement template. The editor gains a semantic-change ledger and conditional companion handoffs while remaining independently callable. Exact relocation and low-risk contract-neutral editing use preservation and structural checks; material meaning changes retain explicit intent and independent review; comparative behavioral claims retain bounded independent evaluation. Neither route introduces blanket model experiments.

Verified against actual files and unchanged base:

- All 32 capability identities, display names, descriptions, curated validation matrices, baseline metadata and curated job-contract fields are preserved. No baseline-tree edits, new named agents or expanded provider scope.
- Both complete source bodies, five new canonical resource files, the existing clarity policy, generated eval contracts/topologies, metadata aggregates, install manifest, public docs and all 40 untracked product files were inspected. Provider body changes are identical across all five providers.
- All ten bundled capability descriptors match their canonical descriptors. Owned resource copies match canonical bytes. All ten newly emitted `load_module.py` files match the existing `src/intent_pipeline/capability_resources.py` exactly. No generator, parser, test or shared runtime source changes.
- The UAC authoring route owns its template dependency. Editor audit selects the existing clarity reference; rewrite/diff/verify add the ledger. Entrypoints state when to read the resources. There are no sibling-skill private-file dependencies or added runtime routing authority.
- Templates explicitly state `template_not_evidence` and cannot stand in for an independent requirement attestation or promotion verdict. They add no shared schema-validator infrastructure.
- Aggregate manifest changes are confined to the two skill records and seven added resource paths per provider. All 59 changed install-manifest entries match their actual file hashes; no inventory removal. The broad generated diff follows existing serialization, review metadata and source/resource hash propagation.
- No maintainer home paths, temporary candidate paths or absolute machine source references occur in the 80 product paths. Repository-relative capability metadata remains portable.
- README, getting-started, examples, UAC usage, CLI reference and changelog explain the behavior in their existing documentation roles. Current wrapper source and actual `plan --help` / `judge --help` support the documented commands and flags. Generated status and release delta remain inspection aids.
- Both original apply attempts returned process exit zero but payload `apply_failed_validation` because required vendor cache entries were absent. That failure remains recorded separately from cache recovery, serial build and strict-validation success. No failed apply payload is presented as a passing gate.
- The six semantic fixtures are source-level acceptance observations, including one existing-loader missing-resource check. They are not a model pilot, comparative improvement result or CI replacement. `behavioral_pending` remains explicit; no source hash, lint score or completed ledger is treated as efficacy proof.

The two source changes and generated artifacts form one coherent D1.S1 patch. No split or scope reduction is necessary. External donor licensing and runtime efficacy were not re-investigated over the network in this review; the resources preserve those stated evidence limits and use independently expressed patterns.

## Validation Evidence at Final Seal

The controller's recorded GitLab-aligned local sequence and targeted recovery give **1105 distinct tests passed, 1 skipped, 16 subtests passed**. The 45 pre-review checks overlap that sequence and are not added again. Counts reconcile as 288 resource/UAC, 480 shaping, 19 presentation, 58 routing, 5 bootstrap, 253 initial packaging passes and 2 focused packaging retry passes. Strict surface validation, contract compilation, static-only calibration, installer capsule and legacy catalog checks passed. The reviewer inspected the receipts, decisive failure/success outputs and `.gitlab-ci.yml`; this review did not independently rerun the entire suite.

`docs/STATUS.md` accurately retains the one live Gemini discovery timeout: zero smoke failures is not a successful Gemini native-discovery observation. One shaping test was skipped. Static calibration used zero model calls and does not qualify semantic judges or establish efficacy. Hosted checks, actual user-home installation and behavioral promotion remain unverified/out of scope.

Final readback after the controller's index recovery: product digest remains `c9b04205784cea34c86f8b05fc2c024d98d49c4c062d857d69c08504c6b8635f`; all 80 product paths are staged and there are no unstaged product changes. `git diff --check` passed during review. The staging operation is attributed to the controller, not this reviewer.

## Message Assessment

The proposed title accurately states the delivered behavior and makes no efficacy, installation or release promise. The eventual body should explain that admission and preservation use checks proportionate to the change, while behavioral claims still require separate proof. It should identify the two current skill names, note generated resources/docs, summarize validation, and retain the review-only/no-merge boundary and Gemini discovery warning.

## Recommended Fixes

No source-code or instruction correction remains. Retain the original failure and retry evidence, commit the sealed product payload with the selected durable review evidence, and obtain hosted GitLab/GitHub checks on that exact resulting commit. Any product-byte change invalidates the payload seal and requires affected review renewal.

## Merge Readiness

**Ready for review-only PR/MR pending hosted checks.** Zero open blocking findings. The local process failures are resolved on the unchanged reviewed payload, with their history retained. This verdict authorizes no human merge, installation or release. The controller owns staging, commit, hosted checks and delivery; the reviewer performed no Git mutation.
