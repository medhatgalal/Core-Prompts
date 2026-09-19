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

## Model, Effort, Context, and Delegation

- Use the least expensive model and lowest reasoning effort that can reliably meet the task's requirements. Honor explicit user choices and stricter project rules.
- Route clear, repeatable work to a fast, low-cost tier; everyday tool-using work to a balanced tier; ambiguous or high-value work to a deeper reasoning tier; and only the hardest end-to-end work to the strongest tier. For the current OpenAI family, those tiers are Luna, Terra, Sol, and Astra respectively; recheck provider guidance when the roster changes.
- Use low effort for narrow deterministic work, medium for ordinary multi-step work, and high for complex logic, edge cases, or consequential trade-offs. Use maximum effort only when depth matters more than latency or cost.
- Escalate model or effort only for a concrete task need or after a lower tier fails. Return to a lower tier for routine follow-up work.
- Use subagents only when the user explicitly requests delegation, an applicable skill or rule requires independent review, or the task contains genuinely independent work whose benefit exceeds coordination cost. Do not enable proactive delegation by default.
- Give each subagent one bounded outcome, the minimum complete context, required evidence, and a stop condition. Set its model and effort explicitly when the host supports that; otherwise use inheritance intentionally.
- Keep one controller responsible for scope, authority, synthesis, and final verification. Agreement among agents is not independent evidence, and delegation does not grant new write, merge, deploy, release, or cleanup authority.
- Load skills, rules, tools, files, and external sources on demand. Search narrowly first, batch compatible reads, request selected fields, and preserve decisive diagnostics and exit status.
- Before compaction, handoff, or a model change on a long task, preserve requirements, decisions, evidence, current state, and pending checks in the project's existing durable state.
- Do not treat configuration, invocation, shorter output, or fewer tool calls as proof of quality, savings, or completion.

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

## Agent Surface Approval

- Improve the requested existing skill or agent without adding another surface or expanding provider scope.
- Default reusable capability intake to skills. Do not convert a skill to `agent` or `both`, reintroduce a retired agent, or add an agent on another provider without the user's explicit approval for those identities.
- A recommendation, score, independent reviewer verdict, general implementation request, or `--yes` is not approval to add an agent surface. If approval is absent, return the proposed addition for the user to decide; do not fabricate an approval record.
- Record the actual approval reference and approved capability/provider identities in the existing UAC requirement review's `user_approval` field. Keep that approval separate from execution-need review. Existing approved registration scope can be retained during improvements; it cannot authorize additional identities.
- Named agent packages are distinct from generic independent workers. Keep required independent review and host permission boundaries when named packages are retired.
