# Shaping review rubrics

Score meaning: 1 missing/contradictory; 2 incomplete or dependent on unverified
evidence; 3 adequate and supported for the selected scope; 4 strong with bounded
risks; 5 strong with relevant observed proof. Each score cites its weakest
material evidence. These are assessments, not probabilities or time estimates.

## Team dimensions

| Dimension | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Simplicity | Unnecessary mechanisms or competing responsibilities | Existing pattern with bounded additions | Smallest sufficient change demonstrated |
| Testability | No observable completion | Every workstream has a concrete check | Proposed proof path already exercised where needed |
| Security | Responsibility gap or unsupported assertion | Named owners, boundaries and mitigations | Relevant controls observed and failure paths checked |
| Architecture | Contradicts real boundaries | Follows cited patterns | Seams and lifecycle are supported by current evidence |
| Cost | Unknown/unbounded scaling | Explicit workload and bounded cost assumptions | Relevant costs measured or calculated from evidence |
| Feasibility | Speculation presented as fact | Material claims supported | Critical new seam has observed proof |
| Confidence | No evidence | Cited analogous behavior supports the bounded bet | Relevant end-to-end proof is observed |

## Pitch dimensions

| Dimension | Inspect |
| --- | --- |
| Problem clarity | Affected people, why-now, evidenced pain; not a chosen solution disguised as a problem |
| Appetite fit | Actual willingness to spend, walk-away, scope cut, no hidden work contradicting exclusions |
| Solution sharpness | Macro flow connects; room for builder judgment; real mitigations |
| Contract quality | Interfaces and ownership specific enough at seams; states and patterns cited; measurable constraints |
| Boundary discipline | Testable completion, reasoned no-gos, negative space, no orphan responsibility |

Report seven team scores and five pitch scores with rationale and evidence.
Show each mean and the overall mean across twelve dimensions. Numeric readiness
requires every required dimension >=3 and overall >=4, plus all hard gates pass.
Missing required content scores 1. An unverified material feasibility claim caps
Feasibility at 2. A disclosed proposal with verified precedent is a proposal,
not a false claim that the proposed implementation already works. An unresolved
critical seam still blocks. No average waives these rules.

Author audit precedes independent review. The independent reviewer did not write
the pitch and must recheck its references. If independence or source access is
unavailable, report the limitation and retain review_pending. Direct the three
hardest questions and the next iteration at the weakest supported dimension.

The team source allows some conflicting average/pass interpretations; this
adaptation resolves them conservatively: hard failures and score caps take
precedence. Upstream sources and exact mappings live in research-notes.md.
