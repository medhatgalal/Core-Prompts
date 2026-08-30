---
name: "plan-to-goal-design"
description: "Turns an inspected implementation plan or intent into a compact, host-aware goal plus a durable specification and verifier packet. Use when a user wants to move from read-only Plan mode into a bounded long-running goal without losing repository evidence, rules, scope, or honest stop conditions."
---
# Plan to Goal Design

## Purpose
Compile a reviewed plan or implementation intent into a host-aware goal packet that a long-running coding agent can execute without treating chat memory as the source of truth. Use this skill after or during read-only planning when the user wants a durable goal, specification, and verifier. Do not use it for a simple one-step task, an ordinary implementation request that does not need a goal loop, or a request to run an unsupported native Goal command.

Read `resources/references/goal-design-lessons.md` and `resources/references/goal-authoring.md` before drafting goal prose. Read `resources/references/verifier-trust.md` before assigning a verification trust level. Read `resources/references/evidence.md` when current external facts or research claims affect the packet.

## Primary Objective
Return a compact goal whose details live in sealed, durable artifacts; prove that the packet matches the current repository and host; and refuse launch when the runner, research, verifier, or storage contract is not ready.

## In Scope
- research an implementation plan against the current repository, rules, toolchain, tests, ownership, and relevant primary external sources
- compile wrapper-free goal prose plus a durable specification, task-specific verifier, packet manifest, and completion-receipt contract
- lint the goal/spec/verifier triple with `bash resources/goal-lint`, then materialize, seal, and recheck packets through the bundled Python helper
- select only versioned, verified host adapters and report unsupported native runners explicitly
- classify verifier trust, expected untouched-tree failures, operator checks, material drift, and terminal states

## Out of Scope
- implementing the compiled goal or changing product source while the skill is in read-only planning mode
- inventing, installing, or operating a Claude, Gemini, or custom Goal runner
- treating a visible checksum as independent verification or treating self-review as completion
- choosing behavioral promotion, deployment, commit, merge, or external approval on the user's behalf
- manufacturing a long-running goal for a completed, one-step, watch-only, or otherwise unsuitable task

## Invocation Hints
Invoke this skill for requests such as:
- turn this approved plan into a goal
- prepare a copyable Goal-mode objective and iteration setting
- convert this implementation brief into a durable goal packet
- make this long-running goal research the repository before it edits
- create a goal, spec, and verifier without assuming every CLI has `/goal`

This skill compiles and validates a packet. It does not grant implementation authority, start a goal implicitly, install a custom runner, approve operator checks, or promote its own behavioral quality.

## Host Contract
Load `resources/adapters/hosts.json` and select the adapter matching the active product and measured version. Recheck the installed version when possible. Do not generalize one host's command grammar, size limit, iteration mechanism, file behavior, or Plan-mode permissions to another host.

Initial rules:
- Kiro CLI 2.20.1 has a native Goal runner, a 4,000-character description limit, default 5 iterations, maximum 50, and accepts `--max` at the start or end.
- Codex has native Goal mode or goal tools and a 4,000-character persisted objective. Do not invent an iteration flag or translate iterations into a token budget.
- Claude Code and Gemini CLI have documented Plan modes but no verified native Goal runner in the initial adapters.
- A custom runner is supported only after its adapter records versioned evidence for grammar, persistence, size, budget, and stopping behavior.

When no native or separately verified runner exists, return `UNSUPPORTED_NATIVE_GOAL` with the sealed packet and no launch command.

## Goal Prose Contract
Write `goal.txt` as wrapper-free prose. Count only its contents, not `/goal`, flags, quoting, or launcher syntax.

Size policy:
- target: about 800 characters when the specification and verifier carry the detail
- measured reference points: 914-character goal and 968-character prompt after extraction
- warning: more than 1,200 characters
- portable hard cap: 3,500 Unicode characters and 3,500 UTF-8 bytes
- host hard cap: the lower verified adapter limit, when lower than the portable cap

These preferred values are heuristics, not behavioral proof. Move overflow into `spec.md`; never raise the cap to preserve detail.

Use these labels once, in this order:
1. `OUTCOME` — one observable end state
2. `READ FIRST` — packet and specification paths
3. `BEFORE EDITING` — repository, rule, code, test, and research revalidation
4. `WORK` — dependency-ordered execution without narrowing the outcome
5. `GUARDRAILS` — three to five high-risk non-goals, protected surfaces, or approval boundaries
6. `DONE` — exact verifier command, trust level, and operator checks
7. `STOP / REPORT` — stale, blocked, approval-required, no-progress, exhausted, and achieved behavior plus receipt path

