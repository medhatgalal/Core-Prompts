# engos-delivery-shaping implementation ledger

Authority: user explicitly requested "Proceed with implementation and the pilot
under the reviewed plan." This supersedes the plan snapshot's no-implementation
scope, not its safety/acceptance requirements. Original instruction: fresh worktree,
land on main when done. No runtime goal was requested or started. No new native
agent registrations, home installation, Jira work or product implementation.

Reviewed plan: engos-design-shaping-operating-plan.md, SHA256
1bfb7f01766dbaf8b7c134d3515bd2cf6ebe7162c43cee666e58dd59942b5766.
Task 01a0af1e-f573-7af2-9e64-b2c5abdd4774; worktree
/private/tmp/engos-full-shaping-design; branch AI/engos-full-shaping-design.
Pre-implementation HEAD 59488c0; GitHub main ccf62d9 verified by fresh fetch.
GitLab fetch and authenticated API returned HTTP 403 AccessDenied. Local cached
GitLab a92e0ff has the same tree but does not establish current remote parity.
Continue local work; dual-remote landing remains blocked until normal access returns.

## Current continuation status — presentation and progress verification

Main/MR reconciliation (2026-09-19): Scott's pending work is one GitLab MR!82
containing four independent skills: answer discipline, outbound writing, review
flow and claim discipline. It is not subsumed by shaping and is not included in
v1.16.0. MR!82 remains conflict-blocked at22c7e595 and lacks current routing-fitness
metadata/current-main docs regeneration; its historical pipeline does not establish
current readiness. No shaping dependency or mention was added. Native skill
descriptions plus current advisory routing metadata remain the cheapest future
route after that MR is independently refreshed and accepted.

Current origin/main now includes gitlab/main and the mergedv1.15.3 routing/model-
guidance work. It was merged into this branch. Conflicts were additive: both
shaping and current-main CI tests survive; VERSION remainsv1.16.0; CHANGELOG keeps
v1.16.0 above v1.15.3; generated manifests/job maps/status/release delta were rebuilt
against the actual publishedv1.15.2 baseline. A cheap Luna mechanical reviewer and
Terra docs reviewer found staging/source-only wording issues; both were repaired.
Focused result:97passed/1docs-contract failure, followed by5/5docs-contract pass;
strict validation passed32SSOT. No broad historical suite was repeated per user
direction. Merge review remains pending exact staged recheck and hosted CI.

Repository-neutral correction (2026-09-19): user confirmed that shipped skills
must use the repository in which they run and may ask for relevant folders/modules;
project knowledge, LSP/semantic indexes or other available capabilities should
accelerate bounded scans without becoming tool requirements. The Appian pitch
example remains reader-facing in docs only. Canonical engos-design-shaping and
engos-audit-pitch-review were updated through same-slug UAC plan/judge/apply, with
one new routed repository-discovery resource and five-provider regeneration.

Independent instruction review found and drove three repairs: residual product
defaults in pitch-review, brittle wording/blacklist tests, and an invalid UX-based
exception for missing Product participation. Final review PASS has no P1/P2.
Behavioral exercises covered clear single-repo, ambiguous monorepo and docs-only
input. The initial single-repo run exposed premature code scanning; after a bounded
iteration, framing deferred scanning until acceptedG1/G2, monorepo Research asked
which module applied, and docs-only framing skipped repo discovery. Reused worker
contexts are disclosed; no fresh-sandbox or real-user claim. Verification:
276shaping passed/13 optional renderer skips;40focused docs/resource passed;
strict32-entry validation passed. See engos-quality-repository-neutral-validation.md.
This corrects the earlier planning error: AE/product branches are pilot evidence,
not capability dependencies or release blockers.

Latest pilot checkpoint (2026-09-19): G1-frame-2 passed all four independent
predicates and was accepted immutably at version12, snapshot768e936dfee204a2989baa3b28b810f951b155ca350f8e70cfa9198c47328048.
The first G2 research attempt correctly failed before sealing because U2/U3 were
still blocking. A clean local AE checkout was then discovered and bound at exact
revisionbf4b8e023b69413e16280e993d10b0e9af327a19 for G2-research-2.

