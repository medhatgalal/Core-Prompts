# Supercharge live host acceptance

These are bounded Codex host demonstrations of the emitted Supercharge skill. Slash routes were followed as skill instructions using real tools and independent subagents; no separate model CLI was invoked. This report is local acceptance evidence, not protected behavioral promotion or comparative cross-model efficacy.

| Demonstration | Actual outcome | Evidence |
| --- | --- | --- |
| /grade, explicit two trials | PASS: C0 2.6/10; C1 9.8 improved; C2 9.8 tied. Retained C1 under the frozen tie rule. Exactly two substantive candidate trials after the baseline. | [Four-section result](grade-output.md), [selection](grade/selection.json), [candidates](grade/candidates/), [independent reviews](grade/reviews/) |
| /ult /full skip grade | PASS: four performed passes, independently checked final assembly, explicit no-execution notice, grading skipped. Target observed absent. | [Full result](full-output.md), [assembly review](ult-standalone/review/assembly-review.md), [QA JSON](full/qa-evaluation.json) |
| Standalone /ult with execution authorization | PASS: displayed the reviewed prompt, created only its authorized target using exclusive creation, and read back the exact two bytes 42 with no newline. | [Positive result](ult-positive-output.md), [actual tool result](evidence/positive-execution-tool-result.json), [display/call timing](evidence/positive-output-order.json) |
| Standalone /ult draft-only | PASS: generated/reviewed the prompt, explicitly suppressed execution, and observed its target absent. The full-stack target also remained absent. | [Draft result](ult-draft-output.md), [actual observation](evidence/suppression-tool-result.json) |
| /catchup, this demonstration only | PASS: exact tables/visible checks and facts independently verified; two evidence-wording corrections accepted; mechanical checks pass. | [Catchup](catchup-output.md), [independent recheck](catchup-review/recheck.md), [report verification](evidence/report-verification.json) |

The scores above are independent instruction-quality judgments. The positive file write is an actual local task execution. Neither is a measured comparison of downstream service-reporting performance. C2 tied rather than regressed: earlier-best retention was exercised on a tie; regression rejection and default-limit plateau behavior were not exercised.

## Actual host and review identities

Host session metadata records configured gpt-6-astra with ultra reasoning, Codex CLI 0.153.4 and multi-agent v2. All reviewers used the inherited configured model, so distinct contexts do not establish independence from shared model biases. An exact backend model revision is not exposed.

| Task | Actual host thread ID | Work performed |
| --- | --- | --- |
| verify_live_skill_behaviors | 01a08233-5e2d-7c20-b46b-68e3aee1c9fc | Controller, candidate authorship, synthesis, positive execution, report capture |
| grade_harbor | 01a08234-e21f-70f1-bda9-1d252bf32804 | Independent C0 grade, SIMPLE review/recheck, INVERT contribution |
| grade_meadow | 01a08237-0f36-7073-a347-0b38cfe03fe2 | Fresh C1 comparison, independent ADVERSARIAL, final catchup check |
| grade_cedar | 01a0823c-a467-7173-938b-6c5cbead3781 | Fresh C2 comparison, independent CONTRACT |
| ult_acceptance | 01a08253-cae3-76a2-aa5e-8954db6dc3ff | Fresh final-assembly verification and standalone prompt review |

See [actual session metadata](evidence/host-session-identities.json), [actual reviewer final messages](evidence/reviewer-final-results.json), and each review's evidence.json. Graders received neutral artifact names and the same frozen rubric without author scores or round numbers. Initial judgments were formed in fresh contexts; related later review roles used separate task briefs. Some exported collaboration message bodies are opaque, so the trace is not a complete forensic proof of every earlier assignment's wording.

## Resource binding and tool results

The assigned workspace and repository matched /Users/medhat.galal/.codex/worktrees/921d/Core-Prompts, branch AI/frontier-capability-modernization, initial HEAD c9d6de07b4d1918970a5f70350cf50200a6a0ff4. Shared parent implementation changes were preserved. Python was 3.14.7 and Supercharge v5.0. Recorded demonstration artifacts were authored under live-checks.

