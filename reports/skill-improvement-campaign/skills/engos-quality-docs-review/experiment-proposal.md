> Historical unexecuted narrow proposal from setup. Superseded as the whole-skill plan by full-capability-design.md and model-measurement-plan.md. H1 remains a drift sub-hypothesis; its 1.25M budget and Astra/high nomination were never approved or measured.

# Docs-review experiment proposal

This is an unexecuted proposal. No candidate skill has been authored or applied.
Public answers are development material and cannot become held-out evidence.

## Goal contract and candidate hypothesis

Target: `engos-quality-docs-review` at the commit and complete source/resource
inventory in `baseline-inventory.json`. Improve actionable defect recall without
increasing false findings, unsafe repairs, review time, or operator burden. The
incumbent remains the current shipped skill, not the older historical snapshot.

Joint hypothesis H1: a short evidence-to-repair check inside the existing Workflow
will improve discrimination between current documentation defects and intentional
historical/custom content. The current general requirements may already suffice;
a tie or loss retains the incumbent. There is no measured failure rate yet.

After contract review, propose one bounded SSOT change: expand Workflow step 3
with a checklist substantially equivalent to the following, preserving existing
authority, required output, audience advice, routing, and lifecycle triggers:

> For each suspected active-doc defect, record its path and line or section, the
> conflicting source/help or target heading, user impact, and the smallest viable
> repair. Check current command flags against source or safely obtained help;
> resolve relative links from their containing page and check fragments against
> actual headings. Identify generated pages and their source before recommending
> regeneration. Distinguish current instructions from explicit historical records
> and supported user customizations; do not modernize these merely for consistency.
> Place content according to repository audience and maintainer intent. Verify
> release claims against what the release scripts actually do. State unverified
> checks as limits, never as completed execution. Return no actionable findings
> when the evidence supports none.

This is a candidate direction, not frozen treatment bytes or a new common template.
Prefer an in-body checklist; do not create a helper/resource unless public trial
evidence shows that it adds value beyond this small change. No prose-grade target,
shared evaluator patch, steering edit, or generic restructuring belongs in H1.
Run same-slug UAC plan/judge/apply only after the contract and exact candidate
write set are reviewed through coordinator integration. Keep generated output,
aggregate metadata, docs and active eval artifacts under coordinator ownership.

## Three matched arms and binding

| Arm | Supplied treatment |
| --- | --- |
| A, bare | Strong model with exactly `task.txt`, the selected public fixture tree and its local policy; no docs-review skill or resource discovery |
| B, incumbent | Same task/tree/policy plus full current generated skill and every bundled resource, including capability.json |
| C, candidate | Same task/tree/policy plus full proposed generated skill and every bundled resource from the frozen candidate |

Proposed anchor is `gpt-6-astra`, high effort, one verified local host and identical
tools for all arms. This is a setting proposal, not a claim that the current task
uses that exact model or that an authenticated adapter is admitted. The coordinator
must record the actual immutable model/version, effort, CLI/adapter versions,
tool policy, OS/runtime, hook configuration, skill discovery and supplied bytes.
Record both requested and observed settings; unresolved material differences make
the comparison inconclusive. All context except the treatment must be matched.

Freeze request bytes, system/developer instructions that can be inspected, complete
skill/resource contents and consumption evidence, fixture commit/tree/hash inventory,
candidate SSOT/generated hashes, contract/topology, cases, scorer, judge rubric,
seeds/order and starting state before dispatch. No inherited author conversation,
saved review report, other-arm output, or answer access is permitted. Delivery
hashes alone do not show that the model received the resource bytes.

Allowed later tools: verified repository reads, search, and explicitly inspected
read-only CLI/help commands inside the fixture. Review output must be collected
outside the reviewed tree. Effective denies must cover target-skill autodiscovery
in A, out-of-scope files, MCPs, hooks, browser state, credentials and evaluator
answers for every arm. Demonstrate deny probes and allowed probes through the
actual execution path. Fresh tasks alone establish none of these boundaries.

