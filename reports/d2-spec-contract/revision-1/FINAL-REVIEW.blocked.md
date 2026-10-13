# D2.S1 independent final code review

Review in progress. This file is not a final approval; the post-repair, post-CI payload is not yet bound.

## Commit Under Review

Staged D2.S1 change on `AI/d2-spec-contract`, base `5a6503b65fa28586437965ea6a01540b955fd953`. Initial payload: 75 paths, `b72366d4c772a2c110a3da80f300eb2081edf2a8f8df6644c390cc09a5f0b2c0`. Initial source SHA-256: `2380929f0571f50b167608508631216e3c05a3020eaaae4995ce831e1198da04`; initial effective SHA-256: `f3c416c7865ca755e0bfa2a77ef743883069b630fa80be3ef691ad121553a5bf`.

Reviewer: independent `/root/d2_final_review_astra`; no product edits or nested agents. Applied the actual `engos-quality-code-review` operating contract, repository AGENTS and workflow/behavior/docs steering. Review reads actual staged source, resources, tests, documentation and generated metadata; deterministic identity checks compare provider packages and baseline preservation.

## Findings

1. **P1 — stale inventory expectation blocks CI.** `tests/test_uac_ssot.py:27` still asserts 32 shipped capabilities while this slice adds the 33rd. `reports/d2-spec-contract/local-ci/receipt.json` records the actual failing test with 314 other tests passing in that batch. Update the expected inventory and verify the new skill identity; rerun the affected tests and complete the remaining CI path.
2. **P2 — generated minimal inputs/outputs describe UAC intake, not specification work.** `.meta/capabilities/engos-design-specify-change.json:22` through the expected-output fields and the corresponding handoff entry contain generic source-text/user-intent inputs and uplift/deployment outputs. The richer source-derived job contract is correct and the intake-only tool policy limits authority, but the minimal interface still misdescribes the new skill's job and conflicts with `ssot/engos-design-specify-change.md:120`. Express the existing Required Inputs and Required Output content in the parser-supported structure, preserve all meaning, and regenerate through the existing pipeline; no generator expansion is required.

## Scope Assessment

The inspected initial change is D2.S1 only: one new skill, seven owned resource files, schema/loader tests, generated metadata, five portable skill packages and user documentation. No agent, consumer integration, shared import, production trace checker, shaping mutation, merge or installation is included. All 35 baseline SSOT files (32 capabilities plus three control files) remain byte-identical, and no existing provider package path is changed.

The source has a meaningful job distinct from adjacent skills: it specifies observable behavior and acceptance for a bounded change; framing establishes a solution-free problem, shaping owns pitch/acceptance process, architecture chooses technical structures, and plan-to-goal compiles execution packets. The new skill preserves existing authorization, holds only dependent scope on unresolved material decisions, makes sidecars conditional, and retains reported/observed and expected/unchanged distinctions for bugfixes.

The seven canonical resources match their copies on all five providers. The bundled loader is byte-identical to unchanged `src/intent_pipeline/capability_resources.py`; all five skill bodies match the SSOT after standard frontmatter/footer generation. Metadata aggregates preserve prior entries. Topology references bind all eight source/resource files. Draft evaluation metadata is not behavioral coverage or promotion evidence.

## Message Assessment

No proposed commit message supplied yet. The final message must describe the new specification skill and optional contract, with draft-only delivery and no behavioral-promotion claim.

## Recommended Fixes

Resolve both findings, renew exact source/effective/package bindings and relevant independent requirement review, complete local CI, and submit the final staged payload for binding. Do not broaden this slice to metadata generator refactoring or downstream consumers.

## Merge Readiness

**Blocked pending the two findings and final evidence binding.** This task authorizes draft PR/MR review only; even a passing final code review will not authorize merge, release, installation, or behavioral promotion.

## Evidence limits

The initial focused log records 67 passed tests. New schema tests exercise shape, required fields, bugfix triad, invalid values/digests, explicit non-enforcement of ID uniqueness/approval, route closure, relocation and a blank non-coverage ledger. `jsonschema` and the existing test module are included in both CI providers. Source truth, unique ID values, authority, decisions, reference validity, semantic correctness and runtime behavior remain separate checks.

The private source admission distinguishes pinned MIT Addy patterns, fresh October 11 public Kiro documentation and frozen October 9 research; no native Kiro equivalence, historical skill baseline, efficacy or savings follows. The candidate-seed intake is honest new-source provenance rather than preservation evidence. An eventual single forward authoring case, if assessed, cannot establish comparative benefit or promotion.

The two private report JSX changes were inspected: D2 receipt appears only for the selected D2 package with data present, uses the existing renderer, adds a new-skill heading, and preserves D1/D6 identities. Receipt data and rendered UI have not yet been reviewed here.