G2-research-2 produced and sealed revision-bound pm-core, process-mining,
pm-dev-tools and AE evidence, but independent reviewer
01a0ba8a-16a7-7762-abde-123ecef931de returned FAIL. Grounded risks passed; the
other three predicates failed because the pinned AE revision remains remote/Thor
facing while pm-core exposes separate in-process preprocess/generateInsights APIs.
No inspected adapter, integration result or attributable assessment proves the
status/failure/read-visibility/result-contract mapping. Actual runtime acceptance
returned hold/gate-not-passed; state remains acceptedG1 at version15. Local AE
refs prepr-min and ads-prepr were inspected without checkout/fetch: they contain
partial preprocessing adapters but retain the old asynchronous insight path and
do not close the mapping. Do not advance G3 or waive D2.

Smallest unblock: supply an exact AE integration/adapter revision, executed
compatibility result, or attributable scoped technical assessment mapping
pm-query-lib preprocessing publication and insight generation onto AE completion,
polling/failure and persisted-result contracts. If unavailable, explicitly decide
whether this replay remains a demonstrated G2 hold and a different fully evidenced
problem supplies the successful G0-G4 acceptance pilot. No merge/release yet.

2026-09-19 continuation: direct user reply "Use the proposed replay framing"
confirms the three previously proposed historical-replay framing choices. Exact
private decision provenance is recorded separately without rewriting earlier
approvals or failed reviews. G1 reopened at version9/generation1; acceptedG0 is
unchanged. Fresh junior-product author01a0b9b3-ab02-78e2-b8e6-d653754e6570 and
junior-engineering reviewer01a0b9b3-adaa-7ee1-9253-6d514e457835 are assigned to
G1-frame-2. Technical feasibility and owner evidence are not inferred from this
human confirmation. Release publication is now in scope per the user's later
request for a new version; real-home installation remains outside scope.

Current-head hosted refresh: GitHub branch35439066408 and PR35439068283 both
SUCCESS for a491bd4818c2ddba5725e7aedebbb283a60fb6cf; GitLab MR pipeline6855248
SUCCESS for that same SHA. Both reviews remain draft; no merge/release claimed.
PR89 is attached to the task. The artifact tool rejected internal GitLab MR92's
URL as unsupported; the MR itself remains accessible and linked in this ledger.

Model-switch checkpoint: user asked about a smaller model to reduce token use.
Controller interrupted the active G1-frame-2 author for a safe checkpoint; reviewer
has only acknowledged its role and has not inspected a candidate. No G1-frame-2
seal or acceptance occurred. Resume that exact unsealed attempt after checking
the author's return/files, or assign a new attempt if actor identity changes.
Do not redo G0, restart research, or infer a passing G1 from the user confirmation.

Public-disclosure approval has been exercised: GitHub draftPR89 and internal
GitLab draftMR92 are open for AI/engos-full-shaping-design. Integrated candidate
1d5d9e8 contains both current main ancestries and preserves the upstream release
and shaping changes. GitHub branch/PR checks succeeded; GitLab branch check
6855208 succeeded, with the separate MR pipeline tracked throughMR92. Do not
infer merge readiness from these checks: the actual replay remains at acceptedG0
with G1changes_requested on product outcome/scope. No Google Doc was created,
because publishing before currentG3 would bypass the agreed pipeline.

The failed-review control-field ambiguity is now clarified in canonical gate
runtime.md: every verdict uses next_state=the assessedorder.gate, while fail
leaves acceptance unchanged. Same-slug UACplan/judge/apply succeeded; no runtime
code change or semantic verdict was made. A regression verifies malformedG0
binding rejects, correctedfailedG1canberecorded, andacceptance staysG0. The focused
progress/docs suite passed82tests, and independent reviewer01a0b93c-b8ba-79a0-b52c-aef7c9878e54
found noP1/P2; all five generated copies and manifest hashes match. This is a
follow-up to1d5d9e8 and requires its own hosted checks after push.

Current next action: obtain the three proposed framing choices asked in this
continuation (correctness-first saved-insight refresh goal, bounded existing-schema/
object scope with external data-layer prerequisites, historical migration rationale),
record direct response as new decisions, and create a freshG1attempt. Earlier
"approve all three" resolved public publication, appetite/walk-away and private
Doc permission only; it must not be reused as answers to these later questions.

