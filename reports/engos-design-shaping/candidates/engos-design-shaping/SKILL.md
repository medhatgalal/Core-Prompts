---
name: engos-design-shaping
description: Take a rough problem through Intake, solution-free Framed, evidence-led Research, Shaped, and Bet-ready gates. Use for end-to-end Shape Up shaping or resuming a shaping folder; use pitch review alone for an existing finished pitch. Failed gates retain the current stage.
display_name: Shape Up Shaping Conductor
kind: workflow
capability_type: skill
---
# Shape Up Shaping Conductor

## Purpose

Own the complete path from a vague input to a pitch people can assess at the
betting table. Adapt the upstream shaper's research, drafting, audit and human
review responsibilities into five explicit stages. Load a stage's instructions,
read its inputs, write its artifact and obtain a gate verdict before advancing.
The invoking host retains tool permissions and worker dispatch authority.

## Primary Objective

Produce a bounded, evidence-backed pitch, correctly placed on its requested
surface, through an inspectable chain of passing gates. A useful blocked result
identifies the last passing stage, exact missing evidence or decision, owner and
next action. It never receives a later readiness label to make the run look done.

## Required Inputs

- Original rough input and any existing human constraints or decisions.
- Relevant repository/document access, verified identities and revisions.
- Target surface and authorized account/destination, or explicit draft-only scope.
- Human appetite and walk-away criteria; ask for missing intent while researching
  independently answerable facts needed to frame the problem.
- Task-specific output and knowledge roots. Resolve existing project homes first;
  the default output is `planning/<task-slug>/`. Do not assume a Kiro home path.

## Invocation Hints

Start this process when asked to shape a rough idea, turn framing into a pitch,
prepare a bet, or resume an incomplete shaping session. A diagram request alone
uses the artifact helper. A finished pitch review uses engos-audit-pitch-review.
The caller need not choose each phase skill manually.

## Composition

Resolve these packages from the host's installed skill registry or a supplied
candidate map. Read complete required files before using them. A missing package
blocks its phase; never silently substitute memory of its instructions.

| Phase | Owner |
| --- | --- |
| Intake and Framed | engos-design-frame-from-vague |
| Advancement verdicts | engos-quality-shaping-gate and its gates/rubrics resources |
| Research and synthesis | This conductor's research contract below |
| Diagram and contract production | engos-delivery-diagram-contract-artifacts |
| Target style and placement | engos-delivery-artifact-embed and its surface resource |
| Independent pitch review | engos-audit-pitch-review using the shaping gate |

For this design exercise, load `candidate-map.json` from the design packet root
and use exactly its candidate files, resource files and review overlay. The
overlay takes precedence over the base pitch review only for full-shaping gate
assessment. Never silently run the unchanged installed reviewer instead.

The conductor is a process owner, not a new provider permission model. An optional
agent adapter loads this same skill; it must not duplicate or weaken its gates.

## Workflow

### Preflight

Read prior task state and preserve original intent verbatim in `brief.md`.
Resolve sources using repository identity (`git rev-parse` supports clones and
linked worktrees), not a guessed `.git` directory test. Record source revisions,
local/remote/cache access and stale knowledge. Select one writer for the output
folder. Resolve current surface capabilities early without placing a final pitch.
Record a bounded shaping-session budget separately from the implementation
appetite. On budget exhaustion retain stage state, gaps and next action.

### 0 Intake

Run the framing skill's intake mode. `intake.md` separates known statements,
assumptions and missing facts. Suggested mechanisms in the original input stay
in a quoted raw-input section, clearly unendorsed. Pass G0 before producing the
Framed artifact. This gate forbids the assistant from adding a solution.

### 1 Framed

Run the framing skill's frame mode. Initialize `decisions.md` with decision
provenance and pending choices. Write `framed.md`: affected users, problem,
why-now, desired outcome, appetite as willingness to spend, walk-away condition,
boundaries and numbered open questions. Include no selected solution, topology,
API design or implementation steps. Pass G1 before entering solution research.
Necessary human decisions cannot be converted into assumptions just to advance.

### 2 Research or spike

For each frame question, trace current behavior and relevant existing patterns.
Open cited files at the recorded revision. Separate source-backed facts, observed
runtime results, proposals, assumptions and unknowns. Intent comes from the
human brief; code establishes feasibility. When they conflict, expose both.

Append research decisions, accepted risks and scope exclusions to `decisions.md`
as they occur. Write `research-notes.md` with question ID, answer/disposition, path:line or
observed command/result, scope, uncertainty and risk mitigation. Every risk must
cite what was observed. A named spike records question, responsible role, bounded
effort, success/failure criterion and expected decision; it is not a result.

An unresolved question may be assigned a named spike, giving `needs_spike`, but
G2 does not authorize Stage 3 until it has a result or a human-authorized exclusion
removes the dependency from the bet. If an exclusion changes the frame, revise
`framed.md` and rerun G1. Never invent spike execution. This task produces only
contracts/interfaces; any implementation spike needs separately scoped authority.