The current shared runner schedules two arms and has hash-only scorer linkage
(coordinator finding). Do not emulate a third arm with a privileged ad-hoc harness.
Coordinator must admit a matched three-arm schedule, or a preregistered pair of
comparisons C:B and C:A with all baseline repeats budgeted and conditions matched.
Run manifests and public evidence must preserve each actual input and call identity.

## Dataset, coverage and scoring meaning

Public setup set: two matched repository trees, six defect/control dimensions
(CLI flag, relative path, fragment, generated drift, audience placement, release
guidance). The drift tree also contains correct commands/links, an immutable v1
record, and a supported custom theme. Its six defects have public path/line/source
evidence and viable repairs. The clean tree should produce zero actionable findings.
The two trees are one matched family, not twelve independent samples.

Use existing capability-eval contracts, topology, schemas and protected scoring
path after coordinator admission. `check_fixtures.py` checks fixture integrity
only; do not substitute its booleans for a semantic finding score. Public case
field conventions match the existing Code Review examples. No general Docs case
schema or semantic scorer has been admitted here.

Proposed primary metric is actionable recall at high precision:

- TP: one unique seeded defect correctly identified with exact path and line or
  section, corroborating evidence, and a viable scoped repair.
- FN: a seed missed, unsupported, or paired only with an invalid repair.
- FP: each distinct unsupported warning, needless rewrite, invented defect or
  unsafe/unscoped repair presented as actionable. Repeated reports of one seed
  cannot create multiple TPs; duplicate actionable items count as noise.
- Recall = TP / seeded defects; precision = TP / (TP + FP). Precision is N/A when
  no findings exist. For the clean case, report FP count and clean-case success,
  not invented perfect recall. Semantic novelty outside public labels requires
  independent adjudication; preserve disputes and do not silently expand labels.

Report per-category recall and FP counts before pooled results. A proposal that
changes the correct CLI source to match stale docs is an invalid repair. A
historical-only flag mention is not current drift. Generating a correct document
in a read-only review violates authority even if it fixes a seed.

Screening threshold, frozen before later public trials: C has mean actionable
recall at least 0.10 above B and A; precision at least 0.95 and no more than 0.02
below either; zero FP on matched clean cases; no category regresses; no hard veto.
No prose/heading score can substitute. If A=B=C saturate, retain B and declare no
demonstrated added value; design a harder subsequent dataset without changing
the completed comparison. These tiny public examples cannot support population
or formal promotion claims, even if the numeric screen passes.

Secondary outcomes: repair viability rate, truthful verification statements,
reviewer minutes to validate/repair output, raw token totals, end-to-end latency,
and avoidable report length. Proposed burden limits: no more than 20% latency/raw
token increase over B, and no more than two extra reviewer minutes per case. Record
the full prompts separately so treatment size is visible. These limits require
coordinator review before use; do not tune them after seeing outcomes.

Hard vetoes: any unauthorized tree or Git change, fabricated execution, sensitive
or answer access, undeclared tool/hook/browser authority, or evidence tampering.
Missing evidence for a boundary yields inconclusive, never a presumed pass. A
confirmed violation remains a recorded failure even if later collection fails.
Broad rewrites, generated-source inversions, and changing custom/history content
are protected regressions. No aggregate score compensates for them.

`contract-mapping.json` proposes public coverage for all 16 extracted IDs but
does not mark them reviewed or covered. Extraction misses substantive clauses.
Independent cases remain needed for missing inputs, explicit edit authority,
out-of-scope code escalation, ordinary sentence-editing routing, useful rich
formatting, and caller-specific review cadence. No author waivers are granted.
Topology review schema currently permits only Batman/BAT-PUB identities; coordinator
must resolve that shared gap without silently treating these mappings as admitted.

## Repetitions, order, statistics and stopping

After explicit admission, one success and one actually fired failure observation
must traverse the real model collection, normalization, verification, semantic
scoring and receipt path. This includes a fabricated-execution claim and an
unauthorized-write control reaching a hard veto, plus a correct no-findings result
reaching clean-case success. Verify scorer implementation use, not merely a hash.
These calls consume the approved budget; current static controls do not meet this
preflight requirement.

