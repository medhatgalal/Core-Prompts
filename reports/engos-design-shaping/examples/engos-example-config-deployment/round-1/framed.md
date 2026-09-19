# Configuration deployment — Framed

Teaching frame; source identity and verbatim brief: intake.md, `input.md:6-7`. G0 passed by author observation before this artifact.

**Problem and affected people.** The scenario customer re-enters cost settings after every deployment. People administering the target also need their local changes protected, and users of older packages need continuity (`input.md:6-13`).

**Why now.** Repeated manual re-entry after each deploy is the supplied reason, not measured incident or revenue evidence (`input.md:13`).

**Desired outcome / business win.** Currency and activity-cost definitions can accompany a process deployment without manual re-entry, unintended target overwrite, or old-package regression. Less repeated work is the intended benefit; no savings figure is claimed (`input.md:6-13`).

**Appetite and walk-away.** C1 accepts one week with two engineers in this hypothetical scenario. Stop if target override protection cannot be preserved (`input.md:9-12`). This is willingness to spend, not an estimate or live commitment.

**In.** Currency and activity-cost definitions, target-local preservation by default, old-package compatibility (`input.md:6-12`).

**Out.** Cost results, unrelated configuration, new permission roles, full data reload and historical recomputation (`input.md:10-12`, `input.md:28-29`). No live deployment or integration test in this teaching task (`input.md:35-36`).

**Hard constraints.** Only a target admin can choose explicit force overwrite (`input.md:11-12`). Existing deployment authorization and encrypted channel remain the boundary; no new transport or credentials (`input.md:32-33`). Scenario workload is 100 processes and at most 200 activities each (`input.md:30-31`). These are source constraints, not a selected design.

## Research questions

| ID | Question | Evidence needed |
| --- | --- | --- |
| C-Q1 | What existing behavior protects target-local changes and who may override it? | Revision/conflict and admin premises |
| C-Q2 | How are settings associated with a process, and what does old-package absence mean? | Identity, data separation and absent-section premises |
| C-Q3 | Can invalid included configuration leave all prior state intact? | Validation and transaction premise |
| C-Q4 | When can analysis see deployed settings without broad recomputation? | Analysis read timing and exclusions |
| C-Q5 | Does the supplied workload fit the existing stated configuration bound? | Workload arithmetic and capacity premise |
| C-Q6 | Who owns authorization and transport protection, and what does the analysis library not own? | Existing security responsibility premise |

No solution topology, endpoint, method or implementation sequence is selected in this frame.
