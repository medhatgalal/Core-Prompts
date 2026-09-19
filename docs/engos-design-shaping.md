# Guided Shape Up

Start with your notes. The assistant helps product and engineering frame a problem,
collect evidence, shape a bounded solution and prepare a pitch for review. You do
not need a finished specification, repository access or a separate prompt for every
stage. You retain decisions about appetite, scope and whether to bet.

This capability is under pilot validation. Generated packages and mechanical tests
do not establish that every host or external publishing path has been verified.
Current source-candidate status: local mechanical tests, independent source reviews
and simulated conversational preflights have run. The user-selected pilot uses
independent subagents; real-person usability remains unmeasured, not an extra
recruitment requirement for that pilot. A private Google Docs teaching-fixture import has
passed saved-content and independent nine-page visual checks; this is adapter
evidence, not real-pitch acceptance. A subsequent six-role product/engineering
simulation exercised framing, evidence handoffs and a complete candidate draft.
Its result was partial. The source candidate now adds rich presentation profiles
and evidence-derived progress views; visual iterations and independent checks
are recorded separately from the earlier pilot. Worker access limits must not
be turned into product requirements. Role-play does not
establish real-person usability. The repository-fit exercises additionally cover
reuse, justified new work, intentional separation, missing access and specialist
scope; two request-overload findings were repaired and replayed successfully.
A complete real-input pitch on both requested surfaces, latest-candidate hosted
checks and dual-remote landing remain pending. Earlier hosted checks passed for an
older candidate; they are not evidence for later changes.
No automatic implementation, tickets, staffing, sharing or global installation
follows from shaping a pitch.

Repository maintainers can inspect `reports/engos-design-shaping/` for detailed
run evidence when available. Reports are not included in release archives; this
runbook's status and limitations are self-contained and do not depend on that folder.

## Start here

Verify that all six core skills from the reviewed bundle are available, not just
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

The core bundle is six skills: `engos-design-shaping`,
`engos-design-frame-from-vague`, `engos-quality-shaping-gate`,
`engos-delivery-diagram-contract-artifacts`, `engos-delivery-artifact-embed`, and
`engos-audit-pitch-review`. The command below also selects three optional advisors:
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
  --slug engos-audit-pitch-review \
  --slug engos-design-architecture \
  --slug engos-audit-code-health \
  --slug engos-quality-testing-review \
  --dry-run > "$SHAPING_PLAN"
```

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

Markdown is the editable source. HTML is a review view. JSON contains structured
documents and workflow records, with source identity. Google Docs uses native tables
and inline diagram images. You choose the outputs; the assistant manages the files.
JSON delivery is checked by parsing and full structured-content comparison, not
by inventing target screenshots. Shaped content still requires local diagram
render inspection; HTML and Google Docs require saved visual checks.

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
