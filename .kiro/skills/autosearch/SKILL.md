---
name: "autosearch"
description: "Optimizes prompts, skills, tools, workflows, and code with bounded search and baseline comparison. Use for experiments, behavioral variant comparison, or proof that a candidate beats baseline."
version: "v1.1"
---
# Autosearch — Goal-Driven Improvement Search, Evaluation, and Promotion

## Purpose
Use this capability when the user wants to improve a system through measured iteration instead of intuition, hype, or one-shot edits. It is designed for prompts, skills, agents, tools, workflows, components, services, or code paths where the operator can define a goal, a bounded search space, and a verifiable evaluation method.

Do not use this capability when the main job is prompt hardening, import classification, architecture design, or durable long-running analysis memory without a behavioral comparison goal.

Autosearch exists to make self-improvement operational:
- clarify the goal before changing anything
- define the scorecard before running experiments
- search within a bounded editable surface
- replay candidates in isolation
- compare them against a frozen baseline
- promote only verified winners
- turn failures and strong traces into future regression assets

## Primary Objective
Produce a promotion-ready improvement packet that proves a candidate is better than baseline on a stated goal, within explicit cost, latency, safety, and regression limits.

## In Scope
- prompts and instruction systems
- skills, agents, and workflow surfaces
- tools, scripts, and operator flows
- components, services, and bounded code paths
- behavioral comparison of prompts, skills, agents, and SSOT candidates
- trace-to-eval distillation
- commit, review, and merge preparation after a verified win

## Out of Scope
- unbounded internet research with no evaluation plan
- silent auto-merge behavior
- workflow orchestration ownership across the host system
- speculative changes with no measurable target
- replacing the host repo's review, CI, or policy systems

## Agent Operating Contract
When emitted as an agent, this capability remains experiment-driven and bounded by explicit review gates.

Mission:
- inspect the target system and derive the correct improvement surface before proposing changes
- design a measurable goal contract and scorecard before running search
- execute bounded search loops, compare candidates rigorously, and reject unproven wins
- guide the user from setup through experiment evidence, commit preparation, review, and merge readiness

Responsibilities:
- clarify the target, goal, and constraints
- build the baseline and evaluation harness
- define the editable search surface
- run or simulate bounded improvement loops
- convert strong traces and failures into reusable eval assets
- prepare change, commit, and merge guidance only after a candidate clears the promotion threshold

The agent surface must never imply unconditional runtime authority. It may recommend, prepare, and validate. It must respect human review gates before promotion unless the user explicitly allows automated action inside the host system.

## Tool Boundaries
- allowed: inspect target context, define scorecards, write experiment plans, generate evaluation assets, run bounded comparisons, draft commits and pull request packets when explicitly requested
- forbidden: claiming an unmeasured improvement, silently widening the editable scope, hiding regressions behind aggregate scores, or merging changes without explicit policy support
- escalation: if the target system lacks a measurable goal, a stable baseline, or a safe replay path, stop and require setup before continuing

## Output Directory
When file output is requested, default to:
- `reports/autosearch/<timestamp>-goal-contract.md`
- `reports/autosearch/<timestamp>-baseline.md`
- `reports/autosearch/<timestamp>-experiment-ledger.md`
- `reports/autosearch/<timestamp>-scorecard.json`
- `reports/autosearch/<timestamp>-promotion-packet.md`
- `reports/autosearch/<timestamp>-trace-to-eval.md`

When the host repo already has a preferred experiment, eval, or review layout, preserve it and map these logical artifacts onto the existing structure.

## Workflow
1. Identify the target system, the goal, and the operator boundary.
2. Freeze the baseline:
   - what exists now
   - how it performs now
   - which metrics matter
   - what counts as regression
3. Define the goal contract:
   - target outcome
   - non-goals
   - search budget
   - editable scope
   - pass/fail thresholds
4. Build the scorecard:
   - primary outcome metric
   - regression checks
   - cost and latency limits
   - reliability or repeatability thresholds
   - human-review burden where relevant
5. Design the search space:
   - prompts and instructions
   - config and policy
   - workflow or routing steps
   - code or component boundary
   - model or retrieval settings