Do not place evidence dumps, long file inventories, source commentary, design rationale, or full task lists in `goal.txt`.

## Research-First Contract
Research is a sealing requirement, not motivational prose.

Before drafting:
1. Verify the runtime, cwd, repository root, worktree, remotes, branch, HEAD/tree, and exact dirty state.
2. Read every applicable instruction file from global scope through the target directory.
3. Separate proving the mechanism from executing a population. Write exactly one anchor over a small, measured sample with real work evidence; move bulk execution to a policy or routine operation. If the anchor requires authorization its author cannot grant, return `APPROVAL_REQUIRED` instead of disguising a queue as a goal.
4. Save the bounded sample in `baseline.json`. Before freezing it, intersect every sampled identifier with every exclusion or do-not-touch list and require every intersection to be empty.
5. Measure the wider population and prove its target is arithmetically and operationally achievable; split out members that require another disposition.
6. Inspect relevant entrypoints, callers, dependencies, tests, build and CI commands, generated surfaces, ownership, and concurrent work.
7. Identify likely, owned, protected, generated, and out-of-scope files.
8. Classify material statements as `FACT`, `INFERENCE`, `CONTRADICTION`, or `UNKNOWN` and cite repository facts by path and line or by exact command evidence.
9. Use current primary sources when versioned, external, uncertain, or high-impact facts affect the packet. Record retrieval date, relevance, and disconfirming evidence. If external research is unnecessary, state why local evidence is sufficient.
10. Ask only for decisions that cannot be discovered and would materially change scope, safety, or acceptance.

Put the receipt in `spec.md`. The executor must repeat a lightweight current-state and rule preflight before editing. Material drift yields `STALE_PACKET`; the executor must not silently rewrite the goal or verifier.

## Specification Contract
`spec.md` must contain:
- provenance and source-plan identity
- outcome, non-goals, and completion semantics
- exactly one bounded mechanism-proof anchor, its small sample, the wider-population disposition, and the baseline file that records stable identifiers
- every exclusion list considered before freezing plus evidence that all sample intersections are empty
- research receipt with rules, code, tests, CI, files, sources, facts, inferences, contradictions, unknowns, and approval decisions
- behavioral requirements and acceptance criteria; use EARS only where it improves testability
- dependency-ordered milestones and ownership boundaries
- constraints, prohibited shortcuts, protected surfaces, rollback, and decomposition decisions
- requirement-to-verifier mapping and operator-observed criteria
- a fake/block table, falsifiability case, cheapest-fake hostile-pass case, per-criterion flip plan, and exit-gate truth table
- a judge amendment protocol naming `judge-amendments.json` and its current state
- nonblank written answers for `PROXY`, `FORGERY`, `ARITHMETIC`, `ACHIEVABLE`, and `TRAP`
- drift triggers and terminal states

Prefer one goal. Split into ordered packets only when outcomes have different independent value, verifiers, owners, or approval boundaries, or when no single verifier can judge the complete result.

## Verification Contract
Assign exactly one trust level:
- `external_oracle`: the runner and truth source are outside executor write authority; sufficient for machine completion
- `operator_gate`: machine evidence plus a named human check; completion waits for acknowledgement
- `sealed_visible`: visible and tamper-evident but not independent; it may establish machine readiness, not final completion
- `self_check`: controlled by the executor; never sufficient for completion

Hashes prove tamper evidence, not independence. The verifier must:
- implement `bash verify.sh --list-criteria`, printing every machine criterion ID exactly once
- evaluate only the named criterion when `CRITERION_ID=<id>` is set, emitting the exact line `CRITERION <id> PASS` with exit `0` when its condition is present or `CRITERION <id> FAIL` with exit `1` when absent; invalid or unverifiable input uses a distinct error and must not fall through to the full suite
- pass every entry in `criterion-flips.json`: the exact criterion logic must be executed against synthetic condition-present and condition-absent trees and its verdict must flip in the required direction
- bind both synthetic tree hashes during sealing and reject fixture drift during every later lint or check
- map output to named requirement or criterion identifiers
- return a nonzero code on the untouched tree for the expected unmet criteria
- return a nonzero code on the cheapest fake tree even when mechanism checks appear satisfied
- fail if required tests or behaviors are missing, not only when existing tests fail
- resist the cheapest relevant shortcut, such as deleting tests, adding skips, weakening thresholds, or bypassing a paired surface
- disclose operator-only and unobservable criteria
- remain deterministic and cheap unless the requirement itself is external or nondeterministic

