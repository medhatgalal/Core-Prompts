# Independent Supercharge Admission Review

**Verdict: approved for source-contract admission, after four preservation findings were resolved.** No remaining semantic-loss or contradiction blocker was found in the reviewed candidate and declared resources. This is not a behavioral promotion verdict.

Reviewer: `review_supercharge_admission`. Author: `implement_skills`. Review date: 2026-09-08. Workspace identity was verified as `/Users/medhat.galal/.codex/worktrees/921d/Core-Prompts`, branch `AI/frontier-capability-modernization`, HEAD `c9d6de07b4d1918970a5f70350cf50200a6a0ff4`. Other agents' dirty implementation work was preserved.

## Findings and disposition

| Finding | Original evidence | Initial gap | Independently verified resolution |
| --- | --- | --- | --- |
| F01 | Historical baseline:283–292 | `/simple` retained an Examples heading but lost the required 1–2 domain-tailored examples and one-general-example fallback. | `references/modules/simple.md:79–80` now requires those examples at runtime and explicitly says reference examples do not substitute. |
| F02 | Historical baseline:325,328,336 | `/simple` lost explicit MUST/PREFER separation, one-way dependencies, and invariant validation beyond outcomes. | `references/modules/simple.md:14–16` restores all three as concrete constraints, including retained guarantees, side effects, and failure behavior. |
| F03 | Historical baseline:413 | `/contract` lost primary-value-over-secondary prioritization. | `references/modules/contract.md:8` restores that ordering and requires an explicit trade-off when values conflict. |
| F04 | Historical baseline:441–442 | `/grade` no longer explicitly restricted activation to user invocation or `/full`. | `references/modules/grade.md:6–7` restores that boundary and honors `skip grade`. |

The reviewer sent these findings before approving the candidate. The author made the changes; the reviewer did not modify candidate or implementation files. Complete updated `simple.md`, `contract.md`, and `grade.md` contents were read again before final approval.

## Edited Artifact

No edit requested or performed by this reviewer. The reviewed entry is `reports/frontier-modernization/candidates/engos-meta-supercharge.md`. The complete declared resource package is `sources/capability-resources/engos-meta-supercharge/`.

## Edit Ledger

The authorized semantic changes are actual independent subagents and cold initial reviews; model-guidance maintenance; material ULT improvement with scoped print-then-execute behavior; `/full` execution precedence; true first-principles reasoning; actual unbraiding; causal inversion with observation-channel checks; grounded adversarial acquittal and independent councils; obligation-based contract verification; real independent candidate grading with best retention and bounded stopping; verified plain-English catchup; conditional fictional gaslight framing; full resource delivery; and retirement of global `/stop` only.

The current and historical maps classify each source span as preserved, reformulated, relocated, or explicitly retired. Historical self-grading, fixed twenty-percent claims, exactly-ten fabricated improvement pressure, simulated review, fixed top-three inversion, and universal gaslight claims are reformulated under the approved modernization rather than silently treated as unchanged. F01–F04 were preservation defects, not authorized retirements, and were repaired before admission.

## Preservation Map

Entry line references below refer to the 292-line candidate. Resource references resolve under `sources/capability-resources/engos-meta-supercharge/`.