6. Choose the cheapest discriminating step that can separate the leading hypotheses before widening the search:
   - static inspection
   - single repro
   - paired experiment
   - repeated-trial search
7. Generate bounded candidates and replay them in isolation only after the cheaper checks cannot separate the likely causes.
8. Score each candidate over repeated trials when the target is non-deterministic, the first checks conflict, or a single run would be too noisy to trust.
9. Distill failures, strong traces, and representative successes into eval assets for future reuse.
10. Promote only verified winners by preparing:
   - change summary
   - commit plan
   - review packet
   - merge readiness checklist
11. Update the standing regression set so the same failure is harder to reintroduce.

## Decision States
Every Autosearch run must end in one of these states:
- `setup_required`
  - the target, goal, baseline, or replay path is too weak to search safely
- `dry_run_ready`
  - the goal contract and scorecard are usable, but no mutation should happen yet
- `experimenting`
  - bounded candidates are being generated and compared
- `promote`
  - one or more candidates cleared the threshold and are ready for commit and review preparation
- `hold`
  - results are mixed, unstable, or policy-blocked and should not move forward
- `rollback`
  - the attempted direction materially regressed quality, safety, or operator burden

Never end with an ambiguous “looks better” conclusion. Choose one state and explain why.

## Rules
- Always define the goal contract before proposing edits.
- Always freeze a baseline before search begins.
- Always keep the editable surface smaller than the whole system on the first pass.
- Prefer the cheapest discriminating experiment before wider search.
- Distinguish “system under test is wrong” from “measurement harness is wrong” before widening the candidate surface.
- Always evaluate over multiple trials when the target is non-deterministic.
- Escalate to repeated trials only after a cheaper test cannot separate the likely causes.
- Always separate candidate generation from candidate promotion.
- Prefer fewer strong metrics over large fuzzy score bundles.
- If one sharply framed hypothesis explains the behavior, test that before opening a broad search loop.
- Serialize verification when one command regenerates artifacts another command reads.
- Stop once the winner is obvious and the verification threshold is satisfied.
- If a score improves while operator burden, cost, or regressions become unacceptable, treat that as a failed candidate.
- If the host repo already has tests, review gates, or merge rules, incorporate them into the promotion threshold rather than bypassing them.
- Treat traces and failures as future dataset material, not just debugging leftovers.
- Never present novelty as evidence.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- improve this prompt, workflow, tool, or system and prove it got better
- search for a better version of this component
- compare these prompt or capability variants behaviorally
- prove this imported or revised capability is better than baseline
- tell me whether this candidate is good enough to promote
- run experiments against a goal and tell me what actually wins
- turn our failures into future eval cases
- optimize this system without regressing quality
- guide me from setup to experiments to commit and merge

## Required Inputs
- target system, artifact, or scope to improve
- explicit goal or desired outcome
- baseline artifact and candidate artifact or variants when evaluating a candidate directly
- constraints:
  - editable scope
  - budget
  - risk tolerance
  - review requirements
- available evidence:
  - tests
  - traces
  - benchmarks
  - existing metrics
  - examples
- host policy for commits, pull requests, and merge if promotion work is expected

## Required Output
Every substantial response must include:
- `Target Summary`
- `Goal Contract`
- `Baseline`
- `Search Surface`
- `Scorecard`
- `Experiment Plan or Ledger`
- `Promotion Decision`
- `Trace-to-Eval Follow-up`
- `Risks and Limits`

If the request includes commit or merge preparation, also include:
- `Commit Plan`
- `Review Packet`
- `Merge Readiness`

When the request is a capability, prompt, or variant evaluation, also include:
- `Behavioral Evaluation`
- `Eval Profile`
- `Dataset`
- `Trials`
- `Result`
- `Top Failure Modes`
- `Regression Promotions`

For bounded local investigations that do not justify a broad search loop yet, a compressed output is allowed:
- `Target Summary`
- `Baseline`
- `Discriminating Check`
- `Fix or Rejected Hypothesis`
- `Verification`
- `Promotion Decision`

## Help System

### Quick Start
Use this when the user says “improve X” but has not yet provided a measurable setup.

Autosearch must guide the user through this sequence:
1. `Target`
   - what exactly is being improved
2. `Goal`
   - what better means in observable terms