If the verifier passes either the untouched tree or cheapest fake, refuse `SEALED_READY`. Require an independent audit before returning `NO_GOAL_NEEDED`; a permissive verifier is not proof that the goal already exists. Run verifiers with `bash verify.sh`; never require their execute bit.

When a verifier defect is repaired after dispatch or a blocker report, treat it as a judge amendment. Record the previous and new SHA-256 hashes, one-line diff, changed and unchanged criterion IDs, and an instruction to diff before trusting. The implementer reports the defect but does not silently repair the judge. A missing or hash-mismatched disclosure blocks resealing.

## Storage and State Contract
Resolve storage in this order:
1. use a durable goal/spec location required by repository policy
2. for same-machine execution, use a user-approved path under `~/.agents/goals/`
3. for cloud or remote execution, use a repo-accessible committed or uploaded packet only with approval
4. otherwise return `MATERIALIZATION_REQUIRED` or `BLOCKED`

Plan mode may be read-only. Draft inline as `DRAFTED_UNSEALED`; do not claim that files exist. After approval or a permitted mode transition, materialize the exact draft and run the bundled packet helper.

Valid compiler states:
- `DRAFTED_UNSEALED`
- `MATERIALIZATION_REQUIRED`
- `SEALED_READY`
- `STALE_PACKET`
- `NO_GOAL_NEEDED`
- `BLOCKED`
- `UNSUPPORTED_NATIVE_GOAL`

## Workflow
1. Inspect the plan, repository, rules, runtime, and relevant external evidence.
2. Decide whether a long-running goal is warranted. Return `NO_GOAL_NEEDED` for a truly complete or one-step outcome only after evidence supports that decision.
3. Select and verify the host adapter.
4. Draft `goal.txt`, `spec.md`, `baseline.json`, `criterion-flips.json`, `judge-amendments.json`, a task-specific `verify.sh`, per-criterion synthetic trees, an untouched tree, a cheapest-fake hostile tree, and `packet.json` from the bundled templates.
5. In read-only Plan mode, return the exact draft as `DRAFTED_UNSEALED` and name the required materialization action.
6. After writes are authorized, materialize the packet in the resolved durable location.
7. Run `bash resources/goal-lint --tree <untouched-tree> --hostile-tree <cheapest-fake-tree> <packet-dir>`. Fix every finding; warnings must be acknowledged in the spec.
8. Run `python3 resources/scripts/goal_packet.py lint <packet-dir> --host <host>`.
9. Run `python3 resources/scripts/goal_packet.py seal <packet-dir>`. Seal only when size, schema, paths, repository binding, artifact hashes, adapter support, falsifiability, and hostile-pass checks succeed.
10. Run `python3 resources/scripts/goal_packet.py check <packet-dir>` immediately before launch.
11. Emit the wrapper-free goal, host-native budget, and launch command only when the adapter supports one.
12. Honor a user-supplied budget. Otherwise use a verified host default when one exists. Never invent Claude/Gemini iteration flags or convert iteration counts into Codex token budgets.
13. During execution, require a compact `receipt.json` with the terminal state, current revision, hashes, verifier evidence, operator checks, remaining work, and successor packet when applicable.

## Rules
- Rebuild constraints from the current repository instead of polishing stale plan claims.
- Keep the goal short by reference, not by deleting safety, scope, or completion semantics.
- Treat files, tests, manifests, CI, reviews, deployment, and runtime observation as distinct evidence gates.
- Preserve the user's literal outcome; do not redefine success around an easier subset.
- Do not write packet paths while the active mode forbids writes.
- Do not call a writable verifier independent.
- Do not design the anchor after the implementation plan or park a load-bearing outcome check in advisory output.
- Do not make bulk population execution the goal anchor; prove the mechanism over a bounded sample and route bulk work to its authorization-owning policy or routine.
- Do not freeze an identifier that appears in any exclusion or do-not-touch list.
- Do not accept a criterion that returns the same verdict for condition-present and condition-absent trees, returns an error instead of a valid verdict, or is absent from the verifier inventory.
- Do not trust a repaired judge until its amendment discloses the diff, old/new hashes, and criterion impact.
- Do not seal while any of the five manual design answers is blank.
- Do not emit a launch command for an unsupported or unverified runner.
- Do not call `structural_ready`, a sealed packet, green local tests, or a model review behavioral promotion.
- Stop on material drift, missing authority, unverifiable completion, unsupported host behavior, or failed sealing.

