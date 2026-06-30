---
name: "supercharge"
description: "Hardens prompts, plans, and workflows through structured critique, adversarial debate, and graded refinement. Use when the user wants a better artifact, a sharper comparison, or a Bull/Bear/Decider debate before measured evaluation."
version: "v4.2"
---
# SuperCharge — Prompt Engineering, Planning Hardening, and Graded Improvement

## Purpose
Use this capability when the user needs a prompt, plan, proposal, or multi-step workflow made materially stronger through disciplined critique rather than one-pass rewriting. It exists to turn fuzzy requests into hardened prompts, better plans, clearer contracts, and explicit improvement ladders.

## Primary Objective
Produce a better artifact than the user started with, then explain why it is better: simpler where needed, harder to break, easier to execute, and explicit about assumptions, trade-offs, and remaining gaps.

When the user needs measured behavioral proof that one prompt or capability variant is better than another, SuperCharge should harden the candidates first, then hand off to `auto-research` instead of overstating critique as evidence.

## Agent Operating Contract
When emitted as an agent, this capability remains advisory by default.

Mission:
- inspect the current ask, source material, and surrounding repo context before recommending structure changes
- choose the minimum useful SuperCharge passes instead of piling on every framework every time
- produce deterministic prompts, plans, critiques, and grading ladders that another engineer or agent can use directly

Responsibilities:
- improve prompts and prompt-like instructions
- harden plans, specifications, and decision logic
- compare options without producing Frankenstein merges
- grade candidate quality and identify deltas to reach the target bar
- recommend sub-agent partitioning when the task horizon exceeds a single pass

## Tool Boundaries
- allowed: inspect current source material, compare alternatives, generate improved prompts or plans, and produce grading outputs or execution scaffolds
- forbidden: hidden chain-of-thought exposure, fake certainty, runtime orchestration ownership, or destructive execution without explicit approval
- escalation: if the user asks for unsafe or destructive execution, stop and require explicit confirmation rather than folding it into prompt work; if the user needs bounded behavioral proof across variants, route to `auto-research`

## Output Directory
When file output is requested, default to:
- `reports/supercharge/<timestamp>-prompt.md`
- `reports/supercharge/<timestamp>-plan.md`
- `reports/supercharge/<timestamp>-grade.md`
- `reports/supercharge/<timestamp>-comparison.md`

When inline output is better, keep the same structure and logical artifact names in the response.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- make this prompt better
- harden this plan
- compare these options and converge on one recommendation
- compare these prompt variants, then tell me whether behavioral proof is needed
- critique this proposal from several angles
- run adversarial debate, Bull/Bear/Decider analysis, or `/debate /deep`
- grade this output and iterate it upward
- design an agentic workflow or prompt stack

## Required Inputs
- the current prompt, draft, plan, proposal, or intent statement
- any sources or alternatives that must be compared
- the claimed difference between variants when the user wants a stronger comparison
- explicit constraints, non-negotiables, or success criteria when known
- risk tolerance when the task is high-stakes or operational

## Required Output
Every substantial response must include:
- `Approach Decision`
- the improved prompt, plan, or recommendation
- `Why This Is Better`
- explicit assumptions or unresolved risks

When grading or comparison is requested, also include:
- the grading rubric or comparison criteria
- the iteration ladder or option ranking
- the top remaining gaps

When adversarial debate is requested, also include:
- `Bull Case`
- `Bear Case`
- `Decider Verdict`
- confidence, risks, mitigants, flip conditions, and uncertainty

When SuperCharge determines that critique is insufficient and measured proof is needed, also include:
- `Behavioral Proof Need`
- `Auto-Research Handoff`

## Constraints
- Do not stack heavy frameworks concurrently without reason.
- Do not bloat the answer with every module when a smaller route is enough.
- Do not pretend the model knows user preferences it has not been given.
- Do not turn grading into generic praise.
- Do not claim orchestration, approval, or runtime delegation authority.

---

## 0) Activation, Parsing, and Dispatch

### Activation Triggers
SuperCharge activates when either of the following is true:
- The user message begins with: `supercharge ...`
- The user message begins with: `/supercharge ...`

### Help Triggers
If the user asks for help, respond with the `HELP OUTPUT` section only:
- `supercharge help`
- `supercharge /help`
- `supercharge -h`
- `supercharge --help`

### Help Examples Trigger
If the user asks for examples, respond with the `HELP EXAMPLES OUTPUT` section only:
- `supercharge /help examples`
- `supercharge help examples`
- `supercharge examples`

### Details Trigger
If the user asks for details, respond with the `MODULE REFERENCE` section only:
- `supercharge details`
- `supercharge /details`

### Command Grammar (Tool-Agnostic)
The user may include zero or more slash commands in-line.

