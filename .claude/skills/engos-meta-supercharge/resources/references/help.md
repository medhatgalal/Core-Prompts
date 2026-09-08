## HELP OUTPUT (Quick Guide)

**SuperCharge v5.0** — Prompt Engineering Swiss Army Knife (portable)

### Common Commands
- `engos-meta-supercharge <task>` -> Auto-route to best sequence
- `engos-meta-supercharge /ult <task>` -> Prompt engineer mode (generate, refine, and execute)
- `engos-meta-supercharge /basis <task>` -> First-principles reasoning and irreducible simplicity
- `engos-meta-supercharge /adversarial <task>` -> Red-team critique and hardening
- `engos-meta-supercharge /adversarial /debate <task>` -> Surface Bull/Bear/Decider debate
- `engos-meta-supercharge /adversarial /debate /deep <task>` -> Deep multi-round Bull/Bear/Decider debate
- `engos-meta-supercharge /debate <task>` -> Shortcut for `/adversarial /debate`
- `engos-meta-supercharge /debate /deep <task>` -> Shortcut for `/adversarial /debate /deep`
- `engos-meta-supercharge /full <task>` -> Run gauntlet outputs without execution
- `engos-meta-supercharge /catchup` -> Deep forensic catchup (multi-intent, validated)
- `engos-meta-supercharge /gaslight <task>` -> GASLIGHT 13 (explicit, bounded)

### All Modules
- Modes: `/ult`, `/catchup`
- Lenses: `/basis`, `/simple`, `/invert`, `/adversarial`, `/contract`, `/grade`
- Adversarial modules: `/adversarial`, `/adversarial /debate`, `/adversarial /debate /deep`
- Debate shortcuts: `/debate`, `/debate /deep`
- Gauntlet: `/full`
- Explicit-only: `/gaslight`
- Controls: `/route`, `/details`, `/help examples`, `/stop-ult`
- Modifiers: `/realism`, `/edge`, `/concise`, `/creative`, `/safe`

### Module Usage
- `/ult <task>` -> create, refine, and execute a prompt
- `/basis <task>` -> derive the simplest sufficient approach without losing sophistication
- `/simple <task>` -> decomplect braided responsibilities
- `/invert <task>` -> start from failure modes and missing signals
- `/adversarial <task>` -> red-team critique and fixes
- `/adversarial /debate <task>` -> surface Bull/Bear/Decider debate
- `/adversarial /debate /deep <task>` -> deep multi-round Bull/Bear/Decider debate
- `/contract <task>` -> produce a contract spec and QA JSON
- `/grade <task>` -> run up to 10 real candidate trials with independent grading by default
- `/full <task>` -> run the gauntlet without executing the final prompt
- `/catchup` -> reconstruct session state as validated forensic tables
- `/gaslight <task>` -> explicit-only GASLIGHT 13 prompt hardening

### Per-Module Examples
- `engos-meta-supercharge /ult improve this agent prompt: <paste>`
- `engos-meta-supercharge /basis audit this onboarding workflow for actual-to-minimum waste: <paste>`
- `engos-meta-supercharge /simple separate product requirements from implementation choices: <paste>`
- `engos-meta-supercharge /invert find how this migration plan could fail: <paste>`
- `engos-meta-supercharge /adversarial red-team this release plan: <paste>`
- `engos-meta-supercharge /adversarial /debate decide whether to adopt this architecture: <paste>`
- `engos-meta-supercharge /adversarial /debate /deep stress-test this investment thesis using only the provided data: <paste>`
- `engos-meta-supercharge /contract turn this plan into a verifiable execution contract: <paste>`
- `engos-meta-supercharge /grade improve this prompt with independent graded trials: <paste>`
- `engos-meta-supercharge /full design an agentic CI gate for OpenAPI breaking changes`
- `engos-meta-supercharge /catchup`
- `engos-meta-supercharge /gaslight refine this prompt to reduce drift: <paste>`

### Stack Examples
- `engos-meta-supercharge /simple /invert analyze micro-frontends adoption`
- `engos-meta-supercharge /basis /simple /contract reduce this workflow's operator burden: <paste>`
- `engos-meta-supercharge /invert /adversarial harden this rollout plan: <paste>`
- `engos-meta-supercharge /adversarial /debate /contract decide and specify this API change: <paste>`
- `engos-meta-supercharge /adversarial /debate /deep /contract decide and specify this migration: <paste>`
- `engos-meta-supercharge /ult /contract create a prompt and then evaluate its contract: <paste>`
- `engos-meta-supercharge /full skip grade compare these three plans: <paste>`

Stacking is sequential, not simultaneous heavy-framework mixing. SuperCharge runs passes in canonical order and keeps the smallest useful route.

Ask `engos-meta-supercharge /help examples` to auto-generate example usage for each module and common module stacks.

### Routing Preview
- `engos-meta-supercharge /route <task>` -> prints routing line, then proceeds

### Full Spec
- `engos-meta-supercharge details` -> prints the module reference


Substantial reviews require actual independent subagents; self-review is not a fallback. `/ult` displays then runs within authorized scope unless draft/review-only or stacked with `/full`. `/full` grades without executing its task. Required module resources must be delivered in full before work.
