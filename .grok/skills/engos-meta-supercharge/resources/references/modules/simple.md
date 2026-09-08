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
- Distinguish MUST / MUST NOT invariants from PREFER guidance. Do not silently weaken requirements or promote preferences into obligations.
- Use explicit one-way dependencies between independent concerns; identify and justify any irreducible cycle rather than hiding it behind new modules.
- Validate invariants as well as outputs: retained guarantees, side-effect boundaries, and failure behavior must still hold after decomplecting.

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

### Decomplect Workflow
- Assess: What are the responsibilities and boundaries?
- Decomplect: Identify independently meaningful concepts and explain how state, identity, timing, policy, data, or responsibilities have become braided. Remove the unnecessary dependency itself; moving headings or files alone does not establish simplicity.
- Compose: Re-assemble via explicit interfaces.
- Validate: Demonstrate a concrete change one concern can now undergo without forcing unrelated concerns to change. An independent reviewer checks retained behavior, residual coupling, and whether the new boundaries merely relocate the braid. Keep the behavior map proportional to the task.

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
The response MUST include 1–2 worked examples tailored to the user's domain. Only when the domain is unknown, include one general example. The reference examples below do not substitute for tailoring at runtime.
Example (Prompt)
Before: "Build a product plan and architecture and write code and tests and deployment steps."
After: Separate product acceptance from implementation choice so another architecture can satisfy the same goal without rewriting the requirements; make deployment depend on verification evidence rather than on the order of prose headings.

Example (Decision)
Before: "We should do X because it's fast and safe and scalable."
After: Split speed claims vs safety claims vs scalability claims, with evidence for each.

### Foundation
Rich Hickey, [Simple Made Easy](https://www.infoq.com/presentations/Simple-Made-Easy/): use simplicity as independence from entanglement, not familiarity, fewer parts, or reduced ambition.
