---
name: "engos-delivery-implement-slice"
description: "Implement one bounded software change from an accepted task or clear request, preserve unrelated work, and report verification tied to the actual patch. Use for a scoped feature or repair; use the review-feedback capability when selected reviewer comments define the work."
display_name: "Implement a Bounded Slice"
kind: "workflow"
capability_type: "skill"
install_target: "global"
---
# Implement a Bounded Slice

## Purpose
Turn an authorized implementation request into a small, usable software change with evidence a reviewer can inspect. Start from an accepted task contract or an equally clear plain-language request. A small ask needs a readable result, not a new planning ceremony or mandatory JSON file.

## Primary Objective
Deliver the requested slice within its allowed writes and stop condition, with proportionate verification and an honest account of what remains unverified.

## In Scope
- One bounded feature, defect repair, or implementation step in an accepted plan.
- Repository inspection, scoped edits, relevant documentation, and checks needed to demonstrate the requested outcome.
- A concise handoff, optionally using `SliceReceipt.v1` when a controller or downstream reviewer requests machine interchange.

## Rules
- Establish the outcome, permitted changes, constraints, dependencies, verification and stop condition before editing. Resolve accessible facts yourself. Ask only when a material decision or missing authority prevents safe progress; continue independent authorized work.
- Read applicable repository instructions and actual files. Record the starting revision and initial dirty paths; preserve unrelated changes and active work. If edits overlap unowned dirty content, resolve ownership before changing it. Never reset or rewrite unrelated work to obtain a clean tree.
- Make the smallest coherent change that delivers the outcome. Do not substitute scaffolding for a usable behavior, add adjacent cleanup, invent requirements, or silently reduce acceptance criteria. Record out-of-scope discoveries for their owner.
- Use the existing host's editor, shell, diagnostics and test facilities. Load a companion or playbook only when the current work needs it and its use is authorized. This skill does not launch agents, create goals, configure providers, or supply a universal executor.
- Inherit stronger repository and controller requirements. This skill itself requires neither a commit after every slice nor a blanket full suite. Commit, push, merge, publish, deploy, install and destructive actions retain their existing authority boundaries; invocation alone grants none of those actions.
- Preserve selected reviewer comment IDs and dispositions when supplied by an authorized review-fix owner. Unselected or rejected comments are context, not permission to implement them. `engos-delivery-address-code-review` remains the owner of selecting and resolving review feedback; this skill does not replace its workflow or Batman's controller gates.

## Workflow
1. **Bind the task.** Inspect the accepted request and source evidence. When supplied, read `TaskContract.v1`: `id`, `outcome`, `requirement_ids`, `design_ids`, `depends_on`, `consumes`, `produces`, `likely_files`, `allowed_writes`, `constraints`, `verification`, `stop_condition`, and `authority_ref`. Check referenced inputs and prerequisites against current state; likely files are hints, not expanded write authority. Null references and unsatisfied dependencies remain explicit gaps. A plain request can supply the same meaningful context without this schema or an installed planning skill. Do not invent a task generation or contract digest absent from the supplied context.
2. **Inspect the starting state.** Confirm repository, base, branch or snapshot and initial dirty files. Locate the affected code, nearest useful tests and actual test configuration or wrappers. Identify a recovery boundary for task-owned edits. State the intended change and any assumption that matters to the outcome.
3. **Choose decisive verification.** Connect each check to an accepted behavior and an observable expected result derived from the requirement. Name a plausible defect the assertion would catch. Use the smallest relevant test, type, syntax, build or inspection path supported by repository evidence. For a bug or executable behavior change, reproduce failure before the fix when practical or required, then observe the expected pass; disclose missing red evidence. Do not delete or weaken tests to manufacture a pass. For a prose-only correction, diff and relevant link or syntax inspection may suffice. Do not claim an internal call count proves an external outcome or mock away the behavior being checked.
4. **Implement and inspect.** Edit only the authorized slice and necessary associated documentation. Keep abstractions proportional to present requirements. Use existing diagnostics to investigate an unexpected failure before changing more code. After an ambiguous stateful operation, inspect its effects before retrying. Stop dependent work for material scope changes, inaccessible prerequisites, authority gaps or a violated stop condition; preserve completed work and explain the next decision.
5. **Verify the candidate.** Run the selected checks on the actual candidate and retain commands, exit results and evidence references. A successful launcher is not evidence that tests ran: inspect the underlying result and expected assertions. Distinguish failed, unavailable and not-run checks. Expand checks only for repository requirements, changed behavior, new failures or unresolved risk. Refresh affected evidence after candidate changes instead of attaching stale results to a later patch.
6. **Review the diff and hand off.** Compare the result with the accepted outcome and original dirty inventory. Account for task-owned changed files, preserved unrelated changes, actual results, remaining limitations and next owner. Distinguish local implementation from independent review, hosted CI and landing. Stop at the requested boundary; do not convert a draft or no-commit request into a delivery campaign.

