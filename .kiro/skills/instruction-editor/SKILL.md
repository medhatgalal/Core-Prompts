---
name: "instruction-editor"
description: "Edit prompts, skills, agent instructions, and workflow rules into direct, plain, scannable language without weakening behavior. Use when asked to remove AI-ish, Claude-ish, or ChatGPT-ish phrasing; apply Google developer style; reduce verbosity; tighten a skill; clarify actors and conditions; or preserve semantics while shortening instructions."
---
# Instruction Editor

## Evidence Status

This skill is experimental during the advisory evaluation rollout. It can produce auditable edits and preservation evidence, but it cannot promote its own rewrite or claim that clearer language improved agent behavior. UAC keeps automatic candidate rewriting off until independent evaluation proves value.

## Purpose
Make instruction artifacts easier to read and invoke while preserving their behavior. Treat clarity as an editorial hypothesis, never as proof that an agent will perform better.

Read `references/instruction-clarity.md` before applying the policy or proposing a rewrite.

## Primary Objective
Return a clearer artifact plus an auditable map from every meaningful edit to the behavior it preserves, changes, or leaves unresolved.

## Modes

### `audit`
Report clarity findings without changing the artifact.

### `rewrite`
Produce a candidate rewrite. Preserve commands, modality, authority, safety, prerequisites, order, schemas, required outputs, examples, exceptions, and fallbacks unless the user explicitly authorizes a semantic change.

### `diff`
Compare two versions clause by clause and classify changes as contract-neutral, behavior-affecting, ambiguous, or removed.

### `verify`
Check that a proposed edit has a preservation map and identify every behavioral claim that still requires evaluation.

## Workflow Contract
1. Identify the artifact, intended user, and requested mode.
2. Extract its actors, commands, conditions, modality, authority boundaries, ordering, outputs, exceptions, examples, and fallbacks.
3. Run the shared `instruction_clarity.v1` policy.
4. Apply only contract-neutral formatting automatically.
5. For wording or structural edits, produce a candidate and preservation map.
6. Mark contradictions or missing intent as unresolved; do not silently resolve them.
7. Route behavioral claims to `auto-research` through `capability-eval`.

## Stack Contract
Ordered handoffs are explicit:

```text
External source -> uac-import -> instruction-editor -> auto-research -> reviewed uac apply
Draft or hardened prompt -> supercharge -> instruction-editor -> auto-research
Documentation analysis -> docs-review-expert -> instruction-editor
```

Preserve upstream artifact identifiers, clause hashes, unresolved questions, and requested output. Add editorial evidence; do not replace upstream evidence.

## Tool Boundaries
- allowed: read artifacts, run deterministic clarity lint, propose edits, compute size deltas, and emit preservation evidence
- forbidden: promote the editor's own output, weaken behavior for fluency, invent missing intent, fetch Google HTML through UAC, or treat style compliance as task success
- escalation: route semantic comparisons to `auto-research`; route unresolved capability contracts back to the owner or UAC reviewer

## Invocation Hints
Use this capability when the user asks to:
- remove AI-ish, Claude-ish, ChatGPT-ish, corporate, or exhausting phrasing
- apply Google developer documentation style to a prompt or skill
- tighten or shorten instructions without changing behavior
- clarify actors, conditions, commands, or outputs
- audit an instruction artifact for readability or translation risk
- compare an edited instruction against its original contract

Do not auto-route ordinary prose editing, general documentation architecture, prompt hardening, or capability intake here unless instruction preservation is the central job.

## Required Inputs
- the instruction artifact or path
- the requested mode, defaulting to `audit`
- any authorized semantic changes
- an upstream Goal Contract or topology when available

## Required Output
Return these sections:
- `Edited Artifact`
- `Edit Ledger`
- `Preservation Map`
- `Before / After Size`
- `Behavioral Claims Requiring Proof`
- `Unresolved Ambiguities`

For `audit`, `Edited Artifact` may state `No edit requested`.

## Rules
- Use direct language only when it preserves the named actor and action.
- Keep `must`, `must not`, `never`, `only`, and approval requirements exact.
- Do not delete low-frequency modules or examples merely to reduce size.
- Keep human readability and behavioral fitness as separate scorecards.
- Report lines, words, bytes, and model-token estimates before and after.
- A smaller artifact is not automatically better.
- A model-preferred artifact is not automatically clearer to people.
- A human-preferred artifact is not automatically safer or more effective for agents.

## Examples

### Audit request
> Audit this skill for Claude-ish phrasing and buried conditions. Do not rewrite it.

Return findings with rule IDs, clause references, and risk. Do not claim behavior improved.

### Rewrite request
> Shorten this prompt while preserving every command and safety boundary.

Return the candidate, edit ledger, preservation map, size delta, and the cases needed to prove non-inferiority.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Preservation | Commands, modality, boundaries, order, outputs, exceptions, and fallbacks remain traceable |
| Clarity | Actors, conditions, and actions are direct and scannable |
| Honesty | Editorial quality is never reported as behavioral proof |
| Ambiguity | Contradictions and missing intent are surfaced, not silently repaired |
| Stack safety | Upstream artifacts remain intact and downstream handoff data is complete |
| Routing | The skill triggers for instruction editing and avoids neighboring general editing or hardening asks |


Capability resource: `.kiro/skills/instruction-editor/resources/capability.json`