Approved replay execution now uses an actual runtime journal with separate fresh
junior-product author and junior-engineering reviewer per stage. G0 passed actual
independent review and was accepted; replaying that same receipt returned replayed
without a second acceptance. G1 passed confirmed appetite/walk-away and solution
purity but failed problem/outcome and human scope-boundary predicates. Actual CLI
acceptance returned hold/gate-not-passed with no pointer mutation. The accepted
stage remainsG0; progress records G1changes_requested andG2–G4not_reached.

The missing items are product choices, not renewed publication permission:
affected user/action and freshness/success, intended scope/exclusions, and why-now.
Three focused proposed replay choices were asked asynchronously, grounded in the
historical note. No answer received at this checkpoint. No solutioning or Doc
publication occurs past this failed gate. Preserve the original/corrected failed
receipt: reviewer initially used last-acceptedG0 in next_state; a corrected copy
uses assessedG1 per runtime contract without changing any semanticFAIL findings.
This exposed a documentation-clarity follow-up for failed-receipt field semantics,
not permission to manufacture a passing verdict.

Private replay root remains outside the public repo. Runtime and input/skill bytes
are pinned there; integration builds do not rewrite them. Actual source/review
provenance is labelled real historical replay, not a live product/staffing bet.
Current actors: G0author01a0b92c-0e3e-7b43-b35a-52106c3491e4,
G0reviewer01a0b92c-1dc2-7651-9c80-5615fbdd5d38;
G1author01a0b937-1237-7261-afac-4beac86c8454,
G1reviewer01a0b937-1e79-70b1-a37e-a49c51cb2462. All stopped after their scope.

Upstream integration preserves thev1.15.2/Supercharge fixes and both CI test sets;
see reports/merge-conflicts/engos-delivery-shaping-upstream.md for actual conflicts,
two discovered integration defects and their reviewed repairs. Final affected
suite147passed; strict32-entry and contract/topology checks passed after regeneration.

2026-09-19 approval update: user explicitly said "approve all three" in this task.
This confirms public GitHub code/sanitized-evidence PR and gated landing; historical
replay appetite five weeks/two engineers and the correctness/ownership walk-away;
one private work-account Continuous Update pilot Doc, no sharing/notifications.
It does not approve a production bet, new scope exclusions, fabricated feasibility,
release/tagging or real-home installation. Earlier pending-approval statements below
are historical and superseded. Resume the real-input replay at current G0/G1 with
fresh bound receipts; retain the earlier failed/held reviews without rewriting them.
Primary checkout/main is read-only. Fresh upstream main now contains the separate
Supercharge/v1.15.2 work; integrate and renew affected delivery checks before landing.

Conditional landing/readiness continuation: user requested remaining work to land
cleanly if ready, updated frontpage/docs/examples, and how to start. Independent
readiness reviewer01a0b590-ffc2-7e43-9b70-8c9aea3fc6d1 returned No-Go: the original
real-input pilot still has no acceptedG0–G4 chain, attributable replay appetite
and walk-away remain pending, and the same accepted real pitch is not verified
on HTML plus Google Docs. The prior exploratory47/12 score remains below4.0;
presentation repairs are not a new content verdict. Human recruitment is NOT
required for the user-selected subagent pilot. Generic merge permission is already
given; specific public-disclosure/private-Doc decisions remain unresolved.

Asked three scoped asynchronous questions: explicit public GitHub PR/gated-merge
approval; historical five-week/two-engineer replay appetite with correctness/
ownership walk-away (no team commitment); one new private Continuous Update pilot
Doc in the work account, no sharing/notifications. No answers received at this
checkpoint. No additional external writes, PR/MR, push or main changes occurred.

Frontpage now has a copyable guided starter and progress/reuse/resume examples.
Runbook includes all six core skills plus three optional advisors and exact
surface-only dry-plan/apply instructions. Readiness status does not imply a real
human trial or completion. Docs reviewer01a0b596-0af2-7662-b33a-ac0e3d0cb470 found
twoP2 issues: ambiguous private artifact home and entry-only setup check. Both
fixed and independently rechecked: docs-onlyPASS, no remainingP1/P2 findings.

