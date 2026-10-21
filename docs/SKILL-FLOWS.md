# Skill Flows

Describe your intent and existing accepted work; let the assistant choose one
first missing job before carrying its artifact and uncertainty to a next needed
owner. The [intent guide](INTENT-ROUTING.md) and [visual guide](guide/index.html)
help distinguish rough problems, unclear acceptance, real competing proposals and
full shaping workshops. These are conditional journeys, not an automatic invocation
chain. A clear small change can enter implementation directly. Existing acceptance
and authorization still apply; a sidecar, neighbor link or passing schema adds none.
The skill contracts, your project's own rules and the applicable
[execution context](../.kiro/steering/agent-behavior.md#execution-context) govern execution.
Core-Prompts source-maintainer prerequisites do not apply to ordinary distribution use.

Use the [job map](SKILL-JOB-MAP.md) for the current names and boundaries, then read the
chosen skill's complete entry and selected resource route. Availability has six
separate evidence dimensions; advisory portfolio labels do not say whether your
host has installed or discovered a skill. [Getting started](GETTING-STARTED.md)
covers that check. JSON contracts below are optional interchange, not a required
new document system.

## The shortest useful route

A vague problem starts with framing; a known feature with unclear acceptance
starts with specification. Actual competing proposals start with Converge; missing
alternatives are requested, not invented. An explicitly requested full Shape Up
workshop stays with the shaping conductor and its actual stage gates and human
betting decisions. An actual diff or finished pitch can be reviewed directly.

A clear one-step request → **implement slice** → review the actual candidate when
required. For a larger uncertain change: **specify** → **architecture if a material
choice remains** → **plan if breakdown helps** → **implement a bounded slice** →
**review** → **GitOps for the authorized hosted gate**. This is a conditional map,
not an automatic pipeline. Existing accepted artifacts let you start later.

Skip a separate test-design pass when existing meaningful checks suffice. Skip
JSON sidecars when your tracker/prose already carries the needed facts. Skip
shaping for an already framed feature. None of these skips waives the selected
skill's own contract, required independent review or your project's checks.

## Optional jobs around the main flow

| Ask for this only when needed | Skill | Output / next use |
| --- | --- | --- |
| Strengthen a prompt, plan or proposal before using it | `engos-meta-supercharge` | Improved artifact, assumptions and failure modes; does not normally execute its target. |
| Resolve disagreement among proposals or sources | `engos-reconciliation-converge` | Attributed conflicts, criteria and one defensible recommendation. |
| Preserve a long investigation across sessions | `engos-memory-context-continuity` | Current context, pending work and insights; resume from verified state. |
| Compile a durable bounded goal/spec/verifier packet | `engos-design-plan-to-goal` | Packet and verification design; launching a goal is separate. |
| Measure whether an improvement works better | `engos-optimization-auto-research` | Baseline-controlled evidence within declared bounds. |

These jobs remain separately callable. Supercharge is not ordinary task planning;
Converge needs competing inputs; continuity is not automatic global memory; a goal
packet is not an implementation dispatch. Use [everyday examples](EXAMPLES.md#everyday-requests-before-and-now)
for small fixes through larger delivery.

## Feature or bounded change

| Missing job | Exact skill | Carry forward / finish condition |
| --- | --- | --- |
| Behavior or acceptance is unclear | `engos-design-specify-change` | Requirements, acceptance IDs, unchanged behavior, source revision and unresolved decisions; optional `SpecContract.v1`. The actual owner accepts scope. |
| A material technical choice needs a decision | `engos-design-architecture` | Design, interfaces, alternatives and unresolved decisions tied to requirements. Return changed requirements to their owner. Skip when no material choice exists. |
| Accepted work needs breakdown | `engos-design-plan-implementation` | Verifiable task outcomes, dependencies, consumed/produced interfaces, allowed writes, checks and stops; optional `TaskContract.v1` / `TaskPlan.v1`. Skip elaborate planning for one-step work. |
| Verification needs a meaningful oracle or coverage design | `engos-quality-testing-review` | Proposed observations and expected results; optional `TestDesign.v1` stays `not_run`. Skip a separate skill when existing checks suffice. |
| A bounded change is authorized | `engos-delivery-implement-slice` | Patch, actual verification, remaining limits and optional `SliceReceipt.v1`. Plain requests can enter here directly. |
| The actual candidate needs independent judgment | `engos-quality-code-review` | Findings bound to the chosen diff/commit/range and review limits. Selected repairs go to the feedback flow below. |

Material unresolved assumptions hold dependent task approval. Docs changes can
call for `engos-quality-docs-review`; a requested hosted merge/release gate calls
for `engos-quality-gitops-review`. Finish at the authorized deliverable and the
applicable repository delivery boundary. Release and live installation are separate.
See the [progressive feature example](EXAMPLES.md#progressive-feature-example).

## Failure diagnosis and repair

`engos-debug-diagnose-failure` accepts a failure without a candidate diff. It
returns reproduction, current/expected/unchanged behavior, competing hypotheses,
discriminating evidence and a supported cause or honest `unknown`; optional
`DiagnosisReceipt.v1` packages that evidence. A passing retry proves neither cause
nor repair. Stop when the diagnostic bound is reached or the next observation is
unavailable or unauthorized.

When repair is authorized, pass those facts and the narrow repair boundary to
`engos-delivery-implement-slice`. Use `engos-quality-testing-review` only when the
regression oracle needs design, and `engos-quality-code-review` for the actual
repair. `engos-operations-ic-assistant` coordinates an incident when that job is
needed; diagnosis does not take over human incident decisions. [Bug example](EXAMPLES.md#progressive-bug-example).

## Framing and shaping

Use `engos-design-frame-from-vague` for a solution-free frame alone, or
`engos-design-shaping` for the guided workshop. The conductor moves through actual
accepted stages and calls for research, architecture or code-health evidence only
when a stage question needs it. `engos-delivery-diagram-contract-artifacts` authors
required diagrams/contracts; `engos-quality-shaping-gate` judges stage evidence.
`engos-audit-pitch-review` can review a finished pitch independently, without a
fabricated workshop history. `engos-delivery-artifact-embed` places an authored
bundle only on an authorized destination.

Carry source evidence, appetite, open decisions and accepted/deferred/forbidden
scope. Missing material evidence returns to research; human choices remain with
their owners. Accepted build scope can enter specification later. Shaping is not
a prerequisite for every feature. [Workshop guide](engos-design-shaping.md).

## Tests and review feedback

Use `engos-quality-testing-review` to design tests or inspect coverage gaps;
proposed tests remain `not_run`. The implementation package's local verification
route contains shared oracle guidance and does not require invoking a sibling skill.
Use `engos-quality-code-review` to judge an actual target. Complete diff collection
and binding checks support that judgment but do not substitute for it.

Use `engos-delivery-address-code-review` only when selected actionable comments
already exist. Carry every selected comment ID, initial disposition, repair scope
and actual result back to re-review; accepted-but-unfinished work stays unresolved.
A new failure can enter diagnosis. No feedback selection silently expands to
rejected, deferred or unselected comments.

## Long-horizon and repeatable work

`engos-design-plan-implementation` is the ordinary planning owner.
`engos-design-plan-to-goal` compiles an explicitly wanted durable goal/spec/verifier
packet from reviewed intent; compiling does not start a goal. `engos-memory-context-continuity`
maintains resumable evidence and pending work; `engos-memory-threader` exports a
faithful transcript or handoff when that is the requested artifact.

Use `loopy` to find, craft, audit, run or debrief a bounded repeatable loop; select
the requested mode and preserve its own allowed actions, verifier, budget and stop
conditions. Crafting does not run, schedule or publish it. Use
`engos-orchestration-batman` only when explicitly requested for controller-led
delivery; it does not become the default implementation route. Neither a goal
packet nor Loopy creates authority for a downstream action.

## Skill improvement, audits and synthesis

| Need | Exact skill and boundary |
| --- | --- |
| Preserve meaning while editing instructions | `engos-meta-instruction-editor`; retain a semantic clause ledger. |
| Improve/import a capability | `engos-meta-uac-import`; reuse current clauses, choose one owner and preserve current names/surfaces through UAC. [Worked example](UAC-USAGE.md#worked-improvement-with-preservation-and-evidence). |
| Strengthen one prompt, plan or proposal | `engos-meta-supercharge`; choose the smallest useful reasoning route. |
| Reconcile competing inputs | `engos-reconciliation-converge`; expose conflicts and rejected alternatives with provenance. |
| Measure improvement against a baseline | `engos-optimization-auto-research`; declare criteria and limits before trials. Text review alone is not a benefit measurement. |
| Audit repository structure | `engos-audit-code-health`; read-only structural findings. |
| Audit feature completion | `engos-audit-feature-status`; compare stated scope against implementation evidence. |
| Report Git activity | `engos-audit-engineering-progress`; activity is not feature completion. |
| Summarize multiple project sources | `engos-audit-weekly-intel`; source confidence and audience-specific report. |
| Review operational incidents | `engos-audit-opex-incident-review`; evidence-backed digest and optional drill-downs. |

Each route ends at its requested artifact or experiment bound. A missing source
remains an evidence gap; conflicting human priorities remain a decision. The
retained [prompt donors (source repository)](https://github.com/medhatgalal/Core-Prompts/blob/main/docs/prompt-pack/README.md) remain callable. No route retires
a donor, renames an owner, adds an agent surface or authorizes installation.