Public development screen: both cases × three arms × three repetitions = 18 model
outputs for one frozen candidate. Use the preregistered order A/B/C, B/C/A, C/A/B
over the three repetitions for each case, alternating case order between repeats.
Fix three seeds if the admitted backend supports them; otherwise record that no
seed is supported and retain repeated observations. Start each output from the
same frozen state, not the prior result. Never stop because the first result wins.
At most one additional distinct candidate hypothesis may be proposed after an
unsuccessful complete screen; it needs a new frozen candidate and separate declared
comparison. Stop new trials at the budget/deadline, material boundary failure,
user stop, verified target, or two complete unsuccessful hypotheses. Partial grids
remain inconclusive; keep failures and actual charged usage.

Independent validation is a separate owner and dataset, not these public answers.
Propose at least 20 independently authored repository families with balanced
positive/control cases across the six dimensions, varied nesting/tooling and
historical/customization conventions. This is a proposed coverage floor, not an
assertion of adequate power. Before dispatch that owner must choose sample size
from a power analysis for a 0.10 paired recall difference and precision margin,
accounting for within-repo dependence and observed pilot discordance. Use paired
family-level analysis and 95% intervals, Holm correction for C:B and C:A, and
report inconclusive if the preregistered precision/recall margins are unresolved.
Repetitions of one repository do not count as independent families. Judges must
qualify on separate gold data and stay independent of candidate authors; no hidden
answers are requested or authored in this setup.

## Effort, budget and admission

Setup is one ordinary subscription-backed development turn, 45 minutes from
23:31:18 UTC on 2026-09-09, ending 00:16:18 UTC on 2026-09-10. Stop new setup work
at that deadline, preserve owned progress and disclose incomplete checks/overrun.
See assessment.md for actual closure. No experimental model calls, API charges,
credits/resets, cloud migration, releases or installs are authorized.

Later proposal: 1,250,000 raw tokens across every phase; maximum three wall-clock
hours starting with the first admitted preflight dispatch, including waits,
review, judging, incomplete calls, reproduction and verification. Suggested
reservation: 150k preflight/qualification, 500k public paired production, 250k
judging/adjudication, 200k reproduction, 150k remaining contingency. It is an
estimate, not a guaranteed complete grid; obtain admission before spending. A
second screen requires releasing/reallocating unused reservations while staying
within the original envelope. Cap exhaustion is inconclusive.

The candidate changes material behavior, so the minimum formal evaluation profile
is `promotion` with a 5M hard cap. A 1.25M spend proposal is not authority to relabel
this as `canary` or omit required cells. Coordinator must reconcile the reservation,
profile, full design and power; the formal study may need a separately authorized
plan. A public development screen is not formal behavioral promotion.

Estimated operator effort after prerequisites exist: 20 minutes to inspect/freeze
inputs and boundaries, 30 minutes for preflight and sign-off, 30–45 minutes to
adjudicate development outputs, and 15 minutes to review the closeout. Adapter or
trust foundation engineering is excluded from this estimate and remains separately
owned; do not absorb it silently into this skill budget.

Named admission gaps: reviewed Goal Contract and topology (including omitted
clauses and waivers); frozen exact candidate; public case/schema integration;
qualified semantic scoring wired to collection; authenticated conforming adapter
with effective boundaries; independently owned validation data and judgments;
three-arm schedule and actual model/settings; preexisting approved trust policy
and purpose-separated evidence where formal promotion requires them; profile,
budget, power and complete-grid approval. Codex/Kiro registered authenticated
adapters are unavailable/promotion-ineligible; their repair belongs to coordinator.

## Decision and follow-up

Retain incumbent. The setup outcome is `setup_required`; behavioral outcome is
`inconclusive` because no comparison ran. Preserve public positive and negative
examples as development assets. Later observed failures should be distilled only
within their disclosure boundary. Shared admission findings belong in coordinator
integration; no standing rule or source rewrite is justified by this setup alone.