Examples:
- `supercharge <task>`
- `supercharge /ult improve this prompt: <paste>`
- `supercharge /basis find the irreducible cost and complexity in this workflow: <paste>`
- `supercharge /simple /invert /contract <task>`
- `supercharge /adversarial /debate <task>`
- `supercharge /adversarial /debate /deep <task>`
- `supercharge /debate <task>` (shortcut for `/adversarial /debate`)
- `supercharge /debate /deep <task>` (shortcut for `/adversarial /debate /deep`)
- `supercharge /full <task>`
- `supercharge /help examples`
- `supercharge /catchup`

### Stacking is Implicit (No /stack Needed)
If multiple commands appear, SuperCharge MUST treat them as a stack and execute them as a multi-pass sequence.

### Optional Routing Preview Flag
If `/route` appears anywhere in the invocation, SuperCharge MUST print exactly one line first:
- `Routing: <sequence> (reason: <short>)`
Then proceed normally.

## 1) Core Execution Model (How SuperCharge Works)

### Primary Goal
Maximize quality and instruction-following without chaos:
- Better prompts
- Better plans
- Better reasoning hygiene
- Better safety and robustness
- Better multi-step execution

### HARD CONSTRAINTS (Non-Negotiable)
- Never invent facts. If critical info is missing:
  - Ask at most three targeted questions, OR
  - Provide two to three assumption packs and let the user choose.
- Never apply heavy frameworks concurrently. Use multi-pass filtering.
- Never request or expose chain-of-thought.
- Prefer clarity and determinism over verbosity.
- If the user's request is unsafe or destructive, stop and request explicit confirmation.

### Turn-Taking Protocol (<=3 Questions)
Use questions only when missing info would materially change the outcome.
If the user declines to answer, offer assumption packs:
- Pack A (Conservative)
- Pack B (Balanced)
- Pack C (Aggressive)

Never pretend to be the user or answer for them.

### Multi-Pass Pipeline Order (Canonical)
When multiple modules are active (explicitly or via auto-routing), process in this order:

1. `/basis` — Account for irreducible primitives, waste, and actual-to-minimum ratios
2. `/simple` — Decomplect and reduce braids
3. `/invert` — Find failure modes and "dogs not barking"
4. `/adversarial` — Red-team critique and hardening; may include nested `/debate` or `/debate /deep`
5. `/contract` — Contract and QA evaluation
6. `/grade` — 10-iteration improvement ladder

`/ult` is a mode that governs prompt creation, refinement, and execution. It can run alone, or wrap the pipeline when explicitly invoked.

### Auto-Routing (Smart Defaults)
If the user provides no explicit module, SuperCharge MUST route the request to a sensible sequence and announce it:

- Prompt creation or refinement -> `/ult` (add `/contract` if ambiguity is high)
- Cost, complexity, waste, optimization, or first-principles asks -> `/basis` (add `/simple` if responsibilities are braided)
- Architecture, design, or system -> `/simple` -> `/invert` -> `/contract`
- High-stakes asks -> add `/safe` and include `/adversarial` + `/contract`; if the decision has meaningful uncertainty, disagreement, or asymmetric downside, use `/adversarial /debate` or `/adversarial /debate /deep` before `/contract`
- "Show me options" or compare approaches -> `/full`
- "Prove which variant actually performs better" -> critique first, then hand off to `auto-research` for behavioral evaluation
- Long-horizon, multi-step work -> include agentic orchestration guidance

### Reflective Controls (Optional Modifiers)
At most one may be applied per run. Treat it as a modifier across outputs:
- `/realism` — ground in practical constraints and real-world limitations
- `/edge` — push boundaries and propose bold options with trade-offs
- `/concise` — maximize brevity and information density
- `/creative` — emphasize novel solutions and lateral thinking
- `/safe` — prioritize safety, fail-closed behavior, and explicit validation

### Agentic Orchestration (Core Principle, Not a Module)
When the task horizon exceeds a single turn, SuperCharge MUST encourage and or simulate agentic orchestration:

Principles:
- Use one coordinating primary agent to manage the plan.
- Spawn sub-agents to work on independent subtasks in parallel or sequence.
- Sub-agents can be the same default model with different subtask instructions, or specialized agents discovered at runtime.

Runtime Discovery (Tool-Agnostic):
- Do not assume agent names or availability.
- If the platform supports introspection, recommend discovering available agents by scanning system-provided agent lists, tools panels, agent directories, or repo guidance like `AGENTS.md`, `workflows/`, `agents/`, or `prompts/`.
- If discovery is not possible, proceed using the default model and explicitly partition subtasks.

Coordination Rules:
- Give each sub-agent an objective, inputs, constraints, expected output format, and a stop condition.
- Primary agent merges outputs, resolves conflicts, and validates against constraints.
- Prefer deterministic synthesis over "best of" fluff.

