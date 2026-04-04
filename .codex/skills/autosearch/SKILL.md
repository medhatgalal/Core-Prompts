---
name: "autosearch"
description: "Autosearch for goal-oriented search, experiment design, repeated-trial evaluation, trace-to-regression distillation, and promotion-ready improvement loops across prompts, tools, systems, workflows, services, and code."
---
# Autosearch — Goal-Driven Improvement Search, Evaluation, and Promotion

## Purpose
Use this capability when the user wants to improve a system through measured iteration instead of intuition, hype, or one-shot edits. It is designed for prompts, skills, agents, tools, workflows, components, services, or code paths where the operator can define a goal, a bounded search space, and a verifiable evaluation method.

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
6. Generate bounded candidates and replay them in isolation.
7. Score each candidate over repeated trials instead of trusting one lucky run.
8. Distill failures, strong traces, and representative successes into eval assets for future reuse.
9. Promote only verified winners by preparing:
   - change summary
   - commit plan
   - review packet
   - merge readiness checklist
10. Update the standing regression set so the same failure is harder to reintroduce.

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
- Always evaluate over multiple trials when the target is non-deterministic.
- Always separate candidate generation from candidate promotion.
- Prefer fewer strong metrics over large fuzzy score bundles.
- If a score improves while operator burden, cost, or regressions become unacceptable, treat that as a failed candidate.
- If the host repo already has tests, review gates, or merge rules, incorporate them into the promotion threshold rather than bypassing them.
- Treat traces and failures as future dataset material, not just debugging leftovers.
- Never present novelty as evidence.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- improve this prompt, workflow, tool, or system and prove it got better
- search for a better version of this component
- run experiments against a goal and tell me what actually wins
- turn our failures into future eval cases
- optimize this system without regressing quality
- guide me from setup to experiments to commit and merge

## Required Inputs
- target system, artifact, or scope to improve
- explicit goal or desired outcome
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

### Mode 2: Search Design
Use when the target is clear but the search surface is not.

Produce:
- editable surface map
- candidate generation strategy
- replay strategy
- trial plan

### Mode 3: Experiment Loop
Use when setup is complete and the user needs the actual improvement loop.

Produce:
- candidate matrix
- repeated-trial plan
- score comparisons
- loser/winner reasoning

### Mode 4: Trace-to-Eval
Use when the user has traces, transcripts, failures, or production examples.

Produce:
- selected trace set
- normalized eval cases
- expected outcomes
- regression promotion policy

### Mode 5: Promotion
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

## Operating Profiles
Use one profile explicitly when the user does not provide one:

### Profile 1: Dry-Run Advisory
- no direct mutation
- design the loop, scorecard, and candidate set
- safest default for new targets

### Profile 2: Bounded Execution
- edits allowed only inside the declared scope
- experiment loop and repeated trials are active
- commit and merge remain advisory unless the user requests execution

### Profile 3: Promotion Prep
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


Capability resource: `.codex/skills/autosearch/resources/capability.json`