| ID | Contract review result and evidence | Limit |
| --- | --- | --- |
| S01 | Verified. Entry:216–219 and `references/shared-review.md:3–9` require actual independent agents, forbid self-review/simulation, and recover failed delegation or leave review incomplete. | Instruction and independent-review provenance, not general host enforcement. |
| S02 | Verified. `references/shared-review.md:5` withholds author verdict/self-grade and other initial conclusions, preserves fair factual context, then allows exchange. | Does not prove independent error sources or unbiased model behavior. |
| S03 | Contract present. `references/model-guidance.md:3–18` has dated model/version rows, evidence classes, one monthly/event research-only workflow, stale retrieval handling, and no silent skill edits. | Provider claims and links were not independently fact-checked in this semantic review; no monthly run is proved here. |
| S04 | Verified. `references/modules/ult.md:10–14` replaces an unconditional percentage with material reasoning/completeness/usability/reliability/efficiency benefit; percentages require metrics and baselines. | Meaningful improvement on real tasks still needs evaluation. |
| S05 | Verified. `references/modules/ult.md:16–24` displays a copy-ready reviewed prompt, announces execution, then runs within authorization; explicit draft/review-only suppresses it. | No generated task was executed by this review. |
| S06 | Verified. Entry:228–229, `ult.md:21–22`, and `full.md:7–9` explicitly announce no task execution for the combined stack while retaining ULT persistence. | Runtime precedence was not model-tested. |
| S07 | Verified. `references/modules/basis.md:3–30` derives sufficient design from primitives, preserves sophistication and safeguards, and permits qualitative/unknown minima with evidence-based ratios only. All six original output fields remain. | Correctness of a derived design is task dependent. |
| S08 | Verified after F01–F02. `references/modules/simple.md:7–16,47–51,79–90` retains Hickey-style independence, removes an actual dependency, tests independent change, restores invariant/priority/dependency details, and requires tailored examples. | No simplification experiment was run. |
| S09 | Verified. `references/modules/invert.md:3–18` starts from an unwanted result, derives causal paths, distinguishes evidence/hypothesis/unknown, and checks expected signals, detectability, opportunity, and alternative explanations. The three output fields remain. | Missing signals are explicitly not automatic evidence of safety. |
| S10 | Verified. `references/modules/adversarial.md:8–22` requires actual attackers and concrete grounded findings, allows a supported no-material-issue result, and retains the four outputs. | Acquittal applies only to inspected evidence. |
| S11 | Verified. `references/modules/adversarial.md:24–91` preserves shortcuts, profiles, surface/deep outputs, rebuttal order, invalid `/deep` handling, and a separate Decider with rejection/uncertainty authority. | Confidence is judgment unless calibrated; no debate experiment was run. |
| S12 | Verified after F03. `references/modules/contract.md:3–43` maps obligation/source/acceptance/evidence, versions criteria before independent checking, preserves primary value, and retains the two outputs. QA JSON is byte-identical to both source baselines. | Schema preservation does not prove a checker will judge correctly. |
| S13 | Verified after F04. `references/modules/grade.md:6–25` restricts activation, defaults to up to ten actual trials, requires at least two absent user/hard limits, freezes the rubric, requires independent grades, retains best/original, and permits default early completion only after target plus two distinct unsuccessful substantive attempts. | Review scores are not measured downstream efficacy. |
| S14 | Verified. `references/modules/full.md:6–21` preserves sequential SIMPLE/INVERT/ADVERSARIAL/CONTRACT/GRADE, basis opt-in, skip grade, no execution, and explicit finding carryforward. | The grade caption changes only to reflect the approved real-trial contract. |
| S15 | Verified. `references/modules/catchup.md:7–53` keeps all visible table rows and validation text, adds independent verification and plain-English reconstruction, and prohibits inventing next steps to fill a quota. Table and validation are byte-identical to the current baseline. | Accessible history limits are disclosed as `[Unclear]`. |
| S16 | Verified. `references/modules/gaslight.md:3–44` retains all 13 IDs/names/templates/examples and explicit-only task/list/help/exact-selection commands. Effects are conditional, fictional premises are labeled, and factual or capability guarantees are rejected. | Comparative efficacy and cited research relevance were not experimentally established here. |
| S17 | Verified structurally. Entry:221–226 and `references/shared-review.md:11–13` require full actual tool/host payloads for each reviewer, reject self-authored read receipts, and reload changed resources. All 19 declared routes assembled successfully with the local loader. | Assembly/delivery is explicitly separate from comprehension and obedience. |
| S18 | Verified structurally. Entry:241–266, bundled help/examples, and the details route retain terminal output selection and complete module aggregation. Details module ordering matches the declared reference order. | No model-mediated help/details run is claimed. |
| S19 | Verified. No global `/stop` token remains in the effective package. Entry:125–129 and `references/modules/stop-ult.md:1–3` retain `/stop-ult`; `ult.md:6–8` preserves mode persistence. | Historical source archives intentionally retain the retired command for comparison. |