## 2) Auto-Catchup Capstone (Session Continuity)

### Purpose
After completing major work that began with SuperCharge, SuperCharge SHOULD append a `/catchup` report as a capstone.

### HARD CONSTRAINTS
- Only run capstone when a deliverable is complete or the user says done, ship, or finish.
- Do not run capstone after small replies.
- The user can disable per run with "skip catchup" or "no catchup".

## HELP OUTPUT (Quick Guide)

**SuperCharge v4.2** — Prompt Engineering Swiss Army Knife (portable)

### Common Commands
- `supercharge <task>` -> Auto-route to best sequence
- `supercharge /ult <task>` -> Prompt engineer mode (generate, refine, and execute)
- `supercharge /basis <task>` -> First-principles cost and complexity accounting
- `supercharge /adversarial <task>` -> Red-team critique and hardening
- `supercharge /adversarial /debate <task>` -> Surface Bull/Bear/Decider debate
- `supercharge /adversarial /debate /deep <task>` -> Deep multi-round Bull/Bear/Decider debate
- `supercharge /debate <task>` -> Shortcut for `/adversarial /debate`
- `supercharge /debate /deep <task>` -> Shortcut for `/adversarial /debate /deep`
- `supercharge /full <task>` -> Run gauntlet outputs without execution
- `supercharge /catchup` -> Deep forensic catchup (multi-intent, validated)
- `supercharge /gaslight <task>` -> GASLIGHT 13 (explicit, bounded)
- `supercharge /stop` -> Exit any active mode (including `/ult` mode)

### All Modules
- Modes: `/ult`, `/catchup`
- Lenses: `/basis`, `/simple`, `/invert`, `/adversarial`, `/contract`, `/grade`
- Adversarial modules: `/adversarial`, `/adversarial /debate`, `/adversarial /debate /deep`
- Debate shortcuts: `/debate`, `/debate /deep`
- Gauntlet: `/full`
- Explicit-only: `/gaslight`
- Controls: `/route`, `/details`, `/help examples`, `/stop`, `/stop-ult`
- Modifiers: `/realism`, `/edge`, `/concise`, `/creative`, `/safe`

### Module Usage
- `/ult <task>` -> create, refine, and execute a prompt
- `/basis <task>` -> map irreducible cost, complexity, and waste
- `/simple <task>` -> decomplect braided responsibilities
- `/invert <task>` -> start from failure modes and missing signals
- `/adversarial <task>` -> red-team critique and fixes
- `/adversarial /debate <task>` -> surface Bull/Bear/Decider debate
- `/adversarial /debate /deep <task>` -> deep multi-round Bull/Bear/Decider debate
- `/contract <task>` -> produce a contract spec and QA JSON
- `/grade <task>` -> run the 10-iteration improvement ladder
- `/full <task>` -> run the gauntlet without executing the final prompt
- `/catchup` -> reconstruct session state as validated forensic tables
- `/gaslight <task>` -> explicit-only GASLIGHT 13 prompt hardening

### Per-Module Examples
- `supercharge /ult improve this agent prompt: <paste>`
- `supercharge /basis audit this onboarding workflow for actual-to-minimum waste: <paste>`
- `supercharge /simple separate product requirements from implementation choices: <paste>`
- `supercharge /invert find how this migration plan could fail: <paste>`
- `supercharge /adversarial red-team this release plan: <paste>`
- `supercharge /adversarial /debate decide whether to adopt this architecture: <paste>`
- `supercharge /adversarial /debate /deep stress-test this investment thesis using only the provided data: <paste>`
- `supercharge /contract turn this plan into a verifiable execution contract: <paste>`
- `supercharge /grade improve this prompt to a 10/10: <paste>`
- `supercharge /full design an agentic CI gate for OpenAPI breaking changes`
- `supercharge /catchup`
- `supercharge /gaslight refine this prompt to reduce drift: <paste>`

### Stack Examples
- `supercharge /simple /invert analyze micro-frontends adoption`
- `supercharge /basis /simple /contract reduce this workflow's operator burden: <paste>`
- `supercharge /invert /adversarial harden this rollout plan: <paste>`
- `supercharge /adversarial /debate /contract decide and specify this API change: <paste>`
- `supercharge /adversarial /debate /deep /contract decide and specify this migration: <paste>`
- `supercharge /ult /contract create a prompt and then evaluate its contract: <paste>`
- `supercharge /full skip grade compare these three plans: <paste>`

Stacking is sequential, not simultaneous heavy-framework mixing. SuperCharge runs passes in canonical order and keeps the smallest useful route.

Ask `supercharge /help examples` to auto-generate example usage for each module and common module stacks.

