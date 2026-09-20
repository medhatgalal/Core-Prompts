---
name: engos-quality-shaping-gate
description: Judge whether a shaping stage can advance using its actual artifacts, evidence, rubrics and target readback. Fail solution-in-framing, unresolved research, missing visuals/contracts, stale verdicts and incomplete placement. Use inside full shaping or independent pitch review.
display_name: Shape Up Stage Gate
kind: workflow
capability_type: skill
---
# Shape Up Stage Gate

## Purpose

Give an explicit pass/fail decision on advancement through Intake, Framed,
Research, Shaped and Bet-ready. One gate contract is shared by the conductor,
author audit and independent pitch reviewer. File existence or a self-reported
status is never sufficient. Inspect the content and the evidence behind it.

## Primary Objective

Prevent premature completion, invented risks and unsupported readiness by making
every advancement depend on current artifacts and observed checks.

## Required Inputs

Stage number; complete artifact paths/hashes; prior gate receipts; original
brief and decisions; evidence/source access; requested target surfaces; reviewer
identity and whether they authored the work. Required resources are
`resources/gates.md` and `resources/rubrics.md`; read both completely before judging.

## Workflow

1. Verify the input/output revision and that every predecessor passed on current
   content. A missing, stale or contradictory predecessor blocks advancement.
2. Read the stage artifact. Verify each applicable condition in `gates.md` by
   inspecting content, citations, rendered pixels or saved-target readback.
3. Quote each violating clause or identify each missing artifact. Give a concrete
   repair, responsible role and recheck. Evaluate meaning, including hidden
   mechanisms in “problem” prose and unsupported risks in otherwise valid tables.
4. Apply the stage's hard blockers before calculating any rubric averages.
   For G3, report the seven quality and five pitch dimensions from `rubrics.md`.
   A high mean cannot override a single failed gate or required dimension below 3.
5. Return a receipt and the next permitted stage. `fail`, `needs_spike`,
   `decision_pending`, `review_pending`, `placement_pending` and `stale` do not
   advance. An explicit human step is useful, but remains pending.
6. After a repair, verify changed inputs and all affected downstream dependencies.
   Preserve the earlier failed result and record what actually changed. Never
   reconstruct a supposed iteration after producing the final artifact.

## Required Output

A receipt contains stage, verdict, inspected artifacts and hashes, reviewer
identity/role, source revision or observation, condition-by-condition result,
blocking findings, repairs, and next permitted stage. The final review adds
scorecards and an evidence tally. Hashes bind the review; they do not prove its
semantic conclusions. Distinguish an executed test from an expected outcome.

## Rules

- G0 excludes assistant-authored solutioning. G1 excludes selected mechanisms
  everywhere in the frame and requires actual investment decisions.
- G2 requires every question to be answered with verified evidence or explicitly
  removed from the selected scope through a sourced decision. Named spikes
  remain unresolved until observed results discharge them.
- G3 requires all three diagram types, contracts, security responsibilities,
  explicit negative responsibilities, risks/mitigations, scoped work, no-gos and
  independent review. Each proposed seam must be distinguishable from an existing
  interface; no invented method is presented as implemented.
- G4 requires complete placement on every requested target, including retained
  table rows and actual rendered views. Report partial surface coverage accurately.
- A reviewer who wrote the pitch performs author audit only. Independent review
  needs another real reviewer with access to the same source evidence.
- An unresolved open question cannot be hidden by renaming it a risk, choosing
  `ready` in a manifest or calling a spike “planned.”

## Constraints

This capability judges advancement and does not authorize production work,
human betting, external sharing or runtime privileges. It does not implement a
platform-level security boundary. Enforcement here is the conductor's explicit
control flow and its recorded review decisions; stronger runtime enforcement
requires a separately implemented verifier, outside this design-only task.

## Examples

Frame includes “Use a new message queue” under Boundaries: G1 fails with that
quote, even if the artifact says `solution_present: false`.

Evidence log lists a question as answered but links only to a future spike: G2
returns `needs_spike`, cites the unresolved question and permits no Stage 3.

Pitch scores average 4.5 yet lacks its security-owner matrix: G3 fails. A
four-row HTML table cannot pass G4 against a twelve-row source table.

## Evaluation Rubric

| Check | Pass |
| --- | --- |
| Meaning-sensitive | Detects solutioning and uncertainty regardless of headings/status labels |
| Evidence-grounded | Every pass identifies the observation supporting it |
| Fail-closed | Failed and stale gates prevent advancement |
| Complete | Exemplar elements and both rubrics are assessed individually |
| Independent | Author and independent reviewer are identified honestly |
| Reproducible | Inputs, revision, verdict and actual correction are recorded |