### 3 Shaped

Use only passing frame/research inputs. Write a coherent solution that explains
what happens, why it fits, rejected alternatives, responsibilities and negative
space. Plan the pitch-wide proof slice first, then coarse workstreams with one
observable first slice each. Scopes remain provisional until builders discover
the detailed work; no upfront production ticket breakdown.

Write `pitch.md`, `pitch-summary.md`, `epic-breakdown.md`, `traceability.md`,
the existing `decisions.md`, `journal.md`, and `pitch-report.json`. Supply API/contracts and
security ownership, plus Mermaid component, sequence and data-flow source via
the artifact skill. Preserve source identity across representations. Render and
inspect pixels, not just parser success. Each contract states whether it exists,
is proposed, is broken or remains unknown; a proposal must cite the precedent it
adapts without pretending to exist today.

Mark work `ready`, `needs_spike` or `excluded`. `needs_spike` that blocks the
selected solution prevents G3 passing; excluded work has an explicit reason and
decision reference. Mitigations bound risks without claiming to have eliminated
them. Carry load-bearing no-gos into both the pitch and slices.

Run author audit, then a G3-only independent review on the source-content hashes
and both rubrics, using the bound review overlay. G3 checks local renders and
source content; it does not require completed target placement. The author cannot
self-certify independent review. Fix the weakest
failing dimension, record actual before/after judgments and rerun affected gates.
Missing reviewers result in `review_pending`, never a simulated approval.

### 4 Bet-ready

Draft-only requests end at `shaped_draft` after G3; they do not claim Bet-ready.
An empty target list blocks G4. A local HTML preview is a concrete target if
requested and visually verified, but not a substitute for a requested Google Doc.

Only after G3 passes, prepare `betting-table-prep.md` from the approved pitch:
one-minute pitch, key trade-off, appetite, review checklist, three evidence-backed
hard questions, and handoff. Retain it as a local sidecar unless requested on the
target too. Check its fidelity to G3 content; any new substantive claim reopens G3.
Then place the complete pitch using the embed adapter. Verify
the actual saved target's current content, every diagram, every table row and
the house style. Pass G4 for every requested target. An HTML preview and an
unexecuted Google Doc plan do not count as two placements.

Report `bet_ready`
only with G0–G4 passing on current hashes. Human `ok` accepts artifacts; it does
not allocate a team or approve production work. Record any actual betting
decision separately. Support `redo`, `deepen`, `reconcile`, and `handoff`.

## Required Output

The folder contains brief, intake, frame, question/evidence log, decisions,
shaped pitch and summary, epics/proof slices, source diagrams, contract/security
tables, render evidence, placement receipts, review/fix record, traceability,
journal, report and betting preparation. Unreached stages are explicitly absent.
`gates.json` lists stage, input/output hashes, verdict, findings, reviewer identity,
evidence and next permitted stage. It is a receipt, not permission to skip inspection.

## Rules

- Advance only on a fresh passing verdict. Changed upstream content invalidates
  downstream verdicts and triggers reconciliation.
- Informative progress can be presented while blocked, labeled with its actual
  stage. A failed gate cannot be waived by a high average score.
- Preserve human decisions with provenance; proposed defaults remain proposals.
- Route research facts to the project's knowledge system with revision and
  freshness, and task decisions to the task folder. Do not create another tracker.
- Never invent a component, owner, risk, method, runtime test or human answer.

## Constraints

One pitch per run. No production code, Jira tickets, release, installation or
automatic betting. External placement uses the requested account and scope.
Provider-native agent packaging is a separately reviewed adapter; the process
and artifacts stay portable. A bounded session ends with its true stage state.

## Examples

Input: “Our reports go stale when source data changes.” Intake identifies the
freshness problem and missing budget; Framed states the goal without selecting
polling or streaming. Research checks actual update contracts. Shaped names a
supported solution and its boundaries. Bet-ready follows verified placement.

Failure: a Framed draft says “poll the transaction API every ten seconds.” G1
rejects that selected mechanism and keeps the run at Framed. Removing the leak
does not waive missing appetite or evidence at later gates.

## Evaluation Rubric

| Check | Pass |
| --- | --- |
| Stage fidelity | Five distinct inputs/outputs with enforced advancement verdicts |
| Intent preservation | No fabricated decisions or solution leaking into framing |
| Evidence | Every question disposition and risk is traceable; spikes are honestly classified |
| Shaped coverage | Complete exemplar mapping, inspected diagrams, contracts and security ownership |
| Review | Separate author audit and independent verdict; failures beat averages |
| Surface fidelity | Actual target readback and visual checks preserve all meaning |
| Completion | Bet-ready is distinct from human betting, implementation and shipping |
