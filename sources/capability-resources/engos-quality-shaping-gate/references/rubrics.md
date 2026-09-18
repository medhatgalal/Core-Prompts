# Shaping rubric — source-specific calibration v3

This policy retains dimension-specific anchors from the team's pinned
quality-score and pitch-review references and evaluates Architecture by justified
repository fit. Historical v1/v2 scores and pinned policies are not retroactively
changed. A proposed interface is judged as a proposal supported by
precedent; claiming it already works needs actual current evidence.

| Team dimension | 1: fail | 3: adequate | 5: strong |
| --- | --- | --- | --- |
| Simplicity | Unnecessary patterns/parts | Existing pattern, bounded additions | Smallest sufficient change, one new thing |
| Testability | No concrete verification | Every workstream verifiable, manual steps allowed | Every piece has explicit automated verification |
| Security | New surface unaddressed | Risks acknowledged and mitigated | No new surface, or explicitly gated with named responsibility |
| Architecture | Ignores relevant patterns or violates trust/contract constraints without a justified disposition | Cited repository evidence supports the material dispositions and relevant boundary/contract fit | Opened sources support each material disposition and its trade-offs against credible alternatives; relevant trust/contract constraints and applicable lifecycle implications are explicit |
| Cost | Unknown scaling | Workload and cost bounded by design | Explicit calls/cost/frequency calculation from supported inputs |
| Feasibility | Unsupported behavior claims | Material claims supported by relevant references | Every material behavior claim backed by working-code evidence |
| Confidence | Unsupported "should work" | Cited analogous pattern supports the bet | Relevant spike/MVP already demonstrates it |

Scores 2 and 4 represent evidence between adjacent anchors; explain the specific
basis, not a generic rule that every 5 needs a completed implementation. Score
the weakest material evidence per dimension. Unknown load-bearing feasibility
caps Feasibility at 2. Missing required content scores 1. No dimension below 3
passes; all hard gates must pass regardless of averages.

Architecture judges the fit and justification of configuration, reuse, extension,
evolution, replacement, new capability or intentional separation. Exact conformity
to an old pattern is neither required for a 5 nor sufficient by itself. Do not
penalize a justified evolution or new design merely for departing from that pattern;
unsupported departures and unresolved material compatibility still hold. Compare
credible alternatives only, and assess migration, owner, rollback and retirement
implications when applicable. Do not reward forced reuse or DRY consolidation.
For a request with no material technical scope, assess the explicit scoped reason
and its supporting evidence; do not invent a technical requirement to score it.
All twelve dimensions and existing quality thresholds remain required.

Also score five pitch dimensions 1–5: Problem clarity (who/why-now/evidenced pain),
Appetite fit (actual bet and scope/cuts), Solution sharpness (connected fat-marker
flows and mitigations), Contract quality (specific seams/states/meaning/material
constraints), Boundary discipline (observable completion and reasoned negative space).
For these, 1 is missing/contradictory, 3 adequate, 5 exceptionally clear and fully
supported at shaping depth. Leave builder-level implementation freedom intact.

Report all twelve scores, each rationale/evidence, both category means and the
equal-weight mean of all twelve scores (category means are reporting only, as in
the existing runtime). Ready requires every score >=3 and overall >=4, plus
all hard gates. Below 3 overall is not ready; 3–3.9 needs specific fixes and re-review,
not an implicit waiver. Ask three focused questions targeting the weakest dimensions.
Avoid a scoring loop that only paraphrases the same evidence to reach a threshold.

Calibration controls before first pilot: a supported one-field additive proposal
can be strong in Simplicity/Security without claiming a finished integration;
a missing critical compatibility result must still hold at G2/G3; a polished pitch
missing its security matrix fails regardless of score. An independent assessor
must apply these distinctions and compare against actual team exemplars. A
calibration pass is a rubric-comprehension check, not proof of team usability.