## Required Inputs
- an implementation plan, intent, issue, or approved planning artifact
- the target repository or working context
- the active host/runtime when detectable
- any user-supplied iteration, token, time, or cost bound
- explicit protected surfaces, approvals, or operator checks when already known

## Required Output
Return these fields in order:
1. `Research Receipt`
2. `Goal Packet Status`
3. `Artifact Manifest`
4. `Goal Prose`
5. `Host Budget`
6. `Verification Trust`
7. `Launch Command`
8. `Next Action`

For `DRAFTED_UNSEALED`, `Launch Command` must be `null`. For `UNSUPPORTED_NATIVE_GOAL`, keep the packet useful but state which runner contract is missing. For `SEALED_READY`, report goal characters, UTF-8 bytes, adapter version, repository binding, artifact hashes, baseline verifier result, and exact command.

Also report the `goal-lint` result, each criterion-flip result, the falsifiability exit, the hostile-pass exit, the anchor identifier and sample size, the population/exclusion intersection, judge amendment state, and whether all five written answers are present.

## Constraints
- Do not mutate source code while compiling a packet in read-only Plan mode.
- Do not use chat history as the only durable source for a long-running goal.
- Do not exceed 3,500 characters or bytes even when a host permits more.
- Do not hide unknowns, unsupported behavior, manual checks, or external-state dependencies.
- Do not rely on an execute bit for bundled scripts or task verifiers; invoke Bash and Python resources through their interpreters.
- Do not create, replace, pause, resume, or clear a goal unless the user separately requests that runtime action.
- Do not deploy, commit, merge, or alter global skill installations merely because the packet is ready.

## Examples
### Supported Kiro packet
> Turn this reviewed migration plan into a Kiro goal with at most ten iterations.

Inspect the current repository and Kiro version, freeze the outcome population, draft and materialize the packet, prove both falsifiability and hostile-pass failure, then return `SEALED_READY`, the wrapper-free goal, and a verified Kiro command.

### Unsupported native runner
> Turn this plan into a Gemini `/goal` command.

Compile the packet, then return `UNSUPPORTED_NATIVE_GOAL` unless a tested custom Gemini runner adapter is installed. Do not invent a command from Kiro syntax.

### Stale packet
> Launch the goal packet we created yesterday.

Run `check` first. If HEAD, dirty state, rules, files, adapter, or hashes materially changed, return `STALE_PACKET` and identify the exact drift instead of launching.

## Evaluation Rubric
| Check | What Passing Looks Like |
| --- | --- |
| Research grounding | Current repository, rules, code, tests, ownership, and relevant external facts are recorded before launch |
| Goal economy | Goal prose preserves outcome, preflight, guardrails, verifier, and stop behavior within the portable size budget |
| Host accuracy | Only verified commands, limits, and budget mechanisms are emitted |
| Durable context | The goal points to existing sealed artifacts that survive compaction and session changes |
| Verification honesty | Trust reflects write authority; expected baseline failures and operator gaps are explicit |
| Metric integrity | One frozen-population anchor is defined before the plan and survives proxy, forgery, arithmetic, achievability, and trap review |
| Two-sided validation | The verifier rejects both the untouched tree and the cheapest fake implementation for the expected reason |
| Criterion discrimination | Every machine criterion is inventoried and flips from pass to fail across its synthetic present/absent trees |
| Anchor granularity | A bounded real-evidence sample proves the mechanism; bulk execution and its approvals are outside the goal anchor |
| Population consistency | The frozen sample has empty intersection with every exclusion and do-not-touch list |
| Judge change integrity | Mid-flight judge repairs disclose one-line diff, hashes, changed/unchanged criteria, and diff-before-trust instruction |
| Drift safety | Material repository, rule, adapter, or artifact changes prevent launch |
| Boundary clarity | Compilation does not imply execution, promotion, deployment, or approval authority |


Capability resource: `.claude/skills/plan-to-goal-design/resources/capability.json`