## Required Inputs
- An authorized bounded outcome or accepted task, including constraints and the intended stopping point.
- Repository or target files, applicable instructions, and access sufficient for the authorized edits and checks.
- Relevant source requirements and verification expectations, or permission to derive proportionate checks from inspected repository evidence.
- When applicable, selected review-comment IDs, task identity, upstream contract reference and controller handoff requirements; missing optional structured metadata stays unknown.

## Required Output
- The implemented outcome and task-owned changed files, or a concrete blocker with completed independent work preserved.
- Checks actually performed, their results and inspectable evidence; explicitly list unverified behavior and unavailable or not-run checks with reasons.
- Candidate identity and relevant starting state, preservation of unrelated dirty work, remaining work and next owner. Readable prose is enough for a small request.
- When machine interchange is requested, a `SliceReceipt.v1` matching the optional resource schema, with truthful nulls and unresolved context rather than invented values.

### Optional receipt contract
Load `resources/resource-map.json` and its `receipt` route only for a structured handoff. The owned template is `resources/templates/slice-receipt.json`; the shape is `resources/schemas/slice-receipt.schema.json`. The generated bundle also contains the repository's unchanged generic `resources/scripts/load_module.py` resource loader; it assembles selected resources and does not implement, diagnose, execute checks or prove consumption.

Record the actual `base` and `head_or_snapshot_digest` with `target_kind` equal to `commit` or `dirty_snapshot`. A commit target is valid only when the claimed candidate contains no additional uncommitted changes. For a dirty snapshot, bind a stable manifest of repository-relative paths, file byte digests, deletion markers and relevant modes, and retain its evidence reference and digest method. Include task-owned and initial unrelated dirty content needed to identify the inspected state; never label HEAD alone as a dirty candidate. Keep `changed_files` limited to this task and record `initial_dirty_files` separately. If state cannot be bound, leave identity null and explain the gap in `unresolved_context`; do not claim verified completion for that state.

Hash exact supplied structured contract bytes when available. `TaskContract.v1` has no generation field: use a separately supplied generation only with its provenance; otherwise `task_generation` is null. A plain ask may have a local task identifier but no structured contract hash. Null contract metadata requires an explicit unresolved-context explanation. `checks[].status = passed` requires an observed zero exit and retained evidence that the intended check actually ran. `failed` requires its observed nonzero exit and evidence; `not_run` and `unavailable` have null exit status and a reason. Schema validation enforces shape and basic consistency only; it cannot prove command execution, source truth, digest correctness, preservation, authority, meaningful assertions or completion. An empty checks list means no recorded command evidence, never a pass. Human inspection evidence can be described in `unverified` or the accompanying readable report; do not fabricate a process exit for it.

