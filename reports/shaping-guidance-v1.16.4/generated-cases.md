# Generated guidance: independent case answers

Read scope: the eight specified generated `.grok/skills` files only. This is a reading-based case assessment, not a runtime or product execution test. The package-decision cases assume betting is in the requested scope; eligibility alone does not expand a draft-only or artifact-only request.

1. **Right — ask the package question now; do not wait for independent review to finish or for a successful upload.**

   Guidance followed: “When the package is eligible and betting is in scope, ask the package question when independent review returns a pass, a fail, or review_pending. Say the result in plain words. Ask then even if target publication is pending or an upload has failed; G4 remains a separate delivery check.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:128-131`). The main skill also says: “Ask while target publication and G4 are still pending if necessary.” (`.grok/skills/engos-design-shaping/SKILL.md:132`).

   I would say that independent review has not come back and the document upload failed, then ask: “The proposal has its diagrams and data contract. A network API is optional. What should happen next?” The choices are: Bet this package; Add or revise an API boundary first; Authorize a separate walking skeleton — a small trial of the proposed parts together; Revise the proposal; Stop (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:177-184`). The skeleton choice is subject to cases 2–3. I would wait for the person's actual answer before dependent work, not treat missing review or delivery as a reason to withhold this eligible decision. Review acceptance and verified delivery remain pending; asking is not evidence that either passed.

2. **Right — the skeleton choice is on the menu even though no repository has been named.**

   Guidance followed: “Offer the skeleton choice unless the person has said there is no code to try. The person supplies repos and code locations after choosing it. Leave repository discovery to that separately authorized effort.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:186-188`).

   I would offer the choice without requiring a repository first. I would not infer that unnamed code means absent code, discover a repository, or start the trial. If selected, I would record the request and stop this skill. The explicit condition for omission has not occurred.

3. **Right — omit the skeleton choice when the person says there is no code to try.**

   Guidance followed: “Omit that choice when the person has said there is no code to try.” (`.grok/skills/engos-design-shaping/SKILL.md:71`). The menu rule independently says: “Offer the skeleton choice unless the person has said there is no code to try.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:186`).

   I would show the other four package choices. I would not offer to create code merely to make a skeleton possible. The person's explicit statement satisfies the omission condition.

4. **Right — record the authorized person's actual yes for this revision, stop shaping, and leave downstream work unopened.**

   Guidance followed: “Record each human choice against the proposal revision, with the person's actual answer and confirmed authority. Preserve it as a candidate decision event until existing reconciliation and acceptance incorporate it; human confirmation and accepted runtime state are separate facts.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:26-29`). “When an authorized person says bet, record their yes against this proposal revision and stop shaping. Keep Bet-ready unchanged. Design, tickets, build and the later integration run remain unopened.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:74-76`).

   I would record the actual answer, confirmed decision authority and package revision without editing immutable accepted state. I would stop shaping and report any pending review or failed delivery in ordinary words. I would not mark delivery complete, launch design, create tickets, start build, or start the later integration run. A yes is a human decision, not execution authority. If authority were unconfirmed, I would preserve the answer without mislabeling it an authorized bet.

5. **Right — `no API` does not remove the data contract.**

   Guidance followed: “With `no API`, input meaning, output meaning, producer, consumer, state, evidence and owner remain required.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:47-48`). The full template says: “For a no API interaction, the full data contract remains required.” (`.grok/skills/engos-design-shaping/resources/templates/shaped-bundle.md:59`). The artifact author's minimum columns are: “Stable row ID, direction, interface (cited network method/endpoint, in-process interface, or no API), purpose, producer, consumer, input meaning/bounds, output meaning, contract state, evidence, owner/action” (`.grok/skills/engos-delivery-diagram-contract-artifacts/SKILL.md:71`).

   I would put the exact token `no API` in the interface cell and retain the stable row ID, direction, purpose, producer, consumer, input meaning and bounds, output meaning, state, evidence and owner/action. I would also cover relevant errors, timeout/retry/idempotency, consistency, persistence, trust/access boundary, lifecycle/version expectations and explicit non-responsibility; use reasoned not-applicable for irrelevant semantics, never blank cells hiding a material gap (`.grok/skills/engos-design-shaping/resources/templates/shaped-bundle.md:51-66`). Components, sequence, data-flow and security ownership remain required. No network method or endpoint is invented for a local transformation.

6. **Right — an unknown interface may not be labeled `no API`.**

   Guidance followed: “Use `no API` only when no API is part of the proposed interaction; an unknown interface stays an unresolved research question.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:46-47`). The template reinforces: “Use no API only for an interaction without an API. An unknown or uninspected interface remains a research gap.” (`.grok/skills/engos-design-shaping/resources/templates/shaped-bundle.md:60-61`).

   I would record the unknown interface and the evidence needed to resolve it, returning a material missing fact to research. I would not use `no API` as a placeholder or invent a method, endpoint or schema. Unknown and known absence are different facts.

