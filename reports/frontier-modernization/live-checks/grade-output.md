## Rubric

Five equally weighted criteria scored 1–10: factual fidelity; observation-channel reasoning; measurement scope and uncertainty; usefulness and execution clarity; proportionality and readability. The frozen [anchors and task facts](grade/rubric.txt) set the target at a mean of at least 9, every criterion at least 8, and no protected-behavior violation. Preserve all supplied facts, their limits, and uncertainty; invent no service observation.

The original C0 is preserved separately. Its independent baseline score is **2.6/10** with two protected-behavior violations: omitted facts/limits and reassurance inferred from unavailable reporting. On ties, retain the prior best unless review establishes a material advantage without added risk. The explicit budget is exactly two candidate trials after C0.

## Iteration Ladder

| Candidate | Substantive change | Independent grade | Decision | Evidence |
| --- | --- | ---: | --- | --- |
| C1 (meadow) | Replaces reassurance with supplied observations, explicit unknowns, two-way silence reasoning, bounded uptime scope, and unrun follow-up proposals. | 9.8/10 | Improved; keep C1 | Fresh pair reviewer found preserved facts, no protected violations, and target met; [review](grade/reviews/meadow/review.md). |
| C2 (cedar) | Tests a fixed four-line reporting strategy to make observations, unknowns, assessment, and next check easier to scan. | 9.8/10 | Tied; retain C1 | Fresh pair reviewer found no net advantage: scanning improves, but repeated uncertainty and mixed report/instruction wording offset it; [review](grade/reviews/cedar/review.md). |

Stopped because the explicitly requested two candidate trials are complete. C1 remains best under the frozen tie rule. This run found one improvement and one tie; it did not encounter a regression or establish a plateau. Grades are independent review judgments, not measured downstream performance.

## Final Artifact

Write a concise service-status report using only these supplied facts: the reporting channel was disabled; uptime probes report 100% availability but measure availability only; no latency or error-rate evidence was supplied. Separate confirmed observations from unknowns. Explain that no complaints through a disabled reporting channel provides no evidence of either health or failure. Limit the uptime result to what those probes observed; do not invent a time window, coverage, thresholds, or a current end-to-end health verdict. State that overall service health is not established by the available evidence. End with proposed follow-up checks for latency, error rates, and the reporting channel, clearly labeled as suggestions that have not been run. Do not run checks, modify systems, or fabricate results.

## Top 3 Remaining Gaps

No material instruction-level gaps remain against the frozen rubric. Reviewers identified two minor opportunities in retained C1: make its dense paragraph easier to scan, and name the missing question each proposed check would resolve. Neither was tested as an additional candidate because the two-trial budget is exhausted. No third gap is invented. Actual downstream adherence remains unmeasured.