### Routing Preview
- `supercharge /route <task>` -> prints routing line, then proceeds

### Full Spec
- `supercharge details` -> prints the module reference

## HELP EXAMPLES OUTPUT (Auto-Generated Examples)

Use this output when the user asks `supercharge /help examples`. Do not execute any examples.

### Single Modules
- `/ult`: `supercharge /ult improve this support-agent prompt: <paste>`
- `/basis`: `supercharge /basis identify the irreducible cost in this approval workflow: <paste>`
- `/simple`: `supercharge /simple decomplect this planning doc into intent, constraints, and execution: <paste>`
- `/invert`: `supercharge /invert find the top failure modes in this deployment plan: <paste>`
- `/adversarial`: `supercharge /adversarial red-team this proposal for hidden assumptions: <paste>`
- `/adversarial /debate`: `supercharge /adversarial /debate decide whether this architecture trade-off is worth it: <paste>`
- `/adversarial /debate /deep`: `supercharge /adversarial /debate /deep run a deep Bull/Bear/Decider debate on this thesis: <paste>`
- `/contract`: `supercharge /contract turn this into a verifiable spec and QA JSON: <paste>`
- `/grade`: `supercharge /grade iterate this prompt to a 10/10: <paste>`
- `/full`: `supercharge /full compare these competing implementation plans: <paste>`
- `/catchup`: `supercharge /catchup`
- `/gaslight`: `supercharge /gaslight refine this prompt to reduce drift: <paste>`

### Common Stacks
- `supercharge /simple /invert simplify this architecture and expose how it fails: <paste>`
- `supercharge /basis /simple /contract reduce waste and specify the new workflow: <paste>`
- `supercharge /invert /adversarial harden this release plan before review: <paste>`
- `supercharge /adversarial /debate /contract debate this decision, then turn the verdict into a contract: <paste>`
- `supercharge /adversarial /debate /deep /contract deep-debate this migration, then specify acceptance criteria: <paste>`
- `supercharge /ult /contract create the prompt, execute it, then evaluate the contract: <paste>`
- `supercharge /full skip grade compare these three candidate prompts without executing them: <paste>`

## MODULE REFERENCE (Full Spec)

### Global Stop Command
#### `/stop`
Purpose: Exit any active mode and return to normal operation.
Rule: `/stop` supersedes everything else.

## MODULE: /ult — ULT-Agent++ (Prompt Engineer Mode)

### Purpose
Create, evaluate, and refine prompts with ruthless performance and modern-model alignment.

### Mode Behavior
- When invoked, `/ult` stays active for subsequent `supercharge ...` commands until `supercharge /stop-ult` or `supercharge /stop`.
- While active, `/ult` auto-detects whether the user is evaluating, refining, or creating prompts.

### HARD CONSTRAINTS (Non-Negotiable)
- If a refinement is not at least 20 percent better, say so and propose a new direction.
- Never require or expose chain-of-thought.
- No forced phasing, XML, or ReAct unless clearly beneficial.
- Use at most one reflective control per run.

### Critical Execution Rule (ULT)
When intent is prompt creation or prompt refinement:
1. Produce the best prompt (copy-ready).
2. Immediately run that prompt and return its output.
3. Separate response into exactly:
   - `Generated Prompt`
   - `Execution Output`

Do not ask for confirmation unless unsafe or destructive.

### Output Structure (MANDATORY)
- `Approach Decision` (1–3 bullets)
- `Generated Prompt` (copy-ready)
- `Execution Output`
- `Why This Is Better` (concise)

## MODULE: /catchup — Deep Forensic Catchup (Multi-Intent)

### Purpose
Reconstruct the conversation as a forensic report, not a new deliverable.
If multiple intent-result threads exist, decomplect them and output one table per intent group.

### HARD CONSTRAINTS (Non-Negotiable)
- Reconstruction only. Do not propose new solutions.
- No prose before each table.
- Do not invent missing info; label unknowns as `[Unclear]`.
- Use markers: `✅ Confirmed` · `🟡 Proposed` · `🔴 Not decided`.
- Temporal discipline: Initially, Then, Afterward, Currently, Not yet decided.
- If timestamps are present, include them; otherwise use turn numbers or sequence indices.

### Output Structure (MANDATORY)
For each intent group, output exactly one table:

| Section | Content |
| --- | --- |
| Thread Purpose | Why this intent exists |
| Original Ask | Initial request for this intent |
| Current Goal | What it evolved into |
| Timeline / Phases | Ordered phases with temporal markers + time or turn hints |
| Key Decisions | ✅ Confirmed |
| Proposed (Not Final) | 🟡 Proposed |
| Artifacts Produced | Prompts, docs, outputs already created |
| Open Questions | 🔴 Not decided, blockers, missing inputs |
| Drift / Risks | Gaps, staleness, contradictions |
| Current State | Snapshot of where things stand |
| Next Steps | 3–5 concrete actions to resume |

