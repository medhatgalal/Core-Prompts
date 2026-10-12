# D6.S1 independent requirement review

## Commit Under Review

This is sealed candidate review before canonical apply, not a committed or hosted review. Base: `5a6503b65fa28586437965ea6a01540b955fd953`; branch: `AI/d6-review-targets`. Reviewer: `/root/d6_requirement_review_astra`; author: `/root/d6_implementation_astra`.

- Candidate SHA-256: `c5d128e24dc1a37bd74af3aba75f667b0da32df630eb810930f1a4a5badab558`.
- Actual `effective_capability_text(..., route="all")` SHA-256: `8f7ce683c13206b41b81ca4204b6f06cbb936d3a6ecf8b6972e08b8458d7a1e4`.
- Review-route bundle SHA-256: `3ed0d2ee715d473e91572a80b0711d421ec9279c5d26bfed9af078cbb1a347de`.

Independently recomputed the candidate, actual effective closure, review bundle, original/current source, historical baseline and every sealed packet file hash. Read the complete current and historical originals, candidate, resource map, target reference, Findings.v1 schema, selected donor clauses/licenses, changed documentation and test diff. The author-proposed mapping was not used as an independent attestation.

## Findings

No open material objection to revision 2.

**D6-IR-001 — resolved:** The first seal's Capture the Commit prose required a selected merge-parent patch, but its `git show ... HEAD` example could present a combined or empty merge diff. That conflicted with exact-target semantics. The writer repaired candidate lines 105–128 to resolve `REVIEW_HEAD` once, distinguish non-merge/root capture, use an explicitly selected full `REVIEW_PARENT` for the merge diff, and recheck ref drift. Independently read the repair and reran the bound non-merge show and selected-parent merge diff in the author's Git fixture; both showed the expected feature patch. The superseded candidate was `706ac622afe7c0ef0c41ae075c478b364d775e9a9aa44678bdfa8302f1f5455c`; approval applies only to revision 2.

## Scope Assessment

One same-name skill remains. S1 adds target, changed-cause, actual consumer and structured finding semantics. It does not add the S2 collector/ReviewPackage schema, S3 consumers, an alias, or a named agent. Current scope, simplicity, security, lifecycle, concurrency, operational, API and message checks remain. All six required response sections remain. Repair, posting, merge, installation and release authority remain outside review.

Selected Addy, Grok and Superpowers local hashes match the frozen admission record. Selected passages and available MIT license notices were inspected. The additions independently express the selected patterns; no substantial donor passage, collector implementation, host-specific publisher, mutation-testing command or multi-model mandate was imported. Grok redistribution clearance remains unknown and is not inferred. Existing loader and schema dependencies are disclosed; no donor runtime dependency was added.

The complete reference/schema route is required, but this is not accompanied by mandatory paid testing, broad test execution, mutation tests or fixed review-size thresholds. Applicable source and caller reads remain tied to material risk. Increased package size alone is not treated as a regression or proof of improved behavior.

## Message Assessment

No final commit message exists at this pre-apply checkpoint. The candidate and changed docs consistently describe the authorized S1 contract scope and separate structural validity from actual review accuracy. A later commit/branch review must assess its real message and final generated diff.

## Recommended Fixes

D6-IR-001 has been verified resolved. No further candidate/resource fix is required for source-preservation admission. The controller must preserve these exact bindings through apply and inspect the actual generated write set; changes to the candidate or effective resources invalidate the attestation.

## Merge Readiness

**Source-preservation admission: approved for the sealed revision only.** `requirement-review-current.json` covers all 317 current lines in 28 contiguous mappings; `requirement-review-historical.json` covers all 236 historical lines in 25 mappings. Both validate with the repository's real `validate_requirement_review`. IDs are reviewer-assigned source-line identifiers, not purported extractor output. The records contain no invented human approval and no agent execution need.

This does not establish behavioral promotion, hosted readiness or permission to merge. The controller's PR/MR-only scope remains. Canonical apply, generation and subsequent checks are not performed by this reviewer.

## Edit ledger and preservation map

No product artifact was edited by this reviewer. The two JSON mappings preserve every source range. Changed clauses explicitly account for stronger target/caller bindings, precise finding locations, incomplete/unverifiable outcomes and six-section output. Historical aliases normalize to existing current identities. The old unconditional artifact-writing example is reformulated consistently with both sources' request-only Output Directory/Tool Boundaries and the authorized read-only scope; its review/capture obligations are not silently retired. All six hard-constraint sentences remain verbatim under the normalized Constraints heading.

## Before / after size

| Material | Lines | Words | UTF-8 bytes | Approximate tokens (bytes/4) |
| --- | ---: | ---: | ---: | ---: |
| Current source | 317 | 2,316 | 15,295 | 3,824 |
| Candidate entry | 355 | 3,015 | 20,216 | 5,054 |
| Effective candidate plus closure | 732 | 4,990 | 39,452 | 9,863 |

Token counts are rough estimates, not measured usage or quality scores.

## Observations and behavioral claims requiring proof

`independent-observations.json` records 14 independently executed positive/negative JSON Schema observations, all with expected outcomes. The default `python3` lacked `jsonschema`; the checks reused `Python3.14.8 in a task-local environment with declared CI dependencies` without installing dependencies. The author separately reports 32 schema cases and 65 focused tests; those counts are not relabeled as reviewer executions.

Structurally valid fabricated read claims, duplicate/dangling evidence IDs, wrong claimed revisions and invented consumers demonstrate limits of schema validation. The reference explicitly requires actual ID resolution, bound revision/source inspection, consumer verification, causal attribution and authority checks. An unrelated pre-existing defect or unsupported caller claim cannot become introduced breakage merely by filling valid fields. No schema result proves those semantic facts.

All 18 planned cases have a separate source-contract assessment, marked `contract_inspected` and behavioral execution `not_run`. Reading instructions supports the stated contract implications, not model compliance or task-level efficacy. There was no comparative pilot, paid model trial, accuracy measurement or behavioral uplift claim. A review artifact is not proof of future execution.

## Unresolved ambiguities

No material unresolved contradiction remains in the reviewed S1 contract. Runtime adherence, actual future reads and later hosted/build evidence remain outside this requirement-review claim. The genuine reviewer identity is recorded by this separate task, while the UAC validator explicitly cannot authenticate identity on its own.
