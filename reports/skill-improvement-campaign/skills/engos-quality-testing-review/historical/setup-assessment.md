> HISTORICAL, unexecuted unit-only setup proposal. Superseded as the whole-capability plan by the current ../assessment.md. Preserved from commit e534396; relative artifact links adjusted for this archive location. No experimental results have been changed.

# Testing Review campaign assessment

Status: **setup_required; incumbent retained; no experimental model dispatch**.
This file is the single local status and experiment proposal. The adjacent JSON
files are fixed evidence, not overlapping task trackers. The setup deliverable is
public fixture development and source inspection, not a skill improvement result.

## Identity, authority, and timing

| Field | Verified value |
| --- | --- |
| Task | `01a08882-d047-7e80-bea7-f7ebf956d191` (`CODEX_THREAD_ID`) |
| Coordinator task | `01a08880-cb62-7703-8061-659a0cf7ae45` |
| Assigned cwd | `/Users/medhat.galal/.codex/worktrees/611a/Core-Prompts` |
| Branch | `AI/campaign-testing-review`, created here from clean detached launch HEAD |
| Launch, fetched origin/main, fetched gitlab/main | `9d481a2da04e672e3b52d79bba6cf466af597fa0`; no launch drift |
| Runtime | Codex desktop task, zsh, Python `3.14.7`; exact resolved setup model version not attested |
| Start | `2026-09-09 23:31:27 UTC` (first recorded clock; includes inspection onward) |
| Deadline | `2026-09-10 00:16:27 UTC`, 45 minutes including checks, coordination, commit and final verification |
| Stop action | Stop new work at deadline, preserve existing owned artifacts and disclose incomplete checks/overrun |
| Scope | One setup turn; subscription-backed development; zero experimental model calls |

The primary checkout was read only. Git's linked-worktree metadata required an
approved sandbox escalation for the requested fetch/branch operations. No other
task's branch was merged or reverted. No release, install, paid API, reset, cloud
migration, producer/judge delegation, or protected-answer access occurred.
The final verification and closeout time are recorded below before commit.

## Target summary and baseline

Target: preserve the skill's four testing modes and improve the usefulness of
generated tests, measured by executed defect detection with low false failures.
Do not broaden the skill into a test runner or release gate. The producer continues
to design/generate tests and report them as **unrun**; an admitted separate evaluator
executes its emitted test artifact afterward.

[`baseline-inventory.json`](../baseline-inventory.json) binds 16 files at the launch
commit: canonical SSOT, descriptor/source assessment, historical baseline snapshot,
contract/topology, and all five generated skill entries with their resource files.
The source resource directory `sources/capability-resources/engos-quality-testing-review/`
does not exist; each generated surface currently has only `resources/capability.json`.
That absence is recorded, not treated as a missing required runtime resource.

- Current SSOT: 5,017 bytes; SHA256
  `13fe64494de3a09d60ddaad9f6c8824e42b59ff90c456a6a4e0c46018223e71b`.
- Inventory digest over sorted canonical JSON file entries:
  `b5e91efe6322fcb38d2c9ae93aa792aa8b61dc144764328fcdff910fa066fcee`.
- Original campaign baseline and current incumbent both equal launch HEAD. No
  accepted candidate exists in this setup. The old source-library fidelity oracle
  is a different identity, not the current comparison baseline.

Historical lineage was inspected with `git log --follow` and commit diffs:
`70368e4f8676921284c4f948f2bf7f31cf33cd7e` introduced the 86-line `testing` family;
`0e753f9293a9b2983f77e449df6d53dedc649d63` added placement guidance;
`0a2c1e46ff9ff65e1ba360e51a98371633cf0bf5` expanded the contract/workflow/rubric to
127 lines and is the descriptor's historical baseline; namespacing landed at
`6fbcff2d4a1c3fab4059715c02715d68de00d2cb`. Historical byte hashes are in the inventory.
The September 7 [help audit](../../../../preserved-fixes-2026-09-07/help-audit.md)
explicitly retained Testing's existing help/mode structure instead of importing a
uniform help template. The source assessment records a four-mode imported seed
and benchmark inspiration. These are prior structural improvements and reviews,
not an accepted modern three-arm behavioral comparison. The bounded search of
current target metadata, history, and report references found no such accepted
comparison; it was not a search of every archived conversation.

## Confirmed findings versus hypotheses

