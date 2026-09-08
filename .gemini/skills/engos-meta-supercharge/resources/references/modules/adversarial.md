## MODULE: /adversarial — Adversarial Red-Teaming (Devil's Advocate)

### Purpose
Stress test the plan, prompt, workflow, code-review conclusion, investment thesis, or architecture decision to expose blind spots and harden it.

Use the standard `/adversarial` mode for compact red-team critique. Use nested `/adversarial /debate` when the decision needs explicit Bull/Bear/Decider dissent. Use nested `/adversarial /debate /deep` when stakes, ambiguity, disagreement, or asymmetric downside justify a multi-round debate.

### HARD CONSTRAINTS
- Use actual independent subagents to take an attacking, refuting stance. Seek concrete counterexamples and pressure-test the strongest claims, not a weak substitute.
- Prefer specific edge cases over generic critique.
- "No material issue found" is a valid result after investigation. Every finding identifies an affected assumption or behavior, its evidence or explicit uncertainty, and its consequence; do not invent defects to fill the format.
- Identify unstated assumptions and where they break.
- Do not rewrite the entire artifact unless asked; critique and fixes first.
- Ground claims in provided context, inspected code, cited data, or explicit reasoning.
- Do not invent facts, cite unavailable evidence, or present stale market knowledge as current.
- Do not claim that debate proves behavioral superiority; route proof requests to `engos-optimization-auto-research`.

### Standard Output Structure (MANDATORY)
1. `Attack Surface`
2. `Contradictions / Gaps`
3. `Mitigations / Fixes`
4. `Residual Risk`

### Nested Module: /adversarial /debate — Surface Bull/Bear/Decider Debate

Purpose: provide a compact structured dissent pass when normal critique may be too one-sided.

Shortcut:
- `engos-meta-supercharge /debate <task>` routes to `engos-meta-supercharge /adversarial /debate <task>`

Council independence: separate Bull and Bear subagents form initial positions from the same factual packet without the author's preferred verdict or each other's initial answer. Only then exchange arguments. A separate Decider adjudicates using evidence, can reject both positions, or retain uncertainty. `Confidence: 0-100` is a judgment estimate unless empirically calibrated, not a probability guarantee.

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
- `engos-meta-supercharge /debate /deep <task>` routes to `engos-meta-supercharge /adversarial /debate /deep <task>`

Rules:
- `/deep` is scoped to `/debate` only. Do not treat it as a global modifier for unrelated modules.
- `/deep` without `/debate` is invalid. Return the corrected `/debate /deep` and `/adversarial /debate /deep` forms without running unrelated modules.
- Bull and Bear first form independent assessments; preserve their initial records before exchanging the documented rebuttal rounds. Bull and Bear must engage each other's strongest points rather than producing parallel essays.
- Use a separate Decider; it may reject both positions or specify the evidence required to break a tie. Label confidence as judgment unless calibrated. The lead agent must not impersonate the council.
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
