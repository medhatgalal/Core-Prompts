# Research dispatch

Use the common work order and prompt in `dispatch.md`; append this instruction:

Read architecture-fit.md for bounded existing-capability investigation and
conditional specialist routing. Extend these same research notes/evidence IDs;
do not create a parallel inventory or select a solution before framing passes.

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

Under the current policy, research-coverage.json records each opened run-relative
source path, its actual SHA256 and the source locators inspected. These are hashed
inputs or accepted source artifacts, not plausible filenames in a narrative.
Keep the source bytes available for the runtime and independent review. A note
that disagrees with opened code fails; repair Research rather than paraphrasing
the claim in a pitch. Load-bearing claims added during shaping reopen G2 first.
New facts may come from newly inspected source ranges or an observed spike result;
renaming a recap or adding coordination files is not evidence acquisition.

## Author preflight before returning Research

Apply these checks under the existing evidence-sufficiency predicate; do not add
a second scorecard. The author repairs its note; the conductor returns findings
without editing candidate prose. Independent review still checks the actual source.

- Compare each material summary claim with its quoted rows and inspected evidence.
  An unexplained contradiction fails sufficiency. Repair the statement or document
  the actual source conflict; a material unresolved conflict remains open.
- Bound exclusivity to the inspected ranges. A claim such as "only in these
  ranges" must include every relevant occurrence there, including test calls.
  Distinguish executable calls, examples and comments rather than treating text
  matches as semantic proof. One example of this pattern is listing production
  calls while omitting test calls visible in the same opened ranges.
- When the citation list changes, revisit dependent wording. Use explicit evidence
  IDs or restate the intended subset where "those" or "the opened ones" becomes
  ambiguous. One example of this pattern is extending a list but leaving its
  following sentence referring to the earlier subset.
- A call-site citation does not cover the callee body. If a material claim depends
  on that implementation, open it in Research or obtain sufficient attributable
  evidence through the human-led route; otherwise retain the research gap. Do not
  scan an entire call graph without an assigned need. One example of this pattern
  is treating a callee result as known or unknown from a caller citation alone.

Return the checked note, changed evidence IDs/coverage and actual artifact hashes
through the assigned worker handoff. These checks require semantic inspection;
neither a completed checklist nor coverage metadata establishes source truth.