| Finding | Evidence and implication | Owner/disposition |
| --- | --- | --- |
| Contract admission is incomplete | Current `GoalContract.v1` and `CapabilityTopology.v1` are draft, runtime cells unresolved, and 0/9 extracted normative clauses mapped or waived. Compile passes without drift; that is structural evidence only. | Coordinator: reviewed contract/topology and complete normative review before calls. |
| Source and bundled descriptor disagree on default report paths | SSOT Output Directory uses `reports/testing/<timestamp>-…`; descriptor `consumption_hints.artifact_conventions` uses `reports/engos-quality-testing-review/<timestamp>-…`, propagated into bundled `capability.json`. | Coordinator metadata repair proposal; keep canonical source placement unless deliberately changed. Do not mix this repair into the behavioral treatment. |
| The current source does not explicitly require specification-derived oracles, unchanged state after rejection, or resource recovery sequences | Confirmed omissions in Rules/Workflow, while general failure/boundary guidance already exists. | Hypothesis H1 below. Omission alone is not an observed generation failure. |
| Public controls expose weak test coverage | Existing one-test suites miss all nine authored mutants; richer public example suites detect them and pass safe alternatives. | Fixture integrity evidence only; not a score for the incumbent or bare model. |

No source-level evidence establishes that the incumbent fabricates execution,
produces false failures, or misses lifecycle defects in practice. Those remain
behavioral questions. No prose score or test-count metric motivates this proposal.

## Goal contract and exact candidate hypothesis

H1: a small addition to existing Rules, directing tests toward specified observable
outcomes, state-preserving rejection, and deterministic failure recovery, improves
meaningful mutant detection over both the incumbent and a strong bare model without
false failures, extra authority, or brittle implementation coupling.

After coordinator contract review, the proposed candidate is exactly the current
SSOT plus these three bullets immediately after the existing rule “Include failure
cases and boundary cases, not only happy path.” No other behavioral edits or new
resource are proposed for this comparison:

```text
- Derive expected outcomes from the stated behavior or an explicit assumption, not from the implementation under test. Assert observable results; avoid duplicating its algorithm or depending on private representation.
- For stateful behavior, cover a successful transition, a rejected transition that leaves state unchanged, and the next valid operation. For resource-owning behavior, cover cleanup and recovery after failure where the contract requires them.
- Use controllable inputs or dependency fakes for time and failures. For each high-risk case, identify the defect its assertions would expose and a valid behavior they must allow. Report generated tests as unrun and give a reproducible execution handoff; do not execute them automatically.
```

This is a proposal, not an applied candidate or authorization to dispatch. Existing
source structure, all four modes, output headings, framework choices, integration
guidance, and GitOps handoff stay intact. No common template or generic checklist
resource is being imposed. Later write set: only owned SSOT; resources only if a
separately reviewed hypothesis needs them. Coordinator owns same-slug UAC plan,
judge/apply integration, descriptor consistency, generated surfaces, docs and
paired-provider delivery. Baseline retention is the rollback; do not reset any
unrelated work.

## Clause/case mapping and unresolved waivers

All mappings below are **proposed**, not an approved overlay. Stable hashes/IDs are
available in `baseline-contract-check.json`. Compiler extraction is not exhaustive:
the workflow steps, mode outputs, and handoff text also require manual review.

| Current clause hash prefix / source area | Public evidence or proposed observation | Remaining gap |
| --- | --- | --- |
| `a13a67440b6c` forbidden operations; `efc7137353f0` automatic execution | Both TASK files require unrun reporting; evaluator compares producer trace and report, verifies no execution, install, production edits or unsupported metric claim. | Actual runtime observation path and protected trace collection not admitted. |
| `77357dbdaba3` required inputs | Both cases supply source, behavior specification, existing tests, stack and risk context. | Missing-stack/input variant and explicit assumption handling case needed. |
| `3d4b9f171064`, `c34906b1f1c3` required output | Both task reports assessed for Scope, Assumptions, Tests/Gaps, Risk, Framework Notes, Follow-up. | Public fixture self-check does not assess model reports. |
| `4fdce19e68b0` failure/boundary cases | Lease L1–L5; retry R1–R5, with listed mutant/failure assertions. | Realistic transfer tasks and remaining modes need independent cases. |
| `b7a8e70ba8ee` fixtures only where needed | Retry uses only injected factory/stream fakes; leases use caller-supplied time. | Qualified reviewer assesses necessity in emitted tests. |
| `c541168a6a14` framework preservation | Both repositories establish `unittest`; outputs must collect there without new dependencies. | Non-Python/framework-diversity case needed. |
| `aa421c4141e9` unsupported coverage metrics | Neither case has a coverage artifact; producer must not invent a percentage. | Separate supplied-coverage-artifact case needed. |
| Workflow, placement and routing | Unit generation is primary; tests go to the supplied `tests/` layout. | Explicit edge-case, coverage-analysis, E2E and GitOps-release-routing cases needed. |
| H1 observable oracle / state / recovery additions | Safe alternate implementations plus L1 rejected acquire, L3 expired renew, R3 errors/retry, R4 close-before-retry. | Candidate clauses must be hashed and mapped after candidate exists. |

