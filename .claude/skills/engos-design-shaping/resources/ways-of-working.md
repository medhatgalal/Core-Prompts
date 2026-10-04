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

Package completeness is not independent review or a human accept. Keep current
review and delivery evidence separate from the three human decisions. The team
question requires a complete package and current accepted independent review;
pending or failed review stays in shaping. Applicable requested package copies
must be saved and checked before the table opens. Do not require unrequested copies.

On Accept at the table, record the person's answer for this pitch revision and
write one handover using handover.md. Then ask which outputs they want, produce
only those copies, verify the saved targets and stop. Preserve the accept if a
save fails, but report the missing copy and next delivery action. No spec,
requirements document, design, architecture document, plan or tasks are written.
A later build session starts at spec only for the handover's build-these list.
Neither a person's yes nor a review receipt starts that session.

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
After acceptance and selected output checks, say "Your accept is recorded. The
handover is written. Shaping has stopped." Name failed saves plainly; do not
claim the chosen outputs are complete until each is verified.

### Read-aloud status pattern

Fill the braces with actual facts before speaking:

```text
What we are doing: {the person's problem and current action}.
Where we are: {framing, shaping, team decision, betting table, handover, or stopped}.
What is needed: {the specific evidence or answer, or nothing needed for this choice}.
Next step: {the pending choice or next permitted transition}.
```

### Agent instructions for questions

Ask only for a pending decision within the requested scope. Reuse a settled answer
on progress or resume when the proposal and authority are unchanged. Use an
ask-the-user tool when the host has one; otherwise show the choices in text and
wait. A host with limited choices can use a supported free-text answer or staged
menu. Dependent work waits for an actual answer; silence, a default selection and
an empty tool result leave the question pending.

Ask the three questions below in order. Do not jump from a frame accept or team
accept to a funding decision. A prior answer carries only when its proposal
revision and confirmed authority are unchanged. Show the four plain lines before
every question, including the output question. Do not call an incomplete or
failed-review package ready. It stays in shaping with the missing evidence and
next action visible; the person may keep shaping or stop.

## Human pauses

The trigger and action paragraphs below are agent instructions. Only the quoted
questions and listed choices are read aloud.

### 1. Before shaping

When the solution-free frame and its current review are ready, ask:

"The frame is ready. Does engineering agree, and are their questions answered?"

- Accept the frame and start shaping
- Revise the frame
- Stop

Record the actual answer, engineering agreement and answered questions against
the frame revision. Missing engineering agreement or unanswered questions holds
shaping even if someone selects Accept. Revise stays in framing; Stop ends the
effort. Existing frame/research evidence remains required. This is the full
workshop menu. For an explicitly separate frame-only request, keep the question
but use “Accept the frame and finish here” as the first choice and stop after
frame acceptance; do not offer or enter shaping or the later two decisions.

### Inside shaping: API and separate trial

Choosing, revising or omitting an API stays in shaping. Keep the optional network
API and complete data-contract rules above. A walking skeleton is a separate
effort the person authorizes. Offer it only inside shaping and omit the offer
when the person has said there is no code to try. Record its requested scope and
package revision, then stop this skill; do not launch it, discover repositories,
clone or write code. The person supplies code locations to that separate effort.
Neither API choices nor a skeleton choice appears at the betting table.

### 2. Before the betting table

When the package is complete and current independent review is accepted, ask:

"The shaping package is ready. Does the team accept it?"

- Accept it and go to the betting table
- Keep shaping
- Stop

Record the actual team answer for the package revision. Without team acceptance,
the table stays closed. Keep shaping returns to shaping; Stop ends the effort.
Accept opens the table only when applicable package delivery checks also hold.
A needed API change or omission is shaping work, and a needed trial is a separate
authorized effort offered only there. New evidence gaps return to research;
changed outcome, scope or appetite returns to framing and renews affected answers.

### 3. Betting table

After actual team acceptance and the applicable checks, ask:

"Accept this pitch, send it back, abandon it, or split it?"

- Accept
- Send back
- Abandon
- Split

Record the actual choice and pitch revision. Accept writes one scope handover
under handover.md, asks for output choices and stops after the selected copies.
It starts no build documents. Send back returns to shaping. Abandon stops.
Split makes smaller pitch candidates with their own build/deferred/forbidden
scope and one proof sentence per in-item; hand nothing to build until one smaller
pitch completes its affected checks, team acceptance and its own table accept.
An in-item without one proof sentence needs correction or splitting, not an
invented proof or silent deletion. No partial acceptance of an unresolved list.

### Skeleton returned

On a return, record which package revision was tried, what was observed, what was
mocked, discrepancies and limits. A return without evidence stays a reported
judgment, not technical proof. Compare it with the current package before asking:
"Did the skeleton apply the sequence diagram, the component diagram and the data
contract?"

- The trial supports the proposal. Return to shaping review and the team decision
- The proposal needs correction
- Stop

"The trial supports the proposal" returns through affected shaping review and
the team decision only if the current package remains eligible. Evidence gaps and the person's bet decision
retain their own requirements. A mismatch
returns to the affected shaping or research work; changed outcome, scope or
appetite returns to framing. Changed artifacts need renewed affected review.
A skeleton does not set sizes, mark delivery complete, start a build session or
replace later integration checks. Do not repeat a previously confirmed bet for an unchanged revision.

## Guidance for different teams

Recommend this process before detailed design, planning or build. Research may
use bounded specialist advice where it resolves a material uncertainty; that is
not permission to start downstream design. Use the team's supplied artifact home
and links without requiring a particular tracker or document platform.

For example, a local file transformation can use `no API` while still showing its
components, execution sequence, data movement, input/output meaning and security
owners. A team without layer sizing omits that sizing section. The full package,
human decisions and independent review remain required in both cases.