## Constraints
- No installed planner or oracle dependency is required. Supplied reviewed interfaces and repository facts are sufficient; unresolved material context still blocks dependent edits.
- No hidden delegation, autonomous goal creation, automatic review-comment selection, generalized route selection, unrelated cleanup, home installation or release side effect.
- No claim of independence from self-review, no test claim from a helper exit alone, and no completion claim from schema validity.
- Do not expose secrets in receipts or logs. Use safe evidence references and preserve the source's disclosure boundary.

## Invocation Hints
- “Implement this accepted task and stop with a reviewable patch.”
- “Fix the boundary error, show the focused regression result, and do not commit.”
- “Use `engos-delivery-implement-slice` for the next bounded step; preserve the unrelated dirty files.”
- For existing selected reviewer feedback, begin with `engos-delivery-address-code-review`. For an explicitly requested controller protocol, use `engos-orchestration-batman`; this capability does not start it.

## Examples
### Bounded bug repair
Request: “Reject an expired token at the exact expiry timestamp; keep valid tokens working and do not commit.” Inspect the actual expiry contract and test configuration, reproduce the boundary failure when practical, change the comparison, then run boundary and valid-token checks. Report observed red/green evidence, changed files and the dirty candidate identity. Do not present a hypothetical test invocation as executed.

### Small documentation change
Request: “Correct the stale configuration path in this guide.” Verify the intended path, edit that guide, and inspect the diff and relevant link. A short response states the correction and inspection. No structured receipt, test suite, task generation or commit is imposed.

### False completion and missing tools
A wrapper exits zero but produces no underlying test result. Report the test as unverified; investigate through existing diagnostics. If the required runner is missing, record `unavailable`, null exit and the missing prerequisite. Do not convert either observation into passed tests.

### Preserved unrelated work
The user authorizes one parser repair while a separate UI file is dirty. Record both starting paths, change only the parser and needed regression test, and verify the UI content remains unchanged. If selected feedback A is authorized but comment B was rejected, preserve B's rejected disposition and implement only A.

## Evaluation Rubric
Score each dimension 0 (absent or contradicted), 1 (partial with explicit gap), or 2 (supported by inspectable evidence):
- **Outcome and scope:** the accepted slice is usable and allowed writes and stop condition are respected.
- **Preservation:** initial dirty state is accounted for and unrelated work remains intact.
- **Verification:** checks target requirement-derived outcomes and plausible faults, with actual execution and limits distinguished.
- **Evidence integrity:** results are bound to the assessed state; failed, unavailable and not-run checks cannot become passed.
- **Handoff and authority:** remaining work and next owner are clear; no unauthorized lifecycle step, hidden agent or goal occurred.
A reviewable result needs no zero scores and explicit treatment of partial dimensions. Verified completion additionally requires evidence for every material acceptance criterion and no unresolved identity or authority gap. A numeric score or valid receipt alone never establishes completion or comparative improvement.

## Source Admission and Differences
This is independently written pattern synthesis informed by [Addy Osmani's incremental implementation guidance](https://github.com/addyosmani/agent-skills/blob/1be8e34187e34647bb83adc3a1323b26ae6f6abe/skills/incremental-implementation/SKILL.md), inspected at revision `1be8e34187e34647bb83adc3a1323b26ae6f6abe`, SHA-256 `df66536610071727feae1ca95f3c391c248ad828041750ccd3699cce763aa00b`, under MIT (copyright 2025 Addy Osmani). No donor body, code, template, asset or dependency is copied. Its per-slice commit and blanket full-suite requirements are not adopted.

A local installed `kiro/deliver` snapshot, SHA-256 `5c6d794efa0f8a8c9c02b5b68fd4d61958da6ae34f20c47020e083b576c23eac`, informed phase-specific context loading and honest completion concepts. Upstream revision and redistribution clearance are unknown; no literal content or bundled resources are imported. No universal router, provider controls or local installation dependency is adopted. The destination owns this new implementation workflow and its three resources; no existing clause is displaced. Reviewed TaskContract and oracle principles inform compatibility only; shared imports and sibling wiring remain separate work. This admission records inspected inputs and independently expressed differences, not behavioral superiority.
