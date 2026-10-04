# Seven answers, written before the instructions change

These are the requested answers, recorded before editing any skill or resource.
They are not a test set or a grading rubric for a later patch.
Before every question, show four plain lines: what we are doing, where we are,
what is needed, and the next step. Use the host's ask-the-user tool when available;
otherwise print the choices and wait. Silence never accepts anything.

## 1. Engineering has not agreed the frame

Question: “The frame is ready. Does engineering agree, and are their questions
answered?” Choices: Accept the frame and start shaping. Revise the frame. Stop.
Record the actual answer and engineering's agreement and answered questions, or
the missing agreement/questions, against the frame revision. Shaping does not
start without the actual acceptance and that agreement; revise stays in framing,
and stop ends the effort. Formats produced: no handover exports.

## 2. The team has not accepted the shaping package

Question: “The shaping package is ready. Does the team accept it?” Choices:
Accept it and go to the betting table. Keep shaping. Stop.
Record the actual team/package decision, revision, remaining concerns, and current
review/delivery state. The betting table stays closed without actual team acceptance
and the existing required evidence. Keep shaping stays in shaping; stop ends the
effort. API decisions stay in shaping. A separately authorized walking skeleton
is offered only there and omitted if the person said there is no code to try.
Formats produced: no acceptance handover or new unrequested exports.

## 3. Accept one item, HTML only

Question: “Accept this pitch, send it back, abandon it, or split it?” Choices:
Accept. Send back. Abandon. Split.
Record the person's accept against the exact pitch revision and write one handover:

- In this handoff, build these: Show the stored status on the existing page.
  Proof: With a stored status present, the existing page displays that same status.
- Named, and not in this handoff: A per-worker status row is deferred because this
  pitch accepts only the stored status on the existing page. It needs its own
  pitch before anyone builds it.
- Do not build: A second queue.

Also record Shaping finished (agreed frame, existing component, sequence and
data-flow diagrams, data contract, API decision or no API, and any skeleton result);
Shaping did not do (spec, requirements, design, architecture, plan, tasks);
Next (a separate build session starts at spec only for the build-these list);
and Not done (everything named and not in this handoff).
After writing that handover, ask “Which outputs do you want: HTML, Google Doc,
Word, JSON, or all four?” The person selects HTML only. Produce only the HTML
copy, reusing the existing diagram bundle and verifying the saved HTML. Stop;
do not start spec or build. Keep the source handover and decision/delivery records.

## 4. Split because an item has no single proof sentence

Question: “Accept this pitch, send it back, abandon it, or split it?” Record Split,
the unprovable item, and the smaller pitch candidates with their own scope and
proof sentences. Hand nothing to build: no accepted handover, spec, plan or tasks.
Each smaller pitch returns through the affected shaping/review and team decision;
one must receive its own accept before its handover exists. Formats produced:
no acceptance handover exports.

## 5. Proceed and loop picks up the deferred row

The handover must state that a build session may finish every build-these line,
may not drop a line, and may not build a deferred or forbidden line. “Proceed and
loop” continues the current item and cannot widen the handover. The deferred row
therefore cannot enter the current build scope. Record the scope conflict; ask
for a new pitch and a new accept if the person wants a wider job. No silent scope
change, extra accepted item, or new handover format is produced.

## 6. All four outputs

After writing the one accepted handover, ask “Which outputs do you want: HTML,
Google Doc, Word, JSON, or all four?” Record All four and produce HTML, a native
Google Doc, a Word document (.docx), and a full document JSON export of that same
handover. Reuse component.mmd, sequence.mmd (a real sequenceDiagram), data-flow.mmd,
contracts.md, and security-owners.md from the accepted shaping-artifacts bundle;
reuse their source-bound SVG/PNG derivatives where the destination needs images.
Use the existing embed/render path and the existing host Word skill, not a second
diagram renderer. Record source identity and saved-target checks for all four;
inspect saved visual outputs and parse/compare JSON. A failed target remains
pending, with no false all-four completion claim.

## 7. Shaping writes design and tasks

Gate result: Hold. The output includes downstream documents shaping must not
write. Record the design document and task list as violations and the needed
repair. Do not treat them as approved deliverables, accept the package for the
betting table, or hand them to build. Return to shaping for an in-scope package;
do not delete useful user files. No handover formats are produced. After repair,
ask the package question before opening the table; no previous yes is inferred.