Machine-readable attestations:

- `current-requirement-review.json`: 88 meaningful ordered spans cover all 722 current-baseline lines, without gaps or overlap.
- `historical-requirement-review.json`: 69 meaningful ordered spans cover all 526 historical-baseline lines, without gaps or overlap.
- `review-binding.json`: full entry/effective hashes and each declared resource hash.
- `review-checks.json`: static shape, assembly, source coverage, and size evidence.

Both attestations pass `validate_requirement_review` with zero failures. This validates binding and coverage; semantic judgment remains the responsibility of the independently dispatched reviewer. Global `/stop` retirements each record the explicit S19 authorization. Each nonretired requirement contains a meaningful excerpt present in the effective candidate package.

## Before / After Size

| Artifact | Lines | Words | UTF-8 bytes | Approximate tokens |
| --- | ---: | ---: | ---: | ---: |
| Current baseline | 722 | 5,202 | 36,102 | 8,990 |
| Historical baseline | 526 | 3,342 | 23,983 | 5,914 |
| Candidate entry | 292 | 2,713 | 19,723 | 4,924 |
| Candidate entry plus all declared resources | 923 | 9,162 | 67,895 | 16,938 |

Token estimates use characters divided by four, not a model tokenizer. The entrypoint is smaller, but the full effective contract is larger. Route-specific assembly changes what needs delivery for a selected operation; these counts do not establish latency, cost, clarity, or quality improvements.

## Behavioral Claims Requiring Proof

- Runtime use of real independent reviewers with cold initial context and complete relevant resources.
- Material improvement over a strong native baseline on the actual model and task.
- Correct ULT persistence, print-before-execute ordering, authorization boundaries, and combined full/ULT nonexecution.
- Actual grading candidates, stable criteria, truthful stop reasons, regression rejection, and best retention.
- Accuracy and utility of basis, simple, inversion, adversarial, contract, and catchup outputs.
- Any gaslight technique benefit, using original and strong-neutral comparators and correctness/honesty/adherence/cost measures.

No model experiments, subdelegation, installation, generated-surface runtime validation, hosted CI, merge, or release were performed by this reviewer. Model-provider source claims remain outside this admission attestation.

## Unresolved Ambiguities

No unresolved source-contract ambiguity blocks admission. The existing unsafe/destructive confirmation boundary remains intact. The candidate explicitly distinguishes actual tool evidence, instruction-only compliance, and host-enforced delivery; this review does not promote one evidence class into another.

Initial assessment was made from the baselines, candidate, and complete tool-read resources without author grades or preferred verdicts. A filename-discovery search later incidentally displayed three author change-map summary rows; those were not used as evidence. The acceptance register supplied S01–S19 labels after the independent comparison. The four concrete preservation findings originated from direct historical comparison and were resolved through author follow-up.

## Frozen Binding

- Current original: `c2d39e85db9267a1ca0acd29394cf1e88255bc5e1f0d797ba42ac091a066aec2`
- Historical original: `488bc14a2fa4e3ce625adad07c98b2aa7a6af38d6ddbee64e182b2db82d9897a`
- Candidate entry: `4cf3de8aafce2a6ccfc7668e7c3aeb1dee1ed6f2394ecaddb48d6b957f0bec82`
- Effective candidate: `3cca08e07f6caf656915f8641810bf8d00ad05decc0e2dd359d0b877a57d3524`

Any subsequent entry, manifest, or resource change requires rebinding and review of the affected semantics. The review generator is a reviewer-authored mapping artifact, not an automatic authorization source.
