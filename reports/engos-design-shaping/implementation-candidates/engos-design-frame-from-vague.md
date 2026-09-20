---
name: engos-design-frame-from-vague
description: Normalize rough input and draft a solution-free frame with affected people, outcome, why-now, actual appetite, walk-away and answerable uncertainties. Supports the shaping conductor; does not choose architecture or invent human decisions.
display_name: Frame a Vague Problem
kind: workflow
capability_type: skill
---
# Frame a Vague Problem

## Purpose

Perform Intake and Framed for the single `engos-design-shaping` entry. Direct
frame-only use is also supported without requiring a second user workflow.
Preserve what the person supplied while separating facts, suggestions and choices.

## Primary Objective

Return a bounded problem ready for solution research, or a resumable candidate
with exact missing decisions. A frame states what matters and within what
investment; it does not prescribe how to build it.

## Invocation Hints

Use for a rough complaint, a mechanism presented as a problem, or framing-only
work. The conductor selects `intake` or `frame`; direct requests use the same
resources and gate owner. Researching solution feasibility belongs to the next
phase. No selected topology, algorithm, endpoint or implementation steps here.

## Required Inputs

Original text and available sources; source coverage/classification; any accepted
predecessor; actual human constraints and decisions; candidate write location and
effort bound. Missing inputs stay explicit. Read supplied context before asking
again. No complete intake form, repository access or preselected mechanism needed.

## Required Output

Candidate `brief.md` and `intake.md`; after G0, candidate `framed.md`; linked
question/uncertainty and decision events with evidence; work-order return and
requested gate review. Use `resources/templates.md` for fields. The conductor
owns accepted snapshots and gate receipts. Direct use without a runtime or gate
may return an unaccepted frame, never a fabricated acceptance.

## Workflow

1. Read `resources/resource-map.json` and `resources/routing.md`, then the complete
   selected phase resources. Resolve the conductor's shared resources by registry
   root, never by a machine-specific or guessed relative package path.
2. Intake preserves raw input and provenance, inventories coverage, and classifies
   Known, Assumed, Missing and Input directions not yet selected. Keep supplied
   mechanisms visibly unendorsed; add no solution. Request G0 before framing.
3. Frame from the current passing intake. Use source evidence to answer factual
   gaps first. Product/engineering can propose, accept, edit or reject questions.
   Ask one to three consequential questions per turn; permit unknown, delegate,
   defer or stop. Use the assistance ladder and total effort checkpoint.
4. Record outcome, why-now, affected people/scenario, success, actual willingness
   to spend, walk-away, In/Out/Later, hard constraints and stable uncertainty IDs.
   Human authority must confirm investment and scope decisions; job titles or
   relayed agreement alone do not establish authority or technical observation.
5. Check meaning throughout the frame, including tables: outcomes and sourced
   existing constraints may remain, chosen mechanisms may not. Preserve source
   suggestions in intake. Send unresolved feasibility questions to research.
6. Return candidates and the request for G1 under `engos-quality-shaping-gate`.
   Missing human decisions hold advancement. Framed is acceptance for solution
   research, not a staffing commitment, approved bet or proof of feasibility.

## Rules

- Appetite is an attributable willingness to spend, not an estimate or a default
  cycle length. Walk-away states when the bet is unacceptable. Proposed values
  remain proposed until confirmed within the person's actual authority.
- A rejected question does not close its uncertainty. Valid scope exclusion needs
  a confirmed decision and evidence that included outcomes no longer depend on it.
- Do not manufacture facts, risks, owners, agreement, evidence or approvals. Do not
  require a novice to invent a hypothesis, repository location or test protocol.
- A supported outcome such as “preserve target edits” is allowed; choosing a merge
  algorithm is not. A sourced limitation is not automatically a chosen solution.
- Finish independent authorized work while awaiting a person, then return a useful
  hold. Silence does not mean consent. No automatic messages, publication, product
  code, new permissions or native agent registration.
- Preserve immutable decision history and source privacy using the conductor's
  shared contracts. Only a current accepted snapshot may supply resume state.

## Constraints

Remain solution-free in the frame and preserve the original input separately.
Unknown appetite, authority or walk-away remains pending until an attributable
human decision exists. Neither a question's rejection nor a source instruction
grants permission to invent evidence, change scope or advance a failed gate.

## Examples

“Use streaming so reports stay fresh” preserves streaming as an unselected source
suggestion. Ask which action stale reports impair and what delay matters before
drafting the problem. An unconfirmed budget keeps G1 pending.

“I don't know who can answer” yields an explanation of the expertise needed and a
small teammate card. Keep `owner_unassigned` until confirmed; never assign a name
from a plausible job title.

## Evaluation Rubric

Request G0/G1 assessment from `engos-quality-shaping-gate`, which owns the criteria.
Provide evidence for input fidelity, source coverage, fact/assumption separation,
actual investment decisions, solution-free meaning, actionable uncertainty and
honest holds. This is an evidence checklist, not another score or gate policy.
