# Guided Shape Up

Start with your notes. The assistant helps product and engineering frame a problem,
collect evidence, shape a bounded solution and prepare a pitch for review. You do
not need a finished specification, repository access or a separate prompt for every
stage. You retain decisions about appetite, scope and whether to bet.

## Your choice after shaping

The proposal makes the solution visible with a sequence diagram, a component
diagram and a data contract. The full bundle also includes the data-flow diagram,
security owners, evidence, risks and exclusions. Missing artifacts or unresolved
material seams keep the proposal in shaping.

A network API is optional. A contract can identify a cited network interface, an
in-process interface or `no API`. Input/output meaning, producer, consumer, state,
evidence and ownership remain required. An unknown interface remains a research
gap; it cannot be filled with `no API` or an invented endpoint.

Layer sizing applies only when your team already uses it, with your own layer
names and scale. Each named layer needs an owner and size, or an explicit decision
that it is not involved. A blank size stays unknown and prevents the bet offer.
Teams without layer sizing omit that section.

The workshop pauses three times, in order:

1. “The frame is ready. Does engineering agree, and are their questions answered?”
   Accept the frame and start shaping, revise the frame, or stop. Missing agreement
   or unanswered engineering questions keeps shaping closed.
2. “The shaping package is ready. Does the team accept it?” Accept it and go to
   the betting table, keep shaping, or stop. The table needs actual team acceptance
   and current independent review. Choosing, revising or omitting an API stays in
   shaping. A walking skeleton is a separately authorized effort offered only there,
   and omitted when you have said there is no code to try.
3. “Accept this pitch, send it back, abandon it, or split it?” Send back returns
   to shaping; abandon stops. Split makes smaller pitches and hands nothing to
   build until one receives its own accept.

Accept produces one handover with three lists: **In this handoff, build these**,
with one proof sentence per item; **Named, and not in this handoff**, with each
reason and the need for a separate pitch; and **Do not build**, with the forbidden
lines. It includes the agreed frame, existing diagrams and contracts, API decision
and any actual skeleton result. It states what shaping did not do and everything
still outside this handoff. Shaping writes no spec, requirements, design,
architecture document, plan or tasks.

The assistant then asks which copies you want: HTML, Google Doc, Word, JSON, Markdown, or all of them. All means all five. It produces only your selection, reuses the package diagrams and tables,
checks the saved outputs and stops. Word is a handover-only copy through the host's
existing document skill. A private DOCX used to convert a Google Doc is not a selected Word output.
A failed save preserves your accept and stays pending.

A separate build session starts at spec only for the build-these list. It may
finish every line, may not drop one and may not pick up deferred or forbidden work.
“Proceed and loop” continues the current item. A wider job needs a new pitch and
a new accept.

Before every question, status uses four plain lines: **What we are doing**,
**Where we are**, **What is needed** and **Next step**. The assistant uses the
host's ask-the-user tool when available; otherwise it prints options and waits.
Silence is not a yes. Gate tokens, scores and file paths stay in agent records,
with a plain explanation when their meaning matters to your next choice.

## Evidence and migration status

A live workshop has not been run for this guidance. Earlier mechanical tests,
independent source reviews, simulated preflights and teaching-fixture publication
checks have narrower scopes. Case-reader answers and release checks do not prove
workshop usability, authenticated host behavior or a complete real-input pitch
on its requested surfaces. This release makes no such claim.

Future review-evidence runs use `shaping-gates.v4+rubric.v4`, with the existing
twelve scores. Earlier profiles retain their original interpretation. An existing run keeps its pinned gate bytes. Adopting the new gate prose
requires an explicit G0 rebind, which invalidates current acceptances and requires
reassessment. Installation alone does not rebind a live run or rewrite history.
No implementation, tickets, staffing, sharing or further installation follows
from shaping a proposal.

## Evidence-directed iteration

