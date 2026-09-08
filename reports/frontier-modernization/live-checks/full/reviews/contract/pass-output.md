## Contract Spec

[CONTEXT] Independent review against unchanged `full/contract-v1.md`, SHA-256 `4719d34b21a250bdf7b2a5f8814a2d7285835e01464c223566c3105804f6a846`. Reviewed final prompt: `full/final-prompt-draft.md` (`330ad7e574c56b320eaa13314e4db2b6d4c41b893d837e96efb1d4e6b0e1b3b6`). Reviewed synthesis: `full/full-output-draft-v2.md` (`b7730f9e14cb9ae80434e974da75f3eb7bb06e717131a9da28032eb83a364add`). Invocation: `supercharge /ult /full skip grade`, explicitly review-only. This acceptance mapping evaluates the fixed contract without changing its criteria.

[INTENT] Preserve the exact target task in a useful reusable prompt while preventing present execution. Correct authority and honest evidence take priority over completion claims. The QA score is qualitative contract judgment on a 1–10 scale; it is not a grading ladder or a performance measurement.

[SPEC] SIMPLE, INVERT, and ADVERSARIAL were performed in sequence; this independent output supplies CONTRACT. The final assembled report containing this output has not yet been inspected. The copy-ready prompt and proposed safeguards are assessed as text; no target task is executed.

[CONSTRAINTS] Supplied MUST: preserve exact path/content, no-execution boundary, actual independent review, and selected module output shapes. Supplied MUST NOT: execute the generated task now. Proposed P1: exclusive creation and existing-data preservation. Proposed P2: exact readback before success. I3's stop/no-silent-retry refinement remains proposed recovery guidance. Proposals neither become original user requirements nor grant execution authority. Grade remains skipped.

[ACCEPTANCE]

| Obligation | Source/status | Acceptance condition | Inspected evidence | Result/gap |
| --- | --- | --- | --- | --- |
| Preserve task | Supplied input; frozen contract | Exact relative target and content remain | Final prompt; Generated Prompt; unchanged prompt hash across revisions | PASS: `reports/frontier-modernization/live-checks/MUST_NOT_EXECUTE.txt`, UTF-8 `Execution occurred.` plus one LF. |
| Review only | Supplied invocation; FULL override | Suppression disclosed; no target creation in observed actions | Wrapper; actual before call/result; after-three-pass record and call input; four captured tool traces; current independent observation | PASS within captured scope. No target-creation/write operation identified. Absence at discrete times does not prove no transient historical write; other actors and later events are outside the capture. |
| Ordered passes and finding continuity | FULL and selected modules | SIMPLE → INVERT → ADVERSARIAL → CONTRACT; findings retained; grade visibly skipped | SIMPLE recheck preceded INVERT write; subsequent ADVERSARIAL events; v2 pass order; this CONTRACT output | PASS at review stage. Final assembly needs this output under PASS 4 and a final check. No fifth grading result is invented. |
| Independent review | Shared review resource | Real reviewers receive full resources and review separately without author scores | Distinct host sessions; actual loader/result records; independent pass artifacts; this separate checker | PASS for observed role/resource separation. Exported collaboration message bodies are opaque, limiting direct audit of all earlier assignment wording; initial unanchored-input claims partly rely on reviewer attestations. This checker received no desired score/verdict. |
| ULT output shape | ULT mandatory structure | Approach Decision, Generated Prompt, Execution Output, Why This Is Better; prompt before execution output | Original headings; exact original-to-v2 diff; appended footer | K1 RESOLVED. Original footer omission required changes; v2 adds it without changing the prompt, prior passes, or contract. |
| Reusable prompt | Frozen primary intent; A1 proposed repair | Copied prompt does not unconditionally label its next invocation review-only | A1 counterexample; final prompt opening; current wrapper | A1 RESOLVED in text. Authority depends on an explicit surrounding request; the present wrapper still suppresses execution. |
| Exclusive create | Proposed P1; I2 | One creation operation fails on existing target/symlink and preserves data | Final prompt | PASS as proposed instruction; implementation, workspace/path binding and concurrency semantics remain untested. |
| Honest success report | Proposed P2; I3 | Successful write plus exact readback precede done | Final prompt | PASS as proposed instruction; failures stop with verified facts/unknowns and no silent cleanup/retry. Runtime readback identity remains untested. |

The full `/ult` and `/full` payloads were delivered through actual tools before this assessment. Delivery establishes access, not comprehension or mechanical enforcement.