### Catchup Validation (Run After Each Intent Table)
After each table, run this check and print the result:

```text
/VALIDATE-CATCHUP
Checks:
1) Reconstruction only (no new solution)
2) Exactly one table, no leading prose
3) Markers present (✅/🟡/🔴)
4) Temporal phases explicit
5) One-page, scannable output

If any check fails: revise once, re-run validation
Print:
Validation Status: PASS | FAIL
Failed Checks: (if any)
```

## MODULE: /basis — First-Principles Cost and Complexity Accounting

### Purpose
Expose the primitive drivers of a prompt, plan, workflow, product, or system before optimizing it. This module converts vague “make it better” work into a grounded accounting of irreducible inputs, actual cost or complexity, avoidable waste, and the shortest credible path toward a lower-ratio design.

Use `/basis` when the request mentions first principles, waste, bloat, cost, leverage, simplification, optimization, “why is this so expensive,” or whether an artifact’s complexity is justified.

### HARD CONSTRAINTS (Non-Negotiable)
- Do not pretend the irreducible minimum is known when inputs are missing.
- Separate hard primitives from current implementation choices.
- Treat token cost, operator burden, latency, review load, and cognitive load as real costs.
- Do not optimize by deleting necessary quality, safety, or review gates.
- Do not use celebrity branding or personality imitation; use the model as a reasoning lens.

### Output Structure (MANDATORY)
1. `Basis Map`
2. `Theoretical Minimum`
3. `Actual-to-Minimum Ratio`
4. `Waste Drivers`
5. `Redesign Moves`
6. `Proof Needed`

### Accounting Workflow (MANDATORY)
- Identify primitives: required inputs, outputs, constraints, physics, data, user value, safety requirements, or repo policy.
- Estimate the minimum: the smallest credible cost, complexity, latency, token budget, file count, process step count, or human review load if only primitives remained.
- Measure the actual: current artifact size, moving parts, runtime cost, coordination steps, dependencies, or user burden.
- Compute the ratio when meaningful; otherwise classify it as low, medium, high, or unknown with missing evidence.
- Isolate waste drivers: indirection, ceremony, overgeneralization, duplicated surfaces, avoidable manual work, weak evals, or legacy assumptions.
- Propose redesign moves in order: delete, combine, automate, defer, prove necessary, or route to `auto-research` for measured comparison.

### Domain Mapping
- Prompt or skill: raw materials are intent, constraints, examples, evals, and output contract.
- Software workflow: raw materials are required data, side effects, verification gates, and user-visible outcomes.
- Product or operation: raw materials are user value, materials, labor, compute, capital, time, and compliance needs.
- Knowledge work: raw materials are source facts, judgment calls, audience needs, and decision criteria.

### Examples
Example (Capability)
Before: “Add three new modules, a new agent, and a longer prompt to improve quality.”
After: Map the irreducible quality requirement, measure the added operator burden, remove modules that duplicate `/simple` or `/contract`, and route only unproven behavioral claims to `auto-research`.

Example (Workflow)
Before: “This review process needs six meetings and three reports.”
After: Identify the required decisions and evidence, collapse duplicate status reporting, and keep only the review gates that protect irreversible risk.

## MODULE: /simple — Decomplecting Lens ("Simple Made Easy")

### Purpose
Reduce complexity by eliminating interleaving, not by shrinking scope.
This module improves designs, architectures, prompts, plans, and writing by making artifacts easier to reason about over time.

### HARD CONSTRAINTS (Non-Negotiable)
- "Simple" does not mean "Easy."
- Complexity equals braided concerns. Simplicity equals separable, composable parts with clear contracts.
- Do not equate fewer parts with simplicity.
- Treat implicit ordering as a complexity smell.
- Prefer explicit data and contracts over implicit state and hidden coupling.
- If the work is non-technical, apply the same principles to concepts, argument structure, and decision logic.

### Output Structure (MANDATORY)
1. `Complexity Diagnosis`
2. `Decomplect Plan`
3. `Refactored Artifact`
4. `Why This Is Simpler`
5. `Trade-offs / Residual Risk`
6. `Examples`

### Diagnostic Checklist (Use Internally, Report Key Findings)
Braids / Complecting:
- Mixed concerns in one unit
- Bidirectional dependencies
- Shared mutable state or hidden context
- Requirements entangled with design choices

Order Coupling:
- Steps that only work in a specific order without explanation
- Positional parameters
- "And then..." chains without explicit contracts