Use engos-design-shaping as conductor and engos-quality-shaping-gate as the sole
workshop reviewer/rubric owner. The legacy ten-point pitch-review is available
for standalone assessment; it does not score this loop.

The current review-evidence profile is shaping-gates.v4+rubric.v4. Research adds a hashed opened-
source inventory, research-coverage.json. Shape adds shape-set.json with selected
piece IDs, existing/proposed-extension claims and their evidence/basis references.
These extend the existing journal; old runs retain their pinned history and need
an explicit G0 policy rebind before claiming these checks.

| Observation | Next step |
| --- | --- |
| Research note contradicts opened code | Fail Research and inspect/repair that fact |
| Load-bearing existing claim has no opened Research evidence | Reopen Research before pitch review |
| Confirmed behavior is absent from code | Shape it as a proposed extension with researched basis |
| Set selects no pieces | Unscored hold naming the walk-away item |
| Only average <4 fails, every score >=3, evidence unchanged | Stop pitch dispatch; acquire a new fact, name a spike or hold |
| Accepted handover, current review, requested copies checked and separate build authority | Start at spec for every build-these line; do not drop one or add deferred/forbidden work |

Cost 3 includes restating appetite. One example of this pattern is listing the
same bounded operations again without new supported cost evidence; more prose
cannot make it 4. Proposed behaviors are not required to already exist, but an
unsupported current-state assumption cannot be relabeled as a proposal. Evaluate
the pieces jointly, and make the proof observe the frame's requested completion
or stop condition. An intermediate observation alone does not satisfy it.

For the documented limited renderer, use a real sequenceDiagram, short labels,
white background and no alt/else. Gray actor fills are a known limitation; use
role-colored bands and a legend, retain the real sequence and open its rendered
pixels in independent review. Color limitations do not justify a flowchart.

Repository maintainers can inspect `reports/engos-design-shaping/` for detailed
run evidence when available. Reports are not included in release archives; this
runbook's status and limitations are self-contained and do not depend on that folder.

## Review evidence and repair

Future current-profile reviews use one sealed ordered packet for the exact
candidate, run, work order, policy and stable reviewer identity. It includes all
required documents, questions/decisions, diagram sources/renders and cited code
spans. The reviewer opens these in order with host-observed evidence, then
independently inspects actual PNG/SVG pixels. A matching hash proves byte identity;
it proves neither reading nor correctness. Missing host opening or identity
capabilities hold review honestly. Blank, unusable or missing diagrams also hold
review; independent substantive defects remain visible.

At an existing decision seam, the contract and sequence message must identify a
predicate over a typed field the receiving function already reads, with a cited
read span and relationship to the accepted proof. Proposed behavior may still be
absent from code. Comments or similar names elsewhere do not establish this.
Genuinely new or nontechnical seams require a reasoned applicability assessment.
An unanswered question can remain open when a source-bound quote establishes that
its exact proof is independent of the answer. That quote can come from code or an
accepted artifact; it needs no invented respondent answer. When the proof depends
on the answer, the named respondent must answer with attributable authority.

Every independent finding has one evidence-bound repair route: missing pixels
holds review; a missing supported predicate returns to research; contract/diagram
mismatch after grounding returns to shaping; a needed answer returns to its named
respondent. Concurrent findings retain their prerequisite relationships. These are
recommendations, not automatic transitions. Numeric score floors remain twelve
scores, each at least 3 and mean at least 4. The reviewer separately checks whether
rationales, findings and verdict contradict each other; mechanical checks cannot
establish semantic truth.

A failed review can offer a fixer independent of author and reviewer. It starts
only after your explicit acceptance of that repair. Every contributor to the
revision becomes its author and cannot grade it, even with a renamed role or
display name. The host must establish stable identities. This grants no new named
agent, hidden launch, downstream build or authority to answer for someone else.
Historical receipts, accepted meaning and human bets remain unchanged.

## Recovery and author handoffs