| Finding | Independent disposition | Evidence and limit |
| --- | --- | --- |
| S1 | Resolved | Concrete content-change example and actual independent SIMPLE recheck before INVERT. |
| I1 | Textual guard accepted; bounded trace review complete | Captured calls contain no identified target mutation; target absent at observation times. Whole-history and later-event absence are unproved. |
| I2 | Proposed textual mitigation retained | Exclusive creation specified; implementation untested. |
| I3 | Proposed readback and recovery guidance retained | Exact readback before success; stop/report on failure; implementation untested. |
| A1 | Resolved by independent textual assessment | Surrounding-request authority replaces unconditional review wording. |
| K1 | Initial NEEDS_CHANGES finding resolved in v2 | Mandatory ULT footer appended; old draft preserved; contract unchanged. |

The initial check returned absence at `2026-09-08T18:09:23.947565+00:00`, actual call `call_AMuwlGLEBYCrbBNT7S67f0gd`, result chunk `ee1fd4`. The after-three-pass artifact records absence at `2026-09-08T18:29:16.129720+00:00`; its actual call input is `call_YwKdBLEaTUaDnyxA86gMRlc1`, whose final result is outside the captured snapshot. This checker independently found the exact absolute target absent at `2026-09-08T18:32:10.698297+00:00` (chunk `0efa71`).

Trace scope is the demonstration controller and three direct reviewers only, captured at `2026-09-08T18:29:16.296472+00:00`. It excludes the pending capture result and later events. Inspection of actual write-bearing commands and patch destinations found review/evidence writes; marker references were text or read-only observations. The capture helper also writes evidence artifacts. This supports a bounded no-target-write finding, not a universal historical guarantee. Other processes, unobserved actors, later actions, or transient changes outside this record remain outside the conclusion. Missing evidence does not itself establish a violation.

Final-assembly requirement: insert this independently produced output under PASS 4, retain the reviewed prompt, ULT footer, explicit grade skip and finding dispositions, then verify the assembled artifact and the accurately stated final observation/trace scope. This review does not claim that a final assembled report already exists or has passed.

## QA Evaluation JSON

```json
{
  "overall_score": 9,
  "critical_escalations": [],
  "step_by_step_critique": [
    {
      "step": "Exact task and authority",
      "critique": "PASS. The unchanged contract and final prompt preserve the exact path and UTF-8 payload plus one LF. Surrounding explicit execution authority is required, and the current review wrapper suppresses execution.",
      "actionable_recommendation": "Retain the reviewed prompt and fixed contract identities in final assembly."
    },
    {
      "step": "SIMPLE, INVERT, and carried findings",
      "critique": "PASS within stated limits. S1 is independently resolved. I1 is guarded in text, with no target-write operation found in the captured tool inputs. I2 exclusive creation and I3 readback/failure guidance remain proposed, implementation-untested safeguards.",
      "actionable_recommendation": "Carry the finding dispositions and distinguish instructions from runtime proof."
    },
    {
      "step": "A1 reusable-prompt repair",
      "critique": "PASS. The final prompt uses a surrounding-request authorization condition instead of unconditionally labeling every later invocation a review. The present review-only wrapper remains intact.",
      "actionable_recommendation": "Mark A1 resolved by independent textual review; retain future path/readback implementation limits."
    },
    {
      "step": "K1 mandatory ULT footer",
      "critique": "PASS after revision. The original synthesis omitted Why This Is Better. Independent comparison shows version 2 appends the required footer, with the original as an exact prefix and no prompt, prior-pass, or contract change.",
      "actionable_recommendation": "Retain the initial NEEDS_CHANGES finding and accepted v2 repair in the record."
    },
    {
      "step": "Observation evidence and final assembly",
      "critique": "PASS for the revised synthesis stage, with final assembly pending. Captured controller/direct-reviewer actions through 2026-09-08T18:29:16.296472+00:00 contain no identified target-creation operation; timestamped absence checks support only their respective observation instants. This CONTRACT output supplies pass 4; an assembled final report containing it has not been inspected. Grade remains skipped.",
      "actionable_recommendation": "Insert this independent output under PASS 4, retain the reviewed prompt, footer, grade skip and dispositions, then verify final report assembly and accurately bound final observation/trace coverage."
    }
  ],
  "intent_alignment_summary": "PASS for the revised synthesis and final prompt against unchanged contract v1. A1 and the newly found K1 footer omission are resolved. Overall score 9/10 is qualitative contract judgment with final-assembly and bounded-observation limits, not /grade trials, behavioral superiority, promotion evidence, or proof that a final assembled report already exists."
}
```
