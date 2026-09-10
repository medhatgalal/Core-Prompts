# Proposed whole-capability comparison

Status: **unapproved; no model dispatch**. This replaces the old unit-only 1.25M
proposal as the prospective whole-skill plan. It does not reset prior usage.
Research preparation is underway in the owner task; model-mediated experiments
remain zero. See `phase-baseline.json` for the separate 60-minute phase clock.

## Which model capabilities matter

| Work | Relevant capability | Observation, not a model-brand assumption |
| --- | --- | --- |
| Strategy and test-level selection | Reasoning about consequences and evidence boundaries | Correct risk/level choices, appropriate restraint and minimal operator clarification |
| Unit/integration generation | Precise code synthesis, framework conventions, contract reasoning | Executable tests detect faults, allow correct variants, preserve data and cleanup |
| E2E design/generation | UI/API grounding and asynchronous state reasoning | Observable synchronization, real/mocked boundaries, correct selectors and recoverable failures |
| Edge cases | Equivalence partitions, boundary/state reasoning, ambiguity handling | Concrete missing cases without inventing new product rules |
| Coverage analysis | Artifact interpretation and skepticism | Correct provenance/metric interpretation and assertion-gap identification |
| Every job | Instruction fidelity, context selection and truthful reporting | No execution/coverage fabrication, no skill loading in bare arm, no source edits outside scope |

Read-only evidence in `native-runtime.json` shows Codex CLI `0.153.4`, Kiro CLI
`2.21.2` and local model metadata freshly fetched near phase start. Astra/Sol/Terra
list `high`; the app also exposes those models. These facts do not prove successful
authenticated calls or that any model is suitable. The registered adapters still
declare authentication unavailable and bind older versions (Codex `0.150.1`,
Kiro `2.20.0`). The `codex exec` help exposes model/config selection, JSONL output,
ephemeral operation and user-config/rules suppression; none by itself proves
suppression of skills, ancestor instructions, hooks, credentials or all tools.