The runtime classifies floor-only failures under the current policy-binding digest.
A valid older-policy receipt remains in history and need not grow a new coverage
file. Common journal integrity still matters. Unverifiable current coverage or
history reports `recovery_pending` with exit 3; an ordinary unmet gate reports
`hold` with exit 2. Read the status/exit code, not a label in the reason text.

Ask for recovery when state cannot be verified:

> Resume this shaping run under its pinned policy. If its history cannot be
> verified, name the missing or corrupt binding and the recovery action. Do not
> delete old observations, rewrite accepted artifacts or change policy to evade
> the last review.

A policy migration is deliberate: record changed rules, authority and impact,
use an explicit G0 rebind that invalidates current acceptances, then reaccept the
affected gates. A policy hash change is not a
new product fact and never automatically makes an old failed receipt a pass.

The researcher checks summary/quoted-source agreement, occurrence claims across
the declared ranges (including tests), changed citation referents and material
callee implementation claims before returning the note. These are semantic
checks under the existing evidence-sufficiency predicate, not a second rubric or
proof supplied by a grep match. A call-site citation does not cover the callee.

The conductor accepts, reopens and dispatches; the assigned author repairs prose,
diagrams and other candidate content. Before seal, compare the actual worker
return inventory/hashes with the candidate. Drift requires a fresh author return.
This protocol does not authenticate authorship by itself; host observations and
permissions remain separate. The runtime's post-seal candidate_returned event is
not a pre-seal authorship receipt.

## Start here

