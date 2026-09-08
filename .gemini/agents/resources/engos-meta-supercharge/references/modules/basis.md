## MODULE: /basis — First-Principles Reasoning and Irreducible Simplicity

### Purpose
Reconstruct a problem from the required outcome, supported facts, binding constraints, and explicitly identified assumptions. Challenge what is actually necessary, then derive the simplest sufficient approach without losing sophistication, capability, quality, or legitimate safeguards. Cost accounting is one application, not the definition of this lens.

Use `/basis` for first principles, justified complexity, waste, optimization, or questions about whether the current approach is necessary. An independent reviewer challenges claimed primitives, cost assumptions, and proposed removals before synthesis.

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

### First-Principles Workflow
- Identify primitives: required inputs, outputs, constraints, physics, data, user value, safety requirements, or repo policy.
- Derive a sufficient approach from those primitives before optimizing the inherited implementation. Preserve necessary sophistication; distinguish irreducible requirements from familiar ways of meeting them.
- Estimate a minimum only where defensible: cost, complexity, latency, token budget, file count, process steps, or review load. Under `Theoretical Minimum`, describe a qualitative sufficient design or state unknown when no numerical minimum can be justified.
- Measure the actual: current artifact size, moving parts, runtime cost, coordination steps, dependencies, or user burden.
- Compute `Actual-to-Minimum Ratio` only when both quantities have defensible units and evidence. Otherwise state not applicable or unknown and identify what would make comparison meaningful; do not invent a ratio or categorical estimate.
- Isolate waste drivers: indirection, ceremony, overgeneralization, duplicated surfaces, avoidable manual work, weak evals, or legacy assumptions.
- Choose redesign moves that follow from the primitives: delete unnecessary work, separate concepts, combine genuine duplicates, automate, defer, prove necessity, or run a measured comparison. These are choices, not a mandatory deletion-first sequence.

### Domain Mapping
- Prompt or skill: raw materials are intent, constraints, examples, evals, and output contract.
- Software workflow: raw materials are required data, side effects, verification gates, and user-visible outcomes.
- Product or operation: raw materials are user value, materials, labor, compute, capital, time, and compliance needs.
- Knowledge work: raw materials are source facts, judgment calls, audience needs, and decision criteria.

### Examples
Example (Capability)
Before: “Add three new modules, a new agent, and a longer prompt to improve quality.”
After: Map the irreducible quality requirement, measure the added operator burden, remove modules that duplicate `/simple` or `/contract`, and route only unproven behavioral claims to `engos-optimization-auto-research`.

Example (Workflow)
Before: “This review process needs six meetings and three reports.”
After: Identify the required decisions and evidence, collapse duplicate status reporting, and keep only the review gates that protect irreversible risk.