No waiver is granted by this author. Proposed development scope is unit-test
generation only; E2E, other frameworks, coverage-analysis, edge-case-only mode,
missing-input handling and release handoff remain explicitly uncovered. Coordinator
may approve a narrower development comparison; it cannot establish whole-skill
promotion. Formal promotion needs those cases or legitimate independently reviewed
waivers, and review of every normative clause including clauses missed by extraction.

## Dataset and fixture verification

[`public-fixtures/README.md`](../public-fixtures/README.md) gives a single reproduction
command and the producer/evaluator file boundary. These are PUBLIC development
examples and PUBLIC illustrative answers, never a hidden or independent holdout.

| Case | Observable coverage | Public illustrative mutants | Safe controls |
| --- | --- | --- | --- |
| Lease book | Exact expiry, contention, rejected-state preservation, renewal after expiry, owner release, invalid duration, independent instances/keys | Inclusive expiry; failed-acquire overwrite; expired renewal; wrong-owner release | Correct dictionary reference; correct list representation; same-owner denial and invalid-operation nonmutation |
| Retrying read | Total attempt bound, zero budget, empty success, open/read failure, final exception identity, nonretryable error, exactly-once close, next-call recovery | Missing close; extra attempt; swallowed exhaustion; retrying programming errors; zero attempt acceptance | Correct for-loop reference; correct helper/while implementation; deterministic injected streams |

The public validator delegates collection/execution to `unittest` in temporary
directories, checks exact mutation substitutions, and records normalized assertion
failures separately from collection errors. It does not accept generated submissions,
score skills, sign receipts, or claim process isolation. Do not use it to execute
untrusted model artifacts. Its 52 observations include two repetitions of references,
safe alternatives, mutants, ineffective-existing-suite controls, always-failing
suite controls, and collection-error controls. Every declared fault fires as the
named assertion failure, with no mutant collection errors; all correct variants pass.
Results reproduce exactly after excluding the repetition index.

Checks executed in this setup:

- `bin/capability-eval compile --skill engos-quality-testing-review --check`: pass,
  no drift, `structural_ready`; draft admission remains incomplete.
- `python3 -m pytest tests/test_capability_eval.py -q -p no:cacheprovider`: 12 passed.
- Public fixture command: pass, 9/9 illustrative mutants exposed, zero false failures
  on the four correct case implementations, two deterministic repetitions.
- Baseline Git-byte comparison: all 16 inventoried files equal launch HEAD.
- Negative validator control: changing one expected public failure name in a
  temporary copy makes the real self-check exit 1 with an assertion error;
  original fixture files remain unchanged. Details and pytest output are in
  [`static-verification.json`](../static-verification.json).

[`public-fixture-checks.json`](../public-fixture-checks.json) binds every fixture input
including the self-check code. [`baseline-contract-check.json`](../baseline-contract-check.json)
preserves the actual existing evaluator compile result. The public suites were
authored and executed as expressly requested setup work; none was produced by an
experimental invocation of the target skill.

## Three matched arms and scoring meaning

Proposed arms: A = strong model plus public task only; B = same model plus full
current generated skill and all current resources; C = same model plus full proposed
generated skill and all candidate resources. Suggested cell is `gpt-6-astra` with
`high` effort, subject to coordinator admission and a frozen resolved version.
No model was selected or called experimentally here. Record the actual model build,
effort, tool policy, adapter/CLI versions, complete rendered request, output budget,
resource bytes, starting state and dataset hashes before every admitted run.

