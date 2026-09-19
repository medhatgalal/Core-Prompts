# Insight visibility — round 2 frame

Source: `engos-example-insight-visibility/input.md` plus I1/I2 in `round-two-clarifications.md`. Original vague statement remains verbatim in intake.

**Problem/people:** Product managers currently request monthly aggregate adoption counts from support (`input.md:8`).

**Why now:** The hypothetical requester now chooses daily adoption visibility without support requests. No quantified savings or external deadline is supplied (`round-two-clarifications.md:20-25`).

**Desired outcome and success:** Permitted product managers see the existing viewed/generated daily counts in the existing internal reporting tool. Visibility is the outcome; ranking or content quality is not inferred from counts (`input.md:14`, `round-two-clarifications.md:20-25`).

**Appetite:** One week with one engineer, a supplied hypothetical willingness to spend, not an estimate (`round-two-clarifications.md:22`).

**Kill criterion:** Stop if achieving the outcome requires customer text, new metric computation or a new analytics service (`round-two-clarifications.md:23-24`).

**Boundaries:** Existing daily counts from activation forward. History is Later. No ranking/content improvements, new metrics, document text or prompts leaving the product boundary. Existing role restrictions remain (`input.md:9-14`, `round-two-clarifications.md:20-34`).

Round-one Q1–Q4 were intent/appetite/success/kill decisions. I1 now answers them; they are not relabeled as previously answered (`input.md:16-19`, `round-two-clarifications.md:20-25`). New research questions:

| ID | Question | Evidence needed |
| --- | --- | --- |
| RQ1 | Which existing data may cross the boundary? | Approved fields and prohibited content |
| RQ2 | What receiving contract handles duplicate account/day data? | Existing schema and replacement semantics |
| RQ3 | Who may read source metrics and see the result? | Source and destination access responsibilities |
| RQ4 | What volume and history limits bound the outcome? | Quota, retention and activation scope |

No selected publisher, schedule implementation, endpoint, topology or new service is prescribed in this frame.
