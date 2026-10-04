# Ways of working, for shaping

This guide separates agent instructions from words spoken to a person. Keep
bookkeeping in the agent instructions and records. Use the read-aloud blocks for
status and questions, filling them with the actual facts. The bound gate policy
continues to own acceptance, scores and execution boundaries.

## Agent instructions: purpose and people

Prepare a proposal a person can fund. Following Shape Up, describe the problem,
appetite, bounded solution, rabbit holes and no-gos. Appetite is the person's
willingness to spend, not an estimate or an invented deadline. Rabbit holes are
risks or difficult details that need investigation, mitigation or a stop boundary.
No-gos are deliberate exclusions with reasons; naming a risk does not resolve it.
Keep the frame free of a selected solution and leave detailed build tasks to the
team after the bet.

Identify who can confirm the problem, appetite and scope, who supplies technical
evidence, and who can fund the proposal. Where those roles exist, product leads
framing with engineering support; engineering leads shaping with product support.
Use the team's own role names. One person may hold several human roles, but an
author cannot supply the required independent review of their own work. The
conductor coordinates and records; authors propose; independent reviewers assess.
Do not invent departments, assign staff or infer decision authority from a title.

Record each human choice against the proposal revision, with the person's actual
answer and confirmed authority. Preserve it as a candidate decision event until
existing reconciliation and acceptance incorporate it; human confirmation and
accepted runtime state are separate facts. Never edit an accepted snapshot or its
derived decision view to insert an answer. A material revision requires a fresh
affected decision; never transfer an old yes silently. A relayed, disputed or
simulated answer is not a confirmed funding decision. Preserve dissent.

## Agent instructions: package eligibility

A bet may be offered only when a sequence diagram, a component diagram and a data
contract exist and convey the proposed solution. An empty file, a heading or a
flowchart named as a sequence does not qualify. Keep the full bundle's data-flow
diagram and security-owner table, evidence, risks and no-gos. Check that the same
actors, direction, data meaning and ownership agree across the package; expose
contradictions and unresolved material seams before offering the bet.

The data contract names input and output meaning, producer, consumer, state,
evidence and owner. A network API is optional. The interface entry can be a cited
interface, an identified in-process interface, or the exact token `no API`.
Use `no API` only when no API is part of the proposed interaction; an unknown
interface stays an unresolved research question. With `no API`, input meaning,
output meaning, producer, consumer, state, evidence and owner remain required.
Use only methods, paths and schemas supported by evidence. Mark existing,
proposed and unknown behavior
separately. A proposed behavior can be shaped before it is implemented; an
unsupported claim about existing behavior must return to research.

Leave non-load-bearing internals to builders. "The builder will choose" cannot
replace a missing interaction, component boundary, data meaning or critical owner.

Only if the team already sizes by layer, use its existing layer names and scale.
For every named layer, record its owner and size with provenance, or an explicit
decision that it is not involved. A blank size is unknown and keeps the package
incomplete for the bet question. Invalid or unmapped values also remain gaps.
Use only this team's existing layer names and sizing practice. Keep appetite,
estimates and any local capacity calculations as distinct facts. Teams without
layer sizing omit the layer section.

## Agent instructions: decisions and later work

Package completeness is not an independent review. Accepted G3 PASS is required
for later design; it does not fund the proposal or grant execution authority.
G4 Bet-ready records required delivery verification, not a person's investment.
Keep the actual G3 and G4 status in the record. Beside a package question, tell
the person the plain meaning of any pending review or delivery, using the glosses
below. G3 and G4 each retain their existing acceptance requirements after a bet.

When an authorized person says bet, record their yes against this proposal
revision and stop shaping. Keep Bet-ready unchanged. Design, tickets, build and
the later integration run remain unopened. Describe outstanding review or delivery
in plain words.
Later design needs accepted G3, the human bet, any delivery the person actually
requested, and its own scoped authority. Hand over the exact package revision, evidence, review
receipts, decisions, open gaps and boundaries; a document link alone is insufficient.
Design, the integration run that follows the bet, and build happen later. This
skill starts none of them and creates no implementation tasks.

## Words to use with a person

### Agent instructions for speaking

At each pause or milestone, fill the four status lines from the current record.
Use everyday words for the problem, present activity, missing input and next action.
Keep exact bookkeeping labels in agent records. When their meaning matters to the
person's next choice, give the plain gloss once at its first relevant mention.

| Agent label or record | Plain gloss to use when relevant |
| --- | --- |
| review_pending | Independent review has not come back. |
| Independent review pass | The proposal passed independent review. |
| Independent review fail | Independent review found these problems: [specific findings]. |
| G4 / Bet-ready | The requested copies have been saved and checked. Use this only when true; otherwise name the failed or pending save/check. |
| candidate decision event awaiting acceptance | Your answer is recorded; the record checks are still pending. |
| accepted snapshot | The last checked version. |
| derived decision view | A summary of the recorded decisions. |

