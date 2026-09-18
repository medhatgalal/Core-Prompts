# Guided Shape Up

Start with your notes. The assistant helps product and engineering frame a problem,
collect evidence, shape a bounded solution and prepare a pitch for review. You do
not need a finished specification, repository access or a separate prompt for every
stage. You retain decisions about appetite, scope and whether to bet.

This capability is under pilot validation. Generated packages and mechanical tests
do not establish that every host or external publishing path has been verified.
Current source-candidate status: local mechanical tests, independent source reviews
and simulated conversational preflights have run. The simulations do not replace a
real product/engineering pilot. Saved Google Docs verification, real-human pilot
acceptance, hosted CI and dual-remote landing remain pending. No automatic
implementation, tickets, staffing, sharing or global installation follows from
shaping a pitch.

Repository maintainers can inspect `reports/engos-design-shaping/` for detailed
run evidence when available. Reports are not included in release archives; this
runbook's status and limitations are self-contained and do not depend on that folder.

## Start here

Ask your assistant to use `engos-design-shaping`:

> Help us frame and shape this problem. Read these documents first, tell us what
> you understand and guide product and engineering through the missing decisions.

In a host using explicit skill names, select that skill through its normal skill
mechanism. It loads the supporting skills; you do not have to coordinate them.

Supply what you have:

- A complaint, rough idea, meeting notes, existing frame, specification or pitch.
- Relevant document links or files. Text, Markdown, searchable PDF, DOCX and native
  Google Docs are supported inputs through available host readers. Scans/images
  may need text extraction or selected pages; unreadable content is disclosed.
- Optional repository path/link and relevant revision, with authorized read access.
- Any actual appetite, constraints, exclusions and decision owners already agreed.

Keep confidential material in an approved private project location. Do not put
company source documents into a public capability repository. The assistant should
identify the artifact home and account before exporting or publishing.

The first response should summarize the problem, identify material uncertainty,
suggest the next step and ask no more than three useful questions. It should not
invent your budget or choose an architecture before framing.

## Choose how research happens

| Mode | What the assistant does | What you supply |
| --- | --- | --- |
| AI-led | Inspects authorized code, specs, configuration and tests, citing revisions | Access and decisions only humans can make |
| Human-led | Drafts focused research requests and checks returned evidence | Permitted excerpts, specifications, observations or attributable review results |
| Hybrid | Splits questions between available sources and human owners | Missing evidence and decisions, without duplicate asks |

You can change modes without restarting. A source reference that cannot be opened
is not treated as verified. An expert opinion can support judgment but is not
relabeled as a completed experiment. Private evidence can be assessed by a
designated independent human with its scope and limitations recorded.

## Work through the stages

| Stage | You receive | What permits the next stage |
| --- | --- | --- |
| Intake | What is known, assumed, missing and merely suggested | Faithful original input, honest source coverage, no invented solution |
| Framed | Problem, people, why-now, outcome, appetite/walk-away, boundaries and questions | Actual decision provenance and no selected solution |
| Research | Answers with evidence, or concrete bounded research requests | No unresolved in-scope blocking uncertainty |
| Shaped | Problem and solution, diagrams, contracts/security owners, cuts, risks and No-Gos | Complete artifacts, inspected diagrams and independent review |
| Bet-ready | Approved content on every requested surface and betting preparation | Current saved-target content, rows and images verified |

Shaping can reopen research. Changed scope can reopen framing. This is not a
one-way sequence that invents answers to keep moving. A future builder-level
choice is also not automatically a blocking research question.

Ask for **frame only** to stop after framing, **shaped draft only** to stop after
content review, or name the final surfaces. Bet-ready does not mean the team has
approved the bet or started building it.

## If you do not know an answer

Say so. The assistant should explain the decision using your scenario, check the
material you already provided and offer the smallest useful next step. An unknown
fact needs evidence; an undecided preference needs trade-offs; an unknown owner
needs help finding the right expertise. None is permission to invent a decision.

You can answer, challenge, attach evidence, delegate, defer or stop. Rejecting a
question's wording does not erase the underlying uncertainty. The assistant should
show what remains blocking and why, not keep asking the same question differently.

Expect a checkpoint after the agreed interview effort, with a summary and choices
to continue, narrow, delegate or hold. A long list of new questions is not progress
unless those questions change the decision you are trying to make.

## Bring an engineer or product owner into the conversation

Ask for a teammate card. It contains the decision needed, relevant context, options,
evidence, dissent, expected respondent and a simple way to answer or challenge it.
Share it through your normal approved channel; the assistant does not contact
people or grant access automatically.

When someone returns, the assistant explains what changed and what remains open.
“Engineering agrees” relayed by another person is recorded as a relay, not direct
approval. Conflicting answers remain visible until the appropriate owner resolves
the decision. Product can change scope; it cannot turn missing technical proof
into an observed result.

## Documents and edits

Markdown is the editable source. HTML is a review view. JSON contains structured
documents and workflow records, with source identity. Google Docs uses native tables
and inline diagram images. You choose the outputs; the assistant manages the files.
JSON delivery is checked by parsing and full structured-content comparison, not
by inventing target screenshots. Shaped content still requires local diagram
render inspection; HTML and Google Docs require saved visual checks.

The engineering pitch includes component, sequence and data-flow diagrams, complete
interface and security-owner tables, and explicit boundaries. These are required
outputs of shaping, not a substitute for the earlier work.

If people edit a published Doc, ask:

> Review the edits in this Doc against the current pitch. Preserve our changes,
> show conflicts and tell us which decisions or reviews need refreshing.

The assistant compares the published baseline, current Doc and current source.
Comments remain discussion; material changes become candidates for review. It must
not silently overwrite concurrent edits or claim that an old export is current.

## Resume or understand a hold

> Resume this shaping folder or registered document. Tell us what is accepted,
> what changed and the next decision needed.

Expect separate status for content and delivery. For example: “Pitch review passed;
HTML verified; Google Doc delivery needs access.” A delivery failure should not
make you repeat settled product decisions. An unverified required target still
prevents overall Bet-ready completion.

The run is stored in the project's artifact home, normally `planning/<task-slug>/`.
The assistant maintains candidate outputs, immutable accepted revisions, question
and decision snapshots, reviews and delivery receipts. You should not need to
shuffle these files manually.

## Maintainer and pilot notes

Six roles use five shaping/support skills and the existing pitch reviewer. Workers
receive bounded context and write candidates; the controller accepts state. Actual
reviewers are independent of authors. Generic workers are sufficient for the pilot;
no new provider-native registration is implied. Host permissions and inherited
context must be checked separately from prompt instructions.

The gate package's runtime reference documents the actual CLI/schema and recovery
semantics. The embed package documents local export dependencies and external
placement checks. Use those canonical resources, not copied commands from an old
session. A self-authored pass flag cannot substitute for an actual review.

Before rollout, verify cold start, two unknown answers, human-led completion,
conflicting evidence, teammate return, document edits, stale work, interrupted
acceptance and separate publication failure. At least one real approved bundle
must be verified on HTML and Google Docs. Keep model trials separate from observed
human usability; neither static checks nor this runbook certifies the latter.