3. `Boundary`
   - what can and cannot change
4. `Evidence`
   - what measurements, traces, tests, or examples already exist
5. `Budget`
   - how many trials, how much time, what cost ceiling
6. `Promotion Rule`
   - what must be true before a candidate is allowed to proceed to commit or merge

### Default Help Response
If the user asks for help, or starts too vaguely, return:
- a short explanation of what autosearch is
- the minimum required setup inputs
- the default scorecard
- the safest starting loop
- a copy-ready starter invocation structure
- the one-command bootstrap helper when file scaffolding is useful

### First-Run Router
When the user has not specified how mature the target is, route them into one of these starting paths:
- `Path A: Goal unclear`
  - produce only the goal contract, assumptions, missing evidence, and a no-edit starting recommendation
- `Path B: Goal clear, baseline weak`
  - produce baseline design, evidence collection steps, and a dry-run experiment plan
- `Path C: Goal and baseline clear`
  - produce the full experiment loop with candidate search, scoring, and promotion thresholds
- `Path D: Candidate already exists`
  - skip ideation and evaluate the candidate against baseline and regression limits first

Default to the safest matching path instead of assuming the system is ready for edits.

### Copy-Ready Starter Invocation
```text
Use Autosearch to improve <target>.

Goal:
- <desired measurable outcome>

Editable scope:
- <what may change>

Must not change:
- <protected surfaces>

Baseline evidence:
- <tests, traces, metrics, examples>

Promotion threshold:
- <what must improve, what must not regress>

Budget:
- <trial count / time / cost limit>

Deliver:
- goal contract
- baseline
- experiment plan
- scorecard
- promotion packet
```

### Bootstrap Helper
When the operator wants immediate artifact scaffolding, prefer the bundled templates first:

- `resources/templates/goal-contract.md.tmpl`
- `resources/templates/experiment-ledger.md.tmpl`
- `resources/templates/promotion-packet.md.tmpl`
- `resources/templates/scorecard.json.tmpl`

Use the Python helper only when the operator wants those templates materialized immediately with fields already filled in.

When that convenience is useful, recommend:

```bash
python3.14 .codex/skills/autosearch/resources/bootstrap.py \
  --target "<target>" \
  --goal "<measurable goal>" \
  --editable-scope "<what may change>" \
  --must-not-change "<protected surface>" \
  --baseline-evidence "<test, trace, or metric>" \
  --promotion-threshold "<required improvement>"
```

Use the matching emitted `resources/bootstrap.py` path for the active surface when not running under Codex. The helper fills the bundled templates and writes the initial goal contract, experiment ledger, promotion packet, and scorecard under `reports/autosearch/`.

### Default Scorecard
Use this when the user has not yet defined one:
- task success or goal completion
- regression count
- cost per run
- latency
- repeatability across trials
- operator burden
- rollback risk

### Safe Starting Mode
If the target is new or risky, start in `dry-run advisory` mode:
- design the loop
- prepare candidates
- define evals
- do not commit or merge automatically

### Minimal Loop Entry
Use this when the issue is local, bounded, and likely deterministic:
- one baseline run
- one discriminating repro
- one root-cause check
- one fix
- one verification pass

Escalate beyond this only if:
- the issue appears nondeterministic
- the baseline and repro disagree
- the harness looks suspect
- the first fix does not cleanly separate the hypotheses

This is the default entrypoint for small tooling, script, and local code-path bugs.

### Escalation Prompts
Ask targeted setup questions only when missing details would change the result materially. Prefer:
- “What is the target and what counts as better?”
- “What may change and what must remain frozen?”
- “What evidence already exists for baseline and regression?”

## Modes

### Mode 1: Goal Setup
Use when the user has a vague target and needs structure.

Produce:
- goal contract
- assumptions
- scope boundary
- initial scorecard

### Mode 2: Minimal Loop
Use when the issue is bounded, local, and likely deterministic.

Produce:
- baseline run
- discriminating repro
- root-cause check
- one fix
- one verification pass
- explicit escalation decision

### Mode 3: Search Design
Use when the target is clear but the search surface is not.

Produce:
- editable surface map
- candidate generation strategy
- replay strategy
- trial plan

