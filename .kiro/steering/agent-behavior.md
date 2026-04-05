---
inclusion: always
---

# Agent Behavior Steering

## Purpose

Keep rule surfaces machine-readable, keep human docs free of hidden policy, and force execution quality to stay grounded in facts and best practices.

## Rules Versus Docs

- Do not comingle rules and docs.
- If content is intended to govern agent behavior, put it in `AGENTS.md` or `.kiro/steering/*.md`, not in human onboarding or maintainer docs.
- Write rule files so an LLM can execute them deterministically:
  - imperative wording
  - explicit triggers
  - explicit boundaries
  - minimal ambiguity
- Human docs may describe workflows, rationale, and examples, but they must not be the canonical source of agent policy.
- Human docs should link to the relevant steering surface when behavior is governed by rules elsewhere.

## Ask Evaluation Quality

- Do not execute a user ask blindly when it conflicts with repo facts, verified behavior, or clear best practices.
- Test requests against:
  - current repository state
  - verified command and path behavior
  - generated surface reality
  - established engineering and documentation best practices
- If a request is weak, risky, or internally inconsistent, say so plainly and propose the strongest corrected version.
- Prefer verified facts over remembered assumptions.
- When facts are easy to verify locally, verify them before encoding them into docs or rules.
- When changing Kiro-specific steering, skills, agents, or invocation guidance, verify the current behavior against official Kiro documentation or the Kiro Help Agent before freezing repo policy.

## Policy Placement

- Put cross-surface operating policy in steering.
- Put short routing guidance in `AGENTS.md`.
- Put user guidance, maintainer explanation, and examples in `README.md` or `docs/`.
- If a human doc starts reading like agent policy, move that content into steering and leave behind a short explanatory reference.