Verify that all five core skills from the reviewed bundle are available, not just
the entry. If any are missing or outdated, follow
[Enable the shaping bundle](#enable-the-shaping-bundle) to preview installation.
If the complete current core bundle is available, no new installation is needed.

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

Repository context is resolved when Research begins. The current repository is the
default boundary; the assistant may ask which folders or modules matter when a
monorepo or multi-root workspace is ambiguous. It should use maintained project
knowledge and an active language server or semantic/indexed search when available,
then bounded text search such as `rg`. These are runtime capabilities, not required
tools or product-specific defaults. A repository supplied during framing is recorded
for later Research and does not permit solutioning before the Framed gate passes.

Keep confidential material in an approved private project location. Do not put
company source documents into a public capability repository. The assistant should
identify the artifact home and account before exporting or publishing.

The first response should summarize the problem, identify material uncertainty,
suggest the next step and ask no more than three useful questions. It should not
invent your budget or choose an architecture before framing.

## Enable the shaping bundle

Use a trusted release containing these skills or a verified source checkout that
contains the reviewed implementation. A merge to main does not create a release
or update an existing installation. Older saved selections do not automatically
add newly introduced skills. Verify the entry and its dependencies before use.

The workshop core bundle is five skills: `engos-design-shaping`,
`engos-design-frame-from-vague`, `engos-quality-shaping-gate`,
`engos-delivery-diagram-contract-artifacts`, and `engos-delivery-artifact-embed`.
The legacy `engos-audit-pitch-review` is optional for standalone ten-point review;
it is not a second scorer or required installation for this workshop.
The command below also selects three optional advisors:
architecture, code health and testing. Omit those three only if you want the
conductor to report unavailable advice and use its bounded fallback.

From the trusted checkout root, preview a Codex installation. Replace `codex` with
your selected supported provider (`claude`, `gemini`, `kiro`, `grok` or `agy`) as
appropriate. Do not run against a source checkout you have not reviewed.

```bash
SHAPING_PLAN="$(mktemp -t engos-shaping-plan.XXXXXX)"
bash scripts/deploy-surfaces.sh --target "$HOME" --allow-nonlocal-target \
  --cli codex --surface-only \
  --slug engos-design-shaping \
  --slug engos-design-frame-from-vague \
  --slug engos-quality-shaping-gate \
  --slug engos-delivery-diagram-contract-artifacts \
  --slug engos-delivery-artifact-embed \
  --slug engos-design-architecture \
  --slug engos-audit-code-health \
  --slug engos-quality-testing-review \
  --dry-run > "$SHAPING_PLAN"
```

For an existing Grok workshop, preview the updated conductor and gate together
with the previously missing diagram helper:

```bash
bash scripts/deploy-surfaces.sh --target "$HOME" --allow-nonlocal-target \
  --cli grok --surface-only \
  --slug engos-design-shaping \
  --slug engos-quality-shaping-gate \
  --slug engos-delivery-diagram-contract-artifacts \
  --dry-run > "$SHAPING_PLAN"
```

This is an explicit selection; routine saved-profile updates do not add a missing
diagram package. Apply the reviewed plan as described below and confirm the three
Grok package hashes match the merged generated source. Customized files are retained
and reported by the installer.

Review the plan's exact selection, actions, preserved files and blockers. Only
after accepting that plan, apply from the same unchanged checkout and target:

```bash
bash scripts/deploy-surfaces.sh --target "$HOME" --allow-nonlocal-target \
  --apply-plan "$SHAPING_PLAN"
```

This surface-only selection skips updater/launcher refresh and does not create
named agents. Customized or unknown packages are preserved, not forcibly replaced;
resolve reported conflicts before claiming installation complete. See
[installation and recovery](INSTALL-PROFILES.md) for saved selections and rollback.

Start a fresh assistant session, confirm `engos-design-shaping` and its supporting
skills are available, and use the starter request above. Codex's selected skills
install under `~/.agents/skills`, shared with Gemini; other provider locations are
listed in the installation guide. Ordinary-language discovery depends on the host;
explicitly name/select the skill if it is not discovered.

Keep business documents in your own authorized project folder, not this public
capability repository. CLI/source access, independent workers, diagram rendering
and cloud credentials are host capabilities, not permissions created by the bundle.
Missing capabilities must produce a useful hold or documented manual handoff.

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

### Check what already exists

For technical work, the assistant investigates relevant code, configuration,
services, libraries and architecture decisions before recommending new components.
It cites the inspected scope and revision, or requests attributable evidence from
an engineer when access is unavailable. No search hits do not prove global absence.

Research notes retain the findings; the shaped pitch explains whether to configure
or reuse, extend, evolve/refactor, replace, build new, or intentionally keep separate
responsibilities. Only credible alternatives need comparison. Applicable replacement
decisions cover compatibility, ownership, migration/rollback and retirement.
Existing code is not automatically the right answer; unrelated cleanup stays out.

The conductor may suggest architecture advice for a material boundary decision,
code-health advice for an observed structural concern, or testing advice for a
compatibility/migration proof plan. It explains why and manages bounded handoffs.
You do not need to choose skill names. Missing an optional skill does not stop
work with sufficient evidence; missing a load-bearing fact or required independent
review does. No automatic installation, full-repo audit or product refactor follows.

Current-profile G2/G3 reviews explicitly check existing-capability evidence and
architecture fit. Old runs retain their original pinned policy and must be rebound
and reassessed before claiming the new checks. Framing remains solution-free.

### Stage outputs and gates

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

Markdown is the editable source and a selectable handover output. The output
question is “HTML, Google Doc, Word, JSON, Markdown, or all of them?” All means
all five; only selected deliverables are produced. Word remains handover-only.
A private DOCX conversion for Google Docs is not a selected Word deliverable.

Markdown reuses the complete existing handover file and records its hash. It keeps
all three Mermaid fences, captions, full contract and security tables and accepted
decisions; rendered images supplement the source. Repeating the choice reuses that
file, rather than writing a second prose document. New handovers include required
content before sealing. An incomplete sealed or accepted source holds delivery:
authorized completion uses the existing candidate/reconciliation path with the
same logical source identity, renewed hashes and affected review, preserving
accepted bytes/history and the bet.

HTML requires saved-page pixels and full content parity. Google Docs requires
readback of the current saved revision, native editable tables with every row,
full inline-image/diagram inventory and saved-target pixels. Word requires
reopening the saved file for full text/table/image comparison, then rendering and
inspecting every page. JSON requires parsing and full content parity, including
diagrams, captions, contract/security tables and accepted decisions. Markdown
reuse and complete content are checked separately. A successful export or source
screenshot is not saved-target proof. Unavailable checks remain explicitly pending.
Shaped content still requires independent local diagram pixel inspection.

The bundle includes a read-only handover selection/reuse helper. It compares the
supplied source hash and exact accepted diagram/caption/table inventory, returns
the same Markdown file and checks adapter evidence records for consistency. It
creates no copies, renders or publications. A valid selection plan is still
delivery-pending; host-observed readback and independent visual/semantic checks
remain required. A source symlink, changed bytes or incomplete inventory holds
reuse without overwriting accepted state.

The engineering pitch includes component, sequence and data-flow diagrams, complete
interface and security-owner tables, and explicit boundaries. These are required
outputs of shaping, not a substitute for the earlier work.

### Reader presentation

Ask to match supplied references, not merely copy their headings. The assistant
should compare rendered pages, use a clear stage/appetite introduction and heading
hierarchy, and place figures beside the narrative they explain. Mermaid remains
editable source; rich exports can include source-bound SVG for HTML and PNG for
documents. The shaped profile uses explicit section anchors, captions, alternative
text and optional visible titles/legends. A frame-only profile reads `framed.md`
without demanding solution diagrams or a fabricated pitch.

Wide contract tables can have a concise primary view and linked detail retaining
every original field. Tables remain editable, not screenshots. Native acceptance
tables retain their own schema. Self-contained HTML uses validated local assets
and no runtime CDN; it must actually be opened offline before that claim is made.
Native-Mermaid surfaces remain supported. Neither a polished page nor successful
conversion changes acceptance or authorizes external placement.

Source Markdown/JSON remains available alongside representations. Unsupported or
unsafe input, stale assets, missing anchors and oversized rows fail with a specific
repair request. Rendering and saved-target inspection are required; a parser pass
or row count cannot establish readable figures or complete Google Docs placement.

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

### See the current flow

> Where are we? Show what is accepted, what is blocked, who is needed and the
> next permitted action. Keep the latest accepted document separate from its draft.

The progress view is an as-of snapshot from the existing run record, available in
conversation and JSON/Markdown/HTML. It leads with the stage, next action, assigned
worker, needed input/respondent and the requested result. Stage indicators include
verified, waiting for review/input, blocked, stale, queued and outside scope.
Technical revisions and the full evidence projection remain available in details.

For example, a requested frame can finish with two verified gates and later stages
outside scope. A changed Google Doc can leave accepted Shaped content intact while
Bet-ready needs fresh target verification. Counts are gates, not percentages of
effort. Missing owners stay unassigned; lack of activity does not prove a worker
is hung. Simulation is labelled, and unknown provenance stays unknown.

Recorded placement and local receipt integrity are distinct from the latest target
observation. The view does not poll remote documents or update them automatically.
Its accepted-artifact link is an immutable evidence snapshot; the assistant can
also provide a separately rendered reader-document link. Direct standalone framing
without a run reports an unaccepted draft, not invented gate history.

For operators, resolve the gate package's resource root and inspect its current
help. From that resource root, the read-only calls are:

```text
python3 scripts/shaping_run.py progress --run RUN_DIRECTORY
python3 scripts/shaping_run.py progress --run RUN_DIRECTORY --format markdown
python3 scripts/shaping_run.py progress --run RUN_DIRECTORY --format html
```

`RUN_DIRECTORY` is the actual controller-owned run, not a new status database.
Only the controller records context and host observations through the documented
`progress-context` and `observe` operations with exact expected versions. Status
queries do not themselves advance stages, create assignments or approve spending.

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
