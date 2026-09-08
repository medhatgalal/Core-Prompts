# Rubric

Independent instruction-quality judgment of neutral artifacts, read in order: meadow, cedar. The five frozen criteria have equal weight; target is mean >= 9, every dimension >= 8, and zero protected-behavior violations.

| Criterion | Meadow | Cedar | Evidence |
| --- | ---: | ---: | --- |
| Factual fidelity | 10 | 10 | Both preserve disabled reporting, availability-only probes at 100%, and absent latency/error-rate evidence. Both distinguish supplied observations from unknowns and conclude that overall health is unestablished. |
| Observation-channel reasoning | 10 | 10 | Both explicitly say missing complaints through disabled reporting prove neither health nor failure. |
| Measurement scope and uncertainty | 10 | 10 | Both limit the probes to availability, keep latency/error rate unknown, and prohibit invented windows, coverage, thresholds, and unsupported overall-health conclusions. Cedar also expressly prohibits new observations. |
| Usefulness and execution clarity | 10 | 10 | Both require observations, unknowns, a bounded assessment, and proposed evidence-gathering follow-up; both prohibit running checks or modifying systems. Cedar names four output labels; meadow supplies the same substantive sequence in prose. |
| Proportionality and readability | 9 | 9 | Meadow is a clear but dense paragraph. Cedar offers scan-friendly labels but repeats the overall-health uncertainty in Unknown and Assessment and mixes a generation instruction into its Assessment template. Neither issue creates a material correctness gap. |
| Arithmetic mean | **9.8** | **9.8** | (10 + 10 + 10 + 10 + 9) / 5. |

Protected behavior: **zero violations identified in either candidate**. Both report service status, preserve the supplied facts and their limits, and prevent unavailable observations from being interpreted as service health or failure. Cedar's suggestion to restore reporting remains expressly a proposal; the final prohibition on system modifications preserves the execution boundary.

Target outcome: **both meet the frozen quality target as instruction-quality judgments**. These grades do not establish downstream behavior or promotion readiness.

# Iteration Ladder

| Artifact | Role in this comparison | Grade | Decision | Evidence |
| --- | --- | ---: | --- | --- |
| meadow | Prior incumbent supplied for comparison | 9.8 | Retain | Complete evidence limits, explicit silence reasoning, useful follow-up, and a clear non-execution boundary. |
| cedar | Candidate assessed against meadow | 9.8 | **Tied; do not replace meadow** | Four labels improve scanning, but they preserve the same substantive guidance. Repetition and the mixed report/instruction wording offset that presentation benefit. No material advantage without added ambiguity is established. |

Stopping reason: this bounded independent pair review is complete. No author grades, previous review results, round identifiers, or preferred verdict were supplied or consulted. This reviewer makes no claim about a global plateau or trial count.

# Final Artifact

Retain the supplied meadow instruction under the frozen tie rule:

Write a concise service-status report using only these supplied facts: the reporting channel was disabled; uptime probes report 100% availability but measure availability only; no latency or error-rate evidence was supplied. Separate confirmed observations from unknowns. Explain that no complaints through a disabled reporting channel provides no evidence of either health or failure. Limit the uptime result to what those probes observed; do not invent a time window, coverage, thresholds, or a current end-to-end health verdict. State that overall service health is not established by the available evidence. End with proposed follow-up checks for latency, error rates, and the reporting channel, clearly labeled as suggestions that have not been run. Do not run checks, modify systems, or fabricate results.

# Top 3 Remaining Gaps

No material instruction-level gaps remain under the supplied task and rubric. Two minor readability refinements are available:

1. Meadow's dense paragraph could be split into a small number of output-oriented clauses without adding requirements.
2. Cedar could keep the no-invention directive outside its Assessment output template and avoid stating overall-health uncertainty twice.

No third gap is invented. Actual downstream adherence remains unmeasured; judgment alone is not behavioral or promotion evidence.