Setup rehearsal used a fresh disposable physical tmp directory, never real HOME.
Reviewed68new-write actions:67package files for9Codex skills plus one installation
state file; no blockers/preserved conflicts, updater/launcher or native-agent
configuration. Installer returned complete transaction39248f5d9cd74a99aed06bd8157545f2.
All67package hashes matched,9entrypoints present, installed runtime/exporter help
worked, and repeating the documented dry-run returned0actions. The logging helper
initially failed after saving the successful apply receipt because actions was an
integer, not an array; corrected logging and readback/no-op verification established
the result without repeating apply. This proves the disposable installation path,
not real-home installation, live discovery or source-pilot success.

Docs/resource checks66passed after the wording repairs; strict32-entry validation
passed. No capability source/generated bundle change in this docs slice. Preserve
unique evidence and the unmerged worktree; do not relabel this as mainline delivery.

Repository-fit continuation (user approved application plus testing): both existing
conductor/gate skills now include scoped capability investigation, justified
reuse/non-reuse, conditional architecture/code-health/testing advice and two new
current-profile predicates. Same-slug UAC and five-provider regeneration complete.
See engos-quality-repository-fit-validation.md for frozen criteria, red/green
tests, nine actual actor calls across seven cases and the corrective handoff
iteration. Initial specialist replies exposed request overload; the direct route
now includes question guidance and distinguishes active asks from queued unknowns.
No specialist source or runtime executable changed. Final local checks:272shaping,
72package/resource and92UAC/contract passes;1optionalrenderer test skipped.
Strict32-entry and contract/topology checks pass. Independent outcome assessment
confirms scoped validation: initial5pass/2partial, both repaired replays pass;
latest observations cover7scenarios. Five initial cases were not rerun after the
narrow repair; no causal superiority or full-pipeline claim. Nine actor calls,
one outcome assessment under the disclosed amended ceiling and original deadline.
No new push, PR/MR, merge, install or release.
Earlier hosted pipelines have now succeeded for7e94f9e only; no hosted evidence
exists for this newer local change. Existing publication and full-pilot holds remain.

Delivery update: implementation committed as7e94f9eb217bc998356b8767e45db9b1e6c4a0b5.
The branch was pushed to both configured remotes. Subsequent GitHub draft-PR
creation was blocked by automatic review pending explicit approval for public
disclosure; do not retry via another route or publish more without resolving it.
No PR or MR was created, no main ref changed. The public GitHub branch already
exists: the rejection happened after both successful pushes. User was informed
and asked for explicit approval. GitLab visibility verified internal, project13564.
Both branch pipelines began on exact7e94f9e: GitHub run35349247955 and GitLab
pipeline6848064. At the latest readback both were running, not accepted as green.
Read-only checks may continue; publication, pilot and merge limits remain explicit.
The historical no-push statements below describe earlier checkpoints only.

2026-09-18: the five same-slug candidates have passed UAC judge and apply, and
all five provider bundles are regenerated. Canonical exporter SHA256 is
353efb6e917d5c58027613347a5db630cc22759c2f3e1794daffa34771b8c9bd;
runtime SHA256 is 2e56fa597d1493f7f9a0cff9d6705b1678e9d003e332367b07feb02751388247.
Independent instruction/code/docs reviews resolved their blocking findings.
Framed two-page and Shaped eleven-page local renders passed independent pixel
review. HTML loads at 375/1280/1920 with no page overflow, missing images, broken
internal anchors, scripts or external requests. A real narrow-screen hash overflow
was caught, fixed and independently reviewed. Complete details and limits are in
[the presentation/progress verification](engos-quality-presentation-progress-verification.md).

Six distinct product/engineering role simulations passed the focused status-card
comprehension check; that does not establish human usability or complete G0–G4.
The user explicitly selected subagents for the pilot: named human participants are
not a prerequisite to that simulation. The historical real-input exercise still
lacks an attributable appetite decision; do not invent it or relabel simulation
as real approval. Earlier successful private Google Doc placement remains evidence
only for its previous payload. The new richer private Doc awaits exact approval;
the old Doc is untouched. No new upload, sharing or notification has occurred.

