# engos-design-shaping validation plan

This is a design exercise, not statistical comparison or behavioral promotion.
The baseline is the inspected upstream shaper plus Core-Prompts' current pitch
and artifact skills. Baseline deficiencies are source findings, not measured
baseline runtime scores. Do not claim comparative superiority from this run.

## Boundaries and budget

- One real input: historical rough Continuous Update request with recorded human
  clarifications, not an already-shaped architecture exemplar.
- One end-to-end attempted replay through five gates.
- At most two candidate review/repair rounds initially, plus one gate failure
  matrix and one repair/retest round if a critical mutant survives.
- No production code or new runtime verifier implementation. Stage contracts and
  gate observations are the deliverable. Render/format tooling operates on artifacts.
- All actual model reviews identify their worker/task, input hashes and results.
  Same-author audit is not counted as independent review.
- Ask for missing human budget/intent decisions; retain dependent stage while
  waiting. Elapsed time is not approval. Do independent design checks meanwhile.
- Record elapsed observations per phase. No total shaping time improvement is
  claimed. Stop expanding trial count if bounds are reached; report incomplete.

## Gate probes

Inspect real G0 input. Separately give a fresh reviewer the candidate gate rules
and small, explicitly synthetic probe artifacts. Include matched framing control
and failures for invented risk, hidden solution in framing, unexecuted spike,
missing required artifact, and dropped target table rows. Expected results are
fixed before the reviewer returns. The reviewer must cite the actual violating
content rather than echoing the fixture label. These are behavioral smoke checks
of a model applying the protocol, not proof of platform enforcement or reliability.

Success criterion for the failure matrix: all injected failures rejected at the
correct stage, framing control accepted, G0 genuine intake correctly assessed.
Any wrong advance is critical and requires a candidate correction and re-run of
that case plus its matched control. Preserve initial result and actual correction.

## Full exercise checks

G0: known/assumed/missing and no selected solution.
G1: complete solution-free frame with actual appetite decision.
G2: every question answered/excluded with provenance; named spike stays pending.
G3: full exemplar coverage, inspected pixels, both scorecards, independent review,
and at least one documented real iteration on a weak dimension.
G4: same complete bundle on HTML and native Google Docs with saved content,
table rows and diagrams checked. No public-sharing workaround.

Any gate failure means the run did not reach Bet-ready. A named human step is a
useful incomplete result, not fulfillment of the two-successful-surfaces criterion.
