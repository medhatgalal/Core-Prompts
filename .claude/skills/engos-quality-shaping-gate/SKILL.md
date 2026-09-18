---
name: "engos-quality-shaping-gate"
description: "Check whether a shaping stage may advance from its actual artifacts, evidence and prior receipts. Reject solution-in-framing, invented evidence, unresolved material questions, stale reviews and incomplete publication. Use within guided shaping or independent pitch review."
version: "v1.0"
---
# Shape Up Stage Gate

## Purpose

Judge Intake, Framed, Research, Shaped and Bet-ready separately. Make missing
decisions and evidence actionable without inventing a pass. Own the shared stage
policy and mechanical state helper; the host owns tools, permissions and dispatch.

## Primary Objective

Permit only supported, current stage transitions. A useful hold identifies the
failed condition, evidence or decision needed, responsible person/role and next
permitted action. It does not discard useful drafts or reopen unrelated decisions.

## Invocation Hints

Use at each engos-design-shaping handoff, to inspect a resumed run, or as the
gate component of engos-audit-pitch-review. A standalone pitch can be reviewed
without fabricating historical gates; report unassessed prerequisites explicitly.

## Required Inputs

Stage, original brief/constraints, candidate inventory, prior receipts, current
source/policy identities, question/decision snapshots, source access, actual host
reviewer identity, authorship and targets. Read resources/references/gates.md in
full. For G3 also read resources/references/rubrics.md. For any runtime operation
read resources/references/runtime.md and the helper's current --help first.

## Workflow

1. Verify subject identity, predecessor hashes and source coverage. Hold missing,
   stale or contradictory dependencies before evaluating a later stage.
2. Inspect actual prose, citations and required artifacts. Explain each failed
   predicate with a quote or missing item. Read source evidence instead of trusting
   manifest claims. A named spike or rejected question is not uncertainty closure.
3. Distinguish product decisions, engineering evidence and expert judgments. Ask
   the designated human when authority is missing; continue independent work only.
4. For G3 inspect every local render and all contract/security rows, cross-check
   their meaning, apply both scorecards and keep author audit separate from actual
   independent review. Lack of independent context means review_pending.
5. For G4 inspect each saved target's revision, content, tables and diagrams. A
   successful upload, empty target list or source-only image check is insufficient.
6. Return the documented predicate-level ReviewReceipt with exact subject/policy
   and evidence bindings. The controller checks and accepts it using the runtime;
   the reviewing worker never writes accepted state or approves its own work.
7. After repairs, reevaluate the affected conditions and dependencies. Preserve
   failed receipts and changes. New scope reopens framing; new material design
   uncertainty reopens research. Keep content readiness distinct from delivery.

## Required Output

A structured receipt and a short explanation: current stage; pass/fail/unverifiable
conditions; inspected content hashes; evidence; actual reviewer/authorship; blockers;
repair owner; next permitted stage. G3 adds all twelve scores, rationales, means,
top fixes and three hardest questions. Never substitute `complete` for a verdict.

## Rules

The gates and rubric resources are the single policy owners. Missing mandatory
assessment or unverified material feasibility holds regardless of average. Interpret
score anchors at shaping depth; do not demand a built feature solely for points.
Question deletion cannot waive a risk. Human-reviewed private evidence is labeled
accurately, not AI-verified. Preserve typed scope and source identity across exports.

## Constraints

The script checks mechanical consistency, not truth or human authority. Host-bound
worker provenance and permission boundaries must be observed separately. It is not
a sandbox against a caller who can rewrite its state. No sharing, production code,
Jira work, betting decision, native agent registration or privilege expansion.

## Examples

A frame saying "poll every ten seconds" fails G1 even if its JSON says no solution.
A recorded but unrun spike fails G2. A polished pitch without a security owner fails
G3. Three images uploaded but not read back on the saved Doc fail G4. A prior passed
pitch retains content-ready status when only its requested publication is blocked.

## Evaluation Rubric

| Check | Passing behavior |
| --- | --- |
| Meaning | Reads actual clauses and evidence, not just status labels |
| Progress | Valid current evidence advances; missing evidence holds the right stage |
| Independence | Actual non-author review; contaminated context restarted or held |
| Completeness | Exemplar coverage and full saved-target inventories checked |
| Recovery | Replayed/stale work cannot double-apply or overwrite accepted state |
| Honesty | Mechanical, semantic, visual and human evidence remain distinct |


Capability resource: `resources/capability.json`