Strict surface validation and contract/topology checks pass. All twelve native
DOCX regressions pass; the HTML/presentation focused suite has 71 passes and one
optional renderer skip (actual renderer execution is separate evidence). Six
macOS presentation tests passed outside the sandbox after native-service denial.
Broad rerun:1445passed,13skipped,138subtests,3 build/test-race failures caused by
controller regeneration during package copying. After freezing generation, all72
package/resource checks pass, including those cases. This combined evidence is
not a single clean full-suite run. Final frozen-source shaping checks:244passed,
1optional renderer skip; native DOCX12passed separately. Inventory/manifest hashes
remained unchanged through the final serial runs. Final caption contrast7.58:1 is pixel-reviewed;
the final sanitized DOCX hash is recorded in the verification report. Hosted
checks, main merge, release and home
installation have not occurred. Freshly fetched GitHub/GitLab base trees match;
historical GitLab403 is resolved. Preserve worktree/evidence while gates remain.

## Historical in-progress checkpoint — superseded by the status above

Current implementation checkpoint (2026-09-18): five same-slug presentation/status
candidates are under presentation-candidates/; UAC apply/regeneration has NOT run.
Semantic reviewer Schrodinger closed four instruction conflicts; report retained
in engos-quality-presentation-instruction-review.md. Controller subsequently added
discovery wording and reader-composition guidance; final binding review still due.
Runtime author reported 137 then 154 passing tests; controller independently ran
154 passing. Reviewer Laplace 01a0b41c-374b-7350-9ab4-b99b30226651 confirmed five
initial repairs but found F6–F8 (visual-summary conflict, resurrected old activity,
unverifiable-scope completion message). Aristotle is fixing those in the same scope.
Renderer reviewer Averroes 01a0b41f-e4c5-79f2-a2bf-78c36540a747 found seven current
issues plus inherited source-read TOCTOU; Parfit is repairing them. No review pass
or merge readiness is claimed. Full suite/hosted checks remain unrun for this slice.

Controller observed a real static Mermaid render failing passive SVG validation on
the renderer's unused animation CSS; exact private diagnostic SVG retained. Added
and red/green tested an explicit native-table map for acceptance tables that must
not be forced into the interface schema. New teaching layout preserves the exact
previous source hash 976b809ae57aa5e3bdda2d58e3197bffdb4060b230f9e22323e49b2339e51308.
Actual framed DOCX was generated with the one-time document-operation marker,
sanitized and rendered using bundled LibreOffice; its one page was inspected.
This is local format evidence, not G1 or saved-target proof. Do not rerun that marker
in this turn. The new private teaching Doc request is awaiting the user's exact
approval; the previous test Doc is untouched. All private captures/fixtures stay
under the established task research root, outside this public repo.

Three progress-view scenarios were generated through the real runtime using
explicitly FAKE unit-fixture receipts: waiting at G2, framing-only completion, and
changed saved target retaining G3. They are marked simulated and prove no actual
semantic stage acceptance; human-view/render/role checks still remain.

Implementation of the presentation/progress slice is now authorized by the user's
latest "proceed". Source baseline bf6c44e. Both main refs fetched successfully;
base trees still match. Actual private Framed/Shaped PDFs were exported read-only
and all seven pages inspected before renderer edits; frozen acceptance is in
engos-quality-visual-baseline.md. Progress worker Aristotle
01a0b409-b745-7db2-a923-5a59b3243849 owns canonical gate runtime/resources/tests;
renderer worker Parfit 01a0b40c-7b76-7001-94a5-ea3e4037b7bf owns canonical embed
resources/export tests. Controller owns capability candidates, conductor/diagram
guidance, docs, UAC, integration and actual render checks. No new target write,
native registration, release or home installation is included implicitly.

Next scoped work is defined in
[the presentation/progress plan](engos-design-presentation-progress-plan.md), with
an independently reviewed initial proposal and preserved reviewer recommendations.
It covers reference-matched SVG/PNG/document presentation and a read-only flow
status projection over existing gate state. Clarifications address concrete review
findings; visual baseline capture, implementation and runtime/visual proof remain
pending. No new progress dashboard or polished renderer is claimed shipped.

