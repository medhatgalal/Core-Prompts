---
name: engos-quality-shaping-gate
description: Check whether a shaping stage may advance from its actual artifacts, evidence and prior receipts. Reject solution-in-framing, invented evidence, unresolved material questions, stale reviews and incomplete publication. Use within guided shaping or independent pitch review.
display_name: Shape Up Stage Gate
kind: workflow
capability_type: skill
version: v1.0
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
full. For G3 also read resources/references/rubrics.md and the current review-evidence
route, including resources/references/review-evidence.md. For any runtime operation
read resources/references/runtime.md and the helper's current --help first.

## Workflow

1. Verify subject identity, predecessor hashes and source coverage. Hold missing,
   stale or contradictory dependencies before evaluating a later stage.
2. Inspect actual prose, citations and required artifacts. Explain each failed
   predicate with a quote or missing item. Read source evidence instead of trusting
   manifest claims. A named spike or rejected question is not uncertainty closure.
   At Research, assess the author's source/summary agreement, range-scoped
   exclusivity, updated citation referents and material callee evidence.
3. Distinguish human decisions, engineering evidence and expert judgments. Check
   the three actual answers in order using the conductor's ways-of-working.md:
   engineering accepts the frame before shaping; the team accepts the package
   before the table; the table accepts a pitch before a handover. Four plain lines
   precede each question, using the host ask-the-user tool or a text menu and wait.
   Silence is not a yes. Missing agreement or an unanswered question holds the
   transition; continue independent work only within the current phase.
4. For future `shaping-gates.v4+rubric.v4` / `review_evidence: true` G3,
   seal the author subject first, then derive one ordered packet for exact subject, run,
   work order, policy and stable reviewer identity. Include all required artifacts,
   question/decision snapshots, sources/renders and cited code spans with portable
   paths/hashes/read order. Bind the immutable seal/return hash; post-seal host
   observations bind the packet hash, with no circular pre-seal read requirement.
   Require host-observed opens; receipt assertions alone
   authenticate neither reading nor identity. Validate membership, hashes, spans
   and source/render ownership. Require decodable source-bound PNG/SVG and actual
   independent pixel inspection; Mermaid text or blank/unrendered assets hold
   review. Continue identifying independent substantive defects.
   For G3 inspect every local render and all contract/security rows, cross-check
   their meaning, apply the existing twelve-score rubric and keep author audit separate from actual
   independent review. Lack of independent context means review_pending.
   A set with no selected work is an unscored hold naming the walk-away item.
   Check proposed extensions as proposals; absent code is not proof they cannot
   be selected. Check the whole set and the frame's requested observable stop. Hold shaping
   output containing a spec, requirements, design, architecture document, plan or
   task list; they belong to a separate build session. Fat-marker diagrams,
   contracts and provisional workstreams retain their existing shaping scope.
   Every in-item needs one proof sentence. Check the proposed build/deferred/
   forbidden lists against the pitch; no silent drop, addition or scope cut.
5. On table Accept, require one handover with the three lists, shaping-finished
   evidence, shaping-did-not-do statement, spec-first next step and Not done list.
   Check it against the accepted pitch revision using the conductor's handover.md;
   hold missing or widened scope. Send back returns to shaping; abandon stops;
   split hands nothing to build until a smaller pitch receives its own accept.
   Check that API and skeleton choices occurred only inside shaping.
   After the handover is written, require the output question: HTML, Google Doc,
   Word, JSON, Markdown, or all of them. All means all five; verify only chosen
   outputs. Markdown reuses the complete existing source/hash with three Mermaid
   fences, captions and full contract/security tables. Required content precedes
   candidate seal; incomplete accepted sources hold delivery for candidate/
   reconciliation, renewed hashes and affected review without accepted overwrite,
   changed bet or second authored prose. Private Google Doc conversion DOCX is
   not a selected Word copy. For G4 inspect each
   saved target's revision, content, tables and diagrams. Word is handover-only
   through the existing host Word skill, reusing source-bound diagram images.
   Reopen Word for full text/table/image inventory, then inspect every rendered
   page. Google Docs needs current saved-revision readback, native editable tables
   with every row, full inline-image inventory and saved-target pixels. HTML needs
   saved-page pixels and full content parity; JSON needs parsing and full diagram/
   caption/contract/security/accepted-decision parity. Check Markdown reuse and
   complete content separately; report unavailable verification honestly.
   A successful upload, empty target list or source-only image check is insufficient.
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