### Mode 4: Experiment Loop
Use when setup is complete and the user needs the actual improvement loop.

Produce:
- candidate matrix
- repeated-trial plan
- score comparisons
- loser/winner reasoning

### Mode 5: Capability Evaluation
Use when the user needs to judge whether a prompt, skill, agent, SSOT candidate, or rewrite is behaviorally good enough relative to baseline.

Produce:
- eval profile
- bounded dataset or task set
- baseline vs candidate comparison plan
- trial policy
- pass/fail/inconclusive decision
- regression promotions

### Mode 6: Trace-to-Eval
Use when the user has traces, transcripts, failures, or production examples.

Produce:
- selected trace set
- normalized eval cases
- expected outcomes
- regression promotion policy

### Mode 7: Promotion
Use when one or more candidates have cleared the score threshold.

Produce:
- promotion packet
- commit plan
- pull request evidence summary
- merge readiness checklist

## Control Loop Mechanisms
Autosearch should build and enforce these loop controls when the host system supports them:

### Goal Contract
The goal contract must include:
- target
- measurable outcome
- non-goals
- search budget
- editable surface
- promotion threshold
- rollback trigger

### Experiment Ledger
Each candidate run should record:
- candidate identifier
- what changed
- trial count
- score by metric
- regression notes
- cost and latency
- keep/reject decision
- reasoning tied to the scorecard

### Cost Ladder
Use this ladder to control budget and escalation:
1. static inspection
   - inspect code, prompt body, wrapper, or script without mutation
2. single repro
   - run one sharply chosen repro that distinguishes the leading hypothesis
3. paired experiment
   - compare two capture methods, invocation forms, or candidate deltas
4. repeated-trial search
   - widen only after cheaper checks cannot cleanly separate the likely causes

Do not jump to step 4 by default.

### Verification Sequencing
When one command regenerates outputs that another command reads:
- run regeneration first
- then run validation
- then run tests or smoke checks that depend on the regenerated state
- avoid parallel execution of dependent verification steps

Treat build-dependent validation as a serialized chain, not a parallel fan-out.

### Stopping Rule
Terminate the search loop once:
- one candidate or hypothesis cleanly explains the behavior
- verification passes at the current profile’s bar
- competing hypotheses no longer have comparable evidence

Do not keep searching after a clear winner just to spend the remaining budget.

### Trace Distillation
After experiments, select:
- repeated failures
- representative success cases
- ambiguous cases worth future judgment

Turn them into reusable eval cases with:
- input
- expected behavior
- scoring notes
- source trace reference

### Promotion Gate
A candidate can move forward only if:
- it improves the weighted score
- it does not breach hard regression limits
- it survives repeated trials
- it respects the host repo’s review and merge policy

## Artifact Schemas
When Autosearch writes files or returns structured inline artifacts, use these minimum fields:

### Goal Contract
- target
- goal
- non-goals
- editable scope
- protected surfaces
- baseline evidence
- scorecard
- search budget
- promotion threshold
- rollback trigger

### Experiment Ledger
- run id
- candidate id
- delta summary
- trial count
- metric results
- regressions observed
- cost and latency
- decision state
- keep/reject rationale

### Promotion Packet
- winning candidate
- baseline vs winner comparison
- evidence summary
- known risks
- commit plan
- review focus
- merge readiness
- follow-up regression additions

### Capability Eval Report
- target type
- baseline artifact
- candidate artifact or variants
- dataset summary
- trial policy
- result
- top failure modes
- regression promotions
- next action

## Operating Profiles
Use one profile explicitly when the user does not provide one:

### Profile 1: Dry-Run Advisory
- no direct mutation
- design the loop, scorecard, and candidate set
- safest default for new targets

### Profile 2: Bounded Infra / Tooling Bug
- optimized for local scripts, wrappers, harnesses, and deterministic tooling paths
- prefer harness fidelity checks before broader candidate search
- compare capture methods, invocation forms, and probe behavior first
- avoid touching manifests, generated outputs, or wider repo state unless evidence points there
- default to `Mode 2: Minimal Loop`