Latest: the user assigned the controller as pilot judge and six separate subagents
as junior/mid/senior product/engineering participants. That simulated-role pilot
has now run; see [the role-pilot judgment](engos-quality-role-pilot.md). It is a
partial pass, with confirmed HTML readability, boundary-classification and test-spy
repair work. Real people are not a prerequisite to the user-requested simulation;
their usability/authority evidence remains a distinct untested claim. No real
accepted G0–G4 or two-surface new-pitch completion is inferred. The following
participant request is retained as historical context, superseded for this pilot
by the user's explicit role-play choice.

After the implementation checkpoint, the user approved the exact private upload.
The teaching-fixture Google Doc was created without sharing; saved readback and
independent nine-page pixel review passed. See
[the adapter receipt](engos-quality-google-doc-adapter-receipt.md).
Normal GitLab fetch now succeeds. Both freshly fetched main trees match, although
their commit IDs differ. No hosted branch checks or merge have run.

Remaining holds: named product/engineering pilot participants, attributable
appetite/walk-away decisions, complete real-input progression and same-bundle
two-surface proof, then required hosted checks and dual-remote landing. Approval
of the private teaching upload does not invent these human decisions or pass G4.

The sections below preserve the earlier implementation checkpoint and its then-open
holds. This continuation supersedes its upload-approval and GitLab-access blockers
only; its test counts and remaining semantic/pilot limitations are unchanged.

## Fixed acceptance and ownership (implementation checkpoint)

C01–C12 and P1–P10 in the reviewed plan remain the contract. Every row below needs
actual evidence, not only files or a self-grade. Public-safe fixtures only in repo;
private company documents/pilot artifacts remain in the existing private research root.

| Slice | Owner | Evidence needed | Status |
| --- | --- | --- | --- |
| Intake/framing/research/shaping procedures and context work orders | Prompt worker | Resource-complete instructions, same-slug UAC, independent review | pending |
| Atomic runtime/receipt/gate checks and recovery | Runtime worker | Focused pytest positive/negative cases, independent code review | pending |
| Artifact/export adapters and calibration | Controller | Fidelity checks, rendering, calibrated controls | pending |
| User onboarding/runbook and examples | Controller | Discoverable entry, cold-start worker trial, docs review | pending |
| Real user/engineering pilot | Named humans, controller facilitator | Attributable decisions and uncoached observations | awaiting participants |
| HTML + private Google Doc | Controller publisher, independent reviewer | Same bundle, saved readback, full rows/images and pixels | pending |
| Build, regression, independent checks | Controller/reviewers | Exact reviewed source/generated revision | pending |
| GitHub/GitLab checks, merge, parity, cleanup | Controller | Hosted CI and post-merge refs | GitLab access blocked |

## Observed implementation checks

- Prompt worker authored two new skill candidates and phase resources. Independent
  instruction review found workstream naming/ownership, standalone-scope leakage,
  and JSON-only pixel-check conflicts. Narrow fixes, including publisher dispatch,
  were rechecked with no residual instruction finding in that scope. Receipts live
  in engos-quality-implementation-instruction-review.md and its recheck.
- Runtime worker initially reported 86 focused tests on Python 3.14 and 84 plus
  two optional-dependency skips on Python 3.11. Controller's initial combined
  runtime/export/resource tests observed 140 passing. These did not waive review.
- Independent code review reproduced seven defects, including a policy pin masked
  by ordinary inputs. Four runtime regressions and three native DOCX regressions
  failed before repair. Repaired runtime policy checks and content/delivery drift;
  repaired exporter no-follow/exclusive publication, buffered verified images,
  bounded renderer process group and literal code preservation. Re-review pending.
- Corrected focused run: 107 passed, three optional DOCX tests skipped under system
  Python. Those same three native DOCX cases passed separately in the approved
  bundled document runtime. Do not count skips as passes. Both CI files now include
  these suites and install the optional document dependencies.
