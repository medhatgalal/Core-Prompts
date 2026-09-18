# Independent review dispatch

Resolve and read `engos-quality-shaping-gate` SKILL, applicable gate/receipt
resources and its calibrated rubric; read `engos-audit-pitch-review` SKILL and
the bound full-shaping integration. The gate is the sole owner of predicates,
scores and thresholds. Do not duplicate its scorecard, inherit a historic trial
rubric, average conflicting judgments into a pass or let the legacy combined
readiness label substitute for separate G3/G4. Missing integration/calibration
holds dependent review; it does not block an explicitly unaccepted author draft.

Minimum reviewer conditions: did not author the candidate; initial work order
omits author self-grades/preferred verdict and unrelated parent chat; actual
effective context and resource identities recorded; relevant source inspection
available; result attributable to a host-bound worker or designated independent
human. Shared-model bias remains a limitation. Contamination requires a fresh
independent assessment, not disclosure followed by a pass. If these conditions
cannot be met, retain `review_pending` or use an authorized independent human.

Use `dispatch.md`; append this prompt with no author score or suggested verdict:

> Act only as the independent reviewer of the specified stage and revision.
> Read the original requirements, accepted predecessors, candidate inventory,
> selected gate policy and relevant sources. Inspect meaning, not just headings:
> framing purity, decision provenance, evidence sufficiency, cross-artifact contract
> and security coverage, and actual render/readback where required. Assess every
> mandatory predicate as pass, fail or unverifiable with evidence and explanation
> using the gate's receipt schema; report its scorecards when applicable. Return
> findings, blockers, weakest supported dimension, concrete repairs and next
> permitted state. Do not repair the candidate, accept state, invent observations
> or infer a verdict from the author. G3 assesses source content and local renders;
> G4 separately assesses all requested saved targets and betting-prep fidelity.

The conductor binds reviewer identity and reviewed hashes to actual dispatch/return
evidence, validates freshness and completeness using the runtime, and checks semantic
findings. Malformed, missing, stale or unverifiable mandatory assessments hold.
Schema validity is not truth. Preserve failed receipts and dissent; repair the
specific gap and re-review affected inputs. A policy change gets a new version and
appropriate calibration, never retroactive rescore of earlier judgments.
