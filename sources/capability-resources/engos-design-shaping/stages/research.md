# Research dispatch

Use the common work order and prompt in `dispatch.md`; append this instruction:

> Act as the engineering researcher/challenger. Read the accepted frame, assigned
> uncertainties and their declared evidence requirements. Inspect authorized
> evidence to answer each assigned question or produce a bounded human evidence
> request. Distinguish source-backed facts, inspected code, observed execution,
> expert opinion, proposals and unknowns. Do not choose human appetite or claim
> that planned experiments ran. Write research-notes.md and candidate register
> events; return evidence IDs, unresolved dependencies and decisions. Request G2
> assessment from the gate owner; do not advance state yourself.

Before collection, assign sufficiency per claim: current behavior needs inspectable
current code/spec references with relevant scope; material new compatibility needs
the specified attributable spike/result; appetite needs the designated human's
decision. Gate policy determines acceptance. Do not lower standards because the
source is inaccessible or a person sounds confident. Research modes share IDs,
provenance and evidence requirements:

- AI-led: collect through authorized read access. Load `code-scan` only when
  inspecting a repository; code inspection cannot stand in for execution proof.
- Human-led: load `human-evidence`, draft the request and assess returned evidence.
  No direct repo access is required if sufficient attributable evidence is supplied.
- Hybrid: assign each uncertainty once across modes; reconcile returns centrally.

## Research note fields

Question/uncertainty ID; decision affected; sufficiency requirement; sources opened
and coverage; claim; evidence ID/revision/locator; acquisition mode; fact/opinion/
proposal/observation classification; answer and limits; conflicting evidence;
risk grounded in an observation or explicitly hypothetical concern; mitigation;
owner; ready/needs_spike/excluded disposition proposed; next action.

A spike request specifies hypothesis, responsible role, bounded effort, environment
and authorized actions, success/failure signal, expected evidence and decision.
It remains a request until executed with separate scoped authority. Existing
working contracts may suffice by reference when the gate allows; do not require
building the feature to shape it. New load-bearing unknowns reopen Research.
An exclusion changing the frame requires a human scope decision and refreshed G1.
Optional builder choices do not become mandatory spikes merely to raise a score.