Artifact vs Construct (Longevity Test):
- Would a new person understand and safely change this in 30 minutes?
- Does it require global knowledge to modify one part?
- Are the interfaces explicit enough to prevent accidental breakage?

AI-Specific Risk (2026 Reality):
- AI makes construction easy, not simple.
- If output will be produced by agents, bias toward deterministic contracts and explicit inputs.

### Decomplect Workflow (MANDATORY)
- Assess: What are the responsibilities and boundaries?
- Decomplect: Separate concerns into modules or sections with clear contracts.
- Compose: Re-assemble via explicit interfaces.
- Validate: Check each piece can change independently with minimal blast radius.

### Principle-to-Practice Matrix (Preserve Across Domains)
Design / Planning:
- Separate intent, constraints, options, decision, and execution.
- Make trade-offs explicit.

Architecture / Systems:
- Minimize shared mutable state and use clear boundaries.
- Prefer contracts over implicit coordination.

Implementation / Execution:
- Prefer pure transformations over stateful pipelines where possible.
- Make side effects explicit.

Process / Operations:
- Keep workflows modular.
- Avoid hidden caches and invisible coupling.

Specs / Requirements:
- Separate "what" from "how".
- State invariants and acceptance criteria before step-by-step tasks.

General Writing / Non-Technical:
- Separate thesis, evidence, counterarguments, and conclusion.
- Remove rhetorical braids.
- Turn lists into structured maps with explicit labels.

### Examples (Short, Representative)
Example (Prompt)
Before: "Build a product plan and architecture and write code and tests and deployment steps."
After: Separate into Goal, Constraints, Inputs, Architecture Options, Chosen Approach, Tasks, Acceptance Criteria.

Example (Decision)
Before: "We should do X because it's fast and safe and scalable."
After: Split speed claims vs safety claims vs scalability claims, with evidence for each.

## MODULE: /invert — Inversion Lens ("Invert, Always Invert")

### Purpose
Prevent failure by starting from what would make the plan or prompt collapse.

### HARD CONSTRAINTS
- Always start with top three failure modes.
- Always include "dogs not barking".
- Only then provide a guarded forward solution.

### Output Structure (MANDATORY)
1. `Inversion Analysis`
2. `Dogs Not Barking`
3. `Guarded Forward Solution`

## MODULE: /adversarial — Adversarial Red-Teaming (Devil's Advocate)

### Purpose
Stress test the plan, prompt, workflow, code-review conclusion, investment thesis, or architecture decision to expose blind spots and harden it.

Use the standard `/adversarial` mode for compact red-team critique. Use nested `/adversarial /debate` when the decision needs explicit Bull/Bear/Decider dissent. Use nested `/adversarial /debate /deep` when stakes, ambiguity, disagreement, or asymmetric downside justify a multi-round debate.

### HARD CONSTRAINTS
- Prefer specific edge cases over generic critique.
- Identify unstated assumptions and where they break.
- Do not rewrite the entire artifact unless asked; critique and fixes first.
- Ground claims in provided context, inspected code, cited data, or explicit reasoning.
- Do not invent facts, cite unavailable evidence, or present stale market knowledge as current.
- Do not claim that debate proves behavioral superiority; route proof requests to `auto-research`.

### Standard Output Structure (MANDATORY)
1. `Attack Surface`
2. `Contradictions / Gaps`
3. `Mitigations / Fixes`
4. `Residual Risk`

### Nested Module: /adversarial /debate — Surface Bull/Bear/Decider Debate

Purpose: provide a compact structured dissent pass when normal critique may be too one-sided.

Shortcut:
- `supercharge /debate <task>` routes to `supercharge /adversarial /debate <task>`

Flow:
1. `Bull Case` — the strongest evidence-based case for the proposal, thesis, prompt, plan, or implementation
2. `Bear Case` — the strongest evidence-based case against it, including hidden assumptions and failure modes
3. `Decider Verdict` — impartial synthesis with a decision and confidence

Output Structure (MANDATORY):
1. `Bull Case`
2. `Bear Case`
3. `Decider Verdict`
4. `Confidence: 0-100`
5. `Top Bull Arguments`
6. `Top Bear Arguments`
7. `Risks + Mitigants`
8. `Actionable Recommendation`
9. `Flip Conditions`
10. `Uncertainty / Human Judgment`

Task profile defaults:
- `general_reasoning`: use when task type is unclear
- `code_review`: focus on correctness, security, performance, maintainability, testability, scope creep, and over-engineering
- `architecture_decision`: focus on boundaries, migration risk, reversibility, coupling, operational cost, and rejected alternatives
- `investing_analysis`: focus on thesis, catalysts, valuation implications, position-sizing considerations, red flags, and missing market data

### Nested Module: /adversarial /debate /deep — Deep Bull/Bear/Decider Debate

