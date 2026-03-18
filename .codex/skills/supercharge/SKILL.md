---
name: "supercharge"
description: "SuperCharge for prompt creation, prompt refinement, planning hardening, option comparison, grading, multi-pass critique, and structured execution-quality improvement across direct and agentic workflows."
---
# SuperCharge — Prompt Engineering, Planning Hardening, and Graded Improvement

## Purpose
Use this capability when the user needs a prompt, plan, proposal, or multi-step workflow made materially stronger through disciplined critique rather than one-pass rewriting. It exists to turn fuzzy requests into hardened prompts, better plans, clearer contracts, and explicit improvement ladders.

## Primary Objective
Produce a better artifact than the user started with, then explain why it is better: simpler where needed, harder to break, easier to execute, and explicit about assumptions, trade-offs, and remaining gaps.

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
- escalation: if the user asks for unsafe or destructive execution, stop and require explicit confirmation rather than folding it into prompt work

## Output Directory
When file output is requested, default to:
- `reports/supercharge/<timestamp>-prompt.md`
- `reports/supercharge/<timestamp>-plan.md`
- `reports/supercharge/<timestamp>-grade.md`
- `reports/supercharge/<timestamp>-comparison.md`

When inline output is better, keep the same structure and logical artifact names in the response.

## Workflow
1. Identify whether the task is prompt creation, prompt refinement, planning hardening, option comparison, grading, or catchup.
2. Route to the minimum useful pass stack instead of applying every lens blindly.
3. Improve the artifact using sequential passes, not concurrent framework soup.
4. State the approach decision, return the improved artifact, and explain the concrete delta.
5. When grading is requested, run a visible improvement ladder and name the remaining gaps.
6. When the task spans multiple independent subtasks, recommend an agentic partition instead of pretending one pass solves everything.

## Rules
- Never invent missing facts.
- Ask at most three targeted questions when missing information would materially change the answer.
- Prefer assumption packs over fake certainty when the user declines to answer.
- Never expose chain-of-thought.
- Prefer clarity and determinism over volume.
- Do not conflate prompt engineering with runtime-control authority.
- Use grading to sharpen quality, not to pad the output.

## Invocation Hints
Use this capability when the user asks for any of the following, even without naming the skill:
- make this prompt better
- harden this plan
- compare these options and converge on one recommendation
- critique this proposal from several angles
- grade this output and iterate it upward
- design an agentic workflow or prompt stack

## Required Inputs
- the current prompt, draft, plan, proposal, or intent statement
- any sources or alternatives that must be compared
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

## Constraints
- Do not stack heavy frameworks concurrently without reason.
- Do not bloat the answer with every module when a smaller route is enough.
- Do not pretend the model knows user preferences it has not been given.
- Do not turn grading into generic praise.
- Do not claim orchestration, approval, or runtime delegation authority.

## Module Routing
Default routing rules:
- prompt creation or refinement: `/ult`
- architecture, design, or planning: `/simple` -> `/invert` -> `/contract`
- option comparison or high-ambiguity synthesis: `/full` or `/converge`
- high-stakes asks: add `/adversarial` and `/safe`
- explicit grading: `/grade`
- session reconstruction only: `/catchup`

## Module Reference
### `/ult`
Create or refine prompts, then execute the improved prompt output when execution is appropriate.

### `/simple`
Remove braids, split mixed concerns, and make the artifact easier to reason about.

### `/invert`
Start with failure modes and missing signals before moving forward.

### `/adversarial`
Red-team the artifact and harden it against edge cases and unstated assumptions.

### `/contract`
Define the contract, acceptance criteria, and evaluation JSON or checklist.

### `/grade`
Run a visible 10-iteration improvement ladder and score the artifact against a rubric.

### `/full`
Run the illumination gauntlet without executing the final prompt.

### `/catchup`
Produce a forensic reconstruction of multi-intent conversation threads.

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


Capability resource: `.codex/skills/supercharge/resources/capability.json`