| Binding | SHA-256 |
| --- | --- |
| ssot/engos-meta-supercharge.md | 4cf3de8aafce2a6ccfc7668e7c3aeb1dee1ed6f2394ecaddb48d6b957f0bec82 |
| .codex/skills/engos-meta-supercharge/SKILL.md | 3ecc726652ceae81c5e50bc48b4833bd9f22428c651786b91357a29622e09892 |
| .codex/skills/engos-meta-supercharge/resources/resource-map.json | 56fee7ec78e0bac117fb3f517e8577890cfa638c3ac3a758f236ec64ee3df91f |
| .codex/skills/engos-meta-supercharge/resources/scripts/load_module.py | 48e30c5a38201f3c0f428daec99c7c60560420a50f6e1a170a03dc2e30d68150 |

| Delivered route | Bundle SHA-256 |
| --- | --- |
| /grade | cc455648f3db75347d131cfae2ca86a434458112a522a7dbcaeda5a6ae43b21f |
| /ult | 791152fa6f311a3d9a82a0f1a7fb46166b82eaba069ddaaa83151b25cd28d16f |
| /full | d259d4328534c1a630e8dbcb166c96f498254b05858bb6690490ae7904417fcd |
| /catchup | e5129c59f933efd6e189446437fd62b96b031a5858589b9330cfc9077b4a001d |

Complete selected payloads were supplied through actual emitted-loader results before dependent work. The source/map/grade delivery was recovered in chunk fa5884; complete initial ULT/FULL/CATCHUP delivery is d9f4b3. After helper regeneration, the descriptor and helper changed while every selected instruction payload remained byte-identical. Full reload recovery is 420473; standalone ULT reload is 4650b1. Full payload files and [start/final binding comparison](evidence/rebuild-recheck.json) are retained. A hash alone is not treated as delivery or comprehension proof.

Key actual outcomes: positive creation/readback chunk be7f55, execution call call_P2PB4YsyjfnLQAZBD4q2TgpG; suppression observation chunk cd09b5; final report verification chunk 20b942. Actual controller prompt-display message msg_00a4a0f2bbfc8d95016aa057fdb50887d196609aa8d7b14db5 at 18:46:26.432 UTC preceded execution at 18:46:35.524 UTC.

[Captured traces](evidence/trace-extraction.json) preserve actual host tool calls/results, visible controller messages and reviewer final answers, with original call IDs and explicit cutoffs. Private reasoning, unrelated agent inventory and the initial irrelevant read-only memory result are excluded; the omitted result is identified and hash-bound, with its original retained in native host history. Cedar's capture ends after its second final answer, before it was released to unrelated parent work. The scope is this demonstration, not the wider parent program.

## Findings, recoveries and limits

- S1: the first SIMPLE draft lacked a concrete worked change example. A separate revision was independently accepted; the initial draft and finding remain inspectable.
- A1: the INVERT prompt's permanent review wording made later authorized reuse ambiguous. The controller moved current review status into the wrapper; an independent CONTRACT check accepted the surrounding-request authority condition.
- K1: the first assembled ULT/full draft omitted Why This Is Better. A separate v2 restored it without changing the prompt or frozen contract. Independent CONTRACT and final-assembly checks accepted the repair.
- Catchup initially needed a documented timestamp and a bounded write-scope claim. The accepted revision uses the independent 18:44 observation and says recorded demonstration writes; the original draft and independent findings are preserved.
- Tool display truncation was recovered with complete standalone reads. Agent-capacity failures were recovered through successful independent delegation; no self-review or simulated reviewer replaced a required role.
- I2/I3 remain proposed safeguards with untested concurrency, path/readback identity and partial-failure branches. The standalone happy-path write does not test those branches.

No target-creation operation was identified for either suppressed target in the reviewed captured actions. Discrete absence observations and a bounded trace do not prove the absence of all historical, transient, later or unrelated actor writes. The evidence supports the observed local demonstrations only. No installation, release, protected evaluator promotion, broader model comparison, or real-service operation is claimed.