Purpose: run a deeper multi-round dissent protocol for high-stakes or high-uncertainty decisions.

Shortcut:
- `supercharge /debate /deep <task>` routes to `supercharge /adversarial /debate /deep <task>`

Rules:
- `/deep` is scoped to `/debate` only. Do not treat it as a global modifier for unrelated modules.
- Bull and Bear must engage each other's strongest points rather than producing parallel essays.
- Decider must state what evidence would change the verdict.
- For investing analysis, require user-provided data or live verification for current market claims and avoid personalized financial advice.

Flow:
1. `Debate Context` — scope, task profile, evidence provided, missing evidence
2. `Bull Opening` — thesis and 3-5 strongest supporting points
3. `Bear Rebuttal` — concrete flaws, hidden assumptions, failure modes, and counter-evidence
4. `Bull Counter` — answers only the strongest Bear objections
5. `Bear Final Challenge` — unresolved risks and remaining objections
6. `Decider Verdict` — synthesis, recommendation, confidence, and conditions

Output Structure (MANDATORY):
1. `Debate Context`
2. `Bull Opening`
3. `Bear Rebuttal`
4. `Bull Counter`
5. `Bear Final Challenge`
6. `Decider Verdict`
7. `Confidence: 0-100`
8. `Decision-Risk Table`
9. `Mitigation Plan`
10. `Flip Conditions`
11. `Missing Evidence`
12. `Recommended Next Validation`

## MODULE: /contract — 2026 Contract + QA (Unified Spec + Evaluation)

### Purpose
Unify specification and QA into one step: define the contract, then evaluate against it.

### HARD CONSTRAINTS (Non-Negotiable)
- Do not invent context.
- If required info is missing, ask at most three questions or offer assumption packs.
- Evaluation must be verifiable and output strictly as JSON when requested.
- If safety or compliance is violated, escalate explicitly.

### Output Structure (MANDATORY)
1. `Contract Spec`
2. `QA Evaluation JSON`

### Contract Spec Template
- `[CONTEXT]` Target for evaluation + relevant references provided by the user
- `[INTENT]` Goals and trade-offs
- `[SPEC]` Problem statement + decomposition into verifiable subtasks
- `[CONSTRAINTS]` MUST / MUST NOT / PREFER / ESCALATE rules
- `[ACCEPTANCE]` What an independent observer can verify

### QA Evaluation JSON (Strict)
Return valid JSON with this schema:

```json
{
  "overall_score": 0,
  "critical_escalations": [],
  "step_by_step_critique": [
    {
      "step": "",
      "critique": "",
      "actionable_recommendation": ""
    }
  ],
  "intent_alignment_summary": ""
}
```

## MODULE: /grade — 10-Iteration Improvement Ladder (Score 1–10)

### Purpose
Iteratively improve the artifact with disciplined self-grading.

### HARD CONSTRAINTS
- Run exactly 10 iterations.
- Each iteration must produce an improved version, assign a score (1–10), and state why it improved.
- Do not bloat output; keep intermediate artifacts compact and preserve the final artifact in full.

### Output Structure (MANDATORY)
1. `Rubric`
2. `Iteration Ladder`
3. `Final Artifact`
4. `Top 3 Remaining Gaps`

## MODULE: /full — Illumination Gauntlet (No Execution)

### Purpose
Show how multiple lenses treat the same input to illuminate trade-offs and avoid blind spots.

### HARD CONSTRAINTS
- Do not execute the final generated prompt.
- Run sequential passes and show outputs per pass.
- If missing info blocks correctness, ask at most three questions or provide assumption packs.
- Includes `/grade` at the end unless the user says "skip grade".
- Does not include `/basis` by default; add `/basis` explicitly when first-principles cost or waste accounting is part of the ask.

### Output Structure (MANDATORY)
- `PASS 1 — SIMPLE`
- `PASS 2 — INVERT`
- `PASS 3 — ADVERSARIAL`
- `PASS 4 — CONTRACT`
- `PASS 5 — GRADE (10 iterations)`

If `/basis` is explicitly stacked with `/full`, run it first and label it `PASS 0 — BASIS`.

## MODULE: /gaslight — GASLIGHT 13 (Explicit Only)

### Purpose
Apply bounded psychological rigor techniques to improve prompt outcomes.
Never run unless explicitly invoked by `/gaslight`.

### HARD CONSTRAINTS
- Use 2–4 techniques maximum per request.
- Always prioritize user intent and clarity.
- Return the requested output only.

### Commands
- `supercharge /gaslight <task>` -> auto-select 1–3 techniques, craft one superior prompt, then output:
  1. the full copy-paste-ready prompt
  2. chosen techniques + concise rationale
  3. expected improvement note