- An exploratory full-suite run overlapped initial generation and later source
  edits; it is not final release evidence. It reported 1297 passed, 13 failed and
  138 subtests. Failures were packaging's Unreleased-entry rule (five), sandboxed
  macOS WebKit tests (six), and stale skill-count assertions/docs (two). The six
  unchanged WebKit tests subsequently passed outside the restricted sandbox.
  Source version is prepared as v1.16.0 (not tagged/released/installed); README and
  catalog-count test reflect 32 skills. Serial final regression remains required.
- UAC single-candidate plan/judge/apply succeeded for all six candidates after
  public vendor-schema cache refresh. The attempted multi-source apply raised a
  resource-map error for multi-source-import before applying the collection; no
  core UAC bypass/fix was introduced. First framing apply wrote files but strict
  validation held on missing schema cache; refresh and repeat passed. Later code
  repairs require regeneration/rebinding before final verification.
- Local exporter diagnostic: three Mermaid PNGs and an eight-page sanitized DOCX
  from an explicitly synthetic teaching bundle. All pages inspected after layout
  repairs; native table rows 3/4/5/5 and three images confirmed. This is not real
  pitch/G4 completion. Exact private Google Doc upload was blocked before execution
  by automatic safety review pending payload/destination approval. User was asked;
  no alternate upload path or retry was used.
- A cold-start generated-package worker found the guided entry and returned a
  solution-free first response plus tailored human-research help. Two scripted
  unknown-answer follow-ups are bounded in engos-quality-pilot-acceptance.md.
  This is a simulated model preflight; real participants and decisions remain
  unanswered. Its inherited host instructions and an out-of-path Git metadata
  read are recorded limitations, not proven enforced context isolation.

Current external/human holds: normal GitLab access; exact private upload approval;
real product/engineering pilot participants and historical exercise appetite.
Do not merge, claim complete pilot acceptance, or clean unique work while held.

## Local checkpoint outcome

All six capability candidates have been applied through same-slug UAC into SSOT,
canonical resources and five generated provider packages. Count: 32 skills, zero
new named-agent configurations. The state helper and exporter are implemented;
no global installation, release, main merge or real-user acceptance is claimed.

Independent source review closed the original seven code findings and a subsequent
empty-target issue: frame/draft-only runs now work without publication targets,
while G4 still rejects empty/unrequested targets. Final source verdict and exact
hashes: engos-quality-implementation-code-final.md. Independent docs review closed
runbook packaging, evidence-link and resource-root command defects, comparing all
five generated runtime references: engos-quality-implementation-docs-final.md.

Actual verification:
- Serial full suite: 1319 passed, 3 optional DOCX skips, 138 subtests passed, exit 0.
- All three skipped native DOCX regressions passed separately in the approved
  bundled document runtime; both CI files install those dependencies and run them.
- Subsequent docs/archive corrections: 56 focused package/docs/resource tests passed.
- Strict surface validation: passed, 32 SSOT entries. Installer capsule and legacy
  catalog checks passed. Zero-token contract compile/check: 32, no blockers;
  contracts remain draft and no behavioral promotion is asserted.
- Static evaluator calibration: 14 controls present, no missing controls, zero
  model calls; semantic judges explicitly unqualified for formal promotion.
- CLI smoke completed with Gemini discovery exit-41 warning. Do not claim live
  invocation/discovery success for every provider.

Observed model preflight:
- Initial simulated run exposed over-batched delegated asks and incomplete
  preference assistance. Source guidance was repaired, then the same case rerun
  in a fresh worker with the same two scripted follow-ups.
- Independent rerun assessment found the visible conversational criteria met:
  relevant 3/2/0 request counts, illustrative trade-offs, preserved unknowns and a
  useful stop/handoff. It expressly withholds human usability, successful evidence
  return, actual resume/stage acceptance, enforced sandbox and complete protocol
  claims. See engos-quality-pilot-preflight-initial.json and rerun.json.
- The read-boundary rule was prospectively corrected to allow mandatory host
  identity metadata; the initial deviation remains recorded, not retroactively
  passed. Guidance and criteria changes prevent causal/statistical superiority claims.