7. **Right — no layer section is required for a team that does not size by layer.**

   Guidance followed: “Teams without layer sizing omit the layer section.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:62-63`). The template says: “Do not invent a layer taxonomy, capacity formula or staffing commitment; omit this section for teams that do not use layer sizing.” (`.grok/skills/engos-design-shaping/resources/templates/shaped-bundle.md:35-36`).

   I would omit the layer section and keep the other package requirements. I would not impose layers, fabricate sizes, or make this omission a blocker. The requirement is explicitly conditional on the team's existing practice.

8. **Right — a blank required layer size prevents offering the bet.**

   Guidance followed: “For every named layer, record its owner and size with provenance, or an explicit decision that it is not involved. A blank size is unknown and keeps the package incomplete for the bet question. Invalid or unmapped values also remain gaps.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:58-60`). The shape instructions add: “An empty size stays unknown and missing. Do not infer zero, require a fixed layer count, prescribe a non-involvement code or calculate capacity.” (`.grok/skills/engos-design-shaping/resources/stages/shape.md:60-61`).

   I would name the missing size as the actual gap. At the package decision pause, I would offer only “Keep working on the proposal” or “Stop” using the incomplete-package question (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:158-168`). I would not offer the bet until the layer has an attributable size and owner, or an explicit non-involvement decision. A blank is not zero or implicit exclusion.

9. **Right — these are the actual four spoken status lines for case 1.**

   Guidance followed: “At each pause or milestone, fill the four status lines from the current record. Use everyday words for the problem, present activity, missing input and next action.” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:88-89`). The four labels are “Working on”, “Where we are”, “What is missing”, and “Next step” (`.grok/skills/engos-design-shaping/resources/ways-of-working.md:113-116`). “When review_pending applies, say ‘Independent review has not come back.’ When an upload fails, say ‘The document upload failed.’” (`.grok/skills/engos-design-shaping/resources/progress.md:62-63`; quotation marks normalized here).

   ```text
   Working on: your proposal and the decision about what happens next.
   Where we are: waiting for your choice. Independent review has not come back. The document upload failed.
   What is missing: your choice; you can make it while the review and document upload are still pending.
   Next step: choose whether to fund the proposal, add or revise an API boundary, authorize a separate small trial, revise the proposal, or stop.
   ```

   These lines report the supplied facts without claiming review passed or delivery succeeded, and without exposing internal status labels. The case supplies no actual problem description, so I do not invent one. The small-trial choice is included under case 2's condition and would be removed under case 3's condition. The lines precede the actual package question and choices; they do not replace the wait for an actual answer.

10. **Right — the protected passages and policy version remain explicit.**

    First protected passage, exactly as written in `.grok/skills/engos-design-shaping/SKILL.md:165-166`:

    > Accepted G3 PASS is the only door to design; a proposal, low-average review,
    > no-selection hold or Research pass does not authorize design or implementation.

    Second protected passage, exactly as written in `.grok/skills/engos-design-shaping/SKILL.md:186-187`:

    > No production code, tickets, staffing, bet approval, release or installation is
    > authorized by shaping. A proposed spike needs its own scoped execution authority.

    Exact policy-version line from `.grok/skills/engos-quality-shaping-gate/resources/references/gates.md:3`:

    > Policy version: shaping-gates.v3, paired with rubric.v4 in the current profile

    Its continuation on line 4 is:

    > `shaping-gates.v3+rubric.v4`. Mechanical validity is not a semantic pass.

    I would preserve those acceptance and execution boundaries when recording an early human bet. Neither a complete package, a pending review, a skeleton choice nor a human yes substitutes for accepted G3 or separately scoped downstream authority. The quoted text proves the current wording observed here, not behavioral enforcement or a comparison against an unread prior version.

Wrong case numbers: none.

Report path: `reports/shaping-guidance-v1.16.4/generated-cases.md`.