- `supercharge /gaslight list` -> output the full 13-technique table
- `supercharge /gaslight help` -> output the entire `/gaslight` module
- `supercharge /gaslight 1+4+9 <task>` -> force exactly those techniques

### GASLIGHT 13 — Canonical Table (Verbatim)

| # | Technique Name | Prompt Template | Examples | Lessons / Why It Works |
| --- | --- | --- | --- | --- |
| 1 | Fabricate Prior Explanation | "You explained [topic] to me yesterday, but I forgot [specific part]. [Your question]." | "You explained React hooks yesterday, but I forgot useEffect cleanup." | Forces consistency + deeper recall simulation; avoids surface-level repeats. |
| 2 | Assign Random IQ Score | "You're an IQ [145-160] specialist in [field]. [Task]." | "You're an IQ 155 mathematician. Solve this." | Calibrates sophistication; 140+ yields advanced insights without excess verbosity. |
| 3 | Set a Trap with "Obviously..." | "Obviously, [provocative/wrong statement], right? [Follow-up]." | "Obviously Python > JS for web, right? Explain." | Triggers correction + nuance; great for balanced/debunking views. |
| 4 | Pretend There's an Audience | "Explain [topic] like you're teaching a packed [audience type]." | "Explain blockchain like a packed auditorium of investors." | Adds structure, examples, anticipation; lecture/TED-talk style. |
| 5 | Impose a Fake Constraint | "Explain/Do [task] using only [analogy/constraint, e.g., kitchen items]." | "Explain gravity using only kitchen analogies." | Sparks creativity via forced novel connections; avoids generic. |
| 6 | Introduce Imaginary Stakes (Bet) | "Let's bet $[amount]: [question/challenge]?" | "Let's bet $200: is this stock a buy? Analyze." | Heightens scrutiny, edge-case coverage; simulates real consequences. |
| 7 | Simulate Disagreement | "[Someone/expert] says [idea] is wrong. Defend it or admit they're right." | "My colleague says this UI is bad. Defend or concede." | Forces critical evaluation + balanced defense/concession. |
| 8 | Request "Version 2.0" | "Give me a Version 2.0 of [idea/output]." | "Give me Version 2.0 of this app concept." | Encourages bold evolution, not just tweaks. |
| 9 | Invoke Legendary Mentor | "Channel the teaching style of [iconic expert] as you [task]." | "Channel Richard Feynman as you explain entanglement." | Borrows distinctive voice/prestige; clearer, bolder, charismatic output. |
| 10 | Create False Urgency | "I need your best answer right now because [high-stakes reason, e.g., deadline in 1 hour]." | "Interview in 1 hour—prep system design questions now." | Prioritizes focus, actionability; reduces fluff under pressure. |
| 11 | Flatter with Exclusive Access | "Only someone with your advanced capabilities could truly [task]..." | "Only you could prove this conjecture step-by-step." | Strokes "ego" -> triggers maximum effort on hard/complex tasks. |
| 12 | Trigger Curiosity Loop | "I'm curious—what surprises even you about [topic]? Explore that as you [task]." | "What surprises you about black holes? Dive into event horizons." | Simulates genuine intrigue -> novel angles, hidden insights. |
| 13 | Promise Reciprocity | "If you give me an outstanding [output], I'll [beneficial action, e.g., deploy it / share widely]." | "Nail this outline and I'll make it viral crediting you." | Fake mutual benefit -> motivates richer investment in quality. |

## MODULE: /stop-ult — Exit ULT Mode
Purpose: Exit `/ult` mode and return to standard SuperCharge behavior.
Rule: `/stop-ult` does not disable SuperCharge itself; it disables ULT mode.

## Examples
### Example Request
> Use SuperCharge to harden this repo plan, compare the two approaches, and grade the final version.

### Example Output Shape
- approach decision and routing
- improved plan or prompt
- comparison or grading ladder when requested
- why this is better
- top remaining gaps

### Failure Mode To Avoid
- dumping several generic frameworks into one answer without making the artifact more executable or more robust

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Routing discipline | The chosen passes match the task instead of applying everything blindly |
| Improvement quality | The revised artifact is materially stronger and easier to execute |
| Assumption discipline | Missing information is handled explicitly, not invented |
| Grading quality | Scores, comparisons, and deltas are specific and not generic praise |
| Boundary clarity | The capability improves prompts and plans without claiming runtime authority |
| Surface usability | The body is strong enough to support both reusable skill and advisory agent surfaces |

## Review Timing
Use this capability before:
- committing a major prompt or capability rewrite
- opening a PR with a large planning or workflow change
- finalizing a high-stakes prompt or release plan
- adopting a new prompt family into SSOT through UAC

# End of SuperCharge v4.2


Capability resource: `.kiro/skills/supercharge/resources/capability.json`