Treat these as translations, not extra status lines. Keep each statement tied to
what actually happened. A failed document upload is "the document upload failed."
After a bet, "Your yes is recorded. Shaping has stopped" describes the human
choice and the stop; review and delivery keep their separate recorded states.

### Read-aloud status pattern

Fill the braces with actual facts before speaking:

```text
Working on: {the person's problem and current action}.
Where we are: {preparing the proposal, waiting for your choice, reviewing, or stopped}.
What is missing: {the specific evidence or answer, or nothing needed for this choice}.
Next step: {the pending choice or next permitted action}.
```

### Agent instructions for questions

Ask only for a pending decision within the requested scope. Reuse a settled answer
on progress or resume when the proposal and authority are unchanged. Use an
ask-the-user tool when the host has one; otherwise show the choices in text and
wait. A host with limited choices can use a supported free-text answer or staged
menu. Dependent work waits for an actual answer; silence, a default selection and
an empty tool result leave the question pending.

When the package is eligible and betting is in scope, ask the package question
when independent review returns a pass, a fail, or review_pending. Say the result
in plain words. Ask then even if target publication is pending or an upload has
failed; G4 remains a separate delivery check. A person may also request the
question before review finishes. Apply the same package prerequisites and follow
the chosen branch. Preserve a recorded bet through a delivery failure. Keep an
unchanged answer on resume while its record checks are pending.

## Human pauses

The trigger and action paragraphs below are agent instructions. Only the quoted
questions and listed choices are read aloud.

### Frame decision

When the frame and its current review are ready, ask:

"The problem statement is ready. What should happen next?"

- Accept it and prepare the proposal
- Revise the problem statement
- Stop

For a frame-only request, the first choice is "Accept it and finish here."
G1 and the G2 research required before shaping retain their existing requirements.
For a full workshop, proceed through research before shaping.
A requested frame correction stays in framing; stop ends the current effort.

### Package has a gap

At a package decision, if required artifacts, meaning, evidence, ownership or
applicable layer sizes are missing, name the actual gap and ask:

"The proposal still needs [missing item]. What should happen next?"

- Keep working on the proposal
- Stop

This menu contains only continued shaping or stopping. "Keep working on the
proposal" permits the next shaping action within existing authority. Evidence
requirements and separate authority for executing a spike remain in force.
New feasibility uncertainty returns to research; changed outcome, scope or
appetite returns to framing. Do not ask this question for every unfinished draft.

### Package decision

Use the review-return trigger above, or the person's request for an earlier
decision, once the package is eligible and betting is in scope. Ask:

"The proposal has its diagrams and data contract. A network API is optional.
What should happen next?"

- Bet this package
- Add or revise an API boundary first
- Authorize a separate walking skeleton — a small trial of the proposed parts together
- Revise the proposal
- Stop

Offer the skeleton choice unless the person has said there is no code to try.
The person supplies repos and code locations after choosing it. Leave repository
discovery to that separately authorized effort. Keep draft-only and artifact-only
requests within their original scope.

"Bet" records the authorized person's yes for this revision and stops shaping.
Bet-ready keeps its existing recorded status; design remains unopened and still
requires an accepted G3 pass and the person's yes, plus its own scoped authority.
"Add or revise an API boundary first" stays in shaping:
use cited interface evidence, an in-process interface or `no API`. If evidence is
missing, record the question and return to research; the choice cannot authorize
an invented endpoint. "Revise the proposal" records the requested correction
and reopens the affected stage. "Stop" records the hold and ends this effort.

A skeleton choice records the person's request, package revision and any supplied
scope and bounds, then stops this skill. The person supplies repos and code
locations to that effort. Do not launch it, clone repos or write code here.
Its scoped execution authority is separate from permission to continue shaping.

### Skeleton returned

On a return, record which package revision was tried, what was observed, what was
mocked, discrepancies and limits. A return without evidence stays a reported
judgment, not technical proof. Compare it with the current package before asking:
"Did the skeleton apply the sequence diagram, the component diagram and the data
contract?"

- The trial supports the proposal. Return to the bet decision
- The proposal needs correction
- Stop

"The trial supports the proposal" returns to the package decision only if the
current package remains eligible. Evidence gaps and the person's bet decision
retain their own requirements. A mismatch
returns to the affected shaping or research work; changed outcome, scope or
appetite returns to framing. Changed artifacts need renewed affected review.
A skeleton does not set sizes, mark Bet-ready, open design or replace the later
integration run. Do not repeat a previously confirmed bet for an unchanged revision.

## Guidance for different teams

Recommend this process before detailed design, planning or build. Research may
use bounded specialist advice where it resolves a material uncertainty; that is
not permission to start downstream design. Use the team's supplied artifact home
and links without requiring a particular tracker or document platform.

For example, a local file transformation can use `no API` while still showing its
components, execution sequence, data movement, input/output meaning and security
owners. A team without layer sizing omits that sizing section. The full package,
human decisions and independent review remain required in both cases.