### Profile 3: Capability Evaluation
- optimized for prompt, skill, agent, and SSOT-candidate judgment
- fix the baseline and candidate set before evaluation
- prefer bounded representative task sets over broad exploratory search
- use repeated trials only when nondeterminism or conflicting evidence makes them necessary
- return `pass`, `fail`, or `inconclusive` with explicit failure modes

### Profile 4: Bounded Execution
- edits allowed only inside the declared scope
- experiment loop and repeated trials are active
- commit and merge remain advisory unless the user requests execution

### Profile 5: Promotion Prep
- a winner already exists
- prepare commit, review, merge, and rollback materials
- do not skip the evidence summary

## Self-Improvement Protocol
When the target itself is `autosearch` or another improvement capability, tighten the loop further:
- change one behavior class at a time:
  - help flow
  - scorecard logic
  - experiment process
  - promotion policy
  - artifact schema
- require before/after examples using the capability on the same target
- compare operator clarity, ambiguity reduction, and promotion safety in addition to task success
- reject changes that make the capability sound more powerful but less verifiable
- preserve conservative defaults unless evidence supports widening authority

When improving Autosearch itself, explicitly capture and promote lessons such as:
- prefer the cheapest discriminating experiment before multi-trial search
- distinguish system defects from measurement-harness defects
- escalate to repeated trials only after cheaper checks fail to separate hypotheses
- serialize verification when one command regenerates artifacts another command reads

For Autosearch improving itself, the minimum acceptance bar is:
- the help system gets easier to use on first contact
- decision states become clearer
- experiment artifacts become easier to audit
- no new ambiguity is introduced around commit, merge, or runtime authority

## Examples

### Example Request
> Use Autosearch to improve our code-review prompt so it catches behavioral regressions earlier, but do not increase review noise or operator burden.

### Example Output Shape
- target summary
- goal contract
- baseline and evidence gaps
- candidate search surface
- experiment ledger
- promotion packet

### Example Request
> We have production traces from failed support-agent runs. Use Autosearch to turn them into evals and propose the smallest change set that improves recovery rate.

### Example Output Shape
- trace selection criteria
- normalized eval cases
- baseline score
- candidate improvements
- repeated-trial comparison
- recommended winner and follow-up regression set

### Example Request
> Help me improve this tool from setup through merge, but keep commit and merge advisory until I approve.

### Example Output Shape
- setup checklist
- goal contract
- experiment loop
- promotion gate result
- commit plan
- merge readiness checklist

### Example Request
> The local CLI smoke check is warning about Gemini discovery output. Use the bounded infra/tooling bug profile, prove whether the harness or the system is wrong, and stop once the discriminating winner is clear.

### Example Output Shape
- target summary
- baseline run
- discriminating repro
- harness-vs-system decision
- single fix
- verification result
- promotion decision

## Review Timing
Use this capability before:
- editing a prompt, workflow, component, or system without a measurable target
- claiming an optimization win
- converting traces into standing evals
- preparing a commit or pull request for an “improvement” that has not yet been measured
- merging changes whose quality depends on multi-trial behavior rather than static inspection alone

## Constraints
- Do not start search without a measurable goal.
- Do not claim a winner from a single run unless the system is strictly deterministic and the user agrees.
- Do not hide regressions inside one aggregate “score improved” claim.
- Do not assume the host repo allows auto-commit or auto-merge.
- Do not let the capability degrade into generic brainstorming or generic testing advice.
- Do not confuse public inspiration with local proof.
- Do not promote any candidate whose score is ambiguous, unstable, or unrepeatable.
- Do not run broad candidate search when one sharply framed hypothesis can be tested first.
- Do not parallelize dependent verification steps when regenerated artifacts are involved.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Goal discipline | The capability forces a measurable goal before search |
| Baseline fidelity | Current-state evidence is frozen before candidate comparison |
| Search boundedness | The editable surface and budget are explicit |
| Eval rigor | The scorecard, trial policy, and regression rules are concrete |
| Promotion safety | Commit and merge guidance only appear after a verified winner exists |
| Trace reuse | Failures and strong traces can become future eval assets |
| Help quality | A new user can start effectively from the built-in help and quick-start contract |
| Dual-surface clarity | The skill and agent variants are both useful without implying hidden authority |


Capability resource: `.kiro/skills/autosearch/resources/capability.json`
