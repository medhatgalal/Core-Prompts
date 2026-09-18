# engos-design-shaping design packet

This packet preserves design and implementation evidence for Intake → Framed →
Research → Shaped → Bet-ready. The user authorized implementation and the pilot;
canonical sources and generated skill packages are changed in the isolated
worktree. This is not shipped to main. Native registrations, home installations
and production services remain unchanged.

The current status is [the implementation ledger](engos-delivery-implementation-ledger.md),
including local verification and the still-open human, publication and GitLab gates.

## Read in order

Start with [the revised operating proposal](engos-design-shaping-operating-plan.md)
for the document-first product/engineering workshop, isolated roles, assistance,
handoffs, formats, validators and proposed pilot. Independent review recommends
proceeding to pilot design, not team rollout. It supersedes earlier execution recommendations
where explicitly revised, but does not silently rewrite or install the candidate
skills below. Those require a later reviewed adoption pass.

The [final plan QA](engos-quality-shaping-operating-plan-final-qa.json) binds v3
hash 1bfb7f01766dbaf8b7c134d3515bd2cf6ebe7162c43cee666e58dd59942b5766.
The proposal is frozen at its review-submission state; this separate receipt is
the latest verdict. It resolves design clarifications, not missing operational proof.

1. research-notes.md — authoring authority, actual upstream chain, source revisions.
2. gap-analysis.md — failures mapped to missing stages, gates and Shape Up principles.
3. candidate-map.json — exact proposed skill/resource dependency map.
4. candidates/engos-design-shaping/SKILL.md — conductor and phase progression.
5. candidates/engos-design-shaping/AGENT-DESIGN.md — agent role and host boundary.
6. validation-plan.md and iteration-log.md — preregistered checks and actual repairs.
7. validation-report.md — observed results and outstanding acceptance criteria.
8. [Worked-example library](examples/README.md) — four complexity/vagueness cases,
   two actual author/reviewer rounds, rendered diagrams and honest stop states.
9. reference-findings.md — sanitized lessons from real Framed/Shaped and Discovery
   documents; private source extracts are intentionally outside this public repo.
10. engos-quality-shaping-operating-plan-review.md — original independent UX and
    engineering critiques of the operating proposal, retained without rewriting.

## How the design is exercised

The host receives the candidate map, loads the conducting skill and the selected
phase's complete dependencies, and operates on one task folder. Each phase writes
its artifact; a reviewer applies the named gate to actual content. The conductor
does not dispatch the next phase after a failing or pending verdict. G3 includes
an independent reviewer; the author cannot certify that independence itself.

Draft identities: one conductor, one framing skill, one shared quality gate, and
same-name revisions of the two existing delivery helpers. The existing pitch
reviewer is loaded with an explicit design overlay. The agent role uses this
same process; native provider configuration is neither necessary nor emitted
for this experiment. Future native admission remains a separate repo gate.

These are instruction-level rails with observed model gate probes. This design
does not claim executable platform enforcement or automatic installation.
Canonical adoption would require the repository's normal UAC apply, generation,
review and authorized delivery workflow after the remaining exercise succeeds.

## Current real-input exercise

A real historical rough brief and its clarifications were used. G0 passed;
G1 stopped on investment-decision provenance. Full private artifacts and raw
receipts are retained in task-local storage, not this public repository. No
later-stage success, native Google Doc placement or end-to-end bet-ready result
is claimed. The final validation report identifies what must happen next.

## Example asks

“Shape this rough brief using the supplied candidate map. Start at Intake,
record each gate result and stop advancement when a required decision or proof
is missing.”

“Resume this shaping folder. Verify the latest artifact hashes and decisions,
rerun the earliest pending gate, and continue only from that result.”

“Review the shaped source under G3 without requiring the future target placement.
After it passes, place the full pitch and check G4 on the saved target.”