Use identical public task files, baseline test file, framework/runtime, common
output-artifact protocol and limits in A/B/C. Full resource inclusion in B/C is the
treatment; differences in prompt length/cost are measured. Tools-off generation is
proposed: source files are supplied in full as task context; outputs are test-file
bytes and an unrun report. Verify the bare runtime has no auto-loaded target skill,
home/repo steering that imports it, ancestor conversation, hooks, browser state,
MCP/credential access or other skill-discovery route. A fresh task is not proof.
The current owner task visibly has the skill available and is unsuitable as arm A.
Independent producers/judges must start without inherited author history only
after coordinator verifies effective boundaries. No hidden answers are authored or
read in this setup; independent dataset owners control any later held-out material.

The separate admitted evaluator collects each emitted suite, executes it on the
reference and safe alternative first, then the mutants under existing contracts.
It must validate that a mutant failure follows the intended behavior defect and
that the same suite passes correct implementations. Crash, import error, timeout,
missing/empty suite, suppressed assertions or fixture failure is not a killed mutant.
Actor-caused unusable output counts as task failure; infrastructure failure is
recorded separately and makes dependent comparison inconclusive. No human repair
of emitted tests is allowed in the frozen scored batch.

Primary outcome: per-case proportion of the declared distinct behavior mutants
detected by runnable emitted tests, averaged equally across the two cases and six
repetitions. An unusable or false-failing suite receives zero for that cell, with
the separate veto retained. Test count, coverage percentage, prose length and
assertion count contribute nothing. Existing tests alone miss all nine mutants,
so a passing empty addition cannot earn a detection score.

Development acceptance requires C minus B **and** C minus A each at least 0.15 on
that 0–1 mean scale, neither case mean worse, and both contrast directions positive
in at least five of six matched repetition blocks. Ties retain B; saturated A/B/C
scores mean no measured gain. This practical screen is not a powered population
claim, and repeated attempts on two cases are not independent dataset breadth.

Hard vetoes: any false failure on a correct implementation; any fabricated run or
coverage claim; production edits/unauthorized execution; missing mandatory output;
representation-coupled/mirror assertions; loss of a previously detected critical
fault; or failure to detect each critical public fault in every C repetition.
Critical public faults are failed-acquire overwrite, wrong-owner release, missing
close and swallowed exhaustion. The exact critical set stays frozen for the batch.

Secondary outcomes are completion rate, determinism of each emitted artifact over
three evaluator executions, raw tokens, end-to-end latency, and operator effort.
Maintainability review checks four concrete properties: assertions trace to the
public contract, setup uses only public dependency boundaries, failures identify
the violated behavior, and shared fixtures do not hide the oracle or require
operator repair. Reviewers record pass/fail evidence, not a stylistic score.
Proposed efficiency guard: C uses at most 1.25 times B's median raw tokens and
latency, unless a new objective is reviewed before a new batch. Preserve raw numbers
and unresolved reviewer disagreement; do not change thresholds after seeing results.

## Repetitions, order, effort and budget proposal

For public development, freeze one candidate before dispatch; no search or feedback
between scored cells. Run each case in six matched repetition blocks with all six
orders `ABC`, `ACB`, `BAC`, `BCA`, `CAB`, `CBA`, for 36 producer calls total. Seed
`611009` chooses case interleaving under the coordinator's admitted scheduler.
Three executions of each emitted suite test execution reproducibility; they are
not three additional independent model observations. Preflight successes, actual
faults, and collection failures must traverse the **real** later collection,
verification and scoring path before the 36-call batch. This public self-check
does not establish that integration. If preflight changes inputs or scoring, freeze
a new batch identity before dispatch rather than mixing results.

The later proposed envelope is 1,250,000 raw tokens, all phases, and at most three
hours from preflight dispatch, including waits, model retries, independent review,
reproduction and final verification. It is **not authorized** by this proposal.
Suggested ceilings: 100k candidate/contract preparation; 150k conformance/preflight;
600k primary generation (36 calls, at most 16k total raw tokens reserved per call,
576k scheduled with 24k phase headroom); 200k independent judgment/reproduction;
200k adjudication/failed-call reserve. Input, cached input, output, reasoning and
charged incomplete attempts count toward raw usage; do not equate an output-token
limit to a total-token reservation. If an admitted adapter cannot enforce the
needed raw accounting, dispatch stays blocked.