Cost 3 includes a restatement of appetite; more wording of the same bound cannot
earn 4. One example of this pattern is listing the same bounded operations again
without additional supported cost evidence. A failed average below 4 with all
scores at least 3 and no other miss requires new evidence, a named spike or a
hold before another pitch. Floors remain 3 per dimension and 4 overall. Unopened
load-bearing facts return to Research before scoring; Research notes contradicting
opened code still fail. Reviewers inspect sequence pixels and assess independently;
no conductor message supplies the preferred verdict.
Floor classification uses the current policy-binding digest; valid older receipts
stay history after common integrity checks, without current coverage requirements.
Unverifiable persistent history is recovery_pending, not an ordinary hold. A
policy migration cannot be used as an automatic retry or counted as a new fact.

The accepted handover permits every build-these line and prohibits dropping one,
adding a deferred line or building a forbidden line. “Proceed and loop” continues
the current item; it cannot widen the sheet. A wider job needs a new pitch and a
new accept. Gate tokens, scores and file paths stay in agent records, not the
person's handover prose. Source inspection establishes instruction coverage only;
it does not prove that a later build agent will obey the sheet.

## Current-profile review contract

Read gates.md and review-evidence.md as the single policy/contract owners. Claims
about existing decision seams require a predicate over a typed field the receiving
function actually reads, with cited span, contract input, sequence message and
accepted-proof relationship. Comments/unrelated fields are insufficient; proposed
behavior may be absent. New/nontechnical seams need reasoned applicability, never
an escape from an existing seam. Non-blocking unanswered questions require exact
proof/question-specific source-bound independence quotes; a respondent answer is
not required for that evidence. Dependent answers need the named respondent's
authority and observed provenance, never fixer substitution.

Preserve twelve numeric dimensions, reject booleans/nonfinite/invalid values and
recompute aggregates: each >=3, mean >=4, mandatory assessments pass. Require
structured unresolved-predicate and finding/assessment/verdict consistency;
missing predicates cannot pass beside empty or irrelevant findings. Independently
audit semantic rationales, paraphrase and negation; scanners cannot determine
truth. Each substantive finding has exactly one typed evidence-bound return and
repair: missing pixels -> review hold; missing predicate -> Research; mismatch
with established predicate -> Shaped; dependent question -> named respondent.
Report concurrent findings and prerequisites. Routes do not execute transitions;
next_state remains the assessed gate. Version new structured contracts deliberately
and preserve legacy schema-1 findings and pinned historical receipt interpretation.

Offer a fixer independent of author/reviewer only after failure; start only with
explicit user acceptance of that repair. Bind stable host identities and every
revision contributor as author; none may grade that revision even with renamed
roles/display names. Missing identity/opening capabilities hold honestly. Consent
adds no hidden launch, named agent, product work or downstream authority.

## Constraints

The script checks mechanical consistency, not truth or human authority. Host-bound
worker provenance and permission boundaries must be observed separately. It is not
a sandbox against a caller who can rewrite its state. No sharing, production code,
issue-tracker work, betting decision, native agent registration or privilege expansion.

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

## Visual Quality and Evidence-Derived Progress

Visual review checks readability and reference fidelity in addition to existence
and semantic coverage. Inspect labels, captions, legends, hierarchy and all table
fields at the intended surface size. Reject broken-word table columns or missing
linked detail even when row counts match. Source, visual review and saved-target
proof remain distinct. Preserve every original field and source-bound SVG/PNG.

For a status/progress request, load the progress/runtime route from the current
resource map and read helper help. Derive views from controller state and actual
observations, not author assertions. Distinguish accepted versus candidate, queued
versus last-observed active, blocked versus awaiting input, and local receipt
integrity versus remote freshness. Requested stopping points govern which stages
are applicable. Simulation, snapshot time and unknown activity must remain visible.
The projection never accepts a stage, overrides drift, appoints owners, publishes
externally or grants betting authority. Existing default status behavior remains
compatible; the resource contract specifies the actual new interface.

Blast radius: all full-shaping gate users receive the added visual criteria and
optional progress projection; standalone pitch review still does not fabricate
historical stage acceptance or infer a live monitor.

## Existing Capabilities and Architecture Fit

The current gate policy adds existing_capability_evidence at G2 and architecture_fit
at G3. Read their meanings in resources/references/gates.md and current rubric;
use the current policy example for new runs. Assess scoped investigation, credible
options and evidence-backed disposition, not a mandatory reusable-component find.
Justified new capability and intentionally separate responsibilities may pass.
Missing optional specialist participation alone is not failure; missing material
proof, contradictory responsibilities or unreasoned duplicate capability hold.
For nontechnical/no-material-seam work require an explicit reasoned applicability
assessment. Do not invent code findings or force architecture into framing.

Use the existing receipt mechanism for these mandatory current-profile predicates;
the helper checks outcomes/evidence bindings, not semantic fit. Preserve old pinned
policy history. Adopting current policy requires the documented policy-rebind path,
not silently adding assessments to historical receipts. All shared full-shaping
gate consumers receive this policy; standalone review reports actual coverage
without fabricating earlier stages or implying new checks already passed.
