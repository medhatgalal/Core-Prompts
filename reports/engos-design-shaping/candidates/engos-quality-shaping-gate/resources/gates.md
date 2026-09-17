# Stage advancement contract

States are ordered 0 Intake, 1 Framed, 2 Research, 3 Shaped, 4 Bet-ready.
Each gate inspects its output before authorizing the next state. Start/resume
at the earliest stage without a current passing receipt. A content revision change
invalidates dependent receipts; reread affected evidence and record reconciliation.
Hash boundaries are explicit: G0 binds brief/intake; G1 binds those plus frame
and decision inputs; G2 binds frame, question/evidence log and decision inputs;
G3 binds an enumerated source-content manifest (approved pitch/summary,
workstreams/slices, constraints/no-gos, complete table data, Mermaid sources and
captions) plus its upstream content hashes. Local render observations are evidence
referencing those hashes. Gate receipts, journal entries and later placement
observations are separate files, not part of a recursive whole-folder digest.
Adding observations about unchanged content does not invalidate G3. Altering
approved content does. G4 binds the G3 content hash, betting-prep sidecar and each
saved target identity/revision with inventory and pixel evidence.

| Gate | Input | Output inspected | Conditions for pass | Failure result |
| --- | --- | --- | --- | --- |
| G0 | Raw input, supplied context | intake.md | Original source preserved; known/assumed/missing separated; supplied suggestions marked unselected; no assistant-authored solution | fail, remain Intake |
| G1 | Passing intake and actual decisions | framed.md | Problem/user/why-now/outcome; human appetite and walk-away; boundaries; question IDs; no selected solution or implementation detail | decision_pending or fail, remain Framed |
| G2 | Passing frame, inspected sources/spikes | research-notes.md and decisions.md | Each question answered with opened path:line or actual spike result, or excluded by a sourced scope decision; risks grounded with mitigation; no unresolved dependency in selected scope | needs_spike or fail, remain Research |
| G3 | Passing frame/evidence | Source-content manifest and local renders | All exemplar coverage checks below pass; every relevant dimension >=3; overall review >=4; separate G3-only independent review; no blocking question hidden in selected scope | fail or review_pending, remain Shaped |
| G4 | Passing shaped folder | Target pitch and receipts | Every requested surface has complete diagrams/tables and content; pixel inspection/readback at current revision; style; source identity; betting preparation | placement_pending or fail, not Bet-ready |

Question dispositions: `answered` requires evidence and an answer that resolves
the question; `needs_spike` requires owner/question/bound/success criterion and
is not an answer; `excluded` requires why, decision provenance and no dependency
from included work. A human must own irreducible willingness-to-spend/risk calls.
Only answered or validly excluded questions allow G2/G3 to pass. Naming the
spike fulfills triage, not advancement.

G3 exemplar checklist:

1. Holistic problem and solution, appetite fit and explicit exclusions.
2. Component diagram with seams and boundaries; sequence with actual/proposed
   interactions; data-flow with stores and transformations. Source is Mermaid
   unless an expressiveness limit is demonstrated and alternative source retained.
3. Every diagram rendered, visually inspected for readable labels/arrows/boundaries,
   and checked against evidence. Syntax success alone fails this condition.
4. API/contracts retain exemplar Method/Purpose or Method/Endpoint/Purpose shape,
   extended with provider, consumer, state and evidence as needed. Mark in-process,
   network and proposed contracts explicitly; retain complete parameter/response
   meaning without pretending new methods already exist.
5. Security matrix contains Responsibility, Owner and How enforced, with evidence
   and unresolved status. Negative space names what a component does not own and
   identifies where the responsibility actually resides. No fabricated owners.
6. Workstream rows marked ready/needs_spike/excluded; no required needs_spike item
   included in the bet. Pitch-wide and per-workstream slices have visible proof
   criteria. Detailed build tasks are left to the builder.
7. Real rabbit holes have mitigation, responsible role and stop boundary. No-go
   reasons and accepted risk decisions are traceable.
8. Original constraints survive in the source solution, contracts and slices;
   contradictions are resolved through a decision and downstream refresh.
9. Both scorecards complete; blockers override averages. Author audit and
   independent review are separate actual observations.

G3 does not require saved target placement, which occurs afterward. G4 requires
at least one explicitly requested target; zero targets is not a vacuous pass.
Draft-only scope terminates at shaped_draft. Betting preparation is authored
before G4 review, checked against G3 content, and retained locally as a sidecar
unless inclusion on the target was requested.

G4 comparison uses the authoritative source bundle: full text/row inventory,
three diagrams, captions, no-gos and unresolved status. A receipt pointing at a
planned target, expired image URL or upload response is not saved-document proof.
Native Mermaid support must be observed on the actual target, not assumed from
the product family. Stage 4 is readiness for human deliberation, not approval.
