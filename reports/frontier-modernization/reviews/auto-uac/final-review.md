# Auto-Research and UAC source admission review

**Decision: approved for source requirement preservation at the identities below.** All six first-pass findings are resolved. A subsequent UAC-only review also approved the two specific agent/output sections described below. This is independent source review and deterministic attestation/assembly validation. It is not a behavioral result, promotion verdict, general implementation approval, installed-host proof, release, or merge approval.

Reviewer: `review_autoresearch_uac_admission`. Authors: `implement_skills` for Auto-Research and `root` for UAC. The parent task's independent delegation provides review provenance. Merely accepting those strings in JSON does not authenticate the reviewer. No candidate, source, resource, production code or test files were edited by this reviewer; only files beneath this review directory were written.

## Findings resolved

| Finding | Resolution checked in final content |
| --- | --- |
| AR-R1, incomplete resource binding | Auto-Research's new resource map binds shared delivery guidance, the experiment loop, all four templates and bootstrap. `effective_capability_text` now includes the complete declared package. |
| AR-R2, wrong agent resource root | The Resource Delivery Contract and Mode 4 distinguish skill `resources/...` from paths directly beneath the agent's `capability.json` directory. |
| UAC-R1, judge canonical-write ambiguity | Workflow step 11 explicitly prohibits canonical repository modifications and confines mechanical repairs to a candidate artifact. |
| UAC-R2, historical apply sequence lost | Workflow step 17 restores canonical SSOT/descriptor writes, persisted quality reviews, then surface rebuild and validation. |
| UAC-R3, unscoped output/contradiction checks | Rules scope outputs to the operative selected-route contract with precedence, review contradictions with scope/exception handling, and prevent quoted examples becoming obligations. |
| UAC-R4, reviewer/delegation ambiguity | The prohibition now addresses imported runtime/control-plane decisions. Host-authorized independent onboarding review is explicitly permitted without granting runtime policy authority. |

## Auto-Research acceptance evidence

Paths below are relative to the repository. Candidate references mean `reports/frontier-modernization/candidates/engos-optimization-auto-research.md`; loop references mean `sources/capability-resources/engos-optimization-auto-research/references/experiment-loop.md`.

| ID | Source-review result and evidence |
| --- | --- |
| A01 | **Pass.** Candidate Mode 4, lines 415-426, requires actual mutation, protected execution, scoring, keep/discard and repetition. Loop lines 3 and 11-17 prohibit substituting plans or simulated scores for executed trials. |
| A02 | **Pass.** Loop lines 6 and 11-17 distinguish original baseline, incumbent and isolated trial; reject changes restore the incumbent while retaining hypotheses, scores and traces. Candidate Experiment Ledger at line 472 and its template retain lineage and decisions. |
| A03 | **Pass.** Loop line 12 permits one or coordinated mutations with exact mutation set and joint hypothesis; candidate Rules and Self-Improvement Protocol distinguish attribution needs from blanket single-change restrictions. |
| A04 | **Pass.** Loop lines 6, 8, 13 and 22 protect evaluator, evaluation data, scoring, limits and comparison settings; measurement changes are separately declared and held-out answers stay out of candidate generation. |
| A05 | **Pass.** Loop lines 8, 13-14 and candidate Promotion Gate at line 524 permit declared quality/speed/cost/simplicity objectives, hard non-regression limits, verified equivalent-quality complexity wins and separate invalid/crashed outcomes. |
| A06 | **Pass.** Loop lines 16 and 20 plus candidate Stopping Rule at line 507 require continuation after wins and losses until declared trial/budget/target/plateau/interruption limits. Diagnosis may stop at a verified explanation/fix. Plateau does not claim a global optimum. |

The introductory objective, execution mode, rules, ledger, profiles and stopping contract agree on continuing authorized optimization. Formal promotion remains separate from provisional trial acceptance. Setup and deterministic diagnosis retain their narrower outputs and stopping behavior. Existing tool, output, trace, review and host-authority boundaries are retained.

## UAC acceptance evidence

Candidate references mean `reports/frontier-modernization/candidates/engos-meta-uac-import.md`.

| ID | Source-review result and evidence |
| --- | --- |
| U01 | **Pass at skill-contract level.** Rules line 87 require joint entry/dependency judgment and block missing files, cycles, path escapes and mismatched content bindings. Assembly and host delivery are kept distinct. General resolver implementation coverage is outside this source review. |
| U02 | **Pass at skill-contract level.** Workflow step 14, line 74, separates structural checks, semantic attestations, assembly, host delivery and behavioral results. Rule line 86 scopes output diagnostics to the operative contract and precedence; unrelated bullets/quoted examples cannot satisfy or create output requirements. |
| U03 | **Pass at skill-contract level.** Rules lines 86-87 apply scope/exception-aware contradiction review to the entry and routed dependencies. Line 97 preserves imported control-plane authority while permitting the host's independent onboarding review. |
| U04 | **Pass.** Workflow step 11, line 71, requires targeted mechanical repairs and invoking-agent/independent-review semantic repairs. Rule line 88 targets the authoritative location, reuses equivalent existing content, preserves commands/schemas/quotes/user decisions/scope, and prohibits invented facts/procedures. |
| U05 | **Pass.** Rule line 89 distinguishes exact relocation, reviewed reformulation and authorized retirement; the attestation binds original/candidate/effective hashes and complete requirement dispositions. The operator must establish provenance, and the code validates neither reviewer authenticity nor semantic truth. |
| U06 | **Pass at skill-contract level.** Workflow step 11 enumerates structure, formatting, style, ambiguity, contradictions, missing details, references, outputs, boundaries and preservation with per-dimension disposition. Rule line 90 stops stagnant/cyclic refinement and forbids new obligations or oscillation on repeated unchanged input. |
| U07 | **Implementation acceptance not assessed here.** The skill uses current canonical companion names and requires content/hash distinctions. Canonical-name evaluator dispatch and resource-aware topology implementation need their separate code and test review; these source attestations do not satisfy that implementation gate. |