Suggested wall-clock partitions: 20 minutes preflight, 80 primary batch,
50 independent review/reproduction, 30 adjudication/closeout. Operator effort
estimate is 30–45 active minutes across contract review, admission and outcome
review, within that elapsed envelope; log actual active minutes, interventions,
artifact repairs and unexpected waits separately. No promise of throughput is
made before adapter admission. Stop new dispatch at a phase/global limit, cancel
or bound outstanding calls through the admitted runner, count spent/reserved tokens,
and report incomplete cells as inconclusive. Never drop cells or purchase capacity.

The existing impact function, given proposed `module_output`, `state`, `safety`
classes, yields `minimum_profile: promotion` and a 5M profile hard cap; see
[`proposed-impact-plan.json`](../proposed-impact-plan.json). This is a conservative
proposal with candidate clause IDs still unbound. The coordinator must reconcile
the 1.25M requested spend ceiling with that minimum profile; it does not authorize
silently using canary or spending 5M. A narrower public pilot remains development
evidence only. Formal promotion also needs independently owned broader cases,
preregistered power/sample size and margins, correction for the two primary
contrasts (e.g. Holm), and independent reproduction under the existing policy.
No powered sample size is asserted for these two public examples.

## Admission gaps, promotion decision, and next action

1. Coordinator must approve the goal, complete the normative clause/case mapping,
   and resolve the explicit mode/coverage waivers. The incumbent has no closed
   current contract or runtime envelope.
2. Candidate SSOT, same-slug UAC delta, full generated resources, exact impact plan,
   baseline/candidate commits and all actual prompts must be created/frozen after
   contract review. No candidate content identity or accepted improvement exists yet.
3. Coordinator reports shared runner gaps: two-arm scheduling and hash-only scorer
   linkage. The existing `EvalRunPlan.v1` exposes baseline/candidate identities,
   not this three-arm treatment. The preregistration schema inspected locally is
   currently Batman-specific. Coordinator must fit/extend the existing interfaces
   and prove semantic execution/scoring; this owner must not invent a second runner.
4. Codex/Kiro registered authenticated adapters remain unavailable/promotion-ineligible
   per the launch boundary. Coordinator owns admitted runtime/credential isolation,
   conformance, accounting, trust policy, qualified judges and effective bare-arm
   exclusion. No workaround with provider keys or another cloud is proposed.
5. Independently exercise representative success and fired-failure controls through
   the actual admitted observation-to-score path; preserve the unrun producer report
   separately from evaluator execution. Local fixture checks cannot satisfy this gate.
6. Resolve concrete token/time reservations and preregistration before any calls.
   Any missing gate leaves comparative result **inconclusive** and incumbent retained.

Commit/review packet: owned public assessment, fixtures and evidence only. No shared
metadata, evaluator code, generated surface, canonical SSOT or skill resource change
is staged. Branch is retained for coordinator integration; no push/merge/install
or release is part of this setup. Public assertions may inform later regression
assets; independently observed failures should be normalized by the dataset owner
and reviewed before adding them to canonical evaluation cases. Do not call these
author examples independent regression validation.

Copy-ready next action:

> Review the Testing Review setup commit on `AI/campaign-testing-review`. Retain
> the incumbent. Accept or revise H1 and the proposed clause/mode coverage in
> `reports/skill-improvement-campaign/skills/engos-quality-testing-review/assessment.md`.
> Integrate the public fixtures through existing capability-eval contracts after
> resolving shared three-arm/scorer and runtime admission gaps. Approve a concrete
> budget/profile and frozen candidate/input plan before dispatching independent
> producers or judges. Do not treat the public self-check as model proof.

Closeout checkpoint: `2026-09-09 23:43:52 UTC`, 12 minutes 25 seconds from recorded
start, with no overrun. Baseline and all 13 fixture file hashes rechecked; negative
self-check control passed. All 19 staged files are owned report/fixture files and
match disk bytes; no unstaged tracked changes. JSON, Python syntax, report links,
inventory digest and staged whitespace checks pass. The coordinator separately
reported that independent review passed the 13-file public fixture snapshot,
9 mutants and 52 reproducible observations; that report is not model proof.
The requested preservation commit is recoverable with
`git log -1 -- reports/skill-improvement-campaign/skills/engos-quality-testing-review/`.
