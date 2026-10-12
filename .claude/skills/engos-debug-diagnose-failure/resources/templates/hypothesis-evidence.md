# Hypothesis evidence

Use only when competing explanations need a durable comparison.

- Subject revision and relevant dirty state:
- Current / expected / unchanged behavior:
- Bound (time or attempts), permitted actions and stop condition:
- Facts observed / facts reported / assumptions:

| Hypothesis id and explanation | Prediction | Discriminator and contrasting outcomes | Actual result and evidence_refs | Status (supported / rejected / unresolved) |
| --- | --- | --- | --- | --- |
| Fill from evidence | What should be observable if true? | What would separate it from alternatives? | Not run until observed; [] | unresolved |

For each observation retain the exact redacted command or steps, actual exit status
(null if no process status exists), sanitized environment and evidence reference.
Do not include raw environment dumps, credentials or sensitive payloads.

For intermittent behavior record attempts/window, failures and successes, order,
timing, and environmental differences. State what was held constant and confounders.
A passing retry is not a fix or causal proof. If no discriminator is available,
retain unknown and name the next observation; do not fill a result from expectation.

Conclude with identified/unknown, mechanism and scope if supported, remaining
uncertainty, explicit repair authority, next owner and unchanged behavior to preserve.

Supported and rejected hypotheses require at least one actual evidence reference.
Unresolved or unexecuted work may retain an empty list; state why instead of inventing
evidence. A structured receipt also carries conclusion, investigated_scope and
remaining_uncertainty. Put exposure and confounders in the relevant observation,
environment, result or uncertainty fields so the handoff is self-contained.