- Worker-run before/after package manifests matched. After that run completed, the
  controller corrected the unused runtime guide's working-directory text and
  regenerated packages while the outcome assessor inspected the live tree. That
  explains its later package mismatch/transient missing-file observation. It is
  not evidence of in-run worker mutation, nor a full-package reproducibility pass.
- Some retained trace outputs cannot independently establish full resource ingestion.
  No further trial is silently added to the bounded preflight; address observation
  capture and host boundaries before broader P1–P10/real-user acceptance.

Merge/release gate remains closed: required real-input/human and saved Google Doc
proof is incomplete; the exact upload is approval-blocked, GitLab is access-blocked,
and no hosted PR/MR checks have run. Useful source work and evidence are retained
locally for resumption. Do not relabel this checkpoint as completion of the request.

## Requirement accounting at handoff

| Requirement | Implemented and observed | Still required |
| --- | --- | --- |
| C01 entry/input help | Guided entry discovered in two model preflights; source coverage rules/resources | Real uncoached participants and positive complete-evidence case |
| C02 product/engineering questions | Assistance ladder, question/uncertainty split, request-budget repair observed on known scenario | Human decisions, real disagreement/return flow |
| C03 research modes | AI/human/hybrid protocols, explicit code-scan boundaries, teammate/evidence cards | Actual returned engineering evidence and full research progression |
| C04 framing versus shaping | Stage predicates, no-fabrication guidance, model holds rather than invented solution | Real input through all stages |
| C05 scoped worker roles | Role/context work orders and actual independent reviewers; limitations disclosed | Effective host-boundary audit; no enforced-sandbox claim |
| C06 state/handoff/recovery | Atomic accepted snapshot, replay/reopen and regressions; candidate handoff observed | Uncoached real resume and full stage-worker handoffs |
| C07 formats/delivery | JSON/HTML/DOCX helper, actual Mermaid render and eight-page DOCX QA; full rows/images retained locally | Saved Google Doc approval/readback/pixels; real approved bundle on both targets |
| C08 validators | Positive/negative mechanics, reproduced defects repaired and independently rechecked | Live semantic gate evidence, not fake fixture receipts |
| C09 exemplar/rubric | Three-diagram/full-table policy, source-specific anchors and bounded comprehension controls | Complete real-pitch judgment and exemplar calibration |
| C10 iteration | Actual independent design/instruction/code/docs findings and repaired rechecks retained | No additional design-only acceptance substituted for live proof |
| C11 repo delivery | Same-slug UAC, source-first regeneration, strict checks, tests, packaged runbook | GitLab access, exact-head hosted PR/MR CI, merge/parity/cleanup |
| C12 pilot/goal boundary | Bounded model preflight with explicit protocol amendment and limitations | Human pilot; no runtime goal was created implicitly |

The full suite passed before the final documentation-only working-directory and
archive-membership corrections. Those corrections were followed by the 56 passing
focused package/docs/resource checks and strict regeneration/validation. Semantic
model proof remains bounded; do not convert the test counts into a readiness score.

## Implementation boundaries

Canonical skill bodies enter through UAC from task-owned candidates. Helpers live
under sources/capability-resources/<slug>; generated surfaces are never hand-edited.
Runtime is a small portable Python helper, not a new agent orchestration service.
It enforces mechanical consistency when used by the controller; host permissions
and actual worker provenance remain a separately observed trust boundary. Do not
claim OS isolation or authentication from a supplied identity string.

Runtime public interface target: init, status, prepare, seal, accept, reopen,
delivery-intent, delivery-record; exact arguments and schemas must be documented
and tested before skill prompts invoke them. Worker output directories are separate
from controller-owned accepted state. G0–G4 require current dependency bindings;
G3 independent review; G4 saved-target evidence. Code must distinguish success,
validation failure and unverifiable/error. Positive fixtures must advance and
negative mutations must fail without state mutation. Source/decision changes
invalidate affected later acceptance, preserving history.

Scope for current tests: first implementation acceptance, not statistical
superiority or formal behavioral promotion. Earlier examples remain training
material. Freeze concrete pilot inputs before trials; do not give expected answers
to trial workers. Human pilot cannot be replaced by simulated stakeholder approval.
User has been asked for actual participants and the historical replay appetite;
other authorized work continues while those decisions are pending.
