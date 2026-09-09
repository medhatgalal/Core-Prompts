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

## Comparative Evaluation and Bounded Work

- Before comparative grading, define score meaning, material success/regression criteria, and the baseline. When baseline and candidate saturate the same metric, do not claim improvement on that metric. Resolve reviewer disagreements material to a comparative conclusion, or report that conclusion as uncertain. Preserve the original criteria and judgments; design harder cases or a revised rubric as a subsequent experiment rather than changing the completed comparison to fit a preferred verdict.
- For Core-Prompts capability comparisons, identify the treatment and bind the actual supplied prompts/resources, model settings, starting state and effective runtime to the run record. Keep other conditions comparable or declare intended differences. Verify material file, tool, hook and browser boundaries using execution evidence where configuration alone is insufficient; unverified or violated boundaries make dependent comparative conclusions inconclusive. Do not infer isolation from fresh agents alone.
- Before a costly Core-Prompts capability experiment batch, exercise representative success and failure observations through the actual collection, verification and scoring path. Verify the expected outcomes and resolve discrepancies before dispatching the batch. Confirm that any injected fault used as evidence fired. Include model-mediated preflight in the authorized call, time and token budgets; a setup label grants no additional execution authority.
- When a Core-Prompts capability experiment stops or becomes inconclusive, retain confirmed defects, protocol deviations and the declared accounting, including incomplete calls and released or remaining reservations. Missing evidence does not erase an established failure. Preserve detailed findings within their existing disclosure boundary and use permitted summaries or references in public closeout records.
- For a declared task or experiment time budget, record the clock anchor, deadline, included phases, and stop action before dispatch. Account for waiting, coordination, and final verification, or name separate phase budgets. At a hard limit, perform the declared stop action, including stopping new trials, and disclose incomplete work or overruns; do not silently extend the window or report active model time as end-to-end latency.
- Plan delegation against observed host capacity, including controllers and nested workers. Avoid idle coordination layers that occupy slots needed for productive work. Reuse related agents only while preserving required review independence. After a capacity rejection, retry when capacity changes; do not assume an interrupt releases a slot or substitute simulated reviewers.

## Policy Placement

- Put cross-surface operating policy in steering.
- Put short routing guidance in `AGENTS.md`.
- Put user guidance, maintainer explanation, and examples in `README.md` or `docs/`.
- If a human doc starts reading like agent policy, move that content into steering and leave behind a short explanatory reference.