Official [model guidance](https://learn.chatgpt.com/docs/models) supports comparing
effort/usage tradeoffs and warns that availability depends on runtime/account.
The [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model)
specifically makes accessible instructions and over-testing relevant controls.
Those facts guide the plan; vendor capability labels do not select a winner.

## Separate model effects from skill effects

**Model suitability screen:** hold the complete incumbent, public task inputs,
artifact protocol, tools and starting state fixed. Compare `gpt-6-astra/high`,
`gpt-5.6-sol/high` and `gpt-5.6-terra/high` over one task from each of six major jobs,
two independent builds per task/model: 36 builds. Use counterbalanced order and
the same bounded context. Freeze actual resolved identifiers and versions before
dispatch; equal effort labels are not equal compute across models. Measure total
raw tokens and latency. Luna or another model can be a later preregistered screen
if the efficient model fails the desired cost/quality point; no automatic substitution.

**Effort screen:** on the selected model, compare its existing high-arm results to
12 new medium-effort builds (six jobs × two builds), changing only effort. If the
high-arm runs are no longer comparable in version/runtime/state, do not reuse them:
re-budget a fresh paired screen. No Max/Ultra in this screen; automatic extra builds
or subagent use would confound a single-model comparison and need separate accounting.

Choose the least expensive configuration meeting all protected outcomes and a
predeclared task-success non-inferiority margin of 0.05 against the quality reference,
with at least 20% median raw-token or end-to-end latency improvement and no more
than 10% worsening on the other efficiency metric. With six authored task families,
this is a developmental screen, not proof of population non-inferiority. An
ambiguous/noisy result retains Astra/high provisionally or remains inconclusive;
its earlier suggestion never counts as suitability evidence. Require confirmation
on new task instances before recommending a default. No account billing estimate
is substituted for raw usage; record cached/uncached and actual charges separately
if the admitted runtime supplies them. No API purchase is authorized.

**Skill comparison:** use one frozen quality-reference model/settings cell for all
three arms: A bare public task, B full incumbent, C full candidate and resources.
Keep task/context, tools, output protocol, starting state, runtime version and
limits identical. Full supplied bytes, including descriptor and resource content,
must be bound. This draft has source and authored resources, not a generated release
bundle; coordinator must generate/freeze the trial descriptor/surface before using
it as C. Never give C a stale four-mode incumbent descriptor by accident.

For the first comparison supply every resource completely so resource selection
does not become an uncontrolled advantage. A subsequent resource-selection/cost
experiment may measure applicable-route delivery, holding the skill's actual
content and task fixed. Keep complete manifests and actual supplied bundles in
both records. The bare arm gets only common instructions and task data: no target
skill in messages, config, filesystem, memory, hooks, browser or MCP discovery.

Two paths have different scope: prompt-only builds can test reasoning and emitted
artifact quality with all public repository inputs pre-supplied; read/tool-enabled
builds also test discovery and environment behavior. Start with the smallest admitted
prompt-only path and label its limit. Do not infer native repository discovery or
browser competence from it. Later native tests require observed file/tool/MCP/hook/
browser boundaries. Fresh tasks/worktrees alone are insufficient in either path.

## Outcomes and scoring

The 12 public cases in `../public-scenarios/cases.json` cover strategy, unit,
integration, E2E, edge and coverage jobs. Three additional routing/authority controls
are preflight gates. Their authored expectations are openly disclosed development
answers. Independently owned confirmation cases must differ materially from them;
the author receives public contracts and permitted aggregate feedback only.

Primary outcome is the fraction of tasks whose useful artifact is accepted within
each job, macro-averaged equally across six jobs. For generated-code tasks,
acceptance needs successful collection, correct/safe implementation passes and
predeclared meaningful fault detection. For plans/analyses, independent review must
verify the specific high-risk decisions, evidence and executable next step against
the task's acceptance observations. Review is blinded to arm identity and uses
evidence, not prose polish or heading count. Plan acceptance is a judgment outcome;
it must not be reported as executed E2E success. Actual browser-generated tests
require an admitted runner and a real semantic observation before any execution claim.

Also report per-case mutant detection, false failures, unsupported gap findings,
critical-risk recall, fixture/collection failures, diagnostic usefulness and human
interventions. Equivalent/invalid mutants do not inflate denominators. Timeouts
and fixture errors remain distinct from semantic detection; if the chosen mutation
tool counts them differently, preserve the original result and state our metric.

Proposed practical improvement bar: C minus B and C minus A both at least 0.10 on
the macro task-acceptance scale; no major-job mean below either control; nonnegative
contrast in both repetition blocks. For generation subtests, require at least 0.15
mean semantic-detection improvement over each control unless that metric saturates;
saturation yields no claim of detection gain. All critical faults must be caught
in every candidate repeat. Critical public faults include lost durable orders,
unauthorized lease release, state corruption after rejected acquire, lost cleanup,
swallowed exhaustion and allowing settled-order cancellation.

Hard vetoes: false failure on a correct implementation; fabricated execution,
coverage or hosted state; unauthorized source/data writes or test execution;
unsupported framework replacement; missing critical assertions/decision; an
uncontained generated artifact; or a claim stronger than the measured boundary.
For analyses, unsupported high-severity gaps are false positives and cannot be
offset by longer lists. Missing dependencies/collection errors caused by an output
count as task failures. Infrastructure failures retain consumed usage and make
dependent comparisons inconclusive rather than erasing established output defects.

Maintainability: observable contract oracles; only necessary dependency fakes;
clear failure attribution; isolated setup/cleanup; no redundant coverage without a
reason. Judge these as evidenced properties. No reward for test count, mirrored
implementation algorithms, giant snapshots, or private attribute coupling.

Cost guard for quality-improving C: median raw tokens and latency each no more than
1.35× B and no more than two additional active reviewer minutes per task. This
relaxes the historical 1.25 ratio prospectively for a broader resource treatment,
not in response to results. A separate simplicity candidate can qualify with no
observed job/critical regression and at least 20% raw-token/latency reduction, or
30% operator-time reduction, with no material worsening of the other metrics.
That is an explicit alternative objective, not a post-hoc way to claim a tie won.

## Repetition, exploration and confirmation

For each trial candidate, 12 cases × 3 arms × 2 independent builds = 72 outputs.
Use paired cases and seeded balanced order (`seed: 611010`); assign the six A/B/C
permutations evenly across 24 case/repetition blocks. Re-execute a generated test
artifact three times in clean admitted environments to test determinism; those
executions are not independent model builds. Record model stochasticity separately.

At most two distinct candidate hypotheses in this proposed wave. T0 is the drafted
full-workflow/resource design. Use the observed failure pattern to define T1, such
as removing redundant resource requirements if overhead outweighs benefit. Freeze
T1 identity, objective and all inputs before its comparisons; do not modify evaluators
or scoring while optimizing the skill. An accepted T0 provisionally becomes the
incumbent for T1, but retain the original B anchor and A comparison. Preserve losses
and ties. No improvement is a valid result; absence of valid measurement is inconclusive.

Continue after an initial win/loss until two hypotheses are evaluated, two distinct
non-improving hypotheses establish the bounded plateau, or the declared broad target
survives independent confirmation. Confirmation uses six new independently authored
task instances, one per major job, × three arms × two builds = 36 outputs. It must
retain the gain direction, pass every hard gate and resolve reviewer disagreements
material to the conclusion. Six new families are not automatically enough for formal
promotion; a qualified evaluator must set power/sample size, confidence intervals,
multiple-comparison correction and wider transfer requirements prospectively.

## Proposed aggregate contribution and clocks

### First decision: a fixture-sized stage, not the whole envelope

Admit **only Stage D0 first**, if its runtime boundary can be proved: one supplied
SQLite integration task, three matched A/B/C producer calls, at most 20k raw tokens
each. The separate evaluator runs each emitted artifact against the correct local
SQLite implementation and the public missing-commit fault, plus a known collection
failure control. This exercises actual success/failure collection and scoring;
static fixture results do not replace it. Two bounded tools-off review calls at
8k each may verify semantic failure attribution and truthful unrun reporting.
Reserve one failed/charged producer replacement at 20k; total **96k raw tokens**,
at most six model calls, **30 elapsed minutes**, including final evidence binding.
The replacement is only for a classified infrastructure failure; do not retry a
bad skill output until it passes. Unknown charged usage blocks further reservation.

Before reserving any call, upper-bound the exact full prompt/resources, maximum
artifact and hidden reasoning under the selected runtime. Reject this 20k/8k grid
if complete input/output cannot fit; do not truncate the skill or borrow from the
larger envelope. Full candidate descriptor generation and observed bare-arm skill
exclusion remain prerequisites. D0 tests the collection path, not whole-skill
benefit or model suitability. No winner is selected from this one-task stage.

After D0 passes, coordinator reviews actual sizes/latency and admits a job-sized
next stage. The 12-case/three-arm design is a menu with explicit claims, not an
automatic batch launch. A six-job screen can precede the second instance of each
job; a partial screen cannot establish the full capability. Native/tool-enabled
evidence is a separate stage. Coordinator reports a nested Seatbelt launch
limitation, not verified isolation; this owner has not reproduced that diagnostic.

### Contingent whole-wave sizing ceiling

This is a **new unapproved contribution of at most 5,000,000 raw tokens** for the
broader Testing workstream, including preparation. It supersedes the old narrow
1.25M proposal; it is not authorization to spend. Prior ordinary setup usage remains
unknown and must be reconciled separately in the campaign ledger, never set to zero.
Current research/design usage is also not yet measured. The preparation reservation
below must cover the measured current/new preparation or the budget must be revised
before dispatch. Calls include hidden reasoning, cached input, output, retries and
charged incomplete requests; an output-token limit is not a full-call reservation.

| Phase | Raw-token ceiling | Call/build ceiling |
| --- | ---: | --- |
| Research, candidate/contract preparation and handoff | 200,000 | At most 4 further author/review turns; reconcile this phase's actual usage |
| Actual collection/scoring preflight and controls | 120,000 | 6 × 20,000 |
| Model suitability | 540,000 | 36 × 15,000 |
| Effort suitability | 180,000 | 12 × 15,000 |
| Two full skill trials | 2,880,000 | 144 × 20,000 |
| Independent scoring/judgment/adjudication | 384,000 | 48 × 8,000; deterministic execution preferred |
| Independent confirmation | 540,000 | 36 × 15,000 |
| Failed calls, reserve and final verification | 156,000 | At most 12 bounded calls × 13,000; no hidden retries |
| Total | 5,000,000 | Up to 294 experimental calls plus bounded preparation turns |

Use exact input sizes and enforced worst-case output/reasoning limits at admission.
If a 15k/20k reservation cannot hold a complete task/skill/resource input and useful
output, reject this grid and revise prospectively; do not silently truncate inputs.
The whole-wave table is contingent sizing, not reserved capacity or an admission
request to launch every cell now. D0 is charged within its preflight allowance.
Unused reservations do not authorize an unlisted experiment. The 5M figure happens
to match a promotion-profile cap; spending it does not confer promotion evidence.
Formal cross-model/runtime claims may require a higher profile under existing
policy, and need separate authorization rather than bypass through a development label.

Proposed downstream wall-clock cap: six hours from first admitted preflight dispatch,
inclusive of waiting, all builds, judges, retries and final verification. Partitions:
30 minutes preflight; 60 model/effort screening; 150 two trial batches; 80 confirmation
and independent judging; 40 reserve/closeout. Operator effort estimate: 60–90 active
minutes for admission, domain review and unresolved judgments within that elapsed
window, measured separately. Do not assume host slots or time targets are achievable:
coordinator must reserve actual capacity and adjust the grid before launch if needed.
Stop new dispatch at phase/global limits, boundedly stop outstanding calls, account
for charged/incomplete attempts and retain the last supported incumbent. Do not
silently reset clocks or omit cells to fit a preferred conclusion.

The current ordinary preparation phase started `2026-09-10 00:08:03 UTC` and targets
`01:08:03 UTC`, including research, fixture checks, review handoff and preservation.
No experimental clock has started. At that deadline, stop new preparation and
record incomplete artifacts or overrun. The coordinator owns independent challenge.

## Smallest development path needing a decision

Request once: admit or reject a prompt-only, subscription-authenticated development
path that supplies frozen public context and complete artifacts, disables unintended
skill/tool loading, emits reliable usage/content receipts, and sends generated tests
to an isolated existing runner. Start with representative real success/failure
observations through collection and scoring, not a new general evaluator framework.
This path can establish only supplied-context artifact performance until native
discovery/tool behavior is separately tested. Existing capability-eval contracts,
resource assembly and receipt/scoring formats should be reused where they fit;
coordinator owns small extensions for three-arm scheduling and semantic execution.

Missing: observed runtime boundaries and admission; exact resolved model/call
reservations; complete reviewed clause mapping; candidate rendered descriptor/bundle;
actual E2E execution/semantic scorer integration; independent case/judge ownership;
and a reconciled budget that accounts for preparation. `PromotionVerdict.v2` is a
formal promotion gate, not a blanket prerequisite for drafting or an explicitly
admitted bounded development experiment. No provider keys, new credentials,
paid APIs, resets, cloud migration or privileged ad-hoc harness are proposed.