The candidate retains the source/mode inventory, baseline fidelity, classification, advisory metadata, all intake outputs, companion handoffs, URL/content-type boundaries, apply confirmation, deploy separation, legacy-verdict restrictions and baseline-lineage safeguards. Historical structural `ship` is reformulated as `structural_ready`, with behavioral promotion separately gated.

## Supplemental UAC-only admission

The author added `Agent Operating Contract` and `Output Directory` before Workflow to satisfy the existing agent/template requirements with UAC-specific content. Removing exactly these two sections from the revised candidate reproduces the prior approved SHA-256 `8b3a8cba6c6eb5ac8477bb9cabacd4d84405bd125bc5fb8e5e01a3ea30ed9b42`; no other candidate text changed in this supplemental review.

- Candidate lines 54-55 retain the invoking host's runtime/authorization control, require actual independent review of material meaning changes, preserve judge's no-canonical-write boundary, and permit only authorized apply. This conditional agent contract does not itself promote capability classification or change imported runtime policy. The CLI's confirmation and judge/apply dispatch, `_apply_payload`, and requirement-review validator support these distinctions.
- Candidate lines 57-58 correctly name `ssot/<slug>.md`, `.meta/capabilities/<slug>.json`, `reports/quality-reviews/<slug>/`, baseline lineage under `sources/ssot-baselines/<slug>/`, generated surfaces and evaluation contracts. These match `quality_review_dir`, canonical writes and `compile_result` in `_apply_payload`; baseline persistence is guarded by an independently validated `promote` result. The text explicitly limits these destinations to UAC onboarding and does not invent report paths for imported tasks.

Both additions are approved. The two UAC attestations include their complete text, section-specific rationale and supporting implementation pointers, and bind the revised hash below. Auto-Research's reviewed content and attestation files are unchanged. This targeted code corroboration does not expand the review into general implementation or behavioral approval.

## Frozen identities and coverage

| Package | Candidate SHA-256 | Effective SHA-256 |
| --- | --- | --- |
| Auto-Research | `b8bf02b356e20aeb3465fa77efc50559c42b468c7881f0fdcd098a876521d7da` | `2abaaa2e5cd7af15546d22cbb22bb5aafaa43d5ffc709d1765c0ead707500ade` |
| UAC | `4d81b852a81e7d1cc8b18d41c50b36c9ce97515db66aa1984940eae8e3526571` | `4d81b852a81e7d1cc8b18d41c50b36c9ce97515db66aa1984940eae8e3526571` |

| Attestation | Complete source lines | Meaningful section spans | `validate_requirement_review` failures |
| --- | ---: | ---: | ---: |
| `engos-optimization-auto-research.current.requirement-review.json` | 699 | 65 | 0 |
| `engos-optimization-auto-research.historical.requirement-review.json` | 676 | 64 | 0 |
| `engos-meta-uac-import.current.requirement-review.json` | 169 | 16 | 0 |
| `engos-meta-uac-import.historical.requirement-review.json` | 145 | 16 | 0 |

Source spans are ordered, complete, gap-free and nonoverlapping. Exact retained sections are marked preserved. Reviewed replacements are marked reformulated with section-specific rationale and the supplied user-approved modernization authorization. Historical duplicate/misnumbered headings are corrected while retaining their complete behavior. No requirement is silently retired or treated as preserved merely because the full file is accepted.

## Verification and limits

- Read both candidates, current and historical source baselines and their differences before relying on any author grade or change map. No author grade or change map was used to establish this decision.
- Read Auto-Research's complete resource map, both references, four templates and helper source. All, experiment, templates, bootstrap and promotion routes assembled through the repo resolver with the expected dependency order; this is static assembly evidence.
- Serialized the completed review with `build_attestations.py`, which rejects candidate, baseline or effective-content drift from the reviewed hashes. All four artifacts passed the exact `validate_requirement_review` API. See `validation.json` for counts.
- No model-mediated experiment, behavioral comparison, generated-surface host invocation, deployment or reviewer-authenticity test was performed. UAC code implementation findings belong to the independent implementation review.
- The source's attribution to Karpathy is explicitly separated from local adaptations. This review assessed the supplied execution contract; it did not independently refresh the external upstream document.

Any later candidate or declared resource change invalidates these exact-content attestations until re-reviewed and rebound.
